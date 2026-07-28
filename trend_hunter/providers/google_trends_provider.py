"""
Google Trends RSS provider.

Uses Google's free trending searches RSS feed:
https://trends.google.com/trending/rss?geo={country}

No API key or unofficial scraping library is required.
"""

from __future__ import annotations

import re

import httpx

from trend_hunter.config.settings import TrendHunterSettings
from trend_hunter.domain.enums import ProviderType
from trend_hunter.domain.models import TrendItem, TrendQuery, TrendResult
from trend_hunter.infrastructure.logging import get_logger
from trend_hunter.providers.base_http_provider import HttpTrendProvider
from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.common.rss_parser import parse_feed
from trend_hunter.providers.common.scoring import clamp_score, normalize_by_rank

logger = get_logger("providers.google_trends")

_TRAFFIC_PATTERN = re.compile(r"(\d[\d,]*)")


def _traffic_to_score(raw_traffic: str | None, rank_index: int, total: int) -> float:
    """Convert Google Trends approximate traffic strings into a normalized score."""
    if raw_traffic:
        match = _TRAFFIC_PATTERN.search(raw_traffic.replace("+", ""))
        if match:
            traffic = int(match.group(1).replace(",", ""))
            return clamp_score(max(normalize_by_rank(rank_index, total), traffic / 500_000))
    return normalize_by_rank(rank_index, total)


class GoogleTrendsRssProvider(HttpTrendProvider):
    """Collect trending search topics from Google Trends RSS."""

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GOOGLE_TRENDS

    async def fetch_trends(self, query: TrendQuery) -> TrendResult:
        geo = query.region or self._settings.google_trends_geo
        rss_url = f"https://trends.google.com/trending/rss?geo={geo}"

        try:
            content = await self._http.get_bytes(rss_url)
            parsed_items = await parse_feed(content)
        except httpx.HTTPError as exc:
            message = f"Google Trends RSS request failed: {exc}"
            logger.error(message)
            return self._empty_result(message)

        items: list[TrendItem] = []
        limit = min(query.limit, len(parsed_items))
        for index, entry in enumerate(parsed_items[:limit]):
            score = _traffic_to_score(entry.raw_traffic, index, limit or 1)
            search_url = (
                f"https://trends.google.com/trends/explore?"
                f"q={entry.title.replace(' ', '%20')}&geo={geo}"
            )
            items.append(
                self._build_item(
                    title=entry.title,
                    url=entry.url or search_url,
                    score=score,
                    published_at=entry.published_at,
                    category="search",
                    country=geo,
                    language=query.language,
                    extra_keywords=(entry.title.lower(),),
                )
            )

        return self._success_result(items)


def create_google_trends_provider(
    settings: TrendHunterSettings,
    http_client: AsyncHttpClient,
) -> GoogleTrendsRssProvider:
    return GoogleTrendsRssProvider(settings, http_client)
