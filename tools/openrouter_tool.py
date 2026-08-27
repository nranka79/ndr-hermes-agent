"""
openrouter_tool — Route a single sub-task to an explicitly-chosen model via OpenRouter.

ONLY invoked when the user explicitly says "via openrouter" AND names a model family.
Returns the model's full response to the Hermes agent. The agent decides what to do
next with that text (reply, save to Drive, chain into another tool, etc.).
"""
import json
import logging
import os
import re
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_MODELS_URL = "https://openrouter.ai/api/v1/models"

_OPENROUTER_RE = re.compile(r"open\s*router", re.IGNORECASE)
_MODEL_FAMILY_RE = re.compile(
    r"\b(gemini|gpt|claude|deepseek|qwen|kimi|llama|mistral|grok)\b",
    re.IGNORECASE,
)
_VISION_HINT_RE = re.compile(
    r"\b(look at|see|view|read|scan|analy[sz]e|describe|interpret|extract (?:text|content)"
    r"|transcrib|ocr|vision|image|photo|picture|screenshot|pdf|page)\b",
    re.IGNORECASE,
)

_FAMILY_PREFERENCES = {
    "gemini":   ["google/gemini-3", "google/gemini-2.5-pro"],
    "deepseek": ["deepseek/deepseek-chat-v3.1", "deepseek/deepseek-chat"],
    "claude":   ["anthropic/claude-opus-4", "anthropic/claude-sonnet-4"],
    "gpt":      ["openai/gpt-5", "openai/gpt-4.1"],
    "qwen":     ["qwen/qwen-3"],
    "kimi":     ["moonshotai/kimi-k2"],
    "llama":    ["meta-llama/llama-3.3"],
    "mistral":  ["mistralai/mistral-large"],
    "grok":     ["x-ai/grok-3"],
}


def _fetch_openrouter_models() -> list:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    req = urllib.request.Request(
        OPENROUTER_MODELS_URL,
        headers={"Authorization": f"Bearer {key}"},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read())
    return [m["id"] for m in data.get("data", []) if isinstance(m, dict) and "id" in m]


def _resolve_model(model_arg: Optional[str], trigger_phrase: str) -> str:
    if model_arg and "/" in model_arg:
        return model_arg.strip()

    family = None
    if model_arg:
        m = _MODEL_FAMILY_RE.search(model_arg)
        if m:
            family = m.group(1).lower()
    if not family:
        m = _MODEL_FAMILY_RE.search(trigger_phrase)
        if m:
            family = m.group(1).lower()
    if not family:
        family = "gemini"

    available = []
    try:
        available = _fetch_openrouter_models()
    except Exception as e:
        logger.warning("OpenRouter model list fetch failed: %s", e)

    for pref_prefix in _FAMILY_PREFERENCES.get(family, []):
        matches = sorted(
            [m for m in available if m.startswith(pref_prefix)],
            reverse=True,
        )
        if matches:
            return matches[0]

    fallbacks = {
        "gemini":   "google/gemini-2.5-pro",
        "deepseek": "deepseek/deepseek-chat",
        "claude":   "anthropic/claude-sonnet-4",
        "gpt":      "openai/gpt-4.1",
        "qwen":     "qwen/qwen-2.5-72b-instruct",
        "kimi":     "moonshotai/kimi-k2",
        "llama":    "meta-llama/llama-3.3-70b-instruct",
        "mistral":  "mistralai/mistral-large",
        "grok":     "x-ai/grok-3",
    }
    return fallbacks.get(family, "google/gemini-2.5-pro")


def _call_openrouter(model: str, prompt: str, max_tokens: int) -> Dict[str, Any]:
    key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not set in environment")
    body = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
    }).encode()
    req = urllib.request.Request(
        OPENROUTER_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://transcribe.ahfl.in",
            "X-Title": "Hermes Telegram Agent",
        },
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        return json.loads(resp.read())


