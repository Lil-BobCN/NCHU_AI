from pathlib import Path
import secrets
from typing import Dict


PROJECT_DIR = Path("/app/rag-java-internal")
SOURCE_ENV = Path("/app/.env")
TARGET_ENV = PROJECT_DIR / ".env"
DEFAULT_DEV_TOKEN = "local-dev-rag-service-token-change-before-production"


def read_env(path: Path) -> Dict[str, str]:
    values = {}
    if not path.exists():
        return values
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def main() -> None:
    source = read_env(SOURCE_ENV)
    current = read_env(TARGET_ENV)
    token = current.get("RAG_SERVICE_TOKEN", "")
    if not token or token == DEFAULT_DEV_TOKEN:
        token = secrets.token_urlsafe(32)

    values = {
        "APP_NAME": "Java Internal RAG Service",
        "INTERNAL_API_PREFIX": "/internal/rag",
        "RAG_SERVICE_TOKEN": token,
        "APP_PUBLIC_BASE_URL": "http://47.100.216.222:18020",
        "DATABASE_URL": "postgresql+asyncpg://rag:rag@postgres:5432/rag",
        "REDIS_URL": "redis://redis:6379/0",
        "MINIO_ENDPOINT": "minio:9000",
        "MINIO_ACCESS_KEY": "minioadmin",
        "MINIO_SECRET_KEY": "minioadmin",
        "MINIO_SECURE": "false",
        "MINIO_PUBLIC_BASE_URL": "http://47.100.216.222:19004",
        "MINIO_DOCUMENTS_BUCKET": "rag-documents",
        "MINIO_PARSED_BUCKET": "rag-parsed",
        "MINIO_PREVIEW_BUCKET": "rag-preview",
        "DEEPSEEK_API_KEY": source.get("DEEPSEEK_API_KEY", ""),
        "CHAT_MODEL": source.get("CHAT_MODEL", "deepseek-v4-flash"),
        "EMBEDDING_API_KEY": source.get("EMBEDDING_API_KEY", source.get("DEEPSEEK_API_KEY", "")),
        "EMBEDDING_MODEL": source.get("EMBEDDING_MODEL", "text-embedding-v4"),
        "EMBEDDING_DIMENSION": "1024",
        "RERANK_API_KEY": source.get("RERANK_API_KEY", ""),
        "RERANK_MODEL": source.get("RERANK_MODEL", "qwen3-vl-rerank"),
        "RERANK_ENABLED": "true",
        "CHUNK_SIZE": "800",
        "CHUNK_OVERLAP": "120",
        "VECTOR_TOP_K": "30",
        "KEYWORD_TOP_K": "30",
        "QA_TOP_K": "10",
        "RERANK_TOP_K": "5",
        "OCR_ENABLED": "false",
        "OCR_LANG": "ch",
        "OCR_USE_GPU": "false",
        "WEB_CONCURRENCY": "2",
    }
    TARGET_ENV.write_text(
        "\n".join(f"{key}={value}" for key, value in values.items()) + "\n",
        encoding="utf-8",
    )
    TARGET_ENV.chmod(0o600)
    configured = {
        key: bool(values.get(key))
        for key in ("RAG_SERVICE_TOKEN", "DEEPSEEK_API_KEY", "EMBEDDING_API_KEY", "RERANK_API_KEY")
    }
    print(configured)


if __name__ == "__main__":
    main()
