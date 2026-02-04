"""Role Spec Interview question definitions."""

from typing import Any
from pydantic import BaseModel


class InterviewQuestion(BaseModel):
    """A single interview question."""

    id: str
    question: str
    description: str
    type: str  # "choice" | "boolean" | "text"
    options: list[dict[str, str]] | None = None
    required: bool = True


# Role Spec Interview Questions
INTERVIEW_QUESTIONS: list[InterviewQuestion] = [
    InterviewQuestion(
        id="ship_vs_correctness",
        question="What matters more right now: shipping speed or correctness?",
        description="This affects how we weight speed vs quality in evaluations",
        type="choice",
        options=[
            {"value": "ship", "label": "Ship fast - we need to move quickly"},
            {"value": "balanced", "label": "Balanced - both matter equally"},
            {"value": "correctness", "label": "Correctness - quality is paramount"},
        ],
    ),
    InterviewQuestion(
        id="on_call_first_month",
        question="Will this engineer be on-call within the first month?",
        description="This helps us assess operational readiness",
        type="boolean",
    ),
    InterviewQuestion(
        id="has_ci",
        question="Do you have CI/CD pipelines set up?",
        description="Helps us understand your development maturity",
        type="boolean",
    ),
    InterviewQuestion(
        id="has_tests",
        question="Do you have an existing test suite?",
        description="Helps us calibrate testing expectations",
        type="boolean",
    ),
    InterviewQuestion(
        id="biggest_risk",
        question="What's the biggest engineering risk in the next 60 days?",
        description="Helps us understand what skills matter most",
        type="text",
    ),
    InterviewQuestion(
        id="failure_by_day_30",
        question="What would failure look like by day 30 for this hire?",
        description="Helps us understand success criteria",
        type="text",
    ),
]


def get_interview_questions() -> list[dict[str, Any]]:
    """Get the role spec interview questions."""
    return [q.model_dump() for q in INTERVIEW_QUESTIONS]
