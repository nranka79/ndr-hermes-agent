#!/usr/bin/env python3
"""
Honcho model pin (formerly "sync watcher").

Pins Honcho's chat model — [deriver], [dialectic.levels.*], and
[dream.*_model_config] — to a FIXED, INDEPENDENT model that has NOTHING to
do with whatever model the main Hermes agent (model.default / model.provider
in config.yaml) happens to be running.

--- Why this changed (2026-07-10) ---
This used to mirror the agent's live model 1:1, restarting honcho-api +
honcho-deriver every time model.default changed. That seemed like a good
idea (keep Honcho "on the same brain" as the agent) but had a real cost:
Honcho's dialectic_chat does its OWN internal agentic tool loop (5-14
sequential search_memory / search_messages / get_messages_by_date_range
calls per query — one full LLM round trip per hop). When the agent's model
was switched to a big frontier reasoning model (grok-4.3), every Honcho
query started taking 20-62 seconds — blowing straight through the 30s
client-side timeout in plugins/memory/honcho/client.py and stalling
delivery of already-computed agent responses (see client.py's own comment:
Honcho calls happen on run_conversation's post-response path). This is what
users saw as "Open WebUI shows busy / no response" — the answer was ready,
Honcho just wouldn't let go of the request in time.

Honcho's job (structured extraction + tool-driven retrieval, not
user-facing judgment calls) doesn't need frontier-model reasoning quality.
A fast/cheap model does the same 5-14 hops in a couple of seconds instead
of a minute. So: independent pin, not a mirror.

--- Configuring Honcho's model ---
Set in /opt/hermes/.env (both read by this script AND passed through to the
honcho-api/honcho-deriver containers via env_file in docker-compose.override.yml):

  HONCHO_CHAT_PROVIDER=opencode-go     # default if unset
  HONCHO_CHAT_MODEL=deepseek-v4-flash  # default if unset

Provider routing (same resolution logic as before):
  - provider == "opencode-go": honcho's chat blocks point directly at
    opencode-go (base_url=https://opencode.ai/zen/go/v1,
    api_key_env=OPENCODE_GO_API_KEY, bare model name e.g. "deepseek-v4-flash").
    This is the default pin — already proven working on this stack (this
    exact pairing served both the agent AND Honcho successfully before the
    agent was switched to grok-4.3), and OPENCODE_GO_API_KEY is already
    present in the honcho-api / honcho-deriver containers' env.
  - any other provider: falls back to OpenRouter (base_url=
    https://openrouter.ai/api/v1, api_key_env=OPENROUTER_API_KEY), mapping
    the bare model name to an OpenRouter slug via OPENROUTER_MAP.

To change Honcho's model later: edit HONCHO_CHAT_PROVIDER / HONCHO_CHAT_MODEL
in /opt/hermes/.env, then `docker compose -f docker-compose.yml -f
docker-compose.override.yml restart honcho-model-sync` (it re-patches once
at startup and exits into an idle wait — see main()). Changing the AGENT's
model.default in config.yaml no longer has ANY effect on Honcho — that
coupling is gone on purpose.

Both honcho-api and honcho-deriver must restart together: each caches its
config.toml-derived Settings in memory from process start and never
re-reads the file. honcho-api serves the dialectic (chat) endpoint;
honcho-deriver serves background fact-extraction and dream
deduction/induction. Restarting only one leaves the other running on
stale/default model config -- see 2026-07-10 postmortem: dialectic.levels.
low/medium/high/max and dream.deduction/induction_model_config had NO
config.toml override at all for a long time and silently fell back to
Honcho's hardcoded "gpt-5.4-mini" default against OpenAI's real endpoint,
fed an OpenRouter-shaped key -- looked exactly like a bad API key (401
"Incorrect API key provided") but wasn't.

Embedding model is NOT touched — chat LLMs and embedding models are not
interchangeable, and opencode-go has no embeddings endpoint. The embedding
block stays pinned to openai/text-embedding-3-small via OpenRouter
regardless of what Honcho's chat provider/model is.

State is tracked in /data/hermes/.honcho_model_sync_state.json so we only
restart the containers when the pinned provider/model actually changes
across a restart of this watcher (e.g. after editing .env).
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import yaml

AGENT_CONFIG = Path(os.environ.get("HERMES_HOME", "/data/hermes")) / "config.yaml"
HONCHO_CONFIG = Path("/opt/hermes-honcho/config.toml")
STATE_FILE = Path(os.environ.get("HERMES_HOME", "/data/hermes")) / ".honcho_model_sync_state.json"

# How often to re-check (idle heartbeat only — the pinned model is fixed
# for the life of this process via env vars, so there's nothing to detect
# short of a container recreation, which re-runs main() from scratch anyway).
IDLE_HEARTBEAT_SECONDS = 3600

OPENCODE_GO_BASE_URL = "https://opencode.ai/zen/go/v1"
OPENCODE_GO_API_KEY_ENV = "OPENCODE_GO_API_KEY"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"

# Independent pin for Honcho's own chat model — NOT tied to the agent's
# model.default. See module docstring for why.
DEFAULT_HONCHO_CHAT_PROVIDER = "opencode-go"
DEFAULT_HONCHO_CHAT_MODEL = "deepseek-v4-flash"

# Fallback mapping table for honcho-model-name -> OpenRouter-slug. Only used
# when HONCHO_CHAT_PROVIDER isn't opencode-go. Add more as needed.
OPENROUTER_MAP = {
    "deepseek-v4-flash": "deepseek/deepseek-v4-flash",
    "deepseek-chat": "deepseek/deepseek-chat",
    "deepseek-reasoner": "deepseek/deepseek-reasoner",
    "deepseek-r1": "deepseek/deepseek-r1",
    "gpt-4o": "openai/gpt-4o",
    "gpt-4o-mini": "openai/gpt-4o-mini",
    "gpt-4.1": "openai/gpt-4.1",
    "gpt-4.1-mini": "openai/gpt-4.1-mini",
    "gpt-5": "openai/gpt-5",
    "gpt-5-mini": "openai/gpt-5-mini",
    "o1": "openai/o1",
    "o1-mini": "openai/o1-mini",
    "o3": "openai/o3",
    "o3-mini": "openai/o3-mini",
    "o4-mini": "openai/o4-mini",
    "grok-4.3": "x-ai/grok-4.3",
    "grok-4.5": "x-ai/grok-4.5",
    "grok-latest": "x-ai/grok-latest",
    "claude-opus-4": "anthropic/claude-opus-4",
    "claude-sonnet-4": "anthropic/claude-sonnet-4",
    "claude-haiku-4": "anthropic/claude-haiku-4",
    "claude-3.5-sonnet": "anthropic/claude-3.5-sonnet",
    "claude-3.5-haiku": "anthropic/claude-3.5-haiku",
    "gemini-2.5-pro": "google/gemini-2.5-pro",
    "gemini-2.5-flash": "google/gemini-2.5-flash",
    "gemini-2.5-flash-lite": "google/gemini-2.5-flash-lite",
    "gemini-2.0-flash": "google/gemini-2.0-flash",
    "qwen-2.5-72b": "qwen/qwen-2.5-72b-instruct",
    "llama-3.3-70b": "meta-llama/llama-3.3-70b-instruct",
    "llama-3.1-405b": "meta-llama/llama-3.1-405b-instruct",
    "mistral-large": "mistralai/mistral-large-latest",
}


def resolve_openrouter_slug(honcho_model: str) -> str:
    """Map a bare honcho-side model name to OpenRouter slug (fallback path only).

    If already in 'provider/model' form, return as-is. If bare, look up in
    OPENROUTER_MAP. If unknown, fail loud — the user must add to the map.
    """
    if not honcho_model:
        raise ValueError("honcho model is empty")
    if "/" in honcho_model:
        return honcho_model
    if honcho_model in OPENROUTER_MAP:
        return OPENROUTER_MAP[honcho_model]
    raise KeyError(
        f"Unknown honcho model {honcho_model!r}. Add it to OPENROUTER_MAP in "
        f"/opt/hermes/bin/honcho_model_sync.py and restart honcho-model-sync."
    )


def resolve_target(provider: str, model: str) -> tuple[str, str, str]:
    """Return (model_slug, base_url, api_key_env) for honcho's chat blocks."""
    if provider == "opencode-go":
        return model, OPENCODE_GO_BASE_URL, OPENCODE_GO_API_KEY_ENV
    slug = resolve_openrouter_slug(model)
    return slug, OPENROUTER_BASE_URL, OPENROUTER_API_KEY_ENV


