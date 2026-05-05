#!/usr/bin/env python3
"""
smart_browser_server.py — HTTP sidecar for smart_browser tool.

Runs inside its own Docker container (browser-use + playwright + Chromium).
The hermes container calls POST /run with a JSON body.
Listens on 0.0.0.0:9181.
"""

import asyncio
import json
import logging
import os
import re
import uuid
from dataclasses import dataclass

import uvicorn
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────────

_MINIMAX_BASE_URL = "https://api.minimax.io/v1"
_MINIMAX_MODEL    = "MiniMax-M2.7"

_STEALTH_ARGS = [
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-gpu",
    "--window-size=1920,1080",
    (
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
]

_THINK_RE      = re.compile(r"<think>.*?</think>", re.DOTALL)
_CODE_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?", re.MULTILINE)
_MAX_RETRIES   = 3


# ── Think-tag stripping ───────────────────────────────────────────────────────

def _clean_response(text: str) -> str:
    text = _THINK_RE.sub("", text)
    text = _CODE_FENCE_RE.sub("", text)
    text = text.replace("```", "")
    return text.strip()


# ── LLM builder ──────────────────────────────────────────────────────────────

def _build_llm(base_url: str, api_key: str, model: str):
    from browser_use.llm.openai.chat import ChatOpenAI

    @dataclass
    class _ChatThinkStrip(ChatOpenAI):
        """ChatOpenAI subclass that strips MiniMax <think> blocks before parsing."""

        async def ainvoke(self, messages, output_format=None, **kwargs):
            if output_format is None:
                result = await super().ainvoke(messages, output_format=None, **kwargs)
                if isinstance(result.completion, str):
                    return result.model_copy(
                        update={"completion": _clean_response(result.completion)}
                    )
                return result
            # Structured path: get raw, strip, parse manually
            raw = await super().ainvoke(messages, output_format=None, **kwargs)
            cleaned = _clean_response(raw.completion)
            parsed = output_format.model_validate_json(cleaned)
            return raw.model_copy(update={"completion": parsed})

    return _ChatThinkStrip(
        model=model,
        base_url=base_url,
        api_key=api_key,
        dont_force_structured_output=True,
        add_schema_to_system_prompt=True,
        max_completion_tokens=4096,
    )


# ── Core browser run ─────────────────────────────────────────────────────────

async def _run_once(
    instruction: str,
    timeout_seconds: int,
    max_steps: int,
    base_url: str,
    api_key: str,
    model: str,
) -> dict:
    from browser_use import Agent
    from browser_use.browser import BrowserProfile, BrowserSession

    profile = BrowserProfile(
        headless=True,
        args=_STEALTH_ARGS,
        # No executable_path — let playwright auto-detect the installed Chromium
    )
    session = BrowserSession(browser_profile=profile)
    llm = _build_llm(base_url, api_key, model)

    agent = Agent(
        task=instruction,
        llm=llm,
        browser_session=session,
        max_actions_per_step=5,
    )

    try:
        history = await asyncio.wait_for(
            agent.run(max_steps=max_steps),
            timeout=timeout_seconds,
        )
        final = history.final_result()
        return {
            "success": bool(final),
            "result": final,
            "steps_taken": len(history.history),
        }
    except asyncio.TimeoutError:
        raise
    finally:
        try:
            await session.kill()
        except Exception:
            pass


# ── Request handler ───────────────────────────────────────────────────────────

async def run_handler(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)

    instruction = body.get("instruction")
    if not instruction:
        return JSONResponse({"error": "instruction required"}, status_code=400)

    session_id      = body.get("session_id") or uuid.uuid4().hex[:12]
    timeout_seconds = int(body.get("timeout_seconds", 120))
    max_steps       = int(body.get("max_steps", 20))

    # LLM config: prefer caller-provided, fall back to MINIMAX env
    base_url = body.get("llm_base_url") or _MINIMAX_BASE_URL
    api_key  = body.get("llm_api_key")  or os.environ.get("MINIMAX_API_KEY", "")
    model    = body.get("llm_model")    or _MINIMAX_MODEL

    if not api_key:
        return JSONResponse(
            {"error": "no API key: set MINIMAX_API_KEY or pass llm_api_key in request"},
            status_code=500,
        )

    logger.info("session=%s instruction=%r", session_id, instruction[:120])

    last_error = None
    for attempt in range(1, _MAX_RETRIES + 1):
        try:
            logger.info("attempt %d/%d", attempt, _MAX_RETRIES)
            outcome = await _run_once(
                instruction, timeout_seconds, max_steps, base_url, api_key, model
            )
            outcome["attempts"] = attempt
            outcome["error"]    = None
            logger.info("done attempt=%d success=%s", attempt, outcome["success"])
            return JSONResponse(outcome)

        except asyncio.TimeoutError:
            last_error = f"Timeout after {timeout_seconds}s (attempt {attempt})"
            logger.warning("timeout attempt=%d", attempt)

        except Exception as exc:
            last_error = f"{type(exc).__name__}: {exc}"
            logger.warning("error attempt=%d: %s", attempt, last_error)

    return JSONResponse({
        "success":    False,
        "result":     None,
        "steps_taken": 0,
        "attempts":   _MAX_RETRIES,
        "error":      last_error,
    })


async def health_handler(request: Request) -> JSONResponse:
    return JSONResponse({"status": "ok"})


# ── App ───────────────────────────────────────────────────────────────────────

app = Starlette(routes=[
    Route("/run",    run_handler,    methods=["POST"]),
    Route("/health", health_handler, methods=["GET"]),
])

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9181, log_level="info")
