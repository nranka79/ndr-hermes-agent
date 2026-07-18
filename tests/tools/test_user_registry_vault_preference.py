"""Tests for tools._user_registry.find_user_by_identity()'s vault/file merge
of app-specific fields (2026-07-18 users.json consolidation).

Core property: once a user's gbrain_home/phone/contacts_sheet_id exist in
vault (post-migration), those values win over whatever's in the file
registry. Users not yet migrated (vault doesn't have the field) still get
their value from the file -- no regression for the transition period.
Identities/permissions merge behavior (pre-existing, untouched) is pinned
too, to catch any accidental disturbance.
"""

from unittest.mock import MagicMock

import pytest

import tools.gws_vault_client as vault_module
import tools._user_registry as registry_module


@pytest.fixture(autouse=True)
def _clear_registry_cache():
    """load_user_registry() is mtime-cached at module scope -- reset
    between tests so monkeypatched file registries aren't stale."""
    registry_module._registry_cache = None
    registry_module._registry_mtime = 0.0
    yield
    registry_module._registry_cache = None
    registry_module._registry_mtime = 0.0


def _stub_file_registry(monkeypatch, data):
    monkeypatch.setattr(registry_module, "load_user_registry", lambda: data)


class TestVaultFieldsPreferredWhenPresent:
    def test_vault_gbrain_home_wins_over_file(self, monkeypatch):
        _stub_file_registry(monkeypatch, {
            "user@example.com": {
                "email": "user@example.com",
                "gbrain_home": "/data/hermes/users/STALE-FILE-PATH",
                "identities": {"telegram": ["1234567890"]},
            }
        })
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="user@example.com"))
        monkeypatch.setattr(
            vault_module, "get_identity",
            MagicMock(return_value={"gbrain_home": "/data/hermes/users/CURRENT-VAULT-PATH"}),
        )

        _, rec = registry_module.find_user_by_identity("telegram", "1234567890")
        assert rec["gbrain_home"] == "/data/hermes/users/CURRENT-VAULT-PATH"

    def test_vault_phone_and_contacts_sheet_id_win_over_file(self, monkeypatch):
        _stub_file_registry(monkeypatch, {
            "user@example.com": {
                "email": "user@example.com",
                "phone": "+91-OLD-NUMBER",
                "contacts_sheet_id": "OLD-SHEET",
                "identities": {"telegram": ["1234567890"]},
            }
        })
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="user@example.com"))
        monkeypatch.setattr(
            vault_module, "get_identity",
            MagicMock(return_value={"phone": "+91-NEW-NUMBER", "contacts_sheet_id": "NEW-SHEET"}),
        )

        _, rec = registry_module.find_user_by_identity("telegram", "1234567890")
        assert rec["phone"] == "+91-NEW-NUMBER"
        assert rec["contacts_sheet_id"] == "NEW-SHEET"


class TestFileFallbackForUnmigratedUsers:
    def test_file_value_used_when_vault_lacks_the_field(self, monkeypatch):
        """A user not yet migrated: vault's identity record exists (has
        name/role) but doesn't have gbrain_home/phone yet -- file's values
        must still be used, not silently dropped."""
        _stub_file_registry(monkeypatch, {
            "user@example.com": {
                "email": "user@example.com",
                "gbrain_home": "/data/hermes/users/only-in-file",
                "phone": "+91-only-in-file",
                "identities": {"telegram": ["1234567890"]},
            }
        })
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="user@example.com"))
        monkeypatch.setattr(
            vault_module, "get_identity",
            MagicMock(return_value={"name": "User", "role": "employee"}),  # no app fields
        )

        _, rec = registry_module.find_user_by_identity("telegram", "1234567890")
        assert rec["gbrain_home"] == "/data/hermes/users/only-in-file"
        assert rec["phone"] == "+91-only-in-file"


class TestPreExistingMergeBehaviorUnaffected:
    """identities/permissions merge logic predates this change -- confirm
    it's untouched."""

    def test_identities_and_permissions_merge_unchanged(self, monkeypatch):
        _stub_file_registry(monkeypatch, {
            "user@example.com": {
                "email": "user@example.com",
                "identities": {"telegram": ["1234567890"], "email": ["user@example.com"]},
                "permissions": {"manage_users": True},
            }
        })
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="user@example.com"))
        monkeypatch.setattr(
            vault_module, "get_identity",
            MagicMock(return_value={"identities": {}, "permissions": {}}),
        )

        _, rec = registry_module.find_user_by_identity("telegram", "1234567890")
        # File's identities/permissions win when present (setdefault
        # semantics, pre-existing behavior) -- vault's empty dicts here
        # must not clobber them.
        assert rec["identities"]["email"] == ["user@example.com"]
        assert rec["permissions"] == {"manage_users": True}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
