"""
Central configuration for Nexora AI.

Loads settings from environment variables (and optionally a .env file).
No business logic — only typed settings and path helpers.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings loaded from the environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Nexora AI"
    app_env: str = "development"
    debug: bool = False
    log_level: str = "INFO"

    log_dir: Path = PROJECT_ROOT / "logs"
    data_dir: Path = PROJECT_ROOT / "data"

    scheduler_timezone: str = "UTC"

    facebook_app_id: str = ""
    facebook_app_secret: str = ""
    facebook_access_token: str = ""

    youtube_api_key: str = ""
    youtube_client_id: str = ""
    youtube_client_secret: str = ""

    openai_api_key: str = ""


def get_settings() -> Settings:
    """Return a cached-friendly settings instance."""
    return Settings()
