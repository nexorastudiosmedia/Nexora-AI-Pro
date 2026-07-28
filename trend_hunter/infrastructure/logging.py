"""
Logging infrastructure for Trend Hunter.

Configures structured, namespaced loggers under the ``trend_hunter`` prefix.
Call ``configure_logging`` once during application bootstrap before any
service or provider code executes.
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path

from trend_hunter.config.settings import TrendHunterSettings

LOG_NAMESPACE = "trend_hunter"
DEFAULT_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
)
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def configure_logging(settings: TrendHunterSettings) -> None:
    """
    Apply Trend Hunter logging configuration to the process.

    When ``log_to_file`` is enabled, records are written to
    ``{log_dir}/trend_hunter.log`` in addition to stderr. Existing handlers
    on the namespaced logger are replaced to avoid duplicate log lines during
    repeated bootstrap in tests or REPL sessions.
    """
    logger = logging.getLogger(LOG_NAMESPACE)
    logger.handlers.clear()
    logger.setLevel(settings.resolved_log_level)
    logger.propagate = False

    formatter = logging.Formatter(DEFAULT_LOG_FORMAT, datefmt=DEFAULT_DATE_FORMAT)

    stream_handler = logging.StreamHandler(sys.stderr)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if settings.log_to_file:
        log_path = _resolve_log_file(settings.log_dir)
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    logger.debug(
        "Trend Hunter logging configured (level=%s, file=%s).",
        logging.getLevelName(settings.resolved_log_level),
        settings.log_to_file,
    )


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the ``trend_hunter`` namespace.

    Example:
        ``get_logger("services.trend_hunter")`` → ``trend_hunter.services.trend_hunter``
    """
    if name.startswith(f"{LOG_NAMESPACE}."):
        return logging.getLogger(name)
    return logging.getLogger(f"{LOG_NAMESPACE}.{name}")


def _resolve_log_file(log_dir: Path) -> Path:
    """Ensure the log directory exists and return the Trend Hunter log path."""
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "trend_hunter.log"
