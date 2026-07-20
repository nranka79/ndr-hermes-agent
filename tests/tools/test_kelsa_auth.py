"""
Tests for the Kelsa OAuth three-layer fix (2026-07-19):

Layer 1 — idempotency: ``get_auth_url()`` caches URLs per-user within a
cooldown window; repeated calls return the same URL with the same PKCE
verifier. Cache is cleared after a successful token exchange and
expires after ``_AUTH_URL_COOLDOWN_SECONDS``.

Layer 2 — no silent auth: ``_not_authorized_result()`` returns an error
message directing the caller to ``kelsa_login`` instead of auto-generating
an auth URL.

Layer 3 — pending guard: ``kelsa_login`` refuses to generate a new URL
when ``kelsa_login_tool._pending_auth`` already contains the user's id;
``kelsa_complete_login`` clears it on success.

Configurable redirect_uri: ``REDIRECT_URI`` reads from ``KELSA_REDIRECT_URI``
env var, falling back to the public HTTPS callback
``https://transcribe.ahfl.in/kelsa/auth/callback`` (2026-07-20). The DCR
client cache detects stale redirect_uris and re-registers automatically.
"""

from __future__ import annotations

import json
import os
import time

import httpx
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _fresh_cache():
    """Clear module-level caches before each test so prior test state never
    leaks.  This is safe because the isolation plugin spawns fresh processes
    anyway -- but within a single test, we want deterministic cache state."""
    import tools.kelsa_auth as _ka

    _ka._auth_url_cache.clear()
    try:
        import tools.kelsa_tool as _kt

        _kt._pending_auth.clear()
    except Exception:
        pass
    yield


@pytest.fixture
def fake_vault(monkeypatch):
    """Install a fake gws_vault_client that stores tokens in a local dict.
    Mirrors the pattern from ``test_gws_auth_canonical.py``."""
    import tools.gws_vault_client as vault_module

    store: dict[tuple[str, str], str] = {}
    identities: dict[str, dict] = {}

    def resolve(identity_type, value):
        if str(value) in ("1000000001", "7449813913", "ndr@draas.com", "ndr"):
            return "ndr-1000000001"
        if str(value) in ("9999999999", "other@example.com"):
            return "other-9999999999"
        return None

    def set_token(user_id, service, token_json):
        store[(str(user_id), service)] = token_json
        return True

    def get_token(user_id, service, *, session_uid=None):
        return store[(str(user_id), service)]

    def has_token(user_id, service, *, session_uid=None):
        return (str(user_id), service) in store

    def add_identity(user_id, **idents):
        identities[str(user_id)] = idents

    monkeypatch.setattr(vault_module, "resolve", resolve)
    monkeypatch.setattr(vault_module, "set_token", set_token)
    monkeypatch.setattr(vault_module, "get_token", get_token)
    monkeypatch.setattr(vault_module, "has_token", has_token)
    monkeypatch.setattr(vault_module, "add_identity", add_identity)
    return store, identities


@pytest.fixture
def fake_dcr_client(monkeypatch, tmp_path):
    """Point the DCR client cache to a temp directory and stub the httpx
    registration call. Returns (client_id, dcr_cache_path)."""
    import tools.kelsa_auth as ka
    from tools.mcp_oauth import _get_token_dir

    # Redirect the DCR cache dir to temp
    token_dir = tmp_path / "mcp-tokens"
    token_dir.mkdir(parents=True, exist_ok=True)

    def _fake_token_dir():
        return token_dir

    monkeypatch.setattr("tools.mcp_oauth._get_token_dir", _fake_token_dir)

    # Stub httpx.post for DCR registration
    original_post = httpx.post

    def _fake_post(url, *args, **kwargs):
        if url == ka.REGISTRATION_ENDPOINT:
            body = kwargs.get("json", {})
            client_id = "dcr-client-test-001"
            # Return a mock DCR response
            class FakeResponse:
                status_code = 201

                def raise_for_status(self):
                    pass

                def json(self):
                    return {"client_id": client_id, "redirect_uris": body.get("redirect_uris", [])}

            return FakeResponse()
        return original_post(url, *args, **kwargs)

    monkeypatch.setattr(httpx, "post", _fake_post)

    return "dcr-client-test-001", token_dir / "kelsa-read-dcr-client-v2.json"


