#!/usr/bin/env python3
"""Standalone smoke test for tools/gws_vault_client.py — no pytest required.

Exercises the custom JSON-line Unix-socket protocol the gws-vault-server
implements. Run: python3 scripts/smoke_test_gws_vault_client.py
"""
from __future__ import annotations

import json
import os
import socket
import socketserver
import sys
import tempfile
import threading
import time
from unittest.mock import patch

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


# ── Stub vault server (mirrors gws-vault-server semantics) ──────────────────

class StubVaultHandler(socketserver.StreamRequestHandler):
    """Minimal gws-vault-server stub. Reads one JSON line, dispatches by `op`,
    writes one JSON line back."""

    # Server-side state (configured per test via class attributes).
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
            # No user_id / service required for resolve — only identity_*.
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
            # accepts session_uid OR vault_secret
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


class StubUnixServer(socketserver.UnixStreamServer):
    address_family = socket.AF_UNIX


def start_stub(sock_path: str):
    StubVaultHandler.stored_tokens = {}
    StubVaultHandler.valid_secret = "test-secret"
    server = StubUnixServer(sock_path, StubVaultHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    deadline = time.time() + 1.0
    while time.time() < deadline:
        if os.path.exists(sock_path):
            break
        time.sleep(0.01)
    return server


# ── Tests ──────────────────────────────────────────────────────────────────

def test_get_token_happy():
    print("\n[g1] get_token: returns stored JSON when session matches")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            StubVaultHandler.stored_tokens[("1000000001", "google-gmail")] = json.dumps(
                {"token": "ya29.x", "refresh_token": "rt-1"}
            )
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                out = vault.get_token("1000000001", "google-gmail")
                parsed = json.loads(out)
                check("returns refresh_token", parsed["refresh_token"] == "rt-1")
                check("returns access token", parsed["token"] == "ya29.x")
        finally:
            server.shutdown()
            server.server_close()


def test_get_token_no_token_raises_no_token_error():
    print("\n[g2] get_token: raises VaultNoTokenError when no token stored")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                try:
                    vault.get_token("u", "google-gmail")
                    check("raises VaultNoTokenError", False, "no exception")
                except vault.VaultNoTokenError as e:
                    check("raises VaultNoTokenError", True)
                    check("needs_auth flag set on the exception",
                          getattr(e, "needs_auth", False))
        finally:
            server.shutdown()
            server.server_close()


def test_get_token_session_mismatch_raises_unauthorized():
    print("\n[g3] get_token: cross-user read is rejected with VaultUnauthorizedError")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            StubVaultHandler.stored_tokens[("u1", "google-gmail")] = "{}"
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                # session_uid defaults to user_id when not passed — so pass a
                # mismatched one explicitly to simulate a cross-user attempt.
                try:
                    vault.get_token("u1", "google-gmail", session_uid="attacker")
                    check("raises VaultUnauthorizedError", False, "no exception")
                except vault.VaultUnauthorizedError:
                    check("raises VaultUnauthorizedError on session mismatch", True)
        finally:
            server.shutdown()
            server.server_close()


def test_set_requires_secret():
    print("\n[s1] set_token: requires GWS_VAULT_SECRET")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", ""):
                try:
                    vault.set_token("u", "google-gmail", '{"x":1}')
                    check("set without secret raises VaultUnauthorizedError", False, "no exc")
                except vault.VaultUnauthorizedError:
                    check("set without secret raises VaultUnauthorizedError", True)
        finally:
            server.shutdown()
            server.server_close()


def test_set_get_roundtrip():
    print("\n[s2] set + get round-trip with valid secret")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                token = json.dumps({"token": "ya29.new", "refresh_token": "rt-new"})
                vault.set_token("u1", "google-gmail", token)
                check("set succeeded", ("u1", "google-gmail") in StubVaultHandler.stored_tokens)
                out = vault.get_token("u1", "google-gmail")
                check("get returns what was set", json.loads(out)["refresh_token"] == "rt-new")
        finally:
            server.shutdown()
            server.server_close()


def test_has_token_self_check():
    print("\n[h1] has_token: True/False based on storage, self-check default")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                check("has_token False for missing", vault.has_token("u", "google-gmail") is False)
                StubVaultHandler.stored_tokens[("u", "google-gmail")] = "{}"
                check("has_token True for present", vault.has_token("u", "google-gmail") is True)
        finally:
            server.shutdown()
            server.server_close()


def test_has_token_admin_via_secret():
    print("\n[h2] has_token: GWS_VAULT_SECRET lets the caller check any user")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            StubVaultHandler.stored_tokens[("u1", "google-gmail")] = "{}"
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                check("admin can check another user", vault.has_token("u1", "google-gmail") is True)
        finally:
            server.shutdown()
            server.server_close()


def test_delete_returns_true_false():
    print("\n[d1] delete_token: True on present, False on missing")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                check("delete returns False when missing",
                      vault.delete_token("u", "google-gmail") is False)
                StubVaultHandler.stored_tokens[("u", "google-gmail")] = "{}"
                check("delete returns True when present",
                      vault.delete_token("u", "google-gmail") is True)
                check("delete actually removed it",
                      vault.has_token("u", "google-gmail") is False)
        finally:
            server.shutdown()
            server.server_close()


def test_list_services_self_check():
    print("\n[l1] list_services: returns sorted service list for the user")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            StubVaultHandler.stored_tokens.update({
                ("u1", "google-gmail"): "{}",
                ("u1", "google-ahfl"): "{}",
                ("u2", "google-gmail"): "{}",  # different user — should NOT appear
            })
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                result = vault.list_services("u1")
                check("list returns both services for u1",
                      set(result) == {"google-gmail", "google-ahfl"})
                check("list excludes other users' services",
                      "u2" not in result)
        finally:
            server.shutdown()
            server.server_close()


def test_resolve():
    print("\n[r1] resolve: returns the resolved user_id or None")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                # stub returns the user_id from the request
                check("resolve returns user_id when ok",
                      vault.resolve("telegram", "1234") == "1234")
        finally:
            server.shutdown()
            server.server_close()


def test_get_access_token_parses_token_json():
    print("\n[a1] get_access_token: returns parsed dict from stored token_json")
    with tempfile.TemporaryDirectory() as d:
        sock = os.path.join(d, "v.sock")
        server = start_stub(sock)
        try:
            StubVaultHandler.stored_tokens[("1000000001", "google-gmail")] = json.dumps(
                {"token": "ya29.x", "refresh_token": "rt", "scopes": ["gmail"]}
            )
            with patch.object(vault, "VAULT_SOCKET", sock), \
                 patch.object(vault, "VAULT_SECRET", "test-secret"):
                out = vault.get_access_token("1000000001", "google-gmail")
                check("returns dict", isinstance(out, dict))
                check("dict has token", out.get("token") == "ya29.x")
                check("dict has refresh_token", out.get("refresh_token") == "rt")
                check("dict has scopes", out.get("scopes") == ["gmail"])
        finally:
            server.shutdown()
            server.server_close()


def test_unreachable_socket_clear_error():
    print("\n[u1] unreachable socket → clear VaultError")
    with patch.object(vault, "VAULT_SOCKET", "/tmp/this-socket-does-not-exist.sock"), \
         patch.object(vault, "VAULT_SECRET", "x"):
        try:
            vault.get_token("u", "google-gmail")
            check("unreachable raises VaultError", False, "no exception")
        except vault.VaultError as e:
            check("unreachable raises VaultError", True)
            check("error mentions socket path", "this-socket-does-not-exist.sock" in str(e),
                  detail=str(e))


def main():
    test_get_token_happy()
    test_get_token_no_token_raises_no_token_error()
    test_get_token_session_mismatch_raises_unauthorized()
    test_set_requires_secret()
    test_set_get_roundtrip()
    test_has_token_self_check()
    test_has_token_admin_via_secret()
    test_delete_returns_true_false()
    test_list_services_self_check()
    test_resolve()
    test_get_access_token_parses_token_json()
    test_unreachable_socket_clear_error()
    print(f"\n{'='*50}")
    print(f"  {PASSED} passed, {FAILED} failed")
    if ERRORS:
        print("\nFailures:")
        for e in ERRORS:
            print(e)
    sys.exit(0 if FAILED == 0 else 1)


if __name__ == "__main__":
    main()
