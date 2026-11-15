#!/usr/bin/env python3
"""
Smart Browser Tool — calls the smart-browser sidecar over HTTP.

The heavy lifting (browser-use, playwright, Chromium) runs in a separate
Docker container (smart-browser service). This tool is a thin HTTP client
that forwards the request and passes the active session's LLM config so
the sidecar uses the same provider/model as the Hermes agent.

Registered as: smart_browser
Toolset: browser

Args:
  instruction      (str, required)  Natural-language task
  session_id       (str, optional)  ID for log isolation; auto-generated if absent
  timeout_seconds  (int, optional)  Per-attempt timeout; default 120
  max_steps        (int, optional)  Max agent steps per attempt; default 20

Returns JSON:
  {
    "success": bool,
    "result":  str | null,
    "steps_taken": int,
    "attempts": int,
    "error": str | null
  }
"""

import json
import logging
import os
import uuid

from tools.registry import registry

logger = logging.getLogger(__name__)

_SIDECAR_URL = os.environ.get("SMART_BROWSER_URL", "http://smart-browser:9181/run")


def _handle_smart_browser(args: dict, **_) -> str:
    import urllib.request
    import urllib.error

    continuation_id = str(args.get("continuation_id") or "").strip()
    twofa_code      = str(args.get("twofa_code") or "").strip()

    # 2FA continuation: the sidecar kept the browser session alive at the
    # verification page. The code is entered by the sidecar, not the LLM.
    if continuation_id:
        if not twofa_code:
            return json.dumps({
                "success": False, "needs_2fa": True,
                "error": "twofa_code is required to resume",
            })
        resume_url = _SIDECAR_URL.rsplit("/run", 1)[0] + "/resume"
        payload = {"continuation_id": continuation_id, "twofa_code": twofa_code}
        if args.get("instruction"):
            payload["instruction"] = args["instruction"]
        try:
            req = urllib.request.Request(
                resume_url,
                data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=420) as resp:
                return resp.read().decode()
        except urllib.error.HTTPError as exc:
            try:
                detail = exc.read().decode()
            except Exception:
                detail = ""
            return json.dumps({
                "success": False,
                "error": f"2FA resume failed ({exc.code}): {detail[:1000]}",
            })
        except Exception as exc:
            return json.dumps({
                "success": False,
                "error": f"{type(exc).__name__}: {exc}",
            })

    instruction     = args["instruction"]
    session_id      = args.get("session_id") or uuid.uuid4().hex[:12]
    timeout_seconds = int(args.get("timeout_seconds", 120))
    max_steps       = int(args.get("max_steps", 20))

    payload: dict = {
        "instruction":     instruction,
        "session_id":      session_id,
        "timeout_seconds": timeout_seconds,
        "max_steps":       max_steps,
    }
    if args.get("twofa_method"):
        payload["twofa_method"] = args["twofa_method"]

    # Forward the active session's LLM config so the sidecar uses the same model
    try:
        from tools._agent_context import get_llm_config
        ctx = get_llm_config()
        if ctx["base_url"] and ctx["api_key"] and ctx["model"]:
            payload["llm_base_url"] = ctx["base_url"]
            payload["llm_api_key"]  = ctx["api_key"]
            payload["llm_model"]    = ctx["model"]
            logger.debug(
                "smart_browser: forwarding session LLM %s @ %s",
                ctx["model"], ctx["base_url"],
            )
    except Exception:
        pass

    # Forward the session identity so the sidecar can send X-Hermes-* headers
    # to the LLM gateway. Cron jobs use their owner as the attribution key.
    try:
        from gateway.session_context import get_session_env
        user_id = (
            get_session_env("HERMES_SESSION_USER_ID", "").strip()
            or get_session_env("HERMES_CRON_JOB_OWNER_ID", "").strip()
        )
        user_label = (
            get_session_env("HERMES_SESSION_USER_NAME", "").strip()
            or user_id
        )
        platform = get_session_env("HERMES_SESSION_PLATFORM", "").strip() or "browser"
        if user_id:
            payload["user_id"] = user_id
            payload["user_label"] = user_label
        payload["platform"] = platform
    except Exception:
        pass

    # Optional saved credential. The sidecar fetches the encrypted password
    # from the vault and feeds it to browser-use's sensitive_data map; this
    # tool never receives or forwards the plaintext.
    if args.get("use_saved_credential"):
        cred_user = str(
            args.get("credential_user") or payload.get("user_id") or ""
        ).strip()
        cred_domain = str(args.get("credential_domain") or "").strip()
        cred_origin = str(args.get("credential_origin") or "").strip()
        if not cred_user or not (cred_domain or cred_origin):
            return json.dumps({
                "success": False, "result": None, "steps_taken": 0, "attempts": 0,
                "error": "use_saved_credential requires credential_domain "
                         "(and a session user)",
            })
        cred: dict = {"user_id": cred_user}
        if cred_domain:
            cred["domain"] = cred_domain
        if cred_origin:
            cred["origin"] = cred_origin
        payload["credential"] = cred

    logger.info(
        "smart_browser → sidecar session=%s instruction=%r",
        session_id, instruction[:120],
    )

    try:
        body = json.dumps(payload).encode()
        req = urllib.request.Request(
            _SIDECAR_URL,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        # Total timeout = per-attempt timeout × retries + buffer
        http_timeout = timeout_seconds * 3 + 60
        with urllib.request.urlopen(req, timeout=http_timeout) as resp:
            result = json.loads(resp.read().decode())
        return json.dumps(result, ensure_ascii=False)

    except urllib.error.URLError as exc:
        error = f"Sidecar unreachable ({_SIDECAR_URL}): {exc.reason}"
        logger.error("smart_browser: %s", error)
        return json.dumps({
            "success": False, "result": None,
            "steps_taken": 0, "attempts": 0, "error": error,
        })
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        logger.error("smart_browser sidecar call failed: %s", error)
        return json.dumps({
            "success": False, "result": None,
            "steps_taken": 0, "attempts": 0, "error": error,
        })


def _check_available() -> bool:
    # Ping the sidecar health endpoint; fail gracefully if not up yet
    import urllib.request
    health_url = _SIDECAR_URL.replace("/run", "/health")
    try:
        urllib.request.urlopen(health_url, timeout=2)
        return True
    except Exception:
        return False


_SMART_BROWSER_SCHEMA = {
    "name": "smart_browser",
    "description": (
        "AI-driven browser agent. Accepts a natural-language instruction, "
        "autonomously navigates websites, clicks, types, and extracts data, "
        "then returns a structured result. Uses stealth Chromium. "
        "Good for: scraping, form submission, multi-step web workflows, "
        "login-gated pages, research tasks. "
        "If a call with use_saved_credential returns needs_2fa: when "
        "twofa_method is 'email', search the user's Gmail for the latest "
        "LibreView/Abbott code with gws_gmail_search, passing gmail_service_hint "
        "as service_name; when twofa_method is 'phone', ask the user for the "
        "6-digit SMS code. Then call this tool again with continuation_id and "
        "twofa_code. Do not ask the user for an email code unless Gmail has none."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "instruction": {
                "type": "string",
                "description": "Natural-language task for the browser agent to execute.",
            },
            "session_id": {
                "type": "string",
                "description": (
                    "Optional session identifier for log isolation. "
                    "Auto-generated if not provided."
                ),
            },
            "timeout_seconds": {
                "type": "integer",
                "description": "Per-attempt timeout in seconds. Default 120.",
            },
            "max_steps": {
                "type": "integer",
                "description": "Maximum agent steps per attempt. Default 20.",
            },
            "use_saved_credential": {
                "type": "boolean",
                "description": (
                    "If true, the sidecar loads the user's encrypted saved password "
                    "for credential_domain and lets the browser agent log in without "
                    "ever exposing the password to the model."
                ),
            },
            "credential_domain": {
                "type": "string",
                "description": (
                    "Website domain whose saved password should be used, e.g. "
                    "'libreview.com'. Required when use_saved_credential is true."
                ),
            },
            "credential_origin": {
                "type": "string",
                "description": (
                    "Optional exact login origin (e.g. https://www.libreview.com) "
                    "instead of / in addition to credential_domain."
                ),
            },
            "credential_user": {
                "type": "string",
                "description": (
                    "Optional vault user id; defaults to the current session user."
                ),
            },
            "continuation_id": {
                "type": "string",
                "description": (
                    "Returned by a previous call when it hit a 2FA page. Pass it "
                    "with twofa_code to resume the same browser session."
                ),
            },
            "twofa_method": {
                "type": "string",
                "enum": ["email", "phone"],
                "description": (
                    "2FA method for saved-credential logins: 'email' (default) "
                    "fetches the code from Gmail; 'phone' asks the user for the "
                    "SMS code. Use 'phone' if Abbott's email send fails."
                ),
            },
            "twofa_code": {
                "type": "string",
                "description": (
                    "The current 6-digit 2FA code. For email, fetch it from the "
                    "user's Gmail with gws_gmail_search; for phone, ask the user."
                ),
            },
        },
        "required": ["instruction"],
    },
}


# NOTE: registration must be a BARE top-level call — the auto-discovery AST
# scan (tools/registry.py::_module_registers_tools) only picks up modules with
# a top-level ``registry.register(...)`` expression statement. Wrapping it in
# a function or try-block silently disables the tool (regression fixed
# 2026-08-02).
registry.register(
    name="smart_browser",
    toolset="browser",
    schema=_SMART_BROWSER_SCHEMA,
    handler=_handle_smart_browser,
    check_fn=_check_available,
    is_async=False,
    description=_SMART_BROWSER_SCHEMA["description"],
    emoji="🌐",
)
logger.info("smart_browser tool registered (HTTP sidecar mode)")
