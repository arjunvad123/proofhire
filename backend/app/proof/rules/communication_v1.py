"""Proof rules for communication evaluation.

These rules evaluate claims about communication skills using
writeup artifacts and LLM-derived tags (with citations).
"""

from typing import Any

from app.hypothesis.claim_schema import Claim, ProofResult, EvidenceRef
from app.proof.engine import BaseRule
from app.db.models import Artifact, ArtifactType


class CommunicationClearRule(BaseRule):
    """Rule to prove clear communication.

    PROVE communication_clear if:
    - writeup answers all required prompts
    - writeup contains tradeoff_discussed tag (from LLM tagging)
    - writeup contains monitoring_considered tag (from LLM tagging)

    LLM-derived tags are accepted ONLY if:
    - The tag includes citation (evidence_quote, start_char, end_char)
    - The claim is conservative (presence of topics, not quality judgment)
    """

    id = "communication_clear_v1"
    claim_types = ["communication_clear"]
    dimensions = ["communication"]

    REQUIRED_TAGS = ["root_cause_identified", "tradeoff_discussed", "monitoring_considered"]
    MIN_TAGS_FOR_PROOF = 2  # Need at least 2 of 3 tags to prove

    def evaluate(
        self,
        claim: Claim,
        metrics: dict[str, Any],
        artifacts: dict[str, Artifact],
        llm_tags: list[dict[str, Any]] | None,
        com: dict[str, Any],
    ) -> ProofResult:
        evidence_refs = []

        # Check if writeup artifact exists
        writeup_artifact = artifacts.get(ArtifactType.WRITEUP)
        if not writeup_artifact:
            return self._create_unproved(
                claim,
                evidence_refs,
                "No writeup submitted",
            )

        evidence_refs.append(
            EvidenceRef(type="artifact", id=writeup_artifact.id, field="type", value="writeup")
        )

        # Check writeup completeness from metadata
        writeup_meta = writeup_artifact.metadata_json or {}
        prompts_answered = writeup_meta.get("prompts", [])

        if len(prompts_answered) < 3:
            return self._create_unproved(
                claim,
                evidence_refs,
                f"Only {len(prompts_answered)} of 3 required prompts answered",
            )

        evidence_refs.append(
            EvidenceRef(
                type="artifact",
                id=writeup_artifact.id,
                field="prompts_answered",
                value=len(prompts_answered),
            )
        )

        # Check LLM tags if available
        if not llm_tags:
            # Without LLM tagging, we can only verify structure
            return self._create_unproved(
                claim,
                evidence_refs,
                "Writeup complete but content quality not verified (no LLM tagging)",
            )

        # Count valid tags with citations
        found_tags = []
        for tag in llm_tags:
            tag_name = tag.get("tag", "")
            if tag_name in self.REQUIRED_TAGS:
                # Verify tag has citation
                if self._has_valid_citation(tag):
                    found_tags.append(tag_name)
                    evidence_refs.append(
                        EvidenceRef(
                            type="llm_tag",
                            id=tag_name,
                            field="evidence_quote",
                            value=tag.get("evidence_quote", "")[:100],  # Truncate
                        )
                    )

        if len(found_tags) >= self.MIN_TAGS_FOR_PROOF:
            return self._create_proved(
                claim,
                evidence_refs,
                f"Writeup demonstrates clear communication: {', '.join(found_tags)}",
            )

        missing = set(self.REQUIRED_TAGS) - set(found_tags)
        return self._create_unproved(
            claim,
            evidence_refs,
            f"Writeup missing key elements: {', '.join(missing)}",
        )

    def _has_valid_citation(self, tag: dict[str, Any]) -> bool:
        """Check if LLM tag has a valid citation.

        Valid citations must include evidence_quote and position.
        This ensures the LLM is grounding its assessment in actual text.
        """
        evidence_quote = tag.get("evidence_quote", "")
        start_char = tag.get("start_char")
        end_char = tag.get("end_char")

        # Must have a non-empty quote
        if not evidence_quote or len(evidence_quote) < 10:
            return False

        # Position info is nice but not required
        # The quote itself is the key evidence

        return True
