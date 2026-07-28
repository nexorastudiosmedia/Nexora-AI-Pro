"""Public exception types exported by Trend Hunter."""

from trend_hunter.exceptions.base import (
    ConfigurationError,
    ProviderFetchError,
    ProviderNotConfiguredError,
    ProviderNotRegisteredError,
    TrendHunterError,
)

__all__ = [
    "ConfigurationError",
    "ProviderFetchError",
    "ProviderNotConfiguredError",
    "ProviderNotRegisteredError",
    "TrendHunterError",
]
