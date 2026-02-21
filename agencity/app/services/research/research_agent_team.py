"""
Research Agent Team

Replaces Perplexity with a Claude-powered multi-agent research pipeline.
Uses Claude's web_search tool for grounded, cited research with identity
verification via an Anchor-and-Verify pattern.

Architecture:
    Call 1 — Scoped Search Agent (Sonnet + web_search, allowed_domains)
    Call 2 — General Search Agent (Sonnet + web_search, no domain filter)
    Call 3 — Validation Agent (Haiku, no web search — validates findings)

Cost per candidate: ~$0.08-0.12
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx
from pydantic import BaseModel

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

class ResearchFinding(BaseModel):
    category: str          # "github", "publication", "achievement", "news"
    title: str
    url: Optional[str] = None
    summary: str
    verified: bool         # validated against anchor identity
    confidence: float      # 0-1
    source_domain: str     # "github.com", "medium.com", etc.


class ResearchResult(BaseModel):
    candidate_name: str
    anchor_linkedin: str
    findings: list[ResearchFinding] = []
    identity_confidence: float = 0.0  # overall confidence this is the right person
    conflicts: list[str] = []         # any disambiguation issues found
    citations: list[dict] = []        # {url, title}
    search_agent_model: str = ""
    validation_agent_model: str = ""
    total_searches: int = 0
    researched_at: str = ""           # ISO timestamp


# =============================================================================
# RESEARCH AGENT TEAM
# =============================================================================

class ResearchAgentTeam:
    """
    3-agent research pipeline using Claude with web_search tool.

    Extends the Agent Swarm pattern from claude_engine.py.
    """

    SCOPED_DOMAINS = [
        "github.com",
        "medium.com",
        "dev.to",
        "scholar.google.com",
        "stackoverflow.com",
        "npmjs.com",
        "pypi.org",
    ]

    def __init__(
        self,
        api_key: Optional[str] = None,
        search_model: str = "claude-sonnet-4-6",
        validation_model: str = "claude-haiku-4-5-20251001",
    ):
        self.api_key = api_key or settings.anthropic_api_key
        self.search_model = search_model
        self.validation_model = validation_model
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.enabled = bool(self.api_key)

    async def research_candidate(
        self,
        candidate_name: str,
        current_title: Optional[str],
        current_company: Optional[str],
        linkedin_url: Optional[str],
        location: Optional[str],
        role_title: str,
        required_skills: list[str],
    ) -> ResearchResult:
        """
        Run the full 3-agent research pipeline for one candidate.
        """
        if not self.enabled:
            logger.warning("Research agent team disabled (no Anthropic API key)")
            return ResearchResult(
                candidate_name=candidate_name,
                anchor_linkedin=linkedin_url or "",
                identity_confidence=0.0,
                researched_at=datetime.now(timezone.utc).isoformat(),
            )

        anchor = {
            "name": candidate_name,
            "title": current_title or "Unknown",
            "company": current_company or "Unknown",
            "linkedin_url": linkedin_url or "",
            "location": location or "Unknown",
        }

        # Run scoped + general search in parallel (Call 1 & 2)
        scoped_task = self._scoped_search_agent(anchor, role_title, required_skills)
        general_task = self._general_search_agent(anchor, role_title)

        scoped_result, general_result = await asyncio.gather(
            scoped_task, general_task, return_exceptions=True
        )

        if isinstance(scoped_result, Exception):
            logger.error("Scoped search agent failed: %s", scoped_result)
            scoped_result = {"findings": [], "citations": [], "search_count": 0}
        if isinstance(general_result, Exception):
            logger.error("General search agent failed: %s", general_result)
            general_result = {"findings": [], "citations": [], "search_count": 0}

        # Combine raw findings
        all_findings = scoped_result.get("findings", []) + general_result.get("findings", [])
        all_citations = scoped_result.get("citations", []) + general_result.get("citations", [])
        total_searches = scoped_result.get("search_count", 0) + general_result.get("search_count", 0)

        # Call 3: Validation agent
        if all_findings:
            validation = await self._validation_agent(anchor, all_findings)
            if isinstance(validation, Exception):
                logger.error("Validation agent failed: %s", validation)
                validation = {"validated_findings": all_findings, "identity_confidence": 0.3, "conflicts": ["Validation failed"]}
        else:
            validation = {"validated_findings": [], "identity_confidence": 0.2, "conflicts": ["No findings to validate"]}

        # Build structured findings
        findings = []
        for f in validation.get("validated_findings", []):
            findings.append(ResearchFinding(
                category=f.get("category", "unknown"),
                title=f.get("title", ""),
                url=f.get("url"),
                summary=f.get("summary", ""),
                verified=f.get("verified", False),
                confidence=f.get("confidence", 0.0),
                source_domain=f.get("source_domain", "unknown"),
            ))

        return ResearchResult(
            candidate_name=candidate_name,
            anchor_linkedin=linkedin_url or "",
            findings=findings,
            identity_confidence=validation.get("identity_confidence", 0.0),
            conflicts=validation.get("conflicts", []),
            citations=all_citations,
            search_agent_model=self.search_model,
            validation_agent_model=self.validation_model,
            total_searches=total_searches,
            researched_at=datetime.now(timezone.utc).isoformat(),
        )

    # =========================================================================
    # AGENT 1: SCOPED SEARCH
    # =========================================================================

    async def _scoped_search_agent(
        self,
        anchor: dict,
        role_title: str,
        required_skills: list[str],
    ) -> dict:
        """
        Scoped search agent — searches specific domains for technical presence.

        Uses allowed_domains to focus on GitHub, Medium, dev.to, etc.
        max_uses: 5 (caps cost at ~$0.05 in search fees)
        """
        skills_str = ", ".join(required_skills[:5]) if required_skills else "software engineering"

        system_prompt = (
            "You are a research assistant investigating a specific person's technical presence online. "
            "You MUST only report findings that match the anchor identity provided. "
            "If you find information about a different person with the same name, explicitly note it as a conflict. "
            "Output ONLY valid JSON, no markdown formatting."
        )

        user_prompt = f"""Research this person's technical presence:

