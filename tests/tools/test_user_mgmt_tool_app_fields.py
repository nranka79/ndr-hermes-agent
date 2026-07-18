"""Tests for manage_user_tool's vault sync of app-specific fields
(gbrain_home, phone) -- part of the 2026-07-18 users.json consolidation.

manage_user_tool still writes users.json (unchanged this phase -- retiring
that write path entirely is a later step), but now ALSO syncs gbrain_home/
phone to vault via tools.gws_vault_client.add_identity(), so
tools._user_registry.find_user_by_identity() can prefer the vault copy.
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


@pytest.fixture
def _store(monkeypatch, tmp_path):
    """Isolated users.json backing store for _load()/_save()."""
    data = {}

    def fake_load():
        return dict(data)

    def fake_save(d):
        data.clear()
        data.update(d)

    monkeypatch.setattr(user_mgmt_tool, "_load", fake_load)
    monkeypatch.setattr(user_mgmt_tool, "_save", fake_save)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    return data


@pytest.fixture(autouse=True)
def _no_real_find_user_by_identity(monkeypatch):
    """add/update look up existing users via find_user_by_identity before
    touching the store -- stub it to 'not found' by default so add()
    doesn't fail on the pre-check. Individual tests override as needed."""
    monkeypatch.setattr(
        "tools._user_registry.find_user_by_identity", lambda *a, **k: (None, None)
    )


class TestAddSyncsAppFieldsToVault:
    def test_add_passes_gbrain_home_and_phone(self, monkeypatch, _store):
        add_identity_mock = MagicMock(return_value={})
        monkeypatch.setattr(vault_module, "add_identity", add_identity_mock)

        result = json.loads(user_mgmt_tool.manage_user_tool({
            "action": "add",
            "telegram_id": "1234567890",
            "email": "newuser@example.com",
            "name": "New User",
            "phone": "+911111111111",
        }))

        assert result.get("success") is True

        # First add_identity call (identity_type="email") carries the
        # profile fields, including gbrain_home/phone.
        first_call_kwargs = add_identity_mock.call_args_list[0].kwargs
        assert first_call_kwargs["identity_type"] == "email"
        assert first_call_kwargs["gbrain_home"] == "/data/hermes/users/newuser"
        assert first_call_kwargs["phone"] == "+911111111111"

    def test_add_without_phone_omits_it(self, monkeypatch, _store):
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

    def test_vault_sync_failure_does_not_fail_the_add(self, monkeypatch, _store):
        """Vault sync is best-effort (logged, not raised) -- users.json is
        still the source of truth for 'did the add succeed' this phase."""
        monkeypatch.setattr(
            vault_module, "add_identity", MagicMock(side_effect=RuntimeError("vault down"))
        )
        result = json.loads(user_mgmt_tool.manage_user_tool({
            "action": "add",
            "telegram_id": "1234567890",
            "email": "newuser3@example.com",
            "name": "New User Three",
        }))
        assert result.get("success") is True


class TestUpdateSyncsPhoneToVault:
    def test_phone_change_triggers_vault_sync_with_phone(self, monkeypatch, _store):
        _store["existing@example.com"] = {
            "email": "existing@example.com", "name": "Existing User", "role": "employee",
            "identities": {"telegram": ["555"], "email": ["existing@example.com"]},
            "permissions": {},
        }
        monkeypatch.setattr(
            "tools._user_registry.find_user_by_identity",
            lambda identity_type, value: (
                ("existing@example.com", _store["existing@example.com"])
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

    def test_unrelated_change_does_not_trigger_vault_sync(self, monkeypatch, _store):
        """Linking a new telegram id alone (no name/role/phone/permissions
        change) shouldn't fire the profile-sync add_identity call at all --
        only the dedicated add_telegram_id sync call."""
        _store["existing2@example.com"] = {
            "email": "existing2@example.com", "name": "Existing User Two", "role": "employee",
            "identities": {"telegram": ["666"], "email": ["existing2@example.com"]},
            "permissions": {},
        }
        monkeypatch.setattr(
            "tools._user_registry.find_user_by_identity",
            lambda identity_type, value: (
                ("existing2@example.com", _store["existing2@example.com"])
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

        # Only the add_telegram_id linking call should have fired -- no
        # call carrying phone/name/role (the profile-sync branch).
        for call in add_identity_mock.call_args_list:
            assert "phone" not in call.kwargs


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
