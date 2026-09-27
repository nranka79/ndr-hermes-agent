"""Key management for the admin-app (admin.ahfl.in/keys-admin).

Manages the LLM gateway's rotation buckets plus the flat provider keys:

  Buckets (LLM_GATEWAY pools, gateway reads them at startup). Three modalities
  (text / multimodal / image generation), each with the same free ->
  subscription -> pay-per-call shape — the shape /quota groups by:
    * free               -> LLM_FREE_POOL  (Token Harbor free, Gemini, ...)
    * subscription       -> LLM_SUBSCRIPTION_POOL   (OpenCode Go, Mistral, ...)
    * api                -> LLM_OPENROUTER_POOL     (OpenRouter, Token Harbor, any API)
    * multi_free         -> LLM_MULTIMODAL_FREE_POOL          (Gemini free — vision/audio/video)
    * multi_subscription -> LLM_MULTIMODAL_SUBSCRIPTION_POOL  (OpenCode Go / Mistral — vision/audio/video)
    * multi_token        -> LLM_MULTIMODAL_TOKEN_POOL         (OpenRouter / Token Harbor — vision/audio/video)
    * image_free         -> LLM_IMAGE_FREE_POOL         (NVIDIA flux — image generation)
    * image_subscription -> LLM_IMAGE_SUBSCRIPTION_POOL (Token Harbor — image generation)
    * image_token        -> LLM_IMAGE_TOKEN_POOL        (Token Harbor / OpenRouter / Gemini — image generation)
  Each bucket entry is provider + model + key. (Pollinations was the one
  keyless exception here — removed 2026-09-27 when it started requiring a
  paid "pollen" balance with no way to fund it through this page; the
  "keyless" provider flag stays generic infrastructure for if that ever
  changes, or another keyless provider shows up.)

  Flat provider keys (consumed by other services):
    Tavily / Apify / Firecrawl (web search+scrape, multi-key), AssemblyAI
    (voice transcription), SuperGrok, Anthropic (quota reporting only).

The six pool vars live in /opt/hermes/.env.rotator-keys (the env_file every
LLM-consuming container uses). Some entries are ALSO mirrored to the flat
legacy vars other services still read:
  * subscription, provider "opencode" -> OPENCODE_GO_API_KEY series (quota,
    smart-browser, agent credential pool)
  * subscription, provider "mistral"  -> MISTRAL_API_KEY
  * api, provider "openrouter"        -> OPENROUTER_API_KEY (free-whisper)

Security model: this container (hermes-apps) does NOT mount the real
/opt/hermes/.env. Every read/write happens inside a disposable helper
container (python:3.12-slim) launched via the Docker socket with /opt/hermes
bind-mounted just for that one operation, then removed. Secrets travel in as
container env vars and keys are only ever surfaced masked ("…abcd"); the full
pool JSON never reaches this process.

This does NOT defend against a fully compromised hermes-apps process using its
own Docker socket access to go further — that ceiling was already accepted
when docker.sock was mounted (see docker-compose.prod.yml comment near the
hermes-apps volumes).

Auth: no extra check here — relies on the same AuthMiddleware/SSO that
protects the rest of admin.ahfl.in (see auth.py / ADMIN_EMAILS).
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import re
import uuid

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.background import BackgroundTask

from .jinja_env import env
from .provider_models import image_options_for, options_for

router = APIRouter()
logger = logging.getLogger("admin-app.keys")

ENV_PATH = "/opt/hermes/.env.rotator-keys"
MAIN_ENV_PATH = "/opt/hermes/.env"
COMPOSE_FILE = "/opt/hermes/docker-compose.prod.yml"
COMPOSE_DIR = "/opt/hermes"
HELPER_IMAGE = "python:3.12-slim"

DEFAULT_MODEL = "deepseek-v4-flash"

# Value submitted by the Model <select> when the operator chooses "Custom…";
# the real model then arrives in the `model_custom` field. Must match the
# option value in keys_admin.html.
CUSTOM_MODEL_SENTINEL = "__custom__"

# Values are only ever allowed to contain safe characters — a key should
# never carry shell metacharacters, quotes or newlines.
_VALUE_RE = re.compile(r"^[A-Za-z0-9._/:+=-]+$")
_MODEL_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9 ._:\/@-]{0,127}$")
_BASE_RE = re.compile(r"^https?://[A-Za-z0-9._:\/{}@-]+$")
_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Legacy flat opencode series (same discovery order as quota.py / the old page).
OPENCODE_SERIES = [
    "OPENCODE_GO_API_KEY", "OPENCODE_API_KEY", "OPENCODE_GO_KEY_3",
    *(f"OPENCODE_GO_API_KEY_{i}" for i in range(4, 21)),
]

# Which bucket entries are mirrored into flat legacy vars other services read.
# The mirror is best-effort: bucket is the source of truth, the flat var is a
# compatibility projection (first N matching keys fill the series).
MIRROR_SPEC = {
    "subscription": {
        "opencode": {"vars": OPENCODE_SERIES},
        "mistral": {"vars": ["MISTRAL_API_KEY"]},
    },
    "api": {
        "openrouter": {"vars": ["OPENROUTER_API_KEY"]},
    },
}

BUCKETS: dict[str, dict] = {
    "free": {
        "label": "Free tier",
        "env_var": "LLM_FREE_POOL",
        "default_provider": "gemini",
        "restart": ["llm-gateway"],
        "help": "Cost-free credentials (Token Harbor free models, Google AI "
                "Studio/Gemini, Cloudflare Workers AI, DeepSeek free credits, "
                "Azure AI Foundry credits). Each entry fixes provider + model "
                "+ key; calls use the free pool first, round-robin, and weekly "
                "caps park an entry until its reset.",
    },
    "subscription": {
        "label": "Subscription (flat-rate)",
        "env_var": "LLM_SUBSCRIPTION_POOL",
        "default_provider": "opencode",
        "restart": ["llm-gateway", "hermes-apps"],
        "help": "Keys you pay a fixed price per key (OpenCode Go, Mistral, "
                "…). Each entry: provider + model + key. OpenCode entries are "
                "also mirrored to OPENCODE_* for quota/smart-browser.",
    },
    "api": {
        "label": "API / pay-per-call",
        "env_var": "LLM_OPENROUTER_POOL",
        "default_provider": "openrouter",
        "restart": ["llm-gateway", "hermes-apps"],
        "help": "OpenRouter, Token Harbor, and other API-based providers. "
                "Each entry is provider + default model + key. A request that "
                "names a provider/model routes to the right provider's keys; a "
                "no-model call uses that provider's default model.",
    },
    "multi_free": {
        "label": "Multimodal free",
        "env_var": "LLM_MULTIMODAL_FREE_POOL",
        "default_provider": "gemini",
        "restart": ["llm-gateway"],
        "help": "Free vision-capable credentials used for multimodal requests "
                "(image / audio / video content). Gemini free is tried first so "
                "free credits are spent on vision work, not plain text. Each "
                "entry fixes provider + model + key.",
    },
    "multi_subscription": {
        "label": "Multimodal subscription (flat-rate)",
        "env_var": "LLM_MULTIMODAL_SUBSCRIPTION_POOL",
        "default_provider": "opencode",
        "restart": ["llm-gateway"],
        "help": "Flat-rate keys used for multimodal requests, tried after the "
                "free multimodal pool and before the pay-per-call one, so a "
                "subscription you already pay for absorbs vision work instead "
                "of metered credit. Each entry fixes provider + model + key.",
    },
    "multi_token": {
        "label": "Multimodal API / pay-per-call",
        "env_var": "LLM_MULTIMODAL_TOKEN_POOL",
        "default_provider": "openrouter",
        "restart": ["llm-gateway"],
        "help": "Pay-per-call multimodal fallback (OpenRouter / Token Harbor). "
                "Used when no free multimodal key can serve the request. Entry "
                "model defaults to google/gemini-2.5-flash.",
    },
    # -- image generation: a third modality, same free -> subscription ->
    # pay-per-call shape, served on its own gateway endpoint
    # (POST /v1/images/generations) rather than by sniffing the chat body --
    # image generation is a different upstream API on every provider, not a
    # variant of chat completions. See llm-gateway/server.py _IMAGE_ADAPTERS.
    "image_free": {
        "label": "Image generation — free",
        "env_var": "LLM_IMAGE_FREE_POOL",
        "default_provider": "nvidia",
        "restart": ["llm-gateway"],
        "help": "Cost-free image generation. NVIDIA NIM offers flux.1-dev on a "
                "free nvapi- key, but is on the gateway's emergency tier as of "
                "2026-09-27 — production found it taking 68-298s/call under real "
                "load, so it is deliberately tried LAST, after subscription/token, "
                "not first (see LLM_EMERGENCY_PROVIDERS in llm-gateway/server.py). "
                "For fast image generation, fund a subscription/token provider "
                "below instead. (Pollinations was here too until it started "
                "requiring a paid balance we have no way to fund.)",
    },
    "image_subscription": {
        "label": "Image generation — subscription",
        "env_var": "LLM_IMAGE_SUBSCRIPTION_POOL",
        "default_provider": "tokenharbor",
        "restart": ["llm-gateway"],
        "help": "Flat-rate / metered-balance image providers (Token Harbor). "
                "Tried after the free image pool, before pay-per-call.",
    },
    "image_token": {
        "label": "Image generation — API / pay-per-call",
        "env_var": "LLM_IMAGE_TOKEN_POOL",
        "default_provider": "tokenharbor",
        "restart": ["llm-gateway"],
        "help": "Pay-per-call image providers (Token Harbor, OpenRouter, "
                "Gemini). Final fallback for POST /v1/images/generations.",
    },
}

FLAT_PROVIDERS: dict[str, dict] = {
    "tavily": {
        "label": "Tavily (web search)",
        "base": "TAVILY_API_KEY",
        "aliases": [],
        "max_slots": 10,
        "multi": True,
        "restart": ["hermes"],
    },
    "apify": {
        "label": "Apify (web scraping)",
        "base": "APIFY_API_KEY",
        "aliases": [],
        "max_slots": 10,
        "multi": True,
        "restart": ["hermes"],
    },
    "firecrawl": {
        "label": "Firecrawl (web scraping)",
        "base": "FIRECRAWL_API_KEY",
        "aliases": [],
        "max_slots": 10,
        "multi": True,
        "restart": ["hermes"],
    },
    "assemblyai": {
        "label": "AssemblyAI (voice transcription)",
        "base": "ASSEMBLYAI_API_KEY",
        "aliases": [],
        "max_slots": 10,
        "multi": True,
        "restart": ["hermes-apps"],
    },
    "groq": {
        "label": "Groq (voice transcription)",
        "base": "GROQ_API_KEY",
        "aliases": [],
        "max_slots": 10,
        "multi": True,
        "restart": ["hermes-apps"],
    },
    "supergrok": {
        "label": "SuperGrok",
        "base": "XAI_OAUTH_TOKEN",
        "aliases": [],
        "max_slots": 1,
        "multi": False,
        "restart": ["hermes-apps"],
    },
    # Separate from the "anthropic" rotation provider above: that one is a
    # normal API key that serves traffic, this one is an Admin API key
    # (sk-ant-admin01-…) that exists solely so /quota can read the org's cost
    # report. A routing key is 401ed by that endpoint, so both are needed to
    # both use Claude and see what it cost.
    "anthropic": {
        "label": "Claude Code / Anthropic (quota only — Admin API key)",
        "base": "ANTHROPIC_ADMIN_API_KEY",
        "aliases": [],
        "max_slots": 1,
        "multi": False,
        "restart": ["hermes-apps"],
    },
}

# Provider catalog: every dropdown option across the three LLM buckets.
#   label        – shown in the <select>
#   tiers        – which buckets this provider is offered in (free/subscription/api)
#   base         – default endpoint (placeholders {account_id}/{resource} are
#                  substituted from the entry fields on save)
#   auth/auth_header/query – wired through to the gateway config as defaults
#   extra_fields – additional form inputs needed to resolve the endpoint
#                  (name, label, placeholder); shown conditionally in the UI
#   mirror       – flat legacy env var family this provider mirrors into
PROVIDERS: dict[str, dict] = {
    # -- free tier ---------------------------------------------------------
    "gemini": {
        "label": "Google AI Studio (Gemini API)",
        # image_free/image_token: gemini-2.5-flash-image et al, reached over
        # the NATIVE :generateContent endpoint, not this openai-compat base --
        # see llm-gateway/server.py _gemini_image_path. Existence-verified via
        # GET /v1beta/models; generation itself untested (every key was
        # already 429 quota-exceeded for image output when this was built).
        "tiers": ["free", "api", "multi_free", "image_free", "image_token"],
        "base": "https://generativelanguage.googleapis.com/v1beta/openai",
    },
    "tokenharbor": {
        "label": "Token Harbor",
        # image_subscription/image_token: OpenAI-shaped /images/generations
        # (confirmed by its error envelope -- {"error":{"code":"balance_zero"}}
        # is an api_error, not a 404, so route + auth are right); the account
        # used to build this had $0 balance, so no model id could be verified
        # -- see provider_models.IMAGE_CATALOG's comment for why tokenharbor
        # has no image catalog yet.
        "tiers": ["free", "subscription", "api", "multi_subscription", "multi_token",
                 "image_subscription", "image_token"],
        "base": "https://tokenharbor.ai/v1",
    },
    "cloudflare": {
        "label": "Cloudflare Workers AI",
        "tiers": ["free"],
        "base": "https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/v1",
        "extra_fields": [("account_id", "Account ID", "Your Cloudflare account ID")],
    },
    "deepseek": {
        "label": "DeepSeek Official Platform",
        "tiers": ["free", "api"],
        "base": "https://api.deepseek.com/v1",
    },
    "azure": {
        "label": "Azure AI Foundry",
        "tiers": ["free", "api"],
        "base": "https://{resource}.services.ai.azure.com/models",
        "auth": "header",
        "auth_header": "api-key",
        "query": {"api-version": "2024-05-01-preview"},
        "extra_fields": [("resource", "Resource name", "Your Azure resource name")],
    },
    # -- subscription tier --------------------------------------------------
    "opencode": {
        "label": "OpenCode Go (subscription)",
        "tiers": ["subscription", "multi_subscription"],
        "base": "https://opencode.ai/zen/go/v1",
        "mirror": "opencode",
    },
    "mistral": {
        "label": "Mistral AI",
        "tiers": ["subscription", "multi_subscription"],
        "base": "https://api.mistral.ai/v1",
    },
    # -- api / pay-per-call tier --------------------------------------------
    "openrouter": {
        "label": "OpenRouter",
        # image_token: no /images/generations (confirmed 404 "No model
        # found") -- image-capable models are reached through
        # /chat/completions with modalities:["image","text"] instead, see
        # llm-gateway/server.py _openrouter_image_body. Existence-verified via
        # GET /api/v1/models (output_modalities includes "image"); generation
        # untested (402 "requires more credits" on every attempt at build time).
        "tiers": ["api", "multi_token", "image_token"],
        "base": "https://openrouter.ai/api/v1",
    },
    # NVIDIA NIM. Offered in the free buckets (that is what an nvapi- key on the
    # developer program actually gets) and also in the pay-per-call ones for
    # accounts with a paid NVIDIA entitlement. Model ids are namespaced
    # ("deepseek-ai/deepseek-v4.1-flash") and pass _MODEL_RE unchanged; the free
    # tier is entitlement-gated, so see provider_models.CATALOG["nvidia"] for
    # which ids an nvapi- key can actually call.
    "nvidia": {
        "label": "NVIDIA NIM (build.nvidia.com)",
        # image_free/image_token: flux.1-dev image generation lives on a
        # DIFFERENT host (ai.api.nvidia.com/v1/genai/<model>, model in the URL
        # path) from the chat surface above -- integrate.api.nvidia.com has no
        # /images/generations at all (confirmed: flat 404). Only flux.1-dev is
        # offered; its sibling flux.1-schnell hung to a 504 on every attempt
        # (two networks, 300s+) and is deliberately excluded from the catalog.
        "tiers": ["free", "api", "multi_free", "multi_token", "image_free", "image_token"],
        "base": "https://integrate.api.nvidia.com/v1",
    },
    # Anthropic / OpenAI are reached through their OpenAI-compatible surface;
    # the gateway supplies anthropic's x-api-key auth + anthropic-version
    # header from _PROVIDER_DEFAULTS. Both are vision-capable, hence multi_token.
    "anthropic": {
        "label": "Claude / Anthropic API",
        "tiers": ["api", "multi_token"],
        "base": "https://api.anthropic.com/v1",
    },
    "openai": {
        "label": "OpenAI",
        "tiers": ["api", "multi_token"],
        "base": "https://api.openai.com/v1",
    },
    "opencode-zen": {
        "label": "OpenCode Zen (pay-per-use)",
        "tiers": ["api"],
        "base": "https://opencode.ai/zen/v1",
    },
    "groq": {
        "label": "Groq",
        "tiers": ["api"],
        "base": "https://api.groq.com/openai/v1",
    },
    "together": {
        "label": "Together AI",
        "tiers": ["api"],
        "base": "https://api.together.ai/v1",
    },
    "fireworks": {
        "label": "Fireworks AI",
        "tiers": ["api"],
        "base": "https://api.fireworks.ai/inference/v1",
    },
    "openorca": {
        "label": "OpenOrca (custom base URL required)",
        "tiers": ["api"],
        "base": None,
    },
    "openai-compatible": {
        "label": "Custom OpenAI-compatible endpoint",
        "tiers": ["free", "subscription", "api", "multi_free", "multi_subscription", "multi_token"],
        "base": None,
    },
}

BUCKET_DEFAULTS = {
    "free": "gemini",
    "subscription": "opencode",
    "api": "openrouter",
    "multi_free": "gemini",
    "multi_subscription": "opencode",
    "multi_token": "openrouter",
    "image_free": "nvidia",
    "image_subscription": "tokenharbor",
    "image_token": "tokenharbor",
}
BUCKET_PROVIDERS: dict[str, set[str]] = {
    bid: {pid for pid, p in PROVIDERS.items() if bid in p["tiers"]}
    for bid in BUCKETS
}

# Which of the three cost tiers a bucket represents, independent of modality --
# drives the tier-colored accent + consistent left-to-right ordering on the
# page (free / subscription / api, in that order, in every section).
BUCKET_TIER: dict[str, str] = {
    "free": "free", "subscription": "subscription", "api": "api",
    "multi_free": "free", "multi_subscription": "subscription", "multi_token": "api",
    "image_free": "free", "image_subscription": "subscription", "image_token": "api",
}

# Page layout: three modality sections, each rendering its free/subscription/api
# buckets together as one visual group. Order here IS the page order (LLM at
# the top, then multimodal, then image generation) -- matches BUCKETS' own
# insertion order today, but is expressed explicitly here so the page layout
# does not silently depend on dict insertion order elsewhere.
BUCKET_GROUPS: list[dict] = [
    {"id": "llm", "icon": "💬", "title": "LLM",
     "subtitle": "Text chat completions — POST /v1/chat/completions",
     "buckets": ["free", "subscription", "api"]},
    {"id": "multimodal", "icon": "🖼️", "title": "Multimodal",
     "subtitle": "Vision / audio / video — same endpoint, auto-detected from message content",
     "buckets": ["multi_free", "multi_subscription", "multi_token"]},
    {"id": "image", "icon": "🎨", "title": "Image generation",
     "subtitle": "POST /v1/images/generations — NVIDIA flux, Token Harbor, OpenRouter, Gemini",
     "buckets": ["image_free", "image_subscription", "image_token"]},
]


def _bucket_provider_options(bucket_id: str) -> list[dict]:
    return [
        {"value": pid, "label": p["label"]}
        for pid, p in PROVIDERS.items()
        if bucket_id in p["tiers"]
    ]


def _provider_meta() -> dict:
    """provider id -> {base, extra_fields, models, imageModels, keyless} for
    the frontend JS.

    ``models`` carries the FULL chat/vision catalog (with each entry's
    ``vision`` flag); the page filters it per bucket via the select's
    ``data-vision`` attribute. ``imageModels`` is a SEPARATE catalog for the
    image_* buckets -- a provider's image models are a different id space
    entirely from its chat models (nvidia's chat catalog has no relation to
    "black-forest-labs/flux.1-dev"), selected via the select's ``data-kind``
    attribute instead. Either list being empty means the form falls back to
    the free-text "Custom…" input for that bucket kind.

    ``keyless`` marks a provider that needs no API key at all (none currently
    configured -- Pollinations held this until it started requiring a paid
    balance on 2026-09-27; kept generic for whenever one exists again);
    the page un-requires the key field for it, and _validate_entry skips the
    "Key value required" check server-side.
    """
    return {
        pid: {
            "base": p.get("base"),
            "extra_fields": [f[0] for f in p.get("extra_fields", [])],
            "models": options_for(pid, vision_only=False),
            "imageModels": image_options_for(pid),
            "keyless": bool(p.get("keyless")),
        }
        for pid, p in PROVIDERS.items()
    }


def _bucket_extra_fields(bucket_id: str) -> list[tuple[str, str, str]]:
    """Union of extra (name, label, placeholder) across a bucket's providers."""
    seen, out = set(), []
    for p in PROVIDERS.values():
        if bucket_id in p["tiers"]:
            for f in p.get("extra_fields", []):
                if f[0] not in seen:
                    seen.add(f[0])
                    out.append(f)
    return out