def get_honcho_model() -> tuple[str, str]:
    """Return (provider, model) Honcho should use — independent pin via env vars.

    Defaults to opencode-go/deepseek-v4-flash (fast, already proven working
    on this stack) if the env vars aren't set. This is deliberately NOT
    read from the agent's config.yaml — see module docstring.
    """
    provider = os.environ.get("HONCHO_CHAT_PROVIDER", DEFAULT_HONCHO_CHAT_PROVIDER).strip()
    model = os.environ.get("HONCHO_CHAT_MODEL", DEFAULT_HONCHO_CHAT_MODEL).strip()
    return (provider or DEFAULT_HONCHO_CHAT_PROVIDER, model or DEFAULT_HONCHO_CHAT_MODEL)


def get_agent_model_for_logging() -> tuple[str, str]:
    """Best-effort read of the agent's current model, for informational
    log output only. Never used to decide Honcho's model. Failures are
    silent — this is a nice-to-have comparison line, not load-bearing."""
    try:
        if not AGENT_CONFIG.exists():
            return ("", "")
        with open(AGENT_CONFIG) as f:
            d = yaml.safe_load(f) or {}
        model = d.get("model", {}) or {}
        return (model.get("provider", ""), model.get("default", ""))
    except Exception:
        return ("", "")


