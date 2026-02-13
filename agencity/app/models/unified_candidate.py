"""
Unified Candidate Model - Merges data from candidates + people tables
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import datetime

# Import existing RoleBlueprint (don't redefine)
from app.models.blueprint import RoleBlueprint


@dataclass
class UnifiedCandidate:
    """
    Merged candidate from Hermes (candidates) and/or Network (people).
    """

    # Identity (for deduplication)
    person_id: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    # Basic info
    full_name: str = ""
    location: Optional[str] = None

    # Current position
    headline: Optional[str] = None
    current_company: Optional[str] = None
    current_title: Optional[str] = None

    # Skills & experience
    skills: List[str] = field(default_factory=list)
    education_level: Optional[str] = None
    university: Optional[str] = None
    major: List[str] = field(default_factory=list)
    years_of_experience: Optional[str] = None

    # GitHub data
    github_username: Optional[str] = None
    github_profile_url: Optional[str] = None

    # Source metadata
    sources: List[str] = field(default_factory=list)  # ["hermes", "network"]
    primary_source: str = "unknown"
    source_quality: float = 0.5  # 0-1

    # Network intelligence (from people table)
    is_from_network: bool = False
    trust_score: Optional[float] = None
    warmth_score: float = 0.0  # 0-1, computed
    warm_path_description: Optional[str] = None

    # Hermes intelligence (from candidates table)
    opted_in: bool = False
    role_type: List[str] = field(default_factory=list)  # ["SWE", "ML"]

    # Computed metadata
    data_completeness: float = 0.0  # 0-1
    has_enrichment: bool = False
    enrichment_source: Optional[str] = None

    # Timestamps
    created_at: Optional[datetime] = None
    last_enriched: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "person_id": self.person_id,
            "email": self.email,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "full_name": self.full_name,
            "location": self.location,
            "headline": self.headline,
            "current_company": self.current_company,
            "current_title": self.current_title,
            "skills": self.skills,
            "education_level": self.education_level,
            "university": self.university,
            "major": self.major,
            "years_of_experience": self.years_of_experience,
            "github_username": self.github_username,
            "github_profile_url": self.github_profile_url,
            "sources": self.sources,
            "primary_source": self.primary_source,
            "source_quality": self.source_quality,
            "is_from_network": self.is_from_network,
            "trust_score": self.trust_score,
            "warmth_score": self.warmth_score,
            "warm_path_description": self.warm_path_description,
            "opted_in": self.opted_in,
            "role_type": self.role_type,
            "data_completeness": self.data_completeness,
            "has_enrichment": self.has_enrichment,
            "enrichment_source": self.enrichment_source,
        }


@dataclass
class SimpleScore:
    """
    Simple scoring without complex reasoning.
    Your cofounder will replace this with Proof Briefs.
    """

    candidate_id: str
    candidate_name: str

    # Overall
    total_score: float  # 0-100

    # Component scores
    skills_match: float = 0.0  # 0-100
    source_quality: float = 0.0  # 0-100
    warmth: float = 0.0  # 0-100

    # Simple flags
    is_warm: bool = False
    is_opted_in: bool = False
    has_github: bool = False

    # Action
    suggested_next_step: str = ""

    def to_dict(self) -> dict:
        return {
            "candidate_id": self.candidate_id,
            "candidate_name": self.candidate_name,
            "total_score": self.total_score,
            "skills_match": self.skills_match,
            "source_quality": self.source_quality,
            "warmth": self.warmth,
            "is_warm": self.is_warm,
            "is_opted_in": self.is_opted_in,
            "has_github": self.has_github,
            "suggested_next_step": self.suggested_next_step,
        }


# RoleBlueprint is imported from app.models.blueprint above
