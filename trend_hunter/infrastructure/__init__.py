"""Infrastructure adapters supporting Trend Hunter cross-cutting concerns."""

from trend_hunter.infrastructure.logging import configure_logging, get_logger

__all__ = ["configure_logging", "get_logger"]