def load_state() -> dict:
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE) as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_provider": None, "last_model": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)


# Block header patterns for each honcho chat-model surface we manage.
# Each pattern matches the [<section>.model_config] header; the patch
# function extends the match through the immediately-following
# [<section>.model_config.overrides] sub-block so model/base_url/
# api_key_env can all be rewritten together in one pass.
_BLOCK_HEADERS = (
    r"\[deriver\.model_config\]",
    r"\[dialectic\.levels\.[\w.]+\.model_config\]",
    r"\[dream\.(?:deduction|induction)_model_config\]",
)


def _patch_block(content: str, header_pattern: str, model_slug: str, base_url: str, api_key_env: str) -> str:
    """Rewrite model/base_url/api_key_env within every block matching header_pattern.

    Captures from the block header through its trailing .overrides
    sub-block (up to the next top-level-ish [section] or end of file),
    then does targeted field substitution inside that captured span only
    — so this never touches [embedding.model_config...], which uses a
    completely different header pattern and is intentionally excluded.
    """
    span_pattern = re.compile(
        header_pattern + r"[^\[]*\[[^\]]*\.overrides\][^\[]*",
        re.DOTALL,
    )

    def _repl(m: re.Match) -> str:
        chunk = m.group(0)
        chunk = re.sub(r'(model = )"[^"]+"', rf'\1"{model_slug}"', chunk)
        chunk = re.sub(r'(base_url = )"[^"]+"', rf'\1"{base_url}"', chunk)
        chunk = re.sub(r'(api_key_env = )"[^"]+"', rf'\1"{api_key_env}"', chunk)
        return chunk

    return span_pattern.sub(_repl, content)