def _handle(args: dict, **kwargs) -> str:
    trigger = (args.get("user_trigger_phrase") or "").strip()
    prompt = (args.get("prompt") or "").strip()
    model_arg = (args.get("model") or "").strip() or None
    max_tokens = int(args.get("max_tokens") or 8000)

    if not trigger:
        return json.dumps({"error": "Missing required arg: user_trigger_phrase (verbatim quote from user)"})
    if not prompt:
        return json.dumps({"error": "Missing required arg: prompt"})

    if not _OPENROUTER_RE.search(trigger):
        return json.dumps({"error": "Refused: user_trigger_phrase must contain 'openrouter'. This tool may only be used when the user explicitly invokes OpenRouter."})
    if not _MODEL_FAMILY_RE.search(trigger):
        return json.dumps({"error": "Refused: user_trigger_phrase must name a model family (gemini|gpt|claude|deepseek|qwen|kimi|llama|mistral|grok)."})

    if _VISION_HINT_RE.search(prompt or "") or _VISION_HINT_RE.search(trigger or ""):
        return json.dumps({
            "error": (
                "This tool is TEXT-ONLY and cannot accept image/PDF/vision input. "
                "The request appears to involve looking at or reading an image/document. "
                "Use the vision_analyze tool instead (it routes through the proper multimodal "
                "vision router and handles images correctly), or extract text from the PDF via "
                "pdf_tool and pass the extracted text here."
            ),
        })

    try:
        model = _resolve_model(model_arg, trigger)
    except Exception as e:
        return json.dumps({"error": f"Model resolution failed: {e}"})

    try:
        resp = _call_openrouter(model, prompt, max_tokens)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        return json.dumps({"error": f"OpenRouter HTTP {e.code}", "detail": body, "model": model})
    except Exception as e:
        return json.dumps({"error": str(e), "model": model})

    try:
        content = resp["choices"][0]["message"]["content"] or ""
    except (KeyError, IndexError):
        return json.dumps({"error": "Malformed OpenRouter response", "raw": str(resp)[:500]})

    if not content.strip():
        return json.dumps({
            "error": "OpenRouter returned empty content (possibly all tokens consumed by reasoning). Retry with higher max_tokens.",
            "model": model,
            "usage": resp.get("usage"),
        })

    return json.dumps({
        "success": True,
        "model": model,
        "response": content,
        "usage": resp.get("usage"),
    }, ensure_ascii=False)


_TOOL_SCHEMA = {
    "name": "call_openrouter_model",
    "description": (
        "Route ONE sub-task to a specific model via OpenRouter and return that model's full response. "
        "Use ONLY when the user EXPLICITLY says 'via openrouter' or 'use openrouter' AND names a model family "
        "(gemini, gpt, claude, deepseek, qwen, kimi, llama, mistral, grok). "
        "DO NOT use this tool for general analysis, summarisation, or any task where the user did not explicitly request OpenRouter. "
        "Default behaviour is to use the main model (MiniMax) — this tool exists only for explicit user routing requests. "
        "This tool ONLY calls the model and returns its text. It does NOT save files. "
        "If the user wants the result written to a Doc, sheet, or message, YOU do that afterwards with the appropriate tool using the returned 'response' text.\n\n"
        "TEXT-ONLY TOOL — NO IMAGES, PDFS, OR VISION: this tool sends plain text only and CANNOT accept image "
        "input, PDF pages, screenshots, or any other visual content. If the user's task involves seeing or "
        "interpreting an image, PDF, scan, or photo — INCLUDING when they explicitly ask for a vision-capable "
        "model like Gemini 'via openrouter' — do NOT call this tool. Instead use the vision_analyze tool "
        "(or the pdf_tool for documents), which routes images through the proper multimodal vision router "
        "(OpenRouter/Nous/Codex/Anthropic) and handles base64/URL image parts correctly. "
        "Calling this tool with a request to 'look at' an image will fail with an empty or text-only response.\n\n"
        "Args:\n"
        "  user_trigger_phrase — verbatim quote of the user's request showing 'openrouter' + model name. Server rejects if missing either.\n"
        "  prompt — full instruction to send to the chosen model (text only).\n"
        "  model — (optional) full slug like 'google/gemini-2.5-pro', or just family ('gemini'). If omitted, server picks newest from family in trigger phrase.\n"
        "  max_tokens — (optional) default 8000. Reasoning models need >=4000."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_trigger_phrase": {"type": "string", "description": "Verbatim user quote containing 'openrouter' + model family name."},
            "prompt": {"type": "string", "description": "Full prompt for the chosen model."},
            "model": {"type": "string", "description": "OpenRouter slug or family name. Optional."},
            "max_tokens": {"type": "integer", "description": "Max output tokens (default 8000)."},
        },
        "required": ["user_trigger_phrase", "prompt"],
    },
}


def _check_available() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY", "").strip())


from tools.registry import registry

registry.register(
    name="call_openrouter_model",
    schema=_TOOL_SCHEMA,
    handler=_handle,
    toolset="external_model",
    check_fn=_check_available,
    description="Route a single sub-task to a user-specified model via OpenRouter. Returns the model's full response.",
)
