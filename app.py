from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

# Allow all origins for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "FastAPI YouTube backend is running 🚀"}


@app.get("/giveall")
async def give_all(url: str = Query(..., description="YouTube video URL")):
    """
    Takes a YouTube URL and returns:
    - Direct video URL (playable)
    - Timestamps (chapters)
    - Captions (URLs to subtitles)
    - Metadata (title, duration, uploader)
    """
    if not url:
        raise HTTPException(status_code=400, detail="YouTube URL is required")

    try:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'writesubtitles': True,
            'writeautomaticsub': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            # Pick the best playable URL
            formats = info.get("formats", [])
            video_url = None
            for f in reversed(formats):
                if f.get("url") and f.get("acodec") != "none" and f.get("vcodec") != "none":
                    video_url = f["url"]
                    break

            if not video_url:
                raise HTTPException(status_code=404, detail="No playable stream URL found")

            # Extract timestamps / chapters
            chapters = info.get("chapters", [])
            timestamps = []
            if chapters:
                timestamps = [
                    {"title": c.get("title"), "start_time": c.get("start_time"), "end_time": c.get("end_time")}
                    for c in chapters
                ]

            # Extract captions
            subtitles = info.get("subtitles") or info.get("automatic_captions") or {}
            captions = {}
            for lang, tracks in subtitles.items():
                if isinstance(tracks, list) and len(tracks) > 0:
                    captions[lang] = tracks[0].get("url")

            # Return all data
            return {
                "video_url": video_url,
                "timestamps": timestamps,
                "captions": captions,
                "title": info.get("title"),
                "duration": info.get("duration"),
                "uploader": info.get("uploader"),
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing video: {str(e)}")
