"""Quota dashboard + API for the admin-app — no separate service.

The quota logic lives entirely inside the admin-app on the production box. It
fetches quota/credit data directly from the provider APIs (OpenCode Go,
OpenRouter, SuperGrok) via the in-app adapters in quota_providers/.

Endpoints:
  GET /quota              -> dashboard page (SSO session)
  GET /quota/data         -> JSON snapshot (SSO session — dashboard + Chrome ext)
  GET /quota/api/limits   -> JSON snapshot (Bearer QUOTA_API_TOKEN — Android app)

/quota/api is excluded from the session AuthMiddleware; the router enforces
the shared bearer token there so the Android app can authenticate without a
browser session.
"""

import json
import logging
import os
import random
import string
import time

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from .auth import ADMIN_EMAILS, _verify_google_id_token
from .jinja_env import env
from .quota_providers import anthropic, opencode_go, openrouter, supergrok, tokenharbor
from .quota_providers.base import Account, ProviderError, QuotaUnsupported, mask
from .quota_tokens import issue_device_token, verify_device_token

router = APIRouter()
logger = logging.getLogger("admin-app.quota")

QUOTA_API_TOKEN = os.environ.get("QUOTA_API_TOKEN", "")
CACHE_TTL_SECONDS = 60.0

# The rotation buckets keys-admin writes, in display order. Each maps to one
# LLM_*_POOL env var that arrives via env_file /opt/hermes/.env.rotator-keys —
# the same file the gateway reads — so every key added on the keys page shows
# up here with no code change. `modality` + `tier` are the two axes the
# dashboard groups by.
BUCKETS: dict[str, dict] = {
    "free": {
        "env": "LLM_FREE_POOL", "modality": "llm", "tier": "free"},
    "subscription": {
        "env": "LLM_SUBSCRIPTION_POOL", "modality": "llm", "tier": "subscription"},
    "api": {
        "env": "LLM_OPENROUTER_POOL", "modality": "llm", "tier": "api"},
    "multi_free": {
        "env": "LLM_MULTIMODAL_FREE_POOL", "modality": "multimodal", "tier": "free"},
    "multi_subscription": {
        "env": "LLM_MULTIMODAL_SUBSCRIPTION_POOL", "modality": "multimodal", "tier": "subscription"},
    "multi_token": {
        "env": "LLM_MULTIMODAL_TOKEN_POOL", "modality": "multimodal", "tier": "api"},
}

MODALITY_LABELS = {"llm": "LLM", "multimodal": "Multimodal"}
TIER_LABELS = {"free": "Free", "subscription": "Subscription", "api": "API / pay-per-call"}

PROVIDER_LABELS = {
    "opencode": "OpenCode Go", "opencode-zen": "OpenCode Zen",
    "openrouter": "OpenRouter", "tokenharbor": "Token Harbor",
    "anthropic": "Claude / Anthropic", "openai": "OpenAI",
    "gemini": "Google AI Studio",
    "cloudflare": "Cloudflare Workers AI", "deepseek": "DeepSeek",
    "azure": "Azure AI Foundry", "mistral": "Mistral AI", "groq": "Groq",
    "together": "Together AI", "fireworks": "Fireworks AI",
    "supergrok": "SuperGrok", "openorca": "OpenOrca",
    "openai-compatible": "Custom OpenAI-compatible",
}


def _norm(provider: str) -> str:
    """Normalize a provider id the same way the gateway does, so "opencode",
    "OpenCode Go" and "opencode-go" all resolve to one adapter."""
    return "".join(c for c in (provider or "").lower() if c.isalnum())


# Quota adapters, keyed by normalized provider id. A provider absent from this
# table is still listed on the dashboard — it just reports "no quota surface".
PROVIDERS = {
    "opencode": opencode_go.fetch,
    "opencodego": opencode_go.fetch,
    "openrouter": openrouter.fetch,
    "tokenharbor": tokenharbor.fetch,
    "anthropic": anthropic.fetch,
    "claude": anthropic.fetch,
    "supergrok": supergrok.fetch,
}

# Flat env-var series still consulted for keys that never made it into a pool
# (legacy vars, or a key added straight to the VPS env). Pool entries win; a
# flat key is only added when its value is not already covered above.
FLAT_SERIES: list[tuple[str, list[str], str]] = [
    ("opencode",
     ["OPENCODE_GO_API_KEY", "OPENCODE_API_KEY", "OPENCODE_GO_KEY_3"]
     + [f"OPENCODE_GO_API_KEY_{i}" for i in range(4, 21)],
     "subscription"),
    ("openrouter",
     ["OPENROUTER_API_KEY"] + [f"OPENROUTER_API_KEY_{i}" for i in range(2, 21)],
     "api"),
    ("tokenharbor",
     ["TOKENHARBOR_API_KEY"] + [f"TOKENHARBOR_API_KEY_{i}" for i in range(2, 21)],
     "api"),
]

