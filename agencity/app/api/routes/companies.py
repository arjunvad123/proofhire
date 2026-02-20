"""
Company API routes for onboarding and management.

Handles Stage 0 (Onboarding) and Stage 1 (Data Import).
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from app.auth import CompanyAuth, get_current_company, create_api_key
from app.models.company import (
    Company,
    CompanyCreate,
    CompanyUpdate,
    CompanyUMO,
    CompanyUMOCreate,
    CompanyWithStats,
    Role,
    RoleCreate,
    DataSource,
    ImportResult,
)
from app.services.company_db import company_db

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class CreateCompanyRequest(BaseModel):
    """Request to create a company."""
    name: str
    founder_email: str
    founder_name: str
    domain: Optional[str] = None
    stage: Optional[str] = None
    industry: Optional[str] = None
    tech_stack: list[str] = []
    team_size: Optional[int] = None


class UpdateUMORequest(BaseModel):
    """Request to update company UMO."""
    preferred_backgrounds: list[str] = []
    must_have_traits: list[str] = []
    anti_patterns: list[str] = []
    culture_values: list[str] = []
    work_style: Optional[str] = None
    ideal_candidate_description: Optional[str] = None


class CreateRoleRequest(BaseModel):
    """Request to create a role."""
    title: str
    level: Optional[str] = None
    department: Optional[str] = None
    required_skills: list[str] = []
    preferred_skills: list[str] = []
    years_experience_min: Optional[int] = None
    years_experience_max: Optional[int] = None
    description: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None


# =============================================================================
# COMPANY ENDPOINTS
# =============================================================================

class SignupResponse(BaseModel):
    """Response from company signup."""
    company: Company
    api_key: str           # Raw key, shown only once
    api_key_prefix: str    # For reference
    next_steps: list[str]


@router.post("")
async def create_company(request: CreateCompanyRequest):
    """
    Create a new company and start onboarding.

    Returns the company and a one-time API key.
    Save the API key — it cannot be retrieved again.
    """
    try:
        from app.models.company import CompanyStage

        stage = None
        if request.stage:
            try:
                stage = CompanyStage(request.stage)
            except ValueError:
                pass

        company_data = CompanyCreate(
            name=request.name,
            founder_email=request.founder_email,
            founder_name=request.founder_name,
            domain=request.domain,
            stage=stage,
            industry=request.industry,
            tech_stack=request.tech_stack,
            team_size=request.team_size,
        )

        company = await company_db.create_company(company_data)

        logger.info(f"Created company: {company.id} - {company.name}")

        # Generate API key
        raw_key, key_record = await create_api_key(
            company_id=str(company.id),
            name="default",
        )

        return SignupResponse(
            company=company,
            api_key=raw_key,
            api_key_prefix=key_record.get("key_prefix", raw_key[:20]),
            next_steps=[
                f"Save your API key: {raw_key}",
                "Set it as AGENCITY_API_KEY in your environment",
                "Import your LinkedIn connections: POST /api/companies/{id}/import/linkedin",
                "Start searching: POST /api/search",
            ],
        )

    except Exception as e:
        logger.error(f"Failed to create company: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}", response_model=CompanyWithStats)
async def get_company(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Get a company with all related data."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    company = await company_db.get_company_with_stats(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@router.patch("/{company_id}", response_model=Company)
async def update_company(
    company_id: UUID,
    request: CompanyUpdate,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Update company details."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    company = await company_db.update_company(company_id, request)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


# =============================================================================
# UMO ENDPOINTS
# =============================================================================

@router.put("/{company_id}/umo", response_model=CompanyUMO)
async def update_umo(
    company_id: UUID,
    request: UpdateUMORequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Create or update a company's UMO (Unique Mandate Objective)."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        umo_data = CompanyUMOCreate(
            preferred_backgrounds=request.preferred_backgrounds,
            must_have_traits=request.must_have_traits,
            anti_patterns=request.anti_patterns,
            culture_values=request.culture_values,
            work_style=request.work_style,
            ideal_candidate_description=request.ideal_candidate_description,
        )

        umo = await company_db.create_or_update_umo(company_id, umo_data)

        logger.info(f"Updated UMO for company: {company_id}")

        return umo

    except Exception as e:
        logger.error(f"Failed to update UMO: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/umo", response_model=Optional[CompanyUMO])
async def get_umo(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Get a company's UMO."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    umo = await company_db.get_company_umo(company_id)
    return umo


# =============================================================================
# ROLE ENDPOINTS
# =============================================================================

@router.post("/{company_id}/roles", response_model=Role)
async def create_role(
    company_id: UUID,
    request: CreateRoleRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Create a new role for a company."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    try:
        from app.models.company import RoleLevel

        level = None
        if request.level:
            try:
                level = RoleLevel(request.level)
            except ValueError:
                pass

        role_data = RoleCreate(
            title=request.title,
            level=level,
            department=request.department,
            required_skills=request.required_skills,
            preferred_skills=request.preferred_skills,
            years_experience_min=request.years_experience_min,
            years_experience_max=request.years_experience_max,
            description=request.description,
            location=request.location,
            salary_min=request.salary_min,
            salary_max=request.salary_max,
        )

        role = await company_db.create_role(company_id, role_data)

        logger.info(f"Created role: {role.id} - {role.title} for company: {company_id}")

        return role

    except Exception as e:
        logger.error(f"Failed to create role: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}/roles", response_model=list[Role])
async def get_roles(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Get all roles for a company."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    roles = await company_db.get_roles(company_id)
    return roles


# =============================================================================
# IMPORT ENDPOINTS
# =============================================================================

@router.post("/{company_id}/import/linkedin", response_model=ImportResult)
async def import_linkedin(
    company_id: UUID,
    file: UploadFile = File(...),
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Import LinkedIn connections from a CSV file.

    Expected CSV format:
    First Name,Last Name,URL,Email Address,Company,Position,Connected On
    """
    from app.data.importers.linkedin_csv import LinkedInImporter

    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        content = await file.read()
        csv_text = content.decode("utf-8")

        importer = LinkedInImporter()
        result = await importer.import_csv(company_id, csv_text, file.filename)

        # Update company status
        await company_db.update_company(
            company_id,
            CompanyUpdate(linkedin_imported=True),
        )

        logger.info(f"Imported LinkedIn connections for company: {company_id}")

        return result

    except Exception as e:
        logger.error(f"Failed to import LinkedIn: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{company_id}/import/database", response_model=ImportResult)
