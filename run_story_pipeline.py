"""
Story pipeline: Trend Hunter -> Story Content Engine -> Video Story Engine
-> Facebook Story Post

Always generates FRESH content (never reused from run_pipeline.py or
run_reel_pipeline.py). Always produces a video story (with matching zoom
+ music) so every story is visually and audibly consistent.
"""
import asyncio
import os
import random
import requests
from dotenv import load_dotenv

from content.story_content_engine import generate_story_content
from trend_hunter.di.container import create_container
from trend_hunter.domain.models import TrendHunterRequest, TrendQuery
from trend_hunter.providers.common.http_client import AsyncHttpClient
from trend_hunter.providers.google_news_rss_provider import create_google_news_rss_provider
from trend_hunter.providers.google_trends_provider import create_google_trends_provider
from trend_hunter.providers.rss_provider import create_rss_provider
from image_generation.story_video_engine import create_story_video

load_dotenv()

PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
GRAPH_VERSION = "v20.0"


async def get_story_trend():
    container = create_container()
    http_client = AsyncHttpClient(container.settings)
    container.register_provider(create_google_news_rss_provider(container.settings, http_client))
    container.register_provider(create_google_trends_provider(container.settings, http_client))
    container.register_provider(create_rss_provider(container.settings, http_client))
    query = TrendQuery(niche="philosophy", region="US", language="en", limit=10)
    response = await container.service.discover(TrendHunterRequest(query=query))

    if not response.items:
        raise RuntimeError("No trends found — check your internet connection.")

    # Different slice than run_pipeline.py (items[0]) and run_reel_pipeline.py
    # (items[1:5]) so a Story never overlaps their topic pick.
    pool = response.items[5:10] if len(response.items) > 5 else response.items
    return random.choice(pool)


def post_video_story(video_path: str):
    base_url = f"https://graph.facebook.com/{GRAPH_VERSION}"

    # Step 1: start upload session
    start_resp = requests.post(
        f"{base_url}/{PAGE_ID}/video_stories",
        data={"upload_phase": "start", "access_token": ACCESS_TOKEN},
    )
    start_data = start_resp.json()
    if "video_id" not in start_data:
        print("❌ Failed to start story upload session.")
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
        print("❌ Failed to upload story video.")
        print("Error:", upload_resp.status_code, upload_resp.text)
        return upload_resp.json()

    # Step 3: publish
    finish_resp = requests.post(
        f"{base_url}/{PAGE_ID}/video_stories",
        data={"upload_phase": "finish", "video_id": video_id, "access_token": ACCESS_TOKEN},
    )
    finish_data = finish_resp.json()
    if finish_resp.status_code == 200:
        print("✅ Video story published!")
    else:
        print("❌ Video story publish failed.")
        print("Error:", finish_data)
    return finish_data


async def run_story_pipeline():
    print("Step 1/3: Fetching a story-specific trending topic...")
    trend = await get_story_trend()
    print(f"  ✔ Story topic: {trend.title}\n")

    print("Step 2/3: Generating fresh story line (Groq AI)...")
    content = generate_story_content(trend.title)
    print(f"  ✔ Line: {content['line']}\n")

    print("Step 3/3: Building the story video and publishing...")
    asset_path = create_story_video(content["line"])
    post_video_story(asset_path)


if __name__ == "__main__":
    asyncio.run(run_story_pipeline())
