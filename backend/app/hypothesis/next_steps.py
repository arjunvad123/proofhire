"""Generate next steps (interview questions) for unproven claims."""

from typing import Any
from pydantic import BaseModel

from app.hypothesis.claim_schema import Claim, ProofResult


class InterviewQuestion(BaseModel):
    """A suggested interview question."""

    dimension: str
    question: str
    what_good_looks_like: list[str]
    red_flags: list[str]
    source_claim: str  # The claim type this question addresses


# Question templates by dimension
QUESTION_TEMPLATES = {
    "debugging_method": [
        {
            "question": "Walk me through how you diagnosed the bug in the simulation. What was your debugging process?",
            "what_good_looks_like": [
                "Describes systematic approach (reproduce, isolate, identify, fix)",
                "Mentions specific tools or techniques used",
                "Explains how they verified the fix",
            ],
            "red_flags": [
                "Random trial and error without understanding",
                "Cannot explain their process",
                "Fixed symptom but not root cause",
            ],
        },
        {
            "question": "How would you approach debugging a production issue you've never seen before?",
            "what_good_looks_like": [
                "Starts with logs and metrics",
                "Mentions isolating the problem",
                "Discusses communication with team",
            ],
            "red_flags": [
                "Jumps to code changes without investigation",
                "Doesn't mention monitoring or observability",
                "Cannot describe a systematic process",
            ],
        },
    ],
    "testing_discipline": [
        {
            "question": "What types of tests would you write for this feature and why?",
            "what_good_looks_like": [
                "Distinguishes unit, integration, e2e tests",
                "Explains test pyramid concept",
                "Mentions edge cases and error conditions",
            ],
            "red_flags": [
                "Only mentions happy path",
                "Cannot explain when to use different test types",
                "Doesn't consider maintainability",
            ],
        },
        {
            "question": "Tell me about a time you caught a bug through testing that would have caused a production incident.",
            "what_good_looks_like": [
                "Specific example with details",
                "Explains what the test caught",
                "Discusses how they improved testing after",
            ],
            "red_flags": [
                "Cannot provide a specific example",
                "Testing was an afterthought",
                "Doesn't value testing",
            ],
        },
    ],
    "communication": [
        {
            "question": "How would you explain a complex technical decision to a non-technical stakeholder?",
            "what_good_looks_like": [
                "Uses analogies and simplifications",
                "Focuses on business impact",
                "Checks for understanding",
            ],
            "red_flags": [
                "Uses excessive jargon",
                "Cannot simplify concepts",
                "Gets frustrated with the exercise",
            ],
        },
        {
            "question": "Describe a time you had to push back on a requirement. How did you handle it?",
            "what_good_looks_like": [
                "Respectful but firm",
                "Provided alternatives",
                "Focused on trade-offs",
            ],
            "red_flags": [
                "Always says yes or always says no",
                "Confrontational approach",
                "Cannot articulate reasoning",
            ],
        },
    ],
    "shipping_speed": [
        {
            "question": "How do you decide when something is 'good enough' to ship?",
            "what_good_looks_like": [
                "Balances quality and speed consciously",
                "Mentions feature flags or incremental rollout",
                "Considers reversibility of decisions",
            ],
            "red_flags": [
                "Ships without any quality bar",
                "Perfectionistic to the point of not shipping",
                "Cannot articulate trade-offs",
            ],
        },
    ],
    "correctness": [
        {
            "question": "How do you ensure your code handles edge cases correctly?",
            "what_good_looks_like": [
                "Thinks about boundary conditions",
                "Considers null/empty/error states",
                "Writes tests for edge cases",
            ],
            "red_flags": [
                "Only considers happy path",
                "Relies entirely on QA to find issues",
                "Cannot identify edge cases in examples",
            ],
        },
    ],
}


def generate_interview_questions(
    unproven_claims: list[ProofResult],
    com: dict[str, Any],
) -> list[InterviewQuestion]:
    """Generate interview questions for unproven claims.

    Args:
        unproven_claims: List of claims that were not proven
        com: Company Operating Model for context

    Returns:
        List of suggested interview questions
    """
    questions = []
    seen_dimensions = set()

    for result in unproven_claims:
        for dimension in result.claim.dimensions:
            if dimension in seen_dimensions:
                continue

            templates = QUESTION_TEMPLATES.get(dimension, [])
            if templates:
                # Pick the first template (could be smarter based on COM)
                template = templates[0]
                questions.append(
                    InterviewQuestion(
                        dimension=dimension,
                        question=template["question"],
                        what_good_looks_like=template["what_good_looks_like"],
                        red_flags=template["red_flags"],
                        source_claim=result.claim.claim_type,
                    )
                )
                seen_dimensions.add(dimension)

    return questions


def generate_micro_task(
    unproven_claim: ProofResult,
    com: dict[str, Any],
) -> dict[str, Any] | None:
    """Generate a micro-task (15-min follow-up) for an unproven claim.

    This is for v1.5+ - currently returns None.
    """
    # TODO: Implement micro-task generation
    return None
