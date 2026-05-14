"""Application configuration using pydantic-settings."""
from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

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

    # Infrastructure
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/nchu_ai_counselor"
    redis_url: str = "redis://localhost:6379/0"

    # Object storage (official Phase 1 path)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "nchu-counselor-documents"
    minio_secure: bool = False

    # Vector database (official Phase 1 path)
    milvus_host: str = "localhost"
    milvus_port: int = 19530
    milvus_db_name: str = "default"
    milvus_collection: str = "nchu_counselor_documents"
    milvus_vector_dim: int = Field(default=1024, gt=0)
    milvus_metric_type: str = "COSINE"
    milvus_index_type: str = "IVF_FLAT"
    milvus_index_nlist: int = Field(default=1024, gt=0)
    milvus_token: str = ""

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:5173,http://localhost:8000"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, value: str) -> str:
        """Validate log level is a valid Python logging level."""
        valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = value.upper()
        if upper not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}, got {value!r}")
        return upper

    @field_validator("debug", mode="before")
    @classmethod
    def normalize_debug(cls, value):
        """Accept deployment words sometimes exported as DEBUG values."""
        if isinstance(value, str) and value.lower() in {"release", "prod", "production"}:
            return False
        return value

    @field_validator("milvus_metric_type", "milvus_index_type")
    @classmethod
    def normalize_milvus_uppercase(cls, value: str) -> str:
        """Normalize Milvus enum-like settings."""
        return value.upper()

    def parse_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
