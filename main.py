from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import yt_dlp
import uuid
import os

app = FastAPI()

# Ensure audio folder exists
os.makedirs("audio", exist_ok=True)

# Mount static audio files
app.mount("/audio", StaticFiles(directory="audio"), name="audio")

@app.get("/")
def root():
    return {"status": "yt-dlp API is running"}

@app.get("/download")
def download_audio(url: str = Query(...)):
    try:
        video_id = str(uuid.uuid4())
        output_path = f"audio/{video_id}.webm"

        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if os.path.exists(output_path):
            return {"download_url": f"/audio/{video_id}.webm"}
        else:
            return JSONResponse(status_code=500, content={"error": "Audio file was not created."})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

