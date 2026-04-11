"""Authentication utilities for JWT and password hashing.

Provides password hashing, JWT token creation/validation, and FastAPI
dependency for retrieving the current authenticated user.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from app.config import Settings, get_settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["scrypt"], deprecated="auto")

security = HTTPBearer()


class TokenPayload(BaseModel):
    """Parsed JWT payload."""

    sub: str
    exp: datetime


def hash_password(password: str) -> str:
    """Hash a password using bcrypt.

    Args:
        password: Plain-text password.

    Returns:
        Bcrypt-hashed password string.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a bcrypt hash.

    Args:
        plain_password: Plain-text password to check.
        hashed_password: Bcrypt hash to verify against.

    Returns:
        True if the password matches.
    """
    return pwd_context.verify(plain_password, hashed_password)


# ---------------------------------------------------------------------------
# JWT token helpers
# ---------------------------------------------------------------------------

def create_access_token(
    subject: str,
    secret_key: str,
    expires_delta: timedelta | None = None,
) -> str:
    """Create a JWT access token.

    Args:
        subject: Token subject (typically username or user ID).
        secret_key: Signing secret.
        expires_delta: Token lifetime. Defaults to 24 hours.

    Returns:
        Encoded JWT string.
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=24)

    expire = datetime.now(timezone.utc) + expires_delta
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, secret_key, algorithm="HS256")


def decode_access_token(
    token: str,
    secret_key: str,
) -> TokenPayload:
    """Decode and validate a JWT access token.

    Args:
        token: JWT string.
        secret_key: Signing secret.

    Returns:
        Parsed TokenPayload with subject and expiry.

    Raises:
        HTTPException: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, secret_key, algorithms=["HS256"])
        sub = payload.get("sub")
        if sub is None:
            raise JWTError("Token missing subject")
        return TokenPayload(sub=sub, exp=datetime.fromtimestamp(payload["exp"], tz=timezone.utc))
    except JWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证令牌",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    settings: Settings = Depends(get_settings),
) -> str:
    """Extract and validate the current user from the Authorization header.

    Returns the username (sub claim) if the token is valid.

    Args:
        credentials: Bearer token from the Authorization header.
        settings: Application settings (provides JWT secret).

    Returns:
        The authenticated username.

    Raises:
        HTTPException: 401 if token is missing, invalid, or expired.
    """
    payload = decode_access_token(credentials.credentials, settings.jwt_secret_key)
    return payload.sub
