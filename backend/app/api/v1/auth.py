"""Authentication endpoints.

Provides user registration, login, token refresh, and current-user lookup.
"""
from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.db.session import get_session_factory
from app.models.user import User

router = APIRouter()


def _get_db():
    """Get an async database session.

    Returns a context manager for the session lifecycle.
    """
    settings = __import__("app.config", fromlist=["get_settings"]).get_settings()
    factory = get_session_factory(settings.database_url)
    return factory


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=30)
    email: str | None = None
    password: str = Field(..., min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    username: str
    email: str | None = None
    is_active: bool


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post(
    "/auth/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
async def register(request: RegisterRequest) -> UserResponse:
    """Create a new user account.

    The user is stored in PostgreSQL with a scrypt-hashed password.
    """
    factory = _get_db()

    async with factory() as db:
        # Check username uniqueness
        result = await db.execute(
            select(User).where(User.username == request.username)
        )
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户名已存在",
            )

        # Check email uniqueness (only if email provided)
        if request.email:
            result = await db.execute(
                select(User).where(User.email == request.email)
            )
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="邮箱已被注册",
                )

        user = User(
            id=str(uuid.uuid4()),
            username=request.username,
            email=request.email,
            hashed_password=hash_password(request.password),
        )
        db.add(user)
        try:
            await db.commit()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="用户名已存在",
            )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
    )


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Authenticate and receive access token",
)
async def login(request: LoginRequest) -> TokenResponse:
    """Authenticate a user and return a JWT access token."""
    factory = _get_db()

    async with factory() as db:
        result = await db.execute(
            select(User).where(User.username == request.username)
        )
        user = result.scalar_one_or_none()

        if not user or not verify_password(request.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码错误",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被禁用",
            )

    settings = __import__("app.config", fromlist=["get_settings"]).get_settings()
    token = create_access_token(
        subject=user.username,
        secret_key=settings.jwt_secret_key,
    )

    return TokenResponse(access_token=token)


@router.get(
    "/auth/me",
    response_model=UserResponse,
    summary="Get current authenticated user",
)
async def get_me(username: str = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    factory = _get_db()

    async with factory() as db:
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )

    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
    )
