"""
Google News RSS provider.

Uses the free public Google News RSS endpoint — no API key required.
Region and language parameters are derived from the active ``TrendQuery``.
"""

from __future__ import annotations

import httpx

from trend_hunter.config.settings import TrendHunterSettings
from trend_hunter.domain.enums import ProviderType
from trend_hunter.domain.models import TrendItem, TrendQuery, TrendResult
from trend_hunter.infrastructure.logging import get_logger
from trend_hunter.providers.base_http_provider import HttpTrendProvider
from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.common.rss_parser import parse_feed
from trend_hunter.providers.common.scoring import normalize_by_rank

logger = get_logger("providers.google_news_rss")


class GoogleNewsRssProvider(HttpTrendProvider):
    """Collect top news stories from Google News via its public RSS feed."""

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.GOOGLE_NEWS_RSS

    async def fetch_trends(self, query: TrendQuery) -> TrendResult:
        hl = self._settings.google_news_hl or f"{query.language}-{query.region}"
        gl = query.region or self._settings.google_news_gl
        ceid = f"{gl}:{query.language}"
        rss_url = f"https://news.google.com/rss?hl={hl}&gl={gl}&ceid={ceid}"

        try:
            content = await self._http.get_bytes(rss_url)
            parsed_items = await parse_feed(content)
        except httpx.HTTPError as exc:
            message = f"Google News RSS request failed: {exc}"
            logger.error(message)
            return self._empty_result(message)

        items: list[TrendItem] = []
        limit = min(query.limit, len(parsed_items))
        for index, entry in enumerate(parsed_items[:limit]):
            items.append(
                self._build_item(
                    title=entry.title,
                    url=entry.url,
                    score=normalize_by_rank(index, limit or 1),
                    published_at=entry.published_at,
                    category="news",
                    country=gl,
                    language=query.language,
                )
            )

        return self._success_result(items)


def create_google_news_rss_provider(
    settings: TrendHunterSettings,
    http_client: AsyncHttpClient,
) -> GoogleNewsRssProvider:
    return GoogleNewsRssProvider(settings, http_client)
