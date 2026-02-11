"""
Company API routes for onboarding and management.

Handles Stage 0 (Onboarding) and Stage 1 (Data Import).
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

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

@router.post("", response_model=Company)
async def create_company(request: CreateCompanyRequest):
    """
    Create a new company and start onboarding.

    This is the first step of Stage 0.
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

        return company

    except Exception as e:
        logger.error(f"Failed to create company: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{company_id}", response_model=CompanyWithStats)
async def get_company(company_id: UUID):
    """
    Get a company with all related data.

    Returns the company with UMO, roles, and import stats.
    """
    company = await company_db.get_company_with_stats(company_id)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company


@router.patch("/{company_id}", response_model=Company)
async def update_company(company_id: UUID, request: CompanyUpdate):
    """
    Update company details.
    """
    company = await company_db.update_company(company_id, request)

    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    return company


# =============================================================================
# UMO ENDPOINTS
# =============================================================================

@router.put("/{company_id}/umo", response_model=CompanyUMO)
async def update_umo(company_id: UUID, request: UpdateUMORequest):
    """
    Create or update a company's UMO (Unique Mandate Objective).

    This captures what the company is looking for in candidates.
    """
    # Verify company exists
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
async def get_umo(company_id: UUID):
    """
    Get a company's UMO.
    """
    umo = await company_db.get_company_umo(company_id)
    return umo


# =============================================================================
# ROLE ENDPOINTS
# =============================================================================

@router.post("/{company_id}/roles", response_model=Role)
async def create_role(company_id: UUID, request: CreateRoleRequest):
    """
    Create a new role for a company.
    """
    # Verify company exists
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
async def get_roles(company_id: UUID):
    """
    Get all roles for a company.
    """
    roles = await company_db.get_roles(company_id)
    return roles


# =============================================================================
# IMPORT ENDPOINTS
# =============================================================================

@router.post("/{company_id}/import/linkedin", response_model=ImportResult)
async def import_linkedin(
    company_id: UUID,
    file: UploadFile = File(...),
):
    """
    Import LinkedIn connections from a CSV file.

    Expected CSV format:
    First Name,Last Name,URL,Email Address,Company,Position,Connected On
    """
    from app.data.importers.linkedin_csv import LinkedInImporter

    # Verify company exists
    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Read file content
        content = await file.read()
        csv_text = content.decode("utf-8")

        # Import
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
):
    """
    Import company's existing database from a CSV file.

    Expected CSV format:
    name,email,linkedin_url,company,title,skills,notes
    """
    from app.data.importers.company_db_importer import CompanyDBImporter

    # Verify company exists
    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Validate file type
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV")

    try:
        # Read file content
        content = await file.read()
        csv_text = content.decode("utf-8")

        # Import
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
):
    """
    Get people in a company's database.
    """
    # Verify company exists
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
async def get_imports(company_id: UUID):
    """
    Get import history for a company.
    """
    sources = await company_db.get_data_sources(company_id)
    return sources


# =============================================================================
# ONBOARDING STATUS
# =============================================================================

@router.post("/{company_id}/complete-onboarding")
async def complete_onboarding(company_id: UUID):
    """
    Mark onboarding as complete.

    Called after all steps are done.
    """
    company = await company_db.get_company(company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    await company_db.update_company(
        company_id,
        CompanyUpdate(onboarding_complete=True),
    )

    return {"status": "ok", "message": "Onboarding completed"}
