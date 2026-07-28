import os
import re
import textwrap
from PIL import Image, ImageDraw, ImageFont

# ---- Config ----
OUTPUT_DIR = "data/generated_images"
WINDOWS_FONTS_DIR = r"C:\Windows\Fonts"

IMAGE_SIZE = (1080, 1350)  # portrait, good for FB engagement
BG_COLOR_TOP = (20, 24, 38)      # dark navy
BG_COLOR_BOTTOM = (35, 30, 55)   # muted purple-navy
TEXT_COLOR = (240, 240, 235)
SUBTEXT_COLOR = (200, 200, 195)  # slightly dimmer for the explanation part
ACCENT_COLOR = (200, 170, 120)   # subtle gold accent
BRAND_TEXT = "Nexora Media"

HOOK_FONT_PATH = os.path.join(WINDOWS_FONTS_DIR, "georgiab.ttf")   # bold — for the hook line
BODY_FONT_PATH = os.path.join(WINDOWS_FONTS_DIR, "georgia.ttf")    # regular — for the explanation
BRAND_FONT_PATH = os.path.join(WINDOWS_FONTS_DIR, "georgia.ttf")


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


def create_quote_card(quote_text: str, filename: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    img = _make_gradient_background(IMAGE_SIZE, BG_COLOR_TOP, BG_COLOR_BOTTOM)
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
        fill=ACCENT_COLOR,
        width=3,
    )

    draw.multiline_text(
        (width // 2, start_y),
        wrapped_hook,
        font=hook_font,
        fill=TEXT_COLOR,
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
            fill=SUBTEXT_COLOR,
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
        fill=ACCENT_COLOR,
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