def _resolve_base(provider: str, override: str, account_id: str, resource: str) -> tuple[str | None, str | None]:
    """Return (resolved_base, error). User override wins; otherwise the
    provider default with placeholders substituted."""
    p = PROVIDERS.get(provider, {})
    if override.strip():
        return override.strip(), None
    dflt = p.get("base")
    if not dflt:
        return None, f"Base URL required for {p.get('label', provider)} — set it under Advanced."
    resolved = dflt
    if "{account_id}" in resolved:
        if not account_id.strip():
            return None, "Account ID required for Cloudflare Workers AI."
        resolved = resolved.replace("{account_id}", account_id.strip())
    if "{resource}" in resolved:
        if not resource.strip():
            return None, "Resource name required for Azure AI Foundry."
        resolved = resolved.replace("{resource}", resource.strip())
    return resolved, None

_lock = asyncio.Lock()
# Serializes docker-compose restarts so two rapid key-edits can't race two
# `docker compose up` calls against the same container name.
_restart_lock = asyncio.Lock()


def _log_warn(msg: str) -> None:
    logger.warning(msg)

# ---------------------------------------------------------------------------
# Disposable-helper plumbing. The python helper handles ALL file access so key
# material never reaches this process: secrets go in via container env vars,
# and out the only ever-masked projections.
# ---------------------------------------------------------------------------

