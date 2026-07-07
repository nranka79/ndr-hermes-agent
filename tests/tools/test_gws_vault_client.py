"""Tests for tools/gws_vault_client.py — Unix-socket JSON-line protocol.

The vault client speaks a custom newline-delimited JSON protocol over a
Unix domain socket to the gws-vault-server daemon. Each test spins up a
stub server (mirroring the daemon's op semantics) on a temp socket and
exercises the client end-to-end.

Run with: scripts/run_tests.sh tests/tools/test_gws_vault_client.py
"""

from __future__ import annotations

import json
import os
import socket
import socketserver
import threading
import time
from unittest.mock import patch

import pytest

from tools import gws_vault_client as vault


# ── Stub vault server (mirrors gws-vault-server semantics) ──────────────────

class _StubHandler(socketserver.StreamRequestHandler):
    """Minimal gws-vault-server stub. One JSON line in, one JSON line out."""

    stored_tokens: dict = {}  # (uid, svc) -> token_json str
    valid_secret: str = "test-secret"

    def handle(self):
        try:
            line = self.rfile.readline()
            if not line:
                return
            req = json.loads(line.decode("utf-8"))
            resp = self._dispatch(req)
            self.wfile.write((json.dumps(resp) + "\n").encode("utf-8"))
            self.wfile.flush()
        except Exception as exc:
            try:
                self.wfile.write(
                    (json.dumps({"ok": False, "error": str(exc)}) + "\n").encode()
                )
            except Exception:
                pass

    def _dispatch(self, req: dict) -> dict:
        op = req.get("op", "")
        uid = str(req.get("user_id") or req.get("telegram_id", "")).strip()
        svc = str(req.get("service", "")).strip().lower()

        if op in ("get", "has_token", "delete", "set", "list_services"):
            if not uid:
                return {"ok": False, "error": "Invalid or missing user_id"}
            if op in ("get", "has_token", "delete", "set"):
                if not svc or not (svc[0].isalpha() and svc[0].isascii()
                                   and all(c.isalnum() or c == "-" for c in svc)):
                    return {"ok": False, "error": f"Invalid service name: {svc!r}"}

        if op == "resolve":
            iv = str(req.get("identity_value", "")).strip()
            if not iv:
                return {"ok": False, "error": "identity_value is required"}
            return {"ok": True, "user_id": iv}

        if op == "get":
            sess = str(req.get("session_uid", "")).strip()
            if not sess or sess != uid:
                return {"ok": False, "error": "Unauthorized: session user does not match"}
            key = (uid, svc)
            if key not in self.stored_tokens:
                return {"ok": False, "error": f"No {svc} token for user {uid}. Authorize first.",
                        "needs_auth": True}
            return {"ok": True, "token_json": self.stored_tokens[key]}

        if op == "set":
            if req.get("vault_secret") != self.valid_secret:
                return {"ok": False, "error": "Unauthorized: invalid vault secret"}
            tok = req.get("token_json", "")
            if not tok:
                return {"ok": False, "error": "token_json is required"}
            try:
                json.loads(tok)
            except json.JSONDecodeError as e:
                return {"ok": False, "error": f"Invalid token_json: {e}"}
            self.stored_tokens[(uid, svc)] = tok
            return {"ok": True}

        if op == "has_token":
            if req.get("vault_secret") != self.valid_secret:
                sess = str(req.get("session_uid", "")).strip()
                if not sess or sess != uid:
                    return {"ok": False, "error": "Unauthorized"}
            return {"ok": True, "has_token": (uid, svc) in self.stored_tokens}

        if op == "delete":
            if req.get("vault_secret") != self.valid_secret:
                return {"ok": False, "error": "Unauthorized: invalid vault secret"}
            key = (uid, svc)
            deleted = self.stored_tokens.pop(key, None) is not None
            return {"ok": True, "deleted": deleted}

        if op == "list_services":
            sess = str(req.get("session_uid", "")).strip()
            if not sess or sess != uid:
                return {"ok": False, "error": "Unauthorized"}
            return {"ok": True, "services": sorted({s for (u, s) in self.stored_tokens if u == uid})}

        return {"ok": False, "error": f"Unknown operation: {op!r}"}


class _StubUnixServer(socketserver.UnixStreamServer):
    address_family = socket.AF_UNIX


