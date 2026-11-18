"""
Tally Prime MCP tools -- READ-ONLY access to the company's Tally Prime books
through the Tally MCP server on the playground VPS
(https://apps.ahfl.in/tally-mcp/mcp, repo nranka79 fork of QalaLabs/tally-mcp-server,
branch ``ndr-readonly``).

Shape follows tools/tailortalk_tool.py (ephemeral MCP connection per call on the
shared MCP loop), but auth is different: Tally is ONE shared company dataset,
so there is no per-user OAuth. Instead:

  * The server URL, its static service key and the list of canonical vault
    user ids allowed to read Tally live in the vault under
    ``hermes-system`` / ``tally-mcp`` as JSON::

        {"url": "...", "api_key": "...", "allowed_users": ["ndr-7449813913"]}

    Edit that record to grant/revoke access -- no redeploy needed.
  * Every call checks the calling user's canonical uid against
    ``allowed_users`` (fail-closed).

WRITES ARE DISABLED (2026-11-18). Three independent layers:
  1. The server does not register write tools (TALLY_READ_ONLY).
  2. The server refuses any non-Export XML to Tally.
  3. This module only forwards tool names in ``_READ_TOOLS``.
Writes will later go through a human-approval layer; until then do not add
write tool names here.

These handlers use the shared MCP background loop (tools.mcp_tool._mcp_loop):
call _ensure_mcp_loop() (idempotent) and NEVER _stop_mcp_loop().
"""

import json
import logging

from tools.registry import registry, tool_error, tool_result

logger = logging.getLogger(__name__)

_VAULT_USER = "hermes-system"
_VAULT_SERVICE = "tally-mcp"

# Read-only allowlist (layer 3). Anything else is refused before any network call.
_READ_TOOLS = frozenset({
    "metadata-collection", "metadata-fields", "query-option-values",
    "query-database", "query-collection", "list-master", "chart-of-accounts",
    "trial-balance", "profit-loss", "balance-sheet", "stock-summary",
    "ledger-balance", "stock-item-balance", "bills-outstanding",
    "ledger-account", "stock-item-account", "fetch_daybook", "reconcile_gst",
})

_WRITE_REFUSAL = (
    "Tally is connected in READ-ONLY mode. Creating or changing anything in "
    "Tally (ledgers, vouchers, syncs, switching company/period) is disabled "
    "until a human-approval workflow is in place. Tell the user this plainly; "
    "do not try another route (terminal, execute_code, direct HTTP) to write to Tally."
)


class _TallyConfigError(RuntimeError):
    pass


def _load_config() -> dict:
    from tools import gws_vault_client as vault

    try:
        raw = vault.get_token(_VAULT_USER, _VAULT_SERVICE)
    except Exception as exc:  # VaultNoTokenError / VaultError / socket
        raise _TallyConfigError(f"Tally MCP is not configured in the vault ({type(exc).__name__}).") from exc
    try:
        cfg = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise _TallyConfigError("Tally MCP vault record is not valid JSON.") from exc
    if not cfg.get("url") or not cfg.get("api_key"):
        raise _TallyConfigError("Tally MCP vault record is missing url/api_key.")
    return cfg


def _check_access(cfg: dict) -> str | None:
    """Return an error message if the current user may not read Tally, else None."""
    from tools.gws_auth import _current_telegram_id, canonical_uid

    raw = _current_telegram_id()
    if not raw:
        return "No session user context -- cannot check Tally access."
    uid = canonical_uid(raw)
    allowed = {str(u).strip() for u in cfg.get("allowed_users") or []}
    if uid in allowed or raw in allowed:
        return None
    logger.warning("tally: access denied for %s (canonical %s)", raw, uid)
    return (
        "This user is not authorized to access Tally data. Access is granted "
        "per user by the administrator (@ndr_ra). Do not try to work around this."
    )


def _available() -> bool:
    try:
        from tools.gws_vault_client import VAULT_SOCKET
        import os

        return bool(VAULT_SOCKET) and os.path.exists(VAULT_SOCKET)
    except Exception:
        return False


async def _connect_and_run(cfg: dict, fn):
    from tools.mcp_tool import _connect_server

    server = await _connect_server(
        "tally-readonly",
        {"url": cfg["url"], "headers": {"Authorization": f"Bearer {cfg['api_key']}"}},
    )
    try:
        return await fn(server.session)
    finally:
        await server.shutdown()


def _run(cfg: dict, fn, timeout: float):
    from tools.mcp_tool import _ensure_mcp_loop, _run_on_mcp_loop

    _ensure_mcp_loop()
    return _run_on_mcp_loop(_connect_and_run(cfg, fn), timeout=timeout)


def _flatten_error(exc: BaseException) -> str:
    leaves = []
    stack = [exc]
    while stack:
        e = stack.pop()
        subs = getattr(e, "exceptions", None)
        if subs:
            stack.extend(subs)
        else:
            leaves.append(f"{type(e).__name__}: {e}")
    return "; ".join(leaves) or repr(exc)


