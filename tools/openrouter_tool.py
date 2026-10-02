"""
openrouter_tool — Route a single sub-task to an explicitly-chosen model via OpenRouter.

ONLY invoked when the user explicitly says "via openrouter". Model selection is
resolved dynamically against OpenRouter's live catalog (tools/model_resolver.py)
from whatever vendor/tier/capability/version words the user actually used —
"deep thinking", "the latest Opus", "cheapest Gemini flash", "claude opus 4.6",
etc. — instead of requiring one of a small fixed list of brand names (pre
2026-10-02 behavior: hard-refused anything outside gemini/gpt/claude/deepseek/
qwen/kimi/llama/mistral/grok, which is what produced "no provision to select
a model" for asks like "a deep thinking model").

Returns the model's full response to the Hermes agent. The agent decides what
to do next with that text (reply, save to Drive, chain into another tool, etc.).
"""
import json
import logging
import os
import re
import urllib.request
import urllib.error
from typing import Any, Dict

from tools.model_resolver import resolve_openrouter_model

logger = logging.getLogger(__name__)

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

_OPENROUTER_RE = re.compile(r"open\s*router", re.IGNORECASE)
# Was a 17-word generic list (look at|see|view|read|scan|analyze|describe|
# interpret|extract text/content|transcribe|ocr|vision|image|photo|picture|
# screenshot|pdf|page) matched ANYWHERE in the prompt -- fired on ordinary
# business prose for pure text-generation asks ("describe the emotional
# hooks", "this brand image", "landing page", "a complete analysis") because
# those are just common English words, not evidence of an actual image/PDF
# attachment. Confirmed 2026-10-02: a design-brief request got blocked on
# every retry, including prompts with all "visual" vocabulary deliberately
# stripped out, because the guard was never looking for visual vocabulary --
# it was tripping on ordinary verbs like "describe". Narrowed to require
# either an unambiguous visual-input term (ocr/transcribe/screenshot) or a
# determiner immediately before a visual-object noun ("this image", "the
# attached pdf"), not a bare word anywhere in a long prompt.
_VISION_HINT_RE = re.compile(
    r"\bocr\b|\btranscrib\w*|\bscreenshot"
    r"|\blook at (?:the|this|that|these|those|your|my|attached|uploaded)"
    r"|\b(?:the|this|that|these|those|your|my|attached|uploaded)\s+(?:image|photo|picture|scan|pdf)s?\b",
    re.IGNORECASE,
)


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

    resolution_note = ""
    if model_arg and "/" in model_arg:
        model = model_arg.strip()
    else:
        try:
            resolved = resolve_openrouter_model(model_arg or trigger)
        except Exception as e:
            return json.dumps({"error": f"Model resolution failed: {e}"})
        if "error" in resolved:
            return json.dumps({
                "error": resolved["error"],
                "candidates": resolved.get("candidates", []),
                "hint": (
                    "Pass an explicit vendor/model slug in 'model' (e.g. 'anthropic/claude-opus-4.8'), "
                    "or rephrase naming a vendor/tier/capability — e.g. 'deep thinking', 'gemini flash', "
                    "'cheapest', 'claude opus 4.6'."
                ),
            })
        model = resolved["model"]
        resolution_note = resolved.get("note", "")

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

    result = {
        "success": True,
        "model": model,
        "response": content,
        "usage": resp.get("usage"),
    }
    if resolution_note:
        result["resolved_as"] = resolution_note
    return json.dumps(result, ensure_ascii=False)


_TOOL_SCHEMA = {
    "name": "call_openrouter_model",
    "description": (
        "Route ONE sub-task to a specific model via OpenRouter and return that model's full response. "
        "Use ONLY when the user EXPLICITLY says 'via openrouter' or 'use openrouter'. "
        "Model selection is dynamic — it resolves vendor, tier, explicit version, 'deep thinking'/reasoning "
        "capability, and 'latest'/'cheapest' against OpenRouter's live model catalog, so phrases like "
        "'a deep thinking model', 'the latest Opus', 'cheapest Gemini flash model', or 'claude opus 4.6' "
        "all resolve to a real model — it is NOT limited to a fixed brand-name list. "
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
        "  user_trigger_phrase — verbatim quote of the user's request showing 'openrouter'. Server rejects if missing.\n"
        "  prompt — full instruction to send to the chosen model (text only).\n"
        "  model — (optional) full slug like 'google/gemini-2.5-pro'. If omitted, the model is resolved from "
        "user_trigger_phrase's wording (vendor/tier/capability/version/latest/cheapest). On an ambiguous or "
        "unrecognized ask, the tool returns an error with candidate model ids instead of guessing silently — "
        "retry with a vendor/tier named, or pass an explicit slug in 'model'.\n"
        "  max_tokens — (optional) default 8000. Reasoning models need >=4000."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "user_trigger_phrase": {"type": "string", "description": "Verbatim user quote containing 'openrouter'."},
            "prompt": {"type": "string", "description": "Full prompt for the chosen model."},
            "model": {"type": "string", "description": "OpenRouter slug, or free-text vendor/tier/capability words. Optional."},
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
