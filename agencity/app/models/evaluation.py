"""
Evaluated Candidate - the honest assessment.

Key principle: NO CLAIMS WE CAN'T VERIFY.
We separate known facts from observed signals from unknowns.
"""

from pydantic import BaseModel, Field

from app.models.candidate import CandidateData


class EvaluatedCandidate(BaseModel):
    """
    A candidate with honest evaluation against a blueprint.

    This is what we show to founders - transparent about
    what we know vs. what they'll need to verify.
    """

    # The raw data
    candidate: CandidateData

    # Known Facts - Verifiable from the data
    # Examples: "UCSD CS 2026", "Member of Triton AI club"
    known_facts: list[str] = Field(default_factory=list)

    # Observed Signals - What we can infer from behavior
    # Examples: "2 ML projects on GitHub", "Won hackathon prize"
    observed_signals: list[str] = Field(default_factory=list)

    # Unknown - What we CAN'T verify from this data
    # Examples: "Actual skill depth", "Work style", "Interest in startups"
    unknown: list[str] = Field(default_factory=list)

    # Why Consider - Connection to what founder described
    why_consider: str = ""

    # Next Step - What to ask/verify in first conversation
    next_step: str = ""

    # Internal ranking (NOT shown as "match score")
    relevance_score: float = Field(
        default=0.0,
        description="Internal score for ranking. Never shown to users."
    )

    def summary_for_display(self) -> dict:
        """Format for frontend display."""
        return {
            "name": self.candidate.name,
            "tagline": self._build_tagline(),
            "known_facts": self.known_facts,
            "observed_signals": self.observed_signals,
            "unknown": self.unknown,
            "why_consider": self.why_consider,
            "next_step": self.next_step,
        }

    def _build_tagline(self) -> str:
        """Build a short tagline like 'UCSD · CS Junior'."""
        parts = []
        if self.candidate.school:
            parts.append(self.candidate.school)
        if self.candidate.major:
            parts.append(self.candidate.major)
        if self.candidate.graduation_year:
            # Calculate year (Junior, Senior, etc.)
            from datetime import datetime
            current_year = datetime.now().year
            years_left = self.candidate.graduation_year - current_year
            if years_left <= 0:
                parts.append("Alum")
            elif years_left == 1:
                parts.append("Senior")
            elif years_left == 2:
                parts.append("Junior")
            elif years_left == 3:
                parts.append("Sophomore")
            else:
                parts.append("Freshman")
        return " · ".join(parts) if parts else ""


class Shortlist(BaseModel):
    """A ranked list of evaluated candidates."""

    conversation_id: str
    candidates: list[EvaluatedCandidate]
    search_sources: list[str] = Field(default_factory=list)
    total_searched: int = 0
    generated_at: str = ""

    def top(self, n: int = 5) -> list[EvaluatedCandidate]:
        """Get top N candidates by relevance."""
        sorted_candidates = sorted(
            self.candidates,
            key=lambda c: c.relevance_score,
            reverse=True
        )
        return sorted_candidates[:n]
