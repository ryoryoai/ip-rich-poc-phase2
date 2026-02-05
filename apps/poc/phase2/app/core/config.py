"""Application configuration using pydantic-settings."""

from pathlib import Path
from functools import lru_cache
import os

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[2]
DEFAULT_ENV_FILE = BASE_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=DEFAULT_ENV_FILE,
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",  # Ignore extra env vars from Vercel
    )

    # Database
    database_url: str = "postgresql://localhost/phase2"
    direct_url: str | None = None

    # Raw storage
    raw_storage_path: Path = Path("./data/raw")
    bulk_root_path: Path = Path("./data/bulk")

    # Supabase Storage (evidence snapshots)
    supabase_url: str | None = None
    supabase_service_role_key: str | None = None
    supabase_storage_bucket: str = "evidence"
    supabase_storage_public_url: str | None = None
    supabase_patent_raw_bucket: str = "patent-raw"

    # JPO API (optional)
    jpo_api_base_url: str | None = None
    jpo_api_key: str | None = None
    jpo_api_timeout_seconds: int = 30

    # Logging
    log_level: str = "INFO"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # LLM Provider
    llm_provider: str = "openai"  # "openai" or "anthropic"
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    anthropic_api_key: str | None = None
    anthropic_model: str = "claude-sonnet-4-20250514"

    # Prompts
    prompts_dir: Path = Path("./prompts")

    # Search Provider
    search_provider: str = "dummy"  # "tavily" or "dummy"
    tavily_api_key: str | None = None

    # Batch Processing
    max_concurrent_jobs: int = 3
    cron_secret: str | None = None

    # Safety toggles
    allow_schema_init: bool = False

    # JP Index export controls
    jp_index_export_enabled: bool = True
    jp_index_export_max: int = 10000
    jp_index_export_token: str | None = None

    # JP Index rate limit / cache
    jp_index_rate_limit_per_minute: int = 120
    jp_index_cache_ttl_seconds: int = 60
    jp_index_cache_max_entries: int = 1000

    # Company data sources
    nta_corporate_encoding: str = "utf-8"
    gbizinfo_api_base_url: str | None = None
    gbizinfo_api_key: str | None = None
    gbizinfo_api_key_header: str = "X-API-KEY"
    gbizinfo_field_map: str | None = None
    edinet_api_base_url: str | None = None
    edinet_api_key: str | None = None
    edinet_api_key_header: str = "Subscription-Key"
    edinet_field_map: str | None = None
    collection_user_agent: str = "iprich-phase2/1.0"

    @field_validator("jp_index_export_max")
    @classmethod
    def validate_export_max(cls, value: int) -> int:
        if value < 1 or value > 100000:
            raise ValueError("JP_INDEX_EXPORT_MAX must be between 1 and 100000")
        return value

    @field_validator("jp_index_rate_limit_per_minute")
    @classmethod
    def validate_rate_limit(cls, value: int) -> int:
        if value < 0 or value > 100000:
            raise ValueError("JP_INDEX_RATE_LIMIT_PER_MINUTE must be between 0 and 100000")
        return value

    @field_validator("jp_index_cache_ttl_seconds")
    @classmethod
    def validate_cache_ttl(cls, value: int) -> int:
        if value < 0 or value > 86400:
            raise ValueError("JP_INDEX_CACHE_TTL_SECONDS must be between 0 and 86400")
        return value

    @field_validator("jp_index_cache_max_entries")
    @classmethod
    def validate_cache_entries(cls, value: int) -> int:
        if value < 0 or value > 100000:
            raise ValueError("JP_INDEX_CACHE_MAX_ENTRIES must be between 0 and 100000")
        return value


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    env_file = os.getenv("PHASE2_ENV_FILE", str(DEFAULT_ENV_FILE))
    return Settings(_env_file=env_file)


settings = get_settings()
