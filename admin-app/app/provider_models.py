"""Per-provider model catalogs for the keys-admin bucket forms.

Feeds the Model dropdown on admin.ahfl.in/keys-admin. Kept out of key_admin.py
so the catalogs can be regenerated wholesale by
``scripts/refresh-model-catalogs.py`` without touching routing logic.

Entry shape::

    {"id": "<model string sent upstream>",
     "vision": True,          # optional — accepts OpenAI image_url parts
     "paid_only": True,       # optional — hidden in the free-tier buckets
     "note": "short label"}   # optional — shown after the id in the <option>

Only ``vision`` entries are offered in the multimodal buckets (multi_free /
multi_subscription / multi_token); the text buckets offer everything.
``paid_only`` entries (optional, IMAGE_CATALOG too) are hidden in the three
free-tier buckets -- the model exists but costs money on that provider.

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
    # OpenCode Go -- ids from GET opencode.ai/zen/go/v1/models (no key needed
    # to list) on 2026-10-17. paid_only = spends the Go subscription, so the
    # free bucket only offers the "-free" ids; "Fetch live" lists the rest.
    "opencode": [
        {"id": "deepseek-v4.1-flash", "paid_only": True},
        {"id": "muse-spark-1.3-contributor", "paid_only": True},
        {"id": "longcat-2.5-preview-free", "note": "free"},
        {"id": "beam-free", "note": "free"},
    ],
    # OpenRouter's free tier: ids ending ":free" with pricing.prompt ==
    # pricing.completion == "0", confirmed live via GET /api/v1/models
    # (no key needed to list) on 2026-09-29 -- 16 such ids existed at that
    # time, all with output_modalities == ["text"]. One additional ":free"
    # id, nvidia/nemotron-3.5-content-safety:free, is a safety classifier
    # (not a chat model) and is deliberately excluded, same convention as
    # the classifier/embedder exclusions on the nvidia catalog below.
    # OpenRouter rotates which models carry ":free" over time -- this list
    # WILL drift; re-check via the same GET before assuming an id below is
    # still free or still live.
    "openrouter": [
        # -- text-only input (LLM free bucket) -----------------------------
        {"id": "inclusionai/ling-3.0-flash-sante:free"},
        {"id": "liquid/lfm-2.5-2.6b:free"},
        {"id": "nvidia/nemotron-3.5-lightning:free"},
        {"id": "poolside/laguna-s-2.1:free", "note": "coding"},
        {"id": "poolside/laguna-xs-2.1:free", "note": "coding"},
        {"id": "cohere/north-mini-code:free", "note": "coding"},
        {"id": "nvidia/nemotron-3-ultra-550b-a55b:free", "note": "largest, slowest"},
        {"id": "nvidia/nemotron-3-super-120b-a12b:free"},
        # -- text + image input (multimodal free bucket) -------------------
        {"id": "qwen/qwen3.8-27b:free", "vision": True, "note": "also audio+video in"},
        {"id": "dots-studio/dots-3-note-preview:free", "vision": True},
        {"id": "thinkingmachines/inkling-small:free", "vision": True, "note": "also audio in"},
        {"id": "thinkingmachines/inkling:free", "vision": True, "note": "also audio in"},
        {"id": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free", "vision": True, "note": "omni, also audio+video in"},
        {"id": "google/gemma-4-26b-a4b-it:free", "vision": True, "note": "also video in"},
        {"id": "google/gemma-4-31b-it:free", "vision": True, "note": "also video in"},
    ],
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
    # Pollinations.ai -- generated 2026-09-29 from GET gen.pollinations.ai/models
    # (official models only; the ~75 "community/..." third-party endpoints are
    # left out). "paid_only" models need purchased pollen and are hidden in the
    # free buckets; the rest also run on the account's free daily pollen grant.
    # "Fetch live" on the page re-reads the same list with the same filters.
    "pollinations": [
        {"id": "openai/gpt-5.4-nano", "vision": True},
        {"id": "openai/gpt-5.3-codex", "vision": True},
        {"id": "openai/gpt-6-luna", "vision": True},
        {"id": "openai/gpt-6-sol", "vision": True},
        {"id": "typesafe/jev-1.13"},
        {"id": "deepseek/deepseek-v4.1-flash", "vision": True},
        {"id": "openai/gpt-6-astra", "vision": True},
        {"id": "z-ai/glm-5.3-flash", "vision": True},
        {"id": "nvidia/nemotron-3.5-lightning"},
        {"id": "z-ai/glm-5.3"},
        {"id": "qwen/qwen3.8-2.4t-a95b"},
        {"id": "cohere/command-a-plus", "vision": True},
        {"id": "moonshotai/kimi-k3", "vision": True},
        {"id": "openai/gpt-oss-20b"},
        {"id": "x-ai/grok-4.6", "vision": True},
        {"id": "openai/gpt-5.6-luna", "vision": True},
        {"id": "openai/gpt-5.6-sol", "vision": True},
        {"id": "openai/gpt-5.6-terra", "vision": True},
        {"id": "minimax/minimax-m3", "vision": True},
        {"id": "x-ai/grok-4.3", "vision": True},
        {"id": "openai/gpt-5.4-mini", "vision": True},
        {"id": "openai/gpt-5.5", "vision": True},
        {"id": "meta/llama-3.3-70b-instruct"},
        {"id": "moonshotai/kimi-k2.6", "vision": True},
        {"id": "mistralai/mistral-large-3", "vision": True},
        {"id": "amazon/nova-2-lite-v1", "vision": True},
        {"id": "pollinations/midijourney-large"},
        {"id": "qwen/qwen3guard-gen-8b"},
        {"id": "x-ai/grok-4.20", "vision": True},
        {"id": "deepseek/deepseek-v4-flash"},
        {"id": "amazon/nova-micro-v1"},
        {"id": "openai/gpt-5-nano", "vision": True},
        {"id": "openai/gpt-5.4", "vision": True},
        {"id": "pollinations/midijourney"},
        {"id": "qwen/qwen3-coder-30b-a3b-instruct"},
        {"id": "anthropic/claude-opus-5.5", "vision": True, "paid_only": True},
        {"id": "xiaomi/mimo-v2.6-flash", "vision": True, "paid_only": True},
        {"id": "xiaomi/mimo-v2.6-pro", "vision": True, "paid_only": True},
        {"id": "x-ai/grok-4.7", "vision": True, "paid_only": True},
        {"id": "inclusionai/ling-3.0-flash-vl", "vision": True, "paid_only": True},
        {"id": "z-ai/glm-5.3-flashx", "vision": True, "paid_only": True},
        {"id": "tencent/hy3", "paid_only": True},
        {"id": "openai/gpt-4o-mini", "vision": True, "paid_only": True},
        {"id": "tencent/hy4-preview", "paid_only": True},
        {"id": "qwen/qwen3.8-flash", "vision": True, "paid_only": True},
        {"id": "qwen/qwen3.8-max-0902", "vision": True, "paid_only": True},
        {"id": "deepseek/deepseek-v4-flash-vision-exp", "vision": True, "paid_only": True},
        {"id": "google/gemini-3.8-flash", "vision": True, "paid_only": True},
        {"id": "anthropic/claude-fable-5.1", "vision": True, "paid_only": True},
        {"id": "inception/mercury-2.5-preview", "paid_only": True},
        {"id": "thinkingmachines/inkling", "vision": True, "paid_only": True},
        {"id": "qwen/qwen3.8-27b", "vision": True, "paid_only": True},
        {"id": "meta/muse-glimmer-30b", "vision": True, "paid_only": True},
        {"id": "meta/muse-spark-1.2", "vision": True, "paid_only": True},
        {"id": "qwen/qwen3.8-max", "vision": True, "paid_only": True},
        {"id": "thinkingmachines/inkling-small", "vision": True, "paid_only": True},
        {"id": "qwen/qwen3.7-flash", "vision": True, "paid_only": True},
        {"id": "nvidia/nemotron-3-ultra", "paid_only": True},
        {"id": "meituan/longcat-2.0", "paid_only": True},
        {"id": "poolside/laguna-s-2.1", "paid_only": True},
        {"id": "google/gemma-4-31b-it", "vision": True, "paid_only": True},
        {"id": "qwen/qwen3.7-max", "paid_only": True},
        {"id": "xiaomi/mimo-v2.5", "vision": True, "paid_only": True},
        {"id": "xiaomi/mimo-v2.5-pro", "paid_only": True},
        {"id": "anthropic/claude-sonnet-5", "vision": True, "paid_only": True},
        {"id": "inception/mercury-2", "paid_only": True},
        {"id": "moonshotai/kimi-k2.7-code", "vision": True, "paid_only": True},
        {"id": "qwen/qwen3.7-plus", "vision": True, "paid_only": True},
        {"id": "anthropic/claude-fable-5", "vision": True, "paid_only": True},
        {"id": "anthropic/claude-opus-5", "vision": True, "paid_only": True},
        {"id": "stepfun/step-3.5-flash", "paid_only": True},
        {"id": "stepfun/step-3.7-flash", "vision": True, "paid_only": True},
        {"id": "google/gemini-3.7-flash", "vision": True, "paid_only": True},
        {"id": "mistralai/mistral-small-4", "vision": True, "paid_only": True},
        {"id": "qwen/qwen3-vl-235b-a22b-thinking", "vision": True, "paid_only": True},
        {"id": "google/gemma-4-26b-a4b-it", "vision": True, "paid_only": True},
        {"id": "meta/llama-4-maverick", "vision": True, "paid_only": True},
        {"id": "meta/llama-4-scout", "vision": True, "paid_only": True},
        {"id": "deepseek/deepseek-v4-pro", "paid_only": True},
        {"id": "anthropic/claude-opus-4.7", "vision": True, "paid_only": True},
        {"id": "google/gemini-3.5-flash-lite", "vision": True, "paid_only": True},
        {"id": "qwen/qwen3-coder-next", "paid_only": True},
        {"id": "qwen/qwen3-vl-30b-a3b-instruct", "vision": True, "paid_only": True},
        {"id": "minimax/minimax-m2.7", "paid_only": True},
        {"id": "z-ai/glm-5.2", "paid_only": True},
        {"id": "google/gemini-2.5-flash-lite", "vision": True, "paid_only": True},
        {"id": "anthropic/claude-haiku-4.5", "vision": True, "paid_only": True},
        {"id": "google/gemini-3.1-pro-preview", "vision": True, "paid_only": True},
        {"id": "anthropic/claude-opus-4.6", "vision": True, "paid_only": True},
        {"id": "anthropic/claude-sonnet-4.6", "vision": True, "paid_only": True},
        {"id": "perplexity/sonar", "paid_only": True},
        {"id": "google/gemini-2.5-flash-lite:search", "vision": True, "paid_only": True},
        {"id": "google/gemini-3-flash-preview", "vision": True, "paid_only": True},
        {"id": "mistralai/mistral-small-3.2", "vision": True, "paid_only": True},
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
#   pollinations   GENERATION VERIFIED 2026-09-29 (z-image-turbo, ~4s) via
#                  its OpenAI-shaped POST gen.pollinations.ai/v1/images/
#                  generations with a Bearer sk_ key. Every call spends
#                  "pollen" from the key's account balance, hence image_token.
#                  The ids below are the non-community, non-paid-only image
#                  models from GET gen.pollinations.ai/image/models on that
#                  date; "Fetch live" on the page lists the current set.
#                  (History: the old keyless image.pollinations.ai/prompt/ URL
#                  API was dropped here on 2026-09-27 when it began demanding a
#                  pollen balance it had no way to pay -- the keyed gen. API
#                  above is what fixes that.)
IMAGE_CATALOG: dict[str, list[dict]] = {
    # Generated 2026-09-29 from GET gen.pollinations.ai/models (official image
    # models only). paid_only entries are hidden in image_free.
    "pollinations": [
        {"id": "tongyi-mai/z-image-turbo", "note": "fast, cheap — verified"},
        {"id": "black-forest-labs/flux.1.1-pro"},
        {"id": "microsoft/mai-image-2.6"},
        {"id": "microsoft/mai-image-2.6-flash"},
        {"id": "microsoft/mai-image-2.5-flash"},
        {"id": "lykon/dreamshaper-8-lcm"},
        {"id": "openai/gpt-image-2"},
        {"id": "amazon/nova-canvas-v1"},
        {"id": "black-forest-labs/flux.2-klein-4b"},
        {"id": "openai/gpt-image-1.5"},
        {"id": "openai/gpt-image-1-mini"},
        {"id": "black-forest-labs/flux.1-kontext-pro"},
        {"id": "black-forest-labs/flux.1-schnell"},
        {"id": "recraft/recraft-v4.1-flash", "paid_only": True},
        {"id": "qwen/qwen-image-2.1", "paid_only": True},
        {"id": "black-forest-labs/flux.2-max", "paid_only": True},
        {"id": "openai/gpt-image-2.5-flare", "paid_only": True},
        {"id": "openai/gpt-image-2.5-sunburst", "paid_only": True},
        {"id": "black-forest-labs/flux.2-flex", "paid_only": True},
        {"id": "black-forest-labs/flux.2-pro", "paid_only": True},
        {"id": "x-ai/grok-imagine-image-2.0", "paid_only": True},
        {"id": "krea/krea-2-medium", "paid_only": True},
        {"id": "recraft/recraft-v4.1-vector", "paid_only": True},
        {"id": "qwen/qwen-image-3", "paid_only": True},
        {"id": "bytedance/seedream-5.0-pro", "paid_only": True},
        {"id": "google/gemini-3.1-flash-lite-image", "paid_only": True},
        {"id": "ideogram-ai/ideogram-v4-balanced", "paid_only": True},
        {"id": "ideogram-ai/ideogram-v4-quality", "paid_only": True},
        {"id": "ideogram-ai/ideogram-v4-turbo", "paid_only": True},
        {"id": "alibaba/wan-2.7-image", "paid_only": True},
        {"id": "alibaba/wan-2.7-image-pro", "paid_only": True},
        {"id": "qwen/qwen-image", "paid_only": True},
        {"id": "x-ai/grok-imagine-image-quality", "paid_only": True},
        {"id": "prunaai/p-image", "paid_only": True},
        {"id": "prunaai/p-image-edit", "paid_only": True},
        {"id": "bytedance/seedream-5.0-lite", "paid_only": True},
        {"id": "google/gemini-3.1-flash-image", "paid_only": True},
        {"id": "x-ai/grok-imagine-image", "paid_only": True},
        {"id": "bytedance/seedream-4.5", "paid_only": True},
        {"id": "google/gemini-3-pro-image", "paid_only": True},
        {"id": "bytedance/seedream-4.0", "paid_only": True},
        {"id": "google/gemini-2.5-flash-image", "paid_only": True},
    ],
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
    return [{"id": e["id"], "note": e.get("note", ""), "paid_only": bool(e.get("paid_only"))}
            for e in (IMAGE_CATALOG.get(provider) or [])]


def options_for(provider: str, vision_only: bool) -> list[dict]:
    """Catalog entries for ``provider``, vision-filtered for multi_* buckets.

    Returns [] for an unknown or catalog-less provider, which the page renders
    as "Custom…" only.
    """
    entries = CATALOG.get(provider) or []
    if vision_only:
        entries = [e for e in entries if e.get("vision")]
    return [
        {"id": e["id"], "vision": bool(e.get("vision")), "note": e.get("note", ""),
         "paid_only": bool(e.get("paid_only"))}
        for e in entries
    ]


# ---------------------------------------------------------------------------
# Speech-to-text / text-to-speech / embeddings (2026-09-29)
# ---------------------------------------------------------------------------
# Same entry shape as IMAGE_CATALOG (id / note / paid_only). Pollinations ids
# and free/paid flags come from GET gen.pollinations.ai/models on 2026-09-29;
# "Fetch live" refreshes them. For TTS the model is the default VOICE for
# edge (any Edge neural voice id works) and the model id for the others.
STT_CATALOG: dict[str, list[dict]] = {
    "groq": [
        {"id": "whisper-large-v3-turbo", "note": "fast — free-whisper's default"},
        {"id": "whisper-large-v3"},
        {"id": "distil-whisper-large-v3-en", "note": "English only"},
    ],
    "pollinations": [
        {"id": "openai/whisper-large-v3"},
        {"id": "assemblyai/universal-2"},
        {"id": "assemblyai/universal-3.5-pro"},
        {"id": "openai/gpt-transcribe"},
        {"id": "elevenlabs/scribe-v2", "paid_only": True},
        {"id": "x-ai/grok-transcribe", "paid_only": True},
    ],
    "assemblyai": [
        {"id": "universal", "note": "AssemblyAI default"},
    ],
    "openai": [
        {"id": "gpt-4o-mini-transcribe"},
        {"id": "gpt-4o-transcribe"},
        {"id": "whisper-1"},
    ],
}

TTS_CATALOG: dict[str, list[dict]] = {
    "edge": [
        {"id": "en-US-AriaNeural", "note": "Hermes's voice until now"},
        {"id": "en-US-JennyNeural"},
        {"id": "en-GB-SoniaNeural"},
        {"id": "en-IN-NeerjaNeural", "note": "Indian English"},
        {"id": "en-IN-PrabhatNeural", "note": "Indian English"},
        {"id": "hi-IN-SwaraNeural", "note": "Hindi"},
        {"id": "hi-IN-MadhurNeural", "note": "Hindi"},
        {"id": "kn-IN-SapnaNeural", "note": "Kannada"},
        {"id": "kn-IN-GaganNeural", "note": "Kannada"},
        {"id": "ta-IN-PallaviNeural", "note": "Tamil"},
    ],
    "pollinations": [
        {"id": "elevenlabs/eleven-flash-v2.5", "paid_only": True},
        {"id": "elevenlabs/eleven-multilingual-v2", "paid_only": True},
        {"id": "google/gemini-3.8-flash-lite-tts", "paid_only": True},
        {"id": "qwen/qwen3-tts-flash", "paid_only": True},
        {"id": "hexgrad/kokoro-82m", "paid_only": True},
    ],
    "openai": [
        {"id": "gpt-4o-mini-tts"},
        {"id": "tts-1"},
    ],
}

EMBED_CATALOG: dict[str, list[dict]] = {
    "pollinations": [
        {"id": "openai/text-embedding-3-small", "note": "1536 dims — GBrain/Honcho vectors"},
    ],
    "openrouter": [
        {"id": "openai/text-embedding-3-small", "note": "1536 dims — GBrain/Honcho vectors"},
    ],
    "openai": [
        {"id": "text-embedding-3-small", "note": "1536 dims — GBrain/Honcho vectors"},
    ],
}


def kind_options_for(kind: str, provider: str) -> list[dict]:
    """Catalog entries for the stt / tts / embed bucket kinds."""
    catalog = {"stt": STT_CATALOG, "tts": TTS_CATALOG, "embed": EMBED_CATALOG}.get(kind, {})
    return [{"id": e["id"], "note": e.get("note", ""), "paid_only": bool(e.get("paid_only"))}
            for e in (catalog.get(provider) or [])]
