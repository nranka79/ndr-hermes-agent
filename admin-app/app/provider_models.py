"""Per-provider model catalogs for the keys-admin bucket forms.

Feeds the Model dropdown on admin.ahfl.in/keys-admin. Kept out of key_admin.py
so the catalogs can be regenerated wholesale by
``scripts/refresh-model-catalogs.py`` without touching routing logic.

Entry shape::

    {"id": "<model string sent upstream>",
     "vision": True,          # optional — accepts OpenAI image_url parts
     "note": "short label"}   # optional — shown after the id in the <option>

Only ``vision`` entries are offered in the multimodal buckets (multi_free /
multi_subscription / multi_token); the text buckets offer everything.

A provider absent from CATALOG (or mapped to an empty list) renders as
"Custom…" only, which is exactly the pre-dropdown behaviour — that is the
intended state for openorca / openai-compatible, where the model name depends
on whatever endpoint the operator points at.

NVIDIA NIM caveat (measured 2026-09-26, not inferred from docs)
---------------------------------------------------------------
``GET https://integrate.api.nvidia.com/v1/models`` answers 200 *without* auth
and lists ~82 ids, but that is a catalog, not an entitlement list: an account
may only call the models badged "Free Endpoint" on build.nvidia.com. Every
other id answers ``404 {"detail": "Function '<uuid>': Not found for account
'<hash>'"}``. The badge does not follow model-name patterns either —
``google/gemma-4-31b-it`` is entitled while ``google/gemma-3-12b-it`` 404s — so
the list below is the verified intersection (build.nvidia.com "Free Endpoint"
facet AND present on the /v1/chat/completions surface), minus four
classifier/embedder NIMs that are not chat models
(meta/llama-guard-4-12b, nvidia/llama-3.1-nemotron-safety-guard-8b-v3,
nvidia/nemotron-3.5-content-safety, nvidia/nemotron-3-embed-1b).

Every id below was swept with a real nvapi- key: none 404'd. The four marked
vision were checked with an OpenAI-style image_url data: URL —
meta/llama-3.2-11b-vision-instruct correctly described the test image, so these
NIMs take the same message shape the gateway's multimodal path already sends
(older NVIDIA VLMs required an inline <img src="data:..."> tag; these do not).
"""

from __future__ import annotations

CATALOG: dict[str, list[dict]] = {
    "nvidia": [
        # -- general chat / reasoning -------------------------------------
        {"id": "deepseek-ai/deepseek-v4.1-flash", "note": "fast, tool use"},
        {"id": "z-ai/glm-5.3"},
        {"id": "z-ai/glm-5.3-flash", "note": "fast"},
        {"id": "moonshotai/kimi-k3"},
        {"id": "openai/gpt-oss-20b"},
        {"id": "nvidia/nemotron-3-ultra-550b-a55b", "note": "largest, slowest"},
        {"id": "nvidia/nemotron-3-super-120b-a12b"},
        {"id": "nvidia/nemotron-3.5-lightning-30b-a3b", "note": "fast"},
        {"id": "mistralai/mistral-nemotron"},
        {"id": "meta/muse-glimmer-30b"},
        {"id": "poolside/laguna-xs-2.1", "note": "coding"},
        {"id": "google/diffusiongemma-26b-a4b-it", "note": "diffusion LLM"},
        # -- domain specific ----------------------------------------------
        {"id": "nvidia/riva-translate-4b-instruct-v2", "note": "translation only"},
        {"id": "nvidia/riva-translate-4b-instruct-v1.1", "note": "translation only"},
        # A vision-language model, but trained for quantum-calibration
        # readouts — deliberately NOT flagged vision so it does not surface as
        # a general-purpose choice in the multimodal buckets.
        {"id": "nvidia/ising-calibration-1.5-31b", "note": "quantum calibration"},
        # -- vision / multimodal ------------------------------------------
        {"id": "meta/llama-3.2-11b-vision-instruct", "vision": True, "note": "fast vision"},
        {"id": "meta/llama-3.2-90b-vision-instruct", "vision": True},
        {"id": "google/gemma-4-31b-it", "vision": True},
        {"id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning", "vision": True, "note": "omni"},
    ],
}



