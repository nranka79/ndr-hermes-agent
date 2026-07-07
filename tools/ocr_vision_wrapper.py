#!/usr/bin/env python3
"""
OCR + Vision wrapper — plugin, NOT a modification of the vendored
tools/vision_tools.py.

tools/vision_tools.py is vendored from upstream (NousResearch/hermes-agent)
and kept pristine so ``git fetch upstream`` / merges stay clean. All
Hetzner-specific behavior (the OCR fast path) lives here instead, wired in
through the registry's sanctioned plugin-override mechanism —
see tools/registry.py::ToolRegistry.register, ``override=True``: "an
explicit opt-in for plugins that intend to replace an existing built-in
tool implementation."

This file REPLACES the "vision_analyze" tool's handler and schema at
import time. It does not edit, subclass, or monkeypatch vision_tools.py —
it only imports and calls its existing (untouched) public/internal
functions. A DIFFERENT toolset name ("vision-ocr" vs vision_tools.py's
"vision") is used deliberately: tools are discovered alphabetically
(tools/registry.py::discover_builtin_tools), and "ocr_vision_wrapper.py"
sorts before "vision_tools.py" — so this file's registration always runs
first. The registry only enforces override protection when toolset names
differ, so a distinct toolset name here guarantees this wrapper wins
regardless of import order: when vision_tools.py's own (non-override)
registration runs afterwards, it gets rejected as a shadow attempt —
logged as an ERROR-level "Tool registration REJECTED" message on every
startup. That's expected and harmless, not a real error — it's the
registry doing exactly its job.

Behavior when the model calls vision_analyze:
  1. Resolve image_url to a local file (download if remote, use directly
     if a local path) — reusing vision_tools.py's own vetted resolver
     functions (SSRF-guarded download via check_website_access +
     _download_image, URL validation via _validate_image_url_async)
     rather than reimplementing that logic here.
  2. Try tesseract OCR on that file. Free, instant, no LLM credits.
  3. If OCR finds enough readable text (>= 20 non-whitespace characters):
       - Default: return the OCR text directly, skip the vision LLM call
         entirely (fast, free).
       - If the model set ``also_describe_visually=true`` (because the
         user explicitly asked for both text AND a visual/design
         description): also run the normal vision analysis and return
         both, merged.
  4. Otherwise (OCR insufficient, tesseract unavailable, or the source
     couldn't be resolved locally): fall through to the original,
     untouched vision_analyze implementation in tools.vision_tools.
"""

import asyncio
import copy
import json
import logging
import os
import uuid
from pathlib import Path
from typing import Any, Awaitable, Dict, Optional

from hermes_constants import get_hermes_dir
from tools.registry import registry
from tools.vision_tools import (
    VISION_ANALYZE_SCHEMA,
    _download_image,
    _handle_vision_analyze,
    _validate_image_url_async,
    check_vision_requirements,
)
from tools.website_policy import check_website_access

logger = logging.getLogger(__name__)

# Extend (don't modify) the original schema with one optional flag. A
# deep copy of vision_tools.py's schema, not an edit to it.
_OCR_VISION_SCHEMA: Dict[str, Any] = copy.deepcopy(VISION_ANALYZE_SCHEMA)
_OCR_VISION_SCHEMA["description"] = (
    "Load an image into the conversation so you can see it, or read the "
    "text in it. Accepts a URL, local file path, or data URL. If the "
    "image contains readable text (screenshot, document, receipt, error "
    "message, etc.), that text is extracted instantly via free OCR and "
    "returned directly — no vision-model call, no cost. If the image has "
    "no readable text (a photo, diagram, or UI needing visual "
    "understanding), it falls back to full vision analysis automatically. "
    "Call this any time the user references an image (filepath in their "
    "message, URL in tool output, screenshot from the browser, etc.)."
)
_OCR_VISION_SCHEMA["parameters"]["properties"]["also_describe_visually"] = {
    "type": "boolean",
    "description": (
        "Set true ONLY if the user explicitly asked for both the text "
        "content AND a visual/design description (colors, layout, "
        "objects, overall appearance) of the image. Default false: if "
        "the image has readable text, that text alone is returned."
    ),
}


