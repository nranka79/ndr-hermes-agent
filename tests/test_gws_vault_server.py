"""Unit tests for bin_gws_vault_server_live.py's handle_request() -- the
actual gws-vault-server daemon logic (deployed as /usr/local/bin/gws-vault-server
on the Hetzner host, confirmed byte-identical modulo encoding/docstring
examples as of 2026-07-18).

Covers the 2026-07-18 users.json consolidation: add_identity/get_identity
now accept/return gbrain_home, phone, contacts_sheet_id -- app-specific
fields that used to live only in the file registry (tools/_user_registry.py),
migrated here so they get the same admin-secret-gated write protection as
the rest of the identity record.

These were also validated live against a real isolated staging instance of
the actual deployed binary on the Hetzner host before this change shipped
(same socket protocol, real subprocess) -- these tests pin the same
behavior at the unit level so it's covered by the regular test suite going
forward, not just a one-off manual check.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parent.parent / "bin_gws_vault_server_live.py"


@pytest.fixture
def vault_server(tmp_path, monkeypatch):
    """Import a fresh copy of the vault server module, pointed at an
    isolated tmp_path token/identity store. A fresh module instance per
    test avoids cross-test state leakage via the module-level globals."""
    spec = importlib.util.spec_from_file_location("gws_vault_server_under_test", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    mod.VAULT_TOKEN_DIR = str(tmp_path / "tokens")
    mod.VAULT_IDENTITY_DIR = str(tmp_path / "identities")
    mod.VAULT_SECRET = "test-secret"
    Path(mod.VAULT_TOKEN_DIR).mkdir(parents=True, exist_ok=True)
    Path(mod.VAULT_IDENTITY_DIR).mkdir(parents=True, exist_ok=True)
    return mod


class TestAddIdentityAppFields:
    """Core property: gbrain_home/phone/contacts_sheet_id round-trip
    correctly through add_identity/get_identity, same admin-secret gate as
    name/role/permissions."""

    def test_app_fields_stored_on_add(self, vault_server):
        resp = vault_server.handle_request({
            "op": "add_identity",
            "user_id": "testuser",
            "identity_type": "email",
            "identity_value": "testuser@example.com",
            "vault_secret": "test-secret",
            "gbrain_home": "/data/hermes/users/testuser",
            "phone": "+911234567890",
            "contacts_sheet_id": "sheet-abc-123",
        }, peer_uid=1000)

        assert resp["ok"] is True
        assert resp["identity"]["gbrain_home"] == "/data/hermes/users/testuser"
        assert resp["identity"]["phone"] == "+911234567890"
        assert resp["identity"]["contacts_sheet_id"] == "sheet-abc-123"

    def test_app_fields_round_trip_through_get_identity(self, vault_server):
        vault_server.handle_request({
            "op": "add_identity", "user_id": "testuser",
            "identity_type": "email", "identity_value": "testuser@example.com",
            "vault_secret": "test-secret",
            "gbrain_home": "/data/hermes/users/testuser",
            "phone": "+911234567890",
            "contacts_sheet_id": "sheet-abc-123",
        }, peer_uid=1000)

        resp = vault_server.handle_request(
            {"op": "get_identity", "user_id": "testuser", "session_uid": "testuser"},
            peer_uid=1000,
        )
        assert resp["ok"] is True
        assert resp["identity"]["gbrain_home"] == "/data/hermes/users/testuser"
        assert resp["identity"]["phone"] == "+911234567890"
        assert resp["identity"]["contacts_sheet_id"] == "sheet-abc-123"

    def test_app_fields_preserved_across_partial_update(self, vault_server):
        """Linking a new identity type to an existing user (no app fields
        in that request) must not wipe previously-stored app fields --
        same conditional-merge contract as name/role/permissions."""
        vault_server.handle_request({
            "op": "add_identity", "user_id": "testuser",
            "identity_type": "email", "identity_value": "testuser@example.com",
            "vault_secret": "test-secret",
            "gbrain_home": "/data/hermes/users/testuser",
            "phone": "+911234567890",
        }, peer_uid=1000)

        resp = vault_server.handle_request({
            "op": "add_identity", "user_id": "testuser",
            "identity_type": "telegram", "identity_value": "1234567890",
            "vault_secret": "test-secret",
        }, peer_uid=1000)

        assert resp["ok"] is True
        assert resp["identity"]["gbrain_home"] == "/data/hermes/users/testuser"
        assert resp["identity"]["phone"] == "+911234567890"
        assert resp["identity"]["identities"]["telegram"] == ["1234567890"]

    def test_app_fields_omitted_when_never_set(self, vault_server):
        """Adding an identity with no app fields at all must not fabricate
        empty values for them."""
        resp = vault_server.handle_request({
            "op": "add_identity", "user_id": "testuser",
            "identity_type": "email", "identity_value": "testuser@example.com",
            "vault_secret": "test-secret",
        }, peer_uid=1000)
        assert resp["ok"] is True
        assert "gbrain_home" not in resp["identity"]
        assert "phone" not in resp["identity"]
        assert "contacts_sheet_id" not in resp["identity"]

    def test_add_identity_still_requires_valid_secret(self, vault_server):
        """Regression: app fields must not create a bypass of the existing
        admin-secret write gate."""
        resp = vault_server.handle_request({
            "op": "add_identity", "user_id": "testuser",
            "identity_type": "email", "identity_value": "testuser@example.com",
            "vault_secret": "WRONG-SECRET",
            "gbrain_home": "/data/hermes/users/testuser",
        }, peer_uid=1000)
        assert resp["ok"] is False
        assert "Unauthorized" in resp["error"]


class TestExistingBehaviorUnaffected:
    """Regression pins for behavior this change must not touch."""

    def test_resolve_still_works(self, vault_server):
        vault_server.handle_request({
            "op": "add_identity", "user_id": "testuser",
            "identity_type": "telegram", "identity_value": "1234567890",
            "vault_secret": "test-secret",
        }, peer_uid=1000)
        resp = vault_server.handle_request(
            {"op": "resolve", "identity_type": "telegram", "identity_value": "1234567890"},
            peer_uid=1000,
        )
        assert resp == {"ok": True, "user_id": "testuser"}

    def test_cross_user_get_identity_still_rejected(self, vault_server):
        vault_server.handle_request({
            "op": "add_identity", "user_id": "testuser",
            "identity_type": "email", "identity_value": "testuser@example.com",
            "vault_secret": "test-secret",
        }, peer_uid=1000)
        resp = vault_server.handle_request(
            {"op": "get_identity", "user_id": "testuser", "session_uid": "someone-else"},
            peer_uid=1000,
        )
        assert resp["ok"] is False
        assert "Unauthorized" in resp["error"]

    def test_name_role_permissions_unaffected(self, vault_server):
        resp = vault_server.handle_request({
            "op": "add_identity", "user_id": "testuser",
            "identity_type": "email", "identity_value": "testuser@example.com",
            "vault_secret": "test-secret",
            "name": "Test User", "role": "employee",
            "permissions": {"manage_users": False},
        }, peer_uid=1000)
        assert resp["identity"]["name"] == "Test User"
        assert resp["identity"]["role"] == "employee"
        assert resp["identity"]["permissions"] == {"manage_users": False}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
