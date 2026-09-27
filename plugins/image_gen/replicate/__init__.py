"""Replicate image generation backend — FLUX schnell.

UNVERIFIED beyond reachability: confirmed host/auth shape (clean 401 on bad
token, no billing surprise like SambaNova). Job lifecycle and output shape
below are per Replicate's documented API, not confirmed against a real key.

Uses the official-model shorthand endpoint
(``/v1/models/{owner}/{name}/predictions``) instead of pinning a version
hash — avoids the code silently going stale when Replicate publishes a new
version of the model. ``Prefer: wait=60`` asks Replicate to hold the HTTP
connection open and return once the job finishes (documented behavior, up
to 60s); if the job is still running after that, falls back to polling
``urls.get`` for up to another 60s.

Replicate's ``$5 signup credit`` is one-time, not recurring — track
consumption if using regularly.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, List, Optional

import requests

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_url_image,
    success_response,
)

logger = logging.getLogger(__name__)

_MODEL_OWNER = "black-forest-labs"
_MODEL_NAME = "flux-schnell"
_BASE_URL = f"https://api.replicate.com/v1/models/{_MODEL_OWNER}/{_MODEL_NAME}/predictions"

DEFAULT_MODEL = f"{_MODEL_OWNER}/{_MODEL_NAME}"

_ASPECT_RATIOS = {
    "landscape": "16:9",
    "square": "1:1",
    "portrait": "9:16",
}

_POLL_INTERVAL = 2.0
_MAX_POLL_SECONDS = 60.0


class ReplicateImageGenProvider(ImageGenProvider):
    """FLUX schnell via Replicate's official-model endpoint."""

    @property
    def name(self) -> str:
        return "replicate"

    @property
    def display_name(self) -> str:
        return "Replicate (FLUX schnell)"

    def is_available(self) -> bool:
        return bool(os.environ.get("REPLICATE_API_TOKEN", "").strip())

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": DEFAULT_MODEL,
                "display": "FLUX schnell",
                "speed": "~2-5s",
                "strengths": "Fast, $5 one-time free credit (no CC)",
                "price": "~$0.003/image",
            }
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Replicate (FLUX schnell)",
            "badge": "free",
            "tag": "$5 one-time free credit, no credit card required at signup",
            "env_vars": [
                {
                    "key": "REPLICATE_API_TOKEN",
                    "prompt": "Replicate API token",
                    "url": "https://replicate.com/account/api-tokens",
                },
            ],
        }

    def _poll_until_done(
        self, get_url: str, headers: Dict[str, str], deadline: float
    ) -> Dict[str, Any]:
        """Poll a prediction's ``urls.get`` until it leaves 'starting'/'processing'."""
        last: Dict[str, Any] = {}
        while time.monotonic() < deadline:
            resp = requests.get(get_url, headers=headers, timeout=30)
            resp.raise_for_status()
            last = resp.json()
            if last.get("status") not in {"starting", "processing"}:
                return last
            time.sleep(_POLL_INTERVAL)
        return last

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        prompt = (prompt or "").strip()
        aspect = resolve_aspect_ratio(aspect_ratio)

        api_token = os.environ.get("REPLICATE_API_TOKEN", "").strip()
        if not api_token:
            return error_response(
                error="REPLICATE_API_TOKEN is not set.",
                error_type="missing_api_key",
                provider="replicate",
                aspect_ratio=aspect,
            )

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="replicate",
                aspect_ratio=aspect,
            )

        replicate_ar = _ASPECT_RATIOS.get(aspect, "16:9")
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Prefer": "wait=60",
        }
        payload = {
            "input": {
                "prompt": prompt,
                "aspect_ratio": replicate_ar,
                "output_format": "png",
            }
        }

        try:
            response = requests.post(_BASE_URL, headers=headers, json=payload, timeout=70)
            response.raise_for_status()
        except requests.HTTPError as exc:
            resp = exc.response
            status = resp.status_code if resp is not None else 0
            try:
                err_msg = resp.json().get("detail", resp.text[:300])
            except Exception:
                err_msg = resp.text[:300] if resp is not None else str(exc)
            return error_response(
                error=f"Replicate prediction failed ({status}): {err_msg}",
                error_type="api_error",
                provider="replicate",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )
        except (requests.Timeout, requests.ConnectionError) as exc:
            return error_response(
                error=f"Replicate request failed: {exc}",
                error_type="connection_error",
                provider="replicate",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            prediction = response.json()
        except Exception as exc:
            return error_response(
                error=f"Replicate returned invalid JSON: {exc}",
                error_type="invalid_response",
                provider="replicate",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        status = prediction.get("status")
        if status in {"starting", "processing"}:
            get_url = (prediction.get("urls") or {}).get("get")
            if get_url:
                deadline = time.monotonic() + _MAX_POLL_SECONDS
                prediction = self._poll_until_done(get_url, headers, deadline)
                status = prediction.get("status")

        if status != "succeeded":
            err_detail = prediction.get("error") or f"final status: {status}"
            return error_response(
                error=f"Replicate prediction did not succeed: {err_detail}",
                error_type="generation_failed",
                provider="replicate",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        output = prediction.get("output")
        # flux-schnell's documented output is a list of image URLs; handle a
        # bare string too in case a future version simplifies the shape.
        image_url: Optional[str] = None
        if isinstance(output, list) and output:
            image_url = output[0]
        elif isinstance(output, str):
            image_url = output

        if not image_url:
            return error_response(
                error="Replicate succeeded but returned no output URL",
                error_type="empty_response",
                provider="replicate",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        try:
            saved_path = save_url_image(image_url, prefix="replicate_flux")
        except Exception as exc:
            return error_response(
                error=f"Could not save image to cache: {exc}",
                error_type="io_error",
                provider="replicate",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        return success_response(
            image=str(saved_path),
            model=DEFAULT_MODEL,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="replicate",
            extra={"aspect_ratio_native": replicate_ar},
        )


def register(ctx) -> None:
    """Plugin entry point — register the Replicate image-gen provider."""
    ctx.register_image_gen_provider(ReplicateImageGenProvider())