TALLY_LIST_TOOLS_SCHEMA = {
    "name": "tally_list_tools",
    "description": (
        "List the READ-ONLY tools available on the company's Tally Prime "
        "accounting server (ledgers, groups, trial balance, P&L, balance sheet, "
        "stock summary, bills outstanding/receivables/payables, ledger and stock "
        "statements, day book, raw collection queries + SQL over cached results), "
        "with each tool's description and input schema. Call this before "
        "tally_call_tool whenever you don't already know the exact tool name and "
        "arguments from this session -- never guess.\n\n"
        "Tally is READ-ONLY: nothing can be created or modified in Tally. Most "
        "report tools return a tableID; read it with the 'query-database' tool "
        "(SQL SELECT on that table). Amounts: negative = Debit, positive = Credit. "
        "Dates are YYYY-MM-DD; Indian financial year runs 1 Apr - 31 Mar."
    ),
    "parameters": {"type": "object", "properties": {}, "required": []},
}

TALLY_CALL_TOOL_SCHEMA = {
    "name": "tally_call_tool",
    "description": (
        "Call one READ-ONLY tool on the company's Tally Prime accounting server. "
        "Use tally_list_tools first to get the exact tool_name and its arguments. "
        "Typical flow: 'list-master' to find exact ledger/group/item names -> a "
        "report tool (e.g. 'trial-balance', 'ledger-account', 'bills-outstanding') "
        "which returns a tableID -> 'query-database' with a SELECT on that tableID "
        "to read/aggregate rows.\n\n"
        "Writes (creating/updating ledgers or vouchers, syncing, switching company "
        "or period) are DISABLED and will be refused -- tell the user so rather "
        "than looking for another way. If Tally itself is unreachable, say that the "
        "Tally connection is offline; do not invent figures."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "tool_name": {"type": "string", "description": "Exact tool name from tally_list_tools."},
            "arguments": {
                "type": "object",
                "description": "Arguments matching the tool's input schema; {} if none.",
            },
        },
        "required": ["tool_name"],
    },
}


def tally_list_tools_tool(args, **kw):
    try:
        cfg = _load_config()
    except _TallyConfigError as exc:
        return tool_error(str(exc))
    denied = _check_access(cfg)
    if denied:
        return tool_error(denied)

    async def _list(session):
        result = await session.list_tools()
        return [
            {
                "name": t.name,
                "description": getattr(t, "description", "") or "",
                "inputSchema": getattr(t, "inputSchema", None),
            }
            for t in result.tools
            if t.name in _READ_TOOLS
        ]

    try:
        tools = _run(cfg, _list, timeout=40)
    except Exception as exc:
        return tool_error(f"Tally MCP connection failed: {_flatten_error(exc)}")
    return tool_result(tools=tools, mode="read-only")


def tally_call_tool_tool(args, **kw):
    tool_name = (args.get("tool_name") or "").strip()
    if not tool_name:
        return tool_error("tool_name is required.")
    if tool_name not in _READ_TOOLS:
        logger.warning("tally: refused non-read tool %r", tool_name)
        return tool_error(f"'{tool_name}' is not an available read-only Tally tool. {_WRITE_REFUSAL}")
    arguments = args.get("arguments") or {}
    if not isinstance(arguments, dict):
        return tool_error("arguments must be an object.")

    try:
        cfg = _load_config()
    except _TallyConfigError as exc:
        return tool_error(str(exc))
    denied = _check_access(cfg)
    if denied:
        return tool_error(denied)

    async def _call(session):
        result = await session.call_tool(tool_name, arguments=arguments)
        parts = [b.text for b in (result.content or []) if getattr(b, "text", None)]
        text = "\n".join(parts)
        if result.isError:
            return {"error": text or "Tally tool returned an error"}
        return {"result": text}

    try:
        outcome = _run(cfg, _call, timeout=180)
    except Exception as exc:
        return tool_error(f"Tally tool call failed: {_flatten_error(exc)}")

    if "error" in outcome:
        err = outcome["error"]
        if "Unable to connect to Tally" in err or "ECONNREFUSED" in err:
            err = (
                "The Tally server is not reachable right now (the office Tally PC / "
                "its tunnel is offline). Tell the user Tally is offline; do not guess numbers. "
                f"Detail: {err}"
            )
        return tool_error(err)
    return tool_result(**outcome)


registry.register(
    name="tally_list_tools",
    toolset="tally",
    schema=TALLY_LIST_TOOLS_SCHEMA,
    handler=tally_list_tools_tool,
    check_fn=_available,
    emoji="📒",
)
registry.register(
    name="tally_call_tool",
    toolset="tally",
    schema=TALLY_CALL_TOOL_SCHEMA,
    handler=tally_call_tool_tool,
    check_fn=_available,
    emoji="📒",
)
