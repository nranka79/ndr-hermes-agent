"""
Browser Use Cloud Tool — executes web browser tasks via Browser Use Cloud REST API.

Creates a managed remote browser session, runs an AI agent against it,
and returns results + live view URL for human takeover.

Registered as: browser_use_cloud
Toolset:       browser

Args:
  task             (str, required)  Natural language description of the browser task
  max_steps        (int, optional)  Max agent steps before stopping; default 50
  return_live_url  (bool, optional) Skip agent, return live URL immediately; default False
  pause_on_failure (bool, optional) Return live URL on failure instead of erroring; default True
  llm              (str, optional)  Model to use; default "browser-use-2.0"

Returns JSON:
  {
    "status":   "completed" | "paused_for_human" | "failed",
    "result":   str | null,
    "live_url": str | null,
    "error":    str | null
  }
"""

import json
import logging
import os
import time
import urllib.error
import urllib.request

from tools.registry import registry

logger = logging.getLogger(__name__)

_API_BASE = "https://api.browser-use.com/api/v2"
_POLL_INTERVAL = 4       # seconds between task status polls
_LIVE_URL_WAIT = 12      # seconds to wait for live URL to appear after task creation
_DEFAULT_LLM = "browser-use-2.0"

# Task statuses that mean "still running"
_RUNNING_STATUSES = {"created", "started", "paused"}


def _api_key():
    return os.environ.get("BROWSER_USE_API_KEY")


def _req(method, path, body=None):
    key = _api_key()
    if not key:
        raise RuntimeError("BROWSER_USE_API_KEY not set")
    url = f"{_API_BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "X-Browser-Use-API-Key": key,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _wait_for_live_url(session_id, timeout=12):
    """Poll session until liveUrl appears or timeout. Returns URL or None."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(3)
        try:
            sess = _req("GET", f"/sessions/{session_id}")
            url = sess.get("liveUrl")
            if url:
                return url
        except Exception:
            pass
    return None


def _handle_browser_use_cloud(args, **_):
    task             = args["task"]
    max_steps        = int(args.get("max_steps", 50))
    return_live_url  = bool(args.get("return_live_url", False))
    pause_on_failure = bool(args.get("pause_on_failure", True))
    llm              = args.get("llm", _DEFAULT_LLM)

    if not _api_key():
        return json.dumps({
            "status": "failed",
            "result": None,
            "live_url": None,
            "error": "BROWSER_USE_API_KEY not set — add it to /opt/hermes/.env",
        })

    try:
        # 1. Create task (auto-creates session)
        created = _req("POST", "/tasks", {
            "task": task,
            "maxSteps": max_steps,
            "llm": llm,
        })
        task_id    = created["id"]
        session_id = created["sessionId"]
        logger.info("browser_use_cloud: task=%s session=%s", task_id, session_id)

        # 2. Wait for live URL (appears ~5s after browser starts)
        live_url = _wait_for_live_url(session_id, timeout=_LIVE_URL_WAIT)
        logger.info("browser_use_cloud: live_url=%s", live_url)

        # 3. If caller just wants the URL, return immediately
        if return_live_url:
            return json.dumps({
                "status": "paused_for_human",
                "result": "Session created. Open live_url to take control.",
                "live_url": live_url,
                "error": None,
            })

        # 4. Poll until finished / stopped — capture live_url whenever available
        deadline = time.time() + max(max_steps * 10, 120)
        while time.time() < deadline:
            time.sleep(_POLL_INTERVAL)
            task_info = _req("GET", f"/tasks/{task_id}")
            status    = task_info.get("status", "")
            logger.debug("browser_use_cloud: poll status=%s", status)

            # Refresh live URL if it disappears (session still active)
            if not live_url:
                try:
                    sess = _req("GET", f"/sessions/{session_id}")
                    live_url = sess.get("liveUrl") or live_url
                except Exception:
                    pass

            if status == "finished":
                output = task_info.get("output") or ""
                return json.dumps({
                    "status": "completed",
                    "result": output,
                    "live_url": live_url,
                    "error": None,
                })

            if status == "stopped":
                output = task_info.get("output") or ""
                if pause_on_failure:
                    return json.dumps({
                        "status": "paused_for_human",
                        "result": f"Agent stopped before completing. Partial output: {output}",
                        "live_url": live_url,
                        "error": "Task stopped by agent or system",
                    })
                return json.dumps({
                    "status": "failed",
                    "result": output or None,
                    "live_url": live_url,
                    "error": "Task stopped before completion",
                })

            # created / started / paused — keep polling

        # Timeout — return live URL for human takeover
        if pause_on_failure:
            return json.dumps({
                "status": "paused_for_human",
                "result": f"Task timed out after {max_steps} steps. Open live_url to take over.",
                "live_url": live_url,
                "error": "Polling timeout",
            })
        return json.dumps({
            "status": "failed",
            "result": None,
            "live_url": live_url,
            "error": "Polling timeout",
        })

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace") if exc.fp else ""
        error = f"HTTP {exc.code}: {body}"
        logger.error("browser_use_cloud: %s", error)
        return json.dumps({"status": "failed", "result": None, "live_url": None, "error": error})
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        logger.error("browser_use_cloud: %s", error)
        return json.dumps({"status": "failed", "result": None, "live_url": None, "error": error})


def _check_available():
    return bool(_api_key())


_BROWSER_USE_CLOUD_SCHEMA = {
    "name": "browser_use_cloud",
    "description": (
        "Control a real web browser via Browser Use Cloud (remote managed service). "
        "Use for: filling forms, logging into sites, multi-step web flows, scraping "
        "JS-heavy pages, clicking through navigation, extracting live page data. "
        "Always returns live_url so user can watch or take over. "
        "Set pause_on_failure=True (default) to hand off to human on failure rather than error silently. "
        "Set return_live_url=True to skip agent and get session link immediately."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "task": {
                "type": "string",
                "description": "Full natural-language description of the browser task to complete.",
            },
            "max_steps": {
                "type": "integer",
                "description": "Max agent steps before pausing for human. Default 50.",
                "default": 50,
            },
            "return_live_url": {
                "type": "boolean",
                "description": "Skip agent execution and return live session URL immediately.",
                "default": False,
            },
            "pause_on_failure": {
                "type": "boolean",
                "description": "Return live URL on failure instead of erroring out.",
                "default": True,
            },
            "llm": {
                "type": "string",
                "description": "LLM model for the agent. Default: browser-use-2.0.",
                "default": "browser-use-2.0",
            },
        },
        "required": ["task"],
    },
}


# NOTE: registration must be a BARE top-level call — the auto-discovery AST
# scan (tools/registry.py::_module_registers_tools) only picks up modules with
# a top-level ``registry.register(...)`` expression statement. Wrapping it in
# a function or try-block silently disables the tool (regression fixed
# 2026-08-02).
registry.register(
    name="browser_use_cloud",
    toolset="browser",
    schema=_BROWSER_USE_CLOUD_SCHEMA,
    handler=_handle_browser_use_cloud,
    check_fn=_check_available,
    is_async=False,
    description=_BROWSER_USE_CLOUD_SCHEMA["description"],
    emoji="🌐",
)
logger.info("browser_use_cloud tool registered")