# Credentials that exist purely for quota reporting — they are not LLM
# rotation keys, so keys-admin holds them as flat provider keys. The Anthropic
# one is an Admin API key, distinct from any "anthropic" routing key in the API
# pool: only the admin key can read the org cost report.
QUOTA_ONLY: list[tuple[str, str, str, str, str]] = [
    ("supergrok", "XAI_OAUTH_TOKEN", "llm", "subscription", "SuperGrok"),
    ("anthropic", "ANTHROPIC_ADMIN_API_KEY", "llm", "api", "Claude / Anthropic — org spend"),
]


def _pool_entries(env_var: str) -> list[dict]:
    raw = (os.environ.get(env_var) or "").strip()
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
    except ValueError:
        logger.warning("quota: %s is not valid JSON", env_var)
        return []
    return [e for e in parsed if isinstance(e, dict)] if isinstance(parsed, list) else []


def _label(provider: str, n: int, total: int) -> str:
    base = PROVIDER_LABELS.get(provider, provider or "unknown")
    return f"{base} #{n}" if total > 1 else base


def _discover() -> list[Account]:
    """Build the account list from the rotation pools, then top it up with any
    flat keys the pools do not already cover."""
    accounts: list[Account] = []
    seen: set[str] = set()

    for bucket_id, spec in BUCKETS.items():
        entries = [e for e in _pool_entries(spec["env"]) if e.get("key")]
        counts: dict[str, int] = {}
        for e in entries:
            p = str(e.get("provider") or "").strip()
            counts[p] = counts.get(p, 0) + 1
        seq: dict[str, int] = {}
        for e in entries:
            key = str(e["key"]).strip()
            provider = str(e.get("provider") or "").strip()
            seq[provider] = seq.get(provider, 0) + 1
            seen.add(key)
            accounts.append(Account(
                id=f"{bucket_id}:{e.get('id') or seq[provider]}",
                provider=provider,
                label=_label(provider, seq[provider], counts.get(provider, 1)),
                api_key=key,
                modality=spec["modality"],
                tier=spec["tier"],
                bucket=bucket_id,
                model=str(e.get("model") or ""),
                base=str(e.get("base") or ""),
                extra={"management_key_env": "OPENROUTER_MANAGEMENT_KEY"},
            ))

    for provider, env_vars, tier in FLAT_SERIES:
        present = [(v, os.environ[v].strip()) for v in env_vars
                   if (os.environ.get(v) or "").strip()]
        extra = [(v, k) for v, k in present if k not in seen]
        for n, (env_var, key) in enumerate(extra, start=1):
            seen.add(key)
            accounts.append(Account(
                id=f"flat:{env_var}",
                provider=provider,
                label=f"{PROVIDER_LABELS.get(provider, provider)} ({env_var})",
                api_key_env=env_var,
                modality="llm",
                tier=tier,
                bucket=f"flat_{tier}",
                extra={"management_key_env": "OPENROUTER_MANAGEMENT_KEY"},
            ))

    for provider, env_var, modality, tier, label in QUOTA_ONLY:
        if not (os.environ.get(env_var) or "").strip():
            continue
        accounts.append(Account(
            id=f"flat:{env_var}",
            provider=provider,
            label=label,
            token_env=env_var,
            modality=modality,
            tier=tier,
            bucket=f"flat_{tier}",
        ))

    return accounts


_cache = {"payload": None, "fetched_at": 0.0}


async def _refresh() -> dict:
    results = {}
    async with httpx.AsyncClient(timeout=20) as client:
        for acc in _discover():
            credential = acc.credential()
            entry = {
                "id": acc.id,
                "provider": acc.provider,
                "label": acc.label,
                "modality": acc.modality,
                "tier": acc.tier,
                "bucket": acc.bucket,
                "model": acc.model,
                "masked": mask(credential),
                "configured": bool(credential),
            }
            fetch = PROVIDERS.get(_norm(acc.provider))
            if not credential:
                entry["error"] = f"{acc.credential_env()} not set"
            elif fetch is None:
                entry["unsupported"] = f"{acc.provider} does not publish a quota API"
            else:
                try:
                    entry.update(await fetch(acc, client))
                except QuotaUnsupported as exc:
                    entry["unsupported"] = str(exc)
                except ProviderError as exc:
                    entry["error"] = str(exc)
                except Exception as exc:  # noqa: BLE001 - degrade per-account
                    logger.warning("quota fetch %s failed: %s", acc.id, exc)
                    entry["error"] = f"{type(exc).__name__}: {exc}"
            results[acc.id] = entry
    return results


