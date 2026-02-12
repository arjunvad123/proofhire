"""
Supabase Sync Service - REST API Edition

Syncs onboarding data from Supabase startup_users table into OrgProfile.
Uses REST API instead of SQLAlchemy.
"""

import logging
from typing import Any

from app.services.org_profiles_db import org_profiles_db
from app.services.onboarding_import import OnboardingImporter
from app.services.supabase import SupabaseService

logger = logging.getLogger(__name__)


class SupabaseSyncService:
    """
    Syncs onboarding data from Supabase into organization profiles.

    Bridges the gap between:
    - Supabase startup_users table (web onboarding)
    - OrgProfile in Agencity database (Slack agent context)
    """

    def __init__(
        self,
        supabase_service: SupabaseService | None = None,
        onboarding_importer: OnboardingImporter | None = None,
    ):
        self.supabase = supabase_service or SupabaseService()
        self.importer = onboarding_importer or OnboardingImporter()

    async def sync_from_supabase_user(
        self,
        org_profile_id: str,
        supabase_user_id: str,
    ) -> dict[str, Any] | None:
        """
        Sync data from Supabase startup_users into an OrgProfile.

        Args:
            org_profile_id: UUID of the org profile to update
            supabase_user_id: Supabase auth user ID

        Returns:
            Dictionary of synced data or None if user not found
        """
        logger.info(
            f"Syncing Supabase user {supabase_user_id} to org profile {org_profile_id}"
        )

        # Fetch startup user data
        startup_user = await self.supabase.get_startup_user(supabase_user_id)

        if not startup_user:
            logger.warning(f"No startup user found for user_id={supabase_user_id}")
            return None

        logger.info(
            f"Found startup user: company={startup_user.get('company_name')}, "
            f"onboarding_completed={startup_user.get('onboarding_completed')}"
        )

        # Extract data from startup_users
        updates: dict[str, Any] = {
            "supabase_user_id": supabase_user_id,
            "company_name": startup_user.get("company_name"),
        }

        # Parse website if available
        if startup_user.get("website"):
            updates["extra_context"] = {"website": startup_user["website"]}

        # Parse hiring_for field (what role they're hiring for)
        hiring_for = startup_user.get("hiring_for")
        if hiring_for:
            # Store in extra_context as raw hiring_for
            if "extra_context" not in updates:
                updates["extra_context"] = {}
            updates["extra_context"]["hiring_for"] = hiring_for

        # Download and parse job posting file if available
        job_posting_url = startup_user.get("job_posting_file_url")
        job_description = None

        if job_posting_url:
            logger.info(f"Downloading job posting from {job_posting_url}")
            job_description = await self.supabase.download_job_posting(
                job_posting_url
            )

            if job_description:
                logger.info(
                    f"Downloaded job posting ({len(job_description)} chars)"
                )

                # Parse job description using LLM
                jd_data = await self.importer.parse_job_description(
                    job_description
                )

                # Merge parsed data
                if jd_data.get("product_description"):
                    updates["product_description"] = jd_data["product_description"]
                if jd_data.get("company_stage"):
                    updates["company_stage"] = jd_data["company_stage"]
                if jd_data.get("tech_stack"):
                    updates["tech_stack"] = jd_data["tech_stack"]
                if jd_data.get("role_requirements"):
                    # Store requirements in extra_context
                    if "extra_context" not in updates:
                        updates["extra_context"] = {}
                    updates["extra_context"]["role_requirements"] = jd_data[
                        "role_requirements"
                    ]

                # Extract hiring priorities from job description
                priorities = await self.importer.extract_hiring_priorities(
                    job_description
                )
                if priorities:
                    updates["hiring_priorities"] = priorities

            else:
                logger.warning("Failed to download job posting file")

        # Mark onboarding complete if it's complete in Supabase
        if startup_user.get("onboarding_completed"):
            updates["onboarding_complete"] = True

        # Update the profile using REST API
        await org_profiles_db.update_profile(org_profile_id, **updates)

        logger.info(
            f"Synced Supabase data to org profile {org_profile_id}: "
            f"{len(updates)} fields updated"
        )

        return updates

    async def link_profile_to_supabase_user(
        self,
        org_profile_id: str,
        supabase_user_id: str,
    ) -> bool:
        """
        Link an org profile to a Supabase user and sync data.

        Args:
            org_profile_id: UUID of the org profile
            supabase_user_id: Supabase auth user ID

        Returns:
            True if successful, False otherwise
        """
        try:
            result = await self.sync_from_supabase_user(
                org_profile_id, supabase_user_id
            )
            return result is not None
        except Exception as e:
            logger.error(
                f"Failed to link profile to Supabase user: {e}", exc_info=True
            )
            return False

    async def find_and_link_by_company_name(
        self,
        org_profile_id: str,
        company_name: str,
    ) -> bool:
        """
        Find a Supabase user by company name and link to org profile.

        Useful when you have the company name but not the user_id.

        Args:
            org_profile_id: UUID of the org profile
            company_name: Company name to search for

        Returns:
            True if found and linked, False otherwise
        """
        logger.info(
            f"Searching for Supabase user with company_name={company_name}"
        )

        startup_user = await self.supabase.get_startup_user_by_company(
            company_name
        )

        if not startup_user:
            logger.warning(f"No startup user found for company: {company_name}")
            return False

        user_id = startup_user.get("user_id")
        if not user_id:
            logger.warning("Startup user has no user_id")
            return False

        logger.info(f"Found startup user with user_id={user_id}")

        # Sync the data
        return await self.link_profile_to_supabase_user(
            org_profile_id, user_id
        )
