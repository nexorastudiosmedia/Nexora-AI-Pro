"""
Provider adapter package for Trend Hunter.

Concrete source integrations (Google Trends, Reddit, News APIs, RSS, YouTube)
are registered at application startup through ``ProviderRegistry``. This
package intentionally contains no adapter implementations during Phase 1.
"""

from trend_hunter.providers.registry import ProviderRegistry

__all__ = ["ProviderRegistry"]
