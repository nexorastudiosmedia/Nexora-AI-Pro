"""
Story Content Engine
--------------------
Generates short-form story content for the Nexora Reflections Facebook page.
"""

import os
import json
from groq import Groq


GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")


def generate_story_content(trend_title: str) -> dict:
    """
    Generate a fresh short story inspired by a trending topic.

    Returns:
        {
            "title": str,
            "story": str,
            "caption": str
        }
    """

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
Create ONE original short-form philosophical story for a Facebook page
called "Nexora Reflections".

Use this trending topic only as loose inspiration:

"{trend_title}"

Do NOT simply report the news.
Do NOT mention the trending topic directly unless it naturally fits.
Turn the idea into an interesting human story, observation, or life lesson.

Requirements:

- title: short and curiosity-driven.
- story: approximately 100-150 words.
- Make it emotional, thoughtful, relatable and easy to read.
- Use original wording.
- Do not use famous quotes.
- Do not invent specific facts about real people.
- caption: 2-3 sentences suitable for Facebook.
- The caption should end with an engagement question.
- Add 3-5 relevant hashtags at the end.

Return ONLY a JSON object with exactly these fields:

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
                    "You are a professional Facebook story writer. "
                    "Create original, engaging philosophical stories. "
                    "Return only valid JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_tokens=700,
        include_reasoning=False,
    )

    message = response.choices[0].message

    raw = message.content

    if not raw:
        raise ValueError(
            "Groq returned an empty content response for story generation."
        )

    raw = raw.strip()

    # Remove markdown code fences if the model adds them.
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
            f"Groq returned invalid JSON for story generation: {raw[:500]}"
        ) from exc

    # Safety fallbacks
    data.setdefault(
        "title",
        "The Thought We Almost Missed"
    )

    data.setdefault(
        "story",
        (
            "Sometimes life changes quietly before we notice it. "
            "We spend so much time chasing what comes next that we forget "
            "to understand what is already happening around us. "
            "A small moment can reveal something much bigger about ourselves. "
            "The lesson is not always in what happens, but in how we choose "
            "to see it."
        )
    )

    data.setdefault(
        "caption",
        (
            "Sometimes the smallest moments carry the biggest lessons. "
            "What would you have taken from this story? "
            "#philosophy #mindset #life #reflection"
        )
    )

    return data


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
