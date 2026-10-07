"""
TailorTalk MCP tools -- per-user OAuth-authenticated access to the TailorTalk
MCP server (https://api.tailortalk.ai/mcp).

Twin of tools/kelsa_tool.py. Same shape, same reasons:

  * TailorTalk is NOT configured under tools/mcp_tool.py's ``mcp_servers``
    with ``auth: oauth`` -- that routes through the local-interactive flow
    (browser + localhost callback) which can never complete inside the
    headless gateway container, and the server would silently register
    zero tools.
  * Each call opens its own ephemeral MCP connection authenticated with the
    CALLING user's TailorTalk access token (fetched/refreshed from the
    gws-vault via tools.tailortalk_auth), runs one operation, disconnects.
  * The auth URL is never handed to the model. ``tailortalk_login`` delivers
    it itself (Telegram inline button, CLI print, or a pre-formatted
    markdown link for Open WebUI) and returns only a delivery status. The
    HTTPS callback (gateway/platforms/api_server.py,
    ``_handle_tailortalk_auth_callback``) completes the exchange and stores
    the token straight into the vault -- the code and token never pass
    through the LLM.
  * These handlers use the shared MCP background loop
    (tools.mcp_tool._mcp_loop). They call _ensure_mcp_loop() (idempotent)
    and must NEVER call _stop_mcp_loop() -- that would tear down every other
    live MCP connection in the process.
"""

import asyncio
import logging
import os

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

_TAILORTALK_URL = "https://api.tailortalk.ai/mcp"

# Session-level pending-auth guard: user ids with an outstanding auth URL.
# Stops the model from sending a second button while the first is live.
_pending_auth: set[str] = set()

_AUTH_FAILURE_CONTACT = (
    "If authorization keeps failing, copy all messages in this chat "
    "and share them with @ndr_ra — do not retry on your own."
)


def _current_user_id() -> str | None:
    from gateway.session_context import get_gws_identity_env

    tid = get_gws_identity_env().strip()
    return tid or None


def _detect_session() -> tuple[str, str]:
    """Return (platform, chat_id) for the current session (ContextVar source)."""
    try:
        from gateway.session_context import get_session_env

        platform = get_session_env("HERMES_SESSION_PLATFORM", "").lower().strip()
        chat_id = get_session_env("HERMES_SESSION_CHAT_ID", "").strip()
        return platform, chat_id
    except Exception:
        return "", ""


def _deliver_tailortalk_auth_link(url: str) -> dict:
    """Deliver the auth URL via the current session's channel; never return
    the URL itself to the caller (the LLM) -- only a status dict."""
    platform, chat_id = _detect_session()

    if platform == "telegram" and chat_id:
        from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

        bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
        if not bot_token:
            return {"success": False, "delivery": "telegram_button", "error": "TELEGRAM_BOT_TOKEN not set"}

        bot = Bot(token=bot_token)
        text = (
            "Click the button below to authorize TailorTalk.\n\n"
            "This lets Hermes use your TailorTalk account on your behalf "
            "through its MCP server. You can revoke access any time from "
            "your TailorTalk dashboard.\n\n"
            "After authorizing, you'll see an 'Authorization successful!' "
            "page — close it and return here. "
            f"{_AUTH_FAILURE_CONTACT}"
        )
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Authorize TailorTalk", url=url)]])

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
            logger.warning("TailorTalk auth telegram delivery failed: %s", e)
            return {"success": False, "delivery": "telegram_button", "error": str(e)}

        return {"success": True, "delivery": "telegram_button", "message_id": message_id}

    if platform == "cli":
        import sys

        sep = "=" * 72
        sys.stderr.write(
            f"\n{sep}\nTailorTalk Authorization Required\n{sep}\n"
            f"Open this URL in a browser to authorize:\n\n  {url}\n\n"
            f"After authorizing, check for 'Authorization successful!' "
            f"in the browser. {_AUTH_FAILURE_CONTACT}\n\n{sep}\n\n"
        )
        sys.stderr.flush()
        return {"success": True, "delivery": "cli_printed"}

    return {
        "success": True,
        "delivery": "markdown_link",
        "markdown_link": f"[Authorize TailorTalk]({url})",
        "_instruction": (
            "Embed the markdown_link value VERBATIM in your response. "
            "Do not retype or paraphrase it. Also tell the user: "
            "After authorizing, look for an 'Authorization successful!' "
            "page in the browser and return here. "
            f"{_AUTH_FAILURE_CONTACT}"
        ),
    }


