"""Shared API dependencies for Phase 1 business routes."""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import Settings, get_settings
from app.services.business import User, store
from app.services.chat_model import DashScopeChatModelProvider

bearer_scheme = HTTPBearer(auto_error=False)


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    """Resolve the current in-memory user from a bearer token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
        )
    user = store.user_for_token(credentials.credentials)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid bearer token",
        )
    return user


def require_admin(user: Annotated[User, Depends(current_user)]) -> User:
    """Require an administrator user."""
    if user.role != "admin":
        store.record_audit(
            user.id,
            "auth.permission.denied",
            "route",
            "admin",
            result="denied",
            event_tags=["required:admin"],
            counter_key="permission.denied.count",
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


def require_counselor(user: Annotated[User, Depends(current_user)]) -> User:
    """Require a counselor or administrator user."""
    if user.role not in {"counselor", "admin"}:
        store.record_audit(
            user.id,
            "auth.permission.denied",
            "route",
            "counselor",
            result="denied",
            event_tags=["required:counselor"],
            counter_key="permission.denied.count",
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Counselor role required",
        )
    return user


def chat_model_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> DashScopeChatModelProvider:
    """Resolve the configured Qwen/DashScope provider for student Chatbox streaming."""
    return DashScopeChatModelProvider(settings)
