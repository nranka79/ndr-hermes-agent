"""Tests for tools/send_oauth_url.py — channel-aware OAuth delivery.

These tests pin the load-bearing property of the tool: **the URL is never
returned to the LLM**. The tool computes the URL inside the function and
hands it to the channel-specific delivery (Telegram button / CLI print /
markdown link). The LLM's return value is a status object, never the URL.

Also pinned:
  * The tool computes the URL via ``gws_auth.get_auth_url`` (no LLM
    transcription, no string-stitching).
  * Each channel's delivery primitive is invoked with the URL in the
    right place (button URL, stderr print, markdown link).
  * Channels that support buttons (Telegram) get zero URL in the
    return value. Channels that don't (markdown) get the URL only
    as a pre-formatted ``[label](url)`` link with a "verbatim" hint.
  * check_requirements gates on HERMES_OAUTH_CLIENT_ID + _SECRET.
"""

from __future__ import annotations

import io
import json
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Test fixtures: stub session_context + the gws_auth OAuth URL builder
# ---------------------------------------------------------------------------

CORRECT_OAUTH_URL = (
    "https://accounts.google.com/o/oauth2/auth?"
    "response_type=code&"
    "client_id=353166898892-1i1vl4p3uakjahefg11jpvrhnclei5l3"
    ".apps.googleusercontent.com&"
    "redirect_uri=https%3A%2F%2Ftranscribe.ahfl.in%2Fgws%2Fauth%2Fcallback&"
    "scope=openid+email&"
    "state=7449813913"
)


def _stub_get_auth_url(login_hint=None, telegram_id="7449813913"):
    """Return a callable that mimics ``gws_auth.get_auth_url`` and records its args."""
    calls = []

    def _impl(tid, login_hint=None):
        calls.append({"telegram_id": tid, "login_hint": login_hint})
        return CORRECT_OAUTH_URL

    _impl.calls = calls
    return _impl


def _stub_session_context(platform: str, chat_id: str):
    """Return a mock for gateway.session_context.get_session_env."""
    def _get(name, default=""):
        mapping = {
            "HERMES_SESSION_PLATFORM": platform,
            "HERMES_SESSION_CHAT_ID": chat_id,
            "HERMES_SESSION_USER_ID": "7449813913",
        }
        return mapping.get(name, default)
    return _get


@pytest.fixture
def patched_env(monkeypatch):
    """Set the env vars check_requirements looks for."""
    monkeypatch.setenv("HERMES_OAUTH_CLIENT_ID", "test-client-id.apps.googleusercontent.com")
    monkeypatch.setenv("HERMES_OAUTH_CLIENT_SECRET", "GOCSPX-testsecret")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-bot-token")


# ---------------------------------------------------------------------------
# check_requirements
# ---------------------------------------------------------------------------

class TestCheckRequirements:
    def test_passes_when_oauth_env_set(self, patched_env):
        from tools.send_oauth_url import check_requirements
        assert check_requirements() is True

    def test_fails_when_oauth_client_id_missing(self, monkeypatch):
        monkeypatch.setenv("HERMES_OAUTH_CLIENT_ID", "")
        monkeypatch.setenv("HERMES_OAUTH_CLIENT_SECRET", "GOCSPX-test")
        from tools.send_oauth_url import check_requirements
        assert check_requirements() is False

    def test_fails_when_oauth_client_secret_missing(self, monkeypatch):
        monkeypatch.setenv("HERMES_OAUTH_CLIENT_ID", "test.apps.googleusercontent.com")
        monkeypatch.setenv("HERMES_OAUTH_CLIENT_SECRET", "")
        from tools.send_oauth_url import check_requirements
        assert check_requirements() is False


# ---------------------------------------------------------------------------
# Telegram delivery — URL stays in the button, NEVER in the return value
# ---------------------------------------------------------------------------

