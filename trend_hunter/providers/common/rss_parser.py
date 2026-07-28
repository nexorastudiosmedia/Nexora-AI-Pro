"""
RSS and Atom feed parsing utilities.

Wraps ``feedparser`` in a thread offload so async provider adapters remain
non-blocking while consuming syndication feeds from free public endpoints.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

import feedparser

from trend_hunter.infrastructure.logging import get_logger

logger = get_logger("providers.common.rss_parser")


@dataclass(frozen=True)
class ParsedFeedItem:
    """Normalized representation of a single RSS/Atom entry."""

    title: str
    url: str | None
    published_at: datetime | None
    category: str
    raw_traffic: str | None = None


def _parse_published(entry: Any) -> datetime | None:
    """Extract a UTC publication timestamp from a feedparser entry."""
    if hasattr(entry, "published_parsed") and entry.published_parsed:
        try:
            return datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass

    if hasattr(entry, "updated_parsed") and entry.updated_parsed:
        try:
            return datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
        except (TypeError, ValueError):
            pass

    published = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if published:
        try:
            parsed = parsedate_to_datetime(published)
            if parsed.tzinfo is None:
                return parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc)
        except (TypeError, ValueError):
            return None

    return None


def _parse_category(entry: Any, fallback: str) -> str:
    """Read the first category tag from an entry, falling back when absent."""
    tags = getattr(entry, "tags", None) or []
    for tag in tags:
        label = getattr(tag, "term", None) or getattr(tag, "label", None)
        if label:
            return str(label).strip().lower()[:64]
    return fallback


def _parse_traffic(entry: Any) -> str | None:
    """Read Google Trends approximate traffic when present in RSS extensions."""
    for key in ("ht_approx_traffic", "approx_traffic"):
        value = getattr(entry, key, None)
        if value:
            return str(value)
    return None


def _parse_feed_sync(content: bytes | str) -> list[ParsedFeedItem]:
    """Synchronously parse feed content into normalized items."""
    parsed = feedparser.parse(content)
    if parsed.bozo and not parsed.entries:
        logger.warning("Feed parse warning: %s", parsed.bozo_exception)

    items: list[ParsedFeedItem] = []
    for entry in parsed.entries:
        title = getattr(entry, "title", "").strip()
        if not title:
            continue

        url = getattr(entry, "link", None) or getattr(entry, "id", None)
        items.append(
            ParsedFeedItem(
                title=title,
                url=str(url) if url else None,
                published_at=_parse_published(entry),
                category=_parse_category(entry, fallback="news"),
                raw_traffic=_parse_traffic(entry),
            )
        )
    return items


async def parse_feed(content: bytes | str) -> list[ParsedFeedItem]:
    """Parse RSS/Atom content without blocking the event loop."""
    return await asyncio.to_thread(_parse_feed_sync, content)
