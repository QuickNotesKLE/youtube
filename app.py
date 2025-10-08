from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp
import requests
import os

app = FastAPI()

# Allow all origins for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Hardcoded YouTube API key (replace this with your real API key)
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY_HERE"  # ← Replace this!

@app.get("/")
def home():
    return {"message": "🚀 YouTube Hybrid Metadata API is running"}

def extract_video_id(url: str) -> str:
    """Extract YouTube video ID from URL."""
    import re
    patterns = [
        r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})",
    ]
    for p in patterns:
        match = re.search(p, url)
        if match:
            return match.group(1)
    raise HTTPException(status_code=400, detail="Invalid YouTube URL")

@app.get("/giveall")
async def give_all(url: str = Query(..., description="YouTube video URL")):
    """
    Returns:
    - Safe metadata via YouTube Data API
    - Direct stream URL, captions, and chapters via yt-dlp
    """
    if not YOUTUBE_API_KEY:
        raise HTTPException(status_code=500, detail="Missing YouTube API key")

    video_id = extract_video_id(url)

    # Step 1️⃣ - Get safe metadata via YouTube Data API
    metadata_url = (
        f"https://www.googleapis.com/youtube/v3/videos"
        f"?id={video_id}&part=snippet,contentDetails,statistics"
        f"&key={YOUTUBE_API_KEY}"
    )

    response = requests.get(metadata_url)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="YouTube Data API failed")

    data = response.json()
    if not data.get("items"):
        raise HTTPException(status_code=404, detail="Video not found")

    video_data = data["items"][0]
    snippet = video_data["snippet"]
    content = video_data["contentDetails"]

    # Extract metadata fields
    metadata = {
        "title": snippet.get("title"),
        "description": snippet.get("description"),
        "published_at": snippet.get("publishedAt"),
        "channel_title": snippet.get("channelTitle"),
        "tags": snippet.get("tags", []),
        "thumbnail": snippet.get("thumbnails", {}).get("high", {}).get("url"),
        "duration": content.get("duration"),
    }

    # Step 2️⃣ - Get advanced details via yt-dlp
    try:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

        # Playable stream URL
        video_url = None
        for f in reversed(info.get("formats", [])):
            if f.get("url") and f.get("acodec") != "none" and f.get("vcodec") != "none":
                video_url = f["url"]
                break

        # Captions
        subtitles = info.get("subtitles") or info.get("automatic_captions") or {}
        captions = {}
        for lang, tracks in subtitles.items():
            if isinstance(tracks, list) and len(tracks) > 0:
                captions[lang] = tracks[0].get("url")

        # Chapters
        chapters = info.get("chapters", [])
        timestamps = [
            {"title": c.get("title"), "start_time": c.get("start_time"), "end_time": c.get("end_time")}
            for c in chapters
        ] if chapters else []

        metadata.update({
            "video_url": video_url,
            "captions": captions,
            "timestamps": timestamps,
        })

    except Exception as e:
        metadata["yt_dlp_error"] = str(e)

    return metadata
