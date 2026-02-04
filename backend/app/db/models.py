"""SQLAlchemy database models."""

from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Index, String, Text, Boolean, Float, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import enum

from app.db.base import Base
from app.core.ids import generate_id
from app.core.time import utc_now


# Enums
class MembershipRole(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class RoleStatus(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"


class ApplicationStatus(str, enum.Enum):
    APPLIED = "applied"
    PRESCREENED = "prescreened"
    IN_SIMULATION = "in_simulation"
    GRADING = "grading"
    COMPLETE = "complete"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class SimulationRunStatus(str, enum.Enum):
    QUEUED = "queued"
    RUNNING = "running"
    FAILED = "failed"
    SUCCEEDED = "succeeded"


class ArtifactType(str, enum.Enum):
    DIFF = "diff"
    TEST_LOG = "test_log"
    COVERAGE = "coverage"
    WRITEUP = "writeup"
    SOURCE_BUNDLE = "source_bundle"
    METRICS_JSON = "metrics_json"
    LLM_OUTPUT = "llm_output"


class ClaimStatus(str, enum.Enum):
    PROVED = "PROVED"
    UNPROVED = "UNPROVED"


# Models
class Org(Base):
    """Organization (company using ProofHire)."""

    __tablename__ = "orgs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(back_populates="org", cascade="all, delete-orphan")
    roles: Mapped[list["Role"]] = relationship(back_populates="org", cascade="all, delete-orphan")


class User(Base):
    """User account (founders, admins)."""

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str | None] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class Membership(Base):
    """User membership in an organization."""

    __tablename__ = "memberships"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("orgs.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False)
    role: Mapped[MembershipRole] = mapped_column(SQLEnum(MembershipRole), default=MembershipRole.MEMBER)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    org: Mapped["Org"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship(back_populates="memberships")

    __table_args__ = (
        Index("ix_memberships_org_user", "org_id", "user_id", unique=True),
    )


class Role(Base):
    """Job role with evaluation configuration."""

    __tablename__ = "roles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    org_id: Mapped[str] = mapped_column(String(36), ForeignKey("orgs.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    com_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # Company Operating Model
    rubric_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # Evaluation rubric
    evaluation_pack_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # Enabled simulations
    status: Mapped[RoleStatus] = mapped_column(SQLEnum(RoleStatus), default=RoleStatus.DRAFT)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    org: Mapped["Org"] = relationship(back_populates="roles")
    applications: Mapped[list["Application"]] = relationship(back_populates="role", cascade="all, delete-orphan")


class Candidate(Base):
    """Candidate profile."""

    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    github_url: Mapped[str | None] = mapped_column(String(512))
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    applications: Mapped[list["Application"]] = relationship(back_populates="candidate", cascade="all, delete-orphan")


class Application(Base):
    """Application to a role."""

    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    role_id: Mapped[str] = mapped_column(String(36), ForeignKey("roles.id"), nullable=False)
    candidate_id: Mapped[str] = mapped_column(String(36), ForeignKey("candidates.id"), nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(SQLEnum(ApplicationStatus), default=ApplicationStatus.APPLIED)
    consent_version: Mapped[str] = mapped_column(String(50), default="v1.0")
    prescreen_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    role: Mapped["Role"] = relationship(back_populates="applications")
    candidate: Mapped["Candidate"] = relationship(back_populates="applications")
    simulation_runs: Mapped[list["SimulationRun"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    claims: Mapped[list["Claim"]] = relationship(back_populates="application", cascade="all, delete-orphan")
    briefs: Mapped[list["Brief"]] = relationship(back_populates="application", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_applications_role_candidate", "role_id", "candidate_id", unique=True),
    )


class SimulationRun(Base):
    """A single simulation execution."""

    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    simulation_id: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "bugfix_v1"
    status: Mapped[SimulationRunStatus] = mapped_column(SQLEnum(SimulationRunStatus), default=SimulationRunStatus.QUEUED)
    started_at: Mapped[datetime | None] = mapped_column()
    finished_at: Mapped[datetime | None] = mapped_column()
    runner_metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    application: Mapped["Application"] = relationship(back_populates="simulation_runs")
    artifacts: Mapped[list["Artifact"]] = relationship(back_populates="simulation_run", cascade="all, delete-orphan")
    metrics: Mapped[list["Metric"]] = relationship(back_populates="simulation_run", cascade="all, delete-orphan")


class Artifact(Base):
    """Stored evidence artifact (S3 reference)."""

    __tablename__ = "artifacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    simulation_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("simulation_runs.id"), nullable=False)
    type: Mapped[ArtifactType] = mapped_column(SQLEnum(ArtifactType), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(512), nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    simulation_run: Mapped["SimulationRun"] = relationship(back_populates="artifacts")


class Metric(Base):
    """Deterministic measurement from a simulation run."""

    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    simulation_run_id: Mapped[str] = mapped_column(String(36), ForeignKey("simulation_runs.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    value_float: Mapped[float | None] = mapped_column(Float)
    value_text: Mapped[str | None] = mapped_column(Text)
    value_bool: Mapped[bool | None] = mapped_column(Boolean)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    simulation_run: Mapped["SimulationRun"] = relationship(back_populates="metrics")

    __table_args__ = (
        Index("ix_metrics_run_name", "simulation_run_id", "name"),
    )


class Claim(Base):
    """A proven or unproven claim about a candidate."""

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    claim_type: Mapped[str] = mapped_column(String(100), nullable=False)
    claim_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    status: Mapped[ClaimStatus] = mapped_column(SQLEnum(ClaimStatus), nullable=False)
    evidence_refs_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # artifact IDs + metric refs
    rule_id: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    application: Mapped["Application"] = relationship(back_populates="claims")


class Brief(Base):
    """Generated candidate brief."""

    __tablename__ = "briefs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    application_id: Mapped[str] = mapped_column(String(36), ForeignKey("applications.id"), nullable=False)
    brief_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    # Relationships
    application: Mapped["Application"] = relationship(back_populates="briefs")


class AuditLog(Base):
    """Append-only audit log with hash chain."""

    __tablename__ = "audit_log"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_id)
    org_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("orgs.id", ondelete="SET NULL"))
    actor_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"))
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    event_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(default=utc_now)

    __table_args__ = (
        Index("ix_audit_log_org_id", "org_id"),
        Index("ix_audit_log_event_type", "event_type"),
        Index("ix_audit_log_created_at", "created_at"),
    )