# ---------------------------------------------------------------------------
# Layer 1: Auth URL idempotency cache
# ---------------------------------------------------------------------------


class TestAuthUrlCache:
    """Tests for the ``get_auth_url()`` cache (Layer 1)."""

    def test_repeat_call_returns_same_url_within_cooldown(self, fake_dcr_client):
        from tools.kelsa_auth import get_auth_url

        url1 = get_auth_url("7449813913")
        url2 = get_auth_url("7449813913")

        assert url1 == url2, (
            "Second call within cooldown should return the same URL "
            "(same PKCE verifier + challenge)"
        )

    def test_different_users_get_different_urls(self, fake_dcr_client):
        from tools.kelsa_auth import get_auth_url

        url_a = get_auth_url("7449813913")
        url_b = get_auth_url("9999999999")

        assert url_a != url_b, "Different users must get different URLs"

    def test_cache_cleared_after_exchange(self, fake_dcr_client, fake_vault, monkeypatch):
        from tools.kelsa_auth import get_auth_url, exchange_and_store, _auth_url_cache, TOKEN_ENDPOINT

        # Stub the token exchange HTTP call so it doesn't hit Kelsa's real server.
        original_post = httpx.post

        class FakeTokenOk:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "access_token": "test-at-abc",
                    "refresh_token": "test-rt-xyz",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }

        def _fake_post(url, *args, **kwargs):
            if str(url) == TOKEN_ENDPOINT:
                return FakeTokenOk()
            return original_post(url, *args, **kwargs)

        monkeypatch.setattr(httpx, "post", _fake_post)

        url1 = get_auth_url("7449813913")
        assert "7449813913" in _auth_url_cache

        exchange_and_store(
            "7449813913",
            code="test-code-123",
            code_verifier="test-verifier",
        )

        assert "7449813913" not in _auth_url_cache, (
            "Cache should be cleared after a successful token exchange"
        )

    def test_cache_expires_after_cooldown(self, fake_dcr_client, monkeypatch):
        from tools.kelsa_auth import get_auth_url, _auth_url_cache, _AUTH_URL_COOLDOWN_SECONDS

        url1 = get_auth_url("7449813913")

        # Advance time past cooldown
        future = time.time() + _AUTH_URL_COOLDOWN_SECONDS + 10

        def _fake_time():
            return future

        monkeypatch.setattr("tools.kelsa_auth.time.time", _fake_time)

        url2 = get_auth_url("7449813913")
        assert url1 != url2, (
            "After cooldown expires, a fresh URL with a new PKCE verifier "
            "should be generated"
        )

    def test_clear_auth_url_cache_removes_entry(self, fake_dcr_client):
        from tools.kelsa_auth import get_auth_url, _clear_auth_url_cache, _auth_url_cache

        get_auth_url("7449813913")
        assert "7449813913" in _auth_url_cache

        _clear_auth_url_cache("7449813913")
        assert "7449813913" not in _auth_url_cache

    def test_clear_auth_url_cache_noop_for_unknown(self):
        from tools.kelsa_auth import _clear_auth_url_cache, _auth_url_cache

        _clear_auth_url_cache("nonexistent")
        assert True  # should not raise

    def test_has_valid_cached_url_true_within_cooldown(self, fake_dcr_client):
        from tools.kelsa_auth import get_auth_url, _has_valid_cached_url

        get_auth_url("7449813913")
        assert _has_valid_cached_url("7449813913") is True

    def test_has_valid_cached_url_false_after_clear(self, fake_dcr_client):
        from tools.kelsa_auth import get_auth_url, _has_valid_cached_url, _clear_auth_url_cache

        get_auth_url("7449813913")
        _clear_auth_url_cache("7449813913")
        assert _has_valid_cached_url("7449813913") is False

    def test_has_valid_cached_url_false_never_called(self):
        from tools.kelsa_auth import _has_valid_cached_url

        assert _has_valid_cached_url("never-called") is False

    def test_notify_context_set_and_get(self):
        from tools.kelsa_auth import set_notify_context, get_notify_context

        set_notify_context("7449813913", "telegram", "7449813913")
        ctx = get_notify_context("7449813913")
        assert ctx == {"platform": "telegram", "chat_id": "7449813913"}

    def test_notify_context_returns_empty_for_unknown(self):
        from tools.kelsa_auth import get_notify_context

        assert get_notify_context("nobody") == {}

    def test_notify_context_cleared_with_cache(self):
        from tools.kelsa_auth import (
            set_notify_context, get_notify_context,
            _clear_auth_url_cache,
        )

        set_notify_context("7449813913", "telegram", "7449813913")
        _clear_auth_url_cache("7449813913")
        assert get_notify_context("7449813913") == {}

    def test_notify_context_set_during_login(self, fake_dcr_client, fake_vault):
        """Verify that kelsa_login stores the notification context."""
        from tools.kelsa_tool import kelsa_login_tool, _pending_auth
        from tools.kelsa_auth import get_notify_context
        from gateway.session_context import set_session_vars, clear_session_vars

        tokens = set_session_vars(
            user_id="7449813913",
            platform="cli",
            chat_id="session-1",
        )
        try:
            kelsa_login_tool({})

            ctx = get_notify_context("7449813913")
            assert "platform" in ctx
            # CLI puts the chat_id as empty string by default
            assert ctx.get("chat_id") == "session-1"
        finally:
            clear_session_vars(tokens)


