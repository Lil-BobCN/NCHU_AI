"""Application configuration using pydantic-settings."""
from __future__ import annotations

from functools import lru_cache

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=(".env.legacy-20260513T145513", ".env"),
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
    cors_origins: str = (
        "http://localhost:3000,"
        "http://localhost:5173,http://127.0.0.1:5173,"
        "http://localhost:5180,http://127.0.0.1:5180,"
        "http://localhost:8000,http://127.0.0.1:8000"
    )

    # Qwen/DashScope real-model proxy (Phase 3R)
    dashscope_api_key: str = Field(
        default="",
        validation_alias=AliasChoices("DASHSCOPE_API_KEY", "QWEN_API_KEY"),
    )
    dashscope_api_base_url: str = Field(
        default="https://dashscope.aliyuncs.com/compatible-mode/v1",
        validation_alias=AliasChoices("DASHSCOPE_API_BASE_URL", "QWEN_API_BASE_URL"),
    )
    dashscope_model: str = Field(
        default="qwen3.5-flash",
        validation_alias=AliasChoices("DASHSCOPE_MODEL", "QWEN_MODEL"),
    )
    enable_thinking: bool = Field(
        default=False,
        validation_alias=AliasChoices("ENABLE_THINKING", "DASHSCOPE_ENABLE_THINKING"),
    )
    chat_model_timeout_seconds: float = Field(default=30.0, gt=0)
    chat_model_max_tokens: int = Field(default=512, gt=0)
    chat_model_context_message_limit: int = Field(default=8, gt=0)
    chat_model_web_search_enabled: bool = Field(default=True)
    chat_model_web_search_strategy: str = "turbo"
    chat_model_system_prompt: str = (
        "你是南昌航空大学 AI 辅导员 Demo 的学生端助手。"
        "请用中文给出清晰、克制、可执行的支持建议；"
        "不要声称已经接入真实学校数据库、RAG 知识库或真实学生档案。"
        "遇到自伤、他伤或紧急危机风险时，优先建议立即联系紧急服务、校内值班老师或心理咨询中心。"
    )

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

    @field_validator("chat_model_web_search_strategy")
    @classmethod
    def normalize_search_strategy(cls, value: str) -> str:
        """Normalize DashScope search strategy to the documented lowercase form."""
        normalized = value.strip().lower()
        if normalized not in {"turbo", "max", "agent", "agent_max"}:
            raise ValueError(
                "chat_model_web_search_strategy must be one of "
                "'turbo', 'max', 'agent', or 'agent_max'"
            )
        return normalized

    def parse_cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        if not self.cors_origins or self.cors_origins.strip() == "*":
            return ["*"]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached application settings singleton."""
    return Settings()
