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
YOUTUBE_API_KEY = "AlzaSyB0h3TxEUcmZDvYp91f_ZHKa8nE9Kxd9eA"  # ← Replace this!

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
    try:
        import re

        print("🔹 Received URL:", url)
        # extract ID
        match = re.search(r"(?:v=|youtu\.be/|shorts/)([A-Za-z0-9_-]{11})", url)
        if not match:
            raise Exception("Invalid YouTube URL")
        video_id = match.group(1)

        print("🔹 Video ID:", video_id)

        # Hit YouTube Data API
        YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY_HERE"  # <-- make sure this is a valid key
        metadata_url = (
            f"https://www.googleapis.com/youtube/v3/videos"
            f"?id={video_id}&part=snippet,contentDetails,statistics"
            f"&key={YOUTUBE_API_KEY}"
        )

        print("🔹 Fetching metadata:", metadata_url)
        r = requests.get(metadata_url)
        print("🔹 YouTube API response code:", r.status_code)
        if r.status_code != 200:
            raise Exception(f"YouTube API failed: {r.text}")

        data = r.json()
        if not data.get("items"):
            raise Exception("No video found in API response")

        # yt-dlp part (commented out for testing)
        print("🔹 Skipping yt-dlp for debug")

        snippet = data["items"][0]["snippet"]
        content = data["items"][0]["contentDetails"]
        metadata = {
            "title": snippet.get("title"),
            "description": snippet.get("description"),
            "duration": content.get("duration"),
        }

        print("✅ Successfully built metadata")
        return metadata

    except Exception as e:
        print("💥 ERROR in /giveall:", str(e))
        raise HTTPException(status_code=500, detail=str(e))
