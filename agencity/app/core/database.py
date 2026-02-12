"""
Database connection helpers.
"""

import os
from supabase import create_client, Client
from functools import lru_cache


@lru_cache()
def get_supabase_client() -> Client:
    """
    Get Supabase client.

    Cached to reuse connection.
    """
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")

    return create_client(url, key)
