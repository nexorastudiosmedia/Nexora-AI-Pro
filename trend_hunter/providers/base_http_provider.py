"""
HTTP-enabled base class for Trend Hunter provider adapters.

Subclasses inherit shared client access and helper methods for building
normalized ``TrendItem`` instances from parsed upstream data.
"""

from __future__ import annotations

from abc import abstractmethod
from datetime import datetime

from trend_hunter.config.settings import TrendHunterSettings
from trend_hunter.domain.enums import ProviderType
from trend_hunter.domain.models import TrendItem, TrendQuery, TrendResult
from trend_hunter.interfaces.trend_provider import BaseTrendProvider
from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.common.keywords import extract_keywords


class HttpTrendProvider(BaseTrendProvider):
    """Base provider that performs HTTP requests through a shared async client."""

    def __init__(
        self,
        settings: TrendHunterSettings,
        http_client: AsyncHttpClient,
    ) -> None:
        self._settings = settings
        self._http = http_client

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Provider identifier used for registry lookup and result tagging."""

    def is_configured(self) -> bool:
        """Free public-source adapters are always eligible unless overridden."""
        return True

    def _build_item(
        self,
        *,
        title: str,
        url: str | None,
        score: float,
        published_at: datetime | None,
        category: str,
        country: str,
        language: str,
        extra_keywords: tuple[str, ...] = (),
    ) -> TrendItem:
        """Construct a normalized ``TrendItem`` with extracted keywords."""
        keywords = extract_keywords(title, *extra_keywords)
        return TrendItem(
            title=title.strip(),
            url=url,
            score=score,
            source=self.provider_type,
            published_at=published_at,
            keywords=keywords,
            category=category,
            country=country,
            language=language,
        )

    def _empty_result(self, *errors: str) -> TrendResult:
        """Return a provider result containing only error messages."""
        return TrendResult(
            provider=self.provider_type,
            items=(),
            errors=errors,
        )

    def _success_result(self, items: list[TrendItem]) -> TrendResult:
        """Return a successful provider result with normalized items."""
        return TrendResult(
            provider=self.provider_type,
            items=tuple(items),
        )
