"""
API key authentication for Agencity.

Stripe-style API keys: ag_live_<32-char-random>
Only bcrypt hash is stored. Lookup by prefix (first 8 chars of random part).
"""

import logging
import secrets
from datetime import datetime, timezone

import bcrypt as _bcrypt

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pydantic import BaseModel

from app.core.database import get_supabase_client

logger = logging.getLogger(__name__)

# FastAPI security scheme
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class CompanyAuth(BaseModel):
    """Authenticated company context injected into routes."""
    company_id: str
    company_name: str
    scopes: list[str]
    api_key_id: str


def generate_api_key(company_id: str) -> tuple[str, str, str]:
    """
    Generate a new API key for a company.

    Returns: (raw_key, key_hash, key_prefix)
    - raw_key: shown to user ONCE (ag_live_<random>)
    - key_hash: bcrypt hash stored in DB
    - key_prefix: first 12 chars of raw key for lookup/display
    """
    random_part = secrets.token_urlsafe(32)
    raw_key = f"ag_live_{random_part}"
    key_hash = _bcrypt.hashpw(raw_key.encode(), _bcrypt.gensalt()).decode()
    key_prefix = raw_key[:20]  # "ag_live_" + first 12 chars of random

    return raw_key, key_hash, key_prefix


async def create_api_key(
    company_id: str,
    name: str = "default",
    scopes: list[str] | None = None,
) -> tuple[str, dict]:
    """
    Create and store a new API key for a company.

    Returns: (raw_key, key_record)
    """
    if scopes is None:
        scopes = ["read", "write"]

    raw_key, key_hash, key_prefix = generate_api_key(company_id)

    supabase = get_supabase_client()
    result = supabase.table("api_keys").insert({
        "company_id": company_id,
        "key_hash": key_hash,
        "key_prefix": key_prefix,
        "name": name,
        "scopes": scopes,
    }).execute()

    record = result.data[0] if result.data else {}
    return raw_key, record


async def verify_api_key(raw_key: str) -> CompanyAuth | None:
    """
    Verify an API key and return the authenticated company.

    Lookup by prefix, then verify bcrypt hash.
    """
    if not raw_key or not raw_key.startswith("ag_live_"):
        return None

    prefix = raw_key[:20]
    supabase = get_supabase_client()

    # Find key by prefix
    result = supabase.table("api_keys").select(
        "id, company_id, key_hash, scopes, is_active, expires_at"
    ).eq("key_prefix", prefix).eq("is_active", True).execute()

    if not result.data:
        return None

    # Check each matching key (should be 1, but handle collisions)
    for key_row in result.data:
        # Check expiry
        if key_row.get("expires_at"):
            expires = datetime.fromisoformat(key_row["expires_at"])
            if expires < datetime.now(timezone.utc):
                continue

        # Verify hash
        if _bcrypt.checkpw(raw_key.encode(), key_row["key_hash"].encode()):
            # Update last_used_at (fire and forget)
            try:
                supabase.table("api_keys").update({
                    "last_used_at": datetime.now(timezone.utc).isoformat()
                }).eq("id", key_row["id"]).execute()
            except Exception:
                pass  # Non-critical

            # Get company name
            company = supabase.table("companies").select(
                "id, name"
            ).eq("id", key_row["company_id"]).single().execute()

            if not company.data:
                return None

            return CompanyAuth(
                company_id=str(key_row["company_id"]),
                company_name=company.data["name"],
                scopes=key_row.get("scopes", ["read", "write"]),
                api_key_id=str(key_row["id"]),
            )

    return None


async def get_current_company(
    api_key: str | None = Security(api_key_header),
) -> CompanyAuth:
    """
    FastAPI dependency: authenticate via API key.

    Usage:
        @router.get("/something")
        async def something(auth: CompanyAuth = Depends(get_current_company)):
            ...
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Pass via X-API-Key header.",
        )

    auth = await verify_api_key(api_key)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired API key.",
        )

    return auth
