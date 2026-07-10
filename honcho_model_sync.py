#!/usr/bin/env python3
"""
Honcho model sync watcher.

Polls the agent's config.yaml for changes to model.default / model.provider.
When the agent's chat model changes, rewrites Honcho's config.toml to use
the matching OpenRouter slug for [deriver], [dialectic.levels.*], and
[dream.*_model_config] chat model blocks, then restarts BOTH the
honcho-api and honcho-deriver containers. Dialectic is served by
honcho-api, fact-extraction (deriver) and dream deduction/induction
specialists by honcho-deriver -- both cache their Settings in memory from
process start, so both must restart for a config.toml edit to actually
take effect. Restarting only the deriver silently leaves honcho-api's
dialectic calls on stale/default model config.

Bug found 2026-07-10: dialectic.levels.low/medium/high/max and
dream.deduction_model_config/induction_model_config had NO config.toml
override at all and were silently falling back to Honcho's hardcoded
"gpt-5.4-mini" default against OpenAI's real endpoint (api.openai.com) --
fed our OpenRouter-shaped key, which OpenAI's real auth correctly rejects.
Looked exactly like a bad API key (401 "Incorrect API key provided") but
wasn't -- the key was fine, it was just being sent to the wrong provider
for those specific unconfigured blocks. Only [dialectic.levels.minimal]
and [deriver.model_config] had explicit overrides in the original
template, so those two were the only paths that ever worked.

Embedding model is NOT touched — chat LLMs and embedding models are not
interchangeable. deepseek-v4-flash cannot generate embeddings, so the
embedding block stays pinned to openai/text-embedding-3-small unless you
manually edit config.toml.

State is tracked in /data/hermes/.honcho_model_sync_state.json so we only
restart the containers when something actually changes.
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

# Mapping table for agent-model-name → OpenRouter-slug.
# Only models the user is likely to use via /model. Add more as needed.
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
    """Map agent-side model name to OpenRouter slug.

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
    return {"last_slug": None}


def save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE_FILE.with_suffix(".tmp")
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_FILE)


def patch_honcho_config(new_slug: str) -> bool:
    """Rewrite every chat-model block in /opt/hermes-honcho/config.toml.

    Targets (regex inside the toml):
      [deriver.model_config]                       → model = "..."
      [dialectic.levels.<name>.model_config]        → model = "..."
      [dream.deduction_model_config]                → model = "..."
      [dream.induction_model_config]                → model = "..."

    Skips:
      [embedding.model_config]  (embedding model is pinned to text-embedding-3-small)

    Only patches blocks that already exist in config.toml. All five
    dialectic levels (minimal/low/medium/high/max) and both dream
    specialist blocks must have an explicit [*.model_config] block for
    this to keep them all in sync — a block that doesn't exist at all
    silently uses Honcho's built-in default model, not this slug (see
    module docstring).

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

    # Replace model line that follows [deriver.model_config] header,
    # up to the next blank line or [section] header.
    content = re.sub(
        r"(\[deriver\.model_config\][^\[]*?model = )\"[^\"]+\"",
        rf'\1"{new_slug}"',
        content,
        flags=re.DOTALL,
    )
    # Replace every [dialectic.levels.X.model_config] model line
    content = re.sub(
        r"(\[dialectic\.levels\.[\w.]+\.model_config\][^\[]*?model = )\"[^\"]+\"",
        rf'\1"{new_slug}"',
        content,
        flags=re.DOTALL,
    )
    # Replace [dream.deduction_model_config] / [dream.induction_model_config]
    content = re.sub(
        r"(\[dream\.(?:deduction|induction)_model_config\][^\[]*?model = )\"[^\"]+\"",
        rf'\1"{new_slug}"',
        content,
        flags=re.DOTALL,
    )
    if content == original:
        return False  # nothing changed (shouldn't happen if slug changed)
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
            try:
                slug = resolve_openrouter_slug(model)
            except KeyError as e:
                print(f"  SKIP: {e}", file=sys.stderr)
                time.sleep(POLL_SECONDS)
                continue
            if slug == state.get("last_slug"):
                time.sleep(POLL_SECONDS)
                continue
            print(f"  agent model changed: provider={provider} model={model} → {slug}")
            if patch_honcho_config(slug):
                print(f"  patched {HONCHO_CONFIG}; restarting honcho-api + honcho-deriver")
                try:
                    restart_honcho()
                    print(f"  honcho-api + honcho-deriver restarted")
                except subprocess.CalledProcessError as e:
                    print(f"  ERROR restarting honcho: {e.stderr.decode()}", file=sys.stderr)
            state["last_slug"] = slug
            save_state(state)
        except Exception as e:
            print(f"  ERROR: {e}", file=sys.stderr)
        time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
