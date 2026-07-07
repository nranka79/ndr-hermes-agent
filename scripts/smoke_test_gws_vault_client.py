#!/usr/bin/env python3
"""Standalone smoke test for tools/gws_vault_client.py — no pytest required.

Exercises the same logic the pytest suite covers (Unix-socket transport,
HTTP fallback, auth header, error mapping, CRUD), using only the stdlib.
Run: python3 scripts/smoke_test_gws_vault_client.py
"""
from __future__ import annotations

import http.server
import json
import os
import socket
import socketserver
import sys
import tempfile
import threading
import time
from unittest.mock import patch

# Ensure repo root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import gws_vault_client as vault

PASSED = 0
FAILED = 0
ERRORS: list[str] = []


def check(label: str, cond: bool, detail: str = ""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  ✓ {label}")
    else:
        FAILED += 1
        msg = f"  ✗ {label}" + (f" — {detail}" if detail else "")
        print(msg)
        ERRORS.append(msg)


# ── Stub server (shared between socket and HTTP tests) ──────────────────────

class StubHandler(http.server.BaseHTTPRequestHandler):
    requests: list = []
    response_status: int = 200
    response_body: bytes = b"{}"

    def log_message(self, *_a, **_k):
        return

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length) if length else b""
        self.requests.append({"method": "POST", "path": self.path,
                              "headers": dict(self.headers), "body": body})
        self._send()

    def do_GET(self):
        self.requests.append({"method": "GET", "path": self.path,
                              "headers": dict(self.headers), "body": b""})
        self._send()

    def _send(self):
        self.send_response(self.response_status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(self.response_body)))
        self.end_headers()
        self.wfile.write(self.response_body)


class UnixVaultServer(socketserver.UnixStreamServer):
    address_family = socket.AF_UNIX


def start_unix_vault(sock_path: str):
    StubHandler.requests = []
    StubHandler.response_status = 200
    StubHandler.response_body = b"{}"
    server = UnixVaultServer(sock_path, StubHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    deadline = time.time() + 1.0
    while time.time() < deadline:
        if os.path.exists(sock_path):
            break
        time.sleep(0.01)
    return server


def start_http_vault():
    StubHandler.requests = []
    StubHandler.response_status = 200
    StubHandler.response_body = b"{}"
    server = http.server.HTTPServer(("127.0.0.1", 0), StubHandler)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    return server, port


# ── Tests ──────────────────────────────────────────────────────────────────

def test_dispatch_socket():
    print("\n[d1] socket is used when GWS_VAULT_SOCKET is set + file exists")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "vault.sock")
        server = start_unix_vault(sock)
        try:
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "s"):
                StubHandler.response_body = json.dumps({"ok": True}).encode()
                result = vault.get_access_token("u", "svc")
                check("returns parsed body", result == {"ok": True})
                check("client hit /v1/token", StubHandler.requests[0]["path"] == "/v1/token")
                check("client sent auth header",
                      StubHandler.requests[0]["headers"]["X-Vault-Secret"] == "s")
        finally:
            server.shutdown()
            server.server_close()


def test_dispatch_http_fallback():
    print("\n[d2] HTTP is used when GWS_VAULT_SOCKET is unset")
    server, port = start_http_vault()
    try:
        with patch.object(vault, "VAULT_URL", f"http://127.0.0.1:{port}"), \
             patch.object(vault, "VAULT_SOCKET", ""), \
             patch.object(vault, "VAULT_SECRET", "x"):
            StubHandler.response_body = json.dumps({"ok": True}).encode()
            result = vault.get_access_token("u", "svc")
            check("HTTP transport returned parsed body", result == {"ok": True})
            check("request landed on /v1/token",
                  StubHandler.requests[0]["path"] == "/v1/token")
    finally:
        server.shutdown()
        server.server_close()


def test_dispatch_http_fallback_when_socket_missing():
    print("\n[d3] HTTP fallback when GWS_VAULT_SOCKET path doesn't exist")
    server, port = start_http_vault()
    try:
        with patch.object(vault, "VAULT_URL", f"http://127.0.0.1:{port}"), \
             patch.object(vault, "VAULT_SOCKET", "/run/gws-vault/does-not-exist.sock"), \
             patch.object(vault, "VAULT_SECRET", "x"):
            StubHandler.response_body = json.dumps({"ok": True}).encode()
            result = vault.get_access_token("u", "svc")
            check("fell back to HTTP when socket file missing",
                  result == {"ok": True} and StubHandler.requests[0]["path"] == "/v1/token")
    finally:
        server.shutdown()
        server.server_close()


def test_error_mapping_socket():
    print("\n[e1] error mapping (socket path)")
    cases = [
        (401, vault.VaultUnauthorizedError, b'{"detail":"bad secret"}'),
        (403, vault.VaultUnauthorizedError, b'{"detail":"forbidden"}'),
        (404, vault.VaultNoTokenError, b'{"detail":"token not found"}'),
        (500, vault.VaultError, b'{"detail":"server boom"}'),
    ]
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "vault.sock")
        server = start_unix_vault(sock)
        try:
            for status, exc_type, body in cases:
                with patch.object(vault, "VAULT_SOCKET", sock), \
                     patch.object(vault, "VAULT_SECRET", "x"):
                    StubHandler.response_status = status
                    StubHandler.response_body = body
                    try:
                        vault.get_access_token("u", "s")
                        check(f"status {status} raises {exc_type.__name__}", False, "no exception")
                    except exc_type:
                        check(f"status {status} → {exc_type.__name__}", True)
                    except Exception as e:
                        check(f"status {status} → {exc_type.__name__}", False,
                              f"got {type(e).__name__}: {e}")
        finally:
            server.shutdown()
            server.server_close()


