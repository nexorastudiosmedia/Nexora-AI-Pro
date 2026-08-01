"""
Reel pipeline: Trend Hunter -> Reel Content Engine -> Reel Engine -> Facebook Reel Post

This is a SEPARATE pipeline from run_pipeline.py so a Reel never shares text
with a same-day regular post. It also intentionally picks a DIFFERENT trend
item than the main pipeline (which always takes items[0]) to reduce overlap.
"""
import asyncio
import os
import random
import requests
from dotenv import load_dotenv

from content.reel_content_engine import generate_reel_content
from trend_hunter.di.container import create_container
from trend_hunter.domain.models import TrendHunterRequest, TrendQuery
from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.google_news_rss_provider import create_google_news_rss_provider
from trend_hunter.providers.google_trends_provider import create_google_trends_provider
from trend_hunter.providers.rss_provider import create_rss_provider
from image_generation.reel_engine import create_reel

load_dotenv()

PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
GRAPH_VERSION = "v20.0"


async def get_reel_trend():
    container = create_container()
    http_client = AsyncHttpClient(container.settings)
    container.register_provider(create_google_news_rss_provider(container.settings, http_client))
    container.register_provider(create_google_trends_provider(container.settings, http_client))
    container.register_provider(create_rss_provider(container.settings, http_client))
    query = TrendQuery(niche="philosophy", region="US", language="en", limit=10)
    response = await container.service.discover(TrendHunterRequest(query=query))

    if not response.items:
        raise RuntimeError("No trends found — check your internet connection.")

    # Deliberately avoid items[0] (that's what the regular post pipeline uses)
    # so a Reel and a same-day post don't end up inspired by the same topic.
    pool = response.items[1:5] if len(response.items) > 1 else response.items
    return random.choice(pool)


def post_reel_to_facebook(video_path: str, caption: str):
    """
    Publishes a local MP4 as a Facebook Page Reel using the 3-step
    Video Reels API (start -> upload -> finish/publish).
    """
    base_url = f"https://graph.facebook.com/{GRAPH_VERSION}"

    # Step 1: start upload session
    start_resp = requests.post(
        f"{base_url}/{PAGE_ID}/video_reels",
        data={"upload_phase": "start", "access_token": ACCESS_TOKEN},
    )
    start_data = start_resp.json()
    if "video_id" not in start_data:
        print("❌ Failed to start reel upload session.")
        print("Error:", start_data)
        return start_data

    video_id = start_data["video_id"]
    upload_url = start_data["upload_url"]

    # Step 2: upload video bytes
    file_size = os.path.getsize(video_path)
    with open(video_path, "rb") as f:
        upload_resp = requests.post(
            upload_url,
            headers={
                "Authorization": f"OAuth {ACCESS_TOKEN}",
                "offset": "0",
                "file_size": str(file_size),
            },
            data=f.read(),
        )

    if upload_resp.status_code != 200 or not upload_resp.json().get("success", False):
        print("❌ Failed to upload reel video.")
        print("Error:", upload_resp.status_code, upload_resp.text)
        return upload_resp.json()

    # Step 3: publish
    finish_resp = requests.post(
        f"{base_url}/{PAGE_ID}/video_reels",
        data={
            "upload_phase": "finish",
            "video_id": video_id,
            "video_state": "PUBLISHED",
            "description": caption,
            "access_token": ACCESS_TOKEN,
        },
    )
    finish_data = finish_resp.json()

    if finish_data.get("success", False):
        print("✅ Reel published successfully!")
        print("Video ID:", video_id)
    else:
        print("❌ Reel publish step failed.")
        print("Error:", finish_data)

    return finish_data


async def run_reel_pipeline():
    print("Step 1/4: Fetching a reel-specific trending topic...")
    trend = await get_reel_trend()
    print(f"  ✔ Reel topic: {trend.title}\n")

    print("Step 2/4: Generating short-form reel content (Groq AI)...")
    content = generate_reel_content(trend.title)
    print(f"  ✔ Hook: {content['hook']}\n")

    print("Step 3/4: Building the reel video...")
    video_path = create_reel(content["hook"], content.get("line2", ""), content.get("line3", ""))
    print(f"  ✔ Video saved: {video_path}\n")

    print("Step 4/4: Publishing reel to Facebook Page...")
    post_reel_to_facebook(video_path, content["caption"])


if __name__ == "__main__":
    asyncio.run(run_reel_pipeline())