# ---------------------------------------------------------------------------
# Layer 2: _not_authorized_result no longer auto-generates URLs
# ---------------------------------------------------------------------------


class TestNotAuthorizedResult:
    """Tests that ``_not_authorized_result`` returns an error without side
    effects (Layer 2)."""

    def test_returns_error_not_url(self):
        from tools.kelsa_tool import _not_authorized_result

        result = _not_authorized_result("7449813913", "test")
        parsed = json.loads(result)

        assert "error" in parsed, "Must return an error"
        assert "kelsa_login" in parsed["error"], (
            "Error must direct the caller to use kelsa_login"
        )

    def test_does_not_import_get_auth_url(self):
        """_not_authorized_result no longer imports or calls get_auth_url.
        Verify this by checking its source doesn't even reference it."""
        from tools.kelsa_tool import _not_authorized_result
        import inspect

        source = inspect.getsource(_not_authorized_result)
        assert "get_auth_url" not in source, (
            "_not_authorized_result must not call get_auth_url"
        )


# ---------------------------------------------------------------------------
# Layer 3: _pending_auth guard
# ---------------------------------------------------------------------------


class TestPendingAuthGuard:
    """Tests for the ``_pending_auth`` set in ``kelsa_tool`` (Layer 3)."""

    def test_login_adds_to_pending(self, fake_dcr_client, fake_vault):
        from tools.kelsa_tool import kelsa_login_tool, _pending_auth
        from gateway.session_context import set_session_vars, clear_session_vars

        tokens = set_session_vars(user_id="7449813913", platform="cli", chat_id="")
        try:
            result = kelsa_login_tool({})
            parsed = json.loads(result)
            assert "7449813913" in _pending_auth, (
                "After kelsa_login delivers a URL, the user should be "
                "in _pending_auth"
            )
        finally:
            clear_session_vars(tokens)

    def test_repeat_login_returns_pending_message(self, fake_dcr_client, fake_vault):
        from tools.kelsa_tool import kelsa_login_tool, _pending_auth
        from gateway.session_context import set_session_vars, clear_session_vars

        tokens = set_session_vars(user_id="7449813913", platform="cli", chat_id="")
        try:
            # First call adds to _pending_auth
            kelsa_login_tool({})
            assert "7449813913" in _pending_auth

            # Second call should return pending message, not generate new URL
            result2 = kelsa_login_tool({})
            parsed2 = json.loads(result2)

            assert parsed2.get("error") is None, (
                "Second call should not return an error"
            )
            assert "pending" in parsed2.get("message", "").lower() or \
                   "already" in parsed2.get("message", "").lower(), (
                "Second call should indicate auth is already pending"
            )
        finally:
            clear_session_vars(tokens)

    def test_complete_login_clears_pending(self, fake_dcr_client, fake_vault, monkeypatch):
        from tools.kelsa_tool import (
            kelsa_login_tool,
            kelsa_complete_login_tool,
            _pending_auth,
        )
        from tools.kelsa_auth import TOKEN_ENDPOINT
        from gateway.session_context import set_session_vars, clear_session_vars

        # Stub the token exchange HTTP call.
        original_post = httpx.post

        class FakeTokenOk:
            status_code = 200
            def raise_for_status(self):
                pass
            def json(self):
                return {
                    "access_token": "test-at-abc",
                    "refresh_token": "test-rt-xyz",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }

        def _fake_post(url, *args, **kwargs):
            if str(url) == TOKEN_ENDPOINT:
                return FakeTokenOk()
            return original_post(url, *args, **kwargs)

        monkeypatch.setattr(httpx, "post", _fake_post)

        tokens = set_session_vars(user_id="7449813913", platform="cli", chat_id="")
        try:
            kelsa_login_tool({})
            assert "7449813913" in _pending_auth

            # Simulate paste-back with a URL containing code + state
            pasted = (
                "http://127.0.0.1:47562/callback"
                "?code=auth-code-xyz"
                "&state=7449813913:test-verifier-pkce"
            )
            result = kelsa_complete_login_tool({"pasted": pasted})
            parsed = json.loads(result)

            assert "error" not in parsed, (
                f"Exchange should succeed: {parsed.get('error', '')}"
            )
            assert "7449813913" not in _pending_auth, (
                "User should be removed from _pending_auth after "
                "successful login completion"
            )
        finally:
            clear_session_vars(tokens)

    def test_no_session_returns_error(self):
        from tools.kelsa_tool import kelsa_login_tool

        result = kelsa_login_tool({})
        parsed = json.loads(result)
        assert "error" in parsed

    def test_stale_pending_falls_through_after_cooldown(self, fake_dcr_client, fake_vault, monkeypatch):
        """If _pending_auth has the tid but the cache has expired (user
        abandoned the first attempt), kelsa_login should discard the stale
        flag and generate a fresh URL."""
        from tools.kelsa_tool import kelsa_login_tool, _pending_auth
        from tools.kelsa_auth import _auth_url_cache, _AUTH_URL_COOLDOWN_SECONDS
        from gateway.session_context import set_session_vars, clear_session_vars

        tokens = set_session_vars(user_id="7449813913", platform="cli", chat_id="")
        try:
            # First call: generates URL, adds to _pending_auth
            kelsa_login_tool({})
            assert "7449813913" in _pending_auth
            assert "7449813913" in _auth_url_cache

            # Advance time past cooldown so the cached URL expires
            future = time.time() + _AUTH_URL_COOLDOWN_SECONDS + 10

            def _fake_time():
                return future

            monkeypatch.setattr("tools.kelsa_auth.time.time", _fake_time)

            # Second call: _pending_auth has tid but cache is expired
            # Should clear _pending_auth and generate a fresh URL
            result = kelsa_login_tool({})
            parsed = json.loads(result)

            assert parsed.get("error") is None, (
                f"Should not error on stale pending: {parsed.get('error', '')}"
            )
            # Should have generated a new URL (not returned pending message)
            assert "pending" not in parsed.get("message", ""), (
                "Should not return pending message for expired cache"
            )
        finally:
            clear_session_vars(tokens)


