"""
API router - combines all route modules.
"""

from fastapi import APIRouter

from app.api.routes import conversations, shortlists, slack

api_router = APIRouter()

# Include route modules
api_router.include_router(conversations.router)
api_router.include_router(shortlists.router)
api_router.include_router(slack.router, prefix="/slack", tags=["slack"])
