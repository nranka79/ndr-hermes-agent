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

# Layer 3: session-level pending-auth guard. Tracks telegram_ids that have
# an outstanding Kelsa auth URL (one was generated but the user hasn't
# completed the exchange yet). Prevents the LLM from generating multiple
# buttons for the same user.
_pending_auth: set[str] = set()


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


_AUTH_FAILURE_CONTACT = (
    "If authorization keeps failing, copy all messages in this chat "
    "and share them with @ndr_ra — do not retry on your own."
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
            "After authorizing, you'll see an 'Authorization successful!' "
            "page — close it and return here. "
            f"{_AUTH_FAILURE_CONTACT}"
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
            f"After authorizing, check for 'Authorization successful!' "
            f"in the browser. {_AUTH_FAILURE_CONTACT}\n\n{sep}\n\n"
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
            "After authorizing, look for an 'Authorization successful!' "
            "page in the browser and return here. "
            f"{_AUTH_FAILURE_CONTACT}"
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
        "After the user taps Authorize, the browser will show "
        "'Authorization successful!' -- the HTTPS callback completes "
        "automatically and the token is stored directly in the vault. "
        "The token NEVER reaches you. Once the user confirms success, "
        "just call kelsa_list_tools to proceed. Do NOT ask the user for "
        "any pasted URL or authorization code.\n\n"
        "If authorization fails (no success page), tell the user to "
        "try kelsa_login again. If it keeps failing, ask them to share "
        "the chat history with @ndr_ra for investigation. Do NOT suggest "
        "pasting any URL or code from the browser's address bar.\n\n"
        "IMPORTANT: NEVER try to read the Kelsa token from the vault via "
        "terminal() or execute_code() -- use kelsa_list_tools / "
        "kelsa_call_tool instead. They handle token lookup automatically."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

KELSA_COMPLETE_LOGIN_SCHEMA = {
    "name": "kelsa_complete_login",
    "description": (
        "DEPRECATED — do NOT use this tool. The HTTPS callback handles "
        "authorization automatically. Never ask the user to paste an "
        "authorization code or URL — OAuth codes must never pass through "
        "the LLM. If authorization failed, call kelsa_login again or "
        "ask the user to contact @ndr_ra."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

KELSA_LIST_TOOLS_SCHEMA = {
    "name": "kelsa_list_tools",
    "description": (
        "List the tools actually available on the Kelsa MCP server for the "
        "current authorized user, with each tool's description and input "
        "schema. Call this BEFORE kelsa_call_tool whenever you don't "
        "already know the exact tool name from a prior call in this "
        "session -- never guess a Kelsa tool name.\n\n"
        "This tool loads the Kelsa token from the vault automatically. "
        "Do NOT try to read the token yourself or call the Kelsa API "
        "directly via terminal() or execute_code() -- use this tool or "
        "kelsa_call_tool.\n\n"
        "IMPORTANT: If the user is not authorized yet, this tool returns an "
        "error telling you to call kelsa_login first. It does NOT silently "
        "generate an auth URL on its own."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

KELSA_CALL_TOOL_SCHEMA = {
    "name": "kelsa_call_tool",
    "description": (
        "Call one tool on the Kelsa MCP server on behalf of the current "
        "authorized user (e.g. to check leads). Use kelsa_list_tools first "
        "to get the exact tool_name and its expected arguments schema.\n\n"
        "This tool loads the Kelsa token from the vault and opens an "
        "ephemeral MCP connection automatically. Do NOT try to build a "
        "direct MCP connection or call the Kelsa API via terminal() or "
        "execute_code() -- use this tool instead.\n\n"
        "IMPORTANT: If the user is not authorized yet, this tool returns an "
        "error telling you to call kelsa_login first. It does NOT silently "
        "generate an auth URL on its own."
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


def _not_authorized_result(caller: str) -> str:
    """Return a clear error directing the model to use ``kelsa_login``.

    Layer 2: no longer auto-generates an auth URL. ``kelsa_list_tools`` and
    ``kelsa_call_tool`` returning this will NOT create a side-effect button
    -- the LLM must explicitly call ``kelsa_login`` to start auth.
    """
    tid = _current_telegram_id() or "unknown"
    logger.warning(
        "_not_authorized_result called from %s for user %s "
        "-- NOT auto-generating auth URL (Layer 2)",
        caller, tid,
    )
    return tool_error(
        "Not authorized with Kelsa yet. Call kelsa_login first to send the "
        "user an authorization button/link. After they authorize, the "
        "browser should show 'Authorization successful!' and the token is "
        "stored automatically in the vault -- then retry this tool. "
        "If authorization keeps failing, tell the user to share chat "
        "history with @ndr_ra for investigation."
    )


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


def _get_token_or_none():
    """Return a valid access token, or None if the user isn't authorized."""
    from tools.kelsa_auth import get_valid_access_token
    from tools.gws_vault_client import VaultNoTokenError

    try:
        return get_valid_access_token()
    except VaultNoTokenError:
        return None


def kelsa_login_tool(args, **kw):
    tid = _current_telegram_id()
    if not tid:
        return tool_error("No session user context -- cannot generate a Kelsa login link.")

    from tools.kelsa_auth import has_token, get_auth_url, _has_valid_cached_url

    # Layer 3: if an auth is already pending and the cached URL is still
    # valid, don't generate another URL. If the cache has expired (user
    # abandoned the first attempt), clear the pending flag and let through.
    if tid in _pending_auth:
        if _has_valid_cached_url():
            logger.info("kelsa_login: pending auth already exists for user %s -- skipping", tid)
            return tool_result(
                message=(
                    "A Kelsa authorization is already pending. I already sent "
                    "you a button — tap it and authorize in the browser. "
                    "After 'Authorization successful!' appears, return here."
                ),
                instructions=(
                    "There is already a pending Kelsa authorization for this "
                    "user. Do NOT call kelsa_login again. Wait for them to "
                    "authorize and confirm, then use kelsa_list_tools."
                ),
            )
        # Cache expired but _pending_auth still has the tid (user abandoned
        # the first attempt). Clear the stale flag and fall through to
        # generate a fresh URL.
        _pending_auth.discard(tid)
        logger.info("kelsa_login: stale pending auth discarded for user %s -- generating fresh URL", tid)

    try:
        if has_token():
            logger.info("kelsa_login: user %s already has token", tid)
            return tool_result(message="Already authorized with Kelsa.")
    except Exception:
        pass  # fall through to generating a fresh link regardless

    url = get_auth_url()
    delivery = _deliver_kelsa_auth_link(url)
    if not delivery.get("success"):
        return tool_error(f"Could not deliver Kelsa auth link: {delivery.get('error')}")

    _pending_auth.add(tid)
    from tools.kelsa_auth import set_notify_context

    platform, chat_id = _detect_session()
    set_notify_context(platform, chat_id)
    logger.info(
        "kelsa_login: delivered auth URL for user %s (delivery=%s, platform=%s, pending_set=%s)",
        tid, delivery.get("delivery"), platform, len(_pending_auth),
    )

    return tool_result(
        **delivery,
        message=(
            "Sent the Kelsa authorization button/link to the user. "
            "After they authorize in the browser, the HTTPS callback stores "
            "the token directly in the vault. Once the user confirms success, "
            "call kelsa_list_tools to verify and proceed. "
            "Do NOT try to read the token from the vault via terminal or "
            "execute_code -- use kelsa_list_tools / kelsa_call_tool instead. "
            "NEVER ask the user to paste an authorization code or URL."
        ),
    )


def kelsa_complete_login_tool(args, **kw):
    return tool_error(
        "This tool is DEPRECATED. The HTTPS callback handles authorization "
        "automatically — OAuth codes must never pass through the LLM. "
        "Call kelsa_login again if the user needs to re-authorize, or "
        "ask them to share chat history with @ndr_ra if auth keeps failing."
    )


def kelsa_list_tools_tool(args, **kw):
    tid = _current_telegram_id()
    if not tid:
        return tool_error("No session user context -- cannot determine which user's Kelsa token to use.")

    try:
        token = _get_token_or_none()
    except Exception as exc:
        return tool_error(f"Could not load Kelsa token: {exc}")
    if token is None:
        return _not_authorized_result("kelsa_list_tools")

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
        token = _get_token_or_none()
    except Exception as exc:
        return tool_error(f"Could not load Kelsa token: {exc}")
    if token is None:
        return _not_authorized_result("kelsa_call_tool")

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
