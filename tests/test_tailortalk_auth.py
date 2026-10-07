"""Unit tests for tools/tailortalk_auth.py (no network, no vault).

unittest-style on purpose: the production container has no pytest, so these
run there with ``python3 -m unittest tests.test_tailortalk_auth``. pytest
collects them too.
"""

import base64
import hashlib
import json
import os
import sys
import time
import unittest
from unittest import mock
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import tailortalk_auth as ta  # noqa: E402

# Captured before setUp() patches it, so the guard test exercises the real one.
_ORIG_GUARD = ta._reject_if_not_called_from_tailortalk_tool


class _FakeVault:
    class VaultError(RuntimeError):
        pass

    class VaultNoTokenError(VaultError):
        pass

    def __init__(self):
        self.store = {}

    def get_token(self, uid, svc, *, session_uid=None):
        try:
            return self.store[(uid, svc)]
        except KeyError:
            raise self.VaultNoTokenError(f"No {svc} token for user {uid}")

    def set_token(self, uid, svc, token_json):
        self.store[(uid, svc)] = token_json

    def has_token(self, uid, svc, *, session_uid=None):
        return (uid, svc) in self.store


class _Resp:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload)

    def json(self):
        return self._payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class _FakeHttpx:
    """Records POSTs; answers by endpoint."""

    def __init__(self, dcr_payload=None, token_payload=None):
        self.calls = []
        self.dcr_payload = dcr_payload or {"client_id": "cid-1", "token_endpoint_auth_method": "none"}
        self.token_payload = token_payload or {
            "access_token": "at-1", "refresh_token": "rt-1", "expires_in": 3600, "token_type": "Bearer",
        }

    def post(self, url, json=None, data=None, headers=None, timeout=None):
        self.calls.append((url, json, data))
        if url == ta.REGISTRATION_ENDPOINT:
            return _Resp(201, dict(self.dcr_payload))
        if url == ta.TOKEN_ENDPOINT:
            return _Resp(200, dict(self.token_payload))
        raise AssertionError(f"unexpected POST {url}")