_HELPER = r'''
import base64, json, os, urllib.request

cfg = json.loads(base64.b64decode(os.environ["CONFIG"]).decode())
inp = json.loads(base64.b64decode(os.environ["INPUTS"]).decode()) if os.environ.get("INPUTS") else {}
op = inp.get("op", "read")

ENV_FILE, MAIN_FILE = cfg["env"], cfg["main"]
DEFAULT_MODEL = cfg.get("default_model", "deepseek-v4-flash")
BUCKET_DEFS = cfg["buckets"]              # id -> {env_var, default_provider}
MIRROR = cfg.get("mirror", {})

def parse_env(path):
    d = {}
    if os.path.exists(path):
        with open(path, "r") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, _, v = line.partition("=")
                k = k.strip()
                if k:
                    d[k] = v
    return d

def write_env(path, d, drop_keys=frozenset()):
    seen, lines = set(), []
    if os.path.exists(path):
        with open(path, "r") as fh:
            for line in fh:
                line = line.rstrip("\n")
                if line and not line.startswith("#") and "=" in line:
                    k = line.partition("=")[0].strip()
                    if k in drop_keys:
                        continue
                    if k in d:
                        lines.append(f"{k}={d[k]}")
                        seen.add(k)
                        continue
                lines.append(line)
    for k, v in d.items():
        if k not in seen:
            lines.append(f"{k}={v}")
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")

def pool_list(raw):
    try:
        a = json.loads(raw) if raw and str(raw).strip() else []
        return a if isinstance(a, list) else []
    except Exception:
        return []

def nrm(s):
    return "".join(c for c in (s or "").lower() if c.isalnum())

def overlap(a, b):
    A, B = nrm(a), nrm(b)
    if not A or not B:
        return False
    if len(A) < 3 or len(B) < 3:
        return A == B
    return A == B or A in B or B in A

def mask(val):
    val = (val or "").strip()
    if not val:
        return None
    return ("\u2026" + val[-4:]) if len(val) > 4 else ("\u2026" + val)

d = parse_env(ENV_FILE)
main = parse_env(MAIN_FILE)

def materialize():
    """Seed pools from flat legacy vars so the page & gateway agree on data
    even before the first bucket edit."""
    changed = False
    for bid, bdef in BUCKET_DEFS.items():
        if d.get(bdef["env_var"]):
            continue
        if bid == "subscription":
            entries = []
            for v in cfg.get("series", {}).get("opencode", []):
                if d.get(v):
                    entries.append({"id": "legacy-" + v, "provider": "opencode",
                                    "model": DEFAULT_MODEL, "key": d[v]})
            if d.get("MISTRAL_API_KEY"):
                entries.append({"id": "legacy-MISTRAL_API_KEY", "provider": "mistral",
                                "model": cfg.get("series", {}).get("mistral_model") or "open-mistral-nemo",
                                "key": d["MISTRAL_API_KEY"]})
            if entries:
                d[bdef["env_var"]] = json.dumps(entries)
                changed = True
        elif bid == "api":
            if d.get("OPENROUTER_API_KEY"):
                d[bdef["env_var"]] = json.dumps([{"id": "legacy-OPENROUTER_API_KEY",
                                                  "provider": "openrouter", "key": d["OPENROUTER_API_KEY"]}])
                changed = True
    if changed:
        write_env(ENV_FILE, d)

def mirror_vars():
    """{env_var: value} for flat legacy vars that mirror pool entries."""
    out = {}
    for bid, spec in MIRROR.items():
        bdef = BUCKET_DEFS.get(bid)
        if not bdef:
            continue
        entries = pool_list(d.get(bdef["env_var"], ""))
        for provider_alias, mspec in spec.items():
            keys = [e["key"] for e in entries if e.get("key") and overlap(e.get("provider", ""), provider_alias)]
            for i, var in enumerate(mspec["vars"]):
                if i < len(keys):
                    out[var] = keys[i]
                else:
                    out.pop(var, None)
    return out

def masked_entry(e):
    out = {k: v for k, v in e.items() if k != "key"}
    out["has_key"] = bool(e.get("key"))
    out["masked"] = mask(e.get("key"))
    return out

def persist(pool_changes, flat_updates, flat_removes):
    """Write pool vars to the rotator file, flat mirrors to both files."""
    d.update(pool_changes)
    d.update(flat_updates)
    for v in flat_removes:
        d.pop(v, None)
        main.pop(v, None)
    mirrors = mirror_vars()
    d.update(mirrors)
    main.update(mirrors)
    main.update(flat_updates)
    drop = set(flat_removes)
    write_env(ENV_FILE, d, drop_keys=drop)
    write_env(MAIN_FILE, main, drop_keys=drop)

BUCKET_GROUP_OF = cfg.get("bucket_group", {})  # bucket id -> "llm"/"multimodal"/"image"


def key_exists(new_key, current_bid=None, exclude_var=None, exclude_id=None):
    """True if the raw key value collides with an existing one.

    Scoped to `current_bid`'s modality group (llm / multimodal / image) when
    given: the same paid account routinely serves all three (one OpenRouter
    key for chat, vision, AND image generation), so reuse ACROSS groups is
    normal and allowed. Reuse WITHIN a group's three tiers (free/subscription/
    api) still isn't -- that usually means a copy-paste mistake, not a
    deliberate choice. `current_bid=None` (the flat-provider ops) falls back
    to the original fully-global check, since a Tavily/Apify slot has no
    modality group to scope against.
    """
    if not new_key:
        return False
    my_group = BUCKET_GROUP_OF.get(current_bid) if current_bid else None
    for bid, bdef in BUCKET_DEFS.items():
        if current_bid is not None and BUCKET_GROUP_OF.get(bid) != my_group:
            continue
        for e in pool_list(d.get(bdef["env_var"], "")):
            if e.get("id") == exclude_id:
                continue
            if e.get("key") == new_key:
                return True
    for fid, fdef in cfg.get("flat", {}).items():
        for var in fdef["candidate_vars"]:
            if var == exclude_var:
                continue
            if d.get(var) == new_key:
                return True
    return False

KEY_DUP_MSG = ("That API key is already in use in another free/subscription/API "
               "bucket for this modality (or as a provider key). The same key "
               "MAY be reused across different modalities -- e.g. the same "
               "OpenRouter key in both the LLM and image-generation buckets.")

if op == "read":
    materialize()
    result = {"buckets": {}, "flat": {}}
    for bid, bdef in BUCKET_DEFS.items():
        result["buckets"][bid] = [masked_entry(e) for e in pool_list(d.get(bdef["env_var"], ""))]
    for fid, fdef in cfg.get("flat", {}).items():
        slots = []
        for var in fdef["candidate_vars"]:
            v = d.get(var, "")
            slots.append({"env_var": var, "configured": bool(v), "masked": mask(v)})
        result["flat"][fid] = slots
    print(json.dumps(result))
elif op == "bucket":
    bid = inp["bucket"]
    bdef = BUCKET_DEFS[bid]
    materialize()
    entries = pool_list(d.get(bdef["env_var"], ""))
    action = inp["action"]
    new_fields = {k: v for k, v in inp.get("fields", {}).items() if v is not None}
    if action == "add":
        entry = {"id": inp["row_id"]}
        entry.update(new_fields)
        for optional in ("base", "weekly_limit_requests", "weekly_limit_tokens", "reset_days"):
            if entry.get(optional) in (None, "", 0) and optional not in ("weekly_limit_requests", "weekly_limit_tokens"):
                entry.pop(optional, None)
        if key_exists(entry.get("key"), bid):
            print(json.dumps({"ok": False, "error": KEY_DUP_MSG}))
            raise SystemExit(0)
        entries.append(entry)
    elif action == "remove":
        entries = [e for e in entries if e.get("id") != inp["row_id"]]
    elif action == "replace":
        for e in entries:
            if e.get("id") == inp["row_id"]:
                if new_fields.get("key") and key_exists(new_fields["key"], bid, exclude_id=e.get("id")):
                    print(json.dumps({"ok": False, "error": KEY_DUP_MSG}))
                    raise SystemExit(0)
                e.update(new_fields)
                break
        else:
            print(json.dumps({"ok": False, "error": "entry not found"}))
            raise SystemExit(0)
    persist({bdef["env_var"]: json.dumps(entries)}, {}, [])
    print(json.dumps({"ok": True}))
elif op == "flat_set":
    var = inp["env_var"]
    value = inp["value"]
    if key_exists(value, exclude_var=var):
        print(json.dumps({"ok": False, "error": KEY_DUP_MSG}))
        raise SystemExit(0)
    persist({}, {var: value}, [])
    print(json.dumps({"ok": True}))
elif op == "flat_del":
    var = inp["env_var"]
    persist({}, {}, [var])
    print(json.dumps({"ok": True}))
elif op == "list_models":
    # Ask the provider what it serves, using the key the operator just pasted.
    # Runs in here rather than in hermes-apps so the key stays inside the
    # disposable container like every other key operation, and so a hostile
    # provider response can never touch the admin process.
    base = (inp.get("base") or "").rstrip("/")
    key = inp.get("key") or ""
    if not base:
        print(json.dumps({"ok": False, "error": "no base URL for this provider"}))
        raise SystemExit(0)
    url = base + "/models"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    # Send the key both ways: most providers want a bearer token, a few
    # (azure) want it in a named header. Sending both is harmless and avoids
    # threading the per-provider auth style in here.
    if key:
        req.add_header("Authorization", "Bearer " + key)
        for hdr in inp.get("auth_headers") or []:
            req.add_header(hdr, key)
    try:
        with urllib.request.urlopen(req, timeout=15) as fh:
            body = json.loads(fh.read().decode("utf-8", "replace"))
    except Exception as exc:
        detail = ""
        rd = getattr(exc, "read", None)
        if rd:
            try:
                detail = rd().decode("utf-8", "replace")[:200]
            except Exception:
                detail = ""
        code = getattr(exc, "code", type(exc).__name__)
        print(json.dumps({"ok": False, "error": "%s listing models from %s %s" % (code, url, detail)}))
        raise SystemExit(0)
    rows = body.get("data") if isinstance(body, dict) else body
    ids = []
    if isinstance(rows, list):
        for r in rows:
            mid = r.get("id") if isinstance(r, dict) else r
            if isinstance(mid, str) and mid.strip():
                ids.append(mid.strip())
    print(json.dumps({"ok": True, "models": sorted(set(ids))}))
else:
    print(json.dumps({"ok": False, "error": "unknown op"}))
'''

