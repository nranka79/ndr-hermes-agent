"""Tests for tools/gws_vault_client.py — Unix-socket and HTTP backends.

The vault client supports two transports:
  * Unix socket (preferred when GWS_VAULT_SOCKET is set and the file exists)
  * HTTP over TCP (fallback for dev / CI / anywhere the socket isn't mounted)

These tests exercise both paths end-to-end with a tiny stub server, plus
the dispatch / error-mapping logic in between.
"""

from __future__ import annotations

import http.server
import json
import os
import socket
import socketserver
import threading
import time
from unittest.mock import patch

import pytest

from tools import gws_vault_client as vault


# ── Stub vault server (Unix-socket) ──────────────────────────────────────────

class _StubHandler(http.server.BaseHTTPRequestHandler):
    """Trivial vault stub. Records every request in a class-level list so
    tests can assert on method / path / headers / body."""

    requests: list = []  # populated by setUp
    response_status: int = 200
    response_body: bytes = b"{}"

    def log_message(self, *_args, **_kwargs):  # silence stderr noise
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        self.requests.append({
            "method": "POST",
            "path": self.path,
            "headers": dict(self.headers),
            "body": body,
        })
        self._send()

    def do_GET(self):
        self.requests.append({
            "method": "GET",
            "path": self.path,
            "headers": dict(self.headers),
            "body": b"",
        })
        self._send()

    def _send(self):
        self.send_response(self.response_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(self.response_body)))
        self.end_headers()
        self.wfile.write(self.response_body)


class _UnixSocketServer(socketserver.UnixStreamServer):
    address_family = socket.AF_UNIX