class TailorTalkAuthTests(unittest.TestCase):
    UID_RAW = "7449813913"
    UID_CANON = "ndr-7449813913"

    def setUp(self):
        self.vault = _FakeVault()
        self.httpx = _FakeHttpx()
        patches = [
            mock.patch.object(ta, "_vault", lambda: self.vault),
            mock.patch.object(ta, "_canonical_uid", lambda tid: self.UID_CANON),
            mock.patch.object(ta, "_session_user_id", lambda: self.UID_RAW),
            mock.patch.object(ta, "httpx", self.httpx),
            # The caller guard is exercised separately; bypass it here.
            mock.patch.object(ta, "_reject_if_not_called_from_tailortalk_tool", lambda op: None),
            mock.patch.dict(os.environ, {}, clear=False),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)
        os.environ.pop("HERMES_RPC_SOCKET", None)
        ta._auth_url_cache.clear()
        ta._notify_context.clear()

    # -- guards --------------------------------------------------------------

    def test_get_auth_url_rejects_direct_callers(self):
        with mock.patch.object(ta, "_reject_if_not_called_from_tailortalk_tool", _ORIG_GUARD):
            with self.assertRaises(RuntimeError):
                ta.get_auth_url()
        self.assertEqual(self.httpx.calls, [], "guard must fire before any network call")

    def test_exchange_refuses_inside_sandbox_before_burning_code(self):
        os.environ["HERMES_RPC_SOCKET"] = "/tmp/x.sock"
        with self.assertRaises(RuntimeError):
            ta.exchange_and_store("code", "verifier")
        self.assertEqual(self.httpx.calls, [])

    # -- PKCE / URL ----------------------------------------------------------

    def test_pkce_is_s256(self):
        verifier, challenge = ta._generate_pkce()
        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(challenge, expected)
        self.assertNotIn(":", verifier)

    def test_auth_url_shape_and_dcr_registration(self):
        url = ta.get_auth_url()
        parsed = urlparse(url)
        self.assertEqual(f"{parsed.scheme}://{parsed.netloc}{parsed.path}", ta.AUTHORIZATION_ENDPOINT)
        q = {k: v[0] for k, v in parse_qs(parsed.query).items()}
        self.assertEqual(q["response_type"], "code")
        self.assertEqual(q["client_id"], "cid-1")
        self.assertEqual(q["redirect_uri"], ta.REDIRECT_URI)
        self.assertEqual(q["scope"], ta.SCOPE)
        self.assertEqual(q["resource"], ta.MCP_URL)
        self.assertEqual(q["code_challenge_method"], "S256")
        uid, verifier = q["state"].split(":", 1)
        self.assertEqual(uid, self.UID_RAW)
        expected = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
        self.assertEqual(q["code_challenge"], expected)
        # DCR happened once and was cached in the vault under the system user.
        dcr_calls = [c for c in self.httpx.calls if c[0] == ta.REGISTRATION_ENDPOINT]
        self.assertEqual(len(dcr_calls), 1)
        self.assertEqual(dcr_calls[0][1]["token_endpoint_auth_method"], ta.TOKEN_AUTH_METHOD)
        stored = json.loads(self.vault.store[(ta._DCR_USER_ID, ta.DCR_SERVICE_NAME)])
        self.assertEqual(stored["redirect_uri"], ta.REDIRECT_URI)

    def test_auth_url_is_idempotent_within_cooldown(self):
        self.assertEqual(ta.get_auth_url(), ta.get_auth_url())
        ta._auth_url_cache[self.UID_RAW] = (time.time() - ta._AUTH_URL_COOLDOWN_SECONDS - 1, "stale")
        self.assertNotEqual(ta.get_auth_url(), "stale")

    def test_dcr_reregisters_when_redirect_uri_changes(self):
        self.vault.set_token(ta._DCR_USER_ID, ta.DCR_SERVICE_NAME, json.dumps(
            {"client_id": "old", "redirect_uri": "https://old.example/cb", "token_endpoint_auth_method": "none"}
        ))
        client = ta._get_or_register_client()
        self.assertEqual(client["client_id"], "cid-1")
        self.assertEqual(len(self.httpx.calls), 1)

    def test_dcr_cache_hit_makes_no_network_call(self):
        self.vault.set_token(ta._DCR_USER_ID, ta.DCR_SERVICE_NAME, json.dumps(
            {"client_id": "cached", "redirect_uri": ta.REDIRECT_URI, "token_endpoint_auth_method": ta.TOKEN_AUTH_METHOD}
        ))
        self.assertEqual(ta._get_or_register_client()["client_id"], "cached")
        self.assertEqual(self.httpx.calls, [])

    # -- exchange / storage / refresh ----------------------------------------

    def test_exchange_stores_record_under_canonical_uid(self):
        ta._auth_url_cache[self.UID_RAW] = (time.time(), "u")
        ta.exchange_and_store("the-code", "the-verifier")
        token_calls = [c for c in self.httpx.calls if c[0] == ta.TOKEN_ENDPOINT]
        self.assertEqual(len(token_calls), 1)
        data = token_calls[0][2]
        self.assertEqual(data["grant_type"], "authorization_code")
        self.assertEqual(data["code"], "the-code")
        self.assertEqual(data["code_verifier"], "the-verifier")
        self.assertEqual(data["resource"], ta.MCP_URL)
        self.assertEqual(data["client_id"], "cid-1")
        self.assertNotIn("client_secret", data)
        record = json.loads(self.vault.store[(self.UID_CANON, ta.SERVICE_NAME)])
        self.assertEqual(record["access_token"], "at-1")
        self.assertIn("obtained_at", record)
        self.assertNotIn(self.UID_RAW, ta._auth_url_cache, "one-time URL cache cleared after exchange")
        self.assertTrue(ta.has_token())

    def test_client_secret_is_sent_when_dcr_issued_one(self):
        self.httpx.dcr_payload = {"client_id": "cid-s", "client_secret": "sek", "token_endpoint_auth_method": "none"}
        ta.exchange_and_store("c", "v")
        data = [c for c in self.httpx.calls if c[0] == ta.TOKEN_ENDPOINT][0][2]
        self.assertEqual(data["client_secret"], "sek")

    def test_get_valid_access_token_refreshes_when_expired(self):
        self.vault.set_token(self.UID_CANON, ta.SERVICE_NAME, json.dumps(
            {"access_token": "old", "refresh_token": "rt-old", "expires_in": 3600, "obtained_at": time.time() - 7200}
        ))
        self.vault.set_token(ta._DCR_USER_ID, ta.DCR_SERVICE_NAME, json.dumps(
            {"client_id": "cid-1", "redirect_uri": ta.REDIRECT_URI, "token_endpoint_auth_method": ta.TOKEN_AUTH_METHOD}
        ))
        self.httpx.token_payload = {"access_token": "new", "expires_in": 3600}  # no refresh_token in reply
        self.assertEqual(ta.get_valid_access_token(), "new")
        data = self.httpx.calls[-1][2]
        self.assertEqual(data["grant_type"], "refresh_token")
        self.assertEqual(data["refresh_token"], "rt-old")
        record = json.loads(self.vault.store[(self.UID_CANON, ta.SERVICE_NAME)])
        self.assertEqual(record["refresh_token"], "rt-old", "old refresh token kept when server omits it")

    def test_get_valid_access_token_uses_fresh_token_without_network(self):
        self.vault.set_token(self.UID_CANON, ta.SERVICE_NAME, json.dumps(
            {"access_token": "fresh", "refresh_token": "rt", "expires_in": 3600, "obtained_at": time.time()}
        ))
        self.assertEqual(ta.get_valid_access_token(), "fresh")
        self.assertEqual(self.httpx.calls, [])

    def test_force_refresh(self):
        self.vault.set_token(self.UID_CANON, ta.SERVICE_NAME, json.dumps(
            {"access_token": "fresh", "refresh_token": "rt", "expires_in": 3600, "obtained_at": time.time()}
        ))
        self.vault.set_token(ta._DCR_USER_ID, ta.DCR_SERVICE_NAME, json.dumps(
            {"client_id": "cid-1", "redirect_uri": ta.REDIRECT_URI, "token_endpoint_auth_method": ta.TOKEN_AUTH_METHOD}
        ))
        self.assertEqual(ta.get_valid_access_token(force_refresh=True), "at-1")

    def test_no_token_raises_vault_no_token_error(self):
        with self.assertRaises(self.vault.VaultNoTokenError):
            ta.get_valid_access_token()

    def test_notify_context_round_trip(self):
        ta.set_notify_context("telegram", "123")
        self.assertEqual(ta.get_notify_context(), {"platform": "telegram", "chat_id": "123"})
        ta._clear_notify_context()
        self.assertEqual(ta.get_notify_context(), {})


if __name__ == "__main__":
    unittest.main()
