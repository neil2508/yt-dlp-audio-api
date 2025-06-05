from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import os
import uuid
import yt_dlp

app = FastAPI()

# Allow requests from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create an audio folder if it doesn't exist
if not os.path.exists("audio"):
    os.makedirs("audio")

# Allow public access to the audio files
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

@app.get("/")
def root():
    return {"message": "yt-dlp API is running"}

@app.get("/download")
async def download_audio(url: str):
    try:
        audio_id = str(uuid.uuid4())
        output_path = f"audio/{audio_id}.webm"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(output_path):
            public_url = f"https://YOUR-APP-NAME.up.railway.app/audio/{audio_id}.webm"
            return JSONResponse(content={"download_url": public_url})

        return JSONResponse(status_code=500, content={"error": "Audio file was not created."})

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