def _candidate_env_vars(pconfig: dict) -> list[str]:
    """Same discovery order as quota.py / credential_pool.py: legacy aliases
    first, then the canonical numbered series."""
    names = [pconfig["base"], *pconfig["aliases"]]
    start = len(names) + 1
    for i in range(start, pconfig["max_slots"] + 1):
        names.append(f"{pconfig['base']}_{i}")
    return names[: pconfig["max_slots"]]


_config_b64 = base64.b64encode(json.dumps({
    "env": ENV_PATH,
    "main": MAIN_ENV_PATH,
    "default_model": DEFAULT_MODEL,
    "buckets": {k: {"env_var": v["env_var"], "default_provider": v["default_provider"]} for k, v in BUCKETS.items()},
    # bucket id -> modality group id, so the helper's key_exists() can scope
    # the duplicate-key guard to "this modality's 3 tiers" instead of all 9
    # buckets -- see BUCKET_GROUPS / the key_exists docstring in _HELPER.
    "bucket_group": {bid: g["id"] for g in BUCKET_GROUPS for bid in g["buckets"]},
    "mirror": MIRROR_SPEC,
    "series": {"opencode": OPENCODE_SERIES, "mistral_model": "open-mistral-nemo"},
    "flat": {
        k: {"candidate_vars": _candidate_env_vars(v)}
        for k, v in FLAT_PROVIDERS.items()
    },
}).encode()).decode()


