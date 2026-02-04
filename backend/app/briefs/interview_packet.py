"""Generate interview questions for unproven claims."""

from typing import Any

from app.hypothesis.claim_schema import Claim
from app.logging_config import get_logger

logger = get_logger(__name__)


# Question templates by claim type
QUESTION_TEMPLATES: dict[str, list[str]] = {
    "added_regression_test": [
        "Can you walk me through how you would add a regression test for this bug?",
        "What specific scenarios would you want to cover in a regression test?",
        "How do you decide what edge cases to test when writing regression tests?",
    ],
    "debugging_effective": [
        "Can you explain your debugging process for this issue?",
        "What was the root cause of the bug, and how did you identify it?",
        "What tools or techniques did you use to narrow down the problem?",
    ],
    "testing_discipline": [
        "How do you decide what tests to write when fixing a bug?",
        "What's your approach to balancing test coverage with development speed?",
        "Can you describe a time when thorough testing caught an issue before production?",
    ],
    "time_efficient": [
        "Walk me through your approach when you first saw this problem.",
        "How do you prioritize what to investigate first when debugging?",
        "What strategies do you use to avoid rabbit holes when debugging?",
    ],
    "handles_edge_cases": [
        "What edge cases did you consider when implementing your fix?",
        "How do you systematically identify edge cases in a problem?",
        "Can you describe an edge case you've encountered that was particularly tricky?",
    ],
    "communication_clear": [
        "How do you approach documenting your technical decisions?",
        "Can you explain the tradeoffs you considered in your solution?",
        "How would you communicate this fix to a teammate unfamiliar with the codebase?",
    ],
}

# Dimension-based follow-up questions
DIMENSION_QUESTIONS: dict[str, list[str]] = {
    "debugging_method": [
        "What's your systematic approach to debugging unfamiliar code?",
        "How do you use logging and breakpoints effectively?",
    ],
    "testing_discipline": [
        "How do you maintain test quality in a fast-moving codebase?",
        "What's your view on test-driven development?",
    ],
    "correctness": [
        "How do you verify that a fix is complete and doesn't introduce regressions?",
        "What code review practices help you catch correctness issues?",
    ],
    "shipping_speed": [
        "How do you balance thoroughness with shipping quickly?",
        "What techniques help you work efficiently under time pressure?",
    ],
    "communication": [
        "How do you document decisions for future engineers?",
        "What makes technical writing effective in your experience?",
    ],
}


def generate_interview_questions(
    claim: Claim,
    reason: str,
    com: dict[str, Any],
) -> list[str]:
    """Generate interview questions for an unproven claim.

    Args:
        claim: The unproven claim
        reason: Why the claim couldn't be proven
        com: Company Operating Model for context

    Returns:
        List of suggested interview questions
    """
    questions = []

    # Get claim-specific questions
    claim_questions = QUESTION_TEMPLATES.get(claim.claim_type, [])
    questions.extend(claim_questions[:2])  # Take top 2

    # Get dimension-specific questions
    for dimension in claim.dimensions:
        dim_questions = DIMENSION_QUESTIONS.get(dimension, [])
        if dim_questions:
            questions.append(dim_questions[0])

    # Add context-aware question based on reason
    context_question = _generate_context_question(claim, reason, com)
    if context_question:
        questions.append(context_question)

    # Deduplicate while preserving order
    seen = set()
    unique_questions = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique_questions.append(q)

    return unique_questions[:4]  # Return max 4 questions


def _generate_context_question(
    claim: Claim,
    reason: str,
    com: dict[str, Any],
) -> str | None:
    """Generate a question based on specific context."""
    # Adjust question based on company pace
    pace = com.get("pace", "medium")

    if "time" in reason.lower() or "timeout" in reason.lower():
        if pace == "high":
            return "In a fast-paced environment, how do you optimize your debugging workflow?"
        else:
            return "What factors affected your completion time on this task?"

    if "missing" in reason.lower():
        return "What additional information would help you complete this aspect of the task?"

    if "skipped" in reason.lower():
        return "What led you to skip certain tests, and how would you approach this differently?"

    return None


def generate_full_interview_packet(
    unproven_claims: list[tuple[Claim, str]],  # (claim, reason) pairs
    com: dict[str, Any],
    max_questions: int = 10,
) -> list[str]:
    """Generate a complete interview packet from all unproven claims.

    Args:
        unproven_claims: List of (claim, reason) tuples
        com: Company Operating Model
        max_questions: Maximum questions to include

    Returns:
        Deduplicated list of interview questions
    """
    all_questions = []

    for claim, reason in unproven_claims:
        questions = generate_interview_questions(claim, reason, com)
        all_questions.extend(questions)

    # Deduplicate
    seen = set()
    unique = []
    for q in all_questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    return unique[:max_questions]