async def _resolve_to_local_file(image_url: str) -> Optional[Path]:
    """Get a local file path for image_url for OCR purposes only.

    Reuses vision_tools.py's own vetted download/validation helpers
    (SSRF guard included) rather than reimplementing them here. Returns
    None if the source can't be resolved locally — the caller then falls
    through to the original vision tool, which will produce its own clear
    error if the source is genuinely invalid.
    """
    try:
        resolved_url = image_url
        if resolved_url.startswith("file://"):
            resolved_url = resolved_url[len("file://"):]
        local_path = Path(os.path.expanduser(resolved_url))
        if local_path.is_file():
            return local_path
        if await _validate_image_url_async(image_url):
            blocked = check_website_access(image_url)
            if blocked:
                return None
            temp_dir = get_hermes_dir("cache/vision", "temp_ocr_images")
            temp_path = temp_dir / f"ocr_temp_{uuid.uuid4()}.jpg"
            await _download_image(image_url, temp_path)
            return temp_path
    except Exception as exc:
        logger.debug("OCR wrapper: could not resolve image source locally: %s", exc)
    return None


async def _try_ocr_text(image_path: Path, timeout: float = 30.0) -> Optional[str]:
    """Run tesseract OCR on an image and return extracted text if meaningful.

    Returns the text string when at least 20 non-whitespace characters are
    found, None otherwise (image is a photo/diagram with no readable text,
    tesseract is not installed, or the process fails).
    """
    try:
        proc = await asyncio.create_subprocess_exec(
            "tesseract", str(image_path), "stdout", "--psm", "3",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            logger.warning("OCR wrapper: OCR timed out after %.0fs", timeout)
            return None

        if proc.returncode != 0:
            return None

        text = stdout.decode("utf-8", errors="replace").strip()
        non_ws = "".join(text.split())
        if len(non_ws) < 20:
            logger.debug("OCR wrapper: insufficient text (%d non-ws chars), will use vision", len(non_ws))
            return None

        logger.info("OCR wrapper: extracted %d characters", len(text))
        return text

    except FileNotFoundError:
        logger.debug("OCR wrapper: tesseract not found")
        return None
    except Exception as exc:
        logger.debug("OCR wrapper: OCR error: %s", exc)
        return None


async def _vision_analyze_ocr_first(args: Dict[str, Any], **kw: Any) -> str:
    image_url = args.get("image_url", "")
    want_both = bool(args.get("also_describe_visually", False))

    ocr_text = None
    local_path = await _resolve_to_local_file(image_url)
    if local_path is not None:
        ocr_text = await _try_ocr_text(local_path)

    if ocr_text and not want_both:
        logger.info("vision_analyze (OCR wrapper): OCR text sufficient, skipping vision LLM call")
        result = {
            "success": True,
            "analysis": f"[Text extracted via OCR]\n\n{ocr_text}",
            "method": "ocr",
        }
        return json.dumps(result, indent=2, ensure_ascii=False)

    # OCR insufficient/unavailable, or the model explicitly asked for both
    # text AND visual description -- fall through to the untouched
    # upstream implementation for the vision portion.
    vision_result_str = await _handle_vision_analyze(args, **kw)

    if ocr_text and want_both:
        try:
            vision_result = json.loads(vision_result_str)
        except Exception:
            vision_result = None
        if isinstance(vision_result, dict) and vision_result.get("success"):
            vision_result["analysis"] = (
                f"[Text extracted via OCR]\n\n{ocr_text}\n\n"
                f"[Visual analysis]\n\n{vision_result.get('analysis', '')}"
            )
            vision_result["method"] = "ocr+vision"
            logger.info("vision_analyze (OCR wrapper): merged OCR text + vision analysis")
            return json.dumps(vision_result, indent=2, ensure_ascii=False)

    return vision_result_str


def _handle_vision_analyze_with_ocr(args: Dict[str, Any], **kw: Any) -> Awaitable[str]:
    return _vision_analyze_ocr_first(args, **kw)


registry.register(
    name="vision_analyze",
    toolset="vision-ocr",
    schema=_OCR_VISION_SCHEMA,
    handler=_handle_vision_analyze_with_ocr,
    check_fn=check_vision_requirements,
    is_async=True,
    emoji="👁️",
    override=True,
)
