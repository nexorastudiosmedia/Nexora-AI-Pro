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
    total_frames = DURATION * 25

    # Pre-scale the image way up before zoompan, then scale back down.
    # zoompan applied directly at small resolutions is known to sometimes
    # produce a blank/black output — oversizing first avoids that.
    video_filter = (
        f"[0:v]scale=8000:-2,"
        f"zoompan=z='min(zoom+0.0008,1.15)':d={total_frames}:s=1080x1920:fps=25,"
        f"format=yuv420p[v]"
    )

    cmd = [ffmpeg, "-y", "-loop", "1", "-i", still_path]
    if music_path:
        cmd += ["-i", music_path]

    cmd += ["-filter_complex", video_filter, "-map", "[v]"]

    if music_path:
        fade_out_start = DURATION - 1
        cmd += [
            "-map", "1:a:0",
            "-c:a", "aac",
            "-af", f"afade=t=in:st=0:d=0.5,afade=t=out:st={fade_out_start}:d=1",
            "-shortest",
        ]

    cmd += ["-t", str(DURATION), "-c:v", "libx264", "-pix_fmt", "yuv420p", output_path]

    subprocess.run(cmd, check=True)

    os.remove(still_path)
    return output_path


if __name__ == "__main__":
    print(create_story_video("Some doors only open when you stop knocking."))
