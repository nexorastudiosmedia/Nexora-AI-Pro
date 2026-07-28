"""
Trend Hunter domain layer.

Contains pure business types (models and enumerations) with no I/O dependencies.
Import from this package when defining contracts that must remain stable across
provider implementations.
"""

from trend_hunter.domain.enums import ProviderType, TrendSortOrder, TrendTimeRange
from trend_hunter.domain.models import (
    TrendHunterRequest,
    TrendHunterResponse,
    TrendItem,
    TrendQuery,
    TrendResult,
)

__all__ = [
    "ProviderType",
    "TrendHunterRequest",
    "TrendHunterResponse",
    "TrendItem",
    "TrendQuery",
    "TrendResult",
    "TrendSortOrder",
    "TrendTimeRange",
]
