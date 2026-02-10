"""
API router - combines all route modules.
"""

from fastapi import APIRouter

from app.api.routes import conversations, shortlists

api_router = APIRouter()

# Include route modules
api_router.include_router(conversations.router)
api_router.include_router(shortlists.router)
