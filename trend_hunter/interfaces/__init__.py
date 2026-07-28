"""Port interfaces consumed by the Trend Hunter application layer."""

from trend_hunter.interfaces.trend_provider import BaseTrendProvider, TrendProvider

__all__ = ["BaseTrendProvider", "TrendProvider"]
