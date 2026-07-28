"""
Score normalization helpers for cross-provider ranking.

Every provider adapter maps its native popularity signal into the closed
interval [0.0, 1.0] using these functions so the collection engine can
compare trends from heterogeneous sources fairly.
"""

from __future__ import annotations

import math


def clamp_score(value: float) -> float:
    """Restrict a numeric score to the inclusive range [0.0, 1.0]."""
    return max(0.0, min(1.0, value))


def normalize_by_rank(rank_index: int, total: int) -> float:
    """
    Convert a zero-based rank position into a descending normalized score.

    The top item (index 0) receives 1.0; the last item approaches 0.1 so
    lower-ranked entries still contribute to aggregate rankings.
    """
    if total <= 0:
        return 0.0
    if total == 1:
        return 1.0
    return clamp_score(1.0 - (rank_index / (total - 1)) * 0.9)


def normalize_count(count: float, *, ceiling: float) -> float:
    """Scale a raw count against a ceiling using a logarithmic curve."""
    if count <= 0 or ceiling <= 0:
        return 0.0
    return clamp_score(math.log1p(count) / math.log1p(ceiling))


def normalize_linear(value: float, *, maximum: float) -> float:
    """Scale a raw value linearly against a known maximum."""
    if value <= 0 or maximum <= 0:
        return 0.0
    return clamp_score(value / maximum)
