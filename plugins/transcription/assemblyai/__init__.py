"""AssemblyAI speech-to-text backend.

Confirmed reachable, standard token-auth shape (clean 401 on a bad key)
via throwaway probe against the upload endpoint. Full job flow unverified
without a live key.

Three-step job flow (per AssemblyAI's documented API — no synchronous
"just give me text" endpoint exists):
  1. POST /v2/upload with raw audio bytes -> upload_url
  2. POST /v2/transcript with {audio_url: upload_url} -> job id
  3. Poll GET /v2/transcript/{id} until status is 'completed' or 'error'

PILOT SCOPE: happy path only. Poll timeout is generous (5 min) since
transcription jobs can take a while on longer audio; no retry/backoff
tuning beyond a fixed interval.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from agent.transcription_provider import TranscriptionProvider

logger = logging.getLogger(__name__)

_UPLOAD_URL = "https://api.assemblyai.com/v2/upload"
_TRANSCRIPT_URL = "https://api.assemblyai.com/v2/transcript"

_POLL_INTERVAL = 3.0
_MAX_POLL_SECONDS = 300.0


class AssemblyAITranscriptionProvider(TranscriptionProvider):
    """AssemblyAI speech-to-text via the async upload -> transcript -> poll flow."""

    @property
    def name(self) -> str:
        return "assemblyai"

    @property
    def display_name(self) -> str:
        return "AssemblyAI"

    def is_available(self) -> bool:
        return bool(os.environ.get("ASSEMBLYAI_API_KEY", "").strip())

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "AssemblyAI",
            "badge": "free",
            "tag": "~330 hours free",
            "env_vars": [
                {
                    "key": "ASSEMBLYAI_API_KEY",
                    "prompt": "AssemblyAI API key",
                    "url": "https://www.assemblyai.com/app/account",
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
        api_key = os.environ.get("ASSEMBLYAI_API_KEY", "").strip()
        if not api_key:
            return {
                "success": False,
                "transcript": "",
                "error": "ASSEMBLYAI_API_KEY is not set.",
                "provider": "assemblyai",
            }

        headers = {"authorization": api_key}

        try:
            with open(file_path, "rb") as fh:
                upload_resp = requests.post(
                    _UPLOAD_URL, headers=headers, data=fh, timeout=120,
                )
            upload_resp.raise_for_status()
            upload_url = upload_resp.json()["upload_url"]
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            return {
                "success": False,
                "transcript": "",
                "error": f"AssemblyAI upload failed ({status}): {resp.text[:300] if resp is not None else exc}",
                "provider": "assemblyai",
            }
        except (OSError, requests.RequestException, KeyError) as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"AssemblyAI upload failed: {exc}",
                "provider": "assemblyai",
            }

        job_payload: Dict[str, Any] = {"audio_url": upload_url}
        if language:
            job_payload["language_code"] = language

        try:
            create_resp = requests.post(
                _TRANSCRIPT_URL,
                headers={**headers, "content-type": "application/json"},
                json=job_payload,
                timeout=30,
            )
            create_resp.raise_for_status()
            job_id = create_resp.json()["id"]
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            return {
                "success": False,
                "transcript": "",
                "error": f"AssemblyAI job creation failed ({status}): {resp.text[:300] if resp is not None else exc}",
                "provider": "assemblyai",
            }
        except (requests.RequestException, KeyError) as exc:
            return {
                "success": False,
                "transcript": "",
                "error": f"AssemblyAI job creation failed: {exc}",
                "provider": "assemblyai",
            }

        poll_url = f"{_TRANSCRIPT_URL}/{job_id}"
        deadline = time.monotonic() + _MAX_POLL_SECONDS
        status = "queued"
        result: Dict[str, Any] = {}
        while time.monotonic() < deadline:
            try:
                poll_resp = requests.get(poll_url, headers=headers, timeout=30)
                poll_resp.raise_for_status()
                result = poll_resp.json()
            except requests.RequestException as exc:
                return {
                    "success": False,
                    "transcript": "",
                    "error": f"AssemblyAI polling failed: {exc}",
                    "provider": "assemblyai",
                }
            status = result.get("status", "")
            if status in {"completed", "error"}:
                break
            time.sleep(_POLL_INTERVAL)

        if status != "completed":
            err_detail = result.get("error") or f"final status: {status or 'timed out'}"
            return {
                "success": False,
                "transcript": "",
                "error": f"AssemblyAI transcription did not complete: {err_detail}",
                "provider": "assemblyai",
            }

        return {
            "success": True,
            "transcript": result.get("text", "") or "",
            "provider": "assemblyai",
        }


def register(ctx) -> None:
    """Plugin entry point — register the AssemblyAI STT provider."""
    ctx.register_transcription_provider(AssemblyAITranscriptionProvider())
