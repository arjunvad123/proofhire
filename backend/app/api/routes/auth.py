"""Authentication routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.hashing import hash_password, verify_password
from app.core.security import create_access_token, create_refresh_token
from app.core.ids import generate_id
from app.db.session import get_db
from app.db.models import User, Org, Membership, MembershipRole
from app.deps import CurrentUser

router = APIRouter()


class RegisterRequest(BaseModel):
    """User registration request."""

    email: EmailStr
    password: str
    name: str | None = None


class LoginRequest(BaseModel):
    """User login request."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """User response model."""

    id: str
    email: str
    name: str | None
    is_active: bool
    org_id: str | None = None

    class Config:
        from_attributes = True


class OrgResponse(BaseModel):
    """Organization response model."""

    id: str
    name: str

    class Config:
        from_attributes = True


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Register a new user and auto-create their organization."""
    # Check if email already exists
    result = await db.execute(select(User).where(User.email == request.email))
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    # Create user
    user = User(
        id=generate_id(),
        email=request.email,
        password_hash=hash_password(request.password),
        name=request.name,
    )
    db.add(user)
    await db.flush()

    # Auto-create organization for the user
    org_name = f"{request.name}'s Company" if request.name else "My Company"
    org = Org(
        id=generate_id(),
        name=org_name,
    )
    db.add(org)
    await db.flush()

    # Create membership (user is owner of their org)
    membership = Membership(
        id=generate_id(),
        org_id=org.id,
        user_id=user.id,
        role=MembershipRole.OWNER,
    )
    db.add(membership)

    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TokenResponse:
    """Login and get JWT tokens."""
    # Find user by email
    result = await db.execute(select(User).where(User.email == request.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    # Generate tokens
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)

    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserResponse:
    """Get current user information including their org."""
    # Get user's org membership
    result = await db.execute(
        select(Membership).where(Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    user_response = UserResponse.model_validate(current_user)
    if membership:
        user_response.org_id = membership.org_id
    return user_response


@router.get("/me/org", response_model=OrgResponse)
async def get_current_user_org(
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> OrgResponse:
    """Get current user's organization."""
    # Get user's org membership
    result = await db.execute(
        select(Membership).where(Membership.user_id == current_user.id)
    )
    membership = result.scalar_one_or_none()

    if not membership:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User has no organization",
        )

    # Get the org
    result = await db.execute(select(Org).where(Org.id == membership.org_id))
    org = result.scalar_one_or_none()

    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return OrgResponse.model_validate(org)


@router.post("/logout")
async def logout() -> dict[str, str]:
    """Logout (client should discard tokens)."""
    # With JWT, logout is handled client-side by discarding tokens
    # For production, consider token blacklisting
    return {"message": "Logged out successfully"}
