from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import uuid
import os
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
        unique_id = str(uuid.uuid4())
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': f'/tmp/{unique_id}.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '64',
            }],
            'cookiefile': 'cookies.txt',
            'quiet': True,
            'noplaylist': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            output_path = ydl.prepare_filename(info_dict).replace(".webm", ".mp3").replace(".m4a", ".mp3")

        if not os.path.exists(output_path):
            return JSONResponse(status_code=500, content={"error": f"Download failed: {output_path} not found"})

        with open(output_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text"
            )

        summary_prompt = f"""
You are an expert summariser. Your task is to summarise the following spoken transcript clearly and accurately.

- Length: 450 to 500 words
- Tone: neutral, factual, natural
- Audience: general readers unfamiliar with the original video
- Focus: main themes, key points, useful examples or insights
- Do not reference the video, speaker, or transcript directly
- Avoid filler or speculation

Transcript:
{transcript}
"""

        chat_response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You summarise transcripts clearly and concisely for a general audience."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.5
        )

        summary = chat_response.choices[0].message.content.strip()
        return {"summary": summary}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": f"Transcription failed: {str(e)}"})

