import os
import random
import subprocess
import imageio_ffmpeg

from image_generation.story_image_engine import create_story_image

OUTPUT_DIR = "data/generated_stories"
DURATION = 8  # seconds
MUSIC_DIR = "assets/music"


def _pick_any_music():
    """Picks any track from any mood folder under assets/music/."""
    if not os.path.isdir(MUSIC_DIR):
        return None
    tracks = []
    for root, _, files in os.walk(MUSIC_DIR):
        tracks.extend(
            os.path.join(root, f) for f in files
            if f.lower().endswith((".mp3", ".m4a", ".wav"))
        )
    return random.choice(tracks) if tracks else None


def create_story_video(line: str, filename: str = "daily_story.mp4") -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_path = os.path.join(OUTPUT_DIR, filename)
    still_path = create_story_image(line, filename="_story_still.png")

    ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
    music_path = _pick_any_music()

    # slow zoom, done natively by ffmpeg (avoids moviepy's buggy per-frame resize)
    zoom_filter = f"zoompan=z='min(zoom+0.0008,1.15)':d={DURATION * 25}:s=1080x1920:fps=25"

    cmd = [ffmpeg, "-y", "-loop", "1", "-i", still_path]
    if music_path:
        cmd += ["-i", music_path]

    cmd += ["-t", str(DURATION), "-vf", zoom_filter, "-pix_fmt", "yuv420p", "-c:v", "libx264"]

    if music_path:
        fade_out_start = DURATION - 1
        cmd += [
            "-c:a", "aac", "-shortest",
            "-af", f"afade=t=in:st=0:d=0.5,afade=t=out:st={fade_out_start}:d=1",
        ]
    else:
        cmd += ["-an"]

    cmd += [output_path]

    subprocess.run(cmd, check=True)

    os.remove(still_path)
    return output_path


if __name__ == "__main__":
    print(create_story_video("Some doors only open when you stop knocking."))
