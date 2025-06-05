from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import FileResponse
import yt_dlp
import uuid
import os
import time

app = FastAPI()

@app.get("/")
def root():
    return {"status": "yt-dlp API is running"}

@app.get("/download")
def download_audio(url: str = Query(..., description="YouTube video URL")):
    filename = f"{uuid.uuid4()}.mp3"
    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": filename,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.download([url])
            if result != 0:
                raise Exception("yt-dlp failed to download or convert the video.")

        # Check for the file and wait a moment if needed
        timeout = 5
        while not os.path.exists(filename) and timeout > 0:
            time.sleep(1)
            timeout -= 1

        if not os.path.exists(filename):
            raise FileNotFoundError(f"Audio file '{filename}' was not created.")

        return FileResponse(
            path=filename,
            filename="audio.mp3",
            media_type="audio/mpeg",
            background=lambda: os.remove(filename)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
