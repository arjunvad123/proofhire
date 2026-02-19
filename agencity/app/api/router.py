"""
API router - combines all route modules.
"""

from fastapi import APIRouter

from app.api.routes import conversations, shortlists, slack, companies, search, search_v2, search_v3, intelligence, curation, unified, integration, linkedin

api_router = APIRouter()

# Include route modules
api_router.include_router(conversations.router)
api_router.include_router(shortlists.router)
api_router.include_router(slack.router, prefix="/slack", tags=["slack"])
api_router.include_router(companies.router, prefix="/companies", tags=["companies"])
api_router.include_router(curation.router, tags=["curation"])  # V4 (candidate curation) - NEW!
api_router.include_router(search.router, tags=["search"])  # V1 (legacy)
api_router.include_router(search_v2.router, tags=["search-v2"])  # V2 (network-first)
api_router.include_router(search_v3.router, tags=["search-v3"])  # V3 (hybrid external search)
api_router.include_router(unified.router, tags=["unified"])  # ⭐ UNIFIED (replaces all above)
api_router.include_router(intelligence.router, tags=["intelligence"])  # Intelligence system (legacy)
api_router.include_router(integration.router, tags=["integration"])  # ProofHire integration
api_router.include_router(linkedin.router, tags=["linkedin"])  # LinkedIn automation
