"""Google Cloud Speech-to-Text backend — synchronous REST API.

Confirmed reachable, clean error shape (400 API_KEY_INVALID, not a
billing gate) via throwaway probe. Full call unverified without a live
key.

IMPORTANT — key confusion risk: this is a Google Cloud Platform API key
(console.cloud.google.com, Speech-to-Text API enabled on a GCP project),
NOT the AI Studio / Gemini key (aistudio.google.com) Hermes's ``google``
LLM provider uses. The two are different products and a Gemini key will
NOT work here. Deliberately uses its own env var
(``GOOGLE_CLOUD_SPEECH_API_KEY``) instead of reusing ``GOOGLE_API_KEY``
to avoid a silent cross-product failure.

PILOT SCOPE: ``speech:recognize`` (synchronous) only — Google caps this
at ~1 minute of audio / 10MB inline content. Longer audio needs
``speech:longrunningrecognize`` + a GCS upload, not implemented here.
Encoding is inferred from file extension; unrecognized extensions are
sent without an explicit encoding hint (works for self-describing
containers like WAV/FLAC, may fail for raw/headerless audio).
"""

from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from agent.transcription_provider import TranscriptionProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://speech.googleapis.com/v1/speech:recognize"

_ENCODING_BY_EXT = {
    ".wav": "LINEAR16",
    ".flac": "FLAC",
    ".mp3": "MP3",
    ".ogg": "OGG_OPUS",
}

DEFAULT_LANGUAGE = "en-US"


class GoogleSpeechTranscriptionProvider(TranscriptionProvider):
    """Google Cloud Speech-to-Text (synchronous recognize)."""

    @property
    def name(self) -> str:
        return "google-speech"

    @property
    def display_name(self) -> str:
        return "Google Cloud Speech-to-Text"

    def is_available(self) -> bool:
        return bool(os.environ.get("GOOGLE_CLOUD_SPEECH_API_KEY", "").strip())

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Google Cloud Speech-to-Text",
            "badge": "free",
            "tag": "60 min/month free — requires a GCP API key, not an AI Studio key",
            "env_vars": [
                {
                    "key": "GOOGLE_CLOUD_SPEECH_API_KEY",
                    "prompt": "Google Cloud API key (Speech-to-Text API enabled)",
                    "url": "https://console.cloud.google.com/apis/credentials",
                },
            ],
        }

    def transcribe(
        self,
        file_path: str,
        *,
        model: Optional[str] = None,
        language: Optional[str] = None,
        **extra: Any,
    ) -> Dict[str, Any]:
        api_key = os.environ.get("GOOGLE_CLOUD_SPEECH_API_KEY", "").strip()
        if not api_key:
            return {
                "success": False,
                "transcript": "",
                "error": "GOOGLE_CLOUD_SPEECH_API_KEY is not set.",
                "provider": "google-speech",
            }

        try:
            with open(file_path, "rb") as fh:
                audio_bytes = fh.read()
        except OSError as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"Could not read audio file: {exc}",
                "provider": "google-speech",
            }

        config: Dict[str, Any] = {"languageCode": language or DEFAULT_LANGUAGE}
        ext = Path(file_path).suffix.lower()
        if ext in _ENCODING_BY_EXT:
            config["encoding"] = _ENCODING_BY_EXT[ext]

        payload = {
            "config": config,
            "audio": {"content": base64.b64encode(audio_bytes).decode("ascii")},
        }

        try:
            response = requests.post(
                _BASE_URL, params={"key": api_key}, json=payload, timeout=90,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text[:300])
            except Exception:
                err_msg = resp.text[:300] if resp is not None else str(exc)
            return {
                "success": False,
                "transcript": "",
                "error": f"Google Speech-to-Text failed ({status}): {err_msg}",
                "provider": "google-speech",
            }
        except (requests.Timeout, requests.ConnectionError) as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"Google Speech-to-Text request failed: {exc}",
                "provider": "google-speech",
            }

        try:
            result = response.json()
        except Exception as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"Google returned invalid JSON: {exc}",
                "provider": "google-speech",
            }

        results = result.get("results", [])
        if not results:
            # Valid response, just no speech detected — not an error.
            return {"success": True, "transcript": "", "provider": "google-speech"}

        transcript = " ".join(
            r["alternatives"][0]["transcript"]
            for r in results
            if r.get("alternatives")
        ).strip()

        return {"success": True, "transcript": transcript, "provider": "google-speech"}


def register(ctx) -> None:
    """Plugin entry point — register the Google Cloud Speech-to-Text provider."""
    ctx.register_transcription_provider(GoogleSpeechTranscriptionProvider())
