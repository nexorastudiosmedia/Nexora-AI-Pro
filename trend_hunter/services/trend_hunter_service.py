"""
Trend Hunter application service.

Orchestrates concurrent provider fetches, aggregates normalized results, and
applies cross-provider sorting and deduplication rules defined on the domain
models.
"""

from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import datetime, timezone

from trend_hunter.config.settings import TrendHunterSettings
from trend_hunter.domain.enums import ProviderType, TrendSortOrder
from trend_hunter.domain.models import (
    TrendHunterRequest,
    TrendHunterResponse,
    TrendItem,
    TrendQuery,
    TrendResult,
)
from trend_hunter.exceptions import ProviderFetchError
from trend_hunter.infrastructure.logging import get_logger
from trend_hunter.interfaces.trend_provider import TrendProvider
from trend_hunter.providers.registry import ProviderRegistry

logger = get_logger("services.trend_hunter")


class TrendHunterService:
    """
    Primary entry point for trend discovery within Nexora AI.

    The service is constructed with explicit dependencies (registry, settings)
    so it remains pure and easy to unit test without a live network or .env file.
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        settings: TrendHunterSettings,
    ) -> None:
        self._registry = registry
        self._settings = settings

    async def discover(self, request: TrendHunterRequest) -> TrendHunterResponse:
        """
        Discover trends across one or more providers.

        Provider selection follows this order:
        1. Explicit ``request.providers`` when supplied.
        2. Otherwise ``settings.enabled_providers`` resolved through the registry.

        Partial provider failures are captured in ``TrendHunterResponse.provider_results``
        and do not abort the overall operation.
        """
        providers = self._resolve_providers(request)
        if not providers:
            logger.warning(
                "Trend discovery invoked with zero eligible providers "
                "(request_id pending)."
            )
            return TrendHunterResponse(
                items=(),
                provider_results=(),
            )

        logger.info(
            "Starting trend discovery across %d provider(s): %s.",
            len(providers),
            ", ".join(p.provider_type.value for p in providers),
        )

        provider_results = await self._fetch_all(providers, request.query)
        aggregated_items = self._aggregate_items(
            provider_results,
            sort_by=request.sort_by,
            deduplicate=request.deduplicate,
        )

        response = TrendHunterResponse(
            items=aggregated_items,
            provider_results=provider_results,
        )

        logger.info(
            "Trend discovery completed (request_id=%s, items=%d, succeeded=%s, failed=%s).",
            response.request_id,
            response.total_items,
            [p.value for p in response.providers_succeeded],
            [p.value for p in response.providers_failed],
        )
        return response

    def _resolve_providers(
        self,
        request: TrendHunterRequest,
    ) -> tuple[TrendProvider, ...]:
        """Map the request or settings to a concrete, eligible provider list."""
        requested_types: Sequence[ProviderType] = (
            request.providers
            if request.providers is not None
            else self._settings.enabled_providers
        )
        return self._registry.resolve(
            requested_types,
            skip_unconfigured=self._settings.skip_unconfigured,
        )

    async def _fetch_all(
        self,
        providers: Sequence[TrendProvider],
        query: TrendQuery,
    ) -> tuple[TrendResult, ...]:
        """
        Execute provider fetches concurrently with a bounded semaphore.

        Unexpected exceptions are converted into ``TrendResult`` error records
        so aggregation can proceed with surviving provider data.
        """
        semaphore = asyncio.Semaphore(self._settings.fetch_concurrency)
        timeout = self._settings.request_timeout_seconds

        async def _guarded_fetch(provider: TrendProvider) -> TrendResult:
            async with semaphore:
                return await self._fetch_single(provider, query, timeout)

        results = await asyncio.gather(
            *(_guarded_fetch(provider) for provider in providers),
            return_exceptions=False,
        )
        return tuple(results)

    async def _fetch_single(
        self,
        provider: TrendProvider,
        query: TrendQuery,
        timeout: float,
    ) -> TrendResult:
        """Invoke a single provider with timeout and structured error handling."""
        provider_name = provider.provider_type.value
        logger.debug("Fetching trends from provider '%s'.", provider_name)

        try:
            result = await asyncio.wait_for(
                provider.fetch_trends(query),
                timeout=timeout,
            )
        except TimeoutError:
            message = f"Timed out after {timeout:.1f}s."
            logger.error("Provider '%s' %s", provider_name, message)
            return TrendResult(
                provider=provider.provider_type,
                items=(),
                errors=(message,),
            )
        except ProviderFetchError as exc:
            logger.error("Provider '%s' raised ProviderFetchError: %s", provider_name, exc)
            return TrendResult(
                provider=provider.provider_type,
                items=(),
                errors=(str(exc),),
            )
        except Exception as exc:
            message = f"Unexpected error: {exc}"
            logger.exception("Provider '%s' failed with an unexpected error.", provider_name)
            return TrendResult(
                provider=provider.provider_type,
                items=(),
                errors=(message,),
            )

        if result.errors:
            logger.warning(
                "Provider '%s' returned %d item(s) with %d error(s).",
                provider_name,
                result.item_count,
                len(result.errors),
            )
        else:
            logger.debug(
                "Provider '%s' returned %d item(s).",
                provider_name,
                result.item_count,
            )

        return result

    def _aggregate_items(
        self,
        provider_results: Sequence[TrendResult],
        *,
        sort_by: TrendSortOrder,
        deduplicate: bool,
    ) -> tuple[TrendItem, ...]:
        """Merge provider items, optionally deduplicate, and apply sort order."""
        items: list[TrendItem] = [
            item for result in provider_results for item in result.items
        ]

        if deduplicate:
            items = self._deduplicate_items(items)

        items = self._sort_items(items, sort_by)
        return tuple(items)

    @staticmethod
    def _deduplicate_items(items: Sequence[TrendItem]) -> list[TrendItem]:
        """
        Retain the highest-scoring item for each case-insensitive title.

        When two items share a title, the one with the greater ``score`` wins.
        """
        best_by_title: dict[str, TrendItem] = {}
        for item in items:
            key = item.title.casefold()
            existing = best_by_title.get(key)
            if existing is None or item.score > existing.score:
                best_by_title[key] = item
        return list(best_by_title.values())

    @staticmethod
    def _sort_items(
        items: Sequence[TrendItem],
        sort_by: TrendSortOrder,
    ) -> list[TrendItem]:
        """Sort items according to the requested ``TrendSortOrder``."""
        if sort_by is TrendSortOrder.SCORE_DESC:
            return sorted(items, key=lambda item: item.score, reverse=True)

        if sort_by is TrendSortOrder.RECENCY:
            epoch = datetime.min.replace(tzinfo=timezone.utc)
            return sorted(
                items,
                key=lambda item: item.published_at or epoch,
                reverse=True,
            )

        return list(items)
