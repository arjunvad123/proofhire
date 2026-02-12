"""
Database connection helpers.
"""

from supabase import create_client, Client
from functools import lru_cache
from app.config import settings


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client.

    Cached to reuse connection.
    """
    url = settings.supabase_url
    key = settings.supabase_key

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

    return create_client(url, key)
