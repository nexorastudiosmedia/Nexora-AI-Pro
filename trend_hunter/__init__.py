"""
Trend Hunter — multi-source trend discovery for Nexora AI.

Public API for application bootstrap and service access. Provider adapters are
registered on the container before invoking discovery operations.

Example:
    from trend_hunter import create_container
    from trend_hunter.domain import TrendHunterRequest, TrendQuery

    container = create_container()
    response = await container.service.discover(
        TrendHunterRequest(query=TrendQuery(keywords=("ai", "automation")))
    )
"""

from trend_hunter.config import TrendHunterSettings, get_trend_hunter_settings
from trend_hunter.di import TrendHunterContainer, create_container
from trend_hunter.domain import (
    ProviderType,
    TrendHunterRequest,
    TrendHunterResponse,
    TrendItem,
    TrendQuery,
    TrendResult,
    TrendSortOrder,
    TrendTimeRange,
)
from trend_hunter.exceptions import (
    ConfigurationError,
    ProviderFetchError,
    ProviderNotConfiguredError,
    ProviderNotRegisteredError,
    TrendHunterError,
)
from trend_hunter.interfaces import BaseTrendProvider, TrendProvider
from trend_hunter.providers import ProviderRegistry
from trend_hunter.services import TrendHunterService

__all__ = [
    "BaseTrendProvider",
    "ConfigurationError",
    "ProviderFetchError",
    "ProviderNotConfiguredError",
    "ProviderNotRegisteredError",
    "ProviderRegistry",
    "ProviderType",
    "TrendHunterContainer",
    "TrendHunterError",
    "TrendHunterRequest",
    "TrendHunterResponse",
    "TrendHunterService",
    "TrendHunterSettings",
    "TrendItem",
    "TrendProvider",
    "TrendQuery",
    "TrendResult",
    "TrendSortOrder",
    "TrendTimeRange",
    "create_container",
    "get_trend_hunter_settings",
]

__version__ = "1.0.0"
