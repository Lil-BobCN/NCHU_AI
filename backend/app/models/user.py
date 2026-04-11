"""User ORM model.

Provides the database-backed user table for authentication and authorization.
"""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User account model.

    Attributes:
        id: Auto-generated UUID primary key.
        username: Unique username, 2-30 chars.
        email: Optional unique email address.
        hashed_password: scrypt-hashed password string.
        is_active: Whether the account is enabled.
    """

    __tablename__ = "users_auth"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )
    username: Mapped[str] = mapped_column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
    )
    email: Mapped[str | None] = mapped_column(
        String(200),
        unique=True,
        nullable=True,
        index=True,
    )
    hashed_password: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
    )
