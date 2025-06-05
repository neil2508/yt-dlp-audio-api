from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
import uuid
import yt_dlp
import requests
import os

app = FastAPI()

AUDIO_DIR = "audio"
WHISPER_API_URL = "https://whisper-api-production-1c66.up.railway.app/transcribe"

os.makedirs(AUDIO_DIR, exist_ok=True)

@app.get("/transcribe")
def transcribe_youtube_video(url: str):
    video_id = str(uuid.uuid4())
    output_path = f"{AUDIO_DIR}/{video_id}.webm"

    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"yt-dlp error: {str(e)}"})

    try:
        with open(output_path, "rb") as audio_file:
            response = requests.post(
                WHISPER_API_URL,
                files={"file": (f"{video_id}.webm", audio_file, "audio/webm")}
            )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"whisper upload error: {str(e)}"})

    os.remove(output_path)

    if response.status_code != 200:
        return JSONResponse(status_code=500, content={"error": "Whisper API failed", "details": response.text})

    return response.json()
