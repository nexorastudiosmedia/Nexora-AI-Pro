"""
Story Content Engine
--------------------
Generates short-form philosophical story content
for the Nexora Reflections Facebook page.

Groq generation with:
1. JSON Object Mode
2. Plain-text fallback
3. GPT-OSS low reasoning effort
4. Robust response validation
"""

import json
import os
import re
import time

from groq import Groq


# ============================================================
# CONFIGURATION
# ============================================================

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "openai/gpt-oss-120b",
)

MAX_STORY_WORDS = 70


# ============================================================
# API KEY
# ============================================================

def _get_groq_api_key() -> str:
    """
    Get GROQ_API_KEY from environment variables.
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

def _limit_words(text: str, maximum: int) -> str:
    """
    Limit text to the specified number of words.
    """

    text = str(text).strip()

    words = text.split()

    if len(words) <= maximum:
        return text

    return " ".join(words[:maximum]).strip()


# ============================================================
# JSON CLEANER
# ============================================================

def _clean_json(text: str) -> str:
    """
    Clean markdown fences and surrounding text from JSON.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove markdown code fences.
    text = re.sub(
        r"^```(?:json)?\s*",
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

    # Find JSON object if additional text exists.
    first = text.find("{")
    last = text.rfind("}")

    if first >= 0 and last > first:
        text = text[first:last + 1]

    return text.strip()


# ============================================================
# NORMALIZE GENERATED DATA
# ============================================================

def _normalize_story(data: dict) -> dict:
    """
    Validate and normalize generated story data.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Groq response was not a JSON object."
        )

    title = str(
        data.get("title", "")
    ).strip()

    story = str(
        data.get("story", "")
    ).strip()

    caption = str(
        data.get("caption", "")
    ).strip()

    # --------------------------------------------------------
    # Title fallback
    # --------------------------------------------------------

    if not title:
        title = "The Lesson We Almost Miss"

    # --------------------------------------------------------
    # Story fallback
    # --------------------------------------------------------

    if not story:
        story = (
            "Sometimes we rush toward the next moment "
            "without noticing what the present is trying "
            "to teach us."
        )

    # --------------------------------------------------------
    # Caption fallback
    # --------------------------------------------------------

    if not caption:
        caption = (
            "The quiet moments often teach us the most. "
            "What lesson have you learned recently? "
            "#philosophy #mindset #reflection"
        )

    # --------------------------------------------------------
    # Enforce maximum story length
    # --------------------------------------------------------

    story = _limit_words(
        story,
        MAX_STORY_WORDS,
    )

    return {
        "title": title,
        "story": story,
        "caption": caption,
    }


# ============================================================
# JSON GENERATION
# ============================================================

def _generate_json_story(
    client: Groq,
    prompt: str,
) -> dict:
    """
    Generate story using Groq JSON Object Mode.

    This is deliberately simpler than the previous
    strict JSON Schema request because the previous
    request was rejected by Groq with:

        json_validate_failed
        failed_generation: ''
    """

    response = client.chat.completions.create(
        model=GROQ_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a professional short-form "
                    "Facebook writer for Nexora Reflections. "
                    "Return ONLY one valid JSON object with "
                    "exactly these fields: title, story, caption."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],

        temperature=0.7,

        # Give GPT-OSS enough room for its internal reasoning
        # and final response.
        max_completion_tokens=1000,

        # Use simple JSON Object Mode instead of the
        # Structured Output schema that previously caused
        # Groq's json_validate_failed error.
        response_format={
            "type": "json_object",
        },

        # Explicitly request low reasoning effort.
        reasoning_effort="low",
    )

    if not response:
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

    message = getattr(
        choices[0],
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
            "Groq returned empty final content "
            "in JSON mode."
        )

    content = _clean_json(
        str(content)
    )

    if not content:
        raise ValueError(
            "Groq returned empty JSON content."
        )

    try:
        data = json.loads(content)

    except json.JSONDecodeError as exc:
        raise ValueError(
            "Groq returned invalid JSON. "
            f"Response: {content[:1000]}"
        ) from exc

    return _normalize_story(
        data
    )


# ============================================================
# PLAIN TEXT FALLBACK
# ============================================================

def _generate_plain_text_story(
    client: Groq,
    prompt: str,
) -> dict:
    """
    Fallback generator.

    This deliberately does NOT request JSON from Groq.

    If Groq's JSON generation endpoint rejects the request,
    this path asks for three clearly labelled sections and
    parses them locally.
    """

    fallback_prompt = f"""
Create one original short philosophical Facebook story.

Return exactly this format:

TITLE:
<short title>

STORY:
<maximum 70 words>

CAPTION:
<two short sentences followed by exactly 3 hashtags>

Do not add any other headings.
Do not add explanations.
Do not use markdown code fences.

Topic for loose inspiration:
{prompt}
"""

    response = client.chat.completions.create(
        model=GROQ_MODEL,

        messages=[
            {
                "role": "system",
                "content": (
                    "You are a concise professional "
                    "Facebook storyteller."
                ),
            },
            {
                "role": "user",
                "content": fallback_prompt,
            },
        ],

        temperature=0.7,

        max_completion_tokens=1000,

        reasoning_effort="low",
    )

    if not response:
        raise ValueError(
            "Groq plain-text fallback returned no response."
        )

    choices = getattr(
        response,
        "choices",
        None,
    )

    if not choices:
        raise ValueError(
            "Groq plain-text fallback returned no choices."
        )

    message = getattr(
        choices[0],
        "message",
        None,
    )

    if message is None:
        raise ValueError(
            "Groq plain-text fallback returned no message."
        )

    content = getattr(
        message,
        "content",
        None,
    )

    if not content:
        raise ValueError(
            "Groq plain-text fallback returned empty content."
        )

    content = str(content).strip()

    # --------------------------------------------------------
    # Parse TITLE
    # --------------------------------------------------------

    title_match = re.search(
        r"TITLE:\s*(.*?)(?=\n\s*STORY:)",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # --------------------------------------------------------
    # Parse STORY
    # --------------------------------------------------------

    story_match = re.search(
        r"STORY:\s*(.*?)(?=\n\s*CAPTION:)",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # --------------------------------------------------------
    # Parse CAPTION
    # --------------------------------------------------------

    caption_match = re.search(
        r"CAPTION:\s*(.*)$",
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )

    title = (
        title_match.group(1).strip()
        if title_match
        else ""
    )

    story = (
        story_match.group(1).strip()
        if story_match
        else ""
    )

    caption = (
        caption_match.group(1).strip()
        if caption_match
        else ""
    )

    # --------------------------------------------------------
    # Validate fallback result
    # --------------------------------------------------------

    if not title:
        title = "The Lesson We Almost Miss"

    if not story:
        raise ValueError(
            "Groq plain-text fallback did not contain "
            "a recognizable STORY section."
        )

    if not caption:
        caption = (
            "The quiet moments often teach us the most. "
            "What lesson have you learned recently? "
            "#philosophy #mindset #reflection"
        )

    story = _limit_words(
        story,
        MAX_STORY_WORDS,
    )

    return {
        "title": title,
        "story": story,
        "caption": caption,
    }


# ============================================================
# MAIN FUNCTION
# ============================================================

def generate_story_content(
    trend_title: str,
) -> dict:
    """
    Generate a short philosophical Facebook story.

    Returns:
        {
            "title": str,
            "story": str,
            "caption": str
        }
    """

    api_key = _get_groq_api_key()

    client = Groq(
        api_key=api_key,
    )

    # ========================================================
    # STORY PROMPT
    # ========================================================

    prompt = f"""
Create ONE original short philosophical Facebook story.

Facebook page:
"Nexora Reflections"

Trending topic for loose inspiration:
"{trend_title}"

IMPORTANT:

Use the trending topic only as loose inspiration.

Do NOT report the news.

Do NOT mention the trending topic directly.

Do NOT mention SpaceX, companies, products, politicians,
celebrities, or specific real-world events unless necessary.

Transform the underlying idea into a universal human lesson.

The story should feel timeless and relatable.

TITLE:
- Short.
- Curiosity-driven.
- Maximum 10 words.
- No hashtags.

STORY:
- Maximum 70 words.
- Emotional.
- Thoughtful.
- Relatable.
- Original wording.
- Easy to read on Facebook.
- No famous quotes.
- No copied text.
- Do not invent facts about real people.

CAPTION:
- Two short sentences.
- The second sentence must be an engagement question.
- Then exactly 3 relevant hashtags.

Return only:
title
story
caption
"""

    # ========================================================
    # PRIMARY ATTEMPT
    # ========================================================

    try:

        return _generate_json_story(
            client,
            prompt,
        )

    except Exception as json_error:

        # ----------------------------------------------------
        # IMPORTANT:
        # Do not blindly repeat the same failed request.
        #
        # The previous #35 run proved that repeating the
        # strict JSON schema request produces the same 400.
        # ----------------------------------------------------

        print(
            "Groq JSON generation failed. "
            "Switching to plain-text fallback."
        )

        print(
            f"JSON generation error: {json_error}"
        )

    # ========================================================
    # FALLBACK ATTEMPT
    # ========================================================

    try:

        return _generate_plain_text_story(
            client,
            prompt,
        )

    except Exception as fallback_error:

        raise ValueError(
            "Groq story generation failed in both "
            "JSON mode and plain-text fallback. "
            f"Model: {GROQ_MODEL}. "
            f"JSON error: {json_error}. "
            f"Fallback error: {fallback_error}"
        ) from fallback_error


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    from dotenv import load_dotenv

    load_dotenv()

    result = generate_story_content(
        "the pace of modern life"
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False,
        )
    )
