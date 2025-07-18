from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import uuid
import os
from openai import OpenAI

app = FastAPI()
client = OpenAI()  # Uses OPENAI_API_KEY from environment variable

class VideoURL(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "YouTube Audio Extractor & Transcriber is running"}

@app.post("/transcribe-youtube")
async def transcribe(video: VideoURL):
    url = video.url
    if not url:
        return JSONResponse(status_code=400, content={"error": "Missing 'url' in request body"})

    unique_id = str(uuid.uuid4())
    output_path = f"/tmp/{unique_id}.mp3"

    # Step 1: Download audio using yt-dlp
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': output_path,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'cookiefile': 'cookies.txt',
        'quiet': True,
        'noplaylist': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Audio download failed: {str(e)}"})

    # Step 2: Transcribe using OpenAI Whisper
    try:
        with open(output_path, "rb") as f:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=f
            )
        os.remove(output_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Transcription failed: {str(e)}"})

    # Step 3: Summarize using GPT
    try:
        summary_prompt = f"Summarize this YouTube transcript in 200–250 words for a blog post:\n\n{transcript.text}"
        summary_response = client.chat.completions.create(
            model="gpt-4",
            messages=[{"role": "user", "content": summary_prompt}],
            temperature=0.7
        )
        summary = summary_response.choices[0].message.content
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Summary failed: {str(e)}"})

    return {
        "transcript": transcript.text,
        "summary": summary
    }
