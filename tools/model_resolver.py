"""
model_resolver — turn free-text model keywords ("deep thinking opus latest",
"cheapest gemini flash", "claude opus 4.6") into a concrete OpenRouter model id.

Why this exists: tools/openrouter_tool.py used to require the user's trigger
phrase to contain one of 9 hardcoded brand words (gemini/gpt/claude/deepseek/
qwen/kimi/llama/mistral/grok). Asks like "a deep thinking model" or "the
latest Opus" matched none of them and were hard-refused ("no provision to
select a model"). This module replaces that fixed list with a real lookup
against OpenRouter's live model catalog, so vendor, tier (opus/flash/mini/...),
explicit version, reasoning-capability ("deep thinking"), and "give me the
latest" are all resolved dynamically instead of going stale every time a new
model ships.

Scope: resolves against the OpenRouter pay-per-use catalog only. It does NOT
check whether a cheaper match already exists in the Hermes gateway's free/
subscription buckets -- the gateway's /health endpoint only exposes bucket
entry *counts*, not which models they hold, so that preference is a known
fast-follow (would need a small new read-only gateway endpoint), not
implemented here. Added 2026-10-02.
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from typing import Optional

_CATALOG_URL = "https://openrouter.ai/api/v1/models"
_CACHE_PATH = "/data/hermes/cache/openrouter_catalog.json"
_CACHE_TTL_SECONDS = 900  # 15 min -- catalog changes rarely; avoid hammering on every call

# token -> OpenRouter id prefix
_VENDOR_ALIASES: dict[str, str] = {
    "gemini": "google/", "google": "google/",
    "claude": "anthropic/", "anthropic": "anthropic/",
    "opus": "anthropic/", "sonnet": "anthropic/", "haiku": "anthropic/",
    "gpt": "openai/", "openai": "openai/", "o1": "openai/", "o3": "openai/", "o4": "openai/",
    "deepseek": "deepseek/",
    "qwen": "qwen/", "alibaba": "qwen/",
    "kimi": "moonshotai/", "moonshot": "moonshotai/",
    "llama": "meta-llama/", "meta": "meta-llama/",
    "mistral": "mistralai/", "mixtral": "mistralai/",
    "grok": "x-ai/", "xai": "x-ai/",
    "nemotron": "nvidia/", "nvidia": "nvidia/",
}

# Tier/size substrings matched against the model id itself.
_TIER_TOKENS = (
    "opus", "sonnet", "haiku", "flash", "pro", "mini", "nano", "lite",
    "max", "ultra", "air", "r1", "o1", "o3", "o4",
)

# When the user asks for "deep thinking" / "best" / "flagship" without
# naming a tier, bias toward each vendor's top-end tier instead of whatever
# happens to have the newest point-release timestamp (a vendor's smaller
# model can ship a patch release more recently than its flagship).
_FLAGSHIP_TIER = {
    "anthropic/": "opus",
    "openai/": "o3",
    "google/": "pro",
    "deepseek/": "r1",
}

_THINKING_WORDS = (
    "thinking", "think", "reasoning", "reason", "smartest", "smart",
    "flagship", "frontier", "most capable", "best", "deep",
)

_CHEAP_WORDS = ("cheap", "cheapest", "free", "budget")

# Vendor preference order when the user asks for "deep thinking" / "best"
# with no vendor named -- first vendor with a usable reasoning-capable
# candidate wins.
_THINKING_VENDOR_ORDER = ("anthropic/", "openai/", "deepseek/", "google/", "x-ai/")

_EXCLUDE_SUFFIXES = (":batch",)

_VERSION_RE = re.compile(r"\b\d+(?:\.\d+){0,2}\b")


def _fetch_catalog(force: bool = False) -> list[dict]:
    """Fetch+cache the OpenRouter model catalog (id, created, supported_parameters, ...)."""
    try:
        if not force and os.path.exists(_CACHE_PATH):
            age = time.time() - os.path.getmtime(_CACHE_PATH)
            if age < _CACHE_TTL_SECONDS:
                with open(_CACHE_PATH, "r", encoding="utf-8") as f:
                    return json.load(f)
    except Exception:
        pass

    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment")
    req = urllib.request.Request(_CATALOG_URL, headers={"Authorization": f"Bearer {key}"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    models = [m for m in data.get("data", []) if isinstance(m, dict) and m.get("id")]

    try:
        os.makedirs(os.path.dirname(_CACHE_PATH), exist_ok=True)
        with open(_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(models, f)
    except Exception:
        pass  # cache is best-effort; a failed write must never break resolution

    return models


def _find_vendor_prefix(text: str) -> Optional[str]:
    for token in sorted(_VENDOR_ALIASES, key=len, reverse=True):
        if re.search(rf"\b{re.escape(token)}\b", text):
            return _VENDOR_ALIASES[token]
    return None


def _find_tier(text: str) -> Optional[str]:
    for tier in _TIER_TOKENS:
        if re.search(rf"\b{re.escape(tier)}\b", text):
            return tier
    return None


def _wants_reasoning(text: str) -> bool:
    return any(w in text for w in _THINKING_WORDS)


def _wants_cheap(text: str) -> bool:
    return any(w in text for w in _CHEAP_WORDS)


def _explicit_version(text: str) -> Optional[str]:
    m = _VERSION_RE.search(text)
    return m.group(0) if m else None


def _is_excluded(model_id: str) -> bool:
    return any(model_id.endswith(suf) for suf in _EXCLUDE_SUFFIXES)


def _candidate_pool(catalog: list[dict], vendor_prefix: Optional[str]) -> list[dict]:
    pool = [m for m in catalog if not _is_excluded(m["id"])]
    if vendor_prefix:
        pool = [m for m in pool if m["id"].startswith(vendor_prefix)]
    return pool


def resolve_openrouter_model(keywords: str) -> dict:
    """Resolve free-text *keywords* to a concrete OpenRouter model id.

    Returns on success:  {"model": "<id>", "note": "<why this one>"}
    Returns on failure:  {"error": "<message>", "candidates": [<id>, ...]}
    """
    text = (keywords or "").strip().lower()
    if not text:
        return {"error": "No keywords given."}

    vendor_prefix = _find_vendor_prefix(text)
    tier = _find_tier(text)
    reasoning_required = _wants_reasoning(text)
    cheap = _wants_cheap(text)
    version = _explicit_version(text)

    # No recognizable signal at all (no vendor, no tier, no capability word,
    # no version, no cheap/free word) -- refuse instead of silently handing
    # back whatever happens to be the single newest model in the entire
    # 400+ entry catalog, which would be a confident-looking wrong answer.
    if not any([vendor_prefix, tier, reasoning_required, cheap, version]):
        return {
            "error": f"Could not identify any vendor, tier, or capability in '{keywords}'.",
            "candidates": [],
        }

    try:
        catalog = _fetch_catalog()
    except Exception as e:
        return {"error": f"Could not fetch OpenRouter model catalog: {e}"}

    vendor_candidates = [vendor_prefix] if vendor_prefix else (
        list(_THINKING_VENDOR_ORDER) if reasoning_required else [None]
    )

    for v_prefix in vendor_candidates:
        pool = _candidate_pool(catalog, v_prefix)
        if not pool:
            continue

        # Reasoning asks with no explicit tier bias toward the vendor's
        # flagship tier rather than pure recency (see _FLAGSHIP_TIER above).
        effective_tier = tier or (
            _FLAGSHIP_TIER.get(v_prefix) if (reasoning_required and v_prefix) else None
        )

        filtered = pool
        if effective_tier:
            tier_hits = [m for m in filtered if effective_tier in m["id"]]
            if tier_hits:
                filtered = tier_hits
        if version:
            ver_hits = [m for m in filtered if version in m["id"]]
            if ver_hits:
                best = max(ver_hits, key=lambda m: m.get("created", 0))
                return {
                    "model": best["id"],
                    "note": f"Matched explicit version '{version}' under {v_prefix or 'any vendor'}.",
                }
        if reasoning_required:
            think_hits = [m for m in filtered if "reasoning" in (m.get("supported_parameters") or [])]
            if think_hits:
                filtered = think_hits
        if cheap:
            free_hits = [m for m in filtered if m["id"].endswith(":free")]
            if free_hits:
                filtered = free_hits

        if not filtered:
            continue

        best = max(filtered, key=lambda m: m.get("created", 0))
        note_bits = []
        if v_prefix:
            note_bits.append(f"vendor={v_prefix.rstrip('/')}")
        if effective_tier:
            note_bits.append(f"tier={effective_tier}")
        if reasoning_required:
            note_bits.append(
                "reasoning-capable" if "reasoning" in (best.get("supported_parameters") or [])
                else "reasoning not confirmed on best available match"
            )
        note_bits.append("picked latest by release date")
        return {"model": best["id"], "note": "; ".join(note_bits)}

    fallback_pool = _candidate_pool(catalog, vendor_prefix)[:5]
    return {
        "error": f"Could not confidently resolve a model from '{keywords}'.",
        "candidates": [m["id"] for m in fallback_pool],
    }
