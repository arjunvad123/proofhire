"""Tests for the proof engine."""

import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from app.hypothesis.claim_schema import Claim, ClaimSubject
from app.proof.engine import ProofEngine, get_proof_engine
from app.proof.rules.backend_engineer_v1 import (
    AddedRegressionTestRule,
    DebuggingEffectiveRule,
    TestingDisciplineRule,
)
from app.db.models import Metric, Artifact, ArtifactType


def make_subject():
    """Helper to create a valid ClaimSubject."""
    return ClaimSubject(candidate_id="cand_123", application_id="app_456")


class TestAddedRegressionTestRule:
    """Tests for AddedRegressionTestRule."""

    def setup_method(self):
        self.rule = AddedRegressionTestRule()
        self.claim = Claim(
            claim_type="added_regression_test",
            subject=make_subject(),
            statement="Candidate added a regression test",
            dimensions=["testing_discipline"],
            confidence=0.8,
            evidence_requirements=["tests_passed", "test_added"],
        )
        self.com = {"pace": "medium", "quality_bar": "medium"}

    def test_proves_when_tests_passed_and_test_added(self):
        """Should prove when tests pass and test_added is True."""
        metrics = {"tests_passed": True, "test_added": True}
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "PROVED"
        assert "regression test" in result.reason.lower()

    def test_proves_when_test_files_changed_and_count_increased(self):
        """Should prove when test files changed and tests added."""
        metrics = {
            "tests_passed": True,
            "test_added": False,
            "test_files_changed": 1,
            "tests_added_count": 2,
        }
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "PROVED"
        assert "added 2 test" in result.reason.lower()

    def test_unproves_when_tests_not_passed(self):
        """Should not prove when tests didn't pass."""
        metrics = {"tests_passed": False, "test_added": True}
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "UNPROVED"
        assert "did not pass" in result.reason.lower()

    def test_unproves_when_no_tests_added(self):
        """Should not prove when no tests were added."""
        metrics = {"tests_passed": True, "test_added": False}
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "UNPROVED"


class TestDebuggingEffectiveRule:
    """Tests for DebuggingEffectiveRule."""

    def setup_method(self):
        self.rule = DebuggingEffectiveRule()
        self.claim = Claim(
            claim_type="debugging_effective",
            subject=make_subject(),
            statement="Candidate demonstrated effective debugging",
            dimensions=["debugging_method"],
            confidence=0.8,
            evidence_requirements=["tests_passed", "root_cause_identified"],
        )
        self.com = {"pace": "medium", "quality_bar": "medium"}

    def test_proves_with_root_cause_tag(self):
        """Should prove when tests pass and root cause identified."""
        metrics = {"tests_passed": True}
        artifacts = {}
        llm_tags = [
            {
                "tag": "root_cause_identified",
                "evidence_quote": "The bug was caused by off-by-one error",
            }
        ]

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "PROVED"
        assert "root cause" in result.reason.lower()

    def test_proves_when_failed_tests_fixed(self):
        """Should prove when failing tests were fixed."""
        metrics = {"tests_passed": True, "failed_tests_before": 3}
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "PROVED"
        assert "fixed failing tests" in result.reason.lower()

    def test_unproves_when_tests_fail(self):
        """Should not prove when tests still fail."""
        metrics = {"tests_passed": False}
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "UNPROVED"
        assert "bug was not fixed" in result.reason.lower()


class TestTestingDisciplineRule:
    """Tests for TestingDisciplineRule."""

    def setup_method(self):
        self.rule = TestingDisciplineRule()
        self.claim = Claim(
            claim_type="testing_discipline",
            subject=make_subject(),
            statement="Candidate showed good testing discipline",
            dimensions=["testing_discipline"],
            confidence=0.8,
            evidence_requirements=["tests_added_count"],
        )
        self.com = {"pace": "medium", "quality_bar": "medium"}

    def test_proves_when_tests_added(self):
        """Should prove when tests were added."""
        metrics = {"tests_added_count": 2, "skipped_tests_added": 0}
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "PROVED"
        assert "added 2 test" in result.reason.lower()

    def test_unproves_when_skipped_tests_added(self):
        """Should not prove when skipped tests were added."""
        metrics = {"tests_added_count": 2, "skipped_tests_added": 1}
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "UNPROVED"
        assert "skipped" in result.reason.lower()

    def test_unproves_when_coverage_drops_too_much(self):
        """Should not prove when coverage drops significantly."""
        metrics = {
            "tests_added_count": 0,
            "skipped_tests_added": 0,
            "coverage_delta": -15,
        }
        artifacts = {}
        llm_tags = None

        result = self.rule.evaluate(
            self.claim, metrics, artifacts, llm_tags, self.com
        )

        assert result.status == "UNPROVED"


class TestProofEngine:
    """Tests for ProofEngine."""

    def test_evaluates_claim_with_matching_rule(self):
        """Should evaluate claim when matching rule exists."""
        engine = ProofEngine()
        engine.register_rule(AddedRegressionTestRule())

        claim = Claim(
            claim_type="added_regression_test",
            subject=make_subject(),
            statement="Test claim",
            dimensions=["testing_discipline"],
            confidence=0.8,
            evidence_requirements=[],
        )

        # Create metric mocks with correct attribute structure
        metric1 = MagicMock()
        metric1.name = "tests_passed"
        metric1.value_bool = True
        metric1.value_float = None
        metric1.value_text = None

        metric2 = MagicMock()
        metric2.name = "test_added"
        metric2.value_bool = True
        metric2.value_float = None
        metric2.value_text = None

        metrics = [metric1, metric2]

        result = engine.evaluate_claim(
            claim=claim,
            metrics=metrics,
            artifacts=[],
            llm_tags=None,
            com={"pace": "medium"},
        )

        assert result.status == "PROVED"

    def test_returns_unproved_when_no_rule_matches(self):
        """Should return UNPROVED when no rule exists for claim type."""
        engine = ProofEngine()

        claim = Claim(
            claim_type="unknown_claim_type",
            subject=make_subject(),
            statement="Test claim",
            dimensions=["unknown"],
            confidence=0.8,
            evidence_requirements=[],
        )

        result = engine.evaluate_claim(
            claim=claim,
            metrics=[],
            artifacts=[],
            llm_tags=None,
            com={},
        )

        assert result.status == "UNPROVED"
        assert "no rule exists" in result.reason.lower()

    def test_get_proof_engine_returns_singleton(self):
        """Should return the same engine instance."""
        engine1 = get_proof_engine()
        engine2 = get_proof_engine()

        assert engine1 is engine2
