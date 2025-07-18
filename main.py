from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import uuid
import os
import openai

from openai import OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

class VideoURL(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "YouTube Audio Extractor + Transcriber is running"}

@app.post("/transcribe-youtube")
async def transcribe_youtube(video: VideoURL):
    url = video.url
    if not url:
        return JSONResponse(status_code=400, content={"error": "Missing 'url' in request body"})

    try:
        # Generate output path
        unique_id = str(uuid.uuid4())
        output_path = f"/tmp/{unique_id}.mp3"

        # yt-dlp config
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

        # Download audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.download([url])

        # Confirm file exists
        if not os.path.exists(output_path):
            return JSONResponse(status_code=500, content={"error": f"Download failed: {output_path} not found"})

        # Transcribe using OpenAI Whisper
        with open(output_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        # Summarize using GPT
        summary_prompt = (
            f"Please summarize the following YouTube transcript in 200–250 words, "
            f"rewriting it as a blog post:\n\n{transcript}"
        )

        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who writes summaries as engaging blog posts."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.7
        )

        summary = chat_response.choices[0].message.content.strip()

        return {
            "summary": summary
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Transcription failed: {str(e)}"})