async def _run_py(op_code: str, inputs: dict) -> tuple[int, str]:
    """Run the python helper in a disposable container. All file access and
    secret handling happens in there."""
    b64_op = base64.b64encode(op_code.encode()).decode()
    b64_inp = base64.b64encode(json.dumps(inputs).encode()).decode()
    cmd = [
        "docker", "run", "--rm",
        "-e", f"CONFIG={_config_b64}",
        "-e", f"INPUTS={b64_inp}",
        "-e", f"OPCODE={b64_op}",
        "-v", f"{COMPOSE_DIR}:{COMPOSE_DIR}",
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        "-v", "/usr/bin/docker:/usr/bin/docker:ro",
        "-v", "/usr/libexec/docker/cli-plugins:/usr/libexec/docker/cli-plugins:ro",
        HELPER_IMAGE, "python3", "-c",
        "import base64,os;exec(base64.b64decode(os.environ['OPCODE']).decode())",
    ]
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    out, _ = await proc.communicate()
    return proc.returncode or 0, out.decode(errors="replace")


async def _run(op: str, inputs: dict | None = None) -> tuple[bool, str]:
    """Serialize + run a helper op. Returns (ok, message)."""
    async with _lock:
        code, out = await _run_py(_HELPER, {"op": op, **(inputs or {})})
    if code != 0:
        logger.error("helper op=%s failed exit=%s: %s", op, code, out[-2000:])
        return False, f"Key store op failed (exit {code}) — check server logs"
    return True, out


