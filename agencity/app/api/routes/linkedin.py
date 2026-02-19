"""
API endpoints for LinkedIn automation.

Handles:
- Session connection/disconnection
- Connection extraction
- Profile enrichment
- DM automation
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
from app.core.database import get_supabase_client
from app.services.linkedin.session_manager import LinkedInSessionManager
from app.services.linkedin.credential_auth import LinkedInCredentialAuth
from app.services.linkedin.encryption import CookieEncryption
from app.services.linkedin.proxy_manager import ProxyManager


router = APIRouter(prefix="/api/v1/linkedin", tags=["linkedin"])


# --- Request/Response Models ---

class ConnectRequest(BaseModel):
    """Request to connect LinkedIn via Chrome extension."""
    company_id: str
    user_id: str
    cookies: Dict[str, Any]
    user_timezone: Optional[str] = None
    user_location: Optional[str] = None


class ConnectCredentialsRequest(BaseModel):
    """Request to connect LinkedIn via direct credentials."""
    company_id: str
    user_id: str
    email: EmailStr
    password: str
    user_timezone: Optional[str] = None
    user_location: Optional[str] = None


class Submit2FARequest(BaseModel):
    """Request to submit 2FA verification code."""
    company_id: str
    user_id: str
    verification_code: str
    verification_state: Dict[str, Any]


class ConnectResponse(BaseModel):
    """Response after connecting LinkedIn."""
    status: str
    session_id: Optional[str] = None
    linkedin_name: Optional[str] = None
    expires_at: Optional[str] = None
    message: str
    verification_state: Optional[Dict[str, Any]] = None


class RefreshRequest(BaseModel):
    """Request to refresh session cookies."""
    cookies: Dict[str, Any]


class SessionStatusResponse(BaseModel):
    """Session status response."""
    status: str
    health: Optional[str] = None
    connections_extracted: int = 0
    profiles_enriched: int = 0
    messages_sent: int = 0
    expires_at: Optional[str] = None
    last_activity_at: Optional[str] = None
    paused_until: Optional[str] = None
    message: Optional[str] = None


class DisconnectResponse(BaseModel):
    """Response after disconnecting."""
    status: str
    message: str


class ExtractConnectionsRequest(BaseModel):
    """Request to start connection extraction."""
    session_id: str


class ExtractConnectionsResponse(BaseModel):
    """Response after starting extraction."""
    job_id: str
    status: str
    estimated_time_minutes: int


class PrioritizeRequest(BaseModel):
    """Request to prioritize connections."""
    company_id: str
    role_id: str


class PrioritizeResponse(BaseModel):
    """Response after prioritizing connections."""
    total_connections: int
    tier_1_count: int
    tier_2_count: int
    tier_3_count: int
    top_companies: List[str]
    avg_priority_score: float


# --- Dependency ---

def get_session_manager() -> LinkedInSessionManager:
    """Dependency to get session manager."""
    supabase = get_supabase_client()
    return LinkedInSessionManager(supabase)


# --- Endpoints ---

@router.post("/connect", response_model=ConnectResponse)
async def connect_linkedin(
    request: ConnectRequest,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    Connect LinkedIn account via Chrome extension cookies.

    This endpoint is called by the Chrome extension when user
    authorizes Agencity to access their LinkedIn.

    The cookies are encrypted and stored securely.
    """
    try:
        result = await session_manager.create_session(
            company_id=request.company_id,
            user_id=request.user_id,
            cookies=request.cookies,
            user_timezone=request.user_timezone,
            user_location=request.user_location
        )

        return ConnectResponse(
            status=result['status'],
            session_id=result['session_id'],
            linkedin_name=result.get('linkedin_name'),
            expires_at=result['expires_at'],
            message=result['message']
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to connect: {str(e)}")


@router.post("/connect-credentials", response_model=ConnectResponse)
async def connect_linkedin_credentials(
    request: ConnectCredentialsRequest,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    Connect LinkedIn account via direct credentials (email + password).

    This is the zero-friction onboarding method that doesn't require
    a Chrome extension.

    Flow:
    1. User enters email + password
    2. Backend logs in via Playwright
    3. If 2FA required, return verification_state and status='2fa_required'
    4. If successful, return session_id and status='connected'

    The password is NEVER stored - only session cookies are kept.
    """
    try:
        # Initialize credential auth
        auth = LinkedInCredentialAuth()

        # Attempt login — pass user_id so a persistent browser profile is used,
        # meaning LinkedIn only sends a sign-in email on the very first connect.
        result = await auth.login(
            email=request.email,
            password=request.password,
            user_id=request.user_id,
            user_location=request.user_location
        )

        # Handle different outcomes
        if result['status'] == '2fa_required':
            # Need 2FA code from user
            return ConnectResponse(
                status='2fa_required',
                message=result.get('message', 'Please enter verification code'),
                verification_state=result.get('verification_state')
            )

        elif result['status'] == 'connected':
            # Success! Store session
            cookies = result['cookies']

            session_result = await session_manager.create_session(
                company_id=request.company_id,
                user_id=request.user_id,
                cookies=cookies,
                user_timezone=request.user_timezone,
                user_location=request.user_location
            )

            return ConnectResponse(
                status='connected',
                session_id=session_result['session_id'],
                linkedin_name=session_result.get('linkedin_name'),
                expires_at=session_result['expires_at'],
                message='LinkedIn connected successfully via credentials'
            )

        else:
            # Error
            raise HTTPException(
                status_code=400,
                detail=result.get('error', 'Login failed')
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to authenticate: {str(e)}")


@router.post("/submit-2fa-code", response_model=ConnectResponse)
async def submit_2fa_code(
    request: Submit2FARequest,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    Submit 2FA verification code to complete login.

    This is called after /connect-credentials returns '2fa_required'.
    The frontend collects the 6-digit code from user and submits it here.
    """
    try:
        # Initialize credential auth
        auth = LinkedInCredentialAuth()

        # Resume login with 2FA code — pass user_id to reuse the same persistent
        # browser profile that was used in /connect-credentials.
        result = await auth.login(
            email='',  # Not needed for resume
            password='',  # Not needed for resume
            user_id=request.user_id,
            verification_code=request.verification_code,
            resume_state=request.verification_state
        )

        if result['status'] == 'connected':
            # Success! Store session
            cookies = result['cookies']

            session_result = await session_manager.create_session(
                company_id=request.company_id,
                user_id=request.user_id,
                cookies=cookies,
                user_timezone=None,
                user_location=None
            )

            return ConnectResponse(
                status='connected',
                session_id=session_result['session_id'],
                linkedin_name=session_result.get('linkedin_name'),
                expires_at=session_result['expires_at'],
                message='LinkedIn connected successfully with 2FA'
            )

        else:
            # Error
            raise HTTPException(
                status_code=400,
                detail=result.get('error', '2FA verification failed')
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to verify 2FA: {str(e)}")


@router.get("/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(
    session_id: str,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    Get status of a LinkedIn session.

    Returns connection status, health, and usage statistics.
    """
    try:
        status = await session_manager.get_session_status(session_id)
        return SessionStatusResponse(**status)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get status: {str(e)}")


@router.post("/session/{session_id}/refresh")
async def refresh_session(
    session_id: str,
    request: RefreshRequest,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    Refresh session with new cookies.

    Called when user revisits LinkedIn and extension captures fresh cookies.
    Extends session expiration.
    """
    try:
        result = await session_manager.refresh_session(session_id, request.cookies)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to refresh: {str(e)}")


@router.delete("/session/{session_id}", response_model=DisconnectResponse)
async def disconnect_linkedin(
    session_id: str,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    Disconnect LinkedIn session.

    Clears stored cookies and marks session as disconnected.
    User can reconnect anytime via Chrome extension.
    """
    try:
        result = await session_manager.delete_session(session_id)
        return DisconnectResponse(
            status=result['status'],
            message=result['message']
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to disconnect: {str(e)}")


@router.post("/session/{session_id}/pause")
async def pause_session(
    session_id: str,
    hours: int = 72,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    Pause a session (e.g., after detecting LinkedIn warning).

    Session will automatically resume after the pause period.
    Default pause is 72 hours.
    """
    try:
        result = await session_manager.pause_session(session_id, hours)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to pause: {str(e)}")


@router.get("/sessions/{company_id}")
async def list_sessions(
    company_id: str,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    List all LinkedIn sessions for a company.

    Returns basic info about each connected LinkedIn account.
    """
    try:
        sessions = await session_manager.get_active_sessions(company_id)
        return {
            'sessions': sessions,
            'count': len(sessions)
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")


# --- Connection Extraction Endpoints (Phase 2 Placeholder) ---

@router.post("/extract-connections", response_model=ExtractConnectionsResponse)
async def start_connection_extraction(
    request: ExtractConnectionsRequest,
    background_tasks: BackgroundTasks,
    session_manager: LinkedInSessionManager = Depends(get_session_manager)
):
    """
    Start extracting LinkedIn connections.

    This runs in the background and extracts all connections
    from the user's LinkedIn network.

    Phase 2: Implement actual extraction logic
    """
    # Verify session exists and is active
    session = await session_manager.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if session['status'] != 'active':
        raise HTTPException(status_code=400, detail=f"Session is {session['status']}")

    # Create extraction job
    supabase = get_supabase_client()
    job_result = supabase.table('connection_extraction_jobs').insert({
        'session_id': request.session_id,
        'status': 'pending'
    }).execute()

    if not job_result.data:
        raise HTTPException(status_code=500, detail="Failed to create extraction job")

    job_id = job_result.data[0]['id']

    # TODO: Add background task to run extraction
    # background_tasks.add_task(run_connection_extraction, job_id, request.session_id)

    return ExtractConnectionsResponse(
        job_id=job_id,
        status='started',
        estimated_time_minutes=15  # Estimate based on average network size
    )


@router.get("/extraction/{job_id}/status")
async def get_extraction_status(job_id: str):
    """
    Get status of a connection extraction job.
    """
    supabase = get_supabase_client()
    result = supabase.table('connection_extraction_jobs')\
        .select('*')\
        .eq('id', job_id)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Job not found")

    job = result.data[0]

    return {
        'status': job['status'],
        'connections_found': job.get('connections_found', 0),
        'progress_percentage': _calculate_progress(job),
        'estimated_remaining_minutes': _estimate_remaining(job),
        'error_message': job.get('error_message')
    }


def _calculate_progress(job: dict) -> int:
    """Calculate extraction progress percentage."""
    if job['status'] == 'completed':
        return 100
    if job['status'] == 'pending':
        return 0

    # Estimate based on connections found (assuming ~3000 average)
    found = job.get('connections_found', 0)
    return min(int(found / 30), 99)  # Cap at 99 until complete


def _estimate_remaining(job: dict) -> int:
    """Estimate remaining minutes."""
    if job['status'] in ['completed', 'failed']:
        return 0
    if job['status'] == 'pending':
        return 15

    # Rough estimate based on progress
    progress = _calculate_progress(job)
    if progress == 0:
        return 15

    # Linear estimate
    return max(1, int(15 * (100 - progress) / 100))


# --- Prioritization Endpoints (Phase 3 Placeholder) ---

@router.post("/prioritize", response_model=PrioritizeResponse)
async def prioritize_connections(request: PrioritizeRequest):
    """
    Prioritize connections for a role.

    Scores all connections and assigns to tiers:
    - Tier 1: High priority, immediate enrichment
    - Tier 2: Medium priority, on-demand enrichment
    - Tier 3: Low priority, background enrichment

    Phase 3: Implement scoring algorithm
    """
    supabase = get_supabase_client()

    # Get connections for company
    connections = supabase.table('linkedin_connections')\
        .select('id, current_title, current_company, headline, location')\
        .eq('company_id', request.company_id)\
        .execute()

    if not connections.data:
        raise HTTPException(
            status_code=404,
            detail="No connections found. Run extraction first."
        )

    # Get role details
    role = supabase.table('roles')\
        .select('title, required_skills, location')\
        .eq('id', request.role_id)\
        .execute()

    if not role.data:
        raise HTTPException(status_code=404, detail="Role not found")

    # TODO: Implement actual scoring in Phase 3
    # For now, return placeholder response
    total = len(connections.data)

    return PrioritizeResponse(
        total_connections=total,
        tier_1_count=min(200, total),
        tier_2_count=min(500, max(0, total - 200)),
        tier_3_count=max(0, total - 700),
        top_companies=['Placeholder - Phase 3'],
        avg_priority_score=50.0
    )


# --- Proxy Health Check ---

@router.get("/proxy/status")
async def proxy_status(location: Optional[str] = None):
    """
    Check proxy configuration and connectivity.

    Returns whether a proxy is configured, and if so, tests
    connectivity and reports the exit IP and country.

    Query params:
        location (optional): User location to test geo-targeting
    """
    pm = ProxyManager()

    if not pm.is_configured:
        return {
            "configured": False,
            "provider": None,
            "message": "No proxy configured. Set PROXY_PROVIDER, PROXY_USERNAME, "
                       "PROXY_PASSWORD in your .env file."
        }

    proxy = pm.get_proxy_for_location(location=location, sticky_session_id="health_check")

    health = await pm.check_proxy_health(proxy)

    return {
        "configured": True,
        "provider": pm.provider,
        "target_location": location or "default (us)",
        "health": health,
    }
