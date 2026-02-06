"""Main API router that aggregates all route modules."""

from fastapi import APIRouter

from app.api.routes import auth, orgs, roles, candidates, applications, simulations, runs, briefs, artifacts, internal

api_router = APIRouter()

# Include all route modules
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(orgs.router, prefix="/orgs", tags=["orgs"])
api_router.include_router(roles.router, prefix="/roles", tags=["roles"])
api_router.include_router(candidates.router, prefix="/candidates", tags=["candidates"])
api_router.include_router(applications.router, prefix="/applications", tags=["applications"])
api_router.include_router(simulations.router, prefix="/simulations", tags=["simulations"])
api_router.include_router(runs.router, prefix="/runs", tags=["runs"])
api_router.include_router(briefs.router, prefix="/briefs", tags=["briefs"])
api_router.include_router(artifacts.router, prefix="/artifacts", tags=["artifacts"])
api_router.include_router(internal.router, prefix="/internal", tags=["internal"])