async def _snapshot(fresh: bool = False) -> dict:
    now = time.time()
    if fresh or _cache["payload"] is None or (now - _cache["fetched_at"]) > CACHE_TTL_SECONDS:
        _cache["payload"] = await _refresh()
        _cache["fetched_at"] = now
    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(_cache["fetched_at"])),
        "cache_ttl_seconds": CACHE_TTL_SECONDS,
        "groups": {"modalities": MODALITY_LABELS, "tiers": TIER_LABELS},
        "accounts": _cache["payload"],
    }


@router.get("/quota")
async def quota_page(request: Request):
    return HTMLResponse(env.get_template("quota.html").render(user=request.session.get("user")))


@router.get("/quota/data")
async def quota_data():
    return JSONResponse(await _snapshot())


@router.get("/quota/api/limits")
async def quota_api_limits(authorization: str | None = Header(default=None)):
    token = _bearer(authorization)
    if not token:
        raise HTTPException(401, "missing or malformed Authorization header")
    # Accept the shared admin token OR a device token issued at device-login
    # (which is only issued to admin users after Google sign-in).
    if token != QUOTA_API_TOKEN and not verify_device_token(token):
        raise HTTPException(401, "invalid token")
    return JSONResponse(await _snapshot())


@router.post("/quota/api/device-login")
async def quota_device_login(request: Request):
    """Android sign-in: verify the app's Google ID token and issue a device
    token. Only admin-allowlisted emails (ADMIN_EMAILS) are accepted — the
    same users who can use admin.ahfl.in."""
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        raise HTTPException(400, "invalid JSON body") from None
    id_token = (body.get("id_token") or "").strip()
    if not id_token:
        raise HTTPException(400, "id_token required")
    try:
        claims = await _verify_google_id_token(id_token)
    except Exception:  # noqa: BLE001 - invalid token / signature failure
        claims = None
    email = (claims or {}).get("email", "").lower()
    if not email:
        raise HTTPException(401, "invalid Google token")
    if email not in ADMIN_EMAILS:
        raise HTTPException(403, "not an admin user")
    device_token = issue_device_token(email)
    return JSONResponse({"token": device_token, "email": email, "expires_in": 30 * 86400})


def _bearer(authorization: str | None) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        return ""
    return authorization[len("Bearer "):]


# --- Device pairing (sign in with browser — no GCP Android client needed) ---
# The Android app calls /quota/api/pair/start, opens admin.ahfl.in/quota/pair
# in the browser, the (already SSO-authenticated) user confirms, and the app
# polls /quota/api/pair/poll until it gets a device token.

PAIR_TTL_SECONDS = 300
_pairs: dict = {}


def _new_pair_code() -> str:
    while True:
        code = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if code not in _pairs:
            return code


@router.post("/quota/api/pair/start")
async def pair_start():
    code = _new_pair_code()
    _pairs[code] = {"email": None, "expires": time.time() + PAIR_TTL_SECONDS}
    return JSONResponse({"code": code, "expires_in": PAIR_TTL_SECONDS})


@router.get("/quota/pair")
async def pair_page(request: Request, code: str = ""):
    pair = _pairs.get(code)
    if not pair:
        return HTMLResponse("Invalid or expired pairing code.", status_code=400)
    user = request.session.get("user") or {}
    session_email = (user.get("email") or "").lower()
    confirmed = pair["email"] is not None
    return HTMLResponse(env.get_template("pair.html").render(
        code=code,
        email=pair["email"] or session_email,
        confirmed=confirmed,
        paired_email=pair["email"],
    ))


@router.post("/quota/pair/confirm")
async def pair_confirm(request: Request):
    form = await request.form()
    code = (form.get("code") or "").strip()
    pair = _pairs.get(code)
    user = request.session.get("user") or {}
    email = (user.get("email") or "").lower()
    if not pair:
        return HTMLResponse("Invalid or expired pairing code.", status_code=400)
    if not email:
        return RedirectResponse("/auth/login")
    pair["email"] = email
    # status_code=303: force the browser to re-issue as GET. The default
    # (307) preserves the original POST, which 405s against this GET-only
    # route — that was the "method not allowed" bug after confirming.
    return RedirectResponse(f"/quota/pair?code={code}&confirmed=1", status_code=303)


@router.get("/quota/api/pair/poll")
async def pair_poll(code: str = ""):
    pair = _pairs.get(code)
    if not pair:
        return JSONResponse({"status": "invalid"})
    if time.time() > pair["expires"]:
        _pairs.pop(code, None)
        return JSONResponse({"status": "expired"})
    if not pair["email"]:
        return JSONResponse({"status": "pending"})
    token = issue_device_token(pair["email"])
    _pairs.pop(code, None)
    return JSONResponse({
        "status": "approved",
        "token": token,
        "email": pair["email"],
        "expires_in": 30 * 86400,
    })