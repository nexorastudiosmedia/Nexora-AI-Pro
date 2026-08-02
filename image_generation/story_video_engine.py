import os
import random
from PIL import Image, ImageDraw, ImageFont

if not hasattr(Image, "ANTIALIAS"):
    Image.ANTIALIAS = Image.LANCZOS

from moviepy.editor import ImageClip

WIDTH, HEIGHT = 1080, 1920
DURATION = 8  # short — Stories are quick glances

OUTPUT_DIR = "data/generated_stories"
FONT_DIR = os.path.join(os.path.dirname(__file__), "fonts")
HOOK_FONT_PATH = os.path.join(FONT_DIR, "PlayfairDisplay-Bold.ttf")

# reuse the same still-image builder, then animate it with a gentle zoom
from image_generation.story_image_engine import create_story_image


def create_story_video(line: str, filename: str = "daily_story.mp4") -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)

    still_path = create_story_image(line, filename="_story_still.png")

    clip = (
        ImageClip(still_path)
        .set_duration(DURATION)
        .resize(lambda t: 1 + 0.01 * t)
        .set_position(("center", "center"))
    )
    clip.write_videofile(output_path, fps=24, codec="libx264", preset="medium")

    os.remove(still_path)
    return output_path


if __name__ == "__main__":
    print(create_story_video("Some doors only open when you stop knocking."))
