from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import uuid
import os

app = FastAPI()

class VideoURL(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "YouTube Audio Extractor is running"}

@app.post("/transcribe-youtube")
async def transcribe(video: VideoURL):
    url = video.url
    if not url:
        return JSONResponse(status_code=400, content={"error": "Missing 'url' in request body"})

    try:
        output_path = f"/tmp/{uuid.uuid4()}.mp3"
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return {"message": "Audio extracted", "file_path": output_path}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
