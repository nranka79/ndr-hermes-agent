"""Pollinations.ai image generation backend — free, works with or without a key.

Pollinations serves images directly off a GET URL:

    https://image.pollinations.ai/prompt/<url-encoded-prompt>?params...

The URL *is* the generation call — no submit/poll cycle, no auth header.
Response is a raw image (JPEG/PNG), not JSON/base64, so this provider uses
``save_url_image`` (not ``save_b64_image``) to materialize it under
``$HERMES_HOME/cache/images/``.

A random ``seed`` is attached to every call because Pollinations' CDN caches
identical URLs — without it, repeated prompts would return the same cached
image instead of a fresh generation.

Optional ``token`` query param (``POLLINATIONS_API_KEY``): confirmed live
that both keyed and anonymous requests succeed identically — Pollinations
works with zero setup. The token is attached when present because
Pollinations documents it as raising rate-limit/priority tier; it is NOT
required and this provider stays ``is_available() == True`` regardless.

CONFIRMED GOTCHA (live-tested, both with and without a token): requesting
1024x1024 consistently returns a 768x768 image — the free tier silently
clamps size rather than erroring. Not fixable client-side; documented here
so it isn't mistaken for a bug in this plugin.

PILOT SCOPE: single model ("flux"), no retry logic beyond what
``save_url_image`` already provides, no rate-limit backoff.
"""

from __future__ import annotations

import logging
import os
import random
from typing import Any, Dict, List, Optional
from urllib.parse import quote

from agent.image_gen_provider import (
    DEFAULT_ASPECT_RATIO,
    ImageGenProvider,
    error_response,
    resolve_aspect_ratio,
    save_url_image,
    success_response,
)

logger = logging.getLogger(__name__)

_BASE_URL = "https://image.pollinations.ai/prompt"

_SIZES = {
    "landscape": (1024, 576),
    "square": (1024, 1024),
    "portrait": (576, 1024),
}

DEFAULT_MODEL = "flux"


class PollinationsImageGenProvider(ImageGenProvider):
    """Free image generation via image.pollinations.ai — no key required."""

    @property
    def name(self) -> str:
        return "pollinations"

    @property
    def display_name(self) -> str:
        return "Pollinations (free, key optional)"

    def is_available(self) -> bool:
        try:
            import requests  # noqa: F401
        except ImportError:
            return False
        return True

    def list_models(self) -> List[Dict[str, Any]]:
        return [
            {
                "id": DEFAULT_MODEL,
                "display": "Flux",
                "speed": "~5-10s",
                "strengths": "Free, unlimited, no key required (key optional for higher rate limits)",
                "price": "$0",
            }
        ]

    def default_model(self) -> Optional[str]:
        return DEFAULT_MODEL

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Pollinations",
            "badge": "free",
            "tag": "Unlimited image generation — works with zero setup; optional key raises rate limits",
            "env_vars": [
                {
                    "key": "POLLINATIONS_API_KEY",
                    "prompt": "Pollinations API key (optional — leave blank to use anonymously)",
                    "url": "https://auth.pollinations.ai/",
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

        if not prompt:
            return error_response(
                error="Prompt is required and must be a non-empty string",
                error_type="invalid_argument",
                provider="pollinations",
                aspect_ratio=aspect,
            )

        width, height = _SIZES.get(aspect, _SIZES["landscape"])
        seed = random.randint(0, 2**31 - 1)
        url = (
            f"{_BASE_URL}/{quote(prompt)}"
            f"?width={width}&height={height}&nologo=true&seed={seed}&model={DEFAULT_MODEL}"
        )

        api_key = os.environ.get("POLLINATIONS_API_KEY", "").strip()
        if api_key:
            url += f"&token={api_key}"

        try:
            saved_path = save_url_image(url, prefix="pollinations")
        except Exception as exc:
            logger.debug("Pollinations image generation failed", exc_info=True)
            return error_response(
                error=f"Pollinations image generation failed: {exc}",
                error_type="api_error",
                provider="pollinations",
                model=DEFAULT_MODEL,
                prompt=prompt,
                aspect_ratio=aspect,
            )

        return success_response(
            image=str(saved_path),
            model=DEFAULT_MODEL,
            prompt=prompt,
            aspect_ratio=aspect,
            provider="pollinations",
            extra={"width": width, "height": height, "seed": seed, "keyed": bool(api_key)},
        )


def register(ctx) -> None:
    """Plugin entry point — register the Pollinations image-gen provider."""
    ctx.register_image_gen_provider(PollinationsImageGenProvider())
