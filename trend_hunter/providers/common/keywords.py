"""
Keyword extraction utilities for trend titles and descriptions.

Uses lightweight stop-word filtering suitable for downstream content
generation without requiring NLP model dependencies.
"""

from __future__ import annotations

import re

_STOP_WORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "has",
        "have", "how", "i", "in", "is", "it", "its", "of", "on", "or", "that",
        "the", "this", "to", "was", "what", "when", "where", "who", "why", "will",
        "with", "you", "your", "we", "they", "their", "our", "not", "but", "can",
        "all", "new", "just", "about", "into", "over", "after", "before", "out",
    }
)

_WORD_PATTERN = re.compile(r"[a-zA-Z0-9][\w\-+#]{1,}")


def extract_keywords(*texts: str, max_keywords: int = 8) -> tuple[str, ...]:
    """
    Derive topical keywords from one or more text fragments.

    Words are lowercased, stop words removed, and duplicates suppressed while
    preserving first-seen order.
    """
    seen: set[str] = set()
    keywords: list[str] = []

    for text in texts:
        for match in _WORD_PATTERN.finditer(text.lower()):
            word = match.group(0).strip("-+#")
            if len(word) < 3 or word in _STOP_WORDS or word in seen:
                continue
            seen.add(word)
            keywords.append(word)
            if len(keywords) >= max_keywords:
                return tuple(keywords)

    return tuple(keywords)
