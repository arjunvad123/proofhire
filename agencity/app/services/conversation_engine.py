"""
Conversation Engine - Extracts role requirements from natural language
"""

import os
import json
from typing import Optional
from openai import AsyncOpenAI

from app.models.blueprint import RoleBlueprint


class ConversationEngine:
    """
    Simple conversation engine to extract role requirements.

    Uses OpenAI to parse user messages and extract structured role data.
    """

    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY must be set")

        self.client = AsyncOpenAI(api_key=api_key)

    async def extract_role(self, message: str) -> Optional[RoleBlueprint]:
        """
        Extract role requirements from a message.

        Examples:
        - "I need a prompt engineer for my AI startup"
        - "Looking for a backend engineer who knows Python and FastAPI"
        - "Need a senior ML engineer in SF, must know PyTorch"

        Returns:
            RoleBlueprint if requirements are clear, None if need clarification
        """

        system_prompt = """You are a hiring assistant that extracts job requirements from natural language.

Extract these fields from the user's message:
- title: The job title (e.g., "Software Engineer", "Prompt Engineer")
- required_skills: List of must-have skills (e.g., ["Python", "FastAPI"])
- nice_to_have_skills: List of nice-to-have skills
- locations: List of locations (e.g., ["San Francisco", "Remote"])
- seniority: junior, mid, senior, or null

If the message is too vague or missing critical information, return null.

Return ONLY a JSON object with these fields, no additional text.

Examples:

User: "I need a prompt engineer for my AI startup"
{
  "title": "Prompt Engineer",
  "required_skills": [],
  "nice_to_have_skills": [],
  "locations": [],
  "seniority": null
}

User: "Looking for a backend engineer who knows Python and FastAPI, preferably in SF"
{
  "title": "Backend Engineer",
  "required_skills": ["Python", "FastAPI"],
  "nice_to_have_skills": [],
  "locations": ["San Francisco"],
  "seniority": null
}

User: "Need a senior ML engineer, must know PyTorch and transformers"
{
  "title": "ML Engineer",
  "required_skills": ["PyTorch", "transformers"],
  "nice_to_have_skills": [],
  "locations": [],
  "seniority": "senior"
}

User: "just looking around"
null
"""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3,
                max_tokens=500
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON
            if content.lower() == "null":
                return None

            data = json.loads(content)

            # Validate
            if not data.get("title"):
                return None

            return RoleBlueprint(
                title=data["title"],
                required_skills=data.get("required_skills", []),
                nice_to_have_skills=data.get("nice_to_have_skills", []),
                locations=data.get("locations", []),
                seniority=data.get("seniority")
            )

        except Exception as e:
            print(f"Error extracting role: {e}")
            return None

    async def generate_clarifying_question(self, message: str) -> str:
        """
        Generate a clarifying question if role requirements are unclear.
        """

        system_prompt = """You are a helpful hiring assistant. The user mentioned looking for someone but didn't provide enough details.

Ask ONE concise clarifying question to understand what role they're hiring for.

Keep it conversational and friendly. Examples:
- "What role are you hiring for?"
- "What kind of engineer are you looking for?"
- "What skills should this person have?"

Return ONLY the question, no additional text."""

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.7,
                max_tokens=100
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            print(f"Error generating question: {e}")
            return "What role are you hiring for?"
