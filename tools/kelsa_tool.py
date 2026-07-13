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
"""

import logging

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


KELSA_LOGIN_SCHEMA = {
    "name": "kelsa_login",
    "description": (
        "Generate a Kelsa authorization link for the current user. Kelsa "
        "requires a one-time per-user OAuth login before kelsa_list_tools "
        "or kelsa_call_tool will work for that user. Send the returned "
        "auth_url to the user (verbatim, as a clickable link) and ask them "
        "to open it and authorize, then retry the original request."
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
        "session -- never guess a Kelsa tool name."
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
    return tool_error(
        "Not authorized with Kelsa yet.",
        auth_url=url,
        instructions=(
            "Send this auth_url to the user as a clickable link and ask "
            "them to open it and authorize, then retry."
        ),
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
    return tool_result(auth_url=url, message="Send this link to the user to authorize Kelsa.")


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