ANCHOR IDENTITY:
- Name: {anchor['name']}
- Title: {anchor['title']}
- Company: {anchor['company']}
- LinkedIn: {anchor['linkedin_url']}
- Location: {anchor['location']}

ROLE CONTEXT: Evaluating for a {role_title} role requiring {skills_str}.

Search for:
1. Their GitHub profile — look for "{anchor['name']}" or username from LinkedIn
2. Technical blog posts or articles they've written
3. Open source contributions
4. Academic publications or talks

For each finding, note:
- The URL and title
- A brief summary
- Whether you're confident it belongs to THIS person (check company/location match)
- The source domain

Output JSON:
{{
    "findings": [
        {{
            "category": "github|publication|achievement|contribution",
            "title": "Finding title",
            "url": "https://...",
            "summary": "Brief description",
            "confidence": 0.0-1.0,
            "source_domain": "github.com"
        }}
    ],
    "search_queries_used": ["query1", "query2"]
}}"""

        response = await self._call_claude_with_search(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.search_model,
            max_uses=5,
            allowed_domains=self.SCOPED_DOMAINS,
        )

        return self._parse_search_response(response)

    # =========================================================================
    # AGENT 2: GENERAL SEARCH
    # =========================================================================

    async def _general_search_agent(self, anchor: dict, role_title: str) -> dict:
        """
        General search agent — finds news, talks, hackathon wins, etc.

        No domain restriction. max_uses: 3 (caps cost at ~$0.03)
        """
        system_prompt = (
            "You are a research assistant finding professional achievements and public mentions "
            "for a specific person. You MUST only report findings that match the anchor identity. "
            "Check that the company, location, and role match before including a finding. "
            "Output ONLY valid JSON, no markdown formatting."
        )

        user_prompt = f"""Find professional achievements and public mentions for this person:

