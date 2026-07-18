"""Regression tests for canonical-uid token keying in ``tools.gws_auth``.

Pins the fix for the recurring OAuth "no token stored" bug: the write path
stored tokens under ``draas_user_id`` (e.g. ``ndr``) while the read path looked
them up under the raw Telegram id (e.g. ``1000000001``) — two different vault
keys, so a successful callback was never readable.

The invariant these tests enforce: **a token written after an OAuth callback is
readable from the same session**, because both paths resolve the raw channel id
to the same canonical vault ``user_id`` and the read passes ``session_uid`` ==
``user_id`` (which the vault requires).
"""

import tools.gws_vault_client as vault_module

CANON = "ndr-1000000001"


def _install_fake_vault(monkeypatch, store):
    """Patch functions directly on the real tools.gws_vault_client module.

    Using monkeypatch.setitem(sys.modules, ...) here used to work, but is
    fragile to test-collection order: ``from tools import gws_vault_client``
    resolves via getattr on the already-imported ``tools`` package first,
    which wins over a sys.modules substitution once any other test in the
    same session has genuinely imported the real module (2026-07-18,
    surfaced by new gws-vault-related test files changing collection
    order). Patching the real module's attributes is correct regardless of
    import order.
    """
    def resolve(identity_type, value):
        # Every raw identifier for this user maps to the canonical surrogate.
        if str(value) in ("1000000001", "ndr@draas.com", "ndr@ahfl.in", "ndr", CANON):
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

    monkeypatch.setattr(vault_module, "resolve", resolve)
    monkeypatch.setattr(vault_module, "set_token", set_token)
    monkeypatch.setattr(vault_module, "get_token", get_token)
    monkeypatch.setattr(vault_module, "has_token", has_token)


class _FakeCreds:
    def to_json(self):
        return "{}"


def test_canonical_uid_resolves_every_channel_id(monkeypatch):
    _install_fake_vault(monkeypatch, {})
    from tools import gws_auth

    assert gws_auth.canonical_uid("1000000001") == CANON      # telegram
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
    uid = gws_auth.canonical_uid("1000000001")
    gws_auth.save_credentials(uid, _FakeCreds(), "google-draas")

    # Read path resolves the *raw* telegram id to the same canonical uid.
    assert gws_auth.has_token("1000000001", "google-draas") is True
    assert (CANON, "google-draas") in store
    # And nothing was written under the raw telegram id or the slug.
    assert ("1000000001", "google-draas") not in store
    assert ("ndr", "google-draas") not in store
