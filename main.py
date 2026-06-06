from PIL import Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS

import shutil
import os
import re
import datetime
import requests
import feedparser
from pathlib import Path
from groq import Groq
from gtts import gTTS
from moviepy.editor import (
    VideoFileClip,
    AudioFileClip,
    concatenate_videoclips,
    ColorClip
)
from PIL import Image, ImageDraw, ImageFont

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
import json


GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

# Create output folder to store all generated files
OUTPUT_DIR = Path("output")
OUTPUT_DIR.mkdir(exist_ok=True)

def fetch_finance_news():
    """
    Fetches top finance news from Google News RSS.
    Uses 3 different finance-related searches to get variety.
    Returns a list of up to 5 news items with title and summary.
    """

    # 3 different finance RSS feeds for variety
    rss_urls = [
        "https://news.google.com/rss/search?q=stock+market+india&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=nifty+sensex+today&hl=en-IN&gl=IN&ceid=IN:en",
        "https://news.google.com/rss/search?q=india+economy+finance&hl=en-IN&gl=IN&ceid=IN:en",
    ]

    headlines = []

    for url in rss_urls:
        feed = feedparser.parse(url)

        for entry in feed.entries[:2]:  # take 2 from each source
            title   = entry.title
            summary = entry.get("summary", "")

            # Clean up the summary — Google News sometimes adds HTML tags
            # This removes them simply
            import re
            summary = re.sub(r'<[^>]+>', '', summary)
            summary = summary[:300]  # keep only first 300 characters

            headlines.append({
                "title"  : title,
                "summary": summary,
                "link"   : entry.link
            })

        if len(headlines) >= 5:
            break  # stop once we have 5 stories

    return headlines[:5]

