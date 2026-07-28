"""
Quick test script for Trend Hunter.

Run this to check whether the trend research module actually fetches
real trending topics (Google News + Google Trends + RSS).

Usage (from the Nexora-AI-Pro folder):
    pip install -r requirements.txt
    pip install httpx feedparser
    python test_trend_hunter.py
"""

import asyncio

from trend_hunter.di.container import create_container
from trend_hunter.domain.models import TrendHunterRequest, TrendQuery
from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.google_news_rss_provider import create_google_news_rss_provider
from trend_hunter.providers.google_trends_provider import create_google_trends_provider
from trend_hunter.providers.rss_provider import create_rss_provider


async def main():
    container = create_container()
    http_client = AsyncHttpClient(container.settings)

    # Wire up the three free providers (no API keys needed)
    container.register_provider(
        create_google_news_rss_provider(container.settings, http_client)
    )
    container.register_provider(
        create_google_trends_provider(container.settings, http_client)
    )
    container.register_provider(
        create_rss_provider(container.settings, http_client)
    )

    query = TrendQuery(
        niche="philosophy",
        region="US",
        language="en",
        limit=10,
    )
    request = TrendHunterRequest(query=query)

    response = await container.service.discover(request)

    print(f"\nTotal items found: {response.total_items}")
    print(f"Providers succeeded: {[p.value for p in response.providers_succeeded]}")
    print(f"Providers failed: {[p.value for p in response.providers_failed]}\n")

    for item in response.items:
        print(f"- [{item.score:.2f}] {item.title}  ({item.url})")


if __name__ == "__main__":
    asyncio.run(main())
