"""
Master pipeline: Trend Hunter -> Content Engine -> Image Engine -> Facebook Post
Runs the full automation: fetches a trending topic, generates a philosophy
post, creates a matching quote-card image, and publishes both to the
Facebook Page in a single post.
"""
import asyncio
import os
import requests
from dotenv import load_dotenv

from content.content_engine import ContentEngine
from trend_hunter.di.container import create_container
from trend_hunter.domain.models import TrendHunterRequest, TrendQuery
from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.google_news_rss_provider import create_google_news_rss_provider
from trend_hunter.providers.google_trends_provider import create_google_trends_provider
from trend_hunter.providers.rss_provider import create_rss_provider
from image_generation.image_engine import create_quote_card

load_dotenv()

PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")


async def get_top_trend():
    container = create_container()
    http_client = AsyncHttpClient(container.settings)
    container.register_provider(create_google_news_rss_provider(container.settings, http_client))
    container.register_provider(create_google_trends_provider(container.settings, http_client))
    container.register_provider(create_rss_provider(container.settings, http_client))
    query = TrendQuery(niche="philosophy", region="US", language="en", limit=10)
    response = await container.service.discover(TrendHunterRequest(query=query))

    if not response.items:
        raise RuntimeError("No trends found � check your internet connection.")
    return response.items[0]


def post_photo_to_facebook(image_path: str, caption: str):
    """
    Uploads a local image with a caption to the Facebook Page.
    This publishes both the image and text as a single post.
    """
    url = f"https://graph.facebook.com/v20.0/{PAGE_ID}/photos"

    with open(image_path, "rb") as image_file:
        files = {"source": image_file}
        payload = {
            "caption": caption,
            "access_token": ACCESS_TOKEN,
        }
        response = requests.post(url, data=payload, files=files)

    result = response.json()

    if response.status_code == 200 and "id" in result:
        print("? Post with image successful!")
        print("Post ID:", result["id"])
    else:
        print("? Post failed.")
        print("Error:", result)

    return result


async def run_pipeline():
    print("Step 1/4: Fetching top trending topic...")
    top_trend = await get_top_trend()
    print(f"  ? Top trend: {top_trend.title}\n")

    print("Step 2/4: Generating philosophy-angle post (Groq AI)...")
    engine = ContentEngine()
    post = await engine.generate(top_trend.title, top_trend.url)
    caption_text = post.as_facebook_text()
    print("  ? Post generated.\n")

    print("Step 3/4: Creating quote-card image...")
    image_path = create_quote_card(caption_text, "daily_post.png")
    print(f"  ? Image saved: {image_path}\n")

    print("Step 4/4: Publishing to Facebook Page...")
    post_photo_to_facebook(image_path, caption_text)


if __name__ == "__main__":
    asyncio.run(run_pipeline())