"""
Security utilities - JWT, password hashing, etc.
"""
import logging
import secrets
from datetime import datetime, timedelta
from typing import Optional, Set

from jose import JWTError, jwt, ExpiredSignatureError
from passlib.context import CryptContext

from app.core.config import settings

logger = logging.getLogger(__name__)

# Password hashing - using bcrypt (consider argon2 for production)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory token blacklist (use Redis in production)
# Format: {token_jti} for faster lookup
_token_blacklist: Set[str] = set()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token with proper claims"""
    to_encode = data.copy()

    # Set expiration
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    # Add standard claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16),  # Unique token ID for revocation
        "type": "access"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token with proper claims"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "jti": secrets.token_urlsafe(16),  # Unique token ID for revocation
        "type": "refresh"
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[dict]:
    """
    Decode and verify JWT token.

    Returns payload if valid, None if invalid or expired.
    Does NOT check blacklist - call is_token_blacklisted separately.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except JWTError as e:
        logger.warning(f"JWT decode error: {e}")
        return None


def is_token_blacklisted(token: str) -> bool:
    """Check if a token has been blacklisted (logged out)"""
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}  # Allow expired tokens to be checked
        )
        jti = payload.get("jti")
        return jti in _token_blacklist if jti else False
    except JWTError:
        return True  # Invalid tokens are considered blacklisted


def blacklist_token(token: str) -> bool:
    """
    Add a token to the blacklist (for logout).

    In production, this should store in Redis with TTL matching token expiration.
    Returns True if successfully blacklisted.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            options={"verify_exp": False}
        )
        jti = payload.get("jti")
        if jti:
            _token_blacklist.add(jti)
            logger.info(f"Token blacklisted: {jti[:8]}...")
            return True
        return False
    except JWTError as e:
        logger.warning(f"Failed to blacklist token: {e}")
        return False


def generate_api_key() -> str:
    """Generate a secure API key"""
    return f"nxai_{secrets.token_urlsafe(32)}"


def verify_api_key(api_key: str) -> bool:
    """Verify an API key format"""
    return api_key.startswith("nxai_") and len(api_key) > 20


def decode_refresh_token(token: str) -> Optional[dict]:
    """
    Decode and verify refresh token.

    Returns payload if valid, None if invalid or expired.
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Verify token type
        if payload.get("type") != "refresh":
            return None

        return payload
    except ExpiredSignatureError:
        logger.debug("Refresh token expired")
        return None
    except JWTError as e:
        logger.warning(f"Refresh token decode error: {e}")
        return None