TAILORTALK_LOGIN_SCHEMA = {
    "name": "tailortalk_login",
    "description": (
        "Send the current user a TailorTalk authorization button/link via "
        "the current channel (e.g. a Telegram button). TailorTalk requires a "
        "one-time per-user OAuth login before tailortalk_list_tools or "
        "tailortalk_call_tool will work for that user. The tool delivers the "
        "link itself and returns only a delivery status -- it does NOT "
        "return the URL to you. Do not attempt to build or paste a "
        "TailorTalk URL yourself, and NEVER use send_oauth_url for "
        "TailorTalk -- that tool is hardcoded to Google Workspace and will "
        "silently send a Google link instead, mislabeled.\n\n"
        "After the user taps Authorize, the browser will show "
        "'Authorization successful!' -- the HTTPS callback completes "
        "automatically and the token is stored directly in the vault. "
        "The token NEVER reaches you. Once the user confirms success, "
        "just call tailortalk_list_tools to proceed. Do NOT ask the user "
        "for any pasted URL or authorization code.\n\n"
        "If authorization fails (no success page), tell the user to "
        "try tailortalk_login again. If it keeps failing, ask them to share "
        "the chat history with @ndr_ra for investigation.\n\n"
        "IMPORTANT: NEVER try to read the TailorTalk token from the vault "
        "via terminal() or execute_code() -- use tailortalk_list_tools / "
        "tailortalk_call_tool instead. They handle token lookup automatically."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

TAILORTALK_LIST_TOOLS_SCHEMA = {
    "name": "tailortalk_list_tools",
    "description": (
        "List the tools actually available on the TailorTalk MCP server for "
        "the current authorized user, with each tool's description and input "
        "schema. Call this BEFORE tailortalk_call_tool whenever you don't "
        "already know the exact tool name from a prior call in this session "
        "-- never guess a TailorTalk tool name.\n\n"
        "This tool loads the TailorTalk token from the vault automatically. "
        "Do NOT try to read the token yourself or call the TailorTalk API "
        "directly via terminal() or execute_code() -- use this tool or "
        "tailortalk_call_tool.\n\n"
        "IMPORTANT: If the user is not authorized yet, this tool returns an "
        "error telling you to call tailortalk_login first. It does NOT "
        "silently generate an auth URL on its own."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

TAILORTALK_CALL_TOOL_SCHEMA = {
    "name": "tailortalk_call_tool",
    "description": (
        "Call one tool on the TailorTalk MCP server on behalf of the current "
        "authorized user. Use tailortalk_list_tools first to get the exact "
        "tool_name and its expected arguments schema.\n\n"
        "This tool loads the TailorTalk token from the vault and opens an "
        "ephemeral MCP connection automatically. Do NOT try to build a "
        "direct MCP connection or call the TailorTalk API via terminal() or "
        "execute_code() -- use this tool instead.\n\n"
        "IMPORTANT: If the user is not authorized yet, this tool returns an "
        "error telling you to call tailortalk_login first. It does NOT "
        "silently generate an auth URL on its own."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "tool_name": {
                "type": "string",
                "description": "Exact TailorTalk tool name, from tailortalk_list_tools.",
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
    tid = _current_user_id() or "unknown"
    logger.warning(
        "_not_authorized_result called from %s for user %s -- NOT auto-generating auth URL",
        caller, tid,
    )
    return tool_error(
        "Not authorized with TailorTalk yet. Call tailortalk_login first to "
        "send the user an authorization button/link. After they authorize, "
        "the browser should show 'Authorization successful!' and the token "
        "is stored automatically in the vault -- then retry this tool. "
        "If authorization keeps failing, tell the user to share chat "
        "history with @ndr_ra for investigation."
    )


async def _connect_and_run(token: str, fn):
    """Open an ephemeral TailorTalk MCP connection, run fn(session), disconnect.

    Must be scheduled on tools.mcp_tool's shared background loop via
    _run_on_mcp_loop. _connect_server() never touches the process-global
    _servers registry, so concurrent calls reusing the literal name below
    never collide.
    """
    from tools.mcp_tool import _connect_server

    server = await _connect_server(
        "tailortalk-pilot",
        {"url": _TAILORTALK_URL, "headers": {"Authorization": f"Bearer {token}"}},
    )
    try:
        return await fn(server.session)
    finally:
        await server.shutdown()


def _get_token_or_none(*, force_refresh: bool = False):
    """Return a valid access token, or None if the user isn't authorized."""
    from tools.tailortalk_auth import get_valid_access_token
    from tools.gws_vault_client import VaultNoTokenError

    try:
        return get_valid_access_token(force_refresh=force_refresh)
    except VaultNoTokenError:
        return None


def _looks_like_auth_failure(exc: BaseException) -> bool:
    """Best-effort detection of an expired/revoked token behind the MCP SDK's
    TaskGroup wrapping, so one silent refresh+retry can be attempted."""
    seen = set()
    stack = [exc]
    while stack:
        e = stack.pop()
        if id(e) in seen:
            continue
        seen.add(id(e))
        text = str(e).lower()
        if "401" in text or "unauthorized" in text or "invalid_token" in text:
            return True
        stack.extend(getattr(e, "exceptions", []) or [])
        if e.__cause__:
            stack.append(e.__cause__)
    return False


def _run_with_token(token: str, coro_factory, timeout: float):
    """Run coro_factory(token) on the MCP loop; on an auth-looking failure,
    force-refresh the token once and retry."""
    from tools.mcp_tool import _ensure_mcp_loop, _run_on_mcp_loop

    _ensure_mcp_loop()
    try:
        return _run_on_mcp_loop(coro_factory(token), timeout=timeout)
    except Exception as exc:
        if not _looks_like_auth_failure(exc):
            raise
        logger.info("TailorTalk call failed with an auth-looking error; refreshing token once and retrying")
        fresh = _get_token_or_none(force_refresh=True)
        if not fresh or fresh == token:
            raise
        return _run_on_mcp_loop(coro_factory(fresh), timeout=timeout)


def tailortalk_login_tool(args, **kw):
    tid = _current_user_id()
    if not tid:
        return tool_error("No session user context -- cannot generate a TailorTalk login link.")

    from tools.tailortalk_auth import has_token, get_auth_url, _has_valid_cached_url, set_notify_context

    if tid in _pending_auth:
        if _has_valid_cached_url():
            logger.info("tailortalk_login: pending auth already exists for user %s -- skipping", tid)
            return tool_result(
                message=(
                    "A TailorTalk authorization is already pending. I already "
                    "sent you a button — tap it and authorize in the browser. "
                    "After 'Authorization successful!' appears, return here."
                ),
                instructions=(
                    "There is already a pending TailorTalk authorization for "
                    "this user. Do NOT call tailortalk_login again. Wait for "
                    "them to authorize and confirm, then use tailortalk_list_tools."
                ),
            )
        _pending_auth.discard(tid)
        logger.info("tailortalk_login: stale pending auth discarded for user %s", tid)

    try:
        if has_token():
            logger.info("tailortalk_login: user %s already has token", tid)
            return tool_result(message="Already authorized with TailorTalk.")
    except Exception:
        pass  # fall through to generating a fresh link regardless

    url = get_auth_url()
    delivery = _deliver_tailortalk_auth_link(url)
    if not delivery.get("success"):
        return tool_error(f"Could not deliver TailorTalk auth link: {delivery.get('error')}")

    _pending_auth.add(tid)
    platform, chat_id = _detect_session()
    set_notify_context(platform, chat_id)
    logger.info(
        "tailortalk_login: delivered auth URL for user %s (delivery=%s, platform=%s, pending_set=%s)",
        tid, delivery.get("delivery"), platform, len(_pending_auth),
    )

    return tool_result(
        **delivery,
        message=(
            "Sent the TailorTalk authorization button/link to the user. "
            "After they authorize in the browser, the HTTPS callback stores "
            "the token directly in the vault. Once the user confirms success, "
            "call tailortalk_list_tools to verify and proceed. "
            "Do NOT try to read the token from the vault via terminal or "
            "execute_code -- use tailortalk_list_tools / tailortalk_call_tool instead. "
            "NEVER ask the user to paste an authorization code or URL."
        ),
    )


def tailortalk_list_tools_tool(args, **kw):
    tid = _current_user_id()
    if not tid:
        return tool_error("No session user context -- cannot determine which user's TailorTalk token to use.")

    try:
        token = _get_token_or_none()
    except Exception as exc:
        return tool_error(f"Could not load TailorTalk token: {exc}")
    if token is None:
        return _not_authorized_result("tailortalk_list_tools")

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

    try:
        tools = _run_with_token(token, lambda tok: _connect_and_run(tok, _list), timeout=40)
    except Exception as exc:
        return tool_error(f"TailorTalk connection failed: {exc}")

    return tool_result(tools=tools)


def tailortalk_call_tool_tool(args, **kw):
    tid = _current_user_id()
    if not tid:
        return tool_error("No session user context -- cannot determine which user's TailorTalk token to use.")

    tool_name = (args.get("tool_name") or "").strip()
    if not tool_name:
        return tool_error("tool_name is required.")
    arguments = args.get("arguments") or {}

    try:
        token = _get_token_or_none()
    except Exception as exc:
        return tool_error(f"Could not load TailorTalk token: {exc}")
    if token is None:
        return _not_authorized_result("tailortalk_call_tool")

    async def _call(session):
        result = await session.call_tool(tool_name, arguments=arguments)
        parts = []
        for block in result.content or []:
            if hasattr(block, "text") and block.text:
                parts.append(block.text)
        text = "\n".join(parts)
        if result.isError:
            return {"error": text or "TailorTalk tool returned an error"}
        structured = getattr(result, "structuredContent", None)
        if structured is not None:
            return {"result": text, "structuredContent": structured}
        return {"result": text}

    try:
        outcome = _run_with_token(token, lambda tok: _connect_and_run(tok, _call), timeout=60)
    except Exception as exc:
        return tool_error(f"TailorTalk tool call failed: {exc}")

    if "error" in outcome:
        return tool_error(outcome["error"])
    return tool_result(**outcome)


registry.register(
    name="tailortalk_login",
    toolset="oauth",
    schema=TAILORTALK_LOGIN_SCHEMA,
    handler=tailortalk_login_tool,
    emoji="🔑",
)
registry.register(
    name="tailortalk_list_tools",
    toolset="oauth",
    schema=TAILORTALK_LIST_TOOLS_SCHEMA,
    handler=tailortalk_list_tools_tool,
    emoji="📋",
)
registry.register(
    name="tailortalk_call_tool",
    toolset="oauth",
    schema=TAILORTALK_CALL_TOOL_SCHEMA,
    handler=tailortalk_call_tool_tool,
    emoji="🧵",
)
