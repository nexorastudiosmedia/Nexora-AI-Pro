"""
Reel Content Engine
--------------------
Generates SHORT, punchy philosophy content specifically for Reels.
Separate from content/content_engine.py (which writes the longer text posts)
so a Reel never repeats what a same-day regular post says.
"""

import os
import json
from groq import Groq

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def generate_reel_content(trend_title: str) -> dict:
    """
    trend_title: a trending topic title (from Trend Hunter)
    Returns: {"hook": str, "line2": str, "caption": str}
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""You write ultra-short philosophical reel scripts for a Facebook
Reels page called "Nexora Reflections".

Trending topic for loose inspiration (do not mention it literally): "{trend_title}"

Write ONE piece of short-form philosophical content for a 15-20 second video.
Rules:
- hook: max 8 words, punchy, screen-friendly, no hashtags, no emojis
- line2: max 10 words, a natural follow-up to the hook (empty string if hook stands alone)
- caption: 1-2 sentences for the Facebook caption below the video, ending with 3-5 relevant hashtags
- Must feel written for video pacing (short beats), not a generic quote-card line
- Avoid overused/common quotes

Return ONLY valid JSON, no markdown, no preamble, in this exact shape:
{{"hook": "...", "line2": "...", "caption": "..."}}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    data = json.loads(raw)
    data.setdefault("line2", "")
    return data


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    sample = generate_reel_content("the pace of modern life")
    print(json.dumps(sample, indent=2))
