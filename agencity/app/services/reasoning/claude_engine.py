"""
Claude Reasoning Engine

Uses Anthropic's Claude for advanced reasoning about candidates.
Replaces Kimi K2.5 with Claude for more reliable API access.

Key capabilities:
1. Query Reasoning - Generate smart search queries from role requirements
2. Candidate Analysis - Multi-agent analysis of candidates
3. Ranking Reasoning - Explain ranking decisions
4. Context Building - Generate rich narratives

Reference: https://docs.anthropic.com/en/api
"""

import asyncio
import json
import logging
from typing import Optional, Any
from pydantic import BaseModel
import httpx

from app.config import settings

logger = logging.getLogger(__name__)


# =============================================================================
# DATA MODELS
# =============================================================================

class QueryReasoning(BaseModel):
    """Result of query reasoning."""
    primary_query: str
    expansion_queries: list[str]
    reasoning_steps: list[str]
    network_leverage: str  # How we're using network context


class CandidateAnalysis(BaseModel):
    """Deep analysis of a candidate."""
    candidate_id: str
    candidate_name: str

    # Multi-agent scores (0-100)
    skill_score: float
    trajectory_score: float
    fit_score: float
    timing_score: float

    # Reasoning
    skill_reasoning: str
    trajectory_reasoning: str
    fit_reasoning: str
    timing_reasoning: str

    # Summary
    overall_assessment: str
    confidence: float

    # Context for display
    why_consider: list[str]
    concerns: list[str]
    unknowns: list[str]


class RankingReasoning(BaseModel):
    """Explanation of ranking decision."""
    candidate_id: str
    rank: int
    reasoning: str
    key_factors: list[str]
    compared_to: list[str]  # Other candidates this was compared against


# =============================================================================
# CLAUDE REASONING ENGINE
# =============================================================================

class ClaudeReasoningEngine:
    """
    Advanced reasoning engine using Claude.

    Architecture:
    - Uses Anthropic API for inference
    - Implements Agent Swarm pattern for parallel analysis
    - Provides reasoning chains for transparency

    Agent Swarm:
    - Skill Agent: Analyzes skill match
    - Trajectory Agent: Analyzes career trajectory
    - Fit Agent: Analyzes cultural/stage fit
    - Timing Agent: Analyzes readiness signals
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.claude_model
        self.api_url = "https://api.anthropic.com/v1/messages"
        self.enabled = bool(self.api_key)

        if not self.enabled:
            logger.warning("Anthropic API key not configured - reasoning will use fallback mode")

    # =========================================================================
    # QUERY REASONING
    # =========================================================================

    async def reason_about_queries(
        self,
        role_title: str,
        required_skills: list[str],
        preferred_skills: list[str] = [],
        location: Optional[str] = None,
        network_companies: list[str] = [],
        network_schools: list[str] = []
    ) -> QueryReasoning:
        """
        Generate intelligent search queries using network context.

        Instead of naive queries, reasons about:
        - Which network companies have similar talent
        - Which schools produce relevant candidates
        - What adjacent roles might be good fits
        """
        if not self.enabled:
            return self._fallback_query_reasoning(
                role_title, required_skills, network_companies, network_schools
            )

        prompt = f"""You are helping generate search queries for a recruiting search.

ROLE: {role_title}
REQUIRED SKILLS: {', '.join(required_skills)}
PREFERRED SKILLS: {', '.join(preferred_skills)}
LOCATION: {location or 'Any'}

NETWORK CONTEXT:
- Top companies in founder's network: {', '.join(network_companies[:10])}
- Top schools in founder's network: {', '.join(network_schools[:10])}

TASK: Generate search queries that leverage the network context.

Think step by step:
1. Which of the network companies likely have {role_title}s?
2. Which schools are known for producing people with these skills?
3. What adjacent roles might have transferable skills?
4. How can we find "warm" candidates through network overlap?

