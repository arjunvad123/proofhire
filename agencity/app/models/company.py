"""
Company and related data models for Agencity.

These models represent the company onboarding flow (Stage 0) and
data import (Stage 1).
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


# =============================================================================
# ENUMS
# =============================================================================

class CompanyStage(str, Enum):
    """Funding stage of the company."""
    PRE_SEED = "pre_seed"
    SEED = "seed"
    SERIES_A = "series_a"
    SERIES_B = "series_b"
    SERIES_C_PLUS = "series_c_plus"
    BOOTSTRAPPED = "bootstrapped"
    PUBLIC = "public"


class RoleLevel(str, Enum):
    """Seniority level for roles."""
    INTERN = "intern"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    STAFF = "staff"
    PRINCIPAL = "principal"
    LEAD = "lead"
    MANAGER = "manager"
    DIRECTOR = "director"
    VP = "vp"
    C_LEVEL = "c_level"


class RoleStatus(str, Enum):
    """Status of a hiring role."""
    ACTIVE = "active"
    PAUSED = "paused"
    FILLED = "filled"
    CLOSED = "closed"


class PersonStatus(str, Enum):
    """Status of a person in the database."""
    UNKNOWN = "unknown"
    ACTIVE_SEEKER = "active_seeker"
    PASSIVE = "passive"
    NOT_LOOKING = "not_looking"
    HIRED = "hired"


class DataSourceType(str, Enum):
    """Type of data source."""
    LINKEDIN_EXPORT = "linkedin_export"
    COMPANY_DATABASE = "company_database"
    PEOPLE_SEARCH = "people_search"
    MANUAL_ADD = "manual_add"
    AGENCITY_POOL = "agencity_pool"


class DataSourceStatus(str, Enum):
    """Processing status of a data source."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# =============================================================================
# COMPANY MODELS
# =============================================================================

class CompanyBase(BaseModel):
    """Base company fields."""
    name: str
    domain: Optional[str] = None
    stage: Optional[CompanyStage] = None
    industry: Optional[str] = None
    tech_stack: list[str] = Field(default_factory=list)
    team_size: Optional[int] = None


class CompanyCreate(CompanyBase):
    """Fields for creating a company."""
    founder_email: str
    founder_name: str


class Company(CompanyBase):
    """Full company model."""
    id: UUID = Field(default_factory=uuid4)

    # Founder info
    founder_email: str
    founder_name: str
    founder_linkedin_url: Optional[str] = None

    # Onboarding status
    linkedin_imported: bool = False
    existing_db_imported: bool = False
    onboarding_complete: bool = False

    # Pinecone namespace
    pinecone_namespace: Optional[str] = None

    # Stats
    people_count: int = 0
    roles_count: int = 0

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompanyUpdate(BaseModel):
    """Fields that can be updated."""
    name: Optional[str] = None
    domain: Optional[str] = None
    stage: Optional[CompanyStage] = None
    industry: Optional[str] = None
    tech_stack: Optional[list[str]] = None
    team_size: Optional[int] = None
    founder_linkedin_url: Optional[str] = None
    linkedin_imported: Optional[bool] = None
    existing_db_imported: Optional[bool] = None
    onboarding_complete: Optional[bool] = None
    people_count: Optional[int] = None
    roles_count: Optional[int] = None


# =============================================================================
# UMO (Unique Mandate Objective) MODELS
# =============================================================================

class CompanyUMOBase(BaseModel):
    """Base UMO fields - what the company is looking for."""
    # Ideal candidate profile
    preferred_backgrounds: list[str] = Field(default_factory=list)  # ["FAANG", "Startup", "Fintech"]
    must_have_traits: list[str] = Field(default_factory=list)
    anti_patterns: list[str] = Field(default_factory=list)  # What they DON'T want

    # Culture
    culture_values: list[str] = Field(default_factory=list)
    work_style: Optional[str] = None  # "Remote-first", "Hybrid", "In-office"

    # Free-form description
    ideal_candidate_description: Optional[str] = None


class CompanyUMOCreate(CompanyUMOBase):
    """Fields for creating a UMO."""
    pass


class CompanyUMO(CompanyUMOBase):
    """Full UMO model."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID

    # For embedding
    umo_text: Optional[str] = None  # Generated text representation

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# ROLE MODELS
# =============================================================================

class RoleBase(BaseModel):
    """Base role fields."""
    title: str
    level: Optional[RoleLevel] = None
    department: Optional[str] = None  # "Engineering", "Design", "Product"

    # Requirements
    required_skills: list[str] = Field(default_factory=list)
    preferred_skills: list[str] = Field(default_factory=list)
    years_experience_min: Optional[int] = None
    years_experience_max: Optional[int] = None

    # Details
    description: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None


class RoleCreate(RoleBase):
    """Fields for creating a role."""
    pass


class Role(RoleBase):
    """Full role model."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID

    status: RoleStatus = RoleStatus.ACTIVE

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# PERSON MODELS
# =============================================================================

