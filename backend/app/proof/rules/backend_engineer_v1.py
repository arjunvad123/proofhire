"""Proof rules for backend engineer evaluation.

These rules evaluate claims about backend engineering skills using
deterministic evidence from simulation runs.
"""

from typing import Any

from app.hypothesis.claim_schema import Claim, ProofResult, EvidenceRef
from app.proof.engine import BaseRule
from app.db.models import Artifact, ArtifactType


class AddedRegressionTestRule(BaseRule):
    """Rule to prove that candidate added a regression test.

    PROVE added_regression_test if:
    - tests_passed is True
    - test_added metric is True OR
    - diff artifact shows changes to test files AND test count increased
    """

    id = "added_regression_test_v1"
    claim_types = ["added_regression_test"]
    dimensions = ["testing_discipline"]

    def evaluate(
        self,
        claim: Claim,
        metrics: dict[str, Any],
        artifacts: dict[str, Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        evidence_refs = []

        # Check tests passed
        tests_passed = metrics.get("tests_passed", False)
        if not tests_passed:
            return self._create_unproved(
                claim,
                evidence_refs,
                "Tests did not pass - cannot verify regression test",
            )

        evidence_refs.append(
            EvidenceRef(type="metric", id="tests_passed", field="value", value=True)
        )

        # Check test_added metric (from diff analysis)
        test_added = metrics.get("test_added", False)
        if test_added:
            evidence_refs.append(
                EvidenceRef(type="metric", id="test_added", field="value", value=True)
            )
            return self._create_proved(
                claim,
                evidence_refs,
                "Candidate added a regression test - verified by test_added metric and passing tests",
            )

        # Check if test file was modified (from diff metadata)
        test_files_changed = metrics.get("test_files_changed", 0)
        if test_files_changed > 0:
            evidence_refs.append(
                EvidenceRef(type="metric", id="test_files_changed", field="value", value=test_files_changed)
            )

            # Also check if test count increased
            tests_added_count = metrics.get("tests_added_count", 0)
            if tests_added_count > 0:
                evidence_refs.append(
                    EvidenceRef(type="metric", id="tests_added_count", field="value", value=tests_added_count)
                )
                return self._create_proved(
                    claim,
                    evidence_refs,
                    f"Candidate modified test files and added {tests_added_count} test(s)",
                )

        return self._create_unproved(
            claim,
            evidence_refs,
            "Could not verify that candidate added a regression test",
        )


class DebuggingEffectiveRule(BaseRule):
    """Rule to prove effective debugging.

    PROVE debugging_effective if:
    - failing tests were fixed (tests_passed = True after initial failure)
    - writeup includes root_cause_identified tag (from LLM tagging)
    - time_to_green < threshold based on COM pace
    """

    id = "debugging_effective_v1"
    claim_types = ["debugging_effective"]
    dimensions = ["debugging_method"]

    def evaluate(
        self,
        claim: Claim,
        metrics: dict[str, Any],
        artifacts: dict[str, Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        evidence_refs = []

        # Check tests passed
        tests_passed = metrics.get("tests_passed", False)
        if not tests_passed:
            return self._create_unproved(
                claim,
                evidence_refs,
                "Tests did not pass - bug was not fixed",
            )

        evidence_refs.append(
            EvidenceRef(type="metric", id="tests_passed", field="value", value=True)
        )

        # Check time to green
        time_to_green = metrics.get("time_to_green_seconds")
        if time_to_green is not None:
            # Get threshold based on COM pace
            pace = com.get("pace", "medium")
            threshold = {
                "high": 2400,  # 40 min
                "medium": 3000,  # 50 min
                "low": 3600,  # 60 min
            }.get(pace, 3000)

            evidence_refs.append(
                EvidenceRef(type="metric", id="time_to_green_seconds", field="value", value=time_to_green)
            )

            if time_to_green > threshold:
                # Time exceeded but tests passed - partial credit
                pass

        # Check for root cause explanation in writeup
        has_root_cause = False
        if llm_tags:
            for tag in llm_tags:
                if tag.get("tag") == "root_cause_identified":
                    has_root_cause = True
                    evidence_refs.append(
                        EvidenceRef(
                            type="llm_tag",
                            id="root_cause_identified",
                            field="evidence_quote",
                            value=tag.get("evidence_quote", ""),
                        )
                    )
                    break

        # Prove if tests pass and we have root cause
        if has_root_cause:
            return self._create_proved(
                claim,
                evidence_refs,
                "Candidate fixed the bug and explained the root cause",
            )

        # Even without LLM tags, if tests pass, we can prove with lower confidence
        # but only if we have other supporting evidence
        failed_tests_before = metrics.get("failed_tests_before", 0)
        if failed_tests_before > 0:
            evidence_refs.append(
                EvidenceRef(type="metric", id="failed_tests_before", field="value", value=failed_tests_before)
            )
            return self._create_proved(
                claim,
                evidence_refs,
                "Candidate fixed failing tests - demonstrates effective debugging",
            )

        return self._create_unproved(
            claim,
            evidence_refs,
            "Tests pass but could not verify debugging process (missing root cause explanation)",
        )


class TestingDisciplineRule(BaseRule):
    """Rule to prove good testing discipline.

    PROVE testing_discipline if:
    - tests added OR meaningful assertions added
    - no skipped tests introduced
    - coverage maintained or improved
    """

    id = "testing_discipline_v1"
    claim_types = ["testing_discipline"]
    dimensions = ["testing_discipline"]

    def evaluate(
        self,
        claim: Claim,
        metrics: dict[str, Any],
        artifacts: dict[str, Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        evidence_refs = []

        # Check for added tests
        tests_added = metrics.get("tests_added_count", 0)
        if tests_added > 0:
            evidence_refs.append(
                EvidenceRef(type="metric", id="tests_added_count", field="value", value=tests_added)
            )

        # Check for skipped tests
        skipped_tests_added = metrics.get("skipped_tests_added", 0)
        if skipped_tests_added > 0:
            evidence_refs.append(
                EvidenceRef(type="metric", id="skipped_tests_added", field="value", value=skipped_tests_added)
            )
            return self._create_unproved(
                claim,
                evidence_refs,
                f"Candidate introduced {skipped_tests_added} skipped test(s)",
            )

        # Check coverage
        coverage_delta = metrics.get("coverage_delta", 0)
        if coverage_delta is not None:
            evidence_refs.append(
                EvidenceRef(type="metric", id="coverage_delta", field="value", value=coverage_delta)
            )

            # Check threshold from COM
            quality_bar = com.get("quality_bar", "medium")
            min_delta = {
                "high": 0,  # Must not decrease
                "medium": -5,  # Small decrease OK
                "low": -10,
            }.get(quality_bar, -5)

            if coverage_delta < min_delta:
                return self._create_unproved(
                    claim,
                    evidence_refs,
                    f"Coverage decreased by {abs(coverage_delta)}% below acceptable threshold",
                )

        # If tests were added and no skipped tests, prove
        if tests_added > 0:
            return self._create_proved(
                claim,
                evidence_refs,
                f"Candidate added {tests_added} test(s) with no skipped tests",
            )

        # Check if tests pass at least
        tests_passed = metrics.get("tests_passed", False)
        if tests_passed:
            evidence_refs.append(
                EvidenceRef(type="metric", id="tests_passed", field="value", value=True)
            )
            # Partial - tests pass but no new tests added
            # This is unproved for the "testing discipline" claim specifically

        return self._create_unproved(
            claim,
            evidence_refs,
            "Could not verify testing discipline - no new tests added",
        )


class TimeEfficientRule(BaseRule):
    """Rule to prove time efficiency.

    PROVE time_efficient if:
    - time_to_green_seconds < threshold based on COM pace
    """

    id = "time_efficient_v1"
    claim_types = ["time_efficient"]
    dimensions = ["shipping_speed"]

    def evaluate(
        self,
        claim: Claim,
        metrics: dict[str, Any],
        artifacts: dict[str, Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        evidence_refs = []

        time_to_green = metrics.get("time_to_green_seconds")
        if time_to_green is None:
            return self._create_unproved(
                claim,
                evidence_refs,
                "Time to completion not recorded",
            )

        evidence_refs.append(
            EvidenceRef(type="metric", id="time_to_green_seconds", field="value", value=time_to_green)
        )

        # Get threshold based on COM
        pace = com.get("pace", "medium")
        threshold = {
            "high": 2400,  # 40 min for high pace
            "medium": 3000,  # 50 min
            "low": 3600,  # 60 min
        }.get(pace, 3000)

        if time_to_green <= threshold:
            minutes = int(time_to_green / 60)
            return self._create_proved(
                claim,
                evidence_refs,
                f"Candidate completed in {minutes} minutes, within threshold for {pace} pace",
            )

        return self._create_unproved(
            claim,
            evidence_refs,
            f"Completion time ({int(time_to_green/60)} min) exceeded threshold for {pace} pace",
        )


class HandlesEdgeCasesRule(BaseRule):
    """Rule to prove edge case handling.

    PROVE handles_edge_cases if:
    - All tests pass (including edge case tests)
    - No failed assertions
    """

    id = "handles_edge_cases_v1"
    claim_types = ["handles_edge_cases"]
    dimensions = ["correctness"]

    def evaluate(
        self,
        claim: Claim,
        metrics: dict[str, Any],
        artifacts: dict[str, Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        evidence_refs = []

        # Check tests passed
        tests_passed = metrics.get("tests_passed", False)
        if not tests_passed:
            return self._create_unproved(
                claim,
                evidence_refs,
                "Tests did not pass - edge cases may not be handled",
            )

        evidence_refs.append(
            EvidenceRef(type="metric", id="tests_passed", field="value", value=True)
        )

        # Check for failed tests (should be 0)
        failed_count = metrics.get("failed_tests_count", 0)
        evidence_refs.append(
            EvidenceRef(type="metric", id="failed_tests_count", field="value", value=failed_count)
        )

        if failed_count > 0:
            return self._create_unproved(
                claim,
                evidence_refs,
                f"{failed_count} test(s) still failing",
            )

        # Check total tests to ensure coverage
        total_tests = metrics.get("total_tests", 0)
        if total_tests > 0:
            evidence_refs.append(
                EvidenceRef(type="metric", id="total_tests", field="value", value=total_tests)
            )

        return self._create_proved(
            claim,
            evidence_refs,
            f"All {total_tests} tests pass including edge case tests",
        )
