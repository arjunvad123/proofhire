"""
Organization Profiles Database Service - REST API Edition

Uses Supabase REST API (no DATABASE_URL password needed!)
Replaces SQLAlchemy-based ProfileManager with REST API calls.
"""

import logging
import uuid
from typing import Any, Optional

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class OrgProfilesDBService:
    """
    Service for managing organization profiles via Supabase REST API.

    This replaces the SQLAlchemy-based approach with pure REST API calls.
    """

    def __init__(self):
        self.base_url = settings.supabase_url
        self.api_key = settings.supabase_key
        self.headers = {
            "apikey": self.api_key,
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",  # Return created/updated records
        }

    async def _request(
        self,
        method: str,
        table: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
    ) -> list[dict] | dict | None:
        """Make a request to Supabase REST API."""
        url = f"{self.base_url}/rest/v1/{table}"

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=json_data,
                    timeout=30.0,
                )
                response.raise_for_status()

                # Handle different response types
                if response.status_code == 204:  # No content
                    return None

                result = response.json()
                return result if result else None

            except httpx.HTTPError as e:
                logger.error(f"Supabase request failed: {e}")
                raise

    # ========================================================================
    # Organization Profile Operations
    # ========================================================================

    async def get_or_create_profile(
        self,
        slack_workspace_id: str,
        slack_workspace_name: str | None = None,
        supabase_user_id: str | None = None,
        company_id: str | None = None,
    ) -> dict:
        """
        Get existing profile for workspace or create a new one.

        Args:
            slack_workspace_id: Slack team ID (unique identifier)
            slack_workspace_name: Optional workspace name
            supabase_user_id: Optional Supabase user ID to link
            company_id: Optional company ID to link

        Returns:
            Organization profile dict
        """
        # Try to get existing profile
        existing = await self._request(
            method="GET",
            table="org_profiles",
            params={"slack_workspace_id": f"eq.{slack_workspace_id}"},
        )

        if existing and len(existing) > 0:
            logger.info(f"Found existing profile for workspace {slack_workspace_id}")
            return existing[0]

        # Create new profile
        logger.info(f"Creating new profile for workspace {slack_workspace_id}")

        new_profile = {
            "id": str(uuid.uuid4()),
            "slack_workspace_id": slack_workspace_id,
            "slack_workspace_name": slack_workspace_name,
            "supabase_user_id": supabase_user_id,
            "company_id": company_id,
        }

        result = await self._request(
            method="POST",
            table="org_profiles",
            json_data=new_profile,
        )

        return result[0] if isinstance(result, list) else result

    async def get_profile_by_id(self, profile_id: str) -> dict | None:
        """Get a profile by ID."""
        result = await self._request(
            method="GET",
            table="org_profiles",
            params={"id": f"eq.{profile_id}"},
        )
        return result[0] if result and len(result) > 0 else None

    async def get_profile_by_slack_workspace(self, workspace_id: str) -> dict | None:
        """Get a profile by Slack workspace ID."""
        result = await self._request(
            method="GET",
            table="org_profiles",
            params={"slack_workspace_id": f"eq.{workspace_id}"},
        )
        return result[0] if result and len(result) > 0 else None

    async def update_profile(
        self,
        profile_id: str,
        **updates,
    ) -> dict | None:
        """
        Update an organization profile.

        Args:
            profile_id: Profile UUID
            **updates: Fields to update (company_name, tech_stack, etc.)
        """
        # Remove None values
        updates = {k: v for k, v in updates.items() if v is not None}

        if not updates:
            return await self.get_profile_by_id(profile_id)

        result = await self._request(
            method="PATCH",
            table="org_profiles",
            params={"id": f"eq.{profile_id}"},
            json_data=updates,
        )

        return result[0] if isinstance(result, list) and len(result) > 0 else result

    async def import_onboarding_data(
        self,
        profile_id: str,
        company_name: str | None = None,
        company_hq_location: str | None = None,
        company_size: str | None = None,
        product_description: str | None = None,
        tech_stack: list[str] | None = None,
        hiring_priorities: list[str] | None = None,
    ) -> dict:
        """Import structured onboarding data into profile."""
        updates = {}

        if company_name:
            updates["company_name"] = company_name
        if company_hq_location:
            updates["company_hq_location"] = company_hq_location
        if company_size:
            updates["company_size"] = company_size
        if product_description:
            updates["product_description"] = product_description
        if tech_stack:
            updates["tech_stack"] = tech_stack
        if hiring_priorities:
            updates["hiring_priorities"] = hiring_priorities

        return await self.update_profile(profile_id, **updates)

    async def mark_onboarding_complete(self, profile_id: str) -> dict:
        """Mark onboarding as complete."""
        return await self.update_profile(
            profile_id,
            onboarding_complete=True,
        )

    # ========================================================================
    # Knowledge Operations
    # ========================================================================

    async def add_knowledge(
        self,
        org_profile_id: str,
        category: str,
        content: str,
        source: str = "manual",
        confidence: float = 1.0,
        context_json: dict | None = None,
    ) -> dict:
        """
        Add a knowledge entry.

        Args:
            org_profile_id: Profile UUID
            category: Knowledge category (e.g., "cultural_fit", "technical_challenge")
            content: Knowledge content
            source: Source of knowledge ("slack", "manual", "api")
            confidence: Confidence score (0.0-1.0)
            context_json: Optional additional context
        """
        knowledge = {
            "id": str(uuid.uuid4()),
            "org_profile_id": org_profile_id,
            "category": category,
            "content": content,
            "source": source,
            "confidence": confidence,
            "context_json": context_json or {},
        }

        result = await self._request(
            method="POST",
            table="org_knowledge",
            json_data=knowledge,
        )

        return result[0] if isinstance(result, list) else result

    async def get_knowledge(
        self,
        org_profile_id: str,
        category: str | None = None,
    ) -> list[dict]:
        """Get knowledge entries for a profile."""
        params = {"org_profile_id": f"eq.{org_profile_id}"}

        if category:
            params["category"] = f"eq.{category}"

        result = await self._request(
            method="GET",
            table="org_knowledge",
            params=params,
        )

        return result if result else []

    # ========================================================================
    # Hiring Priorities Operations
    # ========================================================================

    async def add_hiring_priority(
        self,
        org_profile_id: str,
        role_title: str,
        must_haves: list[str] | None = None,
        nice_to_haves: list[str] | None = None,
        dealbreakers: list[str] | None = None,
        specific_work: str | None = None,
        success_criteria: str | None = None,
    ) -> dict:
        """Add a hiring priority for a specific role."""
        priority = {
            "id": str(uuid.uuid4()),
            "org_profile_id": org_profile_id,
            "role_title": role_title,
            "must_haves": must_haves or [],
            "nice_to_haves": nice_to_haves or [],
            "dealbreakers": dealbreakers or [],
            "specific_work": specific_work,
            "success_criteria": success_criteria,
        }

        result = await self._request(
            method="POST",
            table="hiring_priorities",
            json_data=priority,
        )

        return result[0] if isinstance(result, list) else result

    async def get_hiring_priorities(
        self,
        org_profile_id: str,
    ) -> list[dict]:
        """Get all hiring priorities for a profile."""
        result = await self._request(
            method="GET",
            table="hiring_priorities",
            params={"org_profile_id": f"eq.{org_profile_id}"},
        )

        return result if result else []


# Global instance
org_profiles_db = OrgProfilesDBService()
