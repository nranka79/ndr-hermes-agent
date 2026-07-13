"""
Kelsa MCP tools -- per-user OAuth-authenticated access to Kelsa-Read
(https://kelsa.io/mcp), the sales/CRM MCP server (e.g. "check leads in
Kelsa").

Why this ever silently failed: Kelsa-Read was configured under
tools/mcp_tool.py's ``mcp_servers`` config with ``auth: oauth``, which
routes through the *local interactive* OAuth flow in tools/mcp_oauth.py
(browser + localhost callback server). That flow cannot complete inside
the headless Docker gateway process -- no TTY, no browser, no way to reach
a localhost port from outside the container. It fails at startup with
"non-interactive environment and no cached tokens", the server connection
raises, and zero Kelsa tools ever get registered -- which is exactly what
was observed (no ``mcp_kelsa_read_*`` tools in the session).

PILOT (Phase 1, single-user happy path, 2026-07-13): each call here opens
its own ephemeral MCP connection authenticated with the CALLING user's
Kelsa access token (fetched/refreshed via tools.kelsa_auth), does one
operation, then disconnects. This deliberately does NOT register Kelsa in
the generic mcp_servers / tools.mcp_tool ``_servers`` persistent-connection
registry -- that registry is one-connection-per-server-name, config-driven
and process-global, with no concept of "this call is on behalf of user X"
that per-user vault tokens require. Wiring per-user identity all the way
through that registry (pooling, eviction, concurrent-user limits) is
Phase 2 -- not needed to prove the auth+call loop works end to end.

IMPORTANT: the shared MCP background event loop (tools.mcp_tool._mcp_loop)
is a process-global resource used by every configured MCP server, not just
Kelsa. These handlers call _ensure_mcp_loop() (idempotent) but must NEVER
call _stop_mcp_loop() -- doing so would tear down every other live MCP
server connection in the process, not just this ephemeral one.

Auth flow history (2026-07-13, in order discovered):
1. First build returned the raw Kelsa auth_url straight to the LLM as
   tool-result text. With no dedicated delivery tool, the model reached
   for tools.send_oauth_url instead -- hardcoded to Google Workspace,
   ignoring everything except its `label` param -- and silently sent a
   real *Google* link mislabeled "Authorize Kelsa CRM". Fixed by never
   handing the raw URL to the LLM: deliver it directly as a Telegram
   button from inside this tool (mirrors send_oauth_url._deliver_telegram_button).
2. Button delivery fixed, but authorizing still didn't complete -- nginx
   in front of the callback domain only proxied /gws/auth/callback to
   hermes; /kelsa/auth/callback fell through to n8n (the domain's default
   app) and 200'd with n8n's SPA, so the exchange never ran. Fixed by
   adding a matching nginx location block.
3. nginx fixed, still didn't complete -- Kelsa's consent page hung on
   "Authorize" with no redirect firing at all. Root cause: Kelsa's OAuth
   server does not accept a public HTTPS redirect_uri AT ALL -- only
   http://127.0.0.1:<port>/callback (documented in the pre-existing
   skills/productivity/kelsa-mcp/SKILL.md from earlier operational
   experience, found only after this was independently re-discovered the
   hard way). This makes a fully-automatic public callback impossible for
   Kelsa specifically (unlike Google). Current design: redirect_uri is a
   fixed, never-listened-on 127.0.0.1 placeholder (see tools/kelsa_auth.py).
   After authorizing, the user's browser fails to connect there (expected)
   but the address bar still carries the code/state -- the user pastes
   that back into Telegram and kelsa_complete_login below finishes the
   exchange. Same paste-back mechanism the legacy CLI flow already used
   for this exact server, reimplemented here to run per-user through
   Telegram with vault-backed storage instead of a shared flat file.
"""

import asyncio
import logging
import os

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

_KELSA_URL = "https://kelsa.io/mcp"


def _current_telegram_id() -> str | None:
    # Same pattern as tools/gws_account_resolver_tool.py -- the session
    # user id lives in a per-task ContextVar (gateway.session_context), not
    # process-global os.environ. Reading os.environ directly here would
    # return "" in every session.
    from gateway.session_context import get_gws_identity_env

    tid = get_gws_identity_env().strip()
    return tid or None


def _detect_session() -> tuple[str, str]:
    """Return (platform, chat_id) for the current session. Mirrors
    tools/send_oauth_url.py's _detect_session -- same ContextVar source."""
    try:
        from gateway.session_context import get_session_env

        platform = get_session_env("HERMES_SESSION_PLATFORM", "").lower().strip()
        chat_id = get_session_env("HERMES_SESSION_CHAT_ID", "").strip()
        return platform, chat_id
    except Exception:
        return "", ""


