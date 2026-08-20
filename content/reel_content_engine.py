"""
Reel Content Engine
--------------------
Generates SHORT, punchy philosophy content specifically for Reels.
Separate from content/content_engine.py (which writes the longer text posts)
so a Reel never repeats what a same-day regular post says.

Produces THREE text beats (hook -> line2 -> line3) so the video has enough
content to fill its full duration instead of one line sitting on screen alone.
"""

import os
import json
from groq import Groq

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")


def generate_reel_content(trend_title: str) -> dict:
    """
    trend_title: a trending topic title (from Trend Hunter)
    Returns: {"hook": str, "line2": str, "line3": str, "caption": str}
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""You write ultra-short philosophical reel scripts for a Facebook
Reels page called "Nexora Reflections". Your #1 job is to stop the scroll in
the first 1 second, because Reels live or die on the hook.

Trending topic for loose inspiration (do not mention it literally): "{trend_title}"

Write ONE piece of short-form philosophical content for an 18-second video,
told in THREE beats that build on each other:

Rules:
- hook: max 8 words, MUST be a curiosity-gap, a bold/mildly controversial claim, \
or a direct "you" statement — never a generic proverb opener. This line alone \
decides if someone keeps watching. No hashtags, no emojis.
- line2: max 12 words, REQUIRED (never empty), develops the hook into a fuller thought
- line3: max 12 words, REQUIRED (never empty), a closing reflection or gentle challenge — the "punch" that ends the video
- caption: 2-3 sentences for the Facebook caption below the video. The LAST sentence \
MUST be a direct engagement question or prompt (e.g. "Do you agree, or nah?", \
"Tag someone who needs this."), followed by 3-5 relevant hashtags.
- Must feel written for video pacing (three distinct short beats, not one long sentence split up)
- Avoid overused/common quotes

Return ONLY valid JSON, no markdown, no preamble, in this exact shape:
{{"hook": "...", "line2": "...", "line3": "...", "caption": "..."}}
"""

response = client.chat.completions.create(
    model=GROQ_MODEL,
    messages=[{"role": "user", "content": prompt}],
    temperature=0.9,
    max_tokens=350,
    response_format={"type": "json_object"},
)
    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    data = json.loads(raw)
    # safety fallbacks in case the model skips a field
    data.setdefault("line2", "There is more beneath the surface.")
    data.setdefault("line3", "Sit with that for a moment.")
    return data


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    sample = generate_reel_content("the pace of modern life")
    print(json.dumps(sample, indent=2))
