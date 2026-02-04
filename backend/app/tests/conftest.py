"""Pytest configuration and fixtures."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from app.hypothesis.claim_schema import Claim, ClaimSubject


@pytest.fixture
def sample_claim():
    """Create a sample claim for testing."""
    return Claim(
        claim_type="added_regression_test",
        subject=ClaimSubject(candidate_id="cand_123", application_id="app_456"),
        statement="Candidate added a regression test",
        dimensions=["testing_discipline"],
        confidence=0.8,
        evidence_requirements=["tests_passed", "test_added"],
    )


@pytest.fixture
def sample_com():
    """Create a sample Company Operating Model."""
    return {
        "pace": "medium",
        "quality_bar": "medium",
        "ambiguity_tolerance": "medium",
        "priorities": ["debugging", "testing"],
    }


@pytest.fixture
def mock_application():
    """Create a mock application."""
    app = MagicMock()
    app.id = uuid4()
    app.role_id = uuid4()
    app.candidate_id = uuid4()
    app.status = "simulation_completed"
    return app


@pytest.fixture
def mock_candidate():
    """Create a mock candidate."""
    candidate = MagicMock()
    candidate.id = uuid4()
    candidate.name = "Test Candidate"
    candidate.email = "test@example.com"
    return candidate


@pytest.fixture
def mock_role():
    """Create a mock role."""
    role = MagicMock()
    role.id = uuid4()
    role.org_id = uuid4()
    role.title = "Backend Engineer"
    return role


@pytest.fixture
def mock_simulation_run():
    """Create a mock simulation run."""
    run = MagicMock()
    run.id = uuid4()
    run.simulation_id = "bugfix_v1"
    run.status = "completed"
    run.started_at = datetime(2024, 1, 1, 10, 0, 0)
    run.completed_at = datetime(2024, 1, 1, 10, 45, 0)
    return run
