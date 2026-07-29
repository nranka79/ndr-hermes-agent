"""Tests for tools._user_registry.find_user_by_identity() vault-only behavior.

As of 2026-07-29, users.json is eliminated. The vault is the single source
of truth for identity. No file fallback exists.
"""

from unittest.mock import MagicMock

import pytest

import tools.gws_vault_client as vault_module
import tools._user_registry as registry_module


class TestVaultOnlyResolution:
    def test_vault_resolve_returns_record(self, monkeypatch):
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="user@example.com"))
        monkeypatch.setattr(
            vault_module, "get_identity",
            MagicMock(return_value={
                "user_id": "user@example.com",
                "name": "User",
                "role": "employee",
                "gbrain_home": "/data/hermes/users/user",
                "identities": {"telegram": ["1234567890"], "email": ["user@example.com"]},
                "permissions": {"manage_users": False},
            }),
        )

        uid, rec = registry_module.find_user_by_identity("telegram", "1234567890")
        assert uid == "user@example.com"
        assert rec["name"] == "User"
        assert rec["gbrain_home"] == "/data/hermes/users/user"
        assert rec["permissions"]["manage_users"] is False

    def test_vault_resolve_returns_none(self, monkeypatch):
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value=None))

        uid, rec = registry_module.find_user_by_identity("telegram", "9999999999")
        assert uid is None
        assert rec is None

    def test_vault_get_identity_returns_none(self, monkeypatch):
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="user@example.com"))
        monkeypatch.setattr(vault_module, "get_identity", MagicMock(return_value=None))

        uid, rec = registry_module.find_user_by_identity("telegram", "1234567890")
        assert uid is None
        assert rec is None

    def test_vault_unreachable_returns_none(self, monkeypatch):
        monkeypatch.setattr(vault_module, "resolve", MagicMock(side_effect=ConnectionError("vault down")))

        uid, rec = registry_module.find_user_by_identity("telegram", "1234567890")
        assert uid is None
        assert rec is None

    def test_get_user_config_returns_empty_for_unknown(self, monkeypatch):
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value=None))

        cfg = registry_module.get_user_config("9999999999")
        assert cfg == {}

    def test_get_user_config_returns_full_record(self, monkeypatch):
        monkeypatch.setattr(vault_module, "resolve", MagicMock(return_value="user@example.com"))
        monkeypatch.setattr(
            vault_module, "get_identity",
            MagicMock(return_value={
                "user_id": "user@example.com",
                "name": "User",
                "role": "employee",
                "permissions": {"cross_message_allowed": True},
            }),
        )

        cfg = registry_module.get_user_config("1234567890")
        assert cfg["name"] == "User"
        assert cfg["permissions"]["cross_message_allowed"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
