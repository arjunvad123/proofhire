"""
Agencity - AI Hiring Agent

Main FastAPI application.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import settings

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting Agencity in {settings.app_env} mode")
    yield
    logger.info("Shutting down Agencity")


# Create FastAPI app
app = FastAPI(
    title="Agencity",
    description="AI hiring agent that finds people you can't search for",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api")


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "name": "Agencity",
        "status": "ok",
        "version": "0.1.0",
        "description": "AI hiring agent that finds people you can't search for",
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "environment": settings.app_env,
        "llm_configured": bool(settings.openai_api_key),
        "github_configured": bool(settings.github_token),
        "supabase_configured": bool(settings.supabase_url and settings.supabase_key),
        "pdl_configured": bool(settings.pdl_api_key),
        "clado_configured": bool(settings.clado_api_key),
        "proofhire_configured": bool(settings.proofhire_api_base),
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,  # Different from proofhire
        reload=settings.debug,
    )