@pytest.fixture
def socket_vault(tmp_path):
    """Spin up a stub vault listening on a temp Unix socket.

    Yields the socket path. The stub is reachable on every call the
    client makes; tests configure its response via StubHandler class
    attributes and inspect StubHandler.requests for the call log.
    """
    sock_path = str(tmp_path / "vault.sock")
    _StubHandler.requests = []
    _StubHandler.response_status = 200
    _StubHandler.response_body = b"{}"
    server = _UnixSocketServer(sock_path, _StubHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Tiny pause so the socket is actually accepting connections by the
    # time the test calls the client. serve_forever is non-blocking; the
    # bind happens synchronously but the listen() / accept() loop is in
    # the thread.
    deadline = time.time() + 1.0
    while time.time() < deadline:
        if os.path.exists(sock_path):
            break
        time.sleep(0.01)
    try:
        yield sock_path
    finally:
        server.shutdown()
        server.server_close()
        if os.path.exists(sock_path):
            os.unlink(sock_path)


@pytest.fixture
def http_vault(monkeypatch):
    """Spin up a stub vault on a real TCP port (for the HTTP-fallback tests)."""
    from http.server import HTTPServer
    _StubHandler.requests = []
    _StubHandler.response_status = 200
    _StubHandler.response_body = b"{}"
    server = HTTPServer(("127.0.0.1", 0), _StubHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setattr(vault, "VAULT_URL", f"http://127.0.0.1:{port}")
    try:
        yield port
    finally:
        server.shutdown()
        server.server_close()


# ── Dispatch tests ──────────────────────────────────────────────────────────

class TestDispatch:
    def test_socket_used_when_set_and_present(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "test-secret")
        _StubHandler.response_body = json.dumps({"ok": True}).encode()

        result = vault.get_access_token("user1", "svc")

        assert result == {"ok": True}
        assert len(_StubHandler.requests) == 1
        assert _StubHandler.requests[0]["method"] == "POST"
        assert _StubHandler.requests[0]["path"] == "/v1/token"

    def test_http_used_when_socket_unset(self, http_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", "")
        monkeypatch.setattr(vault, "VAULT_SECRET", "test-secret")
        _StubHandler.response_body = json.dumps({"ok": True}).encode()

        result = vault.get_access_token("user1", "svc")

        assert result == {"ok": True}
        assert _StubHandler.requests[0]["path"] == "/v1/token"

    def test_http_fallback_when_socket_path_missing(self, http_vault, monkeypatch):
        """Env var set but the file doesn't exist → fall back to HTTP."""
        monkeypatch.setattr(vault, "VAULT_SOCKET", "/run/gws-vault/does-not-exist.sock")
        monkeypatch.setattr(vault, "VAULT_SECRET", "test-secret")
        _StubHandler.response_body = json.dumps({"ok": True}).encode()

        result = vault.get_access_token("user1", "svc")

        assert result == {"ok": True}
        # HTTP path, not socket path
        assert _StubHandler.requests[0]["path"].startswith("/v1/")


# ── Auth header is sent on both paths ───────────────────────────────────────

class TestAuthHeader:
    def test_socket_path_sends_secret(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "super-secret-value")
        _StubHandler.response_body = b"{}"

        vault.get_access_token("u", "s")

        assert _StubHandler.requests[0]["headers"]["X-Vault-Secret"] == "super-secret-value"

    def test_http_path_sends_secret(self, http_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", "")
        monkeypatch.setattr(vault, "VAULT_SECRET", "super-secret-value")
        _StubHandler.response_body = b"{}"

        vault.get_access_token("u", "s")

        assert _StubHandler.requests[0]["headers"]["X-Vault-Secret"] == "super-secret-value"


# ── Error mapping (shared between paths) ────────────────────────────────────

class TestErrorMapping:
    @pytest.mark.parametrize("status,exc_type", [
        (401, vault.VaultUnauthorizedError),
        (403, vault.VaultUnauthorizedError),
        (404, vault.VaultNoTokenError),
        (500, vault.VaultError),
    ])
    def test_socket_error_mapping(self, socket_vault, monkeypatch, status, exc_type):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_status = status
        _StubHandler.response_body = json.dumps({"detail": f"err {status}"}).encode()

        with pytest.raises(exc_type):
            vault.get_access_token("u", "s")

    @pytest.mark.parametrize("status,exc_type", [
        (401, vault.VaultUnauthorizedError),
        (403, vault.VaultUnauthorizedError),
        (404, vault.VaultNoTokenError),
        (500, vault.VaultError),
    ])
    def test_http_error_mapping(self, http_vault, monkeypatch, status, exc_type):
        monkeypatch.setattr(vault, "VAULT_SOCKET", "")
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_status = status
        _StubHandler.response_body = json.dumps({"detail": f"err {status}"}).encode()

        with pytest.raises(exc_type):
            vault.get_access_token("u", "s")


# ── End-to-end CRUD over the socket ─────────────────────────────────────────

class TestEndToEndOverSocket:
    def test_get_token_round_trip(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_body = json.dumps({
            "refresh_token": "rt-1",
            "client_id": "cid",
        }).encode()

        result = vault.get_token("7449813913", "gws:ndr@draas.com")
        parsed = json.loads(result)

        assert parsed["refresh_token"] == "rt-1"
        body = json.loads(_StubHandler.requests[0]["body"])
        assert body == {
            "vault_user_id": "7449813913",
            "service": "gws:ndr@draas.com",
        }

    def test_set_token_sends_token_object(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_body = b"{}"

        token = json.dumps({"refresh_token": "rt-2", "client_id": "cid"})
        vault.set_token("u", "svc", token)

        assert _StubHandler.requests[0]["path"] == "/v1/token/store"
        body = json.loads(_StubHandler.requests[0]["body"])
        assert body["vault_user_id"] == "u"
        assert body["service"] == "svc"
        assert body["token"] == {"refresh_token": "rt-2", "client_id": "cid"}

    def test_has_token_true_on_200(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_status = 200
        _StubHandler.response_body = b"{}"

        assert vault.has_token("u", "svc") is True

    def test_has_token_false_on_404(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_status = 404
        _StubHandler.response_body = json.dumps({"detail": "token not found"}).encode()

        assert vault.has_token("u", "svc") is False

    def test_delete_token_returns_true_on_200(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_status = 200
        _StubHandler.response_body = b"{}"

        assert vault.delete_token("u", "svc") is True

    def test_delete_token_returns_false_on_404(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_status = 404
        _StubHandler.response_body = json.dumps({"detail": "token not found"}).encode()

        assert vault.delete_token("u", "svc") is False

    def test_list_services_gets_parsed_services(self, socket_vault, monkeypatch):
        monkeypatch.setattr(vault, "VAULT_SOCKET", socket_vault)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")
        _StubHandler.response_body = json.dumps({
            "services": ["gws:ndr@draas.com", "gws:rnr@draas.com"],
        }).encode()

        result = vault.list_services("u")

        assert result == ["gws:ndr@draas.com", "gws:rnr@draas.com"]
        assert _StubHandler.requests[0]["method"] == "GET"
        assert _StubHandler.requests[0]["path"] == "/v1/users/u/services"


# ── Unreachable socket raises a clear error ─────────────────────────────────

class TestUnreachableSocket:
    def test_missing_socket_raises_with_path(self, tmp_path, monkeypatch):
        """Path is set but doesn't exist → falls back to HTTP (which will
        also fail with VAULT_URL default). At minimum the error should
        mention the vault URL/path, not silently succeed."""
        missing = str(tmp_path / "no-such.sock")
        # No socket_vault fixture → no HTTP server either, so HTTP will
        # fail to connect to the default VAULT_URL too.
        monkeypatch.setattr(vault, "VAULT_SOCKET", missing)
        monkeypatch.setattr(vault, "VAULT_SECRET", "x")

        with pytest.raises(vault.VaultError) as ei:
            vault.get_access_token("u", "s")

        # Falls back to HTTP → fails connecting to default URL
        assert "127.0.0.1:8000" in str(ei.value) or "Vault" in str(ei.value)
