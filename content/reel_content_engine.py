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
Reels page called "Nexora Reflections".

Trending topic for loose inspiration (do not mention it literally):
"{trend_title}"

Write ONE piece of short-form philosophical content for an 18-second video.

Rules:
- hook: max 8 words. Must create curiosity or make a bold claim.
- line2: max 12 words. Develop the hook.
- line3: max 12 words. End with a reflection or gentle challenge.
- caption: 2-3 sentences. End with an engagement question or prompt.
- No emojis.
- Avoid overused quotes.
- Make the three beats distinct and punchy.

Return ONLY valid JSON with exactly these keys:
{{
  "hook": "string",
  "line2": "string",
  "line3": "string",
  "caption": "string"
}}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": "Return only valid JSON. No markdown or explanation."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.7,
        max_tokens=350,
        include_reasoning=False,
    )

    raw = response.choices[0].message.content

    if not raw:
        raise ValueError("Groq returned an empty content response.")

    raw = raw.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()

    data = json.loads(raw)

    data.setdefault("hook", "Maybe you are thinking about this wrong.")
    data.setdefault("line2", "There is more beneath the surface.")
    data.setdefault("line3", "Sit with that for a moment.")
    data.setdefault(
        "caption",
        "Sometimes the obvious answer hides a deeper truth. "
        "What do you think? #philosophy #mindset #reflection"
    )

    return data

if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    sample = generate_reel_content("the pace of modern life")
    print(json.dumps(sample, indent=2))
