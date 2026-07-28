"""
Provider port definitions for Trend Hunter.

This module defines the contract every external trend source must satisfy.
Concrete adapters (Google Trends, Reddit, and so on) live under
``trend_hunter.providers`` and depend inward on these abstractions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Protocol, runtime_checkable

from trend_hunter.domain.enums import ProviderType
from trend_hunter.domain.models import TrendQuery, TrendResult


@runtime_checkable
class TrendProvider(Protocol):
    """
    Structural interface for trend provider adapters.

    ``Protocol`` enables duck-typing for tests and third-party extensions
    while ``BaseTrendProvider`` supplies a concrete ABC for in-tree adapters.
    """

    @property
    def provider_type(self) -> ProviderType:
        """Unique identifier matching ``ProviderType`` enumeration values."""
        ...

    async def fetch_trends(self, query: TrendQuery) -> TrendResult:
        """Retrieve normalized trend items for the given query."""
        ...

    def is_configured(self) -> bool:
        """Return ``True`` when required credentials and settings are present."""
        ...


class BaseTrendProvider(ABC):
    """
    Abstract base class for first-party Trend Hunter provider adapters.

    Subclasses implement ``fetch_trends`` and declare their ``provider_type``.
    The base class centralizes configuration checks and logging hooks so each
    adapter stays focused on source-specific retrieval logic.
    """

    @property
    @abstractmethod
    def provider_type(self) -> ProviderType:
        """Provider identifier used for registry lookup and result tagging."""

    @abstractmethod
    async def fetch_trends(self, query: TrendQuery) -> TrendResult:
        """
        Fetch and normalize trends from the upstream source.

        Implementations must not raise for expected API conditions (empty
        results, rate limits with retry exhausted). Instead, return a
        ``TrendResult`` with explanatory ``errors`` entries.
        """

    @abstractmethod
    def is_configured(self) -> bool:
        """
        Report whether this adapter has the credentials it needs to run.

        The service layer skips unconfigured providers during discovery when
        ``skip_unconfigured`` is enabled in settings.
        """

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(provider={self.provider_type.value})"
