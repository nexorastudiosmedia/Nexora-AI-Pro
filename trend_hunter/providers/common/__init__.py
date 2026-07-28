"""Shared utilities consumed by Trend Hunter provider adapters."""

from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.common.keywords import extract_keywords
from trend_hunter.providers.common.rss_parser import ParsedFeedItem, parse_feed
from trend_hunter.providers.common.scoring import (
    clamp_score,
    normalize_by_rank,
    normalize_count,
    normalize_linear,
)

__all__ = [
    "AsyncHttpClient",
    "ParsedFeedItem",
    "clamp_score",
    "extract_keywords",
    "normalize_by_rank",
    "normalize_count",
    "normalize_linear",
    "parse_feed",
]
