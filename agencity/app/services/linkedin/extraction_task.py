"""
Background task for LinkedIn connection extraction.

Runs the extraction job asynchronously and stores results in the database.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from supabase import Client

from .connection_extractor import LinkedInConnectionExtractor
from .session_manager import LinkedInSessionManager

logger = logging.getLogger(__name__)


async def run_connection_extraction(
    job_id: str,
    session_id: str,
    supabase: Client
) -> None:
    """
    Background task to extract LinkedIn connections.

    Args:
        job_id: Extraction job UUID
        session_id: LinkedIn session UUID
        supabase: Supabase client
    """
    session_manager = LinkedInSessionManager(supabase)
    extractor = LinkedInConnectionExtractor(session_manager)

    try:
        # Debug: verify we can get cookies
        cookies = await session_manager.get_session_cookies(session_id)
        if cookies:
            logger.info(f"Extraction starting with {len(cookies)} cookies")
            if 'li_at' in cookies:
                logger.info(f"li_at cookie present: {cookies['li_at'].get('value', '')[:20]}...")
        else:
            logger.warning("No cookies found for session!")

        # Update job status to running
        supabase.table('connection_extraction_jobs').update({
            'status': 'running'
        }).eq('id', job_id).execute()

        # Get session to find company_id
        session = await session_manager.get_session(session_id)
        if not session:
            raise Exception("Session not found")

        company_id = session.get('company_id')

        # Define progress callback
        async def progress_callback(found: int, estimated_total: int):
            supabase.table('connection_extraction_jobs').update({
                'connections_found': found,
                'last_scroll_position': found  # Using as proxy for progress
            }).eq('id', job_id).execute()

        # Run extraction
        result = await extractor.extract_connections(
            session_id=session_id,
            progress_callback=progress_callback
        )

        if result['status'] == 'success':
            connections = result['connections']

            # Store connections in database
            stored_count = await _store_connections(
                supabase=supabase,
                company_id=company_id,
                session_id=session_id,
                connections=connections
            )

            # Update job as completed
            supabase.table('connection_extraction_jobs').update({
                'status': 'completed',
                'connections_found': stored_count,
                'completed_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', job_id).execute()

            logger.info(f"Extraction job {job_id} completed: {stored_count} connections stored")

        else:
            # Extraction failed
            supabase.table('connection_extraction_jobs').update({
                'status': 'failed',
                'error_message': result.get('error', 'Unknown error'),
                'completed_at': datetime.now(timezone.utc).isoformat()
            }).eq('id', job_id).execute()

            logger.error(f"Extraction job {job_id} failed: {result.get('error')}")

    except Exception as e:
        logger.exception(f"Extraction job {job_id} failed with exception")

        # Update job as failed
        supabase.table('connection_extraction_jobs').update({
            'status': 'failed',
            'error_message': str(e),
            'completed_at': datetime.now(timezone.utc).isoformat()
        }).eq('id', job_id).execute()


async def _store_connections(
    supabase: Client,
    company_id: str,
    session_id: str,
    connections: list
) -> int:
    """
    Store extracted connections in the database.

    Uses upsert to avoid duplicates based on linkedin_url.

    Args:
        supabase: Supabase client
        company_id: Company UUID
        session_id: Session UUID
        connections: List of connection dicts from extractor

    Returns:
        Number of connections stored/updated
    """
    if not connections:
        return 0

    stored = 0
    batch_size = 50

    for i in range(0, len(connections), batch_size):
        batch = connections[i:i + batch_size]

        records = []
        for conn in batch:
            linkedin_url = conn.get('linkedin_url')
            if not linkedin_url:
                continue

            records.append({
                'company_id': company_id,
                'session_id': session_id,
                'linkedin_url': linkedin_url,
                'full_name': conn.get('full_name'),
                'current_title': conn.get('current_title'),
                'current_company': conn.get('current_company'),
                'headline': conn.get('headline'),
                'profile_image_url': conn.get('profile_image_url'),
                'connected_at_text': conn.get('connected_at_text') or conn.get('connectedDate'),
                'enrichment_status': 'pending',
                'updated_at': datetime.now(timezone.utc).isoformat()
            })

        if records:
            # Upsert - update if (company_id, linkedin_url) exists, insert if new
            result = supabase.table('linkedin_connections').upsert(
                records,
                on_conflict='company_id,linkedin_url'
            ).execute()

            stored += len(result.data) if result.data else 0

        # Small delay between batches to avoid rate limits
        await asyncio.sleep(0.1)

    return stored


def run_extraction_sync(job_id: str, session_id: str, supabase: Client) -> None:
    """
    Synchronous wrapper for running extraction in a background thread.

    FastAPI's BackgroundTasks expects a sync function, so this wraps
    the async extraction in an event loop.
    """
    asyncio.run(run_connection_extraction(job_id, session_id, supabase))