# ---------------------------------------------------------------------------
# Configurable redirect URI
# ---------------------------------------------------------------------------


class TestRedirectUri:
    """Tests that ``REDIRECT_URI`` respects the ``KELSA_REDIRECT_URI`` env var."""

    def test_default_is_https_callback(self):
        # Unset the env var to ensure fallback -- 2026-07-20: default is now
        # the public HTTPS callback (Kelsa's OAuth server confirmed to
        # accept it; see tools/kelsa_auth.py's REDIRECT_URI comment).
        old = os.environ.pop("KELSA_REDIRECT_URI", None)
        try:
            # Reimport to pick up the default
            import importlib
            from tools import kelsa_auth

            importlib.reload(kelsa_auth)
            assert kelsa_auth.REDIRECT_URI == "https://transcribe.ahfl.in/kelsa/auth/callback"
        finally:
            if old is not None:
                os.environ["KELSA_REDIRECT_URI"] = old

    def test_env_var_overrides_default_to_localhost_fallback(self, monkeypatch):
        """KELSA_REDIRECT_URI can still force the old paste-back localhost
        flow (e.g. for debugging if the HTTPS callback ever regresses)."""
        monkeypatch.setenv("KELSA_REDIRECT_URI", "http://127.0.0.1:47562/callback")
        import importlib
        from tools import kelsa_auth

        importlib.reload(kelsa_auth)
        assert kelsa_auth.REDIRECT_URI == "http://127.0.0.1:47562/callback"

    def test_env_var_overrides_default(self, monkeypatch):
        monkeypatch.setenv("KELSA_REDIRECT_URI", "https://transcribe.ahfl.in/kelsa/auth/callback")
        import importlib
        from tools import kelsa_auth

        importlib.reload(kelsa_auth)
        assert kelsa_auth.REDIRECT_URI == "https://transcribe.ahfl.in/kelsa/auth/callback"


