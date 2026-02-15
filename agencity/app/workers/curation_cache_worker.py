"""
Background worker to generate and cache curated candidate shortlists.

This worker runs curation for all pending roles and stores results in cache.
Can be run as a cron job or background task.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.core.database import get_supabase_client
from app.services.curation_engine import CandidateCurationEngine

logger = logging.getLogger(__name__)


async def generate_cache_for_role(
    company_id: str,
    role_id: str,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Generate and cache curated candidates for a single role.

    Args:
        company_id: Company UUID
        role_id: Role UUID
        force_refresh: Force regeneration even if cache exists

    Returns:
        Dict with status and cache metadata
    """
    supabase = get_supabase_client()

    try:
        # Update role status to 'processing'
        supabase.table("roles").update({
            "curation_status": "processing"
        }).eq("id", role_id).execute()

        # Get role details
        role_result = supabase.table("roles").select(
            "id, title, required_skills, preferred_skills"
        ).eq("id", role_id).execute()

        if not role_result.data:
            raise Exception(f"Role {role_id} not found")

        role = role_result.data[0]

        # Initialize curation engine
        engine = CandidateCurationEngine(supabase)

        logger.info(f"Running curation for role {role_id} ({role['title']})...")

        # Temporarily disable Perplexity to save API costs during cache generation
        # NOTE: PDL enrichment still runs for top 5 candidates, but uses 30-day cache
        # so repeat candidates across roles won't be re-enriched (cost optimization)
        import os
        original_perplexity_key = os.environ.get('PERPLEXITY_API_KEY')
        os.environ['PERPLEXITY_API_KEY'] = ''

        try:
            # Run actual curation
            # - PDL enrichment: Top 5 candidates (30-day cache, ~$0.10/new enrichment)
            # - Claude reasoning: Top 5 candidates (~$0.006 total)
            # - Perplexity: DISABLED during cache generation (saves ~$0.025)
            # - Expected cost: ~$0.10-0.50 per role (depending on cache hits)
            shortlist = await engine.curate(
                company_id=company_id,
                role_id=role_id,
                limit=30
            )
        finally:
            # Restore API key
            if original_perplexity_key:
                os.environ['PERPLEXITY_API_KEY'] = original_perplexity_key

        # Calculate metadata
        avg_score = sum(c.match_score for c in shortlist) / len(shortlist) if shortlist else 0
        enriched_count = sum(1 for c in shortlist if c.was_enriched)
        avg_confidence = sum(c.fit_confidence for c in shortlist) / len(shortlist) if shortlist else 0

        # Log enrichment details
        logger.info(f"  📊 Enriched: {enriched_count}/{len(shortlist)} candidates")
        logger.info(f"  💰 PDL uses 30-day cache - only new candidates incur cost ($0.10 each)")
        logger.info(f"  🧠 Claude AI analyzed top 5 (~$0.006 total)")
        logger.info(f"  ⚡ Perplexity disabled during cache generation (saves ~$0.025)")

        # Get total network size
        network_response = supabase.table('people').select(
            'id', count='exact'
        ).eq('company_id', company_id).execute()
        total_searched = network_response.count or 0

        # Convert shortlist to JSON-serializable format
        def serialize_context(context):
            """Convert Pydantic context to JSON-safe dict."""
            if hasattr(context, 'dict'):
                # Use Pydantic's model_dump or dict with exclude_none
                if hasattr(context, 'model_dump'):
                    return context.model_dump(exclude_none=False, mode='json')
                else:
                    return context.dict(exclude_none=False)
            return context

        shortlist_json = [
            {
                "person_id": c.person_id,
                "full_name": c.full_name,
                "headline": c.headline,
                "location": c.location,
                "current_company": c.current_company,
                "current_title": c.current_title,
                "linkedin_url": c.linkedin_url,
                "github_url": c.github_url,
                "match_score": c.match_score,
                "fit_confidence": c.fit_confidence,
                "data_completeness": c.data_completeness,
                "was_enriched": c.was_enriched,
                "context": serialize_context(c.context)
            }
            for c in shortlist
        ]

        curation_result = {
            "shortlist": shortlist_json,
            "total_searched": total_searched,
            "metadata": {
                "enriched_count": enriched_count,
                "avg_match_score": round(avg_score, 1),
                "avg_confidence": round(avg_confidence, 2)
            }
        }

        logger.info(f"Curation complete: {len(shortlist_json)} candidates, avg score: {avg_score:.1f}")

        # Store in cache
        expires_at = datetime.utcnow() + timedelta(hours=24)

        cache_data = {
            "company_id": company_id,
            "role_id": role_id,
            "shortlist": curation_result["shortlist"],
            "metadata": curation_result["metadata"],
            "total_searched": curation_result["total_searched"],
            "enriched_count": curation_result["metadata"]["enriched_count"],
            "avg_match_score": curation_result["metadata"]["avg_match_score"],
            "generated_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat()
        }

        # Upsert cache (insert or update if exists)
        try:
            supabase.table("curation_cache").upsert(
                cache_data,
                on_conflict="company_id,role_id"
            ).execute()
        except Exception as cache_error:
            logger.error(f"Failed to store cache: {cache_error}")
            logger.error(f"Cache data keys: {cache_data.keys()}")
            logger.error(f"Shortlist length: {len(cache_data['shortlist'])}")
            if cache_data['shortlist']:
                logger.error(f"First candidate context keys: {cache_data['shortlist'][0]['context'].keys() if isinstance(cache_data['shortlist'][0]['context'], dict) else 'not a dict'}")
            raise

        # Update role status to 'cached'
        supabase.table("roles").update({
            "curation_status": "cached",
            "last_curated_at": datetime.utcnow().isoformat()
        }).eq("id", role_id).execute()

        logger.info(f"✓ Cache generated for role {role_id} ({role['title']})")

        return {
            "status": "success",
            "role_id": role_id,
            "role_title": role["title"],
            "cached_count": len(curation_result["shortlist"]),
            "expires_at": expires_at.isoformat()
        }

    except Exception as e:
        logger.error(f"✗ Failed to generate cache for role {role_id}: {e}", exc_info=True)

        # Update role status to 'failed'
        try:
            supabase.table("roles").update({
                "curation_status": "failed"
            }).eq("id", role_id).execute()
        except Exception as update_error:
            logger.error(f"Failed to update role status: {update_error}")

        return {
            "status": "failed",
            "role_id": role_id,
            "error": str(e)
        }


