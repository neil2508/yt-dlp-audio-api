from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import uuid
import os
import openai

app = FastAPI()

# INSERT YOUR OPENAI API KEY HERE
openai.api_key = os.getenv("OPENAI_API_KEY")

class VideoURL(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "YouTube Audio Extractor and Transcriber is running"}

@app.post("/transcribe-youtube")
async def transcribe(video: VideoURL):
    url = video.url
    if not url:
        return JSONResponse(status_code=400, content={"error": "Missing 'url' in request body"})

    try:
        # Generate a shared UUID for file naming
        unique_id = str(uuid.uuid4())
        base_path = f"/tmp/{unique_id}"
        download_path = f"{base_path}.mp3"
        output_template = f"{base_path}.%(ext)s"

        # yt-dlp download options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_template,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'noplaylist': True
        }

        # Download the audio
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        if not os.path.exists(download_path):
            return JSONResponse(status_code=500, content={"error": "Audio file was not created"})

        # Transcribe with Whisper
        with open(download_path, "rb") as audio_file:
            transcription = openai.Audio.transcribe("whisper-1", audio_file)

        transcript_text = transcription.get("text", "")
        if not transcript_text:
            return JSONResponse(status_code=500, content={"error": "Transcription failed"})

        # Summarize with GPT
        summary_prompt = f"Summarize the following transcript into a short blog-style summary (200–250 words):\n\n{transcript_text}"
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a helpful assistant who rewrites transcripts into engaging blog summaries."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.7,
            max_tokens=400
        )

        summary_text = response["choices"][0]["message"]["content"]
        return {
            "summary": summary_text.strip()
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
