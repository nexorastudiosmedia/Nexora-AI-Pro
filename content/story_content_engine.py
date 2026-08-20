"""
Story Content Engine
--------------------
Generates short-form philosophical story content
for the Nexora Reflections Facebook page.

Groq-powered generation with robust JSON handling,
validation, and retry support.
"""

import json
import os
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
MAX_RETRIES = 3


# ============================================================
# HELPERS
# ============================================================

def _get_groq_api_key() -> str:
    """Return the Groq API key or raise a clear error."""

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is missing. "
            "Add GROQ_API_KEY to GitHub Actions Secrets."
        )

    api_key = api_key.strip()

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is empty. "
            "Check the GitHub Actions secret value."
        )

    return api_key


def _clean_json_response(raw: str) -> str:
    """
    Clean common markdown/code-fence artifacts from
    an otherwise JSON response.
    """

    if not raw:
        return ""

    raw = raw.strip()

    # Remove markdown code fences.
    if raw.startswith("```json"):
        raw = raw[len("```json"):].strip()

    elif raw.startswith("```JSON"):
        raw = raw[len("```JSON"):].strip()

    elif raw.startswith("```"):
        raw = raw[len("```"):].strip()

    if raw.endswith("```"):
        raw = raw[:-3].strip()

    # Sometimes a model may place text before/after JSON.
    # Try to isolate the outermost JSON object.
    first_brace = raw.find("{")
    last_brace = raw.rfind("}")

    if first_brace != -1 and last_brace != -1:
        raw = raw[first_brace:last_brace + 1]

    return raw.strip()


def _limit_words(text: str, maximum: int) -> str:
    """Limit text to a maximum number of whitespace-separated words."""

    words = text.split()

    if len(words) <= maximum:
        return text.strip()

    return " ".join(words[:maximum]).strip()


def _validate_and_normalize(data: dict) -> dict:
    """
    Validate the generated object and normalize the
    title/story/caption fields.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Groq returned JSON, but it was not a JSON object."
        )

    title = str(data.get("title", "")).strip()
    story = str(data.get("story", "")).strip()
    caption = str(data.get("caption", "")).strip()

    # Safe defaults.
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

    # Enforce the story limit ourselves.
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
# MAIN GENERATOR
# ============================================================

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

    api_key = _get_groq_api_key()

    client = Groq(
        api_key=api_key,
    )

    prompt = f"""
Create ONE original short philosophical Facebook story.

Facebook page:
"Nexora Reflections"

Trending topic for loose inspiration:
"{trend_title}"

Do not directly report the news.

Do not mention the trending topic literally.

Use the topic only as loose inspiration for
a universal human lesson or reflection.

The final story must feel timeless and relatable.

IMPORTANT:
Keep the entire response concise.

STORY:
- Maximum 70 words.
- Emotional.
- Thoughtful.
- Relatable.
- Original wording.
- Easy to read on Facebook.
- No famous quotes.
- Do not invent specific facts about real people.
- Do not claim fictional events are real.

TITLE:
- Short.
- Curiosity-driven.
- No hashtags.

CAPTION:
- Exactly 2 short sentences before hashtags.
- The second sentence must be an engagement question.
- Then add exactly 3 relevant hashtags.

Return ONLY a JSON object.

The JSON must contain exactly these fields:

{{
  "title": "short title",
  "story": "maximum 70 word story",
  "caption": "two short sentences followed by three hashtags"
}}
"""

    last_error = None

    # ========================================================
    # RETRY LOOP
    # ========================================================

    for attempt in range(1, MAX_RETRIES + 1):

        try:

            response = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional short-form "
                            "Facebook writer. "
                            "Return only valid JSON. "
                            "Keep the output concise."
                        ),
                    },
                    {
                        "role": "user",
                        "content": prompt,
                    },
                ],
                temperature=0.7,
                max_completion_tokens=500,
                response_format={
                    "type": "json_object"
                },
                include_reasoning=False,
            )

            # ------------------------------------------------
            # Validate response structure
            # ------------------------------------------------

            if not response:
                raise ValueError(
                    "Groq returned no response object."
                )

            if not getattr(response, "choices", None):
                raise ValueError(
                    "Groq returned a response without choices."
                )

            choice = response.choices[0]

            if not getattr(choice, "message", None):
                raise ValueError(
                    "Groq returned a choice without a message."
                )

            message = choice.message

            raw = getattr(message, "content", None)

            # ------------------------------------------------
            # IMPORTANT:
            # GPT-OSS may expose reasoning separately.
            # We only want final content.
            # ------------------------------------------------

            if raw is None:
                raw = ""

            raw = str(raw).strip()

            # ------------------------------------------------
            # Empty response diagnostics
            # ------------------------------------------------

            if not raw:

                reasoning = getattr(
                    message,
                    "reasoning",
                    None,
                )

                finish_reason = getattr(
                    choice,
                    "finish_reason",
                    None,
                )

                usage = getattr(
                    response,
                    "usage",
                    None,
                )

                diagnostics = (
                    f"Groq returned empty final content. "
                    f"model={GROQ_MODEL}, "
                    f"attempt={attempt}, "
                    f"finish_reason={finish_reason}, "
                    f"reasoning_present={bool(reasoning)}, "
                    f"usage={usage}"
                )

                raise ValueError(diagnostics)

            # ------------------------------------------------
            # Clean JSON
            # ------------------------------------------------

            raw = _clean_json_response(raw)

            if not raw:
                raise ValueError(
                    "Groq returned empty content after JSON cleanup."
                )

            # ------------------------------------------------
            # Parse JSON
            # ------------------------------------------------

            try:

                data = json.loads(raw)

            except json.JSONDecodeError as exc:

                raise ValueError(
                    "Groq returned invalid JSON. "
                    f"Raw response: {raw[:1000]}"
                ) from exc

            # ------------------------------------------------
            # Validate and normalize
            # ------------------------------------------------

            result = _validate_and_normalize(data)

            return result

        except Exception as exc:

            last_error = exc

            # Do not immediately fail.
            # Retry transient/model-response issues.
            if attempt < MAX_RETRIES:

                time.sleep(
                    2 * attempt
                )

                continue

            # Final attempt failed.
            raise ValueError(
                "Groq story generation failed after "
                f"{MAX_RETRIES} attempts. "
                f"Model: {GROQ_MODEL}. "
                f"Last error: {last_error}"
            ) from last_error


# ============================================================
# LOCAL TEST
# ============================================================

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
            ensure_ascii=False,
        )
    )
