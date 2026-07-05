FROM python:3.11-slim
WORKDIR /app

# ffmpeg as a safety net for audio decoding, even though faster-whisper's
# ctranslate2/av stack handles most containers (webm/opus, ogg, mp3, m4a) on its own.
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY server.py .

EXPOSE 8000
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
