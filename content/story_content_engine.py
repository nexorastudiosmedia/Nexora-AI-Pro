````python
"""
Story Content Engine
--------------------
Generates a short philosophical story line for
the Nexora Reflections Facebook Story pipeline.

IMPORTANT:
The caller in run_story_pipeline.py expects:

    content["line"]

Therefore this module returns:

    {
        "line": "..."
    }

Do not change the return key unless the caller is also changed.
"""

import os
import re

from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

MAX_LINE_WORDS = 70


# ============================================================
# API KEY
# ============================================================

def _get_groq_api_key() -> str:
    """
    Read the Groq API key from the environment.
    """

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


# ============================================================
# WORD LIMIT
# ============================================================

def _limit_words(
    text: str,
    maximum: int = MAX_LINE_WORDS,
) -> str:
    """
    Limit generated text to the maximum number of words.
    """

    text = str(text).strip()

    words = text.split()

    if len(words) <= maximum:
        return text

    return " ".join(words[:maximum]).strip()


# ============================================================
# CLEAN RESPONSE
# ============================================================

def _clean_line(text: str) -> str:
    """
    Clean common formatting produced by the model.
    """

    if not text:
        return ""

    text = str(text).strip()

    # Remove markdown code fences if present.
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

    # Remove common labels if the model added one.
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


# ============================================================
# GROQ GENERATION
# ============================================================

def _generate_line(
    client: Groq,
    trend_title: str,
) -> str:
    """
    Generate one short philosophical story line.

    The model is deliberately asked for plain text rather
    than JSON because the pipeline only needs one string:
    content["line"].
    """

    prompt = f"""
Create ONE original short philosophical Facebook story line.

Facebook page:
"Nexora Reflections"

Trending topic for loose inspiration:
"{trend_title}"

IMPORTANT:

Use the trending topic only as loose inspiration.

Do NOT report the news.

Do NOT mention the trending topic directly.

Do NOT mention specific companies, sports teams,
politicians, celebrities, or real-world events.

Transform the underlying idea into a universal
human lesson or reflection.

The line must be:

- Emotional
- Thoughtful
- Relatable
- Original
- Easy to understand
- Suitable for a US Facebook audience
- Suitable for a short vertical story video
- Maximum 70 words

Do not use hashtags.

Do not use a title.

Do not use labels.

Do not use quotation marks around the entire response.

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

    # --------------------------------------------------------
    # Validate response
    # --------------------------------------------------------

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

    line = _clean_line(
        content
    )

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


# ============================================================
# PUBLIC FUNCTION
# ============================================================

def generate_story_content(
    trend_title: str,
) -> dict:
    """
    Generate the story content expected by
    run_story_pipeline.py.

    IMPORTANT:
    The pipeline expects content["line"].

    Returns:
        {
            "line": str
        }
    """

    api_key = _get_groq_api_key()

    client = Groq(
        api_key=api_key
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

    # ========================================================
    # THIS IS THE CRITICAL CONTRACT
    #
    # run_story_pipeline.py does:
    #
    # content["line"]
    #
    # and then:
    #
    # create_story_video(content["line"])
    # ========================================================

    return {
        "line": line
    }


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    from dotenv import load_dotenv

    load_dotenv()

    result = generate_story_content(
        "the pace of modern life"
    )

    print("Generated story line:")
    print(result["line"])
````
