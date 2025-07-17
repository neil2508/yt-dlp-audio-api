from fastapi import FastAPI, Request
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

class VideoURL(BaseModel):
    url: str

@app.get("/")
def root():
    return {"message": "YouTube audio downloader API is running."}

@app.post("/transcribe-youtube")
def transcribe_youtube(data: VideoURL):
    url = data.url

    try:
        output_filename = "audio.%(ext)s"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_filename,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Find the downloaded file
        downloaded_file = None
        for ext in ['mp3', 'm4a', 'webm']:
            fname = f"audio.{ext}"
            if os.path.exists(fname):
                downloaded_file = fname
                break

        if not downloaded_file:
            return {"error": "No audio file found after download"}

        return {"status": "success", "filename": downloaded_file}

    except Exception as e:
        return {"error": str(e)}

