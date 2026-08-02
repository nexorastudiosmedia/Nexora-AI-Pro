"""
Story Content Engine
---------------------
Generates a SINGLE short line for Facebook Stories — always fresh, never
reused from a regular post or a Reel. Stories are quick-glance content,
so this is intentionally lighter than reel_content_engine.py's 3-beat script.
"""

import os
import json
from groq import Groq

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")


def generate_story_content(trend_title: str) -> dict:
    """
    trend_title: a trending topic title (from Trend Hunter)
    Returns: {"line": str}
    """
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""You write single-line philosophical thoughts for Facebook Stories
(a page called "Nexora Reflections"). Stories are viewed for a few seconds only.

Trending topic for loose inspiration (do not mention it literally): "{trend_title}"

Write ONE short line, max 12 words, that stands completely on its own —
no setup needed, no hashtags, no emojis. It should feel like a passing
thought worth pausing on. Avoid overused/common quotes.

Return ONLY valid JSON, no markdown, no preamble, in this exact shape:
{{"line": "..."}}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.9,
        max_tokens=150,
    )

    raw = response.choices[0].message.content.strip()
    raw = raw.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    print(json.dumps(generate_story_content("the pace of modern life"), indent=2))
