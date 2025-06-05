from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import yt_dlp
import requests
import uuid
import os

app = FastAPI()

# Create temp directory if it doesn't exist
TEMP_DIR = "temp_audio"
os.makedirs(TEMP_DIR, exist_ok=True)

class YouTubeURL(BaseModel):
    url: str

@app.post("/transcribe-youtube")
def transcribe_youtube(data: YouTubeURL):
    try:
        # Set up yt_dlp options to download best audio
        ydl_opts = {
            'format': 'bestaudio/best',
            'quiet': True,
            'outtmpl': f"{TEMP_DIR}/%(id)s.%(ext)s",
        }

        # Download video and extract info
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(data.url, download=True)
            title = info.get('title')
            file_path = ydl.prepare_filename(info)

        # Open downloaded audio and send to Whisper API
        with open(file_path, "rb") as f:
            files = {
                "file": (os.path.basename(file_path), f, "audio/webm")
            }
            response = requests.post(
                "https://whisper-api-production-1c66.up.railway.app/transcribe",
                files=files
            )

        # Handle transcription failure
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Transcription failed")

        # Parse transcription result
        transcription = response.json().get("transcription")

        # Delete temp file
        os.remove(file_path)

        # Return both video title and transcript
        return {
            "title": title,
            "transcription": transcription
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



