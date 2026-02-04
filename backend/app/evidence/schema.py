"""Evidence artifact schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ArtifactMetadata(BaseModel):
    """Metadata for a stored artifact."""

    run_id: str
    artifact_type: str
    s3_key: str
    content_type: str
    size_bytes: int
    sha256_hash: str
    created_at: datetime


class DiffArtifact(BaseModel):
    """Parsed diff artifact."""

    files_changed: list[str]
    lines_added: int
    lines_removed: int
    test_files_changed: list[str]
    raw_patch: str


class TestLogArtifact(BaseModel):
    """Parsed test log artifact."""

    tests_passed: bool
    total_tests: int
    passed_count: int
    failed_count: int
    skipped_count: int
    failed_test_names: list[str]
    error_messages: list[str]
    duration_seconds: float


class CoverageArtifact(BaseModel):
    """Parsed coverage artifact."""

    line_coverage_percent: float
    branch_coverage_percent: float | None
    lines_covered: int
    lines_total: int
    uncovered_lines: dict[str, list[int]]  # file -> line numbers


class WriteupArtifact(BaseModel):
    """Parsed writeup artifact."""

    raw_text: str
    word_count: int
    prompts_answered: list[str]
    sections: dict[str, str]


class MetricsBundle(BaseModel):
    """Bundle of all extracted metrics from a run."""

    run_id: str

    # Test results
    tests_passed: bool = False
    total_tests: int = 0
    failed_tests_count: int = 0
    failed_tests_before: int = 0  # If initial state had failing tests
    test_duration_seconds: float = 0

    # Code changes
    files_changed: int = 0
    lines_added: int = 0
    lines_removed: int = 0
    test_files_changed: int = 0
    test_added: bool = False
    tests_added_count: int = 0
    skipped_tests_added: int = 0

    # Coverage
    coverage_percent: float | None = None
    coverage_delta: float | None = None  # Change from baseline

    # Timing
    time_to_green_seconds: float | None = None
    submission_time: datetime | None = None

    # Writeup
    writeup_word_count: int = 0
    writeup_prompts_answered: int = 0

    # Raw data for rules to inspect
    raw_metrics: dict[str, Any] = Field(default_factory=dict)
