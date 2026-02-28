"""
Authentication API Routes
"""
import logging
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db
from app.core.config import settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_refresh_token,
    get_password_hash,
    verify_password,
    blacklist_token,
)
from app.db.database import User

logger = logging.getLogger(__name__)
router = APIRouter()

# For refresh token endpoint
refresh_security = HTTPBearer(auto_error=False)


class LoginRequest(BaseModel):
    """Login request"""
    email: EmailStr
    password: str


class RegisterRequest(BaseModel):
    """Register request"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    full_name: str | None = None


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class RefreshRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class UserResponse(BaseModel):
    """User response"""
    id: int
    email: str
    username: str
    full_name: str | None = None
    avatar_url: str | None = None
    is_superuser: bool = False


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens.

    Validates credentials against database and returns:
    - access_token: Short-lived token for API access
    - refresh_token: Longer-lived token for obtaining new access tokens
    """
    # Look up user by email
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if not user or not verify_password(request.password, user.hashed_password):
        # Use generic message to prevent user enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is disabled"
        )

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": "admin" if user.is_superuser else "user"
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(f"User logged in: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user account.

    Creates a new user and returns JWT tokens.
    Password is securely hashed before storage.
    """
    # Check if email already exists
    result = await db.execute(
        select(User).where(User.email == request.email.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # Check if username already exists
    result = await db.execute(
        select(User).where(User.username == request.username.lower())
    )
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )

    # Hash password
    hashed_password = get_password_hash(request.password)

    # Create user
    user = User(
        email=request.email.lower(),
        username=request.username.lower(),
        hashed_password=hashed_password,
        full_name=request.full_name,
        is_active=True,
        is_superuser=False
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    logger.info(f"New user registered: {user.email}")

    # Generate tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": "user"
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.

    Validates the refresh token and returns new access + refresh tokens.
    The old refresh token is invalidated (rotation).
    """
    # Decode refresh token
    payload = decode_refresh_token(request.refresh_token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user ID from token
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify user still exists and is active
    result = await db.execute(
        select(User).where(User.id == int(user_id))
    )
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Blacklist old refresh token (token rotation)
    blacklist_token(request.refresh_token)

    # Generate new tokens
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "username": user.username,
        "role": "admin" if user.is_superuser else "user"
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    logger.info(f"Tokens refreshed for user: {user.email}")

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """Get current authenticated user info"""
    from app.api.deps import get_current_user

    # Use the auth dependency to validate the token
    user = await get_current_user(credentials)

    # Get full user from database
    result = await db.execute(
        select(User).where(User.id == int(user["id"]))
    )
    db_user = result.scalar_one_or_none()

    if not db_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return UserResponse(
        id=db_user.id,
        email=db_user.email,
        username=db_user.username,
        full_name=db_user.full_name,
        avatar_url=db_user.avatar_url,
        is_superuser=db_user.is_superuser
    )


@router.post("/logout")
async def logout(
    db: AsyncSession = Depends(get_db),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())
):
    """
    Logout by blacklisting the current access token.

    The access token will no longer be valid for API calls.
    """
    from app.api.deps import get_current_user

    # Validate token and get user
    user = await get_current_user(credentials)

    # Blacklist the access token
    blacklist_token(credentials.credentials)

    logger.info(f"User logged out: {user.get('email')}")

    return {"success": True, "message": "Logged out successfully"}
