"""
Story Content Engine
--------------------
Generates short-form philosophical story content
for the Nexora Reflections Facebook page.
"""

import os
import json
from groq import Groq


GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def generate_story_content(trend_title: str) -> dict:
    """
    Generate a short philosophical Facebook story.

    Returns:
        {
            "title": str,
            "story": str,
            "caption": str
        }
    """

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
Create ONE original short philosophical Facebook story.

Facebook page:
"Nexora Reflections"

Trending topic for loose inspiration:
"{trend_title}"

Do not directly report the news.
Do not mention the trending topic literally.
Use it only as inspiration for a human lesson or reflection.

IMPORTANT:
Keep the entire story SHORT enough to fit comfortably in the response.
The story MUST be no more than 70 words.

Requirements:

TITLE:
- Short.
- Curiosity-driven.
- No hashtags.

STORY:
- Maximum 70 words.
- Emotional, thoughtful and relatable.
- Original wording.
- Easy to read on Facebook.
- No famous quotes.
- Do not invent specific facts about real people.

CAPTION:
- 2 short sentences.
- The second sentence must be an engagement question.
- Add 3 relevant hashtags at the end.

Return ONLY valid JSON.
Do not use markdown.
Do not use code fences.

The JSON must have exactly these fields:
title
story
caption
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional short-form Facebook writer. "
                    "Keep responses concise. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_tokens=300,
        include_reasoning=False,
    )

    message = response.choices[0].message
    raw = message.content

    if not raw:
        raise ValueError(
            "Groq returned an empty content response for story generation."
        )

    raw = raw.strip()

    if raw.startswith("```json"):
        raw = raw[7:]

    elif raw.startswith("```"):
        raw = raw[3:]

    if raw.endswith("```"):
        raw = raw[:-3]

    raw = raw.strip()

    try:
        data = json.loads(raw)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Groq returned incomplete or invalid JSON for story generation. "
            f"Response received: {raw[:500]}"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(
            "Groq returned JSON, but it was not a JSON object."
        )

    title = str(data.get("title", "")).strip()
    story = str(data.get("story", "")).strip()
    caption = str(data.get("caption", "")).strip()

    if not title:
        title = "The Lesson We Almost Miss"

    if not story:
        story = (
            "Sometimes we rush toward the next moment "
            "without noticing what the present is trying to teach us."
        )

    if not caption:
        caption = (
            "The quiet moments often teach us the most. "
            "What lesson have you learned recently? "
            "#philosophy #mindset #reflection"
        )

    return {
        "title": title,
        "story": story,
        "caption": caption,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    sample = generate_story_content(
        "the pace of modern life"
    )

    print(
        json.dumps(
            sample,
            indent=2,
            ensure_ascii=False
        )
    )
