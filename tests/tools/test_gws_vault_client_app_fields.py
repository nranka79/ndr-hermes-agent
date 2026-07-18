"""Tests for gws_vault_client.add_identity()'s app-field kwargs
(gbrain_home/phone/contacts_sheet_id) -- confirms the client only includes
them in the wire payload when explicitly provided, matching the existing
name/role/permissions contract."""

from unittest.mock import MagicMock

import pytest

import tools.gws_vault_client as vault_module


@pytest.fixture(autouse=True)
def _capture_send_recv(monkeypatch):
    captured = {}

    def fake_send_recv(payload):
        captured["payload"] = payload
        return {"ok": True, "identity": {}}

    monkeypatch.setattr(vault_module, "_send_recv", fake_send_recv)
    return captured


def test_app_fields_included_when_provided(_capture_send_recv):
    vault_module.add_identity(
        "user1", "email", "user1@example.com",
        gbrain_home="/data/hermes/users/user1",
        phone="+911234567890",
        contacts_sheet_id="sheet-1",
    )
    payload = _capture_send_recv["payload"]
    assert payload["gbrain_home"] == "/data/hermes/users/user1"
    assert payload["phone"] == "+911234567890"
    assert payload["contacts_sheet_id"] == "sheet-1"


def test_app_fields_omitted_when_not_provided(_capture_send_recv):
    vault_module.add_identity("user1", "email", "user1@example.com")
    payload = _capture_send_recv["payload"]
    assert "gbrain_home" not in payload
    assert "phone" not in payload
    assert "contacts_sheet_id" not in payload


def test_existing_name_role_permissions_contract_unaffected(_capture_send_recv):
    vault_module.add_identity(
        "user1", "email", "user1@example.com",
        name="Test", role="employee", permissions={"manage_users": False},
    )
    payload = _capture_send_recv["payload"]
    assert payload["name"] == "Test"
    assert payload["role"] == "employee"
    assert payload["permissions"] == {"manage_users": False}
    assert "gbrain_home" not in payload


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
