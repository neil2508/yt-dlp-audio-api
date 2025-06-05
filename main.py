from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
import yt_dlp
import uuid
import os

app = FastAPI()

@app.get("/")
def root():
    return {"status": "yt-dlp API is running"}

@app.get("/download")
def download_audio(url: str = Query(..., description="YouTube video URL")):
    temp_filename = f"{uuid.uuid4()}.mp3"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": temp_filename,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return FileResponse(
            path=temp_filename,
            filename="audio.mp3",
            media_type="audio/mpeg",
            background=lambda: os.remove(temp_filename),
        )
    except Exception as e:
        return {"error": str(e)}