async def import_database(
    company_id: UUID,
    file: UploadFile = File(...),
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Import company's existing database from a CSV file.

    Expected CSV format:
    name,email,linkedin_url,company,title,skills,notes
    """
    from app.data.importers.company_db_importer import CompanyDBImporter

    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        content = await file.read()
        csv_text = content.decode("utf-8")

        importer = CompanyDBImporter()
        result = await importer.import_csv(company_id, csv_text, file.filename)

        # Update company status
        await company_db.update_company(
            company_id,
            CompanyUpdate(existing_db_imported=True),
        )

        logger.info(f"Imported company database for company: {company_id}")

        return result

    except Exception as e:
        logger.error(f"Failed to import database: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# PEOPLE ENDPOINTS
# =============================================================================

@router.get("/{company_id}/people")
async def get_people(
    company_id: UUID,
    limit: int = 50,
    offset: int = 0,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Get people in a company's database."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    people = await company_db.get_people(company_id, limit=limit, offset=offset)
    count = await company_db.count_people(company_id)

    return {
        "people": people,
        "total": count,
        "limit": limit,
        "offset": offset,
    }


@router.get("/{company_id}/imports")
async def get_imports(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Get import history for a company."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")
    sources = await company_db.get_data_sources(company_id)
    return sources


# =============================================================================
# ONBOARDING STATUS
# =============================================================================

@router.post("/{company_id}/complete-onboarding")
async def complete_onboarding(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Mark onboarding as complete."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await company_db.update_company(
        company_id,
        CompanyUpdate(onboarding_complete=True),
    )

    return {"status": "ok", "message": "Onboarding completed"}


# =============================================================================
# API KEY MANAGEMENT
# =============================================================================

class CreateApiKeyRequest(BaseModel):
    """Request to create a new API key."""
    name: str = "default"


@router.post("/{company_id}/api-keys")
async def create_company_api_key(
    company_id: UUID,
    request: CreateApiKeyRequest,
    auth: CompanyAuth = Depends(get_current_company),
):
    """
    Generate a new API key for this company.

    The raw key is returned only once — save it immediately.
    """
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    raw_key, key_record = await create_api_key(
        company_id=str(company_id),
        name=request.name,
    )

    return {
        "api_key": raw_key,
        "api_key_prefix": key_record.get("key_prefix", raw_key[:20]),
        "name": request.name,
        "id": key_record.get("id"),
    }


@router.get("/{company_id}/api-keys")
async def list_api_keys(
    company_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """List all API keys for this company (prefix only, never raw key)."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    from app.core.database import get_supabase_client
    supabase = get_supabase_client()

    result = supabase.table("api_keys").select(
        "id, key_prefix, name, scopes, is_active, last_used_at, created_at"
    ).eq("company_id", str(company_id)).order("created_at", desc=True).execute()

    return {"api_keys": result.data or []}


@router.delete("/{company_id}/api-keys/{key_id}")
async def revoke_api_key(
    company_id: UUID,
    key_id: UUID,
    auth: CompanyAuth = Depends(get_current_company),
):
    """Revoke (deactivate) an API key."""
    if str(company_id) != auth.company_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Don't let them revoke the key they're currently using
    if str(key_id) == auth.api_key_id:
        raise HTTPException(
            status_code=400,
            detail="Cannot revoke the API key you are currently using",
        )

    from app.core.database import get_supabase_client
    supabase = get_supabase_client()

    result = supabase.table("api_keys").update(
        {"is_active": False}
    ).eq("id", str(key_id)).eq("company_id", str(company_id)).execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="API key not found")

    return {"status": "revoked", "key_id": str(key_id)}
