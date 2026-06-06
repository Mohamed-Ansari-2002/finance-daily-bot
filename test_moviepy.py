from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips

# Load one clip and check it
clip = VideoFileClip("output/clip_0.mp4")
print("Video duration :", clip.duration, "seconds")
print("Video size     :", clip.size)
print("Video fps      :", clip.fps)

clip.close()
print("\nMoviePy is working correctly.")