async def _run_op(op: str, inputs: dict | None = None) -> tuple[bool, dict]:
    """Run a mutating helper op and return (ok, result) parsed from the JSON.

    The helper reports logical failures (e.g. a duplicate key) as a
    ``{"ok": false, "error": ...}`` payload with a 0 exit code, so the raw
    exit code alone is not enough — we parse the JSON to know whether the
    change was applied.
    """
    ok, out = await _run(op, inputs)
    if not ok:
        return False, {"error": out}
    try:
        result = json.loads(out)
    except Exception as e:
        logger.error("could not parse helper %s output: %s", op, e)
        return False, {"error": f"could not parse key store response: {out[:300]}"}
    return bool(result.get("ok")), result


async def _read_state() -> dict:
    ok, out = await _run("read")
    if not ok:
        return {"buckets": {}, "flat": {}}
    try:
        return json.loads(out)
    except Exception as e:
        logger.error("could not parse helper read output: %s", e)
        return {"buckets": {}, "flat": {}}


async def _restart(names: list[str]) -> tuple[bool, str]:
    """Recreate the affected compose services so they pick up the new env.

    Self-healing and runs in a *detached* container: it cleans up leftover
    ``<hash>_<name>`` containers a previous interrupted ``docker compose`` run
    can leave behind (they hold the target container name hostage and cause
    "name already in use"), then retries the compose up before the response is even
    expected back, so this request returns immediately and the actual compose
    work happens independently on the host.

    Why detached: the restart targets often include ``hermes-apps`` itself —
    the very container serving this admin request. Recreating it while the
    request is still being processed kills the process mid-response, which is
    what produced the intermittent 502/504 (the key was saved — just the
    response never made it out). So we launch the restart as a detached
    one-off container (docker run -d) that survives this container's
    recreation, and only *schedule* it (with a delay) so the HTTP response has
    already flushed by the time the recreate starts.
    """
    # Match leftover containers docker compose leaves with a hashed prefix
    # when a previous recreate was interrupted: "<12-hex>_<name>"
    # (e.g. "50cb7904f8d1_llm-gateway-1"). We remove them so the target
    # container name is free for the recreate below.
    pattern = "|".join(f"[0-9a-f]{{12}}_{re.escape(n)}(-[0-9]+)?" for n in names)
    retry_bash = (
        f"cd {COMPOSE_DIR} && "
        f"docker ps -a --format '{{{{.Names}}}}' "
        f"| grep -E '^({pattern})$' | xargs -r docker rm -f; "
        "for i in 1 2 3; do "
        f"docker compose -f {COMPOSE_FILE} up -d --no-deps {' '.join(names)} "
        "&& break || sleep 2; "
        "done"
    )
    async with _restart_lock:
        try:
            proc = await asyncio.create_subprocess_exec(
                "docker", "run", "-d", "--rm",
                "-v", f"{COMPOSE_DIR}:{COMPOSE_DIR}",
                "-v", "/var/run/docker.sock:/var/run/docker.sock",
                "-v", "/usr/bin/docker:/usr/bin/docker:ro",
                "-v", "/usr/libexec/docker/cli-plugins:/usr/libexec/docker/cli-plugins:ro",
                "debian:13-slim", "bash", "-c", retry_bash,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL,
            )
            await proc.communicate()
        except Exception as exc:
            _log_warn(f"could not launch restart container: {exc}")
            return False, f"Restart could not be triggered: {exc}"
    return True, f"Restart triggered: {', '.join(names)} (containers will recreate shortly)."


async def _restart_after_flush(names: list[str]) -> None:
    """Background task: give the HTTP response time to flush, then restart.

    The restart itself is detached so it keeps running even when the
    container serving this request is recreated; the small sleep just makes
    sure the response reaches the client first.
    """
    if not names:
        return
    await asyncio.sleep(3)
    try:
        await _restart(names)
    except Exception as exc:
        _log_warn(f"background restart of {names} failed: {exc}")


