from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import yt_dlp
import uuid
import os
import openai

# Set your OpenAI API key (make sure it's added as an environment variable)
openai.api_key = os.getenv("OPENAI_API_KEY")

app = FastAPI()

class VideoURL(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "YouTube Audio Extractor is running"}

@app.post("/transcribe-youtube")
async def transcribe_and_summarize(video: VideoURL):
    url = video.url
    if not url:
        return JSONResponse(status_code=400, content={"error": "Missing 'url' in request body"})

    try:
        # Generate unique filename
       unique_id = str(uuid.uuid4())
file_path = f"/tmp/{unique_id}.mp3"
yt_dlp_outtmpl = f"/tmp/{unique_id}.%(ext)s"

ydl_opts = {
    'format': 'bestaudio/best',
    'outtmpl': ydl_outtmpl,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
        'preferredquality': '192',
    }],
    'cookiefile': 'cookies.txt',
    'quiet': True,
    'noplaylist': True
}


        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Transcribe the audio
        with open(file_path, "rb") as audio_file:
            transcript_result = openai.Audio.transcribe(
                model="whisper-1",
                file=audio_file
            )

        transcript = transcript_result["text"]

        # Summarize the transcript
        summary_prompt = (
            "Summarise the following transcription in 200–250 words for a blog audience. "
            "Use a clear, engaging tone:\n\n"
            f"{transcript}"
        )

        summary_response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional blog writer."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.7
        )

        summary = summary_response["choices"][0]["message"]["content"]

        return {
            "transcript": transcript,
            "summary": summary
        }

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
