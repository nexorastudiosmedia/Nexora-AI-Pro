"""
Pydantic domain models for Trend Hunter.

These models describe the data that flows through the application layer.
They are intentionally free of HTTP, database, or third-party API details so
that provider adapters remain replaceable and testable in isolation.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator

from trend_hunter.domain.enums import ProviderType, TrendSortOrder, TrendTimeRange


def _utc_now() -> datetime:
    """Return the current UTC timestamp for model defaults."""
    return datetime.now(timezone.utc)


class TrendQuery(BaseModel):
    """
    Provider-facing search parameters.

    A single ``TrendQuery`` is passed to each registered provider during
    discovery. Providers may ignore fields they do not support, but they
    must not mutate the query object.
    """

    model_config = ConfigDict(frozen=True)

    keywords: tuple[str, ...] = Field(
        default=(),
        description="Search terms used to filter or rank trends.",
    )
    niche: str = Field(
        default="",
        description="Optional content niche or vertical (e.g. 'tech', 'finance').",
    )
    region: str = Field(
        default="US",
        min_length=2,
        max_length=8,
        description="ISO 3166-1 alpha-2 country code or provider-specific region token.",
    )
    time_range: TrendTimeRange = Field(
        default=TrendTimeRange.PAST_WEEK,
        description="Look-back window applied to the trend search.",
    )
    limit: int = Field(
        default=25,
        ge=1,
        le=100,
        description="Maximum number of trend items requested from a single provider.",
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=8,
        description="BCP-47 language tag or provider-specific language code.",
    )

    @field_validator("keywords", mode="before")
    @classmethod
    def _normalize_keywords(cls, value: Any) -> tuple[str, ...]:
        """Accept lists or tuples and strip empty keyword strings."""
        if value is None:
            return ()
        if isinstance(value, str):
            stripped = value.strip()
            return (stripped,) if stripped else ()
        return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


class TrendItem(BaseModel):
    """
    A single normalized trend record produced by a provider adapter.

    ``score`` is a provider-agnostic ranking signal on the interval [0.0, 1.0].
    When a source does not expose a numeric ranking, adapters should derive a
    consistent proxy (for example, normalized search volume or upvote ratio).
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    title: str = Field(min_length=1, description="Human-readable trend headline or topic.")
    score: float = Field(
        ge=0.0,
        le=1.0,
        description="Normalized relevance or popularity score.",
    )
    url: str | None = Field(
        default=None,
        description="Canonical URL for the trend, when available.",
    )
    source: ProviderType = Field(description="Provider that surfaced this trend item.")
    published_at: datetime | None = Field(
        default=None,
        description="Publication or first-seen timestamp in UTC.",
    )
    keywords: tuple[str, ...] = Field(
        default_factory=tuple,
        description="Extracted or assigned topical keywords.",
    )
    category: str = Field(
        default="general",
        description="Content category or vertical (e.g. technology, news).",
    )
    country: str = Field(
        default="US",
        min_length=2,
        max_length=8,
        description="ISO 3166-1 alpha-2 country associated with the trend.",
    )
    language: str = Field(
        default="en",
        min_length=2,
        max_length=8,
        description="BCP-47 language tag for the trend content.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Provider-specific attributes preserved for downstream analytics.",
    )

    @field_validator("keywords", mode="before")
    @classmethod
    def _normalize_keywords(cls, value: Any) -> tuple[str, ...]:
        """Accept lists or tuples and strip empty keyword strings."""
        if value is None:
            return ()
        if isinstance(value, str):
            stripped = value.strip()
            return (stripped,) if stripped else ()
        return tuple(item.strip() for item in value if isinstance(item, str) and item.strip())


class TrendResult(BaseModel):
    """
    Outcome of a single provider fetch operation.

    ``errors`` captures non-fatal issues (for example, partial page results)
    while still returning whatever items could be retrieved.
    """

    model_config = ConfigDict(frozen=True)

    provider: ProviderType
    items: tuple[TrendItem, ...] = Field(default_factory=tuple)
    fetched_at: datetime = Field(default_factory=_utc_now)
    errors: tuple[str, ...] = Field(default_factory=tuple)

    @property
    def item_count(self) -> int:
        """Number of trend items returned by the provider."""
        return len(self.items)


class TrendHunterRequest(BaseModel):
    """
    Application-level request consumed by ``TrendHunterService``.

    ``providers`` restricts discovery to an explicit subset. When omitted,
    the service resolves providers from configuration and the registry.
    """

    model_config = ConfigDict(frozen=True)

    query: TrendQuery = Field(default_factory=TrendQuery)
    providers: tuple[ProviderType, ...] | None = Field(
        default=None,
        description="Optional subset of providers; defaults to configured enabled set.",
    )
    sort_by: TrendSortOrder = Field(default=TrendSortOrder.SCORE_DESC)
    deduplicate: bool = Field(
        default=True,
        description="When true, merge items with case-insensitive matching titles.",
    )


class TrendHunterResponse(BaseModel):
    """
    Aggregated discovery response returned to callers.

    ``provider_results`` retains per-provider outcomes so callers can inspect
    partial failures without losing successfully fetched trends.
    """

    model_config = ConfigDict(frozen=True)

    request_id: UUID = Field(default_factory=uuid4)
    items: tuple[TrendItem, ...] = Field(default_factory=tuple)
    provider_results: tuple[TrendResult, ...] = Field(default_factory=tuple)
    completed_at: datetime = Field(default_factory=_utc_now)

    @property
    def total_items(self) -> int:
        """Total number of aggregated trend items."""
        return len(self.items)

    @property
    def providers_succeeded(self) -> tuple[ProviderType, ...]:
        """Providers that returned at least one trend item."""
        return tuple(
            result.provider
            for result in self.provider_results
            if result.item_count > 0
        )

    @property
    def providers_failed(self) -> tuple[ProviderType, ...]:
        """Providers that reported errors and returned no items."""
        return tuple(
            result.provider
            for result in self.provider_results
            if result.item_count == 0 and result.errors
        )
