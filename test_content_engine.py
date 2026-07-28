"""
End-to-end test: Trend Hunter -> Content Engine.

Fetches real trending topics, picks the top one, and generates a
ready-to-publish Facebook post in the Philosophy / Deep Thoughts voice.

Setup:
    1. Get a free API key at https://console.groq.com
    2. Copy .env.example to .env (if you haven't already)
    3. Put your key in .env:  GROQ_API_KEY=gsk_xxxxxxxx
    4. pip install -r requirements.txt
    5. python test_content_engine.py
"""

import asyncio

from content.content_engine import ContentEngine
from trend_hunter.di.container import create_container
from trend_hunter.domain.models import TrendHunterRequest, TrendQuery
from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.google_news_rss_provider import create_google_news_rss_provider
from trend_hunter.providers.google_trends_provider import create_google_trends_provider
from trend_hunter.providers.rss_provider import create_rss_provider


async def get_top_trend():
    container = create_container()
    http_client = AsyncHttpClient(container.settings)

    container.register_provider(create_google_news_rss_provider(container.settings, http_client))
    container.register_provider(create_google_trends_provider(container.settings, http_client))
    container.register_provider(create_rss_provider(container.settings, http_client))

    query = TrendQuery(niche="philosophy", region="US", language="en", limit=10)
    response = await container.service.discover(TrendHunterRequest(query=query))

    if not response.items:
        raise RuntimeError("No trends found — check your internet connection.")

    return response.items[0]  # highest-scored item


async def main():
    print("Fetching top trending topic...")
    top_trend = await get_top_trend()
    print(f"\nTop trend: {top_trend.title}\n")

    print("Generating philosophy-angle Facebook post...\n")
    engine = ContentEngine()
    post = await engine.generate(top_trend.title, top_trend.url)

    print("=" * 60)
    print(post.as_facebook_text())
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
