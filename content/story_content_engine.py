"""
Story Content Engine
--------------------
Generates short-form philosophical story content
for the Nexora Reflections Facebook Story pipeline.

The story pipeline expects:
    content["line"]

Therefore this module returns:
    {
        "line": "..."
    }
"""

import os
import re

from groq import Groq


GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

MAX_LINE_WORDS = 70


def _get_groq_api_key() -> str:
    """Get the Groq API key from the environment."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. "
            "Please check GitHub Actions Secrets."
        )

    api_key = api_key.strip()

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is empty. "
            "Please check GitHub Actions Secrets."
        )

    return api_key


def _limit_words(
    text: str,
    maximum: int = MAX_LINE_WORDS,
) -> str:
    """Limit text to the specified maximum number of words."""

    text = str(text).strip()

    words = text.split()

    if len(words) <= maximum:
        return text

    return " ".join(words[:maximum]).strip()


def _clean_line(text: str) -> str:
    """Clean common formatting from the model response."""

    if not text:
        return ""

    text = str(text).strip()

    text = re.sub(
        r"^```(?:text|txt)?\s*",
        "",
        text,
        flags=re.IGNORECASE,
    )

    text = re.sub(
        r"\s*```$",
        "",
        text,
    )

    text = text.strip()

    prefixes = [
        "LINE:",
        "Line:",
        "STORY:",
        "Story:",
        "TEXT:",
        "Text:",
    ]

    for prefix in prefixes:
        if text.startswith(prefix):
            text = text[len(prefix):].strip()
            break

    return text


def _generate_line(
    client: Groq,
    trend_title: str,
) -> str:
    """Generate one short philosophical story line."""

    prompt = f"""
Create ONE original short philosophical Facebook story.

Facebook page:
"Nexora Reflections"

Trending topic for loose inspiration:
"{trend_title}"

Use the trending topic only as loose inspiration.

Do NOT report the news.

Do NOT mention the trending topic directly.

Do NOT mention specific companies, sports teams,
politicians, celebrities, or real-world events.

Transform the underlying idea into a universal
human lesson or reflection.

Requirements:

- Maximum 70 words.
- Emotional.
- Thoughtful.
- Relatable.
- Original.
- Easy to understand.
- Suitable for a US Facebook audience.
- Suitable for a short vertical story video.
- No hashtags.
- No title.
- No labels.
- No famous quotes.
- No copied text.
- Do not invent facts about real people.

Return ONLY the story text.
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional short-form "
                    "philosophical storyteller. "
                    "Return only the requested story text. "
                    "Do not return JSON."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.7,
        max_completion_tokens=500,
        reasoning_effort="low",
    )

    if response is None:
        raise ValueError(
            "Groq returned no response."
        )

    choices = getattr(
        response,
        "choices",
        None,
    )

    if not choices:
        raise ValueError(
            "Groq returned no choices."
        )

    choice = choices[0]

    message = getattr(
        choice,
        "message",
        None,
    )

    if message is None:
        raise ValueError(
            "Groq returned no message."
        )

    content = getattr(
        message,
        "content",
        None,
    )

    if not content:
        raise ValueError(
            "Groq returned empty story content."
        )

    line = _clean_line(content)

    if not line:
        raise ValueError(
            "Groq returned empty story line "
            "after cleanup."
        )

    line = _limit_words(
        line,
        MAX_LINE_WORDS,
    )

    return line


def generate_story_content(
    trend_title: str,
) -> dict:
    """
    Generate story content expected by run_story_pipeline.py.

    The pipeline expects:
        content["line"]

    Therefore this function returns:
        {
            "line": str
        }
    """

    api_key = _get_groq_api_key()

    client = Groq(
        api_key=api_key,
    )

    try:
        line = _generate_line(
            client,
            trend_title,
        )

    except Exception as exc:
        raise ValueError(
            "Groq story line generation failed. "
            f"Model: {GROQ_MODEL}. "
            f"Error: {exc}"
        ) from exc

    return {
        "line": line,
    }


if __name__ == "__main__":
    from dotenv import load_dotenv

    load_dotenv()

    result = generate_story_content(
        "the pace of modern life"
    )

    print("Generated story line:")
    print(result["line"])
