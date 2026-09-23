"""
Centralized application settings, loaded from environment variables / .env.

Every other module should import `settings` from here rather than calling
os.environ directly, so we have one source of truth for configuration.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM (Groq — free tier)
    groq_api_key: str = ""
    # llama-3.3-70b-versatile was deprecated by Groq on 2026-08-16 for
    # free/developer tier accounts. openai/gpt-oss-120b is Groq's own
    # recommended replacement.
    groq_model: str = "openai/gpt-oss-120b"

    # Live travel data
    serpapi_key: str = ""

    # Persistence (optional for MVP)
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    database_url: str = ""

    # App
    environment: str = "development"
    log_level: str = "info"
    serpapi_cache_ttl_seconds: int = 3600

    # CORS
    frontend_origin: str = "http://localhost:3000"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance — env is only read once per process."""
    return Settings()


settings = get_settings()