"""pollinations.ai image generation backend.

Exposes pollinations.ai (https://pollinations.ai) as an
:class:`ImageGenProvider` implementation.

Why this backend: it is **free and needs no API key** for the anonymous
tier, which makes it the always-reachable rung of the image-gen ladder
when OpenRouter / AI Studio / paid backends are unavailable.

Tiers
-----
- **Anonymous (no key)** — serves exactly ONE model, ``sana``
  (internally ``lykon/dreamshaper-8-lcm``). Every other ``model=`` value
  silently falls back to it. Accepts an ``image=`` reference but does NOT
  honour it; not usable when reference fidelity matters.
- **Registered (``POLLINATIONS_API_KEY``)** — unlocks the full catalogue
  (flux, kontext, gemini-*, flux.2-max, gptimage, ...). Free key from
  ``https://enter.pollinations.ai/keys``.

Selection precedence (first hit wins):
1. ``POLLINATIONS_IMAGE_MODEL`` env var
2. ``image_gen.pollinations.model`` in ``config.yaml``
3. ``image_gen.model`` in ``config.yaml`` (when it is one of our ids)
4. :data:`DEFAULT_MODEL`
"""

from __future__ import annotations

import base64
import logging
import os
import random
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote, urlencode

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

# ---------------------------------------------------------------------------
# Model catalog
# ---------------------------------------------------------------------------

_MODELS: Dict[str, Dict[str, Any]] = {
    # --- anonymous tier: the ONLY model served without a key ---
    "sana": {
        "display": "Sana (Dreamshaper-8-LCM) — free, no key",
        "speed": "~2-10s",
        "strengths": "Free anonymous tier. Weak prompt adherence, ignores reference images.",
        "key_required": False,
    },
    # --- registered tier ---
    "flux": {
        "display": "FLUX (schnell)",
        "speed": "~5-15s",
        "strengths": "Fast, good general fidelity.",
        "key_required": True,
    },
    "flux.2-max": {
        "display": "FLUX.2 Max",
        "speed": "~20-60s",
        "strengths": "Accepts up to 8 reference images in one call. Best for re-skins.",
        "key_required": True,
    },
    "kontext": {
        "display": "FLUX Kontext",
        "speed": "~10-30s",
        "strengths": "Purpose-built image editing / reference-conditioned variation.",
        "key_required": True,
    },
    "turbo": {
        "display": "Turbo",
        "speed": "~2-5s",
        "strengths": "Cheapest and fastest; lower detail.",
        "key_required": True,
    },
    "gemini": {
        "display": "Gemini (Nano Banana)",
        "speed": "~8-20s",
        "strengths": "Strong architectural reasoning + reference editing.",
        "key_required": True,
    },
    "gemini-3.1-flash-lite-image": {
        "display": "Gemini 3.1 Flash Lite Image",
        "speed": "~6-15s",
        "strengths": "Cheapest capable reference-image model (~0.3 paise/img).",
        "key_required": True,
    },
    "gptimage": {
        "display": "GPT Image",
        "speed": "~15-40s",
        "strengths": "Strong prompt adherence.",
        "key_required": True,
    },
}

DEFAULT_MODEL = "sana"

# Pollinations is pixel-dimension based, not aspect-ratio based.
_SIZES: Dict[str, Tuple[int, int]] = {
    "landscape": (1280, 960),
    "square": (1024, 1024),
    "portrait": (960, 1280),
}

_BASE_URL = "https://image.pollinations.ai/prompt/"

# JPEG SOI, PNG signature, RIFF (webp) — anything else means we got JSON/HTML.
_MAGIC_OK = (b"\xff\xd8", b"\x89PNG", b"RIFF")

_UA = "hermes-agent/pollinations-image-gen"


