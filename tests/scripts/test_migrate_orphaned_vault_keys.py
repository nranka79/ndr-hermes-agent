"""Tests for scripts/migrate_orphaned_vault_keys.py's core migrate() logic.

Uses an in-memory fake ``tools.gws_vault_client`` (same pattern as
``tests/tools/test_gws_auth_canonical.py``) so these tests never touch a
real vault -- critical for a data-mutating one-time migration script that
will eventually run against production.
"""

import importlib
import sys
import types

import pytest


@pytest.fixture
def fake_vault(monkeypatch):
    store = {}

    fake = types.ModuleType("tools.gws_vault_client")

    class VaultError(RuntimeError):
        pass

    def list_services(user_id, *, session_uid=None):
        assert session_uid == user_id, "must self-authorize with session_uid == user_id"
        return sorted(svc for (uid, svc) in store if uid == user_id)

    def get_token(user_id, service, *, session_uid=None):
        assert session_uid == user_id
        return store[(user_id, service)]

    def set_token(user_id, service, token_json):
        store[(user_id, service)] = token_json

    def delete_token(user_id, service):
        return store.pop((user_id, service), None) is not None

    fake.VaultError = VaultError
    fake.list_services = list_services
    fake.get_token = get_token
    fake.set_token = set_token
    fake.delete_token = delete_token
    fake.VAULT_SOCKET = ""
    fake.VAULT_SECRET = ""
    monkeypatch.setitem(sys.modules, "tools.gws_vault_client", fake)

    return fake, store


def _load_script():
    sys.modules.pop("scripts.migrate_orphaned_vault_keys", None)
    return importlib.import_module("scripts.migrate_orphaned_vault_keys")


class TestDryRun:
    def test_dry_run_reports_but_does_not_touch_the_store(self, fake_vault):
        _fake, store = fake_vault
        store[("7449813913", "google-draas")] = '{"a":1}'
        mod = _load_script()

        rc = mod.migrate(execute=False)

        assert rc == 0
        # Nothing moved -- dry run never writes.
        assert ("7449813913", "google-draas") in store
        assert ("ndr-7449813913", "google-draas") not in store


class TestCleanMigration:
    def test_service_only_under_raw_id_is_migrated(self, fake_vault):
        _fake, store = fake_vault
        store[("7449813913", "google-draas")] = '{"a":1}'
        mod = _load_script()

        rc = mod.migrate(execute=True)

        assert rc == 0
        assert ("ndr-7449813913", "google-draas") in store
        assert ("7449813913", "google-draas") not in store
        assert store[("ndr-7449813913", "google-draas")] == '{"a":1}'

    def test_users_with_no_raw_id_data_are_left_alone(self, fake_vault):
        _fake, store = fake_vault
        store[("ndr-7449813913", "google-draas")] = '{"a":1}'
        mod = _load_script()

        rc = mod.migrate(execute=True)

        assert rc == 0
        assert store == {("ndr-7449813913", "google-draas"): '{"a":1}'}


class TestConflict:
    def test_service_under_both_keys_is_reported_and_never_touched(self, fake_vault):
        _fake, store = fake_vault
        store[("7449813913", "vocab")] = "raw-copy"
        store[("ndr-7449813913", "vocab")] = "canonical-copy"
        mod = _load_script()

        rc = mod.migrate(execute=True)

        # A conflict is not an error exit code -- it's a "needs manual review"
        # signal, distinct from an actual write failure.
        assert rc == 0
        # Neither copy touched.
        assert store[("7449813913", "vocab")] == "raw-copy"
        assert store[("ndr-7449813913", "vocab")] == "canonical-copy"

    def test_conflict_on_one_service_does_not_block_clean_migration_of_another(self, fake_vault):
        _fake, store = fake_vault
        store[("7449813913", "vocab")] = "raw-copy"
        store[("ndr-7449813913", "vocab")] = "canonical-copy"
        store[("7449813913", "google-draas")] = '{"a":1}'
        mod = _load_script()

        mod.migrate(execute=True)

        # Conflict left alone...
        assert store[("7449813913", "vocab")] == "raw-copy"
        assert store[("ndr-7449813913", "vocab")] == "canonical-copy"
        # ...but the clean one still migrates.
        assert ("ndr-7449813913", "google-draas") in store
        assert ("7449813913", "google-draas") not in store


class TestMultipleUsers:
    def test_only_configured_users_are_considered(self, fake_vault):
        _fake, store = fake_vault
        store[("9999999999", "google")] = "unrelated-user-data"
        mod = _load_script()

        rc = mod.migrate(execute=True)

        assert rc == 0
        # Untouched -- 9999999999 isn't in KNOWN_USERS.
        assert store == {("9999999999", "google"): "unrelated-user-data"}
