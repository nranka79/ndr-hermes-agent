FROM python:3.12-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates wget curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir browser-use starlette uvicorn playwright

# Install Chromium + all system deps via playwright
RUN python -m playwright install chromium --with-deps

WORKDIR /app
COPY smart_browser_server.py .

EXPOSE 9181
CMD ["python", "smart_browser_server.py"]
