#!/usr/bin/env python3
"""
Free Whisper Transcription Service
===================================

Isolated microservice wrapping faster-whisper (local, free, no API key).
Built so voice.ahfl.in (and eventually other Hermes-adjacent apps) can get
Whisper transcription without depending on the live Telegram-bot `hermes`
container or any paid cloud STT API.

PILOT SCOPE (Phase 1) — deliberately minimal:
  - Plain transcription only. POST audio in, get text back.
  - No vault integration, no per-user vocabulary injection yet.
  - X-Hermes-User-Email is accepted and logged now so the request shape
    is already correct for Phase 2, when this will call the gws-vault
    daemon (service="vocab") for per-user initial_prompt/hotwords —
    mirroring how tools/gws_auth.py resolves identity for GWS tokens.

Not in this pilot (see plan): vault-backed vocabulary CRUD endpoints,
migration of existing vocab data, Telegram /vocab command update.

Model is loaded once at startup (not on first request) so the first real
user isn't stuck waiting for both model load AND their own transcription.
Reuses the same faster-whisper model cache directory as the `hermes`
container (bind-mounted read-write in docker-compose) so the already
-downloaded "small" model snapshot is reused with no re-download.
"""

import logging
import os
import tempfile
import time

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [free-whisper] %(message)s",
)
logger = logging.getLogger("free-whisper")

MODEL_SIZE = os.environ.get("WHISPER_MODEL", "small")

app = FastAPI(title="Free Whisper Transcription Service")

_model = None
_model_load_error = None


def _load_model():
    """Lazy-load (and cache) the faster-whisper model. Raises on failure."""
    global _model, _model_load_error
    if _model is not None:
        return _model
    from faster_whisper import WhisperModel

    logger.info("Loading faster-whisper model '%s' (device=cpu, compute_type=int8)...", MODEL_SIZE)
    t0 = time.time()
    try:
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    except Exception as exc:
        _model_load_error = str(exc)
        raise
    logger.info("Model '%s' loaded in %.1fs", MODEL_SIZE, time.time() - t0)
    return _model


@app.on_event("startup")
async def _warm_model_on_startup():
    try:
        _load_model()
    except Exception as exc:
        # Don't crash the process — /health will report the failure and
        # /transcribe will retry loading (and report a clear 503) instead
        # of the whole container being stuck in a restart loop.
        logger.error("Model failed to load at startup: %s", exc, exc_info=True)


@app.get("/health")
async def health():
    return {
        "status": "ok" if _model is not None else "model_not_loaded",
        "model": MODEL_SIZE,
        "model_loaded": _model is not None,
        "model_load_error": _model_load_error,
    }


@app.post("/transcribe")
async def transcribe(request: Request):
    user_email = request.headers.get("x-hermes-user-email", "unknown")
    language = (request.headers.get("x-whisper-language") or request.query_params.get("language") or "").strip()
    language = language or None

    audio_bytes = await request.body()
    if not audio_bytes:
        return JSONResponse({"success": False, "error": "empty audio body"}, status_code=400)

    logger.info(
        "Transcribe request: user=%s bytes=%d language=%s",
        user_email, len(audio_bytes), language or "auto",
    )

    try:
        model = _load_model()
    except Exception as exc:
        logger.error("Model unavailable for request from %s: %s", user_email, exc, exc_info=True)
        return JSONResponse({"success": False, "error": f"model unavailable: {exc}"}, status_code=503)

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".audio", delete=False) as tmp:
            tmp.write(audio_bytes)
            tmp_path = tmp.name

        t0 = time.time()
        kwargs = {"beam_size": 5}
        if language:
            kwargs["language"] = language
        segments, info = model.transcribe(tmp_path, **kwargs)
        text = " ".join(seg.text.strip() for seg in segments).strip()
        elapsed = time.time() - t0

        logger.info(
            "Transcribed for %s: %.1fs audio -> %.1fs processing, lang=%s, %d chars",
            user_email, info.duration, elapsed, info.language, len(text),
        )
        return {
            "success": True,
            "text": text,
            "language": info.language,
            "audio_duration_sec": round(info.duration, 2),
            "processing_sec": round(elapsed, 2),
        }
    except Exception as exc:
        logger.error("Transcription failed for %s: %s", user_email, exc, exc_info=True)
        return JSONResponse({"success": False, "error": str(exc)}, status_code=500)
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
