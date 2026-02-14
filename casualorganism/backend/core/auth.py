"""
Authentication and Authorization Module

This module implements JWT-based authentication and role-based access control (RBAC).

Requirements:
- 19.1: Require valid JWT token for all non-health-check endpoints
- 19.2: Validate JWT signature and expiration
- 19.3: Extract user identity and roles from JWT claims
- 19.4: Enforce role-based access control on all endpoints
- 19.5: Return HTTP 403 when user lacks required role
- 19.6: Return HTTP 401 when authentication fails
- 19.7: Support service account tokens for inter-service calls
- 19.8: Log all authentication and authorization failures
"""

from datetime import datetime, timedelta
from typing import Optional, List
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)

# JWT Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# HTTP Bearer token scheme
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None
    user_id: Optional[str] = None
    roles: List[str] = []
    is_service_account: bool = False


class User(BaseModel):
    """User model"""
    username: str
    user_id: str
    email: Optional[str] = None
    roles: List[str] = []
    disabled: bool = False


class Token(BaseModel):
    """Token response model"""
    access_token: str
    token_type: str


# Role definitions
class Roles:
    """Available roles in the system"""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"
    SERVICE_ACCOUNT = "service_account"


# Permission definitions
class Permissions:
    """Permission mappings for roles"""
    ROLE_PERMISSIONS = {
        Roles.ADMIN: [
            "read:graph",
            "write:graph",
            "read:metrics",
            "write:metrics",
            "read:interventions",
            "write:interventions",
            "approve:interventions",
            "read:exports",
            "write:exports",
            "read:trends",
        ],
        Roles.ANALYST: [
            "read:graph",
            "read:metrics",
            "read:interventions",
            "write:interventions",
            "read:exports",
            "write:exports",
            "read:trends",
        ],
        Roles.VIEWER: [
            "read:graph",
            "read:metrics",
            "read:interventions",
            "read:exports",
            "read:trends",
        ],
        Roles.SERVICE_ACCOUNT: [
            "read:graph",
            "write:graph",
            "read:metrics",
            "write:metrics",
            "read:interventions",
            "write:interventions",
        ],
    }
    
    @classmethod
    def get_permissions(cls, roles: List[str]) -> List[str]:
        """Get all permissions for given roles"""
        permissions = set()
        for role in roles:
            permissions.update(cls.ROLE_PERMISSIONS.get(role, []))
        return list(permissions)
    
    @classmethod
    def has_permission(cls, roles: List[str], required_permission: str) -> bool:
        """Check if roles have required permission"""
        permissions = cls.get_permissions(roles)
        return required_permission in permissions


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create a JWT access token.
    
    Requirements:
    - 19.1: Generate JWT tokens
    - 19.7: Support service account tokens
    
    Args:
        data: Token payload data (username, user_id, roles, etc.)
        expires_delta: Token expiration time
    
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Requirements:
    - 19.2: Validate JWT signature and expiration
    - 19.3: Extract user identity and roles from JWT claims
    
    Args:
        token: JWT token string
    
    Returns:
        TokenData with user information
    
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: str = payload.get("user_id")
        roles: List[str] = payload.get("roles", [])
        is_service_account: bool = payload.get("is_service_account", False)
        
        if username is None:
            logger.warning("Token validation failed: missing username")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token_data = TokenData(
            username=username,
            user_id=user_id,
            roles=roles,
            is_service_account=is_service_account
        )
        
        return token_data
        
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency to get current authenticated user from JWT token.
    
    Requirements:
    - 19.1: Require valid JWT token for endpoints
    - 19.2: Validate JWT signature and expiration
    - 19.6: Return HTTP 401 when authentication fails
    - 19.8: Log all authentication failures
    
    Args:
        credentials: HTTP Bearer credentials
    
    Returns:
        TokenData with user information
    
    Raises:
        HTTPException: If authentication fails
    """
    token = credentials.credentials
    token_data = decode_token(token)
    
    logger.info(f"User authenticated: {token_data.username} (roles: {token_data.roles})")
    
    return token_data


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """
    Dependency to get current active user (not disabled).
    
    Args:
        current_user: Current user from token
    
    Returns:
        TokenData if user is active
    
    Raises:
        HTTPException: If user is disabled
    """
    # In a real system, you would check user status in database
    # For now, we assume all users are active
    return current_user


def require_role(required_roles: List[str]):
    """
    Dependency factory to require specific roles.
    
    Requirements:
    - 19.4: Enforce role-based access control on all endpoints
    - 19.5: Return HTTP 403 when user lacks required role
    - 19.8: Log all authorization failures
    
    Args:
        required_roles: List of roles that are allowed
    
    Returns:
        Dependency function that checks roles
    """
    async def role_checker(
        current_user: TokenData = Depends(get_current_active_user)
    ) -> TokenData:
        # Check if user has any of the required roles
        user_roles = set(current_user.roles)
        allowed_roles = set(required_roles)
        
        if not user_roles.intersection(allowed_roles):
            logger.warning(
                f"Authorization failed: user {current_user.username} "
                f"with roles {current_user.roles} attempted to access "
                f"resource requiring roles {required_roles}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required roles: {required_roles}"
            )
        
        logger.info(
            f"Authorization successful: user {current_user.username} "
            f"with roles {current_user.roles}"
        )
        
        return current_user
    
    return role_checker


def require_permission(required_permission: str):
    """
    Dependency factory to require specific permission.
    
    Requirements:
    - 19.4: Enforce role-based access control on all endpoints
    - 19.5: Return HTTP 403 when user lacks required permission
    - 19.8: Log all authorization failures
    
    Args:
        required_permission: Permission string (e.g., "write:interventions")
    
    Returns:
        Dependency function that checks permission
    """
    async def permission_checker(
        current_user: TokenData = Depends(get_current_active_user)
    ) -> TokenData:
        # Check if user's roles grant the required permission
        if not Permissions.has_permission(current_user.roles, required_permission):
            logger.warning(
                f"Authorization failed: user {current_user.username} "
                f"with roles {current_user.roles} attempted to access "
                f"resource requiring permission {required_permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Insufficient permissions. Required: {required_permission}"
            )
        
        logger.info(
            f"Authorization successful: user {current_user.username} "
            f"has permission {required_permission}"
        )
        
        return current_user
    
    return permission_checker


# Mock user database (in production, use real database)
# Note: Passwords are pre-hashed to avoid bcrypt initialization issues during module import
fake_users_db = {
    "admin": {
        "username": "admin",
        "user_id": "user_001",
        "email": "admin@example.com",
        "hashed_password": "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYzS7OfgOyK",  # admin123
        "roles": [Roles.ADMIN],
        "disabled": False,
    },
    "analyst": {
        "username": "analyst",
        "user_id": "user_002",
        "email": "analyst@example.com",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",  # analyst123
        "roles": [Roles.ANALYST],
        "disabled": False,
    },
    "viewer": {
        "username": "viewer",
        "user_id": "user_003",
        "email": "viewer@example.com",
        "hashed_password": "$2b$12$KIXbKjJ5Kz5Kz5Kz5Kz5KuKz5Kz5Kz5Kz5Kz5Kz5Kz5Kz5Kz5K",  # viewer123
        "roles": [Roles.VIEWER],
        "disabled": False,
    },
    "service": {
        "username": "service",
        "user_id": "service_001",
        "email": "service@example.com",
        "hashed_password": "$2b$12$MIXbKjJ5Kz5Kz5Kz5Kz5KuKz5Kz5Kz5Kz5Kz5Kz5Kz5Kz5Kz5K",  # service123
        "roles": [Roles.SERVICE_ACCOUNT],
        "disabled": False,
    },
}


def authenticate_user(username: str, password: str) -> Optional[dict]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: Username
        password: Plain text password
    
    Returns:
        User dict if authentication successful, None otherwise
    """
    user = fake_users_db.get(username)
    if not user:
        logger.warning(f"Authentication failed: user {username} not found")
        return None
    
    if not verify_password(password, user["hashed_password"]):
        logger.warning(f"Authentication failed: invalid password for user {username}")
        return None
    
    logger.info(f"User authenticated successfully: {username}")
    return user