ANCHOR IDENTITY:
- Name: {anchor['name']}
- Title: {anchor['title']}
- Company: {anchor['company']}
- LinkedIn: {anchor['linkedin_url']}
- Location: {anchor['location']}

Search for:
1. News mentions or press coverage
2. Conference talks or presentations
3. Hackathon wins or awards
4. Podcast appearances
5. Notable project launches

For each finding, include the URL and verify it matches THIS specific person.

Output JSON:
{{
    "findings": [
        {{
            "category": "news|achievement|talk|award",
            "title": "Finding title",
            "url": "https://...",
            "summary": "Brief description",
            "confidence": 0.0-1.0,
            "source_domain": "example.com"
        }}
    ],
    "search_queries_used": ["query1"]
}}"""

        response = await self._call_claude_with_search(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.search_model,
            max_uses=3,
            allowed_domains=None,
        )

        return self._parse_search_response(response)

    # =========================================================================
    # AGENT 3: VALIDATION
    # =========================================================================

    async def _validation_agent(self, anchor: dict, raw_findings: list[dict]) -> dict:
        """
        Validation agent — verifies findings belong to the right person.

        Uses Haiku (cheapest, no web search needed).
        """
        system_prompt = (
            "You are a validation agent that checks whether research findings belong to a specific person. "
            "You use the anchor identity (name, company, location, LinkedIn) to verify each finding. "
            "Output ONLY valid JSON, no markdown formatting."
        )

        user_prompt = f"""Validate these research findings against the anchor identity.

ANCHOR IDENTITY:
- Name: {anchor['name']}
- Title: {anchor['title']}
- Company: {anchor['company']}
- LinkedIn: {anchor['linkedin_url']}
- Location: {anchor['location']}

RAW FINDINGS:
{json.dumps(raw_findings, indent=2)}

For each finding, determine:
1. Does the name match? (exact or close match)
2. Does the company or organization match?
3. Is the location consistent?
4. Are there any date inconsistencies?
5. Could this be a different person with the same name?

