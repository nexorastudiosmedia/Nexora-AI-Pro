import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, CompositeVideoClip, AudioFileClip, afx

# ---- Config (mirrors image_engine.py conventions) ----
OUTPUT_DIR = "data/generated_reels"
WIDTH, HEIGHT = 1080, 1920  # vertical, correct aspect for Reels
DURATION = 16  # seconds

FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
HOOK_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Bold.ttf")
BODY_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Regular.ttf")
BRAND_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Regular.ttf")

BRAND_TEXT = "Nexora Reflections"
MUSIC_DIR = "assets/music"

TEMPLATES = {
    "midnight_navy": {"bg": (13, 27, 51), "accent": (198, 168, 92)},
    "deep_forest": {"bg": (16, 36, 29), "accent": (200, 184, 140)},
    "wine_burgundy": {"bg": (46, 15, 20), "accent": (214, 178, 122)},
    "charcoal_grey": {"bg": (30, 30, 32), "accent": (210, 210, 210)},
    "espresso_brown": {"bg": (35, 24, 18), "accent": (196, 160, 110)},
}


def _make_background(template_name: str) -> Image.Image:
    t = TEMPLATES[template_name]
    img = Image.new("RGB", (WIDTH, HEIGHT), t["bg"])
    draw = ImageDraw.Draw(img)

    if template_name == "midnight_navy":
        draw.rectangle([40, 40, WIDTH - 40, HEIGHT - 40], outline=t["accent"], width=3)
    elif template_name == "deep_forest":
        draw.polygon([(0, 0), (180, 0), (0, 180)], fill=t["accent"])
        draw.polygon([(WIDTH, HEIGHT), (WIDTH - 180, HEIGHT), (WIDTH, HEIGHT - 180)], fill=t["accent"])
    elif template_name == "wine_burgundy":
        draw.rectangle([0, 0, WIDTH, 30], fill=t["accent"])
    elif template_name == "charcoal_grey":
        vignette = Image.new("L", (WIDTH, HEIGHT), 0)
        vdraw = ImageDraw.Draw(vignette)
        vdraw.ellipse([-300, -300, WIDTH + 300, HEIGHT + 300], fill=255)
        dark = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        img = Image.composite(img, dark, vignette)
    elif template_name == "espresso_brown":
        big_font = ImageFont.truetype(HOOK_FONT_PATH, 700)
        draw.text((60, HEIGHT // 2 - 350), "\u201C", font=big_font,
                   fill=tuple(min(c + 15, 255) for c in t["bg"]))

    brand_font = ImageFont.truetype(BRAND_FONT_PATH, 34)
    draw.text((WIDTH // 2, HEIGHT - 90), BRAND_TEXT, font=brand_font,
               fill=t["accent"], anchor="mm")
    return img


def _make_text_overlay(hook: str, line2: str, accent_rgb) -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    hook_font = ImageFont.truetype(HOOK_FONT_PATH, 76)
    line2_font = ImageFont.truetype(BODY_FONT_PATH, 48)

    wrapped_hook = textwrap.fill(hook, width=18)
    wrapped_line2 = textwrap.fill(line2, width=24) if line2 else ""

    draw.multiline_text((WIDTH // 2, HEIGHT // 2 - 60), wrapped_hook, font=hook_font,
                         fill=(255, 255, 255, 255), anchor="mm", align="center", spacing=14)
    if wrapped_line2:
        draw.multiline_text((WIDTH // 2, HEIGHT // 2 + 160), wrapped_line2, font=line2_font,
                             fill=(*accent_rgb, 255), anchor="mm", align="center", spacing=10)
    return img


def _pick_music():
    if not os.path.isdir(MUSIC_DIR):
        return None
    tracks = [f for f in os.listdir(MUSIC_DIR) if f.lower().endswith((".mp3", ".m4a", ".wav"))]
    return os.path.join(MUSIC_DIR, random.choice(tracks)) if tracks else None


def create_reel(hook: str, line2: str, filename: str = "daily_reel.mp4") -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)

    template_name = random.choice(list(TEMPLATES.keys()))
    accent_rgb = TEMPLATES[template_name]["accent"]

    bg_path = os.path.join(OUTPUT_DIR, "_bg_frame.png")
    text_path = os.path.join(OUTPUT_DIR, "_text_frame.png")
    _make_background(template_name).save(bg_path)
    _make_text_overlay(hook, line2, accent_rgb).save(text_path)

    bg_clip = (
        ImageClip(bg_path)
        .set_duration(DURATION)
        .resize(lambda t: 1 + 0.008 * t)
        .set_position(("center", "center"))
    )
    text_clip = (
        ImageClip(text_path)
        .set_duration(DURATION - 0.6)
        .set_start(0.6)
        .crossfadein(0.8)
        .crossfadeout(0.6)
    )
    video = CompositeVideoClip([bg_clip, text_clip], size=(WIDTH, HEIGHT)).set_duration(DURATION)

    music_path = _pick_music()
    if music_path:
        raw_audio = AudioFileClip(music_path)
        audio = raw_audio.subclip(0, min(DURATION, raw_audio.duration))
        audio = audio.fx(afx.audio_fadein, 0.5).fx(afx.audio_fadeout, 1.2).volumex(0.6)
        video = video.set_audio(audio)

    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", preset="medium")

    os.remove(bg_path)
    os.remove(text_path)
    return output_path


if __name__ == "__main__":
    path = create_reel("The mind believes what it repeats", "Not what it is told once.")
    print(f"✅ Reel saved to: {path}")
