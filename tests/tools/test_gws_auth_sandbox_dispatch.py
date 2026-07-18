"""Tests for tools.gws_auth.load_credentials()'s sandboxed/trusted dispatch
(2026-07-18 vault impersonation fix).

Core property under test: when HERMES_RPC_SOCKET is present (sandboxed
execute_code context), load_credentials() must NEVER touch
tools.gws_vault_client directly -- it must go through the gws_fetch_token
RPC tool instead, which the sandbox reaches via the auto-generated
hermes_tools module. Outside the sandbox, behavior is unchanged: it calls
_load_credentials_direct(), which talks to the vault directly.
"""

import json
import sys
import types

import pytest

from google.oauth2.credentials import Credentials


def _fake_creds_info():
    # Minimal shape Credentials.from_authorized_user_info() accepts.
    return {
        "refresh_token": "rt",
        "client_id": "cid",
        "client_secret": "csecret",
        "token": "at",
    }


@pytest.fixture(autouse=True)
def _clear_rpc_env(monkeypatch):
    monkeypatch.delenv("HERMES_RPC_SOCKET", raising=False)


class TestNonSandboxedDispatch:
    """Outside the sandbox: unchanged direct-vault behavior."""

    def test_calls_load_credentials_direct(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.delenv("HERMES_RPC_SOCKET", raising=False)
        called = {}

        def fake_direct(tid, service_name):
            called["tid"] = tid
            called["service_name"] = service_name
            return Credentials.from_authorized_user_info(_fake_creds_info())

        monkeypatch.setattr(gws_auth, "_load_credentials_direct", fake_direct)
        creds = gws_auth.load_credentials("8654428154", "google-draas")

        assert called == {"tid": "8654428154", "service_name": "google-draas"}
        assert isinstance(creds, Credentials)


class TestSandboxedDispatch:
    """Inside the sandbox (HERMES_RPC_SOCKET set): must route through RPC,
    never touch tools.gws_vault_client directly."""

    def _install_fake_hermes_tools(self, monkeypatch, response):
        fake = types.ModuleType("hermes_tools")
        calls = []

        def gws_fetch_token(service_name="google"):
            calls.append(service_name)
            return response

        fake.gws_fetch_token = gws_fetch_token
        monkeypatch.setitem(sys.modules, "hermes_tools", fake)
        return calls

    def test_sandboxed_never_calls_load_credentials_direct(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.setenv("HERMES_RPC_SOCKET", "/tmp/fake.sock")
        self._install_fake_hermes_tools(
            monkeypatch, {"token_json": json.dumps(_fake_creds_info())}
        )

        def fail_if_called(*a, **k):
            raise AssertionError(
                "load_credentials must NOT call _load_credentials_direct "
                "(and therefore must never touch the vault directly) when "
                "HERMES_RPC_SOCKET is set."
            )

        monkeypatch.setattr(gws_auth, "_load_credentials_direct", fail_if_called)
        creds = gws_auth.load_credentials("8654428154", "google-draas")
        assert isinstance(creds, Credentials)

    def test_sandboxed_routes_through_rpc_tool(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.setenv("HERMES_RPC_SOCKET", "/tmp/fake.sock")
        calls = self._install_fake_hermes_tools(
            monkeypatch, {"token_json": json.dumps(_fake_creds_info())}
        )
        gws_auth.load_credentials("8654428154", "google-draas")
        assert calls == ["google-draas"]

    def test_sandboxed_caller_supplied_telegram_id_never_reaches_rpc_call(self, monkeypatch):
        """The RPC stub's signature is service_name only -- a caller-supplied
        telegram_id must never be threaded into the RPC request, since the
        whole point is that identity is resolved server-side, not by
        whatever id this process (sandboxed, untrusted) happens to pass."""
        import tools.gws_auth as gws_auth

        monkeypatch.setenv("HERMES_RPC_SOCKET", "/tmp/fake.sock")
        fake = types.ModuleType("hermes_tools")
        received_kwargs = {}

        def gws_fetch_token(**kwargs):
            received_kwargs.update(kwargs)
            return {"token_json": json.dumps(_fake_creds_info())}

        fake.gws_fetch_token = gws_fetch_token
        monkeypatch.setitem(sys.modules, "hermes_tools", fake)

        gws_auth.load_credentials("some-other-user-id", "google-draas")
        assert "telegram_id" not in received_kwargs
        assert "user_id" not in received_kwargs
        assert "session_uid" not in received_kwargs
        assert received_kwargs == {"service_name": "google-draas"}

    def test_sandboxed_needs_auth_error_raises_file_not_found(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.setenv("HERMES_RPC_SOCKET", "/tmp/fake.sock")
        self._install_fake_hermes_tools(
            monkeypatch, {"error": "No google-draas token for this user.", "needs_auth": True}
        )
        with pytest.raises(FileNotFoundError):
            gws_auth.load_credentials("8654428154", "google-draas")

    def test_sandboxed_other_error_raises_runtime_error(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.setenv("HERMES_RPC_SOCKET", "/tmp/fake.sock")
        self._install_fake_hermes_tools(monkeypatch, {"error": "vault unreachable"})
        with pytest.raises(RuntimeError):
            gws_auth.load_credentials("8654428154", "google-draas")


class TestBuildServiceUnaffectedBySandboxDetail:
    """build_service()'s own caller-facing contract is unchanged either way
    -- it just delegates to load_credentials()."""

    def test_build_service_still_ignores_mismatched_caller_telegram_id(self, monkeypatch):
        import tools.gws_auth as gws_auth

        monkeypatch.delenv("HERMES_RPC_SOCKET", raising=False)
        monkeypatch.setattr(gws_auth, "_current_telegram_id", lambda: "REAL_SESSION_ID")
        captured = {}

        def fake_load(tid, service_name):
            captured["tid"] = tid
            return Credentials.from_authorized_user_info(_fake_creds_info())

        monkeypatch.setattr(gws_auth, "load_credentials", fake_load)
        monkeypatch.setattr(gws_auth, "build", lambda api, version, credentials: "built-service")

        result = gws_auth.build_service("gmail", "v1", telegram_id="SOMEONE_ELSE")
        assert result == "built-service"
        assert captured["tid"] == "REAL_SESSION_ID"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