Output ONLY valid JSON (no markdown):
{{
    "primary_query": "main search query",
    "expansion_queries": ["query1", "query2", "query3"],
    "reasoning_steps": ["step1", "step2", "step3"],
    "network_leverage": "how we're using network context"
}}"""

        try:
            response = await self._call_claude(prompt)
            data = json.loads(response)
            return QueryReasoning(**data)
        except Exception as e:
            logger.error(f"Query reasoning failed: {e}")
            return self._fallback_query_reasoning(
                role_title, required_skills, network_companies, network_schools
            )

    def _fallback_query_reasoning(
        self,
        role_title: str,
        required_skills: list[str],
        network_companies: list[str],
        network_schools: list[str]
    ) -> QueryReasoning:
        """Fallback when Claude is not available."""
        skills_str = " ".join(required_skills[:3])

        primary = f"{role_title} {skills_str}"

        expansions = []
        if network_companies:
            expansions.append(f"{role_title} at {network_companies[0]}")
        if network_schools:
            expansions.append(f"{role_title} {network_schools[0]} alumni")
        expansions.append(f"senior {role_title} {skills_str}")

        return QueryReasoning(
            primary_query=primary,
            expansion_queries=expansions[:3],
            reasoning_steps=[
                f"Searching for {role_title} with {skills_str}",
                "Leveraging network companies for warm matches",
                "Including school alumni for additional reach"
            ],
            network_leverage="Using network companies and schools as search targets"
        )

    # =========================================================================
    # CANDIDATE ANALYSIS (Agent Swarm)
    # =========================================================================

    async def analyze_candidate(
        self,
        candidate: dict,
        role_title: str,
        required_skills: list[str],
        company_context: dict = {}
    ) -> CandidateAnalysis:
        """
        Deep analysis of a candidate using Agent Swarm pattern.

        Runs 4 specialized "agents" in parallel:
        - Skill Agent: Evaluates skill match
        - Trajectory Agent: Evaluates career path
        - Fit Agent: Evaluates cultural/stage fit
        - Timing Agent: Evaluates readiness signals
        """
        if not self.enabled:
            return self._fallback_candidate_analysis(candidate, role_title, required_skills)

        # Run agents in parallel
        skill_task = self._skill_agent(candidate, required_skills)
        trajectory_task = self._trajectory_agent(candidate, role_title)
        fit_task = self._fit_agent(candidate, company_context)
        timing_task = self._timing_agent(candidate)

        skill_result, trajectory_result, fit_result, timing_result = await asyncio.gather(
            skill_task, trajectory_task, fit_task, timing_task,
            return_exceptions=True
        )

        # Handle any exceptions
        if isinstance(skill_result, Exception):
            skill_result = {"score": 50, "reasoning": "Analysis unavailable"}
        if isinstance(trajectory_result, Exception):
            trajectory_result = {"score": 50, "reasoning": "Analysis unavailable"}
        if isinstance(fit_result, Exception):
            fit_result = {"score": 50, "reasoning": "Analysis unavailable"}
        if isinstance(timing_result, Exception):
            timing_result = {"score": 50, "reasoning": "Analysis unavailable"}

        # Synthesize results
        return CandidateAnalysis(
            candidate_id=str(candidate.get("id", "")),
            candidate_name=candidate.get("full_name", "Unknown"),
            skill_score=skill_result.get("score", 50),
            trajectory_score=trajectory_result.get("score", 50),
            fit_score=fit_result.get("score", 50),
            timing_score=timing_result.get("score", 50),
            skill_reasoning=skill_result.get("reasoning", ""),
            trajectory_reasoning=trajectory_result.get("reasoning", ""),
            fit_reasoning=fit_result.get("reasoning", ""),
            timing_reasoning=timing_result.get("reasoning", ""),
            overall_assessment=self._synthesize_assessment(
                skill_result, trajectory_result, fit_result, timing_result
            ),
            confidence=0.85,  # Claude has higher confidence
            why_consider=self._extract_positives(skill_result, trajectory_result, fit_result),
            concerns=self._extract_concerns(skill_result, trajectory_result, fit_result),
            unknowns=self._extract_unknowns(candidate)
        )

    async def _skill_agent(self, candidate: dict, required_skills: list[str]) -> dict:
        """Skill analysis agent."""
        prompt = f"""Analyze this candidate's skills for a role requiring: {', '.join(required_skills)}

CANDIDATE:
- Name: {candidate.get('full_name')}
- Title: {candidate.get('current_title')}
- Company: {candidate.get('current_company')}
- Skills: {candidate.get('skills', [])}
- Headline: {candidate.get('headline')}

Score 0-100 how well their skills match.
Output ONLY valid JSON (no markdown): {{"score": number, "reasoning": "brief explanation"}}"""

        try:
            response = await self._call_claude(prompt, max_tokens=200)
            return json.loads(response)
        except:
            return {"score": 50, "reasoning": "Unable to analyze"}

    async def _trajectory_agent(self, candidate: dict, role_title: str) -> dict:
        """Career trajectory analysis agent."""
        prompt = f"""Analyze this candidate's career trajectory for: {role_title}

