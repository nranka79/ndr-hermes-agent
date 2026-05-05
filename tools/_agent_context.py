#!/usr/bin/env python3
"""
Agent LLM context — lightweight singleton that stores the current session's
LLM config (base_url, api_key, model) so tools like smart_browser can
use the same provider/model the Hermes agent is using.

AIAgent calls set_llm_config() once after it resolves its client.
Tools call get_llm_config() to read it.
"""

import threading

_lock = threading.Lock()
_config: dict = {
    "base_url": None,
    "api_key":  None,
    "model":    None,
}


def set_llm_config(base_url: str, api_key: str, model: str) -> None:
    with _lock:
        _config["base_url"] = base_url
        _config["api_key"]  = api_key
        _config["model"]    = model


def get_llm_config() -> dict:
    with _lock:
        return dict(_config)
