import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont

WIDTH, HEIGHT = 1080, 1920  # Story aspect ratio

OUTPUT_DIR = "data/generated_stories"
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
HOOK_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Bold.ttf")
BODY_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Regular.ttf")
BRAND_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Regular.ttf")

BRAND_TEXT = "Nexora Reflections"

TEMPLATES = {
    "midnight_navy": {"bg": (13, 27, 51), "accent": (198, 168, 92)},
    "deep_forest": {"bg": (16, 36, 29), "accent": (200, 184, 140)},
    "wine_burgundy": {"bg": (46, 15, 20), "accent": (214, 178, 122)},
    "charcoal_grey": {"bg": (30, 30, 32), "accent": (210, 210, 210)},
    "espresso_brown": {"bg": (35, 24, 18), "accent": (196, 160, 110)},
}


def _apply_grain(img: Image.Image, opacity=12) -> Image.Image:
    w, h = img.size
    noise = Image.new("L", (w, h))
    noise.putdata([random.randint(0, 255) for _ in range(w * h)])
    noise_rgb = Image.merge("RGB", (noise, noise, noise))
    return Image.blend(img.convert("RGB"), noise_rgb, opacity / 255)


def create_story_image(line: str, filename: str = "daily_story.png") -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)

    template_name = random.choice(list(TEMPLATES.keys()))
    t = TEMPLATES[template_name]

    img = Image.new("RGB", (WIDTH, HEIGHT), t["bg"])
    draw = ImageDraw.Draw(img)

    if template_name == "midnight_navy":
        draw.rectangle([40, 40, WIDTH - 40, HEIGHT - 40], outline=t["accent"], width=3)
    elif template_name == "deep_forest":
        draw.polygon([(0, 0), (180, 0), (0, 180)], fill=t["accent"])
    elif template_name == "wine_burgundy":
        draw.rectangle([0, 0, WIDTH, 30], fill=t["accent"])
    elif template_name == "charcoal_grey":
        vignette = Image.new("L", (WIDTH, HEIGHT), 0)
        vdraw = ImageDraw.Draw(vignette)
        vdraw.ellipse([-300, -300, WIDTH + 300, HEIGHT + 300], fill=255)
        dark = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        img = Image.composite(img, dark, vignette)
        draw = ImageDraw.Draw(img)  # img was replaced above — rebind draw or all text below is lost
    elif template_name == "espresso_brown":
        big_font = ImageFont.truetype(HOOK_FONT_PATH, 700)
        draw.text((60, HEIGHT // 2 - 350), "\u201C", font=big_font,
                   fill=tuple(min(c + 15, 255) for c in t["bg"]))

    line_font = ImageFont.truetype(HOOK_FONT_PATH, 84)
    wrapped = textwrap.fill(line, width=16)
    draw.multiline_text((WIDTH // 2, HEIGHT // 2), wrapped, font=line_font,
                         fill=(255, 255, 255), anchor="mm", align="center", spacing=18)

    brand_font = ImageFont.truetype(BRAND_FONT_PATH, 34)
    draw.text((WIDTH // 2, HEIGHT - 100), BRAND_TEXT, font=brand_font,
               fill=t["accent"], anchor="mm")

    react_font = ImageFont.truetype(BODY_FONT_PATH, 28)
    draw.text((WIDTH // 2, HEIGHT - 150), "React if this hit different",
               font=react_font, fill=t["accent"], anchor="mm")

    img = _apply_grain(img)
    img.save(output_path)
    return output_path


if __name__ == "__main__":
    print(create_story_image("Some doors only open when you stop knocking."))
