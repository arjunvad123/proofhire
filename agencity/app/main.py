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
from app.logging_config import setup_logging
from app.middleware import RequestIdMiddleware

# Configure structured logging
setup_logging()

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    logger.info(f"Starting Agencity in {settings.app_env} mode")

    # Initialize Sentry if configured
    if settings.sentry_dsn:
        try:
            import sentry_sdk
            sentry_sdk.init(
                dsn=settings.sentry_dsn,
                environment=settings.app_env,
                traces_sample_rate=0.1,
            )
            logger.info("Sentry initialized")
        except ImportError:
            logger.warning("sentry-sdk not installed, skipping Sentry init")

    yield
    logger.info("Shutting down Agencity")


# Create FastAPI app
app = FastAPI(
    title="Agencity",
    description="AI hiring agent that finds people you can't search for",
    version="0.1.0",
    lifespan=lifespan,
)

# Request ID middleware (adds X-Request-ID to every request/response)
app.add_middleware(RequestIdMiddleware)

# CORS middleware
cors_origins = (
    settings.cors_origins.split(",")
    if settings.cors_origins
    else ["http://localhost:3000"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
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
    }


@app.get("/health")
async def health():
    """Detailed health check. Tests actual connectivity."""
    checks = {}

    # Check Supabase
    try:
        from app.core.database import get_supabase_client
        sb = get_supabase_client()
        sb.table("companies").select("id").limit(1).execute()
        checks["supabase"] = "healthy"
    except Exception:
        checks["supabase"] = "unreachable"

    # Check Redis
    try:
        import redis
        r = redis.from_url(settings.redis_url, socket_timeout=2)
        r.ping()
        checks["redis"] = "healthy"
    except Exception:
        checks["redis"] = "unreachable"

    all_healthy = all(v == "healthy" for v in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "environment": settings.app_env,
        "checks": checks,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,  # Different from proofhire
        reload=settings.debug,
    )
