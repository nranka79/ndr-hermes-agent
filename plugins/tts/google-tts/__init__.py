"""Google Cloud Text-to-Speech backend — REST API, base64 JSON response.

Confirmed reachable, clean error shape (400 API_KEY_INVALID) via
throwaway probe. Full call unverified without a live key.

Same key-confusion risk as the ``google-speech`` STT plugin: this needs a
GCP API key (console.cloud.google.com, Text-to-Speech API enabled), NOT
an AI Studio / Gemini key. Checks ``GOOGLE_CLOUD_TTS_API_KEY`` first, then
falls back to ``GOOGLE_CLOUD_SPEECH_API_KEY`` — a single GCP API key with
both Cloud APIs enabled on its project works for both plugins, so users
who already set up Speech-to-Text don't need a second key.

Response is base64 JSON (``audioContent`` field), not raw bytes or a URL.
"""

from __future__ import annotations

import base64
import logging
import os
from typing import Any, Dict, Iterator, List, Optional

import requests

from agent.tts_provider import DEFAULT_OUTPUT_FORMAT, TTSProvider, resolve_output_format

logger = logging.getLogger(__name__)

_BASE_URL = "https://texttospeech.googleapis.com/v1/text:synthesize"

_ENCODING_BY_FORMAT = {
    "mp3": "MP3",
    "wav": "LINEAR16",
    "ogg": "OGG_OPUS",
}

DEFAULT_VOICE = "en-US-Standard-C"


def _resolve_api_key() -> str:
    return (
        os.environ.get("GOOGLE_CLOUD_TTS_API_KEY", "").strip()
        or os.environ.get("GOOGLE_CLOUD_SPEECH_API_KEY", "").strip()
    )


class GoogleTTSProvider(TTSProvider):
    """Google Cloud Text-to-Speech."""

    @property
    def name(self) -> str:
        return "google-tts"

    @property
    def display_name(self) -> str:
        return "Google Cloud Text-to-Speech"

    def is_available(self) -> bool:
        return bool(_resolve_api_key())

    def list_voices(self) -> List[Dict[str, Any]]:
        return [
            {"id": DEFAULT_VOICE, "display": "US English (Standard C)", "language": "en-US", "gender": "female"},
        ]

    def default_voice(self) -> Optional[str]:
        return DEFAULT_VOICE

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Google Cloud Text-to-Speech",
            "badge": "free",
            "tag": "4M chars/month free — requires a GCP API key, not an AI Studio key",
            "env_vars": [
                {
                    "key": "GOOGLE_CLOUD_TTS_API_KEY",
                    "prompt": "Google Cloud API key (Text-to-Speech API enabled)",
                    "url": "https://console.cloud.google.com/apis/credentials",
                },
            ],
        }

    def synthesize(
        self,
        text: str,
        output_path: str,
        *,
        voice: Optional[str] = None,
        model: Optional[str] = None,
        speed: Optional[float] = None,
        format: str = DEFAULT_OUTPUT_FORMAT,
        **extra: Any,
    ) -> str:
        api_key = _resolve_api_key()
        if not api_key:
            raise RuntimeError(
                "GOOGLE_CLOUD_TTS_API_KEY (or GOOGLE_CLOUD_SPEECH_API_KEY) is not set."
            )

        fmt = resolve_output_format(format)
        encoding = _ENCODING_BY_FORMAT.get(fmt, "MP3")
        voice_id = voice or DEFAULT_VOICE
        language_code = "-".join(voice_id.split("-")[:2]) if "-" in voice_id else "en-US"

        payload: Dict[str, Any] = {
            "input": {"text": text},
            "voice": {"languageCode": language_code, "name": voice_id},
            "audioConfig": {"audioEncoding": encoding},
        }
        if speed is not None:
            payload["audioConfig"]["speakingRate"] = speed

        response = requests.post(
            _BASE_URL, params={"key": api_key}, json=payload, timeout=60,
        )
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text[:300])
            except Exception:
                err_msg = resp.text[:300] if resp is not None else str(exc)
            raise RuntimeError(f"Google TTS failed ({status}): {err_msg}") from exc

        result = response.json()
        audio_b64 = result.get("audioContent")
        if not audio_b64:
            raise RuntimeError("Google TTS returned no audioContent")

        audio_bytes = base64.b64decode(audio_b64)
        with open(output_path, "wb") as fh:
            fh.write(audio_bytes)

        return output_path


def register(ctx) -> None:
    """Plugin entry point — register the Google Cloud TTS provider."""
    ctx.register_tts_provider(GoogleTTSProvider())