# ---------------------------------------------------------------------------
# Image generation
# ---------------------------------------------------------------------------
#
# A SEPARATE catalog from CATALOG above -- a provider's image-generation model
# ids are a different id space entirely from its chat/vision ids (there is no
# relationship between nvidia's "deepseek-ai/deepseek-v4.1-flash" and its
# "black-forest-labs/flux.1-dev"), so this cannot reuse CATALOG's per-entry
# "vision" flag. Feeds the image_free/image_subscription/image_token bucket
# forms via image_options_for(); see llm-gateway/server.py _IMAGE_ADAPTERS for
# the request/response shape each of these providers actually speaks.
#
# Build-time verification status per provider (2026-09-26, re-checked 2026-09-27):
#   nvidia         GENERATION VERIFIED — real image, ~1.5-2s per ISOLATED
#                  single request, 100% success rate across every such test.
#                  BUT: production traffic found 68-298s/call under real
#                  concurrent load (2026-09-27), so it is on the gateway's
#                  emergency tier (tried dead last) rather than the primary
#                  free-tier choice -- see LLM_EMERGENCY_PROVIDERS in
#                  llm-gateway/server.py. Success rate and latency are
#                  different axes; both findings are real.
#   openrouter     EXISTENCE VERIFIED (GET /api/v1/models) — generation
#                  untested, every attempt hit 402 "requires more credits"
#   gemini         EXISTENCE VERIFIED (GET /v1beta/models) — generation
#                  untested, every key was already 429 quota-exceeded
#   tokenharbor    NOT VERIFIED AT ALL — see the comment on its (absent) entry
#
# Pollinations was here too, GENERATION VERIFIED on 2026-09-26 (real image,
# ~18-45s). REMOVED 2026-09-27: it started requiring a paid "pollen" credit
# balance overnight, confirmed 0/5 fresh requests succeeding the next day, all
# "Insufficient balance ... available balance is 0.0000" after a ~45s queued
# generation. No referrer=/token=/model= param bypasses it, and its URL-based
# API has no key/token field to fund a balance through even if we wanted to.
IMAGE_CATALOG: dict[str, list[dict]] = {
    "nvidia": [
        # flux.1-schnell is DELIBERATELY EXCLUDED: every attempt (two
        # networks, 300s+ timeouts) either hung client-side or the upstream
        # itself returned a 504 after 302s. flux.1-dev on the same host and
        # account works reliably in ~1.5-2s -- see _nvidia_image_body in
        # llm-gateway/server.py for the schnell-vs-dev parameter differences
        # this adapter already accounts for.
        {"id": "black-forest-labs/flux.1-dev", "note": "verified, ~1.5-2s"},
    ],
    "openrouter": [
        # Existence verified via a real GET /api/v1/models fetch --
        # architecture.output_modalities includes "image" for each of these.
        # Generation itself is UNTESTED: every attempt during build hit 402
        # "This request requires more credits" before a real image came back.
        {"id": "google/gemini-3-pro-image", "note": "untested — 402 (no credits) at build time"},
        {"id": "google/gemini-3.1-flash-image", "note": "untested — 402 at build time"},
        {"id": "google/gemini-3.1-flash-image-preview", "note": "untested"},
        {"id": "google/gemini-3.1-flash-lite-image", "note": "untested"},
        {"id": "google/gemini-2.5-flash-image", "note": "untested — 402 at build time"},
        {"id": "openai/gpt-5-image", "note": "untested"},
        {"id": "openai/gpt-5-image-mini", "note": "untested"},
        {"id": "openai/gpt-5.4-image-2", "note": "untested"},
    ],
    "gemini": [
        # Existence verified via GET /v1beta/models
        # (supportedGenerationMethods includes "generateContent" and the name
        # says "image"). Generation itself is UNTESTED: every key in the pool
        # was already 429 quota-exceeded for image output at build time (the
        # SAME keys' text/vision quota was fine, so this is a separate,
        # already-exhausted quota, not a broken key).
        {"id": "gemini-2.5-flash-image", "note": "untested — 429 quota at build time"},
        {"id": "gemini-3-pro-image", "note": "untested"},
        {"id": "gemini-3-pro-image-preview", "note": "untested"},
        {"id": "gemini-3.1-flash-image", "note": "untested"},
        {"id": "gemini-3.1-flash-image-preview", "note": "untested"},
        {"id": "gemini-3.1-flash-lite-image", "note": "untested"},
    ],
    # tokenharbor: DELIBERATELY NO catalog. Its GET /v1/models listing (62
    # ids, fetched live) contained nothing matching any known image-model
    # naming convention (flux/image/dall/sd/stable/imagen/seedream/qwen-image/
    # recraft/ideogram all matched zero entries), and /images/generations
    # itself answered "balance_zero" before validating the model name, so no
    # id could be confirmed at all -- not even a wrong one. Renders as
    # "Custom…" only until this is checked again with a funded account.
}


def image_options_for(provider: str) -> list[dict]:
    """Image-generation catalog entries for ``provider``.

    No vision-style filtering here (unlike options_for) -- every entry in
    IMAGE_CATALOG is already image-only, there is no text/image split within
    one provider's image catalog. Returns [] for an unknown or catalog-less
    provider (tokenharbor today), which the page renders as "Custom…" only.
    """
    return [{"id": e["id"], "note": e.get("note", "")} for e in (IMAGE_CATALOG.get(provider) or [])]


def options_for(provider: str, vision_only: bool) -> list[dict]:
    """Catalog entries for ``provider``, vision-filtered for multi_* buckets.

    Returns [] for an unknown or catalog-less provider, which the page renders
    as "Custom…" only.
    """
    entries = CATALOG.get(provider) or []
    if vision_only:
        entries = [e for e in entries if e.get("vision")]
    return [
        {"id": e["id"], "vision": bool(e.get("vision")), "note": e.get("note", "")}
        for e in entries
    ]
