"""
Application configuration loaded from environment variables.
Uses pydantic-settings for typed, validated config with sensible defaults.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Application ─────────────────────────────────────
    app_name: str = "EnterpriseAI"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    secret_key: str = "change-me-to-a-random-64-char-string"
    cors_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── PostgreSQL ──────────────────────────────────────
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "eai_user"
    postgres_password: str = "eai_secret_password"
    postgres_db: str = "enterprise_ai"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    # ── Redis ───────────────────────────────────────────
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    @property
    def redis_url(self) -> str:
        auth = f":{self.redis_password}@" if self.redis_password else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    # ── Celery ──────────────────────────────────────────
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── JWT Auth ────────────────────────────────────────
    jwt_secret_key: str = "change-me-jwt-secret-key-64-chars"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ── LLM (commented-out placeholders) ────────────────
    openai_api_key: str = ""
    openai_model: str = "gpt-4o"
    openai_embedding_model: str = "text-embedding-3-small"

    # ── Langfuse ────────────────────────────────────────
    langfuse_public_key: str = ""
    langfuse_secret_key: str = ""
    langfuse_host: str = "https://cloud.langfuse.com"

    # ── Ragas ───────────────────────────────────────────
    ragas_eval_enabled: bool = True

    # ── File Upload ─────────────────────────────────────
    max_upload_size_mb: int = 50
    upload_dir: str = "./uploads"
    allowed_extensions: str = ".pdf,.txt,.md,.docx,.csv,.json,.html"

    @property
    def allowed_extension_list(self) -> List[str]:
        return [e.strip() for e in self.allowed_extensions.split(",")]

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    # ── Rate Limiting ───────────────────────────────────
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10

    # ── Pagination ──────────────────────────────────────
    default_page_size: int = 20
    max_page_size: int = 100

    # ── pgvector ────────────────────────────────────────
    pgvector_enabled: bool = True
    embedding_dimension: int = 1536

    # ── OpenSearch (optional) ───────────────────────────
    opensearch_enabled: bool = False
    opensearch_host: str = "localhost"
    opensearch_port: int = 9200


@lru_cache()
def get_settings() -> Settings:
    return Settings()
