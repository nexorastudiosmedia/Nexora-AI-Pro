"""
Story Content Engine
--------------------
Generates short-form philosophical story content
for the Nexora Reflections Facebook page.

Uses Groq GPT-OSS with strict Structured Outputs
for reliable JSON generation.
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
# JSON SCHEMA
# ============================================================

STORY_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {
            "type": "string"
        },
        "story": {
            "type": "string"
        },
        "caption": {
            "type": "string"
        }
    },
    "required": [
        "title",
        "story",
        "caption"
    ],
    "additionalProperties": False
}


# ============================================================
# HELPERS
# ============================================================

def _get_groq_api_key() -> str:
    """
    Get GROQ_API_KEY from environment variables.
    """

    api_key = os.getenv("GROQ_API_KEY")

    if api_key is None:
        raise ValueError(
            "GROQ_API_KEY environment variable is missing. "
            "Please check GitHub Actions Secrets."
        )

    api_key = api_key.strip()

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY environment variable is empty. "
            "Please check the GitHub Actions secret."
        )

    return api_key


def _limit_words(text: str, maximum: int) -> str:
    """
    Limit text to a maximum number of words.
    """

    text = str(text).strip()

    words = text.split()

    if len(words) <= maximum:
        return text

    return " ".join(words[:maximum]).strip()


def _normalize_story(data: dict) -> dict:
    """
    Validate and normalize the generated story object.
    """

    if not isinstance(data, dict):
        raise ValueError(
            "Groq returned JSON, but the result was not an object."
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
    # Fallback title
    # --------------------------------------------------------

    if not title:
        title = "The Lesson We Almost Miss"

    # --------------------------------------------------------
    # Fallback story
    # --------------------------------------------------------

    if not story:
        story = (
            "Sometimes we rush toward the next moment "
            "without noticing what the present is trying "
            "to teach us."
        )

    # --------------------------------------------------------
    # Fallback caption
    # --------------------------------------------------------

    if not caption:
        caption = (
            "The quiet moments often teach us the most. "
            "What lesson have you learned recently? "
            "#philosophy #mindset #reflection"
        )

    # --------------------------------------------------------
    # Enforce 70-word story limit
    # --------------------------------------------------------

    story = _limit_words(
        story,
        MAX_STORY_WORDS
    )

    return {
        "title": title,
        "story": story,
        "caption": caption
    }


# ============================================================
# MAIN STORY GENERATOR
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
        api_key=api_key
    )

    prompt = f"""
Create ONE original short philosophical Facebook story.

Facebook page:
Nexora Reflections

Trending topic for loose inspiration:
{trend_title}

IMPORTANT:
The trending topic is ONLY inspiration.

Do NOT report the news.

Do NOT mention the trending topic directly.

Do NOT mention SpaceX, companies, products, politicians,
celebrities, or specific real-world events unless absolutely
necessary.

Transform the general idea into a universal human lesson.

The final content should feel timeless, emotional,
thoughtful, relatable, and suitable for a US Facebook audience.

TITLE REQUIREMENTS:
- Short.
- Curiosity-driven.
- No hashtags.
- No quotation marks.
- Maximum 10 words.

STORY REQUIREMENTS:
- Maximum 70 words.
- Emotional.
- Thoughtful.
- Relatable.
- Original wording.
- Easy to read on Facebook.
- No famous quotes.
- No copied material.
- Do not invent specific facts about real people.
- Do not present fictional events as real news.

CAPTION REQUIREMENTS:
- Two short sentences.
- The second sentence MUST be an engagement question.
- After the two sentences, add exactly 3 relevant hashtags.
- Keep the caption concise.

Generate only the three requested fields.
Do not generate explanations.
Do not generate commentary.
"""


    # ========================================================
    # RETRY LOOP
    # ========================================================

    last_error = None

    for attempt in range(
        1,
        MAX_RETRIES + 1
    ):

        try:

            response = client.chat.completions.create(

                # ------------------------------------------------
                # Groq model
                # ------------------------------------------------

                model=GROQ_MODEL,

                # ------------------------------------------------
                # Messages
                # ------------------------------------------------

                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional short-form "
                            "Facebook writer for Nexora Reflections. "
                            "Generate concise philosophical stories. "
                            "Follow the requested output schema exactly."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],

                # ------------------------------------------------
                # Generation settings
                # ------------------------------------------------

                temperature=0.7,

                max_completion_tokens=500,

                # ------------------------------------------------
                # STRICT STRUCTURED OUTPUT
                #
                # GPT-OSS 120B supports strict JSON schema mode.
                # ------------------------------------------------

                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "nexora_reflection_story",
                        "strict": True,
                        "schema": STORY_JSON_SCHEMA
                    }
                },

                # ------------------------------------------------
                # Disable reasoning output.
                # ------------------------------------------------

                include_reasoning=False
            )


            # ====================================================
            # RESPONSE VALIDATION
            # ====================================================

            if response is None:
                raise ValueError(
                    "Groq returned no response object."
                )

            choices = getattr(
                response,
                "choices",
                None
            )

            if not choices:
                raise ValueError(
                    "Groq returned no choices."
                )

            choice = choices[0]

            message = getattr(
                choice,
                "message",
                None
            )

            if message is None:
                raise ValueError(
                    "Groq returned a choice without a message."
                )

            content = getattr(
                message,
                "content",
                None
            )

            if content is None:
                content = ""

            content = str(content).strip()


            # ====================================================
            # EMPTY CONTENT CHECK
            # ====================================================

            if not content:

                finish_reason = getattr(
                    choice,
                    "finish_reason",
                    None
                )

                reasoning = getattr(
                    message,
                    "reasoning",
                    None
                )

                raise ValueError(
                    "Groq returned empty final content. "
                    f"model={GROQ_MODEL}, "
                    f"attempt={attempt}, "
                    f"finish_reason={finish_reason}, "
                    f"reasoning_present={bool(reasoning)}"
                )


            # ====================================================
            # PARSE STRUCTURED JSON
            # ====================================================

            try:

                data = json.loads(
                    content
                )

            except json.JSONDecodeError as exc:

                raise ValueError(
                    "Groq returned content that could not "
                    f"be parsed as JSON: {content[:1000]}"
                ) from exc


            # ====================================================
            # NORMALIZE RESULT
            # ====================================================

            result = _normalize_story(
                data
            )


            # ====================================================
            # SUCCESS
            # ====================================================

            return result


        except Exception as exc:

            last_error = exc

            # ----------------------------------------------------
            # Retry
            # ----------------------------------------------------

            if attempt < MAX_RETRIES:

                time.sleep(
                    attempt * 2
                )

                continue

            # ----------------------------------------------------
            # Final failure
            # ----------------------------------------------------

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

    result = generate_story_content(
        "the pace of modern life"
    )

    print(
        json.dumps(
            result,
            indent=2,
            ensure_ascii=False
        )
    )
