"""Amazon Polly text-to-speech backend.

Structurally different from every other provider in this batch: Polly
uses AWS SigV4-signed requests via boto3's default credential chain
(env vars AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY, ~/.aws/credentials,
or IAM role) — not a simple bearer-token API key. Confirmed via
throwaway probe that an unsigned request gets AWS API Gateway's generic
"Missing Authentication Token" (403), which is expected and doesn't by
itself validate the Polly-specific request shape below.

Lazy-imports boto3 following the exact pattern already established for
the Bedrock provider (agent/bedrock_adapter.py::_require_boto3) — boto3
stays an optional dependency, not a hard requirement for users who don't
touch AWS-backed features.

PILOT SCOPE: standard (non-neural) voice synthesis, single synchronous
call. No SSML validation, no neural/generative engine selection beyond
a hardcoded default.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

from agent.tts_provider import DEFAULT_OUTPUT_FORMAT, TTSProvider, resolve_output_format

logger = logging.getLogger(__name__)

DEFAULT_VOICE = "Joanna"
DEFAULT_REGION = "us-east-1"

_FORMAT_BY_OUTPUT = {
    "mp3": "mp3",
    "wav": "pcm",  # Polly's raw PCM isn't a WAV container; closest available match.
    "ogg": "ogg_vorbis",
}


def _require_boto3():
    """Import boto3, raising a clear error if not installed. Mirrors
    agent.bedrock_adapter._require_boto3 for a consistent error message
    shape across Hermes's two AWS-backed features."""
    try:
        import boto3
        return boto3
    except ImportError:
        raise ImportError(
            "The 'boto3' package is required for the Amazon Polly TTS provider. "
            "Install it with: pip install boto3"
        )


class PollyTTSProvider(TTSProvider):
    """Amazon Polly text-to-speech via boto3."""

    @property
    def name(self) -> str:
        return "polly"

    @property
    def display_name(self) -> str:
        return "Amazon Polly"

    def is_available(self) -> bool:
        try:
            boto3 = _require_boto3()
        except ImportError:
            return False
        try:
            session = boto3.Session()
            return session.get_credentials() is not None
        except Exception:
            return False

    def list_voices(self) -> List[Dict[str, Any]]:
        return [
            {"id": "Joanna", "display": "Joanna (US English, female)", "language": "en-US", "gender": "female"},
            {"id": "Matthew", "display": "Matthew (US English, male)", "language": "en-US", "gender": "male"},
        ]

    def default_voice(self) -> Optional[str]:
        return DEFAULT_VOICE

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Amazon Polly",
            "badge": "free",
            "tag": "5M chars/month free for 12 months — needs AWS credentials, not a simple API key",
            "env_vars": [
                {
                    "key": "AWS_ACCESS_KEY_ID",
                    "prompt": "AWS access key ID",
                    "url": "https://console.aws.amazon.com/iam/home#/security_credentials",
                },
                {
                    "key": "AWS_SECRET_ACCESS_KEY",
                    "prompt": "AWS secret access key",
                    "url": "https://console.aws.amazon.com/iam/home#/security_credentials",
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
        boto3 = _require_boto3()

        fmt = resolve_output_format(format)
        polly_format = _FORMAT_BY_OUTPUT.get(fmt, "mp3")
        region = os.environ.get("AWS_REGION", "").strip() or DEFAULT_REGION

        try:
            client = boto3.client("polly", region_name=region)
            response = client.synthesize_speech(
                Text=text,
                OutputFormat=polly_format,
                VoiceId=voice or DEFAULT_VOICE,
            )
        except Exception as exc:
            raise RuntimeError(f"Amazon Polly synthesis failed: {exc}") from exc

        audio_stream = response.get("AudioStream")
        if audio_stream is None:
            raise RuntimeError("Amazon Polly returned no AudioStream")

        with open(output_path, "wb") as fh:
            fh.write(audio_stream.read())

        return output_path


def register(ctx) -> None:
    """Plugin entry point — register the Amazon Polly TTS provider."""
    ctx.register_tts_provider(PollyTTSProvider())
