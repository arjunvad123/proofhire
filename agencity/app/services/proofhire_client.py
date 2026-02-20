"""
ProofHire API client for Agencity integration endpoints.
"""

from __future__ import annotations

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)


class ProofHireClient:
    """Lightweight async client for ProofHire public/internal endpoints."""

    def __init__(self) -> None:
        self.base_url = settings.proofhire_api_base.rstrip("/")
        self.internal_key = settings.proofhire_internal_api_key
        self.timeout_seconds = settings.external_api_timeout_seconds

    async def create_application(
        self,
        proofhire_role_id: str,
        candidate_name: str,
        candidate_email: str,
        github_url: str | None = None,
    ) -> dict[str, Any]:
        """Create an application in ProofHire for a candidate invitation."""
        payload = {
            "email": candidate_email,
            "name": candidate_name,
            "github_url": github_url,
            "consent": True,
        }
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.post(
                f"{self.base_url}/applications/roles/{proofhire_role_id}/apply",
                json=payload,
            )
            response.raise_for_status()
            return response.json()

    async def get_run_status(self, run_id: str) -> dict[str, Any]:
        """Read a simulation run status from ProofHire."""
        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            response = await client.get(f"{self.base_url}/runs/{run_id}/status")
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> dict[str, Any]:
        """Check ProofHire backend liveness from Agencity."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(f"{self.base_url.replace('/api', '')}/health")
                return {
                    "provider": "proofhire",
                    "ok": response.status_code == 200,
                    "status_code": response.status_code,
                }
        except httpx.HTTPError as exc:
            logger.warning("ProofHire health check failed: %s", exc)
            return {"provider": "proofhire", "ok": False, "reason": str(exc)}

    def verify_internal_key(self, key: str | None) -> bool:
        """Verify webhook caller key against Agencity config."""
        return bool(self.internal_key) and key == self.internal_key


proofhire_client = ProofHireClient()
