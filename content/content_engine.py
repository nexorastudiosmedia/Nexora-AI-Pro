"""
Content Engine — turns a raw trending topic into a ready-to-publish
Facebook post for the "Philosophy / Deep Thoughts" page.

Uses Groq's free chat completions API (OpenAI-compatible HTTP endpoint,
no SDK dependency required — just httpx). Get a free API key at
https://console.groq.com and put it in your .env as GROQ_API_KEY.
"""

from __future__ import annotations

import json
from dataclasses import dataclass

import httpx

from content.settings import ContentEngineSettings, get_content_engine_settings

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

SYSTEM_PROMPT = """You are the ghostwriter behind a viral Facebook page called \
"Nexora AI" in the Philosophy / Deep Thoughts niche, targeting a US audience.

Given a raw trending news headline (which may be about tech, politics, sports, \
entertainment, anything), your job is to reframe it into a short, thought-\
provoking philosophical Facebook post. Do NOT summarize the news itself or \
take a political side — use the headline only as a spark for a universal \
question about life, human nature, technology, meaning, ethics, or change.

Always respond with ONLY valid JSON, no markdown fences, in this exact shape:
{
  "hook": "one short punchy opening line, 8-12 words",
  "caption": "the main post body, 3-5 sentences, reflective and relatable, \
plain conversational English",
  "cta": "one short question inviting comments, e.g. 'What do you think?'",
  "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]
}
"""


@dataclass
class GeneratedPost:
    hook: str
    caption: str
    cta: str
    hashtags: list[str]
    source_title: str
    source_url: str | None

    def as_facebook_text(self) -> str:
        """Assemble the final text block ready to paste into Facebook."""
        tags = " ".join(self.hashtags)
        return f"{self.hook}\n\n{self.caption}\n\n{self.cta}\n\n{tags}"


class ContentEngine:
    """Generates philosophy-angle Facebook posts from raw trending topics."""

    def __init__(self, settings: ContentEngineSettings | None = None) -> None:
        self._settings = settings or get_content_engine_settings()
        if not self._settings.groq_api_key:
            raise ValueError(
                "GROQ_API_KEY is not set. Add it to your .env file. "
                "Get a free key at https://console.groq.com"
            )

    async def generate(self, topic_title: str, topic_url: str | None = None) -> GeneratedPost:
        payload = {
            "model": self._settings.groq_model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Trending headline: {topic_title}"},
            ],
            "temperature": 0.8,
            "response_format": {"type": "json_object"},
        }
        headers = {
            "Authorization": f"Bearer {self._settings.groq_api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(GROQ_CHAT_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        content = data["choices"][0]["message"]["content"]
        parsed = json.loads(content)

        return GeneratedPost(
            hook=parsed["hook"],
            caption=parsed["caption"],
            cta=parsed["cta"],
            hashtags=parsed["hashtags"],
            source_title=topic_title,
            source_url=topic_url,
        )