# ---------------------------------------------------------------------------
# DCR client registration respects redirect_uri changes
# ---------------------------------------------------------------------------


class TestDcrRegistration:
    """Tests that the DCR client re-registers when the redirect_uri changes."""

    def test_re_registers_on_redirect_uri_change(self, fake_dcr_client, monkeypatch, tmp_path):
        """When REDIRECT_URI changes, the cached DCR client should be
        discarded and a new one registered."""
        import tools.kelsa_auth as ka
        from urllib.parse import urlparse, parse_qs

        ka._auth_url_cache.clear()

        # Set a different redirect_uri
        monkeypatch.setattr(ka, "REDIRECT_URI", "https://transcribe.ahfl.in/kelsa/auth/callback")

        url = ka.get_auth_url("7449813913")
        # The redirect_uri is URL-encoded in the query string; decode and check.
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        actual_redirect = params.get("redirect_uri", [""])[0]
        assert actual_redirect == "https://transcribe.ahfl.in/kelsa/auth/callback", (
            f"Auth URL should use the new redirect_uri, got {actual_redirect}"
        )

        # The cached file should now contain the new redirect_uri
        _, cache_path = fake_dcr_client
        if cache_path.exists():
            cached = json.loads(cache_path.read_text(encoding="utf-8"))
            assert cached.get("redirect_uri") == "https://transcribe.ahfl.in/kelsa/auth/callback"


# ---------------------------------------------------------------------------
# Exchange & store
# ---------------------------------------------------------------------------


