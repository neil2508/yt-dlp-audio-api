from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import yt_dlp
import os
import uuid

app = FastAPI()

from fastapi import FastAPI
from pydantic import BaseModel
import yt_dlp
import os

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "yt-dlp-audio-api is running"}

class VideoURL(BaseModel):
    url: str

@app.post("/transcribe-youtube")
def transcribe_youtube(video: VideoURL):
    url = video.url
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': '/tmp/%(id)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(result).rsplit('.', 1)[0] + ".mp3"
            if os.path.exists(filename):
                return {"message": "Download successful", "file_path": filename}
            else:
                return {"error": "Download failed"}
    except Exception as e:
        return {"error": str(e)}

@app.get("/")
async def root():
    return {"message": "YouTube Audio Extractor is running"}

@app.post("/transcribe-youtube")
async def transcribe(request: Request):
    data = await request.json()
    url = data.get("url")
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