class TestTelegramDelivery:
    def test_url_goes_into_button_never_returned(self, patched_env):
        from tools import send_oauth_url

        with patch.object(send_oauth_url, "_detect_session",
                          return_value=("telegram", "7449813913")), \
             patch.object(send_oauth_url, "_deliver_telegram_button",
                          wraps=send_oauth_url._deliver_telegram_button) as mock_deliver:

            # Mock the telegram.Bot that the inner function imports lazily
            with patch("telegram.Bot") as MockBot:
                bot_instance = MagicMock()
                bot_instance.send_message = AsyncMock(return_value=MagicMock(message_id=999))
                bot_instance.close = AsyncMock()
                MockBot.return_value = bot_instance

                result_json = send_oauth_url.send_oauth_url(
                    telegram_id="7449813913",
                    login_hint="ndr@draas.com",
                    service_name="google-draas",
                )

        result = json.loads(result_json)
        # Delivery succeeded
        assert result["success"] is True
        assert result["delivery"] == "telegram_button"
        assert result["message_id"] == 999
        assert result["service"] == "google-draas"

        # CRITICAL: the URL must NOT be in the return value
        assert "url" not in result
        assert CORRECT_OAUTH_URL not in result_json
        assert "googleusercontent" not in result_json

        # Verify the URL was passed to the button
        call_args = bot_instance.send_message.call_args
        reply_markup = call_args.kwargs["reply_markup"]
        buttons = reply_markup.inline_keyboard[0]
        assert len(buttons) == 1
        assert buttons[0].url == CORRECT_OAUTH_URL
        # And the text does NOT contain the URL
        assert CORRECT_OAUTH_URL not in call_args.kwargs["text"]

    def test_telegram_delivery_fails_gracefully_when_no_token(self, monkeypatch):
        monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
        monkeypatch.setenv("HERMES_OAUTH_CLIENT_ID", "x")
        monkeypatch.setenv("HERMES_OAUTH_CLIENT_SECRET", "y")
        from tools import send_oauth_url
        result = send_oauth_url._deliver_telegram_button(
            chat_id="7449813913", url="https://x", label="L",
            login_hint=None, service_name=None,
        )
        assert result["success"] is False
        assert result["delivery"] == "telegram_button"
        assert "TELEGRAM_BOT_TOKEN" in result["error"]


# ---------------------------------------------------------------------------
# CLI delivery — URL goes to stderr, NEVER to the return value
# ---------------------------------------------------------------------------

class TestCliDelivery:
    def test_url_printed_to_stderr_not_returned(self, patched_env, capsys):
        from tools import send_oauth_url

        # The helper returns a dict; the public entrypoint stringifies.
        result = send_oauth_url._deliver_cli_print(
            url=CORRECT_OAUTH_URL,
            label="Authorize Google account",
            login_hint="ndr@draas.com",
            service_name="google-draas",
        )

        # The URL is in stderr (visible to the user)
        captured = capsys.readouterr()
        assert CORRECT_OAUTH_URL in captured.err
        assert "OAuth Authorization Required" in captured.err

        # CRITICAL: the URL must NOT be in the return value
        assert "url" not in result
        assert CORRECT_OAUTH_URL not in json.dumps(result)
        assert "googleusercontent" not in json.dumps(result)

        # Status fields are correct
        assert result["success"] is True
        assert result["delivery"] == "cli_printed"
        assert result["service"] == "google-draas"


# ---------------------------------------------------------------------------
# Markdown / Open WebUI delivery — pre-formatted link with "use verbatim" hint
# ---------------------------------------------------------------------------

class TestMarkdownLinkDelivery:
    def test_returns_preformatted_link_with_instruction(self, patched_env):
        from tools import send_oauth_url

        # The helper returns a dict; the public entrypoint stringifies.
        result = send_oauth_url._deliver_markdown_link(
            url=CORRECT_OAUTH_URL,
            label="Authorize Google account",
            login_hint="ndr@draas.com",
            service_name="google-draas",
        )

        # The URL is in the markdown_link, but framed as "embed this verbatim"
        assert result["success"] is True
        assert result["delivery"] == "markdown_link"
        assert result["markdown_link"] == f"[Authorize Google account]({CORRECT_OAUTH_URL})"
        assert "VERBATIM" in result["_instruction"]
        assert "google." in result["_instruction"]  # warning about the truncation

        # The URL IS present in the JSON for this channel (no button primitive)
        # but it's pre-formatted so the LLM has no reason to retype it.
        assert CORRECT_OAUTH_URL in json.dumps(result)


