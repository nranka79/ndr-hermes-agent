"""
model-changer skill script -- writes a model-switch request for the CURRENT
chat session. Runs as a subprocess via the `terminal` tool, so it cannot
mutate the live gateway's in-memory agent state directly; it drops a small
JSON request file keyed by this session's HERMES_SESSION_KEY (exported by
tools/terminal_tool.py), which gateway/run.py's
_consume_pending_skill_model_switch() picks up and applies on the NEXT
incoming message -- the "from your next message onwards" contract the skill
always documented, now actually wired up (pre 2026-10-02 nobody read this
file's output at all -- see SKILL.md history).

Usage:
    python scripts/main.py -- <keyword-or-free-text>

Keyword shortcuts (fast path, no network call):
    minimax, nematron, gemini2, gemini3, qwen

Anything else is resolved against OpenRouter's live model catalog via
tools.model_resolver (vendor / tier / "deep thinking" / "latest" / explicit
version / "cheapest" -- see that module's docstring), e.g.:
    python scripts/main.py -- "deep thinking opus"
    python scripts/main.py -- "cheapest gemini flash"
    python scripts/main.py -- "claude opus 4.6"
"""
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/hermes")  # so `tools.model_resolver` imports regardless of cwd

MODEL_MAPPINGS = {
    "minimax":  {"provider": "MiniMax",    "model": "Minimax-M2.7"},
    "nematron": {"provider": "OpenRouter", "model": "nvidia/nemotron-3-super-120b-a12b:free"},
    "gemini2":  {"provider": "OpenRouter", "model": "google/gemini-2.5-flash-lite"},
    "gemini3":  {"provider": "OpenRouter", "model": "google/gemini-3-flash-preview"},
    "qwen":     {"provider": "OpenRouter", "model": "qwen/qwen3.6-plus:free"},
}

REQUEST_DIR = Path("/data/hermes/model_switch_requests")


def _session_key() -> str:
    return os.environ.get("HERMES_SESSION_KEY", "").strip()


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scripts/main.py -- <keyword-or-free-text>")
        print(f"Keyword shortcuts: {', '.join(MODEL_MAPPINGS.keys())}")
        print("Anything else is resolved from OpenRouter's catalog (vendor/tier/'deep thinking'/'latest'/version).")
        return 1

    raw = (sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == "--" else sys.argv[1])
    keyword_lower = raw.strip().lower()

    if keyword_lower in MODEL_MAPPINGS:
        cfg = MODEL_MAPPINGS[keyword_lower]
        provider, model, label = cfg["provider"], cfg["model"], keyword_lower.capitalize()
    else:
        try:
            from tools.model_resolver import resolve_openrouter_model
        except Exception as e:
            print(f"Error: could not load model resolver: {e}")
            return 1
        resolved = resolve_openrouter_model(raw)
        if "error" in resolved:
            print(f"Error: {resolved['error']}")
            if resolved.get("candidates"):
                print("Closest catalog matches: " + ", ".join(resolved["candidates"]))
            print(f"Known shortcuts: {', '.join(MODEL_MAPPINGS.keys())}")
            return 1
        provider, model, label = "OpenRouter", resolved["model"], resolved["model"]

    session_key = _session_key()
    if not session_key:
        print(
            "Error: no active session context (HERMES_SESSION_KEY not set) -- "
            "this only works from a live chat session, not a bare CLI/cron run."
        )
        return 1

    try:
        REQUEST_DIR.mkdir(parents=True, exist_ok=True)
        fname = hashlib.sha256(session_key.encode("utf-8")).hexdigest()[:24] + ".json"
        with open(REQUEST_DIR / fname, "w", encoding="utf-8") as f:
            json.dump({
                "model": model,
                "provider": provider,
                "keyword": label,
                "session_key": session_key,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }, f)
    except Exception as e:
        print(f"Error writing model switch request: {e}")
        return 1

    print(f"Model switch to {provider} ({model}) queued for this session.")
    print("Starting from your next message, all LLM calls will use the new model.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
