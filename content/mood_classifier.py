"""
Classifies the emotional mood of a reel script so the right background
music folder can be picked. Keeps this separate from content generation
so it can be re-used or swapped independently.
"""
import os
from groq import Groq

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
VALID_MOODS = ["calm", "hopeful", "melancholic", "intense"]


def classify_mood(hook: str, line2: str, line3: str) -> str:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""Read this short philosophical reel script and classify its overall emotional mood.

Hook: {hook}
Line 2: {line2}
Line 3: {line3}

Pick EXACTLY ONE mood from this list: calm, hopeful, melancholic, intense
- calm: peaceful, meditative, slow-breathing feeling
- hopeful: uplifting, encouraging, forward-looking
- melancholic: bittersweet, wistful, reflective sadness
- intense: urgent, challenging, thought-provoking tension

Return ONLY the single word, nothing else, no punctuation."""

    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=10,
    )
    mood = response.choices[0].message.content.strip().lower()
    return mood if mood in VALID_MOODS else "calm"