CANDIDATE:
- Name: {candidate.get('full_name')}
- Current: {candidate.get('current_title')} at {candidate.get('current_company')}
- Experience: {candidate.get('experience', [])}

Consider:
- Is their career progressing toward this role?
- Do they have relevant company experience?
- Are they at the right seniority level?

Score 0-100 their trajectory fit.
Output ONLY valid JSON (no markdown): {{"score": number, "reasoning": "brief explanation"}}"""

        try:
            response = await self._call_claude(prompt, max_tokens=200)
            return json.loads(response)
        except:
            return {"score": 50, "reasoning": "Unable to analyze"}

    async def _fit_agent(self, candidate: dict, company_context: dict) -> dict:
        """Cultural/stage fit analysis agent."""
        prompt = f"""Analyze this candidate's fit for an early-stage startup.

CANDIDATE:
- Name: {candidate.get('full_name')}
- Current: {candidate.get('current_title')} at {candidate.get('current_company')}
- Experience: {candidate.get('experience', [])}

COMPANY CONTEXT:
- Stage: {company_context.get('stage', 'early')}
- Size: {company_context.get('size', 'small')}
- Culture: {company_context.get('culture', 'fast-moving startup')}

Consider:
- Have they worked at similar stage companies?
- Do they seem adaptable to startup environment?
- Will they thrive without structure?

Score 0-100 their cultural/stage fit.
Output ONLY valid JSON (no markdown): {{"score": number, "reasoning": "brief explanation"}}"""

        try:
            response = await self._call_claude(prompt, max_tokens=200)
            return json.loads(response)
        except:
            return {"score": 50, "reasoning": "Unable to analyze"}

    async def _timing_agent(self, candidate: dict) -> dict:
        """Timing/readiness analysis agent."""
        prompt = f"""Analyze this candidate's readiness to move to a new role.

CANDIDATE:
- Name: {candidate.get('full_name')}
- Current: {candidate.get('current_title')} at {candidate.get('current_company')}
- Timing signals: {candidate.get('timing_signals', [])}

Consider:
- Any layoff exposure?
- Long tenure suggesting readiness for change?
- Profile activity suggesting job search?

