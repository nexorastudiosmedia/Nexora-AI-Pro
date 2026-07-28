"""
Provider registry for Trend Hunter.

The registry is the composition root for provider adapters. Registration
happens explicitly at startup (via the DI container or application bootstrap)
so the set of active sources is always intentional and observable.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator, Sequence

from trend_hunter.domain.enums import ProviderType
from trend_hunter.exceptions import ProviderNotRegisteredError
from trend_hunter.interfaces.trend_provider import TrendProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """
    In-memory registry mapping ``ProviderType`` values to provider adapters.

    Thread safety is the caller's responsibility. The Nexora AI bootstrap
    should build the registry once during application startup and treat it as
    read-only for the lifetime of the process.
    """

    def __init__(self) -> None:
        self._providers: dict[ProviderType, TrendProvider] = {}

    def register(self, provider: TrendProvider) -> None:
        """
        Add or replace a provider adapter.

        Raises:
            TypeError: If ``provider`` does not satisfy the ``TrendProvider`` protocol.
        """
        if not isinstance(provider, TrendProvider):
            raise TypeError(
                f"Provider must implement TrendProvider protocol; got {type(provider)!r}."
            )

        provider_type = provider.provider_type
        if provider_type in self._providers:
            logger.info(
                "Replacing existing provider adapter for '%s'.",
                provider_type.value,
            )

        self._providers[provider_type] = provider
        logger.debug("Registered provider adapter: %s.", provider)

    def unregister(self, provider_type: ProviderType) -> None:
        """Remove a provider adapter if it exists."""
        removed = self._providers.pop(provider_type, None)
        if removed is not None:
            logger.debug("Unregistered provider adapter: %s.", removed)

    def get(self, provider_type: ProviderType) -> TrendProvider:
        """
        Return the adapter for ``provider_type``.

        Raises:
            ProviderNotRegisteredError: When no adapter has been registered.
        """
        try:
            return self._providers[provider_type]
        except KeyError as exc:
            raise ProviderNotRegisteredError(provider_type) from exc

    def resolve(
        self,
        provider_types: Sequence[ProviderType],
        *,
        skip_unconfigured: bool = True,
    ) -> tuple[TrendProvider, ...]:
        """
        Resolve an ordered sequence of providers from explicit type requests.

        Providers that are not registered are omitted with a warning. When
        ``skip_unconfigured`` is true, adapters reporting ``is_configured()``
        as false are also omitted.
        """
        resolved: list[TrendProvider] = []

        for provider_type in provider_types:
            if provider_type not in self._providers:
                logger.warning(
                    "Skipping unregistered provider '%s'.",
                    provider_type.value,
                )
                continue

            provider = self._providers[provider_type]
            if skip_unconfigured and not provider.is_configured():
                logger.warning(
                    "Skipping unconfigured provider '%s'.",
                    provider_type.value,
                )
                continue

            resolved.append(provider)

        return tuple(resolved)

    def all(self) -> tuple[TrendProvider, ...]:
        """Return every registered provider in insertion order."""
        return tuple(self._providers.values())

    def registered_types(self) -> tuple[ProviderType, ...]:
        """Return provider types currently present in the registry."""
        return tuple(self._providers.keys())

    def __contains__(self, provider_type: ProviderType) -> bool:
        return provider_type in self._providers

    def __len__(self) -> int:
        return len(self._providers)

    def __iter__(self) -> Iterator[TrendProvider]:
        return iter(self._providers.values())
