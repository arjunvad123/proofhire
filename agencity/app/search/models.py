"""
Search models - Core data structures for network-driven search.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AccessPattern(str, Enum):
    """Types of access a network node can provide."""
    COMPANY_TEAM = "company_team"           # Access to their coworkers
    COMPANY_ALUMNI = "company_alumni"       # Access to ex-employees
    SCHOOL_ALUMNI = "school_alumni"         # Access to classmates
    SCHOOL_STUDENTS = "school_students"     # Professors -> students
    PORTFOLIO_COMPANIES = "portfolio"       # VCs -> portfolio
    OSS_CONTRIBUTORS = "oss_contributors"   # Maintainers -> contributors
    INDUSTRY_NETWORK = "industry_network"   # General industry connections
    RESEARCH_NETWORK = "research_network"   # Academic collaborators
    INVESTOR_NETWORK = "investor_network"   # Founders -> their investors' networks


class NodeType(str, Enum):
    """Classification of network nodes by their access patterns."""
    PROFESSOR = "professor"
    VC_INVESTOR = "vc_investor"
    FOUNDER = "founder"
    EXECUTIVE = "executive"
    ENGINEER = "engineer"
    ENGINEERING_MANAGER = "engineering_manager"
    RECRUITER = "recruiter"
    RESEARCHER = "researcher"
    OSS_MAINTAINER = "oss_maintainer"
    COMMUNITY_ORGANIZER = "community_organizer"
    UNKNOWN = "unknown"


class NetworkNode(BaseModel):
    """A person in your network analyzed for search potential."""
    person_id: UUID
    full_name: str

    # Current position
    company: Optional[str] = None
    title: Optional[str] = None
    linkedin_url: Optional[str] = None

    # Classification
    node_type: NodeType = NodeType.UNKNOWN
    access_patterns: list[AccessPattern] = []

    # Estimated reach
    estimated_reach: int = 0  # How many people they could connect you to

    # Searchable attributes (extracted for query generation)
    companies: list[str] = []      # Current + past companies
    schools: list[str] = []        # Education
    skills: list[str] = []         # Technical skills
    industries: list[str] = []     # Industry sectors
    locations: list[str] = []      # Geographic locations

    # Scoring components
    seniority_score: float = 0.5   # 0-1, higher = more senior
    network_freshness: float = 0.5 # 0-1, higher = more active/recent
    connection_strength: float = 0.5  # How strong is your connection


class SearchTarget(BaseModel):
    """What we're searching for."""
    role_title: str                          # "Senior ML Engineer"
    required_skills: list[str] = []          # ["Python", "TensorFlow"]
    preferred_skills: list[str] = []         # ["Kubernetes", "Ray"]
    experience_years_min: Optional[int] = None
    experience_years_max: Optional[int] = None

    # Context
    target_companies: list[str] = []         # Companies to search
    target_schools: list[str] = []           # Schools to search
    target_industries: list[str] = []        # Industries
    locations: list[str] = []                # Geographic preferences

    # From company UMO
    preferred_backgrounds: list[str] = []    # "FAANG", "YC", etc.
    anti_patterns: list[str] = []            # "Job hopper", etc.

    # Search parameters
    max_results: int = 100


class SearchPathway(BaseModel):
    """A path through the network to find candidates."""
    gateway_node: NetworkNode                # The network connection
    access_pattern: AccessPattern            # How they provide access

    # Generated queries for different APIs
    pdl_queries: list[dict] = []
    google_queries: list[str] = []
    github_queries: list[dict] = []
    perplexity_queries: list[str] = []

    # Scoring
    expected_value: float = 0.0              # Estimated quality of results
    relevance_to_target: float = 0.0         # How relevant to search target
    estimated_results: int = 0               # Expected number of results


class CandidateSource(BaseModel):
    """Record of how we found a candidate."""
    api: str                                 # "pdl", "google", "github", etc.
    query: str                               # The query that found them
    pathway_person_id: Optional[UUID] = None # Which network node led here
    access_pattern: Optional[AccessPattern] = None
    confidence: float = 0.5                  # API's confidence in result
    found_at: datetime = datetime.utcnow()


class DiscoveredCandidate(BaseModel):
    """A candidate found through search."""
    # Identity
    full_name: str
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    # Profile
    current_company: Optional[str] = None
    current_title: Optional[str] = None
    location: Optional[str] = None

    # How we found them
    sources: list[CandidateSource] = []      # Multiple sources = higher signal

    # Network proximity
    in_network: bool = False                 # Already a direct connection
    network_person_id: Optional[UUID] = None # If in network, which record
    pathway_hops: int = 99                   # 1 = direct, 2 = 2nd degree, etc.
    intro_paths: list[str] = []              # Possible intro routes

    # Raw data from APIs
    raw_data: dict = {}

    # Scores (computed later)
    source_quality_score: float = 0.0
    pathway_strength_score: float = 0.0
    multi_source_bonus: float = 0.0
    network_proximity_score: float = 0.0
    role_match_score: float = 0.0
    final_score: float = 0.0


class SearchResults(BaseModel):
    """Results from a search operation."""
    target: SearchTarget

    # Pathways used
    pathways_explored: int = 0
    queries_executed: int = 0

    # Results
    candidates: list[DiscoveredCandidate] = []
    total_raw_results: int = 0
    deduplicated_count: int = 0

    # Stats per source
    results_by_source: dict[str, int] = {}

    # Timing
    started_at: datetime = datetime.utcnow()
    completed_at: Optional[datetime] = None
    duration_seconds: float = 0.0
