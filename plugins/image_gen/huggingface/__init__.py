"""Hugging Face image generation backend — Inference Providers gateway.

CORRECTED after live testing (2026-09-26): the original implementation
targeted the legacy direct-hosting API
(``router.huggingface.co/hf-inference/models/<id>``), which turned out to
be dead for every popular text-to-image model — confirmed live with a
real token: FLUX.1-schnell, FLUX.1-dev, and SD 3.5 Large all returned
410/400 "deprecated"/"not supported by provider hf-inference".

HF has moved image generation to an OpenAI-images-compatible gateway that
fans out to third-party inference providers (nscale, fal-ai, wavespeed,
together, ...). Confirmed live and working:

    POST https://router.huggingface.co/nscale/v1/images/generations
    {"model": "black-forest-labs/FLUX.1-schnell", "prompt": "...",
     "response_format": "b64_json"}
    -> {"data": [{"b64_json": "..."}]}  (real 1024x1024 PNG verified)

``nscale`` was picked as the provider because HF's own
``inferenceProviderMapping`` for FLUX.1-schnell lists it (along with
fal-ai and wavespeed) as ``"status": "live"`` — ``together`` was listed
as ``"status": "error"`` at the time of testing, so it's deliberately not
used here despite otherwise being a natural fit.

Reuses ``HF_TOKEN`` (same env var models.dev lists for the ``huggingface``
LLM provider).
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
    success_response,
)

logger = logging.getLogger(__name__)

_PROVIDER = "nscale"
_BASE_URL = f"https://router.huggingface.co/{_PROVIDER}/v1/images/generations"
_MODEL = "black-forest-labs/FLUX.1-schnell"


class HuggingFaceImageGenProvider(ImageGenProvider):
    """FLUX.1-schnell via Hugging Face's Inference Providers gateway (nscale)."""

    @property
    def name(self) -> str:
        return "huggingface"

    @property
    def display_name(self) -> str:
        return "Hugging Face (FLUX, free)"

    def is_available(self) -> bool:
        return bool(os.environ.get("HF_TOKEN", "").strip())

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": _MODEL,
                "display": "FLUX.1 schnell (via nscale)",
                "speed": "~5-10s",
                "strengths": "Free via HF Inference Providers, reuses HF_TOKEN",
                "price": "$0",
            }
        ]

    def default_model(self) -> Optional[str]:
        return _MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Hugging Face (FLUX, free)",
            "badge": "free",
            "tag": "FLUX.1-schnell via HF Inference Providers — reuses HF_TOKEN from LLM setup",
            "env_vars": [
                {
                    "key": "HF_TOKEN",
                    "prompt": "Hugging Face access token",
                    "url": "https://huggingface.co/settings/tokens",
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

        api_key = os.environ.get("HF_TOKEN", "").strip()
        if not api_key:
            return error_response(
                error="HF_TOKEN is not set.",
                error_type="missing_api_key",
                provider="huggingface",
                aspect_ratio=aspect,
            )

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="huggingface",
                aspect_ratio=aspect,
            )

        payload = {
            "model": _MODEL,
            "prompt": prompt,
            "response_format": "b64_json",
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(_BASE_URL, headers=headers, json=payload, timeout=90)
            response.raise_for_status()
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            try:
                err_msg = resp.json().get("error", resp.text[:300])
            except Exception:
                err_msg = resp.text[:300] if resp is not None else str(exc)
            return error_response(
                error=f"Hugging Face image generation failed ({status}): {err_msg}",
                error_type="api_error",
                provider="huggingface",
                model=_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            return error_response(
                error=f"Hugging Face request failed: {exc}",
                error_type="connection_error",
                provider="huggingface",
                model=_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            result = response.json()
            b64 = result["data"][0]["b64_json"]
        except Exception as exc:
            return error_response(
                error=f"Hugging Face returned an unexpected response shape: {exc}",
                error_type="invalid_response",
                provider="huggingface",
                model=_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            saved_path = save_b64_image(b64, prefix="hf_flux")
        except Exception as exc:
            return error_response(
                error=f"Could not save image to cache: {exc}",
                error_type="io_error",
                provider="huggingface",
                model=_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        return success_response(
            image=str(saved_path),
            model=_MODEL,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="huggingface",
            extra={"inference_provider": _PROVIDER},
        )


def register(ctx) -> None:
    """Plugin entry point — register the Hugging Face image-gen provider."""
    ctx.register_image_gen_provider(HuggingFaceImageGenProvider())
