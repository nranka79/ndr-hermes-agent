"""Deepgram speech-to-text backend — Nova-3 model.

Confirmed reachable, standard token-auth shape (clean 401 on a bad key,
no billing surprise) via throwaway probe. Full transcription call
unverified without a live key — request shape (raw audio bytes as body,
mimetype-derived Content-Type, query-string options) is per Deepgram's
documented REST API.

PILOT SCOPE: prerecorded audio only, single synchronous request. No
streaming, no diarization/word-timestamps passthrough.
"""

from __future__ import annotations

import logging
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from agent.transcription_provider import TranscriptionProvider

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.deepgram.com/v1/listen"
DEFAULT_MODEL = "nova-3"

_MIME_BY_EXT = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".webm": "audio/webm",
}


def _guess_content_type(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext in _MIME_BY_EXT:
        return _MIME_BY_EXT[ext]
    guessed, _ = mimetypes.guess_type(file_path)
    return guessed or "audio/wav"


class DeepgramTranscriptionProvider(TranscriptionProvider):
    """Deepgram Nova-3 speech-to-text."""

    @property
    def name(self) -> str:
        return "deepgram"

    @property
    def display_name(self) -> str:
        return "Deepgram (Nova-3)"

    def is_available(self) -> bool:
        return bool(os.environ.get("DEEPGRAM_API_KEY", "").strip())

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": DEFAULT_MODEL,
                "display": "Nova-3",
                "languages": ["en", "es", "fr", "de", "hi", "ja", "multi", "+more"],
            }
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Deepgram",
            "badge": "free",
            "tag": "Nova-3 — $200 free credit on signup",
            "env_vars": [
                {
                    "key": "DEEPGRAM_API_KEY",
                    "prompt": "Deepgram API key",
                    "url": "https://console.deepgram.com/",
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
        api_key = os.environ.get("DEEPGRAM_API_KEY", "").strip()
        if not api_key:
            return {
                "success": False,
                "transcript": "",
                "error": "DEEPGRAM_API_KEY is not set.",
                "provider": "deepgram",
            }

        model_id = model or DEFAULT_MODEL
        content_type = _guess_content_type(file_path)

        params: Dict[str, str] = {"model": model_id, "smart_format": "true"}
        if language:
            params["language"] = language

        try:
            with open(file_path, "rb") as fh:
                audio_bytes = fh.read()
        except OSError as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"Could not read audio file: {exc}",
                "provider": "deepgram",
            }

        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": content_type,
        }

        try:
            response = requests.post(
                _BASE_URL, headers=headers, params=params, data=audio_bytes, timeout=120,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            try:
                err_msg = resp.json().get("err_msg", resp.text[:300])
            except Exception:
                err_msg = resp.text[:300] if resp is not None else str(exc)
            return {
                "success": False,
                "transcript": "",
                "error": f"Deepgram transcription failed ({status}): {err_msg}",
                "provider": "deepgram",
            }
        except (requests.Timeout, requests.ConnectionError) as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"Deepgram request failed: {exc}",
                "provider": "deepgram",
            }

        try:
            result = response.json()
            transcript = (
                result["results"]["channels"][0]["alternatives"][0]["transcript"]
            )
        except Exception as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"Could not parse Deepgram response: {exc}",
                "provider": "deepgram",
            }

        return {"success": True, "transcript": transcript, "provider": "deepgram"}


def register(ctx) -> None:
    """Plugin entry point — register the Deepgram STT provider."""
    ctx.register_transcription_provider(DeepgramTranscriptionProvider())
