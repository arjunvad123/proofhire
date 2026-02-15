"""
Data models for candidate curation system.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MatchStrength(str, Enum):
    """Strength of a match signal."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class FitScore(BaseModel):
    """
    Candidate fit score with confidence.

    Confidence indicates how sure we are about the score.
    Low confidence means we need enrichment.
    """
    score: float = Field(ge=0, le=100, description="Overall fit score (0-100)")
    confidence: float = Field(ge=0, le=1, description="Confidence in score (0-1)")

    # Breakdown by category
    skills_match: Optional[float] = None
    experience_match: Optional[float] = None
    culture_match: Optional[float] = None
    signals_score: Optional[float] = None

    # Flags
    needs_enrichment: bool = False

    @property
    def is_confident(self) -> bool:
        """High confidence if > 0.7"""
        return self.confidence >= 0.7


class WhyConsiderPoint(BaseModel):
    """A specific reason to consider this candidate."""
    category: str  # "Skills Match", "Building Experience", etc.
    strength: MatchStrength
    points: List[str]  # ["✓ Python (3 years)", "✓ Built 15 projects"]

    class Config:
        use_enum_values = True


class AgentScore(BaseModel):
    """Score and reasoning from a single agent."""
    score: float = Field(ge=0, le=100, description="Agent score (0-100)")
    reasoning: str = Field(description="Agent reasoning text")


class ResearchHighlight(BaseModel):
    """Structured research insight from Perplexity."""
    type: str = Field(description="Type: github, publication, achievement, skill")
    title: str = Field(description="Title of the highlight")
    description: str = Field(description="Description or details")
    url: Optional[str] = None


class EnrichmentDetails(BaseModel):
    """Details about data enrichment sources."""
    sources: List[str] = Field(default=[], description="Enrichment sources used: pdl, perplexity, manual")
    pdl_fields: List[str] = Field(default=[], description="Fields enriched by PDL")
    research_highlights: List[ResearchHighlight] = Field(default=[], description="Perplexity research insights")
    data_quality_score: float = Field(default=0.0, ge=0, le=1, description="Data completeness score")


class ClaudeReasoning(BaseModel):
    """Claude AI reasoning breakdown."""
    overall_score: float = Field(ge=0, le=100, description="Overall weighted score")
    confidence: float = Field(ge=0, le=1, description="Confidence in analysis")
    agent_scores: Dict[str, AgentScore] = Field(description="Individual agent scores")
    weighted_calculation: str = Field(description="Explanation of weighted calculation")


class CandidateContext(BaseModel):
    """
    Rich context for founder decision-making.

    Answers:
    - Why should I interview this person?
    - What are the match points?
    - What don't we know?
    """
    why_consider: List[WhyConsiderPoint]
    unknowns: List[str]
    standout_signal: Optional[str] = None  # "Won Best AI Hack at SD Hacks 2024"
    warm_path: str

    # NEW: Enrichment details
    enrichment_details: Optional[EnrichmentDetails] = None

    # NEW: Claude reasoning breakdown
    claude_reasoning: Optional[ClaudeReasoning] = None


class CuratedCandidate(BaseModel):
    """
    A candidate in the curated shortlist.

    Everything founder needs to make a yes/no decision.
    """
    # Identity
    person_id: str
    full_name: str
    headline: Optional[str] = None
    location: Optional[str] = None

    # Current
    current_company: Optional[str] = None
    current_title: Optional[str] = None

    # Links
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    # Fit
    match_score: float = Field(ge=0, le=100)
    fit_confidence: float = Field(ge=0, le=1)

    # Context
    context: CandidateContext

    # Metadata
    was_enriched: bool = False
    data_completeness: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "person_id": "uuid-123",
                "full_name": "Maya Patel",
                "headline": "CS @ UCSD | AI/ML Enthusiast",
                "location": "San Diego, CA",
                "current_title": "Student",
                "match_score": 87,
                "fit_confidence": 0.85,
                "context": {
                    "why_consider": [
                        {
                            "category": "Skills Match",
                            "strength": "high",
                            "points": ["✓ Python (3 years)", "✓ React"]
                        }
                    ],
                    "unknowns": ["Professional experience"],
                    "warm_path": "Direct LinkedIn connection"
                }
            }
        }


class CurationRequest(BaseModel):
    """Request to curate candidates for a role."""
    company_id: str
    role_id: str
    limit: int = Field(default=15, ge=1, le=50)


class CurationResponse(BaseModel):
    """Response with curated shortlist."""
    shortlist: List[CuratedCandidate]
    total_searched: int
    metadata: Dict[str, Any]


class UnifiedCandidate(BaseModel):
    """
    Unified candidate profile.

    Built from people + person_enrichments tables.
    Handles incomplete data gracefully.
    """
    # From people table
    person_id: str
    full_name: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None

    # From person_enrichments (may be empty/None)
    skills: List[str] = []
    experience: List[Dict[str, Any]] = []
    education: List[Dict[str, Any]] = []
    projects: List[Dict[str, Any]] = []

    # Enrichment metadata
    enrichment_source: Optional[str] = None
    has_enrichment: bool = False

    # Deep research (from Perplexity, GitHub, etc.)
    deep_research: Optional[Dict[str, Any]] = None

    # Calculated
    data_completeness: float = 0.0

    def calculate_completeness(self) -> float:
        """Calculate how complete this profile is (0-1)."""
        score = 0
        total = 10

        # Basic fields (6 points)
        if self.email: score += 1
        if self.linkedin_url: score += 1
        if self.headline: score += 1
        if self.location: score += 1
        if self.current_company: score += 1
        if self.current_title: score += 1

        # Rich fields (4 points)
        if self.skills: score += 1
        if self.experience: score += 1
        if self.education: score += 1
        if self.projects: score += 1

        return score / total

    @property
    def years_of_experience(self) -> Optional[int]:
        """Estimate years of experience from experience list."""
        if not self.experience:
            return None

        total_months = 0
        for exp in self.experience:
            duration = exp.get('duration_months', 0)
            if duration:
                total_months += duration

        return total_months // 12 if total_months else None

    @property
    def top_skills(self) -> List[str]:
        """Get top 5 skills."""
        return self.skills[:5] if self.skills else []


class GitHubData(BaseModel):
    """Enriched GitHub data."""
    username: str
    profile_url: str
    total_repos: int = 0
    total_stars: int = 0
    commits_last_year: int = 0
    top_languages: List[str] = []
    notable_repos: List[Dict[str, Any]] = []


class DevPostData(BaseModel):
    """Enriched DevPost data."""
    username: str
    projects: List[Dict[str, Any]] = []
    awards: List[str] = []
