"""Tests for the brief builder."""

import pytest
from datetime import datetime
from unittest.mock import MagicMock
from uuid import uuid4

from app.briefs.brief_builder import BriefBuilder, build_brief
from app.briefs.brief_types import CandidateBrief
from app.hypothesis.claim_schema import Claim, ClaimSubject, ProofResult, EvidenceRef


class TestBriefBuilder:
    """Tests for BriefBuilder."""

    def setup_method(self):
        self.builder = BriefBuilder()

        # Create mock objects
        self.application = MagicMock()
        self.application.id = uuid4()

        self.candidate = MagicMock()
        self.candidate.id = uuid4()
        self.candidate.name = "Test Candidate"

        self.role = MagicMock()
        self.role.id = uuid4()
        self.role.org_id = uuid4()

        self.simulation_run = MagicMock()
        self.simulation_run.simulation_id = "bugfix_v1"
        self.simulation_run.started_at = datetime(2024, 1, 1, 10, 0, 0)
        self.simulation_run.completed_at = datetime(2024, 1, 1, 10, 45, 0)

        self.com = {"pace": "medium", "quality_bar": "medium"}

    def _make_proof_result(self, status: str, claim_type: str) -> ProofResult:
        """Helper to create a proof result."""
        claim = Claim(
            claim_type=claim_type,
            subject=ClaimSubject(candidate_id="cand_123", application_id="app_456"),
            statement=f"Test {claim_type} claim",
            dimensions=["testing_discipline"],
            confidence=0.8,
            evidence_requirements=[],
        )
        return ProofResult(
            claim=claim,
            status=status,
            evidence_refs=[
                EvidenceRef(type="metric", id="tests_passed", field="value", value=True)
            ],
            rule_id=f"{claim_type}_v1",
            reason=f"Test reason for {status}",
        )

    def test_builds_brief_with_proven_claims(self):
        """Should build brief with proven claims."""
        proof_results = [
            self._make_proof_result("PROVED", "added_regression_test"),
            self._make_proof_result("PROVED", "debugging_effective"),
        ]

        brief = self.builder.build(
            application=self.application,
            candidate=self.candidate,
            role=self.role,
            simulation_run=self.simulation_run,
            proof_results=proof_results,
            artifacts=[],
            com=self.com,
        )

        assert isinstance(brief, CandidateBrief)
        assert len(brief.proven_claims) == 2
        assert len(brief.unproven_claims) == 0
        assert brief.proof_rate == 1.0

    def test_builds_brief_with_unproven_claims(self):
        """Should build brief with unproven claims."""
        proof_results = [
            self._make_proof_result("PROVED", "added_regression_test"),
            self._make_proof_result("UNPROVED", "communication_clear"),
        ]

        brief = self.builder.build(
            application=self.application,
            candidate=self.candidate,
            role=self.role,
            simulation_run=self.simulation_run,
            proof_results=proof_results,
            artifacts=[],
            com=self.com,
        )

        assert len(brief.proven_claims) == 1
        assert len(brief.unproven_claims) == 1
        assert brief.proof_rate == 0.5

    def test_computes_time_to_complete(self):
        """Should compute correct time to complete."""
        proof_results = [self._make_proof_result("PROVED", "time_efficient")]

        brief = self.builder.build(
            application=self.application,
            candidate=self.candidate,
            role=self.role,
            simulation_run=self.simulation_run,
            proof_results=proof_results,
            artifacts=[],
            com=self.com,
        )

        # 45 minutes = 2700 seconds
        assert brief.time_to_complete_seconds == 2700

    def test_generates_interview_questions_for_unproven(self):
        """Should generate interview questions for unproven claims."""
        proof_results = [
            self._make_proof_result("UNPROVED", "debugging_effective"),
        ]

        brief = self.builder.build(
            application=self.application,
            candidate=self.candidate,
            role=self.role,
            simulation_run=self.simulation_run,
            proof_results=proof_results,
            artifacts=[],
            com=self.com,
        )

        assert len(brief.suggested_interview_questions) > 0
        assert len(brief.unproven_claims[0].suggested_questions) > 0

    def test_computes_dimensions_coverage(self):
        """Should compute dimensions coverage correctly."""
        proof_results = [
            self._make_proof_result("PROVED", "added_regression_test"),
        ]

        brief = self.builder.build(
            application=self.application,
            candidate=self.candidate,
            role=self.role,
            simulation_run=self.simulation_run,
            proof_results=proof_results,
            artifacts=[],
            com=self.com,
        )

        assert "testing_discipline" in brief.dimensions_covered
        assert brief.dimensions_covered["testing_discipline"] == "proven"

    def test_identifies_risk_flags(self):
        """Should identify risk flags from results."""
        # Set up a longer completion time
        self.simulation_run.started_at = datetime(2024, 1, 1, 10, 0, 0)
        self.simulation_run.completed_at = datetime(2024, 1, 1, 12, 0, 0)  # 2 hours

        proof_results = [
            self._make_proof_result("PROVED", "added_regression_test"),
        ]

        brief = self.builder.build(
            application=self.application,
            candidate=self.candidate,
            role=self.role,
            simulation_run=self.simulation_run,
            proof_results=proof_results,
            artifacts=[],
            com=self.com,
        )

        # Should flag long completion time
        flag_types = [f.flag_type for f in brief.risk_flags]
        assert "long_completion_time" in flag_types


class TestBuildBriefFunction:
    """Tests for build_brief convenience function."""

    def test_builds_brief_via_function(self):
        """Should build brief using convenience function."""
        application = MagicMock()
        application.id = uuid4()

        candidate = MagicMock()
        candidate.id = uuid4()
        candidate.name = "Test"

        role = MagicMock()
        role.id = uuid4()
        role.org_id = uuid4()

        run = MagicMock()
        run.simulation_id = "bugfix_v1"
        run.started_at = datetime.utcnow()
        run.completed_at = datetime.utcnow()

        brief = build_brief(
            application=application,
            candidate=candidate,
            role=role,
            simulation_run=run,
            proof_results=[],
            artifacts=[],
            com={},
        )

        assert isinstance(brief, CandidateBrief)
