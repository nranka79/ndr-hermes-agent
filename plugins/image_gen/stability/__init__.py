"""Stability AI image generation backend — Stable Image Core (v2beta).

UNVERIFIED beyond reachability: confirmed the endpoint/host is live and
returns a clean 401 on a bad key (no surprise billing gate like SambaNova
hit). The exact request shape below (multipart/form-data, Accept header
switching between raw-bytes and JSON) is per Stability's v2beta docs, not
confirmed against a real key — Stability's free tier grants a small
one-time credit balance, not a recurring free quota, so treat first live
call as the real test.

v2beta's ``/v2beta/stable-image/generate/core`` endpoint:
- Requires multipart/form-data (not JSON) — hence the ``files={"none": ""}``
  trick to force ``requests`` into multipart encoding for a fields-only body.
- ``Accept: image/*`` returns the raw image bytes directly in the response
  body (what this provider uses, via ``save_raw_image_bytes``).
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, List, Optional

import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_raw_image_bytes,
    success_response,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.stability.ai/v2beta/stable-image/generate/core"

DEFAULT_MODEL = "stable-image-core"

_ASPECT_RATIOS = {
    "landscape": "16:9",
    "square": "1:1",
    "portrait": "9:16",
}


class StabilityImageGenProvider(ImageGenProvider):
    """Stable Image Core via Stability AI's v2beta REST API."""

    @property
    def name(self) -> str:
        return "stability"

    @property
    def display_name(self) -> str:
        return "Stability AI (Stable Image Core)"

    def is_available(self) -> bool:
        return bool(os.environ.get("STABILITY_API_KEY", "").strip())

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": DEFAULT_MODEL,
                "display": "Stable Image Core",
                "speed": "~3-5s",
                "strengths": "Fast, general-purpose",
                "price": "3 credits/image (25 free credits/mo)",
            }
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Stability AI",
            "badge": "free",
            "tag": "Stable Image Core — 25 free credits/month",
            "env_vars": [
                {
                    "key": "STABILITY_API_KEY",
                    "prompt": "Stability AI API key",
                    "url": "https://platform.stability.ai/account/keys",
                },
            ],
        }

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)

        api_key = os.environ.get("STABILITY_API_KEY", "").strip()
        if not api_key:
            return error_response(
                error="STABILITY_API_KEY is not set.",
                error_type="missing_api_key",
                provider="stability",
                aspect_ratio=aspect,
            )

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="stability",
                aspect_ratio=aspect,
            )

        stability_ar = _ASPECT_RATIOS.get(aspect, "16:9")
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "image/*",
        }
        data = {
            "prompt": prompt,
            "aspect_ratio": stability_ar,
            "output_format": "png",
        }

        try:
            response = requests.post(
                _BASE_URL,
                headers=headers,
                files={"none": ""},
                data=data,
                timeout=60,
            )
            response.raise_for_status()
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            try:
                err_msg = "; ".join(resp.json().get("errors", [resp.text[:300]]))
            except Exception:
                err_msg = resp.text[:300] if resp is not None else str(exc)
            return error_response(
                error=f"Stability image generation failed ({status}): {err_msg}",
                error_type="api_error",
                provider="stability",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            return error_response(
                error=f"Stability request failed: {exc}",
                error_type="connection_error",
                provider="stability",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        content_type = (response.headers.get("Content-Type") or "").split(";", 1)[0].strip().lower()
        if not content_type.startswith("image/"):
            snippet = response.text[:300]
            return error_response(
                error=f"Stability did not return an image (content-type={content_type or 'unknown'}): {snippet}",
                error_type="invalid_response",
                provider="stability",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            saved_path = save_raw_image_bytes(response.content, prefix="stability_core")
        except Exception as exc:
            return error_response(
                error=f"Could not save image to cache: {exc}",
                error_type="io_error",
                provider="stability",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        return success_response(
            image=str(saved_path),
            model=DEFAULT_MODEL,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="stability",
            extra={"aspect_ratio_native": stability_ar},
        )


def register(ctx) -> None:
    """Plugin entry point — register the Stability AI image-gen provider."""
    ctx.register_image_gen_provider(StabilityImageGenProvider())
