FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y ffmpeg

# Install Python dependencies
COPY requirements.txt .  # ✅ Copy just the file, not into a file path
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy all app files, including cookies.txt
COPY main.py .           # ✅ Copy script
COPY cookies.txt .       # ✅ Copy cookie file

# Run the API
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]


