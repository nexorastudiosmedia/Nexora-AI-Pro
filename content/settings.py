"""
Content Engine configuration.

Reads GROQ_API_KEY from the project .env file (same pattern as the main
config.py). Isolated here so the content module can be tested independently.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class ContentEngineSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    niche: str = "Philosophy / Deep Thoughts"


def get_content_engine_settings() -> ContentEngineSettings:
    return ContentEngineSettings()
