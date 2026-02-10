"""
Candidate data models.

These represent what we know (and don't know) about potential candidates.
"""

from datetime import datetime
from pydantic import BaseModel, Field


class RepoData(BaseModel):
    """GitHub repository data."""

    name: str
    description: str | None = None
    language: str | None = None
    stars: int = 0
    forks: int = 0
    is_fork: bool = False
    last_updated: datetime | None = None

    # Analysis
    has_llm_usage: bool = False  # Uses LLM APIs
    has_ml_code: bool = False  # ML/AI related
    has_tests: bool = False  # Has test files
    readme_quality: str | None = None  # "good", "basic", "none"


class ActivityStats(BaseModel):
    """GitHub activity statistics."""

    commits_last_90_days: int = 0
    prs_last_90_days: int = 0
    issues_last_90_days: int = 0
    total_contributions_last_year: int = 0
    longest_streak_days: int = 0
    active_days_per_week: float = 0.0


class HackathonData(BaseModel):
    """Hackathon participation data."""

    name: str
    date: datetime | None = None
    project_name: str | None = None
    project_description: str | None = None
    team_size: int | None = None
    won_prize: bool = False
    prize: str | None = None
    technologies: list[str] = Field(default_factory=list)
    devpost_url: str | None = None


class CandidateData(BaseModel):
    """
    Raw candidate data from multiple sources.

    This is what we collect before evaluation.
    We're honest about what we know vs. don't know.
    """

    # Identity
    id: str | None = None
    name: str
    email: str | None = None

    # Education (verifiable)
    school: str | None = None
    major: str | None = None
    graduation_year: int | None = None
    location: str | None = None

    # Affiliations
    clubs: list[str] = Field(default_factory=list)
    courses: list[str] = Field(default_factory=list)

    # GitHub data (observed)
    github_username: str | None = None
    github_url: str | None = None
    github_repos: list[RepoData] = Field(default_factory=list)
    github_activity: ActivityStats | None = None

    # Hackathon data (observed)
    hackathons: list[HackathonData] = Field(default_factory=list)

    # LinkedIn (if available via PDL)
    linkedin_url: str | None = None
    current_role: str | None = None
    current_company: str | None = None
    skills: list[str] = Field(default_factory=list)

    # Source tracking
    sources: list[str] = Field(default_factory=list)
    enriched_at: datetime | None = None

    # Internal scoring (not shown to users)
    initial_relevance_score: float = 0.0

    def has_github(self) -> bool:
        return bool(self.github_username)

    def has_hackathon_wins(self) -> bool:
        return any(h.won_prize for h in self.hackathons)

    def get_relevant_repos(self, keywords: list[str]) -> list[RepoData]:
        """Get repos that match keywords in name/description."""
        relevant = []
        for repo in self.github_repos:
            text = f"{repo.name} {repo.description or ''}".lower()
            if any(kw.lower() in text for kw in keywords):
                relevant.append(repo)
        return relevant
