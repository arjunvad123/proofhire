"""
Network Source - Our own candidate database (Supabase).

This is P0 priority - our opted-in network of 1,375+ candidates.
Fastest and highest quality source.
"""

import logging
from datetime import datetime

from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData, RepoData
from app.services.supabase import supabase
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class NetworkSource(DataSource):
    """
    Search our internal candidate network via Supabase.

    This is the highest priority source because:
    - Candidates have opted in
    - Data is verified
    - Fast to query (direct API)
    - Rich data (GitHub repos, projects, experience)
    """

    @property
    def name(self) -> str:
        return "Our Network"

    @property
    def priority(self) -> int:
        return 0  # Highest priority

    def _convert_to_candidate(self, data: dict) -> CandidateData:
        """Convert Supabase row to CandidateData model."""
        # Parse skills from comma-separated string
        skills_str = data.get("skills") or ""
        skills = [s.strip() for s in skills_str.split(",") if s.strip()]

        # Parse major from array
        major_list = data.get("major") or []
        major = major_list[0] if major_list else None

        # Convert GitHub repos if present
        github_repos = []
        for repo in data.get("github_repos", []):
            github_repos.append(
                RepoData(
                    name=repo.get("name", ""),
                    description=repo.get("description"),
                    language=repo.get("language"),
                    stars=repo.get("stargazers_count", 0),
                    forks=0,
                    is_fork=False,
                )
            )

        return CandidateData(
            id=data.get("id"),
            name=data.get("name", "Unknown"),
            email=data.get("email"),
            school=data.get("university"),
            major=major,
            location=data.get("location"),
            github_username=data.get("github_username"),
            github_url=f"https://github.com/{data.get('github_username')}" if data.get("github_username") else None,
            github_repos=github_repos,
            skills=skills,
            sources=["network"],
        )

    def _extract_keywords(self, blueprint: RoleBlueprint) -> list[str]:
        """Extract search keywords from blueprint."""
        keywords = []

        # Add role title words
        if blueprint.role_title:
            keywords.extend(blueprint.role_title.lower().split())

        # Add must-haves
        keywords.extend([s.lower() for s in blueprint.must_haves])

        # Add nice-to-haves
        keywords.extend([s.lower() for s in blueprint.nice_to_haves])

        # Common mappings for role types
        role_mappings = {
            "prompt": ["llm", "langchain", "rag", "openai", "gpt", "anthropic", "ai"],
            "engineer": ["python", "javascript", "react", "node", "backend", "frontend"],
            "ml": ["machine learning", "pytorch", "tensorflow", "sklearn", "data science"],
            "full": ["fullstack", "full stack", "react", "node", "typescript"],
            "backend": ["python", "go", "java", "fastapi", "django", "postgresql"],
            "frontend": ["react", "vue", "typescript", "css", "tailwind"],
        }

        # Expand keywords based on role
        expanded = []
        for kw in keywords:
            expanded.append(kw)
            if kw in role_mappings:
                expanded.extend(role_mappings[kw])

        # Deduplicate
        return list(set(expanded))

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 50,
    ) -> list[CandidateData]:
        """
        Search our network using the role blueprint.

        Search strategy:
        1. Extract keywords from blueprint
        2. Search candidates by skills, projects, university
        3. Score and rank by relevance
        4. Return top candidates with GitHub data enriched
        """
        logger.info(f"Searching network for: {blueprint.role_title}")

        # Extract search keywords
        keywords = self._extract_keywords(blueprint)
        logger.info(f"Search keywords: {keywords[:10]}")

        # Search via Supabase
        candidates_data = await supabase.search_for_role(
            role_keywords=keywords,
            must_have_skills=blueprint.must_haves,
            nice_to_have_skills=blueprint.nice_to_haves,
            location_preferences=blueprint.location_preferences,
            limit=limit * 2,  # Get extra to filter
        )

        logger.info(f"Found {len(candidates_data)} candidates from network")

        # Convert to CandidateData models
        candidates = []
        for data in candidates_data[:limit]:
            # Get GitHub repos for candidates with GitHub
            if data.get("github_username"):
                repos = await supabase.get_github_repos(data["id"], limit=5)
                data["github_repos"] = repos

            candidate = self._convert_to_candidate(data)
            candidates.append(candidate)

        return candidates

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """
        Enrich candidate with additional data from our network.

        For network candidates, we can pull full profile data.
        """
        if not candidate.id:
            return candidate

        # Get full candidate data
        full_data = await supabase.get_candidate_by_id(candidate.id)
        if not full_data:
            return candidate

        # Get GitHub repos if available
        if candidate.github_username:
            repos = await supabase.get_github_repos(candidate.id, limit=10)
            github_repos = []
            for repo in repos:
                github_repos.append(
                    RepoData(
                        name=repo.get("name", ""),
                        description=repo.get("description"),
                        language=repo.get("language"),
                        stars=repo.get("stargazers_count", 0),
                        forks=0,
                        is_fork=False,
                    )
                )
            candidate.github_repos = github_repos

        # Update enrichment timestamp
        candidate.enriched_at = datetime.utcnow()

        return candidate

    async def is_available(self) -> bool:
        """Check if Supabase connection is available."""
        try:
            # Try a simple query
            result = await supabase.get_candidates(limit=1)
            return len(result) > 0
        except Exception as e:
            logger.error(f"Network source unavailable: {e}")
            return False

    async def get_demo_candidates(self, limit: int = 5) -> list[CandidateData]:
        """
        Get top candidates specifically for demo purposes.

        Returns the most impressive candidates with rich data.
        """
        logger.info("Getting demo candidates from network")

        # Get top candidates from Supabase
        top_data = await supabase.get_top_candidates_for_demo(limit=limit)

        candidates = []
        for data in top_data:
            candidate = self._convert_to_candidate(data)
            candidates.append(candidate)

        logger.info(f"Returning {len(candidates)} demo candidates")
        return candidates