def patch_honcho_config(model_slug: str, base_url: str, api_key_env: str) -> bool:
    """Rewrite every chat-model block in /opt/hermes-honcho/config.toml.

    Targets:
      [deriver.model_config] + [.overrides]
      [dialectic.levels.<name>.model_config] + [.overrides]  (all levels present)
      [dream.deduction_model_config] + [.overrides]
      [dream.induction_model_config] + [.overrides]

    Skips:
      [embedding.model_config]  (different header pattern, never matched here;
      embedding is pinned to openai/text-embedding-3-small via OpenRouter
      regardless of what Honcho's chat provider is)

    Only patches blocks that already exist in config.toml. A level/specialist
    with no [*.model_config] block at all silently uses Honcho's hardcoded
    default model against OpenAI's real endpoint, not this target — see
    module docstring for the incident this caused.

    Implementation note: we do an in-place write (read+rewrite) rather than
    os.replace(tmp, target) because honcho-deriver holds the target file
    open at the file-descriptor level, which makes rename fail with
    EBUSY even when the mount is read-only.
    """
    if not HONCHO_CONFIG.exists():
        print(f"ERROR: {HONCHO_CONFIG} does not exist", file=sys.stderr)
        return False
    with open(HONCHO_CONFIG) as f:
        content = f.read()
    original = content

    for header_pattern in _BLOCK_HEADERS:
        content = _patch_block(content, header_pattern, model_slug, base_url, api_key_env)

    if content == original:
        return False  # nothing changed (shouldn't happen if target changed)
    # In-place rewrite to avoid rename(EBUSY) when honcho-deriver has the
    # file open via its read-only mount. Truncate-then-write keeps the
    # same inode, so other containers' open file descriptors see the new
    # content on their next read.
    with open(HONCHO_CONFIG, "r+") as f:
        f.seek(0)
        f.write(content)
        f.truncate()
    return True


def restart_honcho() -> None:
    """Restart both honcho-api and honcho-deriver.

    Both containers load config.toml into an in-memory Settings object
    once at process start and never re-read it. honcho-api serves the
    dialectic (chat) endpoint; honcho-deriver serves background fact
    extraction and dream deduction/induction. A config.toml edit only
    takes effect for the container(s) restarted, so both must restart
    together or one silently keeps running on stale config.
    """
    subprocess.run(
        ["docker", "compose", "-f", "/opt/hermes/docker-compose.yml",
         "-f", "/opt/hermes/docker-compose.override.yml",
         "restart", "honcho-api", "honcho-deriver"],
        check=True,
        capture_output=True,
    )


def main() -> None:
    provider, model = get_honcho_model()
    agent_provider, agent_model = get_agent_model_for_logging()
    print(
        f"honcho-model-pin: pinning Honcho to provider={provider} model={model} "
        f"(independent of the agent's current model="
        f"{agent_provider or '?'}/{agent_model or '?'} — no longer mirrored)"
    )

    state = load_state()
    if provider == state.get("last_provider") and model == state.get("last_model"):
        print("  no change since last pin — leaving honcho-api/honcho-deriver as-is")
    else:
        try:
            model_slug, base_url, api_key_env = resolve_target(provider, model)
        except KeyError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            print("  keeping previous pin; fix HONCHO_CHAT_PROVIDER/HONCHO_CHAT_MODEL and restart", file=sys.stderr)
        else:
            print(f"  target: {model_slug} @ {base_url}")
            if patch_honcho_config(model_slug, base_url, api_key_env):
                print(f"  patched {HONCHO_CONFIG}; restarting honcho-api + honcho-deriver")
                try:
                    restart_honcho()
                    print("  honcho-api + honcho-deriver restarted")
                except subprocess.CalledProcessError as e:
                    print(f"  ERROR restarting honcho: {e.stderr.decode()}", file=sys.stderr)
            else:
                print("  config.toml already matched target — no restart needed")
            state["last_provider"] = provider
            state["last_model"] = model
            save_state(state)

    # Idle forever. The pin is fixed for this process's lifetime via env
    # vars; there is nothing to poll. Recreate/restart this container
    # (after editing HONCHO_CHAT_PROVIDER/HONCHO_CHAT_MODEL in .env) to
    # apply a new pin.
    while True:
        time.sleep(IDLE_HEARTBEAT_SECONDS)


if __name__ == "__main__":
    main()
