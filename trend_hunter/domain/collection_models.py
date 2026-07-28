"""
Domain models for trend collection runs and persisted topic records.

These types bridge the discovery layer (``TrendItem``) and the SQLite storage
layer without leaking SQL details into application services.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from trend_hunter.domain.enums import ProviderType
from trend_hunter.domain.models import TrendItem


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CollectionRun(BaseModel):
    """Metadata describing a single end-to-end collection execution."""

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    started_at: datetime = Field(default_factory=_utc_now)
    completed_at: datetime | None = None
    providers_queried: tuple[ProviderType, ...] = Field(default_factory=tuple)
    raw_item_count: int = 0
    unique_item_count: int = 0
    stored_item_count: int = 0


class TrendingTopic(BaseModel):
    """
    Fully ranked trend topic ready for API consumption or persistence.

    ``rank`` is 1-based within a collection run, assigned after global
    deduplication and score-based sorting.
    """

    model_config = ConfigDict(frozen=True)

    id: UUID = Field(default_factory=uuid4)
    collection_run_id: UUID
    title: str = Field(min_length=1)
    source: ProviderType
    url: str | None = None
    published_at: datetime | None = None
    popularity_score: float = Field(ge=0.0, le=1.0)
    rank: int = Field(ge=1)
    keywords: tuple[str, ...] = Field(default_factory=tuple)
    category: str = "general"
    country: str = "US"
    language: str = "en"
    content_hash: str = Field(min_length=8)
    collected_at: datetime = Field(default_factory=_utc_now)

    @classmethod
    def from_trend_item(
        cls,
        item: TrendItem,
        *,
        collection_run_id: UUID,
        rank: int,
        content_hash: str,
    ) -> TrendingTopic:
        """Map a discovered ``TrendItem`` into a ranked ``TrendingTopic``."""
        return cls(
            id=item.id,
            collection_run_id=collection_run_id,
            title=item.title,
            source=item.source,
            url=item.url,
            published_at=item.published_at,
            popularity_score=item.score,
            rank=rank,
            keywords=item.keywords,
            category=item.category,
            country=item.country,
            language=item.language,
            content_hash=content_hash,
        )


class CollectionResult(BaseModel):
    """Outcome returned by ``TrendCollectionEngine.collect``."""

    model_config = ConfigDict(frozen=True)

    run: CollectionRun
    topics: tuple[TrendingTopic, ...] = Field(default_factory=tuple)

    @property
    def top_topic(self) -> TrendingTopic | None:
        """Highest-ranked topic from the run, when any were collected."""
        return self.topics[0] if self.topics else None


class TopTrendsRequest(BaseModel):
    """Query parameters for retrieving stored top trends."""

    model_config = ConfigDict(frozen=True)

    limit: int = Field(default=25, ge=1, le=500)
    collection_run_id: UUID | None = Field(
        default=None,
        description="Specific run to query; defaults to the latest completed run.",
    )
    category: str | None = None
    source: ProviderType | None = None
    country: str | None = None


class TopTrendsResponse(BaseModel):
    """Ranked trending topics loaded from SQLite."""

    model_config = ConfigDict(frozen=True)

    collection_run_id: UUID
    collected_at: datetime
    topics: tuple[TrendingTopic, ...] = Field(default_factory=tuple)
    total_available: int = 0
