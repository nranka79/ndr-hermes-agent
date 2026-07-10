#!/usr/bin/env python3
"""
Honcho model sync watcher.

Polls the agent's config.yaml for changes to model.default / model.provider.
When either changes, rewrites Honcho's config.toml so [deriver],
[dialectic.levels.*], and [dream.*_model_config] chat model blocks follow
the SAME model and provider hermes itself is using, then restarts BOTH the
honcho-api and honcho-deriver containers.

Provider routing:
  - provider == "opencode-go" (hermes' default): honcho's chat blocks point
    directly at opencode-go too (base_url=https://opencode.ai/zen/go/v1,
    api_key_env=OPENCODE_GO_API_KEY, bare model name e.g. "deepseek-v4-flash").
    Requires OPENCODE_GO_API_KEY to be present in the honcho-api /
    honcho-deriver containers' env (copied from HERMES_HOME/.env into
    /opt/hermes/.env -- see 2026-07-10 setup).
  - any other provider: falls back to OpenRouter (base_url=
    https://openrouter.ai/api/v1, api_key_env=OPENROUTER_API_KEY), mapping
    the bare model name to an OpenRouter slug via OPENROUTER_MAP.

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
regardless of what hermes' chat provider/model is.

State is tracked in /data/hermes/.honcho_model_sync_state.json so we only
restart the containers when provider or model actually changes.
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
POLL_SECONDS = 30

OPENCODE_GO_BASE_URL = "https://opencode.ai/zen/go/v1"
OPENCODE_GO_API_KEY_ENV = "OPENCODE_GO_API_KEY"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_API_KEY_ENV = "OPENROUTER_API_KEY"

# Fallback mapping table for agent-model-name → OpenRouter-slug. Only used
# when hermes' configured provider isn't opencode-go. Add more as needed.
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


def resolve_openrouter_slug(agent_model: str) -> str:
    """Map agent-side model name to OpenRouter slug (fallback path only).

    If already in 'provider/model' form, return as-is. If bare, look up in
    OPENROUTER_MAP. If unknown, fail loud — the user must add to the map.
    """
    if not agent_model:
        raise ValueError("agent model is empty")
    if "/" in agent_model:
        return agent_model
    if agent_model in OPENROUTER_MAP:
        return OPENROUTER_MAP[agent_model]
    raise KeyError(
        f"Unknown agent model {agent_model!r}. Add it to OPENROUTER_MAP in "
        f"/opt/hermes/bin/honcho_model_sync.py and restart the watcher."
    )


def resolve_target(provider: str, model: str) -> tuple[str, str, str]:
    """Return (model_slug, base_url, api_key_env) for honcho's chat blocks.

    Mirrors the actual provider/model hermes itself is using so honcho's
    background LLM calls (deriver, dialectic, dream) go through the same
    backend as the primary agent. Falls back to OpenRouter for any
    provider other than opencode-go.
    """
    if provider == "opencode-go":
        return model, OPENCODE_GO_BASE_URL, OPENCODE_GO_API_KEY_ENV
    slug = resolve_openrouter_slug(model)
    return slug, OPENROUTER_BASE_URL, OPENROUTER_API_KEY_ENV


def get_agent_model() -> tuple[str, str]:
    """Return (provider, model) from /data/hermes/config.yaml."""
    if not AGENT_CONFIG.exists():
        return ("", "")
    with open(AGENT_CONFIG) as f:
        d = yaml.safe_load(f) or {}
    model = d.get("model", {}) or {}
    return (model.get("provider", ""), model.get("default", ""))


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
      regardless of what hermes' chat provider is)

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
    print(f"honcho-model-sync started; polling {AGENT_CONFIG} every {POLL_SECONDS}s")
    state = load_state()
    while True:
        try:
            provider, model = get_agent_model()
            if not model:
                time.sleep(POLL_SECONDS)
                continue
            if provider == state.get("last_provider") and model == state.get("last_model"):
                time.sleep(POLL_SECONDS)
                continue
            try:
                model_slug, base_url, api_key_env = resolve_target(provider, model)
            except KeyError as e:
                print(f"  SKIP: {e}", file=sys.stderr)
                time.sleep(POLL_SECONDS)
                continue
            print(f"  agent model changed: provider={provider} model={model} → "
                  f"{model_slug} @ {base_url}")
            if patch_honcho_config(model_slug, base_url, api_key_env):
                print(f"  patched {HONCHO_CONFIG}; restarting honcho-api + honcho-deriver")
                try:
                    restart_honcho()
                    print(f"  honcho-api + honcho-deriver restarted")
                except subprocess.CalledProcessError as e:
                    print(f"  ERROR restarting honcho: {e.stderr.decode()}", file=sys.stderr)
            state["last_provider"] = provider
            state["last_model"] = model
            save_state(state)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
