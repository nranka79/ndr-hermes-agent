"""Together AI image generation backend.

Uses FLUX.1-schnell-Free — Together's no-cost FLUX tier. Reuses
``TOGETHER_API_KEY`` (the same env var the ``togetherai`` LLM provider
already uses), so anyone with a Together account has this working with
zero extra setup.

Response shape confirmed reachable via unauthenticated probe (401 +
standard OpenAI-images-style error envelope) — real generation call
unverified without a live key.
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
    save_b64_image,
    save_url_image,
    success_response,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://api.together.xyz/v1/images/generations"

DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell-Free"

_SIZES = {
    "landscape": (1024, 576),
    "square": (1024, 1024),
    "portrait": (576, 1024),
}


class TogetherImageGenProvider(ImageGenProvider):
    """FLUX.1-schnell-Free via Together AI's free tier."""

    @property
    def name(self) -> str:
        return "together"

    @property
    def display_name(self) -> str:
        return "Together AI (FLUX, free tier)"

    def is_available(self) -> bool:
        return bool(os.environ.get("TOGETHER_API_KEY", "").strip())

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": DEFAULT_MODEL,
                "display": "FLUX.1 schnell (Free)",
                "speed": "~3-6s",
                "strengths": "Free tier, no extra key if you already use Together for LLM",
                "price": "$0",
            }
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Together AI (FLUX, free)",
            "badge": "free",
            "tag": "FLUX.1-schnell-Free — reuses TOGETHER_API_KEY from LLM setup",
            "env_vars": [
                {
                    "key": "TOGETHER_API_KEY",
                    "prompt": "Together AI API key",
                    "url": "https://api.together.ai/settings/api-keys",
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

        api_key = os.environ.get("TOGETHER_API_KEY", "").strip()
        if not api_key:
            return error_response(
                error="TOGETHER_API_KEY is not set.",
                error_type="missing_api_key",
                provider="together",
                aspect_ratio=aspect,
            )

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="together",
                aspect_ratio=aspect,
            )

        width, height = _SIZES.get(aspect, _SIZES["landscape"])
        payload = {
            "model": DEFAULT_MODEL,
            "prompt": prompt,
            "width": width,
            "height": height,
            "steps": 4,
            "n": 1,
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(_BASE_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            try:
                err_msg = resp.json().get("error", {}).get("message", resp.text[:300])
            except Exception:
                err_msg = resp.text[:300] if resp is not None else str(exc)
            return error_response(
                error=f"Together image generation failed ({status}): {err_msg}",
                error_type="api_error",
                provider="together",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            return error_response(
                error=f"Together request failed: {exc}",
                error_type="connection_error",
                provider="together",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            result = response.json()
        except Exception as exc:
            return error_response(
                error=f"Together returned invalid JSON: {exc}",
                error_type="invalid_response",
                provider="together",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        data = result.get("data", [])
        if not data:
            return error_response(
                error="Together returned no image data",
                error_type="empty_response",
                provider="together",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        first = data[0]
        b64 = first.get("b64_json")
        url = first.get("url")

        try:
            if b64:
                saved_path = save_b64_image(b64, prefix="together_flux")
            elif url:
                saved_path = save_url_image(url, prefix="together_flux")
            else:
                return error_response(
                    error="Together response contained neither b64_json nor url",
                    error_type="empty_response",
                    provider="together",
                    model=DEFAULT_MODEL,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )
        except Exception as exc:
            return error_response(
                error=f"Could not save image to cache: {exc}",
                error_type="io_error",
                provider="together",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        return success_response(
            image=str(saved_path),
            model=DEFAULT_MODEL,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="together",
            extra={"width": width, "height": height},
        )


def register(ctx) -> None:
    """Plugin entry point — register the Together image-gen provider."""
    ctx.register_image_gen_provider(TogetherImageGenProvider())
