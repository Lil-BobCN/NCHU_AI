"""
配置中心。通过 Pydantic Settings 读取环境变量，集中管理数据库、Redis、MinIO、模型、OCR 和 RAG 参数。
"""

from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DEEPSEEK_BASE_URL = "https://api.deepseek.com"
DASHSCOPE_COMPATIBLE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DASHSCOPE_RERANK_URL = "https://dashscope.aliyuncs.com/api/v1/services/rerank/text-rerank/text-rerank"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=("../.env", ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Java Internal RAG Service"
    api_v1_prefix: str = "/api/v1"
    internal_api_prefix: str = "/internal/rag"
    rag_service_token: str = "change-me"
    sa_token_jwt_secret: str = "change-me"
    sa_token_jwt_algorithm: str = "HS256"
    sa_token_clock_skew_seconds: int = 60
    app_public_base_url: str | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )

    database_url: str = "postgresql+asyncpg://rag:rag@localhost:5432/rag"
    database_pool_size: int = 5
    database_max_overflow: int = 10
    database_pool_timeout_seconds: int = 30
    database_pool_recycle_seconds: int = 1800
    redis_url: str = "redis://localhost:6379/0"
    background_task_queue_key: str = "rag:background_tasks"
    background_worker_concurrency: int = 1
    background_worker_poll_timeout_seconds: int = 5

    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_public_base_url: str = "http://localhost:9000"
    minio_documents_bucket: str = "rag-documents"
    minio_parsed_bucket: str = "rag-parsed"
    minio_preview_bucket: str = "rag-preview"

    jwt_secret_key: str = "change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24
    admin_username: str = "admin"
    admin_password: str = "admin123"

    max_upload_size_mb: int = 100

    deepseek_api_key: str | None = None
    deepseek_base_url: str = DEEPSEEK_BASE_URL
    chat_model: str = "deepseek-chat"
    """默认对话模型名称。使用 deepseek-chat 以获得更好的提炼和总结能力。"""
    stream_char_delay_ms: int = 0
    chat_max_question_chars: int = 2000
    chat_max_top_k: int = 30
    chat_max_rerank_top_k: int = 10
    chat_max_concurrent_requests: int = 20
    chat_global_max_concurrent_requests: int = 0
    chat_distributed_concurrency_enabled: bool = True
    chat_slot_ttl_seconds: int = 300
    chat_summary_model_enabled: bool = False
    chat_suggested_questions_model_enabled: bool = False
    chat_queue_timeout_seconds: float = 0.05
    model_request_timeout_seconds: float = 90.0
    model_request_retries: int = 2
    model_max_concurrent_requests: int = 20

    embedding_api_key: str | None = None
    embedding_base_url: str = DASHSCOPE_COMPATIBLE_BASE_URL
    embedding_model: str = "text-embedding-v4"
    embedding_dimension: int = 1024
    embedding_batch_size: int = 10
    embedding_max_concurrent_requests: int = 8
    embedding_cache_enabled: bool = True
    embedding_cache_ttl_seconds: int = 604800

    rerank_api_key: str | None = None
    rerank_base_url: str = DASHSCOPE_RERANK_URL
    rerank_model: str = "qwen3-vl-rerank"
    rerank_enabled: bool = True
    rerank_max_candidates: int = 10
    rerank_request_timeout_seconds: float = 30.0
    rerank_request_retries: int = 1
    rerank_max_concurrent_requests: int = 20

    chunk_size: int = 800
    chunk_overlap: int = 120
    table_chunk_rows: int = 50
    table_full_index_max_rows: int = 500
    table_sample_rows: int = 50
    max_document_chunks: int = 300
    max_embedding_chars_per_document: int = 200000
    vector_top_k: int = 30
    keyword_top_k: int = 30
    qa_top_k: int = 10
    rerank_top_k: int = 5
    retrieval_max_query_chars: int = 2000
    retrieval_max_top_k: int = 50
    retrieval_max_rerank_top_k: int = 20
    similarity_threshold: float = 0.35
    rerank_threshold: float = 0.45
    retrieval_cache_enabled: bool = True
    retrieval_cache_ttl_seconds: int = 1800
    retrieval_blacklist_keywords: str = (
        "接口测试,API接口,API 接口,接口设计,测试文档,内部文档,内部资料,涉密,保密,AI底座,底座规划"
    )
    answer_cache_enabled: bool = True
    answer_cache_ttl_seconds: int = 3600

    ocr_enabled: bool = True
    ocr_lang: str = "ch"
    ocr_pdf_dpi: int = 180
    ocr_min_confidence: float = 0.45
    ocr_max_pages: int = 80
    ocr_use_gpu: bool = False


@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.deepseek_base_url = DEEPSEEK_BASE_URL
    settings.embedding_base_url = DASHSCOPE_COMPATIBLE_BASE_URL
    settings.rerank_base_url = DASHSCOPE_RERANK_URL
    dotenv_data: dict[str, str] = {}
    for path in [
        Path(__file__).resolve().parents[3] / ".env",
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
    ]:
        if path.exists():
            dotenv_data.update(
                {key.lstrip("\ufeff"): value for key, value in dotenv_values(path).items() if value is not None}
            )
    fallback_fields = {
        "deepseek_api_key": "DEEPSEEK_API_KEY",
        "embedding_api_key": "EMBEDDING_API_KEY",
        "embedding_batch_size": "EMBEDDING_BATCH_SIZE",
        "rerank_api_key": "RERANK_API_KEY",
        "database_url": "DATABASE_URL",
        "database_pool_size": "DATABASE_POOL_SIZE",
        "database_max_overflow": "DATABASE_MAX_OVERFLOW",
        "database_pool_timeout_seconds": "DATABASE_POOL_TIMEOUT_SECONDS",
        "database_pool_recycle_seconds": "DATABASE_POOL_RECYCLE_SECONDS",
        "redis_url": "REDIS_URL",
        "minio_endpoint": "MINIO_ENDPOINT",
        "minio_public_base_url": "MINIO_PUBLIC_BASE_URL",
        "app_public_base_url": "APP_PUBLIC_BASE_URL",
    }
    for field_name, env_name in fallback_fields.items():
        if not getattr(settings, field_name, None) and dotenv_data.get(env_name):
            setattr(settings, field_name, dotenv_data[env_name])
    return settings
