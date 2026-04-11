"""Application configuration using pydantic-settings.

All configuration is loaded from environment variables and .env files.
Mirrors the Flask config/default.py structure but uses pydantic validation.
"""
from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Attributes:
        app_name: Application display name.
        app_version: Current API version.
        host: Server bind address.
        port: Server port number.
        debug: Enable debug/reload mode.
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR).

        dashscope_api_key: DashScope (通义千问) API key.
        dashscope_api_base_url: DashScope API base URL.
        dashscope_model: Default model name for LLM calls.
        embedding_model: Model name for embedding generation.
        enable_thinking: Enable Qwen deep thinking mode.

        database_url: PostgreSQL connection string (asyncpg).
        qdrant_url: Qdrant vector store URL.
        redis_url: Redis connection string.

        cors_origins: Comma-separated list of allowed CORS origins.
        rate_limit_per_minute: Max requests per minute per client.
        rate_limit_per_hour: Max requests per hour per client.

        request_timeout: HTTP request timeout in seconds.
        retry_total: Max retry attempts for failed requests.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    app_name: str = "NCHU AI Counselor API"
    app_version: str = "2.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    log_level: str = "INFO"

    # DashScope (通义千问) API
    dashscope_api_key: str = ""
    dashscope_api_base_url: str = (
        "https://dashscope.aliyuncs.com/compatible-mode/v1"
    )
    dashscope_model: str = "qwen3.5-plus"
    embedding_model: str = "text-embedding-v3"
    enable_thinking: bool = False

    # Infrastructure
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nchu_ai_counselor"
    qdrant_url: str = "http://localhost:6333"
    redis_url: str = "redis://localhost:6379/0"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"

    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000

    # Request config
    request_timeout: int = 60
    retry_total: int = 2

    # Auth
    jwt_secret_key: str = "dev-secret-change-in-production"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in valid_levels:
            raise ValueError(
                f"log_level must be one of {valid_levels}, got '{value}'"
            )
        return upper

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret(cls, value: str) -> str:
        """Ensure JWT secret is not the default value."""
        if not value or value == "dev-secret-change-in-production":
            raise ValueError(
                "JWT_SECRET_KEY must be set to a secure random value"
            )
        return value

    def parse_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins string into a list.

        Returns:
            List of allowed origin strings. Returns ["*"] if empty.
        """
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton.

    Returns:
        Cached Settings instance.
    """
    return Settings()
