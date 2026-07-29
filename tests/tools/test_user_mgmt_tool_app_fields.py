"""Tests for manage_user_tool's vault-only operations (2026-07-29).

Vault is the single source of truth. No users.json is written.
"""

import json
from unittest.mock import MagicMock

import pytest

import tools.user_mgmt_tool as user_mgmt_tool
import tools.gws_vault_client as vault_module


@pytest.fixture(autouse=True)
def _admin_actor(monkeypatch):
    """manage_user_tool is gated on the caller's own permissions.manage_users
    flag, resolved server-side. Bypass that resolution for these tests --
    it's covered by user_mgmt_tool's own existing admin-gate tests."""
    monkeypatch.setattr(
        user_mgmt_tool, "_require_admin",
        lambda: ("admin@example.com", {"permissions": {"manage_users": True}}),
    )


@pytest.fixture(autouse=True)
def _no_real_find_user_by_identity(monkeypatch):
    """Stub find_user_by_identity to 'not found' by default so add()
    doesn't fail on the pre-check. Individual tests override as needed."""
    monkeypatch.setattr(
        "tools._user_registry.find_user_by_identity", lambda *a, **k: (None, None)
    )


class TestAddSyncsToVault:
    def test_add_passes_gbrain_home_and_phone(self, monkeypatch):
        add_identity_mock = MagicMock(return_value={})
        monkeypatch.setattr(vault_module, "add_identity", add_identity_mock)
        monkeypatch.setattr(vault_module, "delete_user", MagicMock(return_value=True))

        result = json.loads(user_mgmt_tool.manage_user_tool({
            "action": "add",
            "telegram_id": "1234567890",
            "email": "newuser@example.com",
            "name": "New User",
            "phone": "+911111111111",
        }))

        assert result.get("success") is True

        first_call_kwargs = add_identity_mock.call_args_list[0].kwargs
        assert first_call_kwargs["identity_type"] == "email"
        assert first_call_kwargs["gbrain_home"] == "/data/hermes/users/newuser"
        assert first_call_kwargs["phone"] == "+911111111111"

    def test_add_without_phone_omits_it(self, monkeypatch):
        add_identity_mock = MagicMock(return_value={})
        monkeypatch.setattr(vault_module, "add_identity", add_identity_mock)

        user_mgmt_tool.manage_user_tool({
            "action": "add",
            "telegram_id": "1234567890",
            "email": "newuser2@example.com",
            "name": "New User Two",
        })

        first_call_kwargs = add_identity_mock.call_args_list[0].kwargs
        assert first_call_kwargs.get("phone") is None
        assert first_call_kwargs["gbrain_home"] == "/data/hermes/users/newuser2"

    def test_vault_sync_failure_fails_the_add(self, monkeypatch):
        """Vault is the single source of truth -- if vault write fails,
        the add fails."""
        monkeypatch.setattr(
            vault_module, "add_identity", MagicMock(side_effect=RuntimeError("vault down"))
        )
        result = json.loads(user_mgmt_tool.manage_user_tool({
            "action": "add",
            "telegram_id": "1234567890",
            "email": "newuser3@example.com",
            "name": "New User Three",
        }))
        assert result.get("success") is not True
        assert "vault" in result.get("error", "").lower()


class TestUpdateSyncsToVault:
    def _existing(self):
        return {
            "user_id": "existing@example.com",
            "name": "Existing User",
            "role": "employee",
            "identities": {"telegram": ["555"], "email": ["existing@example.com"]},
            "permissions": {},
        }

    def test_phone_change_triggers_vault_sync_with_phone(self, monkeypatch):
        monkeypatch.setattr(
            "tools._user_registry.find_user_by_identity",
            lambda identity_type, value: (
                ("existing@example.com", self._existing())
                if value in ("555", "existing@example.com") else (None, None)
            ),
        )
        add_identity_mock = MagicMock(return_value={})
        monkeypatch.setattr(vault_module, "add_identity", add_identity_mock)

        result = json.loads(user_mgmt_tool.manage_user_tool({
            "action": "update",
            "email": "existing@example.com",
            "phone": "+922222222222",
        }))

        assert result.get("success") is True
        add_identity_mock.assert_called_once()
        kwargs = add_identity_mock.call_args.kwargs
        assert kwargs["phone"] == "+922222222222"

    def test_unrelated_change_does_not_trigger_profile_sync(self, monkeypatch):
        monkeypatch.setattr(
            "tools._user_registry.find_user_by_identity",
            lambda identity_type, value: (
                ("existing2@example.com", self._existing())
                if value in ("666", "existing2@example.com", "777") else (None, None)
            ),
        )
        add_identity_mock = MagicMock(return_value={})
        monkeypatch.setattr(vault_module, "add_identity", add_identity_mock)

        user_mgmt_tool.manage_user_tool({
            "action": "update",
            "email": "existing2@example.com",
            "add_telegram_id": "777",
        })

        for call in add_identity_mock.call_args_list:
            assert "phone" not in call.kwargs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
