"""Tests for the gws_fetch_token RPC tool -- the sandbox's only path to a
Google Workspace OAuth token after the 2026-07-18 vault impersonation fix.

The core security property under test: this tool's schema has NO user/
telegram-id parameter, and its handler resolves identity exclusively via
tools.gws_auth._current_telegram_id() (the trusted session context) --
there is no argument path that lets a caller request a different user's
token.
"""

import json

import pytest

from tools.gws_fetch_token_tool import GWS_FETCH_TOKEN_SCHEMA, gws_fetch_token_tool


class TestSchemaHasNoIdentityParameter:
    """The actual security property: nothing in the schema lets a caller
    claim to be a different user."""

    def test_no_user_id_parameter(self):
        props = GWS_FETCH_TOKEN_SCHEMA["parameters"]["properties"]
        for forbidden in ("user_id", "telegram_id", "session_uid", "uid"):
            assert forbidden not in props, (
                f"gws_fetch_token schema must never accept {forbidden!r} -- "
                "identity is resolved server-side only."
            )

    def test_only_service_name_is_a_parameter(self):
        props = GWS_FETCH_TOKEN_SCHEMA["parameters"]["properties"]
        assert set(props.keys()) == {"service_name"}

    def test_registered_under_oauth_toolset(self):
        from tools.registry import registry
        import tools.gws_fetch_token_tool  # noqa: F401 -- ensure registered
        entry = registry.get_entry("gws_fetch_token")
        assert entry is not None
        assert entry.toolset == "oauth"


class _FakeCreds:
    def __init__(self, payload="fake-token-json"):
        self._payload = payload

    def to_json(self):
        return self._payload


class TestHandlerResolvesOwnSessionOnly:
    def test_success_returns_token_json(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.setattr(gws_auth, "_current_telegram_id", lambda: "1234567890")
        monkeypatch.setattr(
            gws_auth, "_load_credentials_direct",
            lambda tid, service_name: _FakeCreds(f"token-for-{tid}-{service_name}"),
        )

        result = json.loads(gws_fetch_token_tool({"service_name": "google-draas"}))
        assert result == {"token_json": "token-for-1234567890-google-draas"}

    def test_defaults_service_name_to_google(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.setattr(gws_auth, "_current_telegram_id", lambda: "1234567890")
        captured = {}

        def fake_load(tid, service_name):
            captured["service_name"] = service_name
            return _FakeCreds()

        monkeypatch.setattr(gws_auth, "_load_credentials_direct", fake_load)
        gws_fetch_token_tool({})
        assert captured["service_name"] == "google"

    def test_caller_cannot_smuggle_identity_via_args(self, monkeypatch):
        """Even if a caller stuffs a user_id/telegram_id into args (there is
        no schema field for it, but nothing stops raw RPC bytes from
        including one), the handler must never read it -- only
        _current_telegram_id() decides identity."""
        import tools.gws_auth as gws_auth

        monkeypatch.setattr(gws_auth, "_current_telegram_id", lambda: "REAL_SESSION_USER")
        captured = {}

        def fake_load(tid, service_name):
            captured["tid"] = tid
            return _FakeCreds()

        monkeypatch.setattr(gws_auth, "_load_credentials_direct", fake_load)
        gws_fetch_token_tool({
            "service_name": "google-draas",
            "user_id": "someone-else@draas.com",
            "telegram_id": "999999999",
        })
        assert captured["tid"] == "REAL_SESSION_USER"

    def test_no_session_context_returns_error(self, monkeypatch):
        import tools.gws_auth as gws_auth

        def raise_no_session():
            raise ValueError("No session user context (HERMES_SESSION_USER_ID not set).")

        monkeypatch.setattr(gws_auth, "_current_telegram_id", raise_no_session)
        result = json.loads(gws_fetch_token_tool({"service_name": "google"}))
        assert "error" in result

    def test_no_token_returns_needs_auth(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.setattr(gws_auth, "_current_telegram_id", lambda: "1234567890")

        def raise_not_found(tid, service_name):
            raise FileNotFoundError(f"No {service_name} token for user {tid}.")

        monkeypatch.setattr(gws_auth, "_load_credentials_direct", raise_not_found)
        result = json.loads(gws_fetch_token_tool({"service_name": "google-draas"}))
        assert result.get("needs_auth") is True
        assert "error" in result

    def test_unexpected_error_is_reported_not_raised(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.setattr(gws_auth, "_current_telegram_id", lambda: "1234567890")

        def raise_weird(tid, service_name):
            raise RuntimeError("vault socket hiccup")

        monkeypatch.setattr(gws_auth, "_load_credentials_direct", raise_weird)
        result = json.loads(gws_fetch_token_tool({"service_name": "google"}))
        assert "error" in result
        assert "vault socket hiccup" in result["error"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
