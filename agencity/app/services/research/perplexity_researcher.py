"""
Perplexity-based deep research for candidates.

Uses Perplexity API to research candidates and generate insights.
"""

import httpx
from typing import Optional, Dict, Any
from app.models.curation import UnifiedCandidate


class PerplexityResearcher:
    """Research candidates using Perplexity AI."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai"

    async def research_candidate(
        self,
        candidate: UnifiedCandidate,
        role_title: str,
        role_skills: list[str]
    ) -> Dict[str, Any]:
        """
        Deep research on a candidate using Perplexity.

        Returns insights about:
        - Technical skills and expertise
        - Notable projects and contributions
        - GitHub activity and repositories
        - Publications, talks, or articles
        - Professional reputation and signals
        """

        # Build research query
        query = self._build_research_query(candidate, role_title, role_skills)

        # Call Perplexity API
        insights = await self._call_perplexity(query)

        # Parse and structure insights
        return self._structure_insights(insights, candidate)

    def _build_research_query(
        self,
        candidate: UnifiedCandidate,
        role_title: str,
        role_skills: list[str]
    ) -> str:
        """Build a focused research query for Perplexity with LinkedIn context."""

        skills_str = ", ".join(role_skills[:5]) if role_skills else "software engineering"

        # Build query with LinkedIn URL for identity verification
        linkedin_context = ""
        if candidate.linkedin_url:
            # Extract LinkedIn username from URL
            linkedin_username = candidate.linkedin_url.split('/in/')[-1].strip('/')
            linkedin_context = f"\n\nVerify identity using their LinkedIn: {candidate.linkedin_url} (username: {linkedin_username})"

        # Add location for disambiguation
        location_context = ""
        if candidate.location:
            location_context = f" based in {candidate.location}"

        query = f"""Research {candidate.full_name} who works as {candidate.current_title} at {candidate.current_company}{location_context}.{linkedin_context}

I'm evaluating them for a {role_title} role that requires: {skills_str}.

Please find and summarize:
1. Their GitHub profile and notable repositories (if any) - verify the GitHub username matches this person
2. Technical skills, frameworks, and languages they use
3. Open source contributions or public projects
4. Professional achievements (hackathon wins, publications, talks)
5. Online presence (blog posts, articles, Stack Overflow, Twitter/X)
6. Education and relevant background

IMPORTANT: Only include information you can verify belongs to THIS specific person. If you find multiple people with the same name, use the LinkedIn profile and location to identify the correct person. If you cannot definitively match the information to this person, state "Unable to verify" for that section.

Focus on technical signals and verifiable accomplishments."""

        return query

    async def _call_perplexity(self, query: str) -> str:
        """Call Perplexity API for research."""

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "sonar",  # Perplexity's online search model
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a technical recruiter researching candidates. Provide factual, verifiable information only. Focus on professional signals and technical expertise."
                            },
                            {
                                "role": "user",
                                "content": query
                            }
                        ],
                        "temperature": 0.2,  # Low temperature for factual responses
                        "max_tokens": 1000
                    },
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    return f"Research failed: HTTP {response.status_code}"

            except Exception as e:
                return f"Research failed: {str(e)}"

    def _structure_insights(
        self,
        raw_insights: str,
        candidate: UnifiedCandidate
    ) -> Dict[str, Any]:
        """Structure raw Perplexity response into actionable insights."""

        return {
            "raw_research": raw_insights,
            "research_method": "perplexity_online",
            "sources_checked": [
                "GitHub",
                "LinkedIn",
                "Stack Overflow",
                "Professional websites",
                "Technical publications"
            ],
            "confidence": "high" if len(raw_insights) > 500 else "medium"
        }


class DeepResearchEngine:
    """
    Orchestrates deep research on top candidates.

    Uses Perplexity to gather additional context that's not in the database.
    """

    def __init__(self, perplexity_api_key: str):
        self.researcher = PerplexityResearcher(perplexity_api_key)

    async def enhance_candidates(
        self,
        candidates: list[UnifiedCandidate],
        role_title: str,
        role_skills: list[str],
        top_n: int = 5
    ) -> list[UnifiedCandidate]:
        """
        Run deep research on top N candidates.

        Adds research insights to candidate context.
        """

        enhanced = []

        for i, candidate in enumerate(candidates):
            # Only research top N
            if i >= top_n:
                enhanced.append(candidate)
                continue

            print(f"🔍 Researching candidate {i+1}/{min(top_n, len(candidates))}: {candidate.full_name}...")

            # Run Perplexity research
            insights = await self.researcher.research_candidate(
                candidate,
                role_title,
                role_skills
            )

            # Create updated candidate with research insights
            # Use model_copy since Pydantic models are immutable
            enhanced_candidate = candidate.model_copy(
                update={'deep_research': insights}
            )

            enhanced.append(enhanced_candidate)

        return enhanced
