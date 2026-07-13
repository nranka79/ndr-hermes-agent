"""Regression tests for canonical-uid keying in ``tools.user_vocab``.

Pins the fix for the second live instance of the "vault resolves by raw id,
not any of the user's identities" bug class: ``tools/gws_auth.py`` was fixed
to canonicalize every raw channel id before touching the vault, but
``tools/user_vocab.py`` (STT vocabulary, sharing the same vault) called
``gws_vault_client`` directly with whatever raw id the caller passed —
confirmed still happening in production a full day after the gws_auth.py
fix landed (``tokens/1000000001/vocab.json`` newer than
``tokens/ndr-1000000001/vocab.json`` on the live vault).

The invariant these tests enforce: regardless of which raw identifier a
caller passes (Telegram id, email, canonical id already), vocab reads and
writes land on the same canonical vault key.
"""

import sys
import types

CANON = "ndr-1000000001"


def _install_fakes(monkeypatch, store):
    """Install a fake ``tools.gws_vault_client`` + ``tools.gws_auth`` backed
    by an in-memory dict, mirroring the pattern in
    ``test_gws_auth_canonical.py``.
    """
    fake_vault = types.ModuleType("tools.gws_vault_client")

    class VaultError(RuntimeError):
        pass

    class VaultNoTokenError(VaultError):
        pass

    def get_token(user_id, service, *, session_uid=None):
        assert session_uid == str(user_id), "read must pass session_uid == user_id"
        try:
            return store[(str(user_id), service)]
        except KeyError:
            raise VaultNoTokenError(f"no token for {user_id}/{service}")

    def set_token(user_id, service, token_json):
        store[(str(user_id), service)] = token_json

    def delete_token(user_id, service):
        return store.pop((str(user_id), service), None) is not None

    fake_vault.VaultError = VaultError
    fake_vault.VaultNoTokenError = VaultNoTokenError
    fake_vault.get_token = get_token
    fake_vault.set_token = set_token
    fake_vault.delete_token = delete_token
    monkeypatch.setitem(sys.modules, "tools.gws_vault_client", fake_vault)

    fake_gws_auth = types.ModuleType("tools.gws_auth")

    def canonical_uid(channel_id):
        cid = str(channel_id or "")
        if cid in ("1000000001", "ndr@draas.com", "ndr@ahfl.in", "ndr", CANON):
            return CANON
        return cid

    fake_gws_auth.canonical_uid = canonical_uid
    monkeypatch.setitem(sys.modules, "tools.gws_auth", fake_gws_auth)

    return fake_vault, fake_gws_auth


def _reload_user_vocab():
    sys.modules.pop("tools.user_vocab", None)
    import tools.user_vocab as uv
    return uv


def test_save_then_load_use_the_same_canonical_key_across_raw_ids(monkeypatch):
    store = {}
    _install_fakes(monkeypatch, store)
    uv = _reload_user_vocab()

    # Saved under the raw Telegram id.
    uv.save_vocab("1000000001", ["Kelsa", "Draas"])
    assert (CANON, "vocab") in store
    assert ("1000000001", "vocab") not in store

    # Loaded via the email identity for the same user -- must see the same data.
    assert uv.load_vocab("ndr@draas.com") == ["Draas", "Kelsa"]


def test_add_terms_does_not_split_across_raw_and_canonical_keys(monkeypatch):
    """Reproduces the exact production symptom: /vocab add (raw telegram id)
    followed by a read from anywhere else must not see an empty list because
    the write landed under a different key."""
    store = {}
    _install_fakes(monkeypatch, store)
    uv = _reload_user_vocab()

    uv.add_terms("1000000001", ["Nishant"])
    uv.add_terms("1000000001", ["Kelsa"])

    assert uv.load_vocab(CANON) == ["Kelsa", "Nishant"]
    # Only one vault key was ever touched for this user.
    assert sum(1 for (uid, svc) in store if svc == "vocab") == 1


def test_clear_vocab_removes_the_canonical_key(monkeypatch):
    store = {}
    _install_fakes(monkeypatch, store)
    uv = _reload_user_vocab()

    uv.save_vocab("1000000001", ["term"])
    assert (CANON, "vocab") in store

    uv.clear_vocab("1000000001")
    assert (CANON, "vocab") not in store