def generate_script(headlines):
    """
    Takes the 5 finance news headlines fetched from RSS
    and asks Groq (Llama 3.3 70B) to write a 90-second
    YouTube video script from them.
    """

    client = Groq(api_key=GROQ_API_KEY)

    today = datetime.date.today().strftime("%B %d, %Y")

    # Build the news block to pass into the prompt
    news_block = ""
    for i, item in enumerate(headlines, 1):
        news_block += f"{i}. {item['title']}\n"
        if item['summary']:
            news_block += f"   {item['summary']}\n"
        news_block += "\n"

    prompt = f"""You are a professional Indian finance news presenter on YouTube.

Today's date: {today}

Here are today's top finance news stories:
{news_block}

Write a STRICT 90-second video script. Maximum 180 words total.

Rules:
- Start with exactly: "Welcome to Finance Daily — your quick market update for {today}."
- Cover only the TOP 3 stories. 2 sentences each. Simple English.
- Mention Nifty or Sensex where relevant.
- NO investment advice. NO predictions. NO "buy" or "sell".
- Facts only — report what already happened.
- End with exactly: "That's all for today. Like and subscribe for your daily market update. See you tomorrow!"
- Write ONLY spoken words. No headings. No brackets. No stage directions.
- MAXIMUM 180 WORDS. Count carefully.
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=800,
        temperature=0.7
    )

    script = response.choices[0].message.content.strip()
    return script

def generate_voiceover(script):
    """
    Converts the generated script text into an MP3 audio file.
    Saves it inside the output/ folder.
    Returns the path of the saved audio file.
    """

    audio_path = OUTPUT_DIR / "voiceover.mp3"

    tts = gTTS(
        text=script,
        lang="en",       # English
        tld="co.in",     # Indian English accent
        slow=False       # Normal speed
    )

    tts.save(str(audio_path))

    print(f"Voiceover saved: {audio_path}")
    return audio_path

def download_stock_videos():
    """
    Searches Pexels for finance-related stock videos.
    Downloads 4 clips and saves them in output/ folder.
    Returns list of file paths.
    """

    PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY")

    # Finance related search keywords
    keywords = [
        "stock market",
        "finance trading",
        "business india",
        "money economy"
    ]

    headers = {"Authorization": PEXELS_API_KEY}
    video_paths = []

    for i, keyword in enumerate(keywords):
        print(f"  Downloading clip {i+1}: '{keyword}'...")

        url = "https://api.pexels.com/videos/search"
        params = {
            "query"      : keyword,
            "per_page"   : 1,
            "orientation": "landscape"
        }

        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if not data.get("videos"):
            print(f"  No video found for '{keyword}', skipping.")
            continue

        # Pick the first video result
        video = data["videos"][0]

        # From available file formats pick the HD one (1280x720)
        chosen_file = None
        for vf in video["video_files"]:
            if vf.get("width") == 1280 and vf.get("height") == 720:
                chosen_file = vf
                break

        # If HD not found, just pick the first available
        if not chosen_file:
            chosen_file = video["video_files"][0]

        # Download the actual video file
        video_url  = chosen_file["link"]
        save_path  = OUTPUT_DIR / f"clip_{i}.mp4"

        video_data = requests.get(video_url, timeout=60)
        with open(save_path, "wb") as f:
            f.write(video_data.content)

        print(f"  Saved: {save_path}")
        video_paths.append(str(save_path))

    return video_paths

def assemble_video(video_paths, audio_path):
    """
    Joins all downloaded stock video clips together,
    loops them to match the voiceover audio length,
    sets the voiceover as audio track,
    exports final video as output/final_video.mp4
    """

    audio          = AudioFileClip(str(audio_path))
    total_duration = audio.duration
    print(f"  Audio duration: {total_duration:.1f} seconds")

    clips = []
    for vp in video_paths:
        try:
            clip = VideoFileClip(vp)

            # Fix mismatched FPS — force all clips to 24fps
            clip = clip.set_fps(24)

            # Resize to 1280x720 if not already
            clip = clip.resize((1280, 720))

            # Remove audio from stock clips
            # (we will add our voiceover as the only audio)
            clip = clip.without_audio()

            print(f"  Loaded: {vp} | {clip.duration:.1f}s | {clip.size} | fps:{clip.fps}")
            clips.append(clip)

        except Exception as e:
            print(f"  Skipping {vp} — error: {e}")

    if not clips:
        print("  No clips loaded. Check your output/ folder.")
        return None

    # Join all clips
    combined = concatenate_videoclips(clips, method="compose")
    print(f"  Combined duration: {combined.duration:.1f}s")

    # Loop if combined is shorter than audio
    if combined.duration < total_duration:
        loops_needed = int(total_duration / combined.duration) + 1
        print(f"  Looping {loops_needed}x to cover {total_duration:.1f}s")
        combined = concatenate_videoclips(
            [combined] * loops_needed,
            method="compose"
        )

    # Trim exactly to audio length
    combined = combined.subclip(0, total_duration)

    # Set voiceover as audio
    combined = combined.set_audio(audio)

    # Export
    out = OUTPUT_DIR / "final_video.mp4"
    print(f"  Exporting → {out}")

    combined.write_videofile(
        str(out),
        fps=24,
        codec="libx264",
        audio_codec="aac",
        logger=None
    )

    audio.close()
    combined.close()
    for c in clips:
        c.close()

    return out

def create_thumbnail(headlines):
    """
    Auto generates a YouTube thumbnail — 1280x720px
    Dark blue background with gold title, red ticker bar at bottom.
    Uses today's date and top headline as content.
    """

    img  = Image.new("RGB", (1280, 720), color=(10, 20, 60))
    draw = ImageDraw.Draw(img)

    # Background gradient
    for i in range(0, 720, 3):
        shade = int(40 * (i / 720))
        draw.rectangle(
            [0, i, 1280, i + 2],
            fill=(10 + shade, 20 + shade, 80 + shade)
        )

    # Left accent bar
    draw.rectangle([0, 0, 8, 720], fill=(255, 180, 0))

    # Load fonts — tries Windows first, then Ubuntu (GitHub Actions), then default
    font_large = font_medium = font_small = None

    for path in [
        "C:/Windows/Fonts/arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
    ]:
        if os.path.exists(path):
            font_large  = ImageFont.truetype(path, 90)
            font_medium = ImageFont.truetype(path, 55)
            break

    for path in [
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"
    ]:
        if os.path.exists(path):
            font_small = ImageFont.truetype(path, 38)
            break

    if not font_large:
        font_large = font_medium = ImageFont.load_default()
    if not font_small:
        font_small = ImageFont.load_default()

    today    = datetime.date.today().strftime("%d %b %Y")
    day_name = datetime.date.today().strftime("%A")

    # Main title
    draw.text((60, 80),  "FINANCE", font=font_large,  fill=(255, 210, 0))
    draw.text((60, 180), "DAILY",   font=font_large,  fill=(255, 255, 255))

    # Divider
    draw.rectangle([60, 300, 700, 305], fill=(255, 180, 0))

    # Subtitle
    draw.text((60, 325), "Market Update", font=font_medium, fill=(180, 220, 255))
    draw.text((60, 395), "Top Stories",   font=font_medium, fill=(150, 190, 230))

    # Date — top right
    draw.text((900, 90),  day_name, font=font_small, fill=(180, 180, 255))
    draw.text((900, 135), today,    font=font_small, fill=(255, 255, 255))

    # Top headline preview — bottom left, above ticker
    if headlines:
        top_story = headlines[0]["title"][:55]  # trim to fit
        draw.text((60, 565), top_story, font=font_small, fill=(200, 200, 200))

    # Bottom red ticker bar
    draw.rectangle([0, 620, 1280, 720], fill=(200, 30, 30))
    draw.text(
        (40, 648),
        "NIFTY  |  SENSEX  |  RBI  |  MARKETS  |  ECONOMY",
        font=font_small,
        fill=(255, 255, 255)
    )

    path = OUTPUT_DIR / "thumbnail.jpg"
    img.save(str(path), "JPEG", quality=95)
    print(f"  Thumbnail saved: {path}")
    return path

def cleanup_output():
    """
    Deletes all files inside output/ folder before each run.
    Ensures no old clips or audio carry over to the new video.
    """
    if OUTPUT_DIR.exists():
        shutil.rmtree(OUTPUT_DIR)   # delete entire output folder
    OUTPUT_DIR.mkdir()              # recreate it fresh and empty
    print("Output folder cleaned.\n")

def upload_to_youtube(video_path, thumb_path, headlines):
    """
    Uploads final_video.mp4 to YouTube using Data API v3.
    On first run opens browser for Google login — saves token.json.
    From second run onwards uses saved token — no login needed.
    """

    SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
    creds  = None

    # If token.json exists from a previous login — use it directly
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)

    # If no valid credentials — open browser for login
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            from google.auth.transport.requests import Request
            print("  Token expired — refreshing automatically...")
            creds.refresh(Request())
            with open("token.json", "w") as f:
                f.write(creds.to_json())
            print("  Token refreshed successfully.")
        else:
            print("  ERROR: No valid token found and cannot open browser on server.")
            print("  Re-run locally to regenerate token.json then update YOUTUBE_TOKEN secret.")
            raise Exception("Invalid token — needs re-authentication locally.")

        # Save token for future runs — no login needed again
        with open("token.json", "w") as f:
            f.write(creds.to_json())
        print("  Login successful. token.json saved.")

    youtube = build("youtube", "v3", credentials=creds)

    today = datetime.date.today().strftime("%B %d, %Y")
    title = f"Finance Daily: Market Update | {today}"

    # Build description from today's headlines
    headline_list = "\n".join([f"• {h['title']}" for h in headlines])
    description   = f"""Today's top finance and stock market news — {today}