@pytest.fixture
def stub_vault(tmp_path, monkeypatch):
    """Spin up a stub vault on a temp Unix socket for the duration of one test."""
    sock_path = str(tmp_path / "vault.sock")
    _StubHandler.stored_tokens = {}
    _StubHandler.valid_secret = "test-secret"
    server = _StubUnixServer(sock_path, _StubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    deadline = time.time() + 1.0
    while time.time() < deadline:
        if os.path.exists(sock_path):
            break
        time.sleep(0.01)
    monkeypatch.setattr(vault, "VAULT_SOCKET", sock_path)
    monkeypatch.setattr(vault, "VAULT_SECRET", "test-secret")
    try:
        yield sock_path
    finally:
        server.shutdown()
        server.server_close()
        if os.path.exists(sock_path):
            os.unlink(sock_path)


# ── get_token ───────────────────────────────────────────────────────────────

class TestGetToken:
    def test_returns_stored_json(self, stub_vault):
        _StubHandler.stored_tokens[("7449813913", "google-gmail")] = json.dumps(
            {"token": "ya29.x", "refresh_token": "rt-1"}
        )
        out = vault.get_token("7449813913", "google-gmail")
        parsed = json.loads(out)
        assert parsed["refresh_token"] == "rt-1"
        assert parsed["token"] == "ya29.x"

    def test_no_token_raises_VaultNoTokenError(self, stub_vault):
        with pytest.raises(vault.VaultNoTokenError) as ei:
            vault.get_token("u", "google-gmail")
        assert ei.value.needs_auth is True

    def test_session_mismatch_raises_VaultUnauthorizedError(self, stub_vault):
        _StubHandler.stored_tokens[("u1", "google-gmail")] = "{}"
        with pytest.raises(vault.VaultUnauthorizedError):
            vault.get_token("u1", "google-gmail", session_uid="attacker")


# ── set_token ───────────────────────────────────────────────────────────────

class TestSetToken:
    def test_requires_secret(self, stub_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SECRET", "")
        with pytest.raises(vault.VaultUnauthorizedError):
            vault.set_token("u", "google-gmail", '{"x":1}')

    def test_set_get_roundtrip(self, stub_vault):
        token = json.dumps({"token": "ya29.new", "refresh_token": "rt-new"})
        vault.set_token("u1", "google-gmail", token)
        out = json.loads(vault.get_token("u1", "google-gmail"))
        assert out["refresh_token"] == "rt-new"


# ── has_token ───────────────────────────────────────────────────────────────

class TestHasToken:
    def test_false_when_missing(self, stub_vault):
        assert vault.has_token("u", "google-gmail") is False

    def test_true_when_present(self, stub_vault):
        _StubHandler.stored_tokens[("u", "google-gmail")] = "{}"
        assert vault.has_token("u", "google-gmail") is True


# ── delete_token ────────────────────────────────────────────────────────────

class TestDeleteToken:
    def test_returns_False_when_missing(self, stub_vault):
        assert vault.delete_token("u", "google-gmail") is False

    def test_returns_True_when_present_and_removes(self, stub_vault):
        _StubHandler.stored_tokens[("u", "google-gmail")] = "{}"
        assert vault.delete_token("u", "google-gmail") is True
        assert vault.has_token("u", "google-gmail") is False


# ── list_services ───────────────────────────────────────────────────────────

class TestListServices:
    def test_returns_only_callers_services(self, stub_vault):
        _StubHandler.stored_tokens.update({
            ("u1", "google-gmail"): "{}",
            ("u1", "google-ahfl"): "{}",
            ("u2", "google-gmail"): "{}",
        })
        result = vault.list_services("u1")
        assert set(result) == {"google-gmail", "google-ahfl"}


# ── get_access_token ────────────────────────────────────────────────────────

class TestGetAccessToken:
    def test_returns_parsed_dict(self, stub_vault):
        _StubHandler.stored_tokens[("7449813913", "google-gmail")] = json.dumps(
            {"token": "ya29.x", "refresh_token": "rt", "scopes": ["gmail"]}
        )
        out = vault.get_access_token("7449813913", "google-gmail")
        assert isinstance(out, dict)
        assert out["token"] == "ya29.x"
        assert out["refresh_token"] == "rt"
        assert out["scopes"] == ["gmail"]


# ── resolve ─────────────────────────────────────────────────────────────────

class TestResolve:
    def test_returns_user_id(self, stub_vault):
        assert vault.resolve("telegram", "1234") == "1234"


# ── Unreachable socket ──────────────────────────────────────────────────────

class TestUnreachableSocket:
    def test_clear_error(self, monkeypatch, tmp_path):
        monkeypatch.setattr(vault, "VAULT_SOCKET", str(tmp_path / "no-such.sock"))
        with pytest.raises(vault.VaultError) as ei:
            vault.get_token("u", "google-gmail")
        assert "no-such.sock" in str(ei.value)
