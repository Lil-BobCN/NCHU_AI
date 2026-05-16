"""Authentication routes for the Phase 1 business API."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import current_user
from app.schemas.business import LoginRequest, SSOCallbackRequest, TokenResponse, UserPublic
from app.services.business import TokenSession, User, store

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest) -> TokenResponse:
    """Authenticate a local Phase 1 user."""
    session = store.authenticate_local(payload.username, payload.password)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )
    return _token_response(session)


@router.post("/sso/callback", response_model=TokenResponse)
async def sso_callback(payload: SSOCallbackRequest) -> TokenResponse:
    """Accept a simulated SSO callback and issue a local bearer token."""
    session = store.authenticate_sso(payload.provider, payload.code, payload.email)
    return _token_response(session)


@router.get("/sso/callback", response_model=TokenResponse)
async def sso_callback_get(
    code: Annotated[str, Query(min_length=1)],
    provider: str = "campus-sso",
    email: str | None = None,
) -> TokenResponse:
    """Support browser-style SSO callbacks with query parameters."""
    session = store.authenticate_sso(provider, code, email)
    return _token_response(session)


@router.get("/me", response_model=UserPublic)
async def me(user: Annotated[User, Depends(current_user)]) -> User:
    """Return the bearer-token user profile."""
    return user


def _token_response(session: TokenSession) -> TokenResponse:
    user = store.users[session.user_id]
    return TokenResponse(
        access_token=session.token,
        provider=session.provider,
        issued_at=session.issued_at,
        user=UserPublic.model_validate(user),
    )