# ---------------------------------------------------------------------------
# Channel routing — main send_oauth_url() dispatches to the right channel
# ---------------------------------------------------------------------------

class TestChannelRouting:
    """Verify the main entrypoint dispatches based on session platform."""

    def test_routes_to_telegram_when_session_is_telegram(self, patched_env):
        from tools import send_oauth_url

        with patch("gateway.session_context.get_session_env",
                   side_effect=_stub_session_context("telegram", "7449813913")), \
             patch.object(send_oauth_url, "_deliver_telegram_button",
                          wraps=send_oauth_url._deliver_telegram_button) as mock_tg, \
             patch.object(send_oauth_url, "_deliver_cli_print") as mock_cli, \
             patch.object(send_oauth_url, "_deliver_markdown_link") as mock_md, \
             patch("telegram.Bot") as MockBot:

            bot_instance = MagicMock()
            bot_instance.send_message = AsyncMock(return_value=MagicMock(message_id=1))
            bot_instance.close = AsyncMock()
            MockBot.return_value = bot_instance

            send_oauth_url.send_oauth_url(telegram_id="7449813913")

        mock_tg.assert_called_once()
        mock_cli.assert_not_called()
        mock_md.assert_not_called()

    def test_routes_to_cli_when_session_is_cli(self, patched_env, capsys):
        from tools import send_oauth_url

        with patch("gateway.session_context.get_session_env",
                   side_effect=_stub_session_context("cli", "")), \
             patch.object(send_oauth_url, "_deliver_cli_print",
                          wraps=send_oauth_url._deliver_cli_print) as mock_cli, \
             patch.object(send_oauth_url, "_deliver_telegram_button") as mock_tg, \
             patch.object(send_oauth_url, "_deliver_markdown_link") as mock_md:

            send_oauth_url.send_oauth_url(telegram_id="7449813913")

        mock_cli.assert_called_once()
        mock_tg.assert_not_called()
        mock_md.assert_not_called()

    def test_routes_to_markdown_when_session_is_webui(self, patched_env):
        from tools import send_oauth_url

        with patch("gateway.session_context.get_session_env",
                   side_effect=_stub_session_context("open_webui", "chat-id")), \
             patch.object(send_oauth_url, "_deliver_markdown_link",
                          wraps=send_oauth_url._deliver_markdown_link) as mock_md, \
             patch.object(send_oauth_url, "_deliver_telegram_button") as mock_tg, \
             patch.object(send_oauth_url, "_deliver_cli_print") as mock_cli:

            send_oauth_url.send_oauth_url(telegram_id="7449813913")

        mock_md.assert_called_once()
        mock_tg.assert_not_called()
        mock_cli.assert_not_called()

    def test_falls_back_to_markdown_when_no_session(self, patched_env):
        """No HERMES_SESSION_PLATFORM (cron, tests) — markdown fallback."""
        from tools import send_oauth_url

        with patch("gateway.session_context.get_session_env",
                   side_effect=_stub_session_context("", "")), \
             patch.object(send_oauth_url, "_deliver_markdown_link",
                          wraps=send_oauth_url._deliver_markdown_link) as mock_md:

            send_oauth_url.send_oauth_url(telegram_id="7449813913")

        mock_md.assert_called_once()

    def test_passes_login_hint_to_url_builder(self, patched_env):
        """The URL builder is called with telegram_id + login_hint."""
        from tools import send_oauth_url

        with patch("gateway.session_context.get_session_env",
                   side_effect=_stub_session_context("cli", "")), \
             patch("tools.gws_auth.get_auth_url",
                   wraps=_stub_get_auth_url()) as mock_url, \
             patch.object(send_oauth_url, "_deliver_cli_print",
                          wraps=send_oauth_url._deliver_cli_print):

            send_oauth_url.send_oauth_url(
                telegram_id="7449813913",
                login_hint="ndr@draas.com",
            )

        # The URL builder was called with the right args
        assert len(mock_url.calls) == 1
        assert mock_url.calls[0]["telegram_id"] == "7449813913"
        assert mock_url.calls[0]["login_hint"] == "ndr@draas.com"