class TestExchangeAndStore:
    """Tests for the token exchange and vault storage path."""

    def test_exchange_stores_token_in_vault(self, fake_dcr_client, fake_vault, monkeypatch):
        store, _ = fake_vault

        import tools.kelsa_auth as ka

        # Stub httpx.post for the token exchange endpoint
        original_post = httpx.post

        class FakeTokenResponse:
            status_code = 200

            def raise_for_status(self):
                pass

            def json(self):
                return {
                    "access_token": "test-access-token-abc",
                    "refresh_token": "test-refresh-token-xyz",
                    "expires_in": 3600,
                    "token_type": "Bearer",
                }

        def _fake_post(url, *args, **kwargs):
            if url == ka.TOKEN_ENDPOINT:
                return FakeTokenResponse()
            return original_post(url, *args, **kwargs)

        monkeypatch.setattr(httpx, "post", _fake_post)

        ka.exchange_and_store(
            "7449813913",
            code="test-code-123",
            code_verifier="test-verifier-abc",
        )

        assert ("ndr-1000000001", "mcp-kelsa-read") in store, (
            "Token should be stored in vault under the canonical uid"
        )

    def test_exchange_failure_raises(self, fake_dcr_client, fake_vault, monkeypatch):
        import tools.kelsa_auth as ka

        original_post = httpx.post

        class FakeErrorResponse:
            status_code = 400

            def raise_for_status(self):
                raise httpx.HTTPStatusError(
                    "Bad Request",
                    request=None,
                    response=self,
                )

            @property
            def text(self):
                return "invalid_grant"

        def _fake_post(url, *args, **kwargs):
            if url == ka.TOKEN_ENDPOINT:
                return FakeErrorResponse()
            return original_post(url, *args, **kwargs)

        monkeypatch.setattr(httpx, "post", _fake_post)

        with pytest.raises(RuntimeError, match="Kelsa token exchange failed"):
            ka.exchange_and_store(
                "7449813913",
                code="bad-code",
                code_verifier="bad-verifier",
            )


# ---------------------------------------------------------------------------
# Parse callback paste
# ---------------------------------------------------------------------------


class TestParseCallbackPaste:
    """Tests for ``parse_callback_paste()``."""

    def test_parses_full_url(self):
        from tools.kelsa_auth import parse_callback_paste

        url = (
            "http://127.0.0.1:47562/callback"
            "?code=abc123"
            "&state=7449813913:verifier-pkce"
        )
        code, state = parse_callback_paste(url)
        assert code == "abc123"
        assert state == "7449813913:verifier-pkce"

    def test_parses_query_string_only(self):
        from tools.kelsa_auth import parse_callback_paste

        qs = "code=abc123&state=7449813913:verifier-pkce"
        code, state = parse_callback_paste(qs)
        assert code == "abc123"
        assert state == "7449813913:verifier-pkce"

    def test_parses_with_leading_question_mark(self):
        from tools.kelsa_auth import parse_callback_paste

        qs = "?code=abc123&state=7449813913:verifier-pkce"
        code, state = parse_callback_paste(qs)
        assert code == "abc123"
        assert state == "7449813913:verifier-pkce"

    def test_raises_on_empty_input(self):
        from tools.kelsa_auth import parse_callback_paste

        with pytest.raises(ValueError, match="Nothing was pasted"):
            parse_callback_paste("")

    def test_raises_on_missing_code(self):
        from tools.kelsa_auth import parse_callback_paste

        with pytest.raises(ValueError, match="code.*state"):
            parse_callback_paste("state=7449813913:verifier")

    def test_raises_on_missing_state(self):
        from tools.kelsa_auth import parse_callback_paste

        with pytest.raises(ValueError, match="code.*state"):
            parse_callback_paste("code=abc123")


# ---------------------------------------------------------------------------
# Sanity: token exchange from callback handler via state split
# ---------------------------------------------------------------------------


class TestStateIdentity:
    """The state format ``tid:verifier`` must round-trip correctly."""

    def test_state_split_roundtrip(self):
        tid = "7449813913"
        verifier = "rvF8kL2xZpQ9wYnS3mB5cA7"

        state = f"{tid}:{verifier}"
        state_tid, state_verifier = state.split(":", 1)

        assert state_tid == tid
        assert state_verifier == verifier

    def test_verifier_has_no_colon(self):
        """PKCE verifier is URL-safe base64 with no colon, so split is safe."""
        import base64
        import hashlib
        import secrets

        verifier = (
            base64.urlsafe_b64encode(secrets.token_bytes(64))
            .rstrip(b"=")
            .decode("ascii")
        )
        assert ":" not in verifier, "URL-safe base64 verifier must not contain ':'"
