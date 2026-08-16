import os
import re
import math
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
        "layout": "framed",
        "bg_top": (20, 24, 38),
        "bg_bottom": (35, 30, 55),
        "text_color": (240, 240, 235),
        "subtext_color": (200, 200, 195),
        "accent_color": (200, 170, 120),  # gold
    },
    {
        "name": "deep_forest",
        "layout": "corner_accent",
        "bg_top": (10, 25, 20),
        "bg_bottom": (20, 45, 35),
        "text_color": (235, 240, 230),
        "subtext_color": (195, 205, 195),
        "accent_color": (190, 170, 100),  # muted gold
    },
    {
        "name": "wine_burgundy",
        "layout": "top_band",
        "bg_top": (35, 10, 18),
        "bg_bottom": (55, 20, 28),
        "text_color": (240, 235, 230),
        "subtext_color": (205, 190, 190),
        "accent_color": (210, 180, 120),
    },
    {
        "name": "charcoal_grey",
        "layout": "vignette",
        "bg_top": (25, 25, 28),
        "bg_bottom": (45, 45, 50),
        "text_color": (245, 245, 245),
        "subtext_color": (200, 200, 205),
        "accent_color": (170, 170, 175),  # silver instead of gold
    },
    {
        "name": "espresso_brown",
        "layout": "big_quote_mark",
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


def _blend(c1, c2, factor):
    """Blends two RGB colors — factor 0 = c1, factor 1 = c2. Used for subtle, non-flat shapes."""
    return tuple(int(c1[i] * (1 - factor) + c2[i] * factor) for i in range(3))


def _apply_grain(img, width, height, opacity=14):
    """Adds a subtle film-grain texture over the whole image — this is the
    single biggest visual cue that separates a 'template look' from a
    'premium/editorial look' on a flat gradient background."""
    import random as _r
    noise = Image.new("L", (width, height))
    noise.putdata([_r.randint(0, 255) for _ in range(width * height)])
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    img_arr = Image.blend(img, noise_rgb, opacity / 255)
    return img_arr


def _apply_vignette(img, width, height):
    """Darkens the corners/edges of the image for a moodier, less flat look."""
    small_w, small_h = max(1, width // 4), max(1, height // 4)
    cx, cy = small_w / 2, small_h / 2
    max_dist = math.hypot(cx, cy)
    mask = Image.new("L", (small_w, small_h))
    pixel_data = []
    for y in range(small_h):
        for x in range(small_w):
            dist = math.hypot(x - cx, y - cy) / max_dist
            val = int(min(255, max(0, (dist - 0.55) * 255 * 1.8)))
            pixel_data.append(val)
    mask.putdata(pixel_data)
    mask = mask.resize((width, height), Image.BICUBIC)
    dark_overlay = Image.new("RGB", (width, height), (0, 0, 0))
    img.paste(dark_overlay, (0, 0), mask)


def _apply_decoration(img, draw, template):
    """Draws a background design element behind the text, based on the template's layout."""
    layout = template.get("layout", "plain")
    width, height = img.size
    bg_top = template["bg_top"]
    bg_bottom = template["bg_bottom"]
    accent = template["accent_color"]

    if layout == "framed":
        inset = 55
        frame_color = _blend(bg_bottom, accent, 0.5)
        draw.rectangle([inset, inset, width - inset, height - inset], outline=frame_color, width=3)

    elif layout == "corner_accent":
        shape_color_1 = _blend(bg_top, accent, 0.35)
        draw.polygon([(0, 0), (260, 0), (0, 260)], fill=shape_color_1)
        shape_color_2 = _blend(bg_bottom, accent, 0.35)
        draw.polygon(
            [(width, height), (width - 260, height), (width, height - 260)],
            fill=shape_color_2,
        )

    elif layout == "top_band":
        band_color = _blend(bg_top, accent, 0.25)
        draw.rectangle([0, 0, width, 130], fill=band_color)
        draw.line([(0, 130), (width, 130)], fill=accent, width=2)

    elif layout == "vignette":
        _apply_vignette(img, width, height)

    elif layout == "big_quote_mark":
        mark_color = _blend(bg_top, bg_bottom, 0.5)
        mark_color = _blend(mark_color, accent, 0.18)
        try:
            mark_font = ImageFont.truetype(HOOK_FONT_PATH, 420)
            draw.text((width // 2, 30), "\u201C", font=mark_font, fill=mark_color, anchor="ma")
        except Exception:
            pass

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

    # Soft drop-shadow behind the hook text — small offset, low-contrast shadow
    # color, gives the text real depth instead of sitting flat on the gradient
    shadow_color = _blend(bg_bottom, (0, 0, 0), 0.6)
    draw.multiline_text(
        (width // 2 + 3, start_y + 4),
        wrapped_hook,
        font=hook_font,
        fill=shadow_color,
        spacing=16,
        align="center",
        anchor="ma",
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

    # Small CTA microcopy just above the brand line — nudges people to comment,
    # which is the single strongest signal for organic reach on Facebook.
    cta_font = ImageFont.truetype(BODY_FONT_PATH, 26)
    cta_options = [
        "Share your thoughts below",
        "Do you agree? Comment below",
        "Tag someone who needs this",
    ]
    draw.text(
        (width // 2, height - 155),
        random.choice(cta_options),
        font=cta_font,
        fill=subtext_color,
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

    img = _apply_grain(img, width, height)

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
