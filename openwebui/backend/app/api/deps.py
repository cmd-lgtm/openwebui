"""
API Dependencies
"""
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Header, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.security import decode_token
from app.core.exceptions import AuthenticationException
from app.db.database import AsyncSessionLocal, User

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Header(None, alias="Authorization")
) -> dict:
    """
    Get current user from JWT token.

    Requires a valid JWT token for all protected endpoints.
    Returns 401 if no token provided or token is invalid/expired.
    """
    # Check if demo mode is enabled (for development only)
    if settings.DEMO_MODE:
        return await _get_demo_user()

    # Require authentication - no token means unauthorized
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer <token>"
    token = credentials.credentials

    # Decode and validate token
    try:
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check token type
        token_type = payload.get("type")
        if token_type == "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Use access token, not refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if token is blacklisted (for logged out users)
        # This would check Redis in production
        # await check_token_blacklisted(token)

        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Optionally verify user still exists and is active in database
        # Commented out for performance - enable in production
        # user = await _get_user_from_db(user_id)
        # if not user or not user.is_active:
        #     raise HTTPException(
        #         status_code=status.HTTP_401_UNAUTHORIZED,
        #         detail="User not found or inactive"
        #     )

        return {
            "id": user_id,
            "email": payload.get("email", ""),
            "username": payload.get("username", ""),
            "role": payload.get("role", "user")
        }

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.warning(f"JWT validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def _get_demo_user() -> dict:
    """Get demo user for development mode"""
    # Try to get demo user from database
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.username == "demo")
        )
        user = result.scalar_one_or_none()

        if user:
            return {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "is_superuser": user.is_superuser
            }

    # Fallback for when demo user doesn't exist
    return {
        "id": "0",
        "email": "demo@example.com",
        "username": "demo",
        "is_superuser": True
    }


async def _get_user_from_db(user_id: str) -> Optional[User]:
    """Get user from database by ID"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.id == int(user_id))
        )
        return result.scalar_one_or_none()


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Header(None, alias="Authorization")
) -> Optional[dict]:
    """
    Get current user if authenticated, None otherwise.

    This endpoint is for routes that can work with or without authentication.
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None
    except Exception:
        return None


async def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Dependency that requires admin privileges"""
    is_admin = current_user.get("is_superuser", False) or current_user.get("role") == "admin"

    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


async def get_db() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
