"""
Authentication Endpoints

This module provides authentication endpoints for login and token management.

Requirements:
- 19.1: Require valid JWT token for all non-health-check endpoints
- 19.2: Validate JWT signature and expiration
- 19.6: Return HTTP 401 when authentication fails
- 19.7: Support service account tokens for inter-service calls
- 19.8: Log all authentication and authorization failures
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from typing import List
from datetime import timedelta

from backend.core.auth import (
    authenticate_user,
    create_access_token,
    get_current_user,
    Token,
    TokenData,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Roles,
    Permissions,
)

router = APIRouter(prefix="/auth", tags=["authentication"])


class LoginRequest(BaseModel):
    """Login request model"""
    username: str
    password: str


class ServiceAccountTokenRequest(BaseModel):
    """Service account token request"""
    service_name: str
    service_secret: str


@router.post("/login", response_model=Token)
async def login(login_request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Requirements:
    - 19.1: Generate JWT tokens for authenticated users
    - 19.6: Return HTTP 401 when authentication fails
    - 19.8: Log all authentication failures
    
    Args:
        login_request: Username and password
    
    Returns:
        JWT access token
    
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(login_request.username, login_request.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "user_id": user["user_id"],
            "roles": user["roles"],
            "is_service_account": False,
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token endpoint.
    
    Requirements:
    - 19.1: Generate JWT tokens for authenticated users
    - 19.6: Return HTTP 401 when authentication fails
    
    Args:
        form_data: OAuth2 password form data
    
    Returns:
        JWT access token
    
    Raises:
        HTTPException: If authentication fails
    """
    user = authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": user["username"],
            "user_id": user["user_id"],
            "roles": user["roles"],
            "is_service_account": False,
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/service-token", response_model=Token)
async def create_service_account_token(request: ServiceAccountTokenRequest):
    """
    Create a service account token for inter-service communication.
    
    Requirements:
    - 19.7: Support service account tokens for inter-service calls
    
    Args:
        request: Service account credentials
    
    Returns:
        JWT access token for service account
    
    Raises:
        HTTPException: If authentication fails
    """
    # In production, validate service account credentials against secure storage
    # For now, use a simple check
    expected_secret = "service-secret-change-in-production"
    
    if request.service_secret != expected_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid service account credentials",
        )
    
    # Create long-lived service account token (24 hours)
    access_token_expires = timedelta(hours=24)
    access_token = create_access_token(
        data={
            "sub": request.service_name,
            "user_id": f"service_{request.service_name}",
            "roles": [Roles.SERVICE_ACCOUNT],
            "is_service_account": True,
        },
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me")
async def read_users_me(current_user: TokenData = Depends(get_current_user)):
    """
    Get current user information.
    
    Requirements:
    - 19.1: Require valid JWT token
    - 19.3: Extract user identity and roles from JWT claims
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User information
    """
    return {
        "username": current_user.username,
        "user_id": current_user.user_id,
        "roles": current_user.roles,
        "is_service_account": current_user.is_service_account,
        "permissions": Permissions.get_permissions(current_user.roles),
    }


@router.get("/roles")
async def list_roles(current_user: TokenData = Depends(get_current_user)):
    """
    List all available roles and their permissions.
    
    Requirements:
    - 19.1: Require valid JWT token
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        Dictionary of roles and permissions
    """
    return {
        "roles": {
            Roles.ADMIN: {
                "name": "Administrator",
                "description": "Full system access",
                "permissions": Permissions.ROLE_PERMISSIONS[Roles.ADMIN],
            },
            Roles.ANALYST: {
                "name": "Analyst",
                "description": "Can analyze data and create interventions",
                "permissions": Permissions.ROLE_PERMISSIONS[Roles.ANALYST],
            },
            Roles.VIEWER: {
                "name": "Viewer",
                "description": "Read-only access",
                "permissions": Permissions.ROLE_PERMISSIONS[Roles.VIEWER],
            },
            Roles.SERVICE_ACCOUNT: {
                "name": "Service Account",
                "description": "Inter-service communication",
                "permissions": Permissions.ROLE_PERMISSIONS[Roles.SERVICE_ACCOUNT],
            },
        }
    }
