#!/usr/bin/env python3
"""
Switch the active LLM model for the current Hermes session.

Writes ~/.hermes/model_switch_request.json which is detected and applied
by the agent loop (_apply_model_switch_request in run_agent.py) after the
next tool call completes. From the following message onwards, all LLM calls
use the new model.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

MODEL_MAPPINGS = {
    "minimax":  {"provider": "MiniMax",    "model": "Minimax-M2.7"},
    "nematron": {"provider": "OpenRouter", "model": "nvidia/nemotron-3-super-120b-a12b:free"},
    "gemini2":  {"provider": "OpenRouter", "model": "google/gemini-2.5-flash-lite"},
    "gemini3":  {"provider": "OpenRouter", "model": "google/gemini-3-flash-preview"},
    "qwen":     {"provider": "OpenRouter", "model": "qwen/qwen3.6-plus:free"},
}


def _handle_switch_model(args: dict, **kwargs) -> str:
    model_keyword = (args.get("model") or "").strip().lower()

    if not model_keyword:
        return json.dumps({
            "success": False,
            "error": "model keyword is required.",
            "supported": list(MODEL_MAPPINGS.keys()),
        })

    cfg = MODEL_MAPPINGS.get(model_keyword)
    if not cfg:
        return json.dumps({
            "success": False,
            "error": f"Unknown model keyword '{model_keyword}'.",
            "supported": list(MODEL_MAPPINGS.keys()),
        })

    hermes_home = Path(os.getenv("HERMES_HOME", Path.home() / ".hermes"))
    hermes_home.mkdir(parents=True, exist_ok=True)
    request_file = hermes_home / "model_switch_request.json"

    payload = {
        "model":     cfg["model"],
        "provider":  cfg["provider"],
        "keyword":   model_keyword.capitalize(),
        "timestamp": datetime.utcnow().isoformat(),
    }

    try:
        with open(request_file, "w", encoding="utf-8") as f:
            json.dump(payload, f)
    except Exception as e:
        logger.error("Failed to write model switch request: %s", e)
        return json.dumps({"success": False, "error": str(e)})

    return json.dumps({
        "success":  True,
        "message":  f"Model switch queued: {cfg['provider']} / {cfg['model']}",
        "note":     "The new model takes effect from your next message onwards.",
        "provider": cfg["provider"],
        "model":    cfg["model"],
    })


_SCHEMA = {
    "name": "switch_model",
    "description": (
        "Switch the active LLM model for the current session. "
        "Use this whenever the user asks to change, switch, or try a different AI model "
        "(e.g. 'switch to Qwen', 'use Gemini2', 'use Gemini3', 'change model to MiniMax', 'try Nematron'). "
        "The new model takes effect from the next message onwards. "
        "Supported keywords: minimax, gemini2, gemini3, nematron, qwen."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "model": {
                "type": "string",
                "enum": ["minimax", "gemini2", "gemini3", "nematron", "qwen"],
                "description": (
                    "The model keyword to switch to. "
                    "minimax → Minimax-M2.7 (MiniMax), "
                    "gemini2 → gemini-2.5-flash-lite (OpenRouter), "
                    "gemini3 → gemini-3-flash-preview (OpenRouter), "
                    "nematron → nvidia/nemotron-3-super-120b (OpenRouter), "
                    "qwen → qwen3.6-plus (OpenRouter)."
                ),
            },
        },
        "required": ["model"],
    },
}


from tools.registry import registry  # noqa: E402

registry.register(
    name="switch_model",
    toolset="configuration",
    schema=_SCHEMA,
    handler=_handle_switch_model,
    check_fn=lambda: True,
    requires_env=[],
    is_async=False,
    description=_SCHEMA["description"],
    emoji="🔄",
)
