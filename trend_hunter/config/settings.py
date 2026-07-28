"""
Trend Hunter configuration loaded from environment variables.

Settings are isolated from the global Nexora AI ``config.py`` so the module
can be tested and deployed independently while still reading from the same
``.env`` file at the project root.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from trend_hunter.domain.enums import ProviderType

PROJECT_ROOT = Path(__file__).resolve().parents[2]


class TrendHunterSettings(BaseSettings):
    """
    Environment-backed settings for Trend Hunter.

    Environment variables use the ``TREND_HUNTER_`` prefix. For example,
    ``TREND_HUNTER_ENABLED_PROVIDERS`` controls which sources the service
    attempts to query when a request does not specify providers explicitly.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="TREND_HUNTER_",
        extra="ignore",
    )

    enabled_providers: tuple[ProviderType, ...] = Field(
        default=(
            ProviderType.RSS,
            ProviderType.GOOGLE_NEWS_RSS,
            ProviderType.REDDIT,
            ProviderType.HACKER_NEWS,
            ProviderType.DEVTO,
            ProviderType.PRODUCT_HUNT,
            ProviderType.GITHUB_TRENDING,
            ProviderType.GOOGLE_TRENDS,
        ),
        description="Default provider set used when a request omits explicit providers.",
    )
    skip_unconfigured: bool = Field(
        default=True,
        description="Omit registered providers that report missing credentials.",
    )
    fetch_concurrency: int = Field(
        default=5,
        ge=1,
        le=32,
        description="Maximum number of concurrent provider fetch operations.",
    )
    request_timeout_seconds: float = Field(
        default=30.0,
        gt=0,
        description="Per-provider fetch timeout enforced by the service layer.",
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level for the trend_hunter namespace.",
    )
    log_to_file: bool = Field(
        default=True,
        description="Write Trend Hunter logs to logs/trend_hunter.log.",
    )
    log_dir: Path = Field(
        default=PROJECT_ROOT / "logs",
        description="Directory for Trend Hunter log output.",
    )
    database_path: Path = Field(
        default=PROJECT_ROOT / "data" / "trend_hunter.db",
        description="SQLite database path for persisted trending topics.",
    )
    default_rss_feeds: tuple[str, ...] = Field(
        default=(
            "https://techcrunch.com/feed/",
            "https://www.theverge.com/rss/index.xml",
            "https://feeds.arstechnica.com/arstechnica/index",
            "https://www.wired.com/feed/rss",
        ),
        description="Built-in RSS feeds used when custom feeds are not configured.",
    )

    reddit_client_id: str = Field(default="", description="Reddit API client ID.")
    reddit_client_secret: str = Field(default="", description="Reddit API client secret.")
    reddit_user_agent: str = Field(
        default="NexoraAI/TrendHunter/1.0",
        description="Reddit API user agent string.",
    )

    news_api_key: str = Field(default="", description="News API authentication key.")

    youtube_api_key: str = Field(
        default="",
        description="YouTube Data API key for trend discovery.",
    )

    rss_feed_urls: tuple[str, ...] = Field(
        default=(),
        description="Additional RSS feed URLs merged with default_rss_feeds.",
    )
    github_trending_since: str = Field(
        default="daily",
        description="GitHub trending window: daily, weekly, or monthly.",
    )
    google_trends_geo: str = Field(
        default="US",
        description="Default geo code for Google Trends RSS (ISO 3166-1 alpha-2).",
    )
    google_news_gl: str = Field(
        default="US",
        description="Default country code for Google News RSS.",
    )
    google_news_hl: str = Field(
        default="en-US",
        description="Default language code for Google News RSS.",
    )
    reddit_subreddit: str = Field(
        default="all",
        description="Subreddit path segment for Reddit hot posts (e.g. all, technology).",
    )
    devto_tag: str = Field(
        default="",
        description="Optional Dev.to tag filter; empty returns site-wide top articles.",
    )

    @field_validator("enabled_providers", mode="before")
    @classmethod
    def _parse_enabled_providers(cls, value: object) -> tuple[ProviderType, ...]:
        """
        Accept comma-separated strings or iterables of provider identifiers.

        Example ``.env`` value:
            TREND_HUNTER_ENABLED_PROVIDERS=google_trends,reddit,rss
        """
        if value is None or value == "":
            return ()
        if isinstance(value, str):
            parts = [part.strip() for part in value.split(",") if part.strip()]
            return tuple(ProviderType(part) for part in parts)
        return tuple(ProviderType(item) for item in value)

    @field_validator("rss_feed_urls", mode="before")
    @classmethod
    def _parse_rss_feed_urls(cls, value: object) -> tuple[str, ...]:
        """Accept comma-separated RSS feed URLs from environment variables."""
        if value is None or value == "":
            return ()
        if isinstance(value, str):
            return tuple(part.strip() for part in value.split(",") if part.strip())
        return tuple(str(item).strip() for item in value if str(item).strip())

    @property
    def all_rss_feed_urls(self) -> tuple[str, ...]:
        """Merge configured and built-in RSS feed URLs without duplicates."""
        seen: set[str] = set()
        merged: list[str] = []
        for url in (*self.default_rss_feeds, *self.rss_feed_urls):
            normalized = url.strip()
            if normalized and normalized not in seen:
                seen.add(normalized)
                merged.append(normalized)
        return tuple(merged)

    @property
    def resolved_log_level(self) -> int:
        """Translate the configured log level string to a ``logging`` constant."""
        numeric_level = logging.getLevelNamesMapping().get(self.log_level.upper())
        if numeric_level is None:
            raise ValueError(
                f"Unsupported TREND_HUNTER_LOG_LEVEL value: {self.log_level!r}."
            )
        return numeric_level


@lru_cache(maxsize=1)
def get_trend_hunter_settings() -> TrendHunterSettings:
    """
    Return a cached ``TrendHunterSettings`` instance.

    The cache ensures a single settings object is shared across the DI
    container, service layer, and provider adapters within a process.
    """
    return TrendHunterSettings()