Score 0-100 their likely readiness to move.
Output ONLY valid JSON (no markdown): {{"score": number, "reasoning": "brief explanation"}}"""

        try:
            response = await self._call_claude(prompt, max_tokens=200)
            return json.loads(response)
        except:
            return {"score": 50, "reasoning": "Unable to analyze"}

    def _synthesize_assessment(self, skill, trajectory, fit, timing) -> str:
        """Synthesize overall assessment from agent results."""
        scores = [
            skill.get("score", 50),
            trajectory.get("score", 50),
            fit.get("score", 50),
            timing.get("score", 50)
        ]
        avg_score = sum(scores) / len(scores)

        if avg_score >= 80:
            return "Strong candidate - high confidence match across all dimensions"
        elif avg_score >= 65:
            return "Good candidate - solid match with some areas to explore"
        elif avg_score >= 50:
            return "Potential candidate - mixed signals, worth investigating"
        else:
            return "Weak match - significant gaps in fit"

    def _extract_positives(self, skill, trajectory, fit) -> list[str]:
        """Extract positive signals from agent results."""
        positives = []
        if skill.get("score", 0) >= 70:
            positives.append(f"Strong skills: {skill.get('reasoning', '')[:50]}")
        if trajectory.get("score", 0) >= 70:
            positives.append(f"Good trajectory: {trajectory.get('reasoning', '')[:50]}")
        if fit.get("score", 0) >= 70:
            positives.append(f"Cultural fit: {fit.get('reasoning', '')[:50]}")
        return positives or ["Matches basic criteria"]

    def _extract_concerns(self, skill, trajectory, fit) -> list[str]:
        """Extract concerns from agent results."""
        concerns = []
        if skill.get("score", 100) < 50:
            concerns.append("Skills gap")
        if trajectory.get("score", 100) < 50:
            concerns.append("Career trajectory mismatch")
        if fit.get("score", 100) < 50:
            concerns.append("Cultural fit concerns")
        return concerns

    def _extract_unknowns(self, candidate: dict) -> list[str]:
        """Identify what we don't know about the candidate."""
        unknowns = []
        if not candidate.get("skills"):
            unknowns.append("Skills not verified")
        if not candidate.get("experience"):
            unknowns.append("Work history incomplete")
        if not candidate.get("linkedin_url"):
            unknowns.append("LinkedIn not verified")
        return unknowns or ["None identified"]

    def _fallback_candidate_analysis(
        self,
        candidate: dict,
        role_title: str,
        required_skills: list[str]
    ) -> CandidateAnalysis:
        """Fallback analysis when Claude is not available."""
        # Simple heuristic scoring
        title = (candidate.get("current_title") or "").lower()
        headline = (candidate.get("headline") or "").lower()

        skill_score = 50
        for skill in required_skills:
            if skill.lower() in headline or skill.lower() in title:
                skill_score += 10
        skill_score = min(skill_score, 100)

        trajectory_score = 60 if role_title.lower() in title else 40
        fit_score = 55  # Default moderate fit
        timing_score = 50  # Default moderate timing

        return CandidateAnalysis(
            candidate_id=str(candidate.get("id", "")),
            candidate_name=candidate.get("full_name", "Unknown"),
            skill_score=skill_score,
            trajectory_score=trajectory_score,
            fit_score=fit_score,
            timing_score=timing_score,
            skill_reasoning="Based on keyword matching",
            trajectory_reasoning="Based on title match",
            fit_reasoning="Default moderate fit (no deep analysis)",
            timing_reasoning="Default moderate timing (no signals detected)",
            overall_assessment="Analysis limited - Claude not available",
            confidence=0.4,
            why_consider=["Matches search criteria"],
            concerns=[],
            unknowns=self._extract_unknowns(candidate)
        )

    # =========================================================================
    # BATCH ANALYSIS
    # =========================================================================

    async def analyze_candidates_batch(
        self,
        candidates: list[dict],
        role_title: str,
        required_skills: list[str],
        company_context: dict = {},
        max_concurrent: int = 5  # Lower than Kimi due to rate limits
    ) -> list[CandidateAnalysis]:
        """
        Analyze multiple candidates in parallel.

        Uses semaphore to limit concurrent API calls.
        """
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_semaphore(candidate):
            async with semaphore:
                return await self.analyze_candidate(
                    candidate, role_title, required_skills, company_context
                )

        tasks = [analyze_with_semaphore(c) for c in candidates]
        return await asyncio.gather(*tasks)

    # =========================================================================
    # RANKING REASONING
    # =========================================================================

    async def explain_ranking(
        self,
        candidates: list[dict],
        role_title: str
    ) -> list[RankingReasoning]:
        """
        Generate explanations for why candidates are ranked as they are.
        """
        explanations = []

        for i, candidate in enumerate(candidates[:10]):  # Top 10 only
            explanations.append(RankingReasoning(
                candidate_id=str(candidate.get("id", "")),
                rank=i + 1,
                reasoning=self._generate_ranking_reason(candidate, i + 1),
                key_factors=self._extract_ranking_factors(candidate),
                compared_to=[c.get("full_name", "") for c in candidates[i+1:i+3]]
            ))

        return explanations

    def _generate_ranking_reason(self, candidate: dict, rank: int) -> str:
        """Generate human-readable ranking reason."""
        fit = candidate.get("fit_score", 0)
        warmth = candidate.get("warmth_score", 0)
        timing = candidate.get("timing_score", 0)

        reasons = []
        if warmth >= 80:
            reasons.append("direct network connection")
        elif warmth >= 50:
            reasons.append("warm intro available")

        if fit >= 80:
            reasons.append("strong skill match")

        if timing >= 60:
            reasons.append("high readiness signals")

        if not reasons:
            reasons.append("matches search criteria")

        return f"Ranked #{rank} due to: {', '.join(reasons)}"

    def _extract_ranking_factors(self, candidate: dict) -> list[str]:
        """Extract key factors that influenced ranking."""
        factors = []

        if candidate.get("is_from_network"):
            factors.append("In network")
        if candidate.get("warm_path"):
            factors.append("Warm path exists")
        if candidate.get("fit_score", 0) >= 70:
            factors.append("High fit score")
        if candidate.get("timing_urgency") == "high":
            factors.append("High urgency")

        return factors or ["Standard match"]

    # =========================================================================
    # API HELPER
    # =========================================================================

    async def _call_claude(self, prompt: str, max_tokens: int = 1000) -> str:
        """Call Claude API."""
        if not self.api_key:
            raise ValueError("Anthropic API key not configured")

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}]
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            return data["content"][0]["text"]


# =============================================================================
# SINGLETON
# =============================================================================

claude_engine = ClaudeReasoningEngine()


# =============================================================================
# BACKWARDS COMPATIBILITY - Alias for Kimi engine
# =============================================================================

# Keep the same interface so existing code works
KimiReasoningEngine = ClaudeReasoningEngine
kimi_engine = claude_engine
