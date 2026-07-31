import os
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont

# ---- Config ----
OUTPUT_DIR = "data/generated_images"
WINDOWS_FONTS_DIR = r"C:\Windows\Fonts"

IMAGE_SIZE = (1080, 1350)  # portrait, good for FB engagement
BRAND_TEXT = "Nexora Reflections"

# ---- Style templates (rotated randomly per post) ----
import random

TEMPLATES = [
    {
        "name": "midnight_navy",
        "bg_top": (20, 24, 38),
        "bg_bottom": (35, 30, 55),
        "text_color": (240, 240, 235),
        "subtext_color": (200, 200, 195),
        "accent_color": (200, 170, 120),  # gold
    },
    {
        "name": "deep_forest",
        "bg_top": (10, 25, 20),
        "bg_bottom": (20, 45, 35),
        "text_color": (235, 240, 230),
        "subtext_color": (195, 205, 195),
        "accent_color": (190, 170, 100),  # muted gold
    },
    {
        "name": "wine_burgundy",
        "bg_top": (35, 10, 18),
        "bg_bottom": (55, 20, 28),
        "text_color": (240, 235, 230),
        "subtext_color": (205, 190, 190),
        "accent_color": (210, 180, 120),
    },
    {
        "name": "charcoal_grey",
        "bg_top": (25, 25, 28),
        "bg_bottom": (45, 45, 50),
        "text_color": (245, 245, 245),
        "subtext_color": (200, 200, 205),
        "accent_color": (170, 170, 175),  # silver instead of gold
    },
    {
        "name": "espresso_brown",
        "bg_top": (30, 20, 15),
        "bg_bottom": (50, 35, 25),
        "text_color": (240, 232, 220),
        "subtext_color": (205, 195, 185),
        "accent_color": (200, 150, 90),
    },
]


def pick_template():
    """Randomly picks one of the visual style templates for a post."""
    return random.choice(TEMPLATES)

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
HOOK_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Bold.ttf")
BODY_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Regular.ttf")
BRAND_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Regular.ttf")


def _make_gradient_background(size, top_color, bottom_color):
    width, height = size
    base = Image.new("RGB", size, top_color)
    bottom = Image.new("RGB", size, bottom_color)
    mask = Image.new("L", size)
    mask_data = []
    for y in range(height):
        mask_data.extend([int(255 * (y / height))] * width)
    mask.putdata(mask_data)
    base.paste(bottom, (0, 0), mask)
    return base


def _split_hook_and_body(text: str):
    """Splits text into the first sentence (hook) and the rest (body)."""
    match = re.search(r"[.?!]", text)
    if not match:
        return text.strip(), ""
    split_at = match.end()
    hook = text[:split_at].strip()
    body = text[split_at:].strip()
    return hook, body


def _wrap_to_fit(draw, text, font, max_width):
    avg_char_width = font.getlength("x") or 1
    wrap_width = max(10, int(max_width / avg_char_width))
    return textwrap.fill(text, width=wrap_width)


def create_quote_card(quote_text: str, filename: str, template: dict = None) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # Pick a random visual style unless one was explicitly passed in
    template = template or pick_template()
    bg_top = template["bg_top"]
    bg_bottom = template["bg_bottom"]
    text_color = template["text_color"]
    subtext_color = template["subtext_color"]
    accent_color = template["accent_color"]
    print(f"🎨 Using template: {template['name']}")

    img = _make_gradient_background(IMAGE_SIZE, bg_top, bg_bottom)
    draw = ImageDraw.Draw(img)

    width, height = IMAGE_SIZE
    margin = 110
    max_text_width = width - (margin * 2)

    clean_text = quote_text.split("#")[0].strip()
    hook, body = _split_hook_and_body(clean_text)

    hook_font = ImageFont.truetype(HOOK_FONT_PATH, 66)
    body_font = ImageFont.truetype(BODY_FONT_PATH, 42)

    wrapped_hook = _wrap_to_fit(draw, hook, hook_font, max_text_width)
    wrapped_body = _wrap_to_fit(draw, body, body_font, max_text_width) if body else ""

    hook_bbox = draw.multiline_textbbox((0, 0), wrapped_hook, font=hook_font, spacing=16)
    hook_height = hook_bbox[3] - hook_bbox[1]

    body_height = 0
    if wrapped_body:
        body_bbox = draw.multiline_textbbox((0, 0), wrapped_body, font=body_font, spacing=14)
        body_height = body_bbox[3] - body_bbox[1]

    gap_between = 45 if wrapped_body else 0
    total_height = hook_height + gap_between + body_height

    # Vertically center the whole text block, nudged slightly upward
    start_y = (height - total_height) // 2 - 60

    # Accent line above the hook
    accent_y = start_y - 60
    draw.line(
        [(width // 2 - 60, accent_y), (width // 2 + 60, accent_y)],
        fill=accent_color,
        width=3,
    )

    draw.multiline_text(
        (width // 2, start_y),
        wrapped_hook,
        font=hook_font,
        fill=text_color,
        spacing=16,
        align="center",
        anchor="ma",
    )

    if wrapped_body:
        body_y = start_y + hook_height + gap_between
        draw.multiline_text(
            (width // 2, body_y),
            wrapped_body,
            font=body_font,
            fill=subtext_color,
            spacing=14,
            align="center",
            anchor="ma",
        )

    # Branding at the bottom
    brand_font = ImageFont.truetype(BRAND_FONT_PATH, 32)
    draw.text(
        (width // 2, height - 110),
        BRAND_TEXT,
        font=brand_font,
        fill=accent_color,
        anchor="ma",
    )

    output_path = os.path.join(OUTPUT_DIR, filename)
    img.save(output_path, quality=95)
    return output_path


if __name__ == "__main__":
    test_quote = (
        "Life's fleeting, what's your timeout? Jake Knapp, the inventor of "
        "the Time Box method, reminds us that our time is limited. How we "
        "choose to spend it defines who we become."
    )
    path = create_quote_card(test_quote, "test_quote_card.png")
    print(f"✅ Quote card saved to: {path}")