Output JSON:
{{
    "validated_findings": [
        {{
            "category": "original category",
            "title": "original title",
            "url": "original url or null",
            "summary": "original summary",
            "verified": true/false,
            "confidence": 0.0-1.0,
            "source_domain": "original domain",
            "verification_note": "why verified or not"
        }}
    ],
    "identity_confidence": 0.0-1.0,
    "conflicts": ["any disambiguation issues found"]
}}"""

        response = await self._call_claude_no_search(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            model=self.validation_model,
        )

        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            # Try to extract JSON from the response
            extracted = self._extract_json(response)
            if extracted:
                return extracted
            logger.warning("Validation agent returned non-JSON: %s", response[:200] if response else "None")
            return {
                "validated_findings": raw_findings,
                "identity_confidence": 0.3,
                "conflicts": ["Validation response could not be parsed"],
            }

    # =========================================================================
    # API HELPERS
    # =========================================================================

    async def _call_claude_with_search(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_uses: int = 5,
        allowed_domains: Optional[list[str]] = None,
    ) -> dict:
        """
        Call Claude Messages API with web_search tool.

        Returns the full API response dict.
        """
        tool_def = {
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": max_uses,
        }
        if allowed_domains:
            tool_def["allowed_domains"] = allowed_domains

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": model,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
            "tools": [tool_def],
        }

        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                self.api_url, headers=headers, json=payload
            )
            response.raise_for_status()
            return response.json()

    async def _call_claude_no_search(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
    ) -> str:
        """Call Claude Messages API without web_search (for validation)."""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }

        payload = {
            "model": model,
            "max_tokens": 2048,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url, headers=headers, json=payload
            )
            response.raise_for_status()
            data = response.json()
            # Extract text content
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block["text"]
            return ""

    # =========================================================================
    # RESPONSE PARSING
    # =========================================================================

    def _parse_search_response(self, api_response: dict) -> dict:
        """
        Parse a Claude web_search response into structured findings + citations.
        """
        findings = []
        citations = []
        search_count = 0

        content_blocks = api_response.get("content", [])

        # Count searches from usage
        usage = api_response.get("usage", {})
        server_tool_use = usage.get("server_tool_use", {})
        search_count = server_tool_use.get("web_search_requests", 0)

        # Extract citations from text blocks
        for block in content_blocks:
            if block.get("type") == "text" and block.get("citations"):
                for cite in block["citations"]:
                    if cite.get("type") == "web_search_result_location":
                        citations.append({
                            "url": cite.get("url", ""),
                            "title": cite.get("title", ""),
                            "cited_text": cite.get("cited_text", ""),
                        })

        # Extract the JSON findings from the final text block
        for block in reversed(content_blocks):
            if block.get("type") == "text":
                text = block.get("text", "")
                parsed = self._extract_json(text)
                if parsed and "findings" in parsed:
                    findings = parsed["findings"]
                    break

        return {
            "findings": findings,
            "citations": citations,
            "search_count": search_count,
        }

    def _extract_json(self, text: str) -> Optional[dict]:
        """Try to extract JSON from text that may contain markdown or other content."""
        if not text:
            return None

        # Try direct parse first
        try:
            return json.loads(text)
        except (json.JSONDecodeError, TypeError):
            pass

        # Try to find JSON in code blocks
        import re
        json_pattern = re.compile(r'```(?:json)?\s*\n?(.*?)\n?```', re.DOTALL)
        match = json_pattern.search(text)
        if match:
            try:
                return json.loads(match.group(1))
            except (json.JSONDecodeError, TypeError):
                pass

        # Try to find JSON between curly braces
        brace_start = text.find('{')
        if brace_start >= 0:
            # Find matching closing brace
            depth = 0
            for i in range(brace_start, len(text)):
                if text[i] == '{':
                    depth += 1
                elif text[i] == '}':
                    depth -= 1
                    if depth == 0:
                        try:
                            return json.loads(text[brace_start:i+1])
                        except (json.JSONDecodeError, TypeError):
                            pass
                        break

        return None


# =============================================================================
# BATCH RESEARCH ORCHESTRATOR
# =============================================================================

class ResearchOrchestrator:
    """
    Orchestrates research across multiple candidates.

    Respects concurrency limits and integrates with the external candidate cache.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        max_concurrent: int = 3,
    ):
        self.team = ResearchAgentTeam(api_key=api_key)
        self.max_concurrent = max_concurrent

    async def research_candidates(
        self,
        candidates: list[dict],
        role_title: str,
        required_skills: list[str],
        top_n: int = 3,
    ) -> list[ResearchResult]:
        """
        Research top N candidates in parallel with concurrency limit.

        Args:
            candidates: List of candidate dicts with name, title, company, linkedin_url, location
            role_title: The role being hired for
            required_skills: Required skills for the role
            top_n: Number of candidates to research

        Returns:
            List of ResearchResult objects
        """
        if not self.team.enabled:
            logger.warning("Research agent team disabled — skipping research")
            return []

        to_research = candidates[:top_n]
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def _research_one(candidate: dict) -> ResearchResult:
            async with semaphore:
                return await self.team.research_candidate(
                    candidate_name=candidate.get("full_name", "Unknown"),
                    current_title=candidate.get("current_title"),
                    current_company=candidate.get("current_company"),
                    linkedin_url=candidate.get("linkedin_url"),
                    location=candidate.get("location"),
                    role_title=role_title,
                    required_skills=required_skills,
                )

        results = await asyncio.gather(
            *[_research_one(c) for c in to_research],
            return_exceptions=True,
        )

        research_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error("Research failed for candidate %d: %s", i, result)
                research_results.append(ResearchResult(
                    candidate_name=to_research[i].get("full_name", "Unknown"),
                    anchor_linkedin=to_research[i].get("linkedin_url", ""),
                    identity_confidence=0.0,
                    researched_at=datetime.now(timezone.utc).isoformat(),
                ))
            else:
                research_results.append(result)

        return research_results
