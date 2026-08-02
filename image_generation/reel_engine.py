import os
import random
import textwrap
from PIL import Image, ImageDraw, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import ImageClip, CompositeVideoClip, AudioFileClip, afx

# ---- Config ----
OUTPUT_DIR = "data/generated_reels"
WIDTH, HEIGHT = 1080, 1920
DURATION = 18  # seconds — enough room for 3 text beats

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

# timing for the 3 text beats (start, duration) within DURATION=18
BEAT_TIMING = [
    (0.5, 5.5),   # hook: 0.5s -> 6.0s
    (6.2, 5.6),   # line2: 6.2s -> 11.8s
    (12.0, 5.8),  # line3: 12.0s -> 17.8s
]


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


def _make_line_image(text: str, is_hook: bool, accent_rgb) -> Image.Image:
    img = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    font = ImageFont.truetype(HOOK_FONT_PATH if is_hook else BODY_FONT_PATH, 78 if is_hook else 60)
    color = (255, 255, 255, 255) if is_hook else (*accent_rgb, 255)
    wrapped = textwrap.fill(text, width=17 if is_hook else 20)

    draw.multiline_text((WIDTH // 2, HEIGHT // 2), wrapped, font=font,
                         fill=color, anchor="mm", align="center", spacing=16)
    return img


def _pick_music(mood: str = None):
    candidates = []
    if mood:
        mood_dir = os.path.join(MUSIC_DIR, mood)
        if os.path.isdir(mood_dir):
            candidates = [
                os.path.join(mood_dir, f) for f in os.listdir(mood_dir)
                if f.lower().endswith((".mp3", ".m4a", ".wav"))
            ]
    if not candidates and os.path.isdir(MUSIC_DIR):
        for root, _, files in os.walk(MUSIC_DIR):
            candidates.extend(
                os.path.join(root, f) for f in files
                if f.lower().endswith((".mp3", ".m4a", ".wav"))
            )
    return random.choice(candidates) if candidates else None


def create_reel(hook: str, line2: str, line3: str = "", filename: str = "daily_reel.mp4") -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)

    lines = [hook, line2, line3 or "Sit with that for a moment."]

    template_name = random.choice(list(TEMPLATES.keys()))
    accent_rgb = TEMPLATES[template_name]["accent"]

    bg_path = os.path.join(OUTPUT_DIR, "_bg_frame.png")
    _make_background(template_name).save(bg_path)

    bg_clip = (
        ImageClip(bg_path)
        .set_duration(DURATION)
        .resize(lambda t: 1 + 0.006 * t)
        .set_position(("center", "center"))
    )

    text_clips = []
    temp_files = []
    for i, (text, (start, dur)) in enumerate(zip(lines, BEAT_TIMING)):
        line_path = os.path.join(OUTPUT_DIR, f"_line_{i}.png")
        _make_line_image(text, is_hook=(i == 0), accent_rgb=accent_rgb).save(line_path)
        temp_files.append(line_path)

        clip = (
            ImageClip(line_path)
            .set_duration(dur)
            .set_start(start)
            .crossfadein(0.6)
            .crossfadeout(0.5)
        )
        text_clips.append(clip)

    video = CompositeVideoClip([bg_clip, *text_clips], size=(WIDTH, HEIGHT)).set_duration(DURATION)

    music_path = _pick_music()
    if music_path:
        raw_audio = AudioFileClip(music_path)
        audio = raw_audio.subclip(0, min(DURATION, raw_audio.duration))
        audio = audio.fx(afx.audio_fadein, 0.5).fx(afx.audio_fadeout, 1.2).volumex(0.6)
        video = video.set_audio(audio)

    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac", preset="medium")

    os.remove(bg_path)
    for f in temp_files:
        os.remove(f)
    return output_path


if __name__ == "__main__":
    path = create_reel(
        "The mind believes what it repeats",
        "Not what it is told once.",
        "Question the voice before you trust it.",
    )
    print(f"✅ Reel saved to: {path}")
