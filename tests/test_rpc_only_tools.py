"""Regression: RPC-only tools (gws_fetch_token) are hidden from the LLM-facing
tool schema but stay in _last_resolved_tool_names so the execute_code sandbox
still generates their RPC stubs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import model_tools  # noqa: E402  (triggers tool discovery)


def test_rpc_only_tool_hidden_from_schema_but_kept_for_sandbox():
    tools = model_tools.get_tool_definitions(
        enabled_toolsets=["hermes-telegram"], quiet_mode=True,
    )
    names = [t["function"]["name"] for t in tools]
    assert "gws_fetch_token" not in names
    assert "gws_fetch_token" in model_tools._last_resolved_tool_names


def test_include_rpc_only_readds_hidden_tools():
    # The execute_code dispatch re-adds RPC-only tools to the sandbox stub set
    # even when the caller passes the LLM-visible tool list (agent.valid_tool_names).
    base = [n for n in model_tools._last_resolved_tool_names if n != "gws_fetch_token"]
    assert "gws_fetch_token" not in base
    re_added = model_tools._include_rpc_only(list(base))
    assert "gws_fetch_token" in re_added


def test_dwd_and_oauth_tools_registered_in_registry():
    from tools.registry import registry

    registered = set(registry._tools)
    assert "gws_dwd_gmail_search" in registered
    assert "gws_dwd_drive_transfer_ownership" in registered
    assert "gws_dwd_resolve" in registered
    assert "gws_gmail_search" in registered
    assert "gws_drive_create_file" in registered
    # No send anywhere.
    assert "gws_dwd_gmail_send" not in registered
    assert "gws_gmail_send" not in registered