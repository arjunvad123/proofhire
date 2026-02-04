"""LLM output schemas - all LLM outputs must conform to these."""

from pydantic import BaseModel, Field


class WriteupTag(BaseModel):
    """A tag extracted from a writeup.

    Tags represent factual observations about the writeup content,
    NOT quality judgments. Each tag must have a citation.
    """

    tag: str  # e.g., "root_cause_identified", "tradeoff_discussed"
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_quote: str  # Direct quote from writeup
    start_char: int | None = None  # Position in original text
    end_char: int | None = None


class WriteupTaggingOutput(BaseModel):
    """Output schema for writeup tagging.

    The LLM identifies specific topics/elements in the writeup,
    NOT quality assessments.
    """

    tags: list[WriteupTag]
    word_count: int
    sections_identified: list[str]


class WriteupSummaryOutput(BaseModel):
    """Output schema for writeup summarization."""

    summary: str = Field(max_length=500)
    key_points: list[str] = Field(max_length=5)
    technical_depth: str  # "shallow", "moderate", "deep"


class InterviewQuestion(BaseModel):
    """A suggested interview question."""

    question: str
    rationale: str  # Why this question is relevant
    dimension: str  # Which dimension it probes


class InterviewQuestionsOutput(BaseModel):
    """Output schema for interview question generation."""

    questions: list[InterviewQuestion] = Field(max_length=10)
