"""
MealMind v3 — Configuration
Loads all environment variables via Pydantic BaseSettings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # ── Telegram ─────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str

    # ── Anthropic ────────────────────────────────────────────
    ANTHROPIC_API_KEY: str
    CLAUDE_MODEL: str = "claude-3-5-haiku-latest"

    # ── Database (PostgreSQL) ────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://mealmind:mealmind_dev@localhost:5432/mealmind"

    # ── App ──────────────────────────────────────────────────
    ENVIRONMENT: str = "development"
    APP_NAME: str = "MealMind"

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


@lru_cache()
def get_settings() -> Settings:
    """Cached settings instance — loaded once per process."""
    return Settings()
