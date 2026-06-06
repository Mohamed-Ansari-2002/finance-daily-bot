from moviepy.editor import VideoFileClip, AudioFileClip
from pathlib import Path

OUTPUT_DIR = Path("output")

# Check audio file
print("=== AUDIO CHECK ===")
try:
    audio = AudioFileClip(str(OUTPUT_DIR / "voiceover.mp3"))
    print(f"Duration  : {audio.duration:.1f} seconds")
    print(f"FPS       : {audio.fps}")
    print(f"Status    : OK")
    audio.close()
except Exception as e:
    print(f"ERROR: {e}")

print()

# Check each video clip
print("=== VIDEO CLIPS CHECK ===")
for i in range(4):
    clip_path = OUTPUT_DIR / f"clip_{i}.mp4"
    if not clip_path.exists():
        print(f"clip_{i}.mp4 : FILE NOT FOUND")
        continue
    try:
        clip = VideoFileClip(str(clip_path))
        print(f"clip_{i}.mp4 :")
        print(f"  Duration : {clip.duration:.1f}s")
        print(f"  Size     : {clip.size}")
        print(f"  FPS      : {clip.fps}")
        print(f"  Audio    : {'Yes' if clip.audio else 'No'}")
        clip.close()
    except Exception as e:
        print(f"clip_{i}.mp4 : ERROR — {e}")

print()

# Check final video
print("=== FINAL VIDEO CHECK ===")
try:
    final = VideoFileClip(str(OUTPUT_DIR / "final_video.mp4"))
    print(f"Duration  : {final.duration:.1f} seconds")
    print(f"Size      : {final.size}")
    print(f"FPS       : {final.fps}")
    print(f"Has audio : {'Yes' if final.audio else 'No'}")
    final.close()
except Exception as e:
    print(f"ERROR: {e}")