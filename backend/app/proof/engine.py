"""Proof engine - evaluates claims against evidence using rules.

The proof engine is the core of the fail-closed guarantee:
- If a claim cannot be proven by rules over evidence, it is marked UNPROVED
- UNPROVED claims are converted to interview questions, not hidden
- All proof attempts are logged for audit
"""

from typing import Any, Protocol, runtime_checkable
from abc import ABC, abstractmethod

from app.hypothesis.claim_schema import Claim, ProofResult, EvidenceRef
from app.db.models import Metric, Artifact, ArtifactType
from app.logging_config import get_logger

logger = get_logger(__name__)


@runtime_checkable
class Rule(Protocol):
    """Protocol for proof rules."""

    id: str
    claim_types: list[str]
    dimensions: list[str]

    def evaluate(
        self,
        claim: Claim,
        metrics: dict[str, Any],
        artifacts: dict[str, Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        """Evaluate the claim against evidence.

        Args:
            claim: The claim to evaluate
            metrics: Dict of metric name -> value
            artifacts: Dict of artifact type -> artifact
            llm_tags: Optional LLM-extracted tags from writeup
            com: Company Operating Model

        Returns:
            ProofResult with PROVED or UNPROVED status
        """
        ...


class BaseRule(ABC):
    """Base class for proof rules."""

    id: str
    claim_types: list[str]
    dimensions: list[str]

    @abstractmethod
    def evaluate(
        self,
        claim: Claim,
        metrics: dict[str, Any],
        artifacts: dict[str, Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        """Evaluate the claim against evidence."""
        pass

    def _create_proved(
        self,
        claim: Claim,
        evidence_refs: list[EvidenceRef],
        reason: str,
    ) -> ProofResult:
        """Helper to create a PROVED result."""
        return ProofResult(
            claim=claim,
            status="PROVED",
            evidence_refs=evidence_refs,
            rule_id=self.id,
            reason=reason,
        )

    def _create_unproved(
        self,
        claim: Claim,
        evidence_refs: list[EvidenceRef],
        reason: str,
    ) -> ProofResult:
        """Helper to create an UNPROVED result."""
        return ProofResult(
            claim=claim,
            status="UNPROVED",
            evidence_refs=evidence_refs,
            rule_id=self.id,
            reason=reason,
        )


class ProofEngine:
    """Main proof engine that coordinates rule evaluation.

    The engine maintains a registry of rules and applies the appropriate
    rules to each claim type.
    """

    def __init__(self):
        self._rules: dict[str, list[Rule]] = {}

    def register_rule(self, rule: Rule) -> None:
        """Register a rule with the engine."""
        for claim_type in rule.claim_types:
            if claim_type not in self._rules:
                self._rules[claim_type] = []
            self._rules[claim_type].append(rule)
            logger.info(f"Registered rule {rule.id} for claim type {claim_type}")

    def evaluate_claim(
        self,
        claim: Claim,
        metrics: list[Metric],
        artifacts: list[Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        """Evaluate a single claim.

        If multiple rules apply, the claim is PROVED if ANY rule proves it.
        """
        # Convert metrics and artifacts to dicts
        metrics_dict = {}
        for m in metrics:
            if m.value_float is not None:
                metrics_dict[m.name] = m.value_float
            elif m.value_bool is not None:
                metrics_dict[m.name] = m.value_bool
            elif m.value_text is not None:
                metrics_dict[m.name] = m.value_text

        artifacts_dict = {a.type: a for a in artifacts}

        # Get applicable rules
        rules = self._rules.get(claim.claim_type, [])

        if not rules:
            logger.warning(f"No rules registered for claim type: {claim.claim_type}")
            return ProofResult(
                claim=claim,
                status="UNPROVED",
                evidence_refs=[],
                rule_id="no_rule",
                reason=f"No rule exists to evaluate claim type: {claim.claim_type}",
            )

        # Try each rule until one proves the claim
        all_evidence_refs = []
        reasons = []

        for rule in rules:
            try:
                result = rule.evaluate(claim, metrics_dict, artifacts_dict, llm_tags, com)
                all_evidence_refs.extend(result.evidence_refs)

                if result.status == "PROVED":
                    logger.info(
                        f"Claim {claim.claim_type} PROVED by rule {rule.id}",
                        claim_type=claim.claim_type,
                        rule_id=rule.id,
                    )
                    return result

                reasons.append(f"{rule.id}: {result.reason}")

            except Exception as e:
                logger.error(
                    f"Error evaluating rule {rule.id}: {e}",
                    rule_id=rule.id,
                    error=str(e),
                )
                reasons.append(f"{rule.id}: Error - {str(e)}")

        # No rule proved the claim
        logger.info(
            f"Claim {claim.claim_type} UNPROVED - no rule succeeded",
            claim_type=claim.claim_type,
            attempted_rules=[r.id for r in rules],
        )

        return ProofResult(
            claim=claim,
            status="UNPROVED",
            evidence_refs=all_evidence_refs,
            rule_id=rules[0].id if rules else "no_rule",
            reason="; ".join(reasons),
        )

    def evaluate_all(
        self,
        claims: list[Claim],
        metrics: list[Metric],
        artifacts: list[Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> list[ProofResult]:
        """Evaluate all claims and return results."""
        results = []
        for claim in claims:
            result = self.evaluate_claim(claim, metrics, artifacts, llm_tags, com)
            results.append(result)
        return results


# Global engine instance
_engine: ProofEngine | None = None


def get_proof_engine() -> ProofEngine:
    """Get the global proof engine instance.

    Lazily initializes and registers all rules.
    """
    global _engine

    if _engine is None:
        _engine = ProofEngine()

        # Import and register rules
        from app.proof.rules.backend_engineer_v1 import (
            AddedRegressionTestRule,
            DebuggingEffectiveRule,
            TestingDisciplineRule,
            TimeEfficientRule,
            HandlesEdgeCasesRule,
        )
        from app.proof.rules.communication_v1 import CommunicationClearRule

        # Register all rules
        _engine.register_rule(AddedRegressionTestRule())
        _engine.register_rule(DebuggingEffectiveRule())
        _engine.register_rule(TestingDisciplineRule())
        _engine.register_rule(TimeEfficientRule())
        _engine.register_rule(HandlesEdgeCasesRule())
        _engine.register_rule(CommunicationClearRule())

    return _engine
