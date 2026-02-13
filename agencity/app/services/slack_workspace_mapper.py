"""
Slack Workspace Mapper - Maps Slack workspace IDs to company IDs
"""

from app.core.database import get_supabase_client


class SlackWorkspaceMapper:
    """
    Maps Slack workspace IDs to Agencity company IDs.

    Uses the org_profiles table to look up company_id by slack_workspace_id.
    """

    def __init__(self):
        self.supabase = get_supabase_client()

    async def get_company_id(self, slack_workspace_id: str) -> str:
        """
        Look up company_id from org_profiles table.

        Args:
            slack_workspace_id: Slack team ID (e.g., "T01234ABCD")

        Returns:
            company_id: UUID string

        Raises:
            ValueError: If no company found for workspace
        """

        result = self.supabase.table("org_profiles").select("company_id").eq(
            "slack_workspace_id", slack_workspace_id
        ).single().execute()

        if not result.data:
            raise ValueError(
                f"No company found for Slack workspace {slack_workspace_id}. "
                f"Please onboard this workspace first."
            )

        return result.data["company_id"]

    async def get_org_profile(self, slack_workspace_id: str) -> dict:
        """
        Get full org profile for a Slack workspace.

        Returns:
            {
                "company_id": "...",
                "company_name": "...",
                "pace": "high",
                "quality_bar": "high",
                ...
            }
        """

        result = self.supabase.table("org_profiles").select("*").eq(
            "slack_workspace_id", slack_workspace_id
        ).single().execute()

        if not result.data:
            raise ValueError(f"No org profile found for Slack workspace {slack_workspace_id}")

        return result.data
