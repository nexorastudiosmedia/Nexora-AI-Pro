"""
Shared async HTTP client for Trend Hunter provider adapters.

Centralizes timeouts, redirect handling, and User-Agent headers so every
free-source adapter behaves consistently when calling public endpoints.
"""

from __future__ import annotations

from typing import Any

import httpx

from trend_hunter.config.settings import TrendHunterSettings
from trend_hunter.infrastructure.logging import get_logger

logger = get_logger("providers.common.http_client")


class AsyncHttpClient:
    """Thin wrapper around ``httpx.AsyncClient`` used by provider adapters."""

    def __init__(self, settings: TrendHunterSettings) -> None:
        self._settings = settings
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout_seconds),
            headers={"User-Agent": settings.reddit_user_agent},
            follow_redirects=True,
        )

    async def get_text(self, url: str, *, headers: dict[str, str] | None = None) -> str:
        """Perform a GET request and return the response body as text."""
        response = await self._request("GET", url, headers=headers)
        return response.text

    async def get_bytes(self, url: str, *, headers: dict[str, str] | None = None) -> bytes:
        """Perform a GET request and return raw response bytes."""
        response = await self._request("GET", url, headers=headers)
        return response.content

    async def get_json(
        self,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> Any:
        """Perform a GET request and decode the JSON response body."""
        response = await self._request("GET", url, headers=headers, params=params)
        return response.json()

    async def _request(
        self,
        method: str,
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        try:
            response = await self._client.request(
                method,
                url,
                headers=headers,
                params=params,
            )
            response.raise_for_status()
            return response
        except httpx.TimeoutException as exc:
            logger.error("HTTP timeout for %s: %s", url, exc)
            raise
        except httpx.HTTPStatusError as exc:
            logger.error(
                "HTTP %s for %s: %s",
                exc.response.status_code,
                url,
                exc.response.text[:200],
            )
            raise
        except httpx.HTTPError as exc:
            logger.error("HTTP error for %s: %s", url, exc)
            raise

    async def aclose(self) -> None:
        """Close the underlying HTTP connection pool."""
        await self._client.aclose()

    async def __aenter__(self) -> AsyncHttpClient:
        return self

    async def __aexit__(self, *args: object) -> None:
        await self.aclose()
