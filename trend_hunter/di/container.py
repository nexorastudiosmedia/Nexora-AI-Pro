"""
Dependency injection container for Trend Hunter.

The container wires settings, logging, the provider registry, and the
application service. Application bootstrap code constructs a single container
per process and registers provider adapters before calling ``service``.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from trend_hunter.config.settings import TrendHunterSettings, get_trend_hunter_settings
from trend_hunter.infrastructure.logging import configure_logging, get_logger
from trend_hunter.interfaces.trend_provider import TrendProvider
from trend_hunter.providers.registry import ProviderRegistry
from trend_hunter.services.trend_hunter_service import TrendHunterService


@dataclass
class TrendHunterContainer:
    """
    Composition root for Trend Hunter dependencies.

    Attributes:
        settings: Environment-backed module configuration.
        registry: Provider adapter registry populated via ``register_provider``.
        service: Application service resolved from the registry and settings.
    """

    settings: TrendHunterSettings = field(default_factory=get_trend_hunter_settings)
    registry: ProviderRegistry = field(default_factory=ProviderRegistry)
    _service: TrendHunterService | None = field(default=None, init=False, repr=False)
    _logging_initialized: bool = field(default=False, init=False, repr=False)

    def bootstrap(self) -> TrendHunterContainer:
        """
        Initialize logging and prepare the container for use.

        Safe to call multiple times; logging handlers are replaced on each call
        to support test isolation.
        """
        configure_logging(self.settings)
        self._logging_initialized = True
        get_logger("di.container").info("Trend Hunter container bootstrapped.")
        return self

    def register_provider(self, provider: TrendProvider) -> None:
        """Register a provider adapter and invalidate the cached service."""
        self.registry.register(provider)
        self._service = None

    @property
    def service(self) -> TrendHunterService:
        """
        Lazily construct the ``TrendHunterService`` singleton for this container.

        Logging is configured automatically on first access when ``bootstrap``
        has not been called explicitly.
        """
        if not self._logging_initialized:
            self.bootstrap()

        if self._service is None:
            self._service = TrendHunterService(
                registry=self.registry,
                settings=self.settings,
            )
        return self._service


def create_container(
    settings: TrendHunterSettings | None = None,
    *,
    bootstrap: bool = True,
) -> TrendHunterContainer:
    """
    Factory function for constructing a ready-to-use container.

    Args:
        settings: Optional settings override (commonly used in tests).
        bootstrap: When true, configure logging during creation.
    """
    container = TrendHunterContainer(
        settings=settings or get_trend_hunter_settings(),
    )
    if bootstrap:
        container.bootstrap()
    return container