{headline_list}

Stay updated with daily Nifty, Sensex, RBI and Indian market news.

#FinanceNews #StockMarket #Nifty #Sensex #MarketUpdate #IndianMarkets #Finance
"""

    print(f"  Uploading: {title}")

    # Upload video
    media    = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
    request  = youtube.videos().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title"      : title,
                "description": description,
                "tags"       : [
                    "finance", "stock market", "nifty", "sensex",
                    "market news", "indian markets", "rbi", today
                ],
                "categoryId" : "25"   # 25 = News & Politics
            },
            "status": {
                "privacyStatus"          : "public",
                "selfDeclaredMadeForKids": False
            }
        },
        media_body=media
    )

    response = request.execute()
    video_id = response["id"]
    print(f"  Video uploaded: https://youtube.com/watch?v={video_id}")

    # Upload thumbnail
    youtube.thumbnails().set(
        videoId   = video_id,
        media_body= MediaFileUpload(str(thumb_path))
    ).execute()
    print(f"  Thumbnail uploaded.")

    return video_id


# Quick test — run this file directly to see the output
if __name__ == "__main__":

    cleanup_output()

    print("Step 1: Fetching finance news...")
    news = fetch_finance_news()
    print(f"Got {len(news)} stories.\n")

    print("Step 2: Generating script with Groq...")
    script = generate_script(news)
    print("Script ready.\n")

    print("Step 3: Generating voiceover...")
    audio_path = generate_voiceover(script)
    print()

    print("Step 4: Downloading stock videos...")
    video_paths = download_stock_videos()
    print(f"Downloaded {len(video_paths)} clips.\n")

    print("Step 5: Assembling final video...")
    final_video = assemble_video(video_paths, audio_path)
    print(f"Final video ready: {final_video}\n")

    print("Step 6: Creating thumbnail...")
    thumb = create_thumbnail(news)
    print(f"Thumbnail ready: {thumb}\n")

    print("Step 7: Uploading to YouTube...")
    try:
        video_id = upload_to_youtube(final_video, thumb, news)
        print(f"\nDone! Video live at: https://youtube.com/watch?v={video_id}")
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise