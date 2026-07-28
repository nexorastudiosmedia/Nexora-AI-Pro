"""
Trend Hunter exception hierarchy.

All module-specific errors inherit from ``TrendHunterError`` so callers can
catch domain failures without coupling to individual provider implementations.
"""

from trend_hunter.domain.enums import ProviderType


class TrendHunterError(Exception):
    """Base exception for recoverable Trend Hunter failures."""


class ConfigurationError(TrendHunterError):
    """Raised when environment or runtime configuration is invalid."""


class ProviderNotRegisteredError(TrendHunterError):
    """Raised when a requested provider has no adapter in the registry."""

    def __init__(self, provider: ProviderType) -> None:
        self.provider = provider
        super().__init__(f"No provider adapter registered for '{provider.value}'.")


class ProviderFetchError(TrendHunterError):
    """Raised when a provider adapter fails during trend retrieval."""

    def __init__(self, provider: ProviderType, message: str) -> None:
        self.provider = provider
        super().__init__(f"Provider '{provider.value}' fetch failed: {message}")


class ProviderNotConfiguredError(TrendHunterError):
    """Raised when a provider adapter is registered but lacks required credentials."""

    def __init__(self, provider: ProviderType, detail: str) -> None:
        self.provider = provider
        super().__init__(
            f"Provider '{provider.value}' is not configured: {detail}"
        )