class PersonBase(BaseModel):
    """Base person fields."""
    # Identity (dedupe keys)
    email: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None

    # Basic info
    full_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    headline: Optional[str] = None
    location: Optional[str] = None

    # Current position
    current_company: Optional[str] = None
    current_title: Optional[str] = None


class PersonCreate(PersonBase):
    """Fields for creating a person."""
    pass


class Person(PersonBase):
    """Full person model."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID  # Which company's namespace this person is in

    # Status
    status: PersonStatus = PersonStatus.UNKNOWN

    # Scores
    trust_score: float = 0.5
    relevance_score: Optional[float] = None

    # Flags
    is_from_network: bool = False  # From founder's LinkedIn
    is_from_existing_db: bool = False  # From company's database
    is_from_people_search: bool = False  # Discovered via API

    # Pinecone reference
    pinecone_id: Optional[str] = None

    # Timestamps
    first_seen: datetime = Field(default_factory=datetime.utcnow)
    last_enriched: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# PERSON ENRICHMENT MODELS
# =============================================================================

class Skill(BaseModel):
    """A parsed skill."""
    name: str
    category: Optional[str] = None  # "language", "framework", "tool", "domain"
    proficiency: Optional[str] = None  # "beginner", "intermediate", "expert"
    evidence: list[str] = Field(default_factory=list)  # ["github", "job_title"]


class WorkExperience(BaseModel):
    """Work experience entry."""
    company: str
    title: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None  # None = current
    is_current: bool = False
    description: Optional[str] = None


class PersonEnrichment(BaseModel):
    """Enriched profile data for a person."""
    id: UUID = Field(default_factory=uuid4)
    person_id: UUID

    # Skills (normalized)
    skills: list[Skill] = Field(default_factory=list)

    # Work history
    experience: list[WorkExperience] = Field(default_factory=list)

    # Education
    education: list[dict] = Field(default_factory=list)

    # Projects & signals
    projects: list[dict] = Field(default_factory=list)
    signals: list[dict] = Field(default_factory=list)

    # Raw enrichment data
    raw_enrichment: Optional[dict] = None
    enrichment_source: Optional[str] = None  # "perplexity_sonar", "manual"

    # Embedding text
    embedding_text: Optional[str] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# DATA SOURCE MODELS
# =============================================================================

class DataSourceBase(BaseModel):
    """Base data source fields."""
    type: DataSourceType
    name: Optional[str] = None  # "Connections.csv", "ATS Export March 2024"


class DataSourceCreate(DataSourceBase):
    """Fields for creating a data source."""
    pass


class DataSource(DataSourceBase):
    """Full data source model."""
    id: UUID = Field(default_factory=uuid4)
    company_id: UUID

    # File info
    file_url: Optional[str] = None
    file_name: Optional[str] = None

    # Stats
    total_records: int = 0
    records_matched: int = 0  # Merged with existing
    records_created: int = 0  # New people added
    records_failed: int = 0

    # Status
    status: DataSourceStatus = DataSourceStatus.PENDING
    error_message: Optional[str] = None

    imported_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# PERSON SOURCE (Junction Table)
# =============================================================================

class PersonSource(BaseModel):
    """Tracks which data source contributed to a person's data."""
    id: UUID = Field(default_factory=uuid4)
    person_id: UUID
    source_id: UUID

    # Original data from this source
    original_data: Optional[dict] = None

    # For network connections (LinkedIn export)
    connected_on: Optional[datetime] = None
    connection_strength: Optional[float] = None  # 0-1

    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# RESPONSE MODELS
# =============================================================================

class CompanyWithStats(Company):
    """Company with aggregated stats."""
    umo: Optional[CompanyUMO] = None
    roles: list[Role] = Field(default_factory=list)
    recent_imports: list[DataSource] = Field(default_factory=list)


class ImportResult(BaseModel):
    """Result of an import operation."""
    source_id: UUID
    status: DataSourceStatus
    total_records: int
    records_created: int
    records_matched: int
    records_failed: int
    errors: list[str] = Field(default_factory=list)


class LinkedInConnection(BaseModel):
    """Parsed LinkedIn connection from CSV."""
    first_name: str
    last_name: str
    full_name: str
    linkedin_url: Optional[str] = None
    email: Optional[str] = None
    company: Optional[str] = None
    position: Optional[str] = None
    connected_on: Optional[datetime] = None