async def generate_caches_for_company(
    company_id: str,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """
    Generate caches for all active roles in a company.

    Args:
        company_id: Company UUID
        force_refresh: Force regeneration even if cache exists

    Returns:
        Dict with summary of cache generation results
    """
    supabase = get_supabase_client()

    try:
        # Get all active roles that need caching
        query = supabase.table("roles").select("id, title").eq(
            "company_id", company_id
        ).eq("status", "active")

        if not force_refresh:
            # Only get roles that don't have cached data
            query = query.in_("curation_status", ["pending", "failed"])

        roles_result = query.execute()

        if not roles_result.data:
            logger.info(f"No roles to cache for company {company_id}")
            return {
                "status": "no_roles",
                "company_id": company_id,
                "processed": 0
            }

        roles = roles_result.data
        logger.info(f"Processing {len(roles)} roles for company {company_id}")

        # Generate cache for each role
        results = []
        for role in roles:
            result = await generate_cache_for_role(company_id, role["id"], force_refresh)
            results.append(result)

        success_count = sum(1 for r in results if r["status"] == "success")
        failed_count = sum(1 for r in results if r["status"] == "failed")

        logger.info(
            f"Company {company_id}: {success_count} succeeded, {failed_count} failed"
        )

        return {
            "status": "completed",
            "company_id": company_id,
            "processed": len(results),
            "success": success_count,
            "failed": failed_count,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error generating caches for company {company_id}: {e}")
        return {
            "status": "error",
            "company_id": company_id,
            "error": str(e)
        }


async def generate_all_caches(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Generate caches for ALL companies and roles.

    This is the main worker function that should be run as a cron job.

    Args:
        force_refresh: Force regeneration even if cache exists

    Returns:
        Dict with summary of all cache generation
    """
    supabase = get_supabase_client()

    try:
        # Get all companies with active roles
        companies_result = supabase.table("companies").select(
            "id, name"
        ).execute()

        if not companies_result.data:
            logger.info("No companies found")
            return {
                "status": "no_companies",
                "processed": 0
            }

        companies = companies_result.data
        logger.info(f"Processing {len(companies)} companies")

        # Process each company
        results = []
        for company in companies:
            result = await generate_caches_for_company(company["id"], force_refresh)
            results.append(result)

        total_processed = sum(r.get("processed", 0) for r in results)
        total_success = sum(r.get("success", 0) for r in results)
        total_failed = sum(r.get("failed", 0) for r in results)

        logger.info(
            f"✓ All companies processed: {total_success} succeeded, {total_failed} failed"
        )

        return {
            "status": "completed",
            "companies_processed": len(results),
            "total_roles_processed": total_processed,
            "total_success": total_success,
            "total_failed": total_failed,
            "results": results
        }

    except Exception as e:
        logger.error(f"Error in generate_all_caches: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


async def cleanup_expired_caches() -> Dict[str, Any]:
    """
    Clean up expired cache entries.

    Deletes cache entries where expires_at < NOW.
    Should be run periodically (e.g., daily).

    Returns:
        Dict with cleanup summary
    """
    supabase = get_supabase_client()

    try:
        # Delete expired caches
        result = supabase.table("curation_cache").delete().lt(
            "expires_at", datetime.utcnow().isoformat()
        ).execute()

        deleted_count = len(result.data) if result.data else 0

        logger.info(f"✓ Cleaned up {deleted_count} expired cache entries")

        return {
            "status": "success",
            "deleted_count": deleted_count
        }

    except Exception as e:
        logger.error(f"Error cleaning up expired caches: {e}")
        return {
            "status": "error",
            "error": str(e)
        }


# CLI interface for running worker manually
if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    command = sys.argv[1] if len(sys.argv) > 1 else "generate_all"

    if command == "generate_all":
        force = "--force" in sys.argv
        result = asyncio.run(generate_all_caches(force_refresh=force))
        print(f"\n✓ Result: {result}")

    elif command == "cleanup":
        result = asyncio.run(cleanup_expired_caches())
        print(f"\n✓ Result: {result}")

    elif command == "company":
        if len(sys.argv) < 3:
            print("Usage: python curation_cache_worker.py company <company_id> [--force]")
            sys.exit(1)
        company_id = sys.argv[2]
        force = "--force" in sys.argv
        result = asyncio.run(generate_caches_for_company(company_id, force_refresh=force))
        print(f"\n✓ Result: {result}")

    elif command == "role":
        if len(sys.argv) < 4:
            print("Usage: python curation_cache_worker.py role <company_id> <role_id> [--force]")
            sys.exit(1)
        company_id = sys.argv[2]
        role_id = sys.argv[3]
        force = "--force" in sys.argv
        result = asyncio.run(generate_cache_for_role(company_id, role_id, force_refresh=force))
        print(f"\n✓ Result: {result}")

    else:
        print("""
Usage:
  python curation_cache_worker.py generate_all [--force]  # Generate cache for all companies
  python curation_cache_worker.py company <id> [--force]  # Generate cache for one company
  python curation_cache_worker.py role <company_id> <role_id> [--force]  # Generate cache for one role
  python curation_cache_worker.py cleanup                 # Clean up expired caches
        """)
