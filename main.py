from fastapi import FastAPI, Query
from fastapi.responses import FileResponse, JSONResponse
import yt_dlp
import uuid
import os

app = FastAPI()

@app.get("/")
def root():
    return {"status": "yt-dlp API is running"}

@app.get("/download")
def download_audio(url: str = Query(..., description="YouTube video URL")):
    temp_filename = f"{uuid.uuid4()}.%(ext)s"
    try:
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": temp_filename,
            "quiet": True,
            "no_warnings": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(url, download=True)
            downloaded_file = ydl.prepare_filename(result)

        if not os.path.exists(downloaded_file):
            return JSONResponse(
                status_code=500,
                content={"error": f"Audio file '{downloaded_file}' was not created."}
            )

        return FileResponse(
            path=downloaded_file,
            filename=os.path.basename(downloaded_file),
            media_type="audio/webm" if downloaded_file.endswith(".webm") else "audio/mpeg"
        )

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