def _looks_duplicated_model(provider: str, model: str) -> bool:
    """True when a model looks like '<provider><provider>-…' — a browser
    auto-fill artifact (the provider name got pasted into the model field,
    e.g. 'gemini' + 'gemini-3.5-flash' -> 'geminigem ini-3.5-flash')."""
    p = (provider or "").strip().lower()
    m = (model or "").strip().lower()
    if not p or not m:
        return False
    if m.startswith(p):
        rest = m[len(p):].lstrip(" -_.")
        return rest.startswith(p)
    return False


def _validate_entry(provider: str, model: str, key: str, base: str,
                    weekly_req: str, weekly_tok: str, reset_days: str) -> str | None:
    if not provider.strip():
        return "Provider required."
    if provider.strip() not in PROVIDERS:
        return "Unknown provider."
    if model.strip() and not _MODEL_RE.match(model.strip()):
        return "Model contains unexpected characters."
    if model.strip() and _looks_duplicated_model(provider, model):
        return (f"Model \"{model.strip()}\" looks like the provider name was pasted twice "
                f"(\"{provider.strip()}\"). Please enter just the model once, e.g. "
                f"\"{model.strip()[len(provider.strip()):].lstrip('- ')}\".")
    keyless = bool(PROVIDERS.get(provider.strip(), {}).get("keyless"))
    if key.strip():
        # Validated the same way regardless of keyless-ness: a keyless
        # provider MAY still be given a key (the flag only means one is not
        # REQUIRED), and if one is supplied it must be well-formed.
        if not _VALUE_RE.match(key.strip()):
            return "Key contains unexpected characters (only letters, digits, and ._/:+- allowed)."
    elif not keyless:
        return "Key value required."
    if base.strip() and not _BASE_RE.match(base.strip()):
        return "Base URL must be a valid http(s) URL."
    for label, val, lo, hi in (
        ("weekly limit requests", weekly_req, 0, 10_000_000),
        ("weekly limit tokens", weekly_tok, 0, 10**11),
    ):
        if val.strip():
            try:
                n = int(val)
            except ValueError:
                return f"{label} must be an integer."
            if not lo <= n <= hi:
                return f"{label} out of range."
    if reset_days.strip():
        try:
            n = int(reset_days)
        except ValueError:
            return "Reset days must be an integer."
        if not 1 <= n <= 90:
            return "Reset days out of range (1-90)."
    return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

def _bucket_view(bid: str, b: dict, state: dict) -> dict:
    """The per-bucket dict the template renders one "card" from."""
    return {
        "id": bid, "label": b["label"], "help": b["help"],
        "tier": BUCKET_TIER.get(bid, "api"),
        "entries": state["buckets"].get(bid, []),
        "provider_options": _bucket_provider_options(bid),
        "extra_fields": _bucket_extra_fields(bid),
        # Multimodal buckets only offer vision-capable models; the page
        # filters PMETA[provider].models on this flag.
        "vision_only": bid.startswith("multi_"),
        # api / multi_token entries may omit the model (the provider's
        # default is then used), the other buckets require one.
        "model_optional": bid in ("api", "multi_token"),
        # image_* buckets pull from PMETA[provider].imageModels instead of
        # .models -- a provider's image-model ids are a different space
        # entirely from its chat/vision ids (see _provider_meta).
        "kind": "image" if bid.startswith("image_") else "chat",
        "default_provider": BUCKET_DEFAULTS.get(bid, b["default_provider"]),
    }


def _render(request: Request, state: dict, message: str | None = None, error: str | None = None, restart: list[str] | None = None) -> HTMLResponse:
    content = env.get_template("keys_admin.html").render(
        user=request.session.get("user"),
        # Three modality sections (LLM -> multimodal -> image generation),
        # each holding its free/subscription/api tier-cards together -- see
        # BUCKET_GROUPS. Replaces a single flat 9-card grid where the three
        # image_* cards (added last) were visually indistinguishable from the
        # six chat/vision ones and easy to miss entirely.
        bucket_groups=[
            {
                "id": g["id"], "icon": g["icon"], "title": g["title"], "subtitle": g["subtitle"],
                "buckets": (bucket_views := [
                    _bucket_view(bid, BUCKETS[bid], state) for bid in g["buckets"] if bid in BUCKETS
                ]),
                "total_entries": sum(len(bv["entries"]) for bv in bucket_views),
            }
            for g in BUCKET_GROUPS
        ],
        provider_meta=_provider_meta(),
        flat_providers=[
            {"id": pid, "label": p["label"], "multi": p["multi"],
             "slots": state["flat"].get(pid, [])}
            for pid, p in FLAT_PROVIDERS.items()
        ],
        message=message, error=error,
    )
    resp = HTMLResponse(content)
    if restart:
        # Restart AFTER the response has been sent to the client. The restart
        # itself is detached, so recreating this container mid-restart does not
        # kill the response (which used to surface as a 502/504).
        resp.background = BackgroundTask(_restart_after_flush, restart)
    return resp


@router.get("/keys-admin")
async def keys_admin_page(request: Request):
    return _render(request, await _read_state())


@router.post("/keys-admin/bucket/add")
async def keys_bucket_add(request: Request,
                          bucket: str = Form(...),
                          provider: str = Form(...),
                          model: str = Form(""),
                          model_custom: str = Form(""),
                          key: str = Form(...),
                          base: str = Form(""),
                          account_id: str = Form(""),
                          resource: str = Form(""),
                          weekly_limit_requests: str = Form(""),
                          weekly_limit_tokens: str = Form(""),
                          reset_days: str = Form("")):
    message = error = None
    # The Model field is a <select>; picking its "Custom…" option submits the
    # sentinel and puts the real value in the sibling free-text input. Resolve
    # before validation so _validate_entry / _MODEL_RE see the same string they
    # saw when this field was a plain text input.
    if model.strip() == CUSTOM_MODEL_SENTINEL:
        model = model_custom
    if bucket not in BUCKETS:
        error = "Unknown bucket."
    else:
        error = _validate_entry(provider, model, key, base,
                                weekly_limit_requests, weekly_limit_tokens, reset_days)
    if not error and provider.strip() not in BUCKET_PROVIDERS.get(bucket, set()):
        error = f"{PROVIDERS.get(provider.strip(), {}).get('label', provider)} is not offered for {BUCKETS[bucket]['label']}."
    if not error:
        resolved_base, base_error = _resolve_base(provider.strip(), base, account_id, resource)
        if base_error:
            error = base_error
        elif not resolved_base:
            error = "Base URL required for this provider."
    if not error:
        fields: dict = {
            "provider": provider.strip(),
            "key": key.strip(),
            "base": resolved_base,
        }
        if model.strip():
            fields["model"] = model.strip()
        if account_id.strip():
            fields["account_id"] = account_id.strip()
        if resource.strip():
            fields["resource"] = resource.strip()
        if weekly_limit_requests.strip():
            fields["weekly_limit_requests"] = int(weekly_limit_requests)
        if weekly_limit_tokens.strip():
            fields["weekly_limit_tokens"] = int(weekly_limit_tokens)
        if reset_days.strip():
            fields["reset_days"] = int(reset_days)
        ok, result = await _run_op("bucket", {
            "bucket": bucket, "action": "add",
            "row_id": uuid.uuid4().hex[:12],
            "fields": fields,
        })
        if ok:
            message = "Added to " + BUCKETS[bucket]["label"] + ". Containers will restart shortly."
        else:
            error = result.get("error") or "Could not add the key."
    return _render(request, await _read_state(), message=message, error=error, restart=BUCKETS[bucket]["restart"] if not error else None)


