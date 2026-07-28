"""
Generic RSS feed provider.

Aggregates entries from configured and built-in RSS feeds, normalizes them
into ``TrendItem`` records, and assigns recency-weighted popularity scores.
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

logger = get_logger("providers.rss")


class RssFeedProvider(HttpTrendProvider):
    """Collect trends from multiple RSS/Atom feeds without authentication."""

    @property
    def provider_type(self) -> ProviderType:
        return ProviderType.RSS

    def is_configured(self) -> bool:
        return bool(self._settings.all_rss_feed_urls)

    async def fetch_trends(self, query: TrendQuery) -> TrendResult:
        feed_urls = self._settings.all_rss_feed_urls
        if not feed_urls:
            return self._empty_result("No RSS feed URLs configured.")

        items: list[TrendItem] = []
        errors: list[str] = []

        for feed_url in feed_urls:
            try:
                content = await self._http.get_bytes(feed_url)
                parsed_items = await parse_feed(content)
                for index, entry in enumerate(parsed_items[: query.limit]):
                    items.append(
                        self._build_item(
                            title=entry.title,
                            url=entry.url,
                            score=normalize_by_rank(index, min(len(parsed_items), query.limit)),
                            published_at=entry.published_at,
                            category=entry.category,
                            country=query.region,
                            language=query.language,
                        )
                    )
            except httpx.HTTPError as exc:
                message = f"Failed to fetch RSS feed {feed_url}: {exc}"
                logger.warning(message)
                errors.append(message)

        if not items and errors:
            return self._empty_result(*errors)

        ranked = sorted(items, key=lambda item: item.score, reverse=True)[: query.limit]
        result = self._success_result(ranked)
        if errors:
            return TrendResult(
                provider=self.provider_type,
                items=result.items,
                errors=tuple(errors),
            )
        return result


def create_rss_provider(
    settings: TrendHunterSettings,
    http_client: AsyncHttpClient,
) -> RssFeedProvider:
    return RssFeedProvider(settings, http_client)
