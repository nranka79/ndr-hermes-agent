"""Regression guard: one unlisted tool must never disable a whole toolset.

On 2026-09-13 ``gws_gmail_attachment_get`` was auto-registered into the
``oauth`` toolset (tools/gws_ops_tools.py generates one tool per entry in
tools/gws_ops.py's OPERATIONS table) without being added to
``toolsets._HERMES_CORE_TOOLS``.  ``messaging`` includes ``oauth``, and
``_get_platform_tools`` decided whether a platform composite implied a
configurable toolset with a strict ``issubset()`` over the *registry-resolved*
view.  One name outside the hand-maintained composite flipped that test to
False, so every gateway session -- Telegram, OpenWebUI and cron alike --
silently lost ``whatsapp_link``, ``send_message``, ``send_oauth_url`` and
every ``gws_*``/``kelsa_*`` tool.  It went unnoticed for ten days because the
models worked around it by importing the handlers inside ``execute_code``.
``apify_run_actor`` did the same thing to ``web``, taking ``web_extract``.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import model_tools  # noqa: E402  (triggers tool discovery)
from hermes_cli.tools_config import (  # noqa: E402
    _composite_covers_toolset,
    _get_platform_tools,
    audit_toolset_coverage,
)

# Tools that must reach the model on every gateway surface.  send_message is
# interactive-UI only, so it is asserted for telegram but not for api_server.
_CORE_REACHABLE = {
    "telegram": {
        "whatsapp_link", "send_message", "send_oauth_url",
        "gws_gmail_search", "gws_drive_list", "kelsa_call_tool",
        "web_search", "web_extract",
    },
    # api_server (OpenWebUI / chat.ahfl.in) carries exactly Telegram's
    # toolset -- see test_openwebui_toolset_matches_telegram below.
    "api_server": {
        "whatsapp_link", "send_message", "send_oauth_url",
        "gws_gmail_search", "gws_drive_list", "kelsa_call_tool",
        "web_search", "web_extract",
    },
    "cron": {
        "whatsapp_link", "gws_gmail_search", "gws_drive_list", "web_extract",
    },
}


def _exposed_tool_names(platform: str) -> set:
    """Tool names a session on *platform* actually gets, via the real path."""
    enabled = sorted(_get_platform_tools({}, platform))
    defs = model_tools.get_tool_definitions(
        enabled_toolsets=enabled, quiet_mode=True,
    )
    return {t["function"]["name"] for t in defs}


@pytest.mark.parametrize("platform", sorted(_CORE_REACHABLE))
def test_platform_exposes_core_tools(platform):
    missing = _CORE_REACHABLE[platform] - _exposed_tool_names(platform)
    assert not missing, (
        f"{platform} sessions cannot see {sorted(missing)}. A tool registered "
        f"under a configurable toolset is probably missing from "
        f"toolsets._HERMES_CORE_TOOLS -- see audit_toolset_coverage()."
    )


def test_messaging_toolset_enabled_for_gateway_platforms():
    """The specific key the 2026-09-13 drift switched off."""
    for platform in ("telegram", "api_server", "cron"):
        assert "messaging" in _get_platform_tools({}, platform), platform


def test_openwebui_toolset_matches_telegram():
    """OpenWebUI must expose exactly what Telegram does.

    They are the same Hermes agent on two front doors; a tool that exists on
    one and not the other is indistinguishable, from the user's side, from the
    tool being broken.  api_server used to share the trimmed
    _HERMES_CORE_TOOLS_NONINTERACTIVE bundle, which cost it clarify,
    send_message and -- because `messaging` declares send_message -- the whole
    messaging key including whatsapp_link.
    """
    telegram = _exposed_tool_names("telegram")
    api_server = _exposed_tool_names("api_server")
    assert telegram == api_server, {
        "only_on_telegram": sorted(telegram - api_server),
        "only_on_openwebui": sorted(api_server - telegram),
    }


def test_extra_registered_tool_does_not_disable_toolset():
    """The guard itself: an unlisted extra is drift, not a veto.

    ``web``'s static definition is {web_search, web_extract}; the registry has
    also filed ``apify_run_actor`` under it.  A composite that carries the
    static pair must keep ``web`` on even though it never lists the extra.
    """
    composite = {"web_search", "web_extract"}
    assert _composite_covers_toolset("web", composite, "telegram") is True


def test_missing_declared_tool_still_disables_toolset():
    """Inference intent is preserved: a composite that does not carry the
    toolset's own declared tools must not get it."""
    assert _composite_covers_toolset("web", {"terminal"}, "telegram") is False


def test_no_toolset_drift():
    """Static composite has not fallen behind the registry.

    Failing here is not itself an outage any more -- the guard above keeps the
    toolset enabled -- but it means a new tool was registered without being
    declared, which is how the 2026-09-13 incident started.
    """
    report = audit_toolset_coverage("telegram")
    assert report == {}, (
        "Tools registered under a configurable toolset but absent from "
        f"toolsets._HERMES_CORE_TOOLS: {report}"
    )
