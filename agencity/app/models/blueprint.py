"""
Role Blueprint - the structured output from intake conversation.

This captures what the founder actually needs, not just job title keywords.
"""

from pydantic import BaseModel, Field


class RoleBlueprint(BaseModel):
    """
    Structured representation of what a founder is looking for.

    Built through conversation - we ask smart follow-up questions
    until we have enough context to search effectively.
    """

    # Core identity
    role_title: str = Field(
        ...,
        description="The role they're hiring for (e.g., 'Prompt Engineer')"
    )

    # Context
    company_context: str = Field(
        ...,
        description="What the startup does, stage, team size"
    )
    specific_work: str = Field(
        ...,
        description="What this person will actually build/do day-to-day"
    )

    # Success criteria
    success_criteria: str = Field(
        ...,
        description="What success looks like by day 60"
    )

    # Requirements
    must_haves: list[str] = Field(
        default_factory=list,
        description="Non-negotiable requirements"
    )
    nice_to_haves: list[str] = Field(
        default_factory=list,
        description="Preferences, not requirements"
    )
    avoid: list[str] = Field(
        default_factory=list,
        description="Red flags or anti-patterns"
    )

    # Preferences
    location_preferences: list[str] = Field(
        default_factory=list,
        description="Schools, cities, remote preferences"
    )

    # Calibration
    calibration_examples: list[str] = Field(
        default_factory=list,
        description="Examples of good/bad hires or patterns that worked"
    )

    def is_complete(self) -> bool:
        """Check if blueprint has enough context to search."""
        required_fields = [
            self.role_title,
            self.company_context,
            self.specific_work,
            self.success_criteria,
        ]
        return all(
            field and len(field) >= 10
            for field in required_fields
        )

    def to_search_query(self) -> str:
        """Convert blueprint to a search-friendly query string."""
        parts = [
            self.role_title,
            self.specific_work,
            " ".join(self.must_haves),
        ]
        return " ".join(parts)

    def to_embedding_text(self) -> str:
        """Convert blueprint to text for embedding/semantic search."""
        return f"""
Role: {self.role_title}
Company: {self.company_context}
Work: {self.specific_work}
Success: {self.success_criteria}
Must have: {', '.join(self.must_haves)}
Nice to have: {', '.join(self.nice_to_haves)}
Avoid: {', '.join(self.avoid)}
Location: {', '.join(self.location_preferences)}
""".strip()
