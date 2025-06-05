from fastapi import FastAPI, Query, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uuid
import yt_dlp
import os
import requests

app = FastAPI()

YT_DLP_AUDIO_DIR = "audio"
WHISPER_API_URL = os.getenv("WHISPER_API_URL", "https://whisper-api-production-1c66.up.railway.app/transcribe")

os.makedirs(YT_DLP_AUDIO_DIR, exist_ok=True)

class YouTubeRequest(BaseModel):
    url: str

@app.get("/")
def root():
    return {"status": "yt-dlp API is running"}

@app.get("/download")
def download_audio(url: str = Query(..., description="YouTube video URL")):
    filename = f"{uuid.uuid4()}.webm"
    filepath = os.path.join(YT_DLP_AUDIO_DIR, filename)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filepath,
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return {"download_url": f"/{YT_DLP_AUDIO_DIR}/{filename}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transcribe-youtube")
def transcribe_youtube(req: YouTubeRequest):
    # Step 1: Call internal /download
    dl_response = download_audio(url=req.url)
    download_url = dl_response["download_url"]
    local_path = download_url.lstrip("/")

    if not os.path.exists(local_path):
        raise HTTPException(status_code=500, detail="Audio file was not created.")

    # Step 2: Send audio to whisper-api
    try:
        with open(local_path, "rb") as f:
            response = requests.post(
                WHISPER_API_URL,
                files={"file": (os.path.basename(local_path), f, "audio/webm")},
            )
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    finally:
        os.remove(local_path)