def test_error_mapping_http():
    print("\n[e2] error mapping (HTTP path)")
    cases = [
        (401, vault.VaultUnauthorizedError),
        (403, vault.VaultUnauthorizedError),
        (404, vault.VaultNoTokenError),
        (500, vault.VaultError),
    ]
    server, port = start_http_vault()
    try:
        for status, exc_type in cases:
            with patch.object(vault, "VAULT_URL", f"http://127.0.0.1:{port}"), \
                 patch.object(vault, "VAULT_SOCKET", ""), \
                 patch.object(vault, "VAULT_SECRET", "x"):
                StubHandler.response_status = status
                StubHandler.response_body = json.dumps({"detail": f"err {status}"}).encode()
                try:
                    vault.get_access_token("u", "s")
                    check(f"HTTP {status} raises {exc_type.__name__}", False, "no exception")
                except exc_type:
                    check(f"HTTP {status} → {exc_type.__name__}", True)
                except Exception as e:
                    check(f"HTTP {status} → {exc_type.__name__}", False,
                          f"got {type(e).__name__}: {e}")
    finally:
        server.shutdown()
        server.server_close()


def test_end_to_end_crud():
    print("\n[c1] end-to-end CRUD over Unix socket")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "vault.sock")
        server = start_unix_vault(sock)
        try:
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "x"):

                # get_token
                StubHandler.response_body = json.dumps(
                    {"refresh_token": "rt-1", "client_id": "cid"}).encode()
                result = json.loads(vault.get_token("7449813913", "gws:ndr@draas.com"))
                check("get_token returns refresh_token", result["refresh_token"] == "rt-1")
                last = StubHandler.requests[-1]
                body = json.loads(last["body"])
                check("get_token sent correct vault_user_id",
                      body["vault_user_id"] == "7449813913")
                check("get_token sent correct service",
                      body["service"] == "gws:ndr@draas.com")

                # set_token
                StubHandler.requests = []
                StubHandler.response_body = b"{}"
                vault.set_token("u", "svc", json.dumps({"refresh_token": "rt-2"}))
                last = StubHandler.requests[-1]
                check("set_token hit /v1/token/store",
                      last["path"] == "/v1/token/store")
                body = json.loads(last["body"])
                check("set_token wraps body under 'token' key",
                      body["token"] == {"refresh_token": "rt-2"})

                # has_token True
                StubHandler.requests = []
                StubHandler.response_status = 200
                StubHandler.response_body = b"{}"
                check("has_token returns True on 200", vault.has_token("u", "s") is True)

                # has_token False
                StubHandler.response_status = 404
                StubHandler.response_body = json.dumps({"detail": "no"}).encode()
                check("has_token returns False on 404", vault.has_token("u", "s") is False)

                # list_services
                StubHandler.requests = []
                StubHandler.response_status = 200
                StubHandler.response_body = json.dumps({
                    "services": ["s1", "s2"],
                }).encode()
                check("list_services returns the service list",
                      vault.list_services("u") == ["s1", "s2"])
                check("list_services uses GET", StubHandler.requests[-1]["method"] == "GET")
                check("list_services path is /v1/users/u/services",
                      StubHandler.requests[-1]["path"] == "/v1/users/u/services")

                # delete_token True
                StubHandler.response_status = 200
                StubHandler.response_body = b"{}"
                check("delete_token returns True on 200", vault.delete_token("u", "s") is True)

                # delete_token False
                StubHandler.response_status = 404
                StubHandler.response_body = json.dumps({"detail": "no"}).encode()
                check("delete_token returns False on 404", vault.delete_token("u", "s") is False)
        finally:
            server.shutdown()
            server.server_close()


def test_unreachable_via_socket():
    print("\n[u1] unreachable socket → clear error (falls back to HTTP)")
    # VAULT_URL points at a port nothing's listening on
    with patch.object(vault, "VAULT_URL", "http://127.0.0.1:1"), \
         patch.object(vault, "VAULT_SOCKET", "/tmp/no-such-vault.sock"), \
         patch.object(vault, "VAULT_SECRET", "x"):
        try:
            vault.get_access_token("u", "s")
            check("unreachable raises VaultError", False, "no exception raised")
        except vault.VaultError as e:
            check("unreachable raises VaultError", True)
            check("error message mentions vault location",
                  "127.0.0.1:1" in str(e), detail=str(e))


def main():
    test_dispatch_socket()
    test_dispatch_http_fallback()
    test_dispatch_http_fallback_when_socket_missing()
    test_error_mapping_socket()
    test_error_mapping_http()
    test_end_to_end_crud()
    test_unreachable_via_socket()
    print(f"\n{'='*50}")
    print(f"  {PASSED} passed, {FAILED} failed")
    if ERRORS:
        print("\nFailures:")
        for e in ERRORS:
            print(e)
    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    main()