class PollinationsImageGenProvider(ImageGenProvider):
    """pollinations.ai backend — free anonymous tier, keyed tier optional."""

    @property
    def name(self) -> str:
        return "pollinations"

    @property
    def display_name(self) -> str:
        return "Pollinations.ai"

    # -- capability ---------------------------------------------------------

    def is_available(self) -> bool:
        """Always available: the anonymous tier needs no credential."""
        return True

    def has_key(self) -> bool:
        return bool(os.environ.get("POLLINATIONS_API_KEY"))

    def list_models(self) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for model_id, meta in _MODELS.items():
            out.append(
                {
                    "id": model_id,
                    "display": meta.get("display", model_id),
                    "speed": meta.get("speed", ""),
                    "strengths": meta.get("strengths", ""),
                    "price": "free" if not meta.get("key_required") else "free key required",
                }
            )
        return out

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Pollinations.ai",
            "badge": "free",
            "tag": (
                "Free image generation. No key needed for the anonymous tier "
                "(model: sana). Add a free key from enter.pollinations.ai/keys "
                "to unlock flux, kontext and the gemini image models."
            ),
            "env_vars": [
                {
                    "key": "POLLINATIONS_API_KEY",
                    "prompt": "Pollinations API key (optional — anonymous tier works without one)",
                    "url": "https://enter.pollinations.ai/keys",
                }
            ],
        }

    def default_model(self) -> Optional[str]:
        return self._resolve_model()

    # -- model resolution ---------------------------------------------------

    def _resolve_model(self) -> str:
        env_model = (os.environ.get("POLLINATIONS_IMAGE_MODEL") or "").strip()
        if env_model:
            return env_model
        try:
            from hermes_constants import load_config

            cfg = load_config() or {}
            section = cfg.get("image_gen") if isinstance(cfg, dict) else None
            if isinstance(section, dict):
                sub = section.get("pollinations")
                if isinstance(sub, dict) and sub.get("model"):
                    return str(sub["model"]).strip()
                top = section.get("model")
                if isinstance(top, str) and top.strip() in _MODELS:
                    return top.strip()
        except Exception as exc:  # noqa: BLE001
            logger.debug("pollinations: config model lookup failed: %s", exc)
        return DEFAULT_MODEL

    # -- generation ---------------------------------------------------------

    def generate(
        self,
        prompt: str,
        aspect_ratio: str = DEFAULT_ASPECT_RATIO,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        aspect = resolve_aspect_ratio(aspect_ratio)

        model = (
            kwargs.get("model")
            or kwargs.get("image_model")
            or self._resolve_model()
        )
        model = str(model).strip() or DEFAULT_MODEL

        width = kwargs.get("width")
        height = kwargs.get("height")
        if not (isinstance(width, int) and isinstance(height, int)):
            width, height = _SIZES[aspect]

        seed = kwargs.get("seed")
        if seed is None:
            seed = random.randint(1, 2_147_483_647)

        reference = kwargs.get("image") or kwargs.get("reference_image")

        params: Dict[str, Any] = {
            "width": width,
            "height": height,
            "seed": seed,
            "model": model,
            "nologo": "true",
        }
        if kwargs.get("enhance") is not None:
            params["enhance"] = "true" if kwargs.get("enhance") else "false"
        if reference:
            # Pollinations expects a publicly reachable URL for img2img.
            params["image"] = reference

        url = _BASE_URL + quote(str(prompt), safe="") + "?" + urlencode(params)

        headers = {"User-Agent": _UA, "Accept": "image/*"}
        key = os.environ.get("POLLINATIONS_API_KEY")
        if key:
            headers["Authorization"] = f"Bearer {key}"

        last_error = ""
        for attempt in range(1, 4):
            try:
                response = requests.get(url, headers=headers, timeout=180)
            except requests.RequestException as exc:
                last_error = f"transport error: {exc}"
                logger.warning("pollinations attempt %d failed: %s", attempt, last_error)
                continue

            if response.status_code != 200:
                last_error = (
                    f"HTTP {response.status_code}: "
                    f"{response.text[:300].strip() or 'no body'}"
                )
                # 401/402/403 are terminal — no point retrying.
                if response.status_code in (401, 402, 403, 404):
                    break
                logger.warning(
                    "pollinations attempt %d: %s", attempt, last_error
                )
                continue

            raw = response.content or b""
            if not raw.startswith(_MAGIC_OK):
                last_error = (
                    "non-image payload returned (expected JPEG/PNG/WEBP); "
                    f"first bytes={raw[:40]!r}"
                )
                logger.warning("pollinations attempt %d: %s", attempt, last_error)
                continue

            extension = "jpg"
            if raw.startswith(b"\x89PNG"):
                extension = "png"
            elif raw.startswith(b"RIFF"):
                extension = "webp"

            try:
                path = save_b64_image(
                    base64.b64encode(raw).decode("ascii"),
                    prefix="pollinations",
                    extension=extension,
                )
            except Exception as exc:  # noqa: BLE001
                return error_response(
                    error=f"could not cache generated image: {exc}",
                    error_type="cache_error",
                    provider=self.name,
                    model=model,
                    prompt=prompt,
                    aspect_ratio=aspect,
                )

            return success_response(
                image=str(path),
                model=model,
                prompt=prompt,
                aspect_ratio=aspect,
                provider=self.name,
                extra={
                    "seed": seed,
                    "width": width,
                    "height": height,
                    "anonymous": not bool(key),
                    "source_url": url,
                },
            )

        return error_response(
            error=last_error or "pollinations generation failed",
            error_type="provider_error",
            provider=self.name,
            model=model,
            prompt=prompt,
            aspect_ratio=aspect,
        )


# ---------------------------------------------------------------------------
# Plugin entry point
# ---------------------------------------------------------------------------


def register(ctx) -> None:
    """Plugin entry point — wire PollinationsImageGenProvider into the registry."""
    ctx.register_image_gen_provider(PollinationsImageGenProvider())
