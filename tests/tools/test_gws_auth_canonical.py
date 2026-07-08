"""Regression tests for canonical-uid token keying in ``tools.gws_auth``.

Pins the fix for the recurring OAuth "no token stored" bug: the write path
stored tokens under ``draas_user_id`` (e.g. ``ndr``) while the read path looked
them up under the raw Telegram id (e.g. ``7449813913``) — two different vault
keys, so a successful callback was never readable.

The invariant these tests enforce: **a token written after an OAuth callback is
readable from the same session**, because both paths resolve the raw channel id
to the same canonical vault ``user_id`` and the read passes ``session_uid`` ==
``user_id`` (which the vault requires).
"""

import sys
import types

CANON = "ndr-7449813913"


def _install_fake_vault(monkeypatch, store):
    """Install a fake ``tools.gws_vault_client`` backed by an in-memory dict."""
    fake = types.ModuleType("tools.gws_vault_client")

    def resolve(identity_type, value):
        # Every raw identifier for this user maps to the canonical surrogate.
        if str(value) in ("7449813913", "ndr@draas.com", "ndr@ahfl.in", "ndr", CANON):
            return CANON
        return None

    def set_token(user_id, service, token_json):
        store[(str(user_id), service)] = token_json

    def get_token(user_id, service, *, session_uid=None):
        # The real vault enforces session_uid == user_id on reads.
        assert session_uid == str(user_id), "read must pass session_uid == user_id"
        return store[(str(user_id), service)]

    def has_token(user_id, service, *, session_uid=None):
        assert session_uid == str(user_id), "read must pass session_uid == user_id"
        return (str(user_id), service) in store

    fake.resolve = resolve
    fake.set_token = set_token
    fake.get_token = get_token
    fake.has_token = has_token
    monkeypatch.setitem(sys.modules, "tools.gws_vault_client", fake)
    return fake


class _FakeCreds:
    def to_json(self):
        return "{}"


def test_canonical_uid_resolves_every_channel_id(monkeypatch):
    _install_fake_vault(monkeypatch, {})
    from tools import gws_auth

    assert gws_auth.canonical_uid("7449813913") == CANON      # telegram
    assert gws_auth.canonical_uid("ndr@draas.com") == CANON   # email
    assert gws_auth.canonical_uid("ndr") == CANON             # slug


def test_canonical_uid_falls_back_to_raw_when_unresolved(monkeypatch):
    _install_fake_vault(monkeypatch, {})
    from tools import gws_auth

    # Unknown id → unchanged (single-key / unmigrated users keep working).
    assert gws_auth.canonical_uid("9999999999") == "9999999999"


def test_write_then_read_use_the_same_canonical_key(monkeypatch):
    store = {}
    _install_fake_vault(monkeypatch, store)
    from tools import gws_auth

    # Write path (callback) stores under the canonical uid.
    uid = gws_auth.canonical_uid("7449813913")
    gws_auth.save_credentials(uid, _FakeCreds(), "google-draas")

    # Read path resolves the *raw* telegram id to the same canonical uid.
    assert gws_auth.has_token("7449813913", "google-draas") is True
    assert (CANON, "google-draas") in store
    # And nothing was written under the raw telegram id or the slug.
    assert ("7449813913", "google-draas") not in store
    assert ("ndr", "google-draas") not in store
