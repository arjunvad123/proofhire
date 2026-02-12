"""
Onboarding Import Service.

Imports existing onboarding data (job description, company info, etc.)
into organization profiles.
"""

import json
import logging
import re
from typing import Any

from app.services.llm import LLMService

logger = logging.getLogger(__name__)


class OnboardingImporter:
    """Service to import and parse onboarding data."""

    def __init__(self, llm_service: LLMService | None = None):
        self.llm = llm_service or LLMService()

    async def parse_job_description(
        self, job_description: str
    ) -> dict[str, Any]:
        """
        Parse a job description to extract company and role context.

        Args:
            job_description: The job description text

        Returns:
            Dictionary with extracted fields
        """
        prompt = f"""Analyze this job description and extract company context information.

Job Description:
{job_description}

Extract the following information (leave empty if not mentioned):
- product_description: What does the company build/do?
- company_stage: seed, series-a, series-b, etc.
- tech_stack: List of technologies/tools mentioned
- role_requirements: Key skills/requirements mentioned
- company_values: Any cultural values mentioned

Respond with ONLY valid JSON, no markdown:
{{"product_description": "...", "company_stage": "...", "tech_stack": [...], ...}}
"""

        response = await self.llm.complete(prompt)

        try:
            # Parse JSON from response
            text = response.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(
                f"Failed to parse job description extraction: {response[:200]}"
            )
            return {}

    def parse_company_size(self, company_size_str: str | int) -> int | None:
        """
        Parse company size from string or int.

        Examples:
            "15 people" -> 15
            "10-20" -> 15 (midpoint)
            "50+" -> 50
            15 -> 15

        Args:
            company_size_str: String or int representing company size

        Returns:
            Integer company size or None if cannot parse
        """
        if isinstance(company_size_str, int):
            return company_size_str

        if not isinstance(company_size_str, str):
            return None

        # Try to extract number
        numbers = re.findall(r"\d+", company_size_str)

        if not numbers:
            return None

        # If range like "10-20", take midpoint
        if len(numbers) >= 2:
            return (int(numbers[0]) + int(numbers[1])) // 2

        # Single number
        return int(numbers[0])

    def parse_location(self, location_str: str) -> str:
        """
        Normalize location string.

        Examples:
            "San Francisco" -> "San Francisco, CA"
            "sf" -> "San Francisco, CA"
            "New York, NY" -> "New York, NY"

        Args:
            location_str: Raw location string

        Returns:
            Normalized location string
        """
        if not location_str:
            return ""

        # Simple normalization
        location_lower = location_str.lower().strip()

        # Common abbreviations
        location_map = {
            "sf": "San Francisco, CA",
            "san francisco": "San Francisco, CA",
            "bay area": "San Francisco, CA",
            "nyc": "New York, NY",
            "new york": "New York, NY",
            "la": "Los Angeles, CA",
            "los angeles": "Los Angeles, CA",
            "boston": "Boston, MA",
            "seattle": "Seattle, WA",
            "austin": "Austin, TX",
            "chicago": "Chicago, IL",
            "miami": "Miami, FL",
        }

        return location_map.get(location_lower, location_str)

    async def import_from_structured_data(
        self,
        job_description: str | None = None,
        company_name: str | None = None,
        company_hq_location: str | None = None,
        company_size: str | int | None = None,
        tech_stack: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Import onboarding data from structured inputs.

        Args:
            job_description: Job description text
            company_name: Company name
            company_hq_location: HQ location
            company_size: Company size (int or string)
            tech_stack: List of technologies

        Returns:
            Dictionary of normalized profile data
        """
        profile_data: dict[str, Any] = {}

        # Parse job description if provided
        if job_description:
            jd_data = await self.parse_job_description(job_description)
            profile_data.update(jd_data)

        # Override with explicit values
        if company_name:
            profile_data["company_name"] = company_name

        if company_hq_location:
            profile_data["company_hq_location"] = self.parse_location(
                company_hq_location
            )

        if company_size is not None:
            parsed_size = self.parse_company_size(company_size)
            if parsed_size:
                profile_data["company_size"] = parsed_size

        if tech_stack:
            # Merge with tech stack from job description
            existing_stack = set(profile_data.get("tech_stack", []))
            existing_stack.update(tech_stack)
            profile_data["tech_stack"] = list(existing_stack)

        return profile_data

    async def extract_hiring_priorities(
        self, job_description: str
    ) -> list[str]:
        """
        Extract hiring priorities from job description.

        Args:
            job_description: The job description text

        Returns:
            List of hiring priorities
        """
        prompt = f"""Analyze this job description and extract the TOP 3 hiring priorities.

Job Description:
{job_description}

What are the 3 most important things this company is looking for in candidates?
Focus on:
- Specific skills/expertise
- Background/experience
- Cultural fit indicators
- Educational background

Respond with ONLY a JSON array of 3 strings:
["priority 1", "priority 2", "priority 3"]
"""

        response = await self.llm.complete(prompt)

        try:
            text = response.strip()
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            return json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse priorities: {response[:200]}")
            return []
