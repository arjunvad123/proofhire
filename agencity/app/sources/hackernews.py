"""
Hacker News Source - Tech talent from Who's Hiring threads.

HN has monthly "Who's Hiring" and "Who wants to be hired" threads
with high-quality tech candidates actively looking.

API Docs: https://github.com/HackerNews/API
"""

import logging
import re
from datetime import datetime

import httpx

from app.models.blueprint import RoleBlueprint
from app.models.candidate import CandidateData
from app.sources.base import DataSource

logger = logging.getLogger(__name__)


class HackerNewsSource(DataSource):
    """
    Search Hacker News "Who wants to be hired" threads.

    These threads contain high-quality candidates who are:
    - Actively looking for work
    - Part of the tech community
    - Often have strong backgrounds
    """

    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    HN_SEARCH_URL = "https://hn.algolia.com/api/v1"

    @property
    def name(self) -> str:
        return "Hacker News"

    @property
    def priority(self) -> int:
        return 6

    async def search(
        self,
        blueprint: RoleBlueprint,
        limit: int = 20,
    ) -> list[CandidateData]:
        """
        Search recent "Who wants to be hired" threads.
        """
        try:
            # Search for recent hiring threads
            candidates = await self._search_hiring_threads(blueprint, limit)
            return candidates

        except Exception as e:
            logger.error(f"Hacker News search failed: {e}")
            return []

    async def enrich(self, candidate: CandidateData) -> CandidateData:
        """HN candidates include all available info from their posts."""
        candidate.enriched_at = datetime.utcnow()
        return candidate

    async def is_available(self) -> bool:
        return True

    async def _search_hiring_threads(
        self,
        blueprint: RoleBlueprint,
        limit: int,
    ) -> list[CandidateData]:
        """
        Search Algolia HN API for candidates.
        """
        candidates = []

        # Build search query
        query = self._build_query(blueprint)

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                # Search for "freelancer" or "seeking work" posts
                response = await client.get(
                    f"{self.HN_SEARCH_URL}/search",
                    params={
                        "query": query,
                        "tags": "comment",  # Search comments
                        "hitsPerPage": 100,
                    },
                )
                response.raise_for_status()
                data = response.json()

                for hit in data.get("hits", []):
                    # Check if this looks like a job-seeking post
                    text = hit.get("comment_text", "")
                    if not self._is_job_seeking_post(text):
                        continue

                    candidate = self._parse_candidate_post(hit)
                    if candidate:
                        candidates.append(candidate)

                    if len(candidates) >= limit:
                        break

            except Exception as e:
                logger.warning(f"HN search failed: {e}")

        logger.info(f"Hacker News found {len(candidates)} candidates")
        return candidates

    def _build_query(self, blueprint: RoleBlueprint) -> str:
        """Build search query from blueprint."""
        terms = [blueprint.role_title]

        # Add key skills
        for skill in blueprint.must_haves[:2]:
            terms.append(skill)

        # Add location if specified
        for loc in blueprint.location_preferences[:1]:
            terms.append(loc)

        return " ".join(terms)

    def _is_job_seeking_post(self, text: str) -> bool:
        """Check if post is someone looking for work."""
        if not text:
            return False

        text_lower = text.lower()

        # Positive indicators
        seeking_phrases = [
            "seeking", "looking for", "available for",
            "open to", "remote ok", "willing to relocate",
            "years of experience", "email:", "contact:",
            "portfolio:", "github:", "linkedin:",
        ]

        # Check for seeking phrases
        has_seeking = any(phrase in text_lower for phrase in seeking_phrases)

        # Check it's long enough to be a real post
        is_substantial = len(text) > 100

        return has_seeking and is_substantial

    def _parse_candidate_post(self, hit: dict) -> CandidateData | None:
        """Parse a HN comment into candidate data."""
        text = hit.get("comment_text", "")
        if not text:
            return None

        author = hit.get("author", "anonymous")

        # Extract contact info
        email = self._extract_email(text)
        github = self._extract_github(text)
        linkedin = self._extract_linkedin(text)

        # Extract skills from text
        skills = self._extract_skills(text)

        # Extract location
        location = self._extract_location(text)

        # Extract experience level
        experience = self._extract_experience(text)

        candidate = CandidateData(
            id=f"hn_{hit.get('objectID', author)}",
            name=author,  # HN username
            email=email,
            location=location,
            github_username=github,
            linkedin_url=linkedin,
            skills=skills,
            sources=["hackernews"],
        )

        # Store the original post for context
        candidate.hn_post = text[:500]  # Truncate for storage

        return candidate

    def _extract_email(self, text: str) -> str | None:
        """Extract email from text."""
        # Common patterns: email: x@y.com, contact: x@y.com, x [at] y [dot] com
        patterns = [
            r'[\w\.-]+@[\w\.-]+\.\w+',
            r'[\w\.-]+\s*\[at\]\s*[\w\.-]+\s*\[dot\]\s*\w+',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                email = match.group(0)
                # Convert [at] [dot] format
                email = re.sub(r'\s*\[at\]\s*', '@', email)
                email = re.sub(r'\s*\[dot\]\s*', '.', email)
                return email

        return None

    def _extract_github(self, text: str) -> str | None:
        """Extract GitHub username from text."""
        patterns = [
            r'github\.com/([a-zA-Z0-9_-]+)',
            r'github:\s*@?([a-zA-Z0-9_-]+)',
            r'gh:\s*@?([a-zA-Z0-9_-]+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)

        return None

    def _extract_linkedin(self, text: str) -> str | None:
        """Extract LinkedIn URL from text."""
        match = re.search(r'linkedin\.com/in/([a-zA-Z0-9_-]+)', text, re.IGNORECASE)
        if match:
            return f"https://linkedin.com/in/{match.group(1)}"
        return None

    def _extract_skills(self, text: str) -> list[str]:
        """Extract skills mentioned in text."""
        common_skills = [
            "Python", "JavaScript", "TypeScript", "React", "Node.js",
            "Go", "Rust", "Java", "C++", "Ruby", "PHP", "Swift",
            "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform",
            "PostgreSQL", "MongoDB", "Redis", "Elasticsearch",
            "Machine Learning", "ML", "AI", "NLP", "LLM", "Deep Learning",
            "Backend", "Frontend", "Full Stack", "DevOps", "SRE",
            "iOS", "Android", "Mobile", "Web", "API",
        ]

        found = []
        text_lower = text.lower()

        for skill in common_skills:
            if skill.lower() in text_lower and skill not in found:
                found.append(skill)

        return found[:10]  # Limit to 10 skills

    def _extract_location(self, text: str) -> str | None:
        """Extract location from text."""
        # Common location patterns
        patterns = [
            r'location:\s*([^,\n]+)',
            r'based in\s+([^,\n]+)',
            r'from\s+([^,\n]+)',
            r'\b(remote|usa|europe|asia|san francisco|new york|london|berlin)\b',
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        return None

    def _extract_experience(self, text: str) -> str | None:
        """Extract years of experience."""
        match = re.search(r'(\d+)\+?\s*years?\s*(of)?\s*(experience)?', text, re.IGNORECASE)
        if match:
            return f"{match.group(1)}+ years"
        return None