# ---------------------------------------------------------------------------
# Regression: the exact failure mode that motivated this tool
# ---------------------------------------------------------------------------

class TestNoUrlInReturnValue:
    """Lock down the invariant across all channels: the URL is never in
    the LLM-returned JSON. The LLM must not have the URL to (mis)transcribe."""

    @pytest.mark.parametrize("platform,chat_id", [
        ("telegram", "7449813913"),
        ("cli", ""),
        ("open_webui", "some-chat"),
        ("webui", "some-chat"),
        ("", ""),  # no session (cron, test)
    ])
    def test_url_never_in_returned_json(self, patched_env, platform, chat_id):
        from tools import send_oauth_url

        with patch("gateway.session_context.get_session_env",
                   side_effect=_stub_session_context(platform, chat_id)), \
             patch("telegram.Bot") as MockBot:
            bot_instance = MagicMock()
            bot_instance.send_message = AsyncMock(return_value=MagicMock(message_id=1))
            bot_instance.close = AsyncMock()
            MockBot.return_value = bot_instance

            result_json = send_oauth_url.send_oauth_url(
                telegram_id="7449813913",
                login_hint="ndr@draas.com",
            )

        # For non-markdown channels, the URL must not appear at all
        if platform in ("", "telegram", "cli"):
            assert "googleusercontent" not in result_json, (
                f"URL leaked to LLM in {platform!r} channel: {result_json}"
            )
            assert CORRECT_OAUTH_URL not in result_json

        # For markdown channels, the URL is in `markdown_link` but
        # framed as a pre-built link with a "verbatim" instruction.
        # The LLM should embed the link as-is, not retype it.
        if platform in ("open_webui", "webui", ""):
            result = json.loads(result_json)
            assert "markdown_link" in result
            assert "VERBATIM" in result["_instruction"]


# ---------------------------------------------------------------------------
# Registry / toolset registration
# ---------------------------------------------------------------------------

class TestRegistry:
    def test_tool_is_registered(self):
        from tools.registry import registry
        assert "send_oauth_url" in registry._tools

    def test_tool_is_in_oauth_toolset(self):
        from tools.registry import registry
        entry = registry._tools["send_oauth_url"]
        assert entry.toolset == "oauth"

    def test_oauth_toolset_is_included_in_messaging(self):
        """The `messaging` toolset pulls in `oauth` so Telegram/Slack/etc. all get it."""
        from toolsets import TOOLSETS
        assert "oauth" in TOOLSETS["messaging"].get("includes", [])
        assert "send_oauth_url" in TOOLSETS["oauth"]["tools"]

    def test_send_oauth_url_in_hermes_core_tools(self):
        """Each platform's toolset (hermes-telegram, hermes-discord, etc.) is
        built from _HERMES_CORE_TOOLS, so the tool must be in that list to
        actually reach the LLM via any platform adapter."""
        from toolsets import TOOLSETS, resolve_toolset
        # The hermes-telegram platform toolset is the canonical "personal assistant
        # on Telegram" — if send_oauth_url is reachable from there, every other
        # platform toolset (which also derives from _HERMES_CORE_TOOLS) has it too.
        resolved = resolve_toolset("hermes-telegram")
        assert "send_oauth_url" in resolved, (
            f"send_oauth_url not in hermes-telegram toolset ({len(resolved)} tools) — "
            "make sure it is in _HERMES_CORE_TOOLS in toolsets.py"
        )
