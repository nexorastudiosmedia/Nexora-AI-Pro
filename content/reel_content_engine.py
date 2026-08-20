"""
Reel Content Engine
--------------------
Generates short, punchy philosophy content specifically for Reels.
"""

import os
import json
from groq import Groq


GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def generate_reel_content(trend_title: str) -> dict:
    """
    Generate a short philosophical Reel script.

    Returns:
        {
            "hook": str,
            "line2": str,
            "line3": str,
            "caption": str
        }
    """

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
Create ONE short philosophical Facebook Reel script for a page called
"Nexora Reflections".

Trending topic for loose inspiration:
"{trend_title}"

Do NOT mention the trending topic directly.

The Reel is approximately 18 seconds long.

Create four pieces of content:

1. hook
Maximum 8 words.
It must create curiosity, make a bold claim, or directly address "you".
Do not use a generic proverb.
No hashtags.
No emojis.

2. line2
Maximum 12 words.
Develop the idea introduced by the hook.

3. line3
Maximum 12 words.
Finish with a reflection, insight, or gentle challenge.

4. caption
Write 2 or 3 natural sentences.
The final sentence must encourage engagement with a question or prompt.
Add 3 to 5 relevant hashtags at the end.

The writing must feel original, modern, thoughtful and suitable for short-form
Facebook video content.

Do not use famous quotes.
Do not mention these instructions.

Return the result as JSON with exactly these four fields:
hook
line2
line3
caption
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional short-form social media writer. "
                    "Generate concise philosophical Reel content."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_tokens=500,
        include_reasoning=False,
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "reel_content",
                "strict": True,
                "schema": {
                    "type": "object",
                    "properties": {
                        "hook": {
                            "type": "string"
                        },
                        "line2": {
                            "type": "string"
                        },
                        "line3": {
                            "type": "string"
                        },
                        "caption": {
                            "type": "string"
                        }
                    },
                    "required": [
                        "hook",
                        "line2",
                        "line3",
                        "caption"
                    ],
                    "additionalProperties": False
                }
            }
        },
    )

    message = response.choices[0].message

    raw = message.content

    if not raw:
        raise ValueError(
            "Groq returned an empty content response. "
            f"Reasoning: {getattr(message, 'reasoning', None)}"
        )

    raw = raw.strip()

    if raw.startswith("```json"):
        raw = raw[7:]

    if raw.startswith("```"):
        raw = raw[3:]

    if raw.endswith("```"):
        raw = raw[:-3]

    raw = raw.strip()

    data = json.loads(raw)

    data.setdefault(
        "hook",
        "Maybe you are thinking about this wrong."
    )

    data.setdefault(
        "line2",
        "There is more beneath the surface."
    )

    data.setdefault(
        "line3",
        "Sit with that for a moment."
    )

    data.setdefault(
        "caption",
        (
            "Sometimes the obvious answer hides a deeper truth. "
            "What do you think? "
            "#philosophy #mindset #reflection"
        )
    )

    return data


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    sample = generate_reel_content(
        "the pace of modern life"
    )

    print(json.dumps(sample, indent=2, ensure_ascii=False))