_PASTE_BACK_INSTRUCTIONS = (
    "After you tap Authorize, your browser will try to load a "
    "127.0.0.1 address and show a connection error / \"can't reach this "
    "page\" — that's expected, nothing is actually listening there. "
    "Copy the FULL URL from your browser's address bar at that point "
    "(it contains the authorization code) and paste it back here."
)


def _deliver_kelsa_auth_link(url: str) -> dict:
    """Deliver the Kelsa auth URL via the current session's channel.

    The URL is NEVER returned to the caller (the LLM) -- only a status
    dict. Telegram gets a real inline-keyboard button (URL carried
    byte-for-byte by Telegram, no LLM transcription involved); other
    channels get a fallback. This is the Kelsa-specific twin of
    tools/send_oauth_url.py's delivery logic -- kept separate because that
    tool is hardcoded to Google Workspace, not because the pattern differs.
    """
    platform, chat_id = _detect_session()

    if platform == "telegram" and chat_id:
        from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not bot_token:
            return {"success": False, "delivery": "telegram_button", "error": "TELEGRAM_BOT_TOKEN not set"}

        bot = Bot(token=bot_token)
        text = (
            "Click the button below to authorize Kelsa CRM.\n\n"
            "This lets Hermes read your Kelsa leads/pipeline on your behalf. "
            "You can revoke access any time from your Kelsa account settings.\n\n"
            f"{_PASTE_BACK_INSTRUCTIONS}"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Authorize Kelsa CRM", url=url)]])

        async def _send():
            try:
                msg = await bot.send_message(
                    chat_id=int(chat_id),
                    text=text,
                    reply_markup=keyboard,
                    disable_web_page_preview=True,
                )
                return msg.message_id
            finally:
                await bot.close()

        try:
            message_id = asyncio.run(_send())
        except Exception as e:
            logger.warning("Kelsa auth telegram delivery failed: %s", e)
            return {"success": False, "delivery": "telegram_button", "error": str(e)}

        return {"success": True, "delivery": "telegram_button", "message_id": message_id}

    if platform == "cli":
        import sys

        sep = "=" * 72
        sys.stderr.write(
            f"\n{sep}\nKelsa CRM Authorization Required\n{sep}\n"
            f"Open this URL in a browser to authorize:\n\n  {url}\n\n"
            f"{_PASTE_BACK_INSTRUCTIONS}\n\n{sep}\n\n"
        )
        sys.stderr.flush()
        return {"success": True, "delivery": "cli_printed"}

    return {
        "success": True,
        "delivery": "markdown_link",
        "markdown_link": f"[Authorize Kelsa CRM]({url})",
        "_instruction": (
            "Embed the markdown_link value VERBATIM in your response. "
            "Do not retype or paraphrase it. Also tell the user: "
            f"{_PASTE_BACK_INSTRUCTIONS}"
        ),
    }


KELSA_LOGIN_SCHEMA = {
    "name": "kelsa_login",
    "description": (
        "Send the current user a Kelsa CRM authorization button/link via "
        "the current channel (e.g. a Telegram button). Kelsa requires a "
        "one-time per-user OAuth login before kelsa_list_tools or "
        "kelsa_call_tool will work for that user. The tool delivers the "
        "link itself and returns only a delivery status -- it does NOT "
        "return the URL to you. Do not attempt to build or paste a Kelsa "
        "URL yourself, and NEVER use send_oauth_url for Kelsa -- that tool "
        "is hardcoded to Google Workspace and will silently send a Google "
        "link instead, mislabeled.\n\n"
        "IMPORTANT: Kelsa's OAuth server only accepts a 127.0.0.1 redirect, "
        "so after the user taps Authorize their browser will show a "
        "connection-error page at a 127.0.0.1 address -- this is EXPECTED, "
        "not a failure. Tell the user to copy that URL from their address "
        "bar and paste it back to you, then call kelsa_complete_login with "
        "that pasted text. Do not tell the user something went wrong when "
        "they report a broken-looking 127.0.0.1 page after authorizing."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

KELSA_COMPLETE_LOGIN_SCHEMA = {
    "name": "kelsa_complete_login",
    "description": (
        "Finish a Kelsa CRM authorization after the user has tapped "
        "Authorize and pasted back the resulting URL (or just the "
        "code=...&state=... portion) from their browser's address bar. "
        "Call this as soon as the user provides that pasted text following "
        "a kelsa_login prompt -- do not ask them to do anything else first."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "pasted": {
                "type": "string",
                "description": (
                    "The full URL or query string the user pasted back "
                    "(e.g. 'http://127.0.0.1:47562/callback?code=...&state=...' "
                    "or just 'code=...&state=...')."
                ),
            },
        },
        "required": ["pasted"],
    },
}

KELSA_LIST_TOOLS_SCHEMA = {
    "name": "kelsa_list_tools",
    "description": (
        "List the tools actually available on the Kelsa MCP server for the "
        "current authorized user, with each tool's description and input "
        "schema. Call this BEFORE kelsa_call_tool whenever you don't "
        "already know the exact tool name from a prior call in this "
        "session -- never guess a Kelsa tool name. If the user isn't "
        "authorized yet, this automatically sends them a fresh Kelsa "
        "authorization button (same delivery as kelsa_login) instead of "
        "returning a URL to you."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

KELSA_CALL_TOOL_SCHEMA = {
    "name": "kelsa_call_tool",
    "description": (
        "Call one tool on the Kelsa MCP server on behalf of the current "
        "authorized user (e.g. to check leads). Use kelsa_list_tools first "
        "to get the exact tool_name and its expected arguments schema."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Exact Kelsa tool name, from kelsa_list_tools.",
            },
            "arguments": {
                "type": "object",
                "description": (
                    "Arguments for the tool, matching its input schema. "
                    "Omit or pass {} if the tool takes none."
                ),
            },
        },
        "required": ["tool_name"],
    },
}


def _not_authorized_result(tid: str) -> str:
    from tools.kelsa_auth import get_auth_url

    url = get_auth_url(tid)
    delivery = _deliver_kelsa_auth_link(url)

    if not delivery.get("success"):
        return tool_error(
            f"Not authorized with Kelsa, and could not deliver a fresh "
            f"auth link: {delivery.get('error')}"
        )

    result = {"error": "Not authorized with Kelsa yet."}
    result.update(delivery)
    result["instructions"] = (
        "I already sent the user a Kelsa authorization button/link via "
        "this delivery — tell them to tap it. After they authorize, their "
        "browser will show a connection-error page at a 127.0.0.1 address "
        "— that's expected. Tell them to copy that URL and paste it back "
        "to you, then call kelsa_complete_login with the pasted text. Do "
        "NOT call send_oauth_url for this (it is Google-only), and do NOT "
        "try to construct, guess, or paste any Kelsa URL yourself."
    )
    import json

    return json.dumps(result, ensure_ascii=False)


async def _connect_and_run(token: str, fn):
    """Open an ephemeral Kelsa MCP connection, run fn(session), disconnect.

    Must be scheduled on tools.mcp_tool's shared MCP background loop (via
    _run_on_mcp_loop) -- _connect_server()/MCPServerTask internals assume
    that loop. _connect_server() does NOT touch the process-global
    _servers registry (that only happens in _discover_and_register_server,
    the config-driven startup path), so concurrent calls -- even reusing
    the same literal server name below -- never collide or leak state.
    """
    from tools.mcp_tool import _connect_server

    server = await _connect_server(
        "kelsa-read-pilot",
        {"url": _KELSA_URL, "headers": {"Authorization": f"Bearer {token}"}},
    )
    try:
        return await fn(server.session)
    finally:
        await server.shutdown()


def _get_token_or_none(tid: str):
    """Return a valid access token, or None if the user isn't authorized."""
    from tools.kelsa_auth import get_valid_access_token
    from tools.gws_vault_client import VaultNoTokenError

    try:
        return get_valid_access_token(tid)
    except VaultNoTokenError:
        return None


def kelsa_login_tool(args, **kw):
    tid = _current_telegram_id()
    if not tid:
        return tool_error("No session user context -- cannot generate a Kelsa login link.")

    from tools.kelsa_auth import has_token, get_auth_url

    try:
        if has_token(tid):
            return tool_result(message="Already authorized with Kelsa.")
    except Exception:
        pass  # fall through to generating a fresh link regardless

    url = get_auth_url(tid)
    delivery = _deliver_kelsa_auth_link(url)
    if not delivery.get("success"):
        return tool_error(f"Could not deliver Kelsa auth link: {delivery.get('error')}")

    return tool_result(
        **delivery,
        message=(
            "Sent the Kelsa authorization button/link to the user. After "
            "they authorize, they'll land on a broken-looking 127.0.0.1 "
            "page -- that's expected. Tell them to paste that URL back, "
            "then call kelsa_complete_login with it."
        ),
    )


def kelsa_complete_login_tool(args, **kw):
    tid = _current_telegram_id()
    if not tid:
        return tool_error("No session user context -- cannot complete a Kelsa login.")

    pasted = (args.get("pasted") or "").strip()
    if not pasted:
        return tool_error("pasted is required -- the URL or code=...&state=... the user gave you.")

    from tools.kelsa_auth import parse_callback_paste, exchange_and_store

    try:
        code, state = parse_callback_paste(pasted)
    except ValueError as exc:
        return tool_error(str(exc))

    if ":" not in state:
        return tool_error("Malformed state in the pasted URL -- ask the user to start a fresh kelsa_login.")
    state_tid, code_verifier = state.split(":", 1)
    state_tid = state_tid.strip()

    if state_tid != str(tid):
        return tool_error(
            "This authorization link belongs to a different user session. "
            "Ask the user to run kelsa_login themselves and paste back "
            "their own link's result."
        )

    try:
        exchange_and_store(tid, code, code_verifier)
    except Exception as exc:
        return tool_error(f"Kelsa token exchange failed: {exc}")

    return tool_result(message="Kelsa CRM authorized successfully. You can now use kelsa_list_tools / kelsa_call_tool.")


def kelsa_list_tools_tool(args, **kw):
    tid = _current_telegram_id()
    if not tid:
        return tool_error("No session user context -- cannot determine which user's Kelsa token to use.")

    try:
        token = _get_token_or_none(tid)
    except Exception as exc:
        return tool_error(f"Could not load Kelsa token: {exc}")
    if token is None:
        return _not_authorized_result(tid)

    from tools.mcp_tool import _ensure_mcp_loop, _run_on_mcp_loop

    async def _list(session):
        result = await session.list_tools()
        return [
            {
                "name": t.name,
                "description": getattr(t, "description", "") or "",
                "inputSchema": getattr(t, "inputSchema", None),
            }
            for t in result.tools
        ]

    _ensure_mcp_loop()
    try:
        tools = _run_on_mcp_loop(_connect_and_run(token, _list), timeout=40)
    except Exception as exc:
        return tool_error(f"Kelsa connection failed: {exc}")

    return tool_result(tools=tools)


def kelsa_call_tool_tool(args, **kw):
    tid = _current_telegram_id()
    if not tid:
        return tool_error("No session user context -- cannot determine which user's Kelsa token to use.")

    tool_name = (args.get("tool_name") or "").strip()
    if not tool_name:
        return tool_error("tool_name is required.")
    arguments = args.get("arguments") or {}

    try:
        token = _get_token_or_none(tid)
    except Exception as exc:
        return tool_error(f"Could not load Kelsa token: {exc}")
    if token is None:
        return _not_authorized_result(tid)

    from tools.mcp_tool import _ensure_mcp_loop, _run_on_mcp_loop

    async def _call(session):
        result = await session.call_tool(tool_name, arguments=arguments)
        parts = []
        for block in result.content or []:
            if hasattr(block, "text") and block.text:
                parts.append(block.text)
        text = "\n".join(parts)
        if result.isError:
            return {"error": text or "Kelsa tool returned an error"}
        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            return {"result": text, "structuredContent": structured}
        return {"result": text}

    _ensure_mcp_loop()
    try:
        outcome = _run_on_mcp_loop(_connect_and_run(token, _call), timeout=60)
    except Exception as exc:
        return tool_error(f"Kelsa tool call failed: {exc}")

    if "error" in outcome:
        return tool_error(outcome["error"])
    return tool_result(**outcome)


registry.register(
    name="kelsa_login",
    toolset="oauth",
    schema=KELSA_LOGIN_SCHEMA,
    handler=kelsa_login_tool,
    emoji="🔑",
)
registry.register(
    name="kelsa_complete_login",
    toolset="oauth",
    schema=KELSA_COMPLETE_LOGIN_SCHEMA,
    handler=kelsa_complete_login_tool,
    emoji="🔓",
)
registry.register(
    name="kelsa_list_tools",
    toolset="oauth",
    schema=KELSA_LIST_TOOLS_SCHEMA,
    handler=kelsa_list_tools_tool,
    emoji="📋",
)
registry.register(
    name="kelsa_call_tool",
    toolset="oauth",
    schema=KELSA_CALL_TOOL_SCHEMA,
    handler=kelsa_call_tool_tool,
    emoji="📇",
)
