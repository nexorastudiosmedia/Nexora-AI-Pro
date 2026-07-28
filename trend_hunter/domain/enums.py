"""
Domain enumerations for Trend Hunter.

These types form the shared vocabulary between the service layer and every
trend provider adapter. Keeping them in the domain layer ensures that
providers, services, and configuration all refer to the same canonical values
without importing infrastructure concerns.
"""

from enum import StrEnum


class ProviderType(StrEnum):
    """
    Identifiers for supported trend data sources.

    Each member maps to exactly one provider adapter under
    ``trend_hunter.providers``. New sources are added here first so that
    configuration, registry keys, and API contracts stay aligned.
    """

    RSS = "rss"
    GOOGLE_NEWS_RSS = "google_news_rss"
    REDDIT = "reddit"
    HACKER_NEWS = "hacker_news"
    DEVTO = "devto"
    PRODUCT_HUNT = "product_hunt"
    GITHUB_TRENDING = "github_trending"
    GOOGLE_TRENDS = "google_trends"
    NEWS_API = "news_api"
    YOUTUBE = "youtube"


class TrendTimeRange(StrEnum):
    """
    Normalized look-back windows for trend queries.

    Providers translate these values into their native API parameters
    (for example, Google Trends ``date`` presets or News API ``from`` dates).
    """

    PAST_HOUR = "past_hour"
    PAST_DAY = "past_day"
    PAST_WEEK = "past_week"
    PAST_MONTH = "past_month"
    PAST_YEAR = "past_year"


class TrendSortOrder(StrEnum):
    """Determines how aggregated trend items are ordered before delivery."""

    RELEVANCE = "relevance"
    SCORE_DESC = "score_desc"
    RECENCY = "recency"