@router.post("/keys-admin/models/fetch")
async def keys_models_fetch(request: Request,
                            bucket: str = Form(...),
                            provider: str = Form(...),
                            key: str = Form(""),
                            base: str = Form(""),
                            account_id: str = Form(""),
                            resource: str = Form("")):
    """Ask a provider what models it serves, for the page's "Fetch live" button.

    Returns JSON (not a re-render) so the dropdown can be topped up without
    losing whatever the operator already typed into the form. ``known`` lets the
    page separate ids we have actually verified from ids the provider merely
    advertises — NVIDIA in particular lists ~82 models but only entitles the
    "Free Endpoint" subset, so the rest must not look equally trustworthy.
    """
    pid = provider.strip()
    if pid not in PROVIDERS:
        return JSONResponse({"ok": False, "error": "Unknown provider."}, status_code=400)
    if bucket not in BUCKETS:
        return JSONResponse({"ok": False, "error": "Unknown bucket."}, status_code=400)
    if key.strip() and not _VALUE_RE.match(key.strip()):
        return JSONResponse(
            {"ok": False, "error": "Key contains unexpected characters."},
            status_code=400,
        )
    resolved_base, base_error = _resolve_base(pid, base, account_id, resource)
    if base_error or not resolved_base:
        return JSONResponse(
            {"ok": False, "error": base_error or "Base URL required for this provider."},
            status_code=400,
        )

    auth_header = PROVIDERS[pid].get("auth_header")
    ok, result = await _run_op("list_models", {
        "base": resolved_base,
        "key": key.strip(),
        "auth_headers": [auth_header] if auth_header else [],
    })
    if not ok:
        return JSONResponse(
            {"ok": False, "error": result.get("error") or "Could not list models."},
            status_code=502,
        )
    if bucket.startswith("image_"):
        known = [e["id"] for e in image_options_for(pid)]
    else:
        known = [e["id"] for e in options_for(pid, vision_only=bucket.startswith("multi_"))]
    return JSONResponse({
        "ok": True,
        "models": result.get("models") or [],
        "known": known,
    })


@router.post("/keys-admin/bucket/remove")
async def keys_bucket_remove(request: Request,
                             bucket: str = Form(...),
                             row_id: str = Form(...)):
    message = error = None
    if bucket not in BUCKETS:
        error = "Unknown bucket."
    elif not row_id:
        error = "Missing entry id."
    else:
        ok, result = await _run_op("bucket", {"bucket": bucket, "action": "remove", "row_id": row_id})
        if ok:
            message = "Removed from " + BUCKETS[bucket]["label"] + ". Containers will restart shortly."
        else:
            error = result.get("error") or "Could not remove the entry."
    return _render(request, await _read_state(), message=message, error=error, restart=BUCKETS[bucket]["restart"] if not error else None)


@router.post("/keys-admin/bucket/replace")
async def keys_bucket_replace(request: Request,
                              bucket: str = Form(...),
                              row_id: str = Form(...),
                              key: str = Form(...)):
    message = error = None
    if bucket not in BUCKETS:
        error = "Unknown bucket."
    elif not row_id:
        error = "Missing entry id."
    elif not key.strip():
        error = "Key value required."
    elif not _VALUE_RE.match(key.strip()):
        error = "Key contains unexpected characters (only letters, digits, and ._/:+- allowed)."
    else:
        ok, result = await _run_op("bucket", {"bucket": bucket, "action": "replace",
                                              "row_id": row_id, "fields": {"key": key.strip()}})
        if ok:
            message = "Key replaced in " + BUCKETS[bucket]["label"] + ". Containers will restart shortly."
        else:
            error = result.get("error") or "Could not replace the key."
    return _render(request, await _read_state(), message=message, error=error, restart=BUCKETS[bucket]["restart"] if not error else None)


@router.post("/keys-admin/add")
async def keys_admin_add(request: Request, provider: str = Form(...), value: str = Form(...)):
    value = value.strip()
    message = error = None
    restart: list[str] | None = None
    if provider not in FLAT_PROVIDERS:
        error = "Unknown provider."
    else:
        pconfig = FLAT_PROVIDERS[provider]
        state = await _read_state()
        slots = state["flat"].get(provider, [])
        if not pconfig["multi"] and any(s["configured"] for s in slots):
            error = f"{pconfig['label']} is single-key only — disable the existing key first."
        elif not value:
            error = "Key value required."
        elif not _VALUE_RE.match(value):
            error = "Key contains unexpected characters (only letters, digits, and ._/:+- allowed)."
        else:
            free = next((s["env_var"] for s in slots if not s["configured"]), None)
            if free is None:
                error = f"All {len(slots)} slots for {pconfig['label']} are already in use."
            elif not _ENV_NAME_RE.match(free):
                error = "internal error: invalid slot name"
            else:
                ok, result = await _run_op("flat_set", {"env_var": free, "value": value})
                if ok:
                    message = f"Added as {free}. Containers will restart shortly."
                    restart = pconfig["restart"]
                else:
                    error = result.get("error") or "Could not add the key."
    return _render(request, await _read_state(), message=message, error=error, restart=restart)


@router.post("/keys-admin/disable")
async def keys_admin_disable(request: Request, provider: str = Form(...), env_var: str = Form(...)):
    message = error = None
    restart: list[str] | None = None
    if provider not in FLAT_PROVIDERS:
        error = "Unknown provider."
    elif not _ENV_NAME_RE.match(env_var):
        error = "Not a recognized slot."
    else:
        ok, result = await _run_op("flat_del", {"env_var": env_var})
        if ok:
            message = f"Disabled {env_var}. Containers will restart shortly."
            restart = FLAT_PROVIDERS[provider]["restart"]
        else:
            error = result.get("error") or "Could not disable the key."
    return _render(request, await _read_state(), message=message, error=error, restart=restart)