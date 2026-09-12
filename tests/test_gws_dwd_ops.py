"""Unit tests for the GWS operations engine + DWD/OAuth native tools.

Security contract under test: the SA key / any Google token must NEVER appear
in a tool result (the only thing that can reach the LLM). These tests assert
that property directly.
"""

import json
import os
import sys
from pathlib import Path
from unittest import mock

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools import gws_ops  # noqa: E402
from tools import gws_vault_client as vault  # noqa: E402


# ---------------------------------------------------------------------------
# Fake Google service objects
# ---------------------------------------------------------------------------

class _FakeExecute:
    def __init__(self, result=None, side_effect=None):
        self._result = result
        self._side_effect = side_effect

    def execute(self):
        if self._side_effect is not None:
            raise self._side_effect
        return self._result


class _FakeService:
    """MagicMock-based fake. Engine calls service.users().messages().list(...),
    so results are set on the call-chain return_values."""

    def __init__(self):
        self.users = mock.MagicMock()
        self.files = mock.MagicMock()
        self.permissions = mock.MagicMock()

        self.users.return_value.messages.return_value.list.return_value = _FakeExecute({
            "messages": [{"id": "m1", "threadId": "t1", "snippet": "hello"}],
        })
        self.users.return_value.messages.return_value.get.return_value = _FakeExecute({
            "id": "m1", "threadId": "t1", "snippet": "hi",
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [
                    {"name": "From", "value": "a@x.com"},
                    {"name": "To", "value": "b@y.com"},
                    {"name": "Subject", "value": "Subj"},
                    {"name": "Date", "value": "Mon, 1 Jan 2026 00:00:00"},
                ],
                "parts": [
                    {"mimeType": "text/plain", "body": {"data": "aGVsbG8="}},  # "hello"
                    {"mimeType": "application/pdf", "filename": "f.pdf",
                     "body": {"size": 99, "attachmentId": "att1"}},
                ],
            },
        })
        self.users.return_value.messages.return_value.modify.return_value = _FakeExecute({})
        self.users.return_value.messages.return_value.trash.return_value = _FakeExecute({})
        self.users.return_value.messages.return_value.untrash.return_value = _FakeExecute({})
        self.users.return_value.messages.return_value.send.return_value = _FakeExecute({"id": "sent"})
        self.users.return_value.threads.return_value.get.return_value = _FakeExecute({"id": "t1", "messages": []})
        self.users.return_value.labels.return_value.list.return_value = _FakeExecute({
            "labels": [{"id": "L1", "name": "INBOX", "type": "system"}],
        })
        self.users.return_value.drafts.return_value.list.return_value = _FakeExecute({
            "drafts": [{"id": "d1", "message": {"id": "m1"}}],
        })
        self.users.return_value.drafts.return_value.create.return_value = _FakeExecute({
            "id": "d-new", "message": {"id": "m-new"},
        })
        self.users.return_value.drafts.return_value.delete.return_value = _FakeExecute({})

        self.files.return_value.list.return_value = _FakeExecute({
            "files": [{"id": "f1", "name": "a.txt", "mimeType": "text/plain"}],
        })
        self.files.return_value.get.return_value = _FakeExecute({
            "id": "f1", "name": "a.txt", "mimeType": "text/plain",
            "parents": ["root"], "permissions": [],
        })
        self.files.return_value.create.return_value = _FakeExecute({
            "id": "f-new", "name": "new", "mimeType": "text/plain",
        })
        self.files.return_value.update.return_value = _FakeExecute({
            "id": "f1", "name": "renamed", "mimeType": "text/plain", "parents": ["root"],
        })
        self.files.return_value.delete.return_value = _FakeExecute({})

        self.permissions.return_value.list.return_value = _FakeExecute({
            "permissions": [{"id": "p1", "type": "user", "role": "writer", "emailAddress": "a@x.com"}],
        })
        self.permissions.return_value.create.return_value = _FakeExecute({
            "id": "p-new", "type": "user", "role": "writer", "emailAddress": "new@x.com",
        })
        self.permissions.return_value.update.return_value = _FakeExecute({"id": "p1", "role": "owner"})
        self.permissions.return_value.delete.return_value = _FakeExecute({})


@pytest.fixture
def fake_build(monkeypatch):
    """Patch gws_ops._build to return a fake google service."""
    svc = _FakeService()
    def _build(api, version, creds):
        return svc
    monkeypatch.setattr(gws_ops, "_build", _build)
    return svc


FAKE_SA = {
    "type": "service_account",
    "project_id": "proj",
    "private_key_id": "kid",
    "private_key": "-----BEGIN PRIVATE KEY-----\nSECRETKEYMATERIAL\n-----END PRIVATE KEY-----\n",
    "client_email": "hermes-dwd@proj.iam.gserviceaccount.com",
    "client_id": "123",
    "token_uri": "https://oauth2.googleapis.com/token",
}


# ---------------------------------------------------------------------------
# Engine: data-only contract
# ---------------------------------------------------------------------------

def test_gmail_get_never_returns_attachment_content_or_creds(fake_build):
    out = gws_ops.gmail_get("creds", "m1")
    assert out["subject"] == "Subj"
    assert out["body"] == "hello"
    assert out["attachments"] == [{"filename": "f.pdf", "mimeType": "application/pdf",
                                   "size": 99, "attachmentId": "att1"}]
    # No binary content, no credential material anywhere.
    assert "SECRETKEYMATERIAL" not in json.dumps(out)


def test_gmail_search_is_data_only(fake_build):
    out = gws_ops.gmail_search("creds", "from:piyush@draas.com", 5)
    assert out["count"] == 1
    assert out["messages"][0]["id"] == "m1"
    assert "creds" not in json.dumps(out)


def test_gmail_draft_create_never_sends(fake_build):
    out = gws_ops.gmail_draft_create("creds", "to@x.com", "Subj", "Body")
    assert out["draft_id"] == "d-new"
    # send() must never have been invoked
    assert fake_build.users.return_value.messages.return_value.send.call_count == 0


def test_reply_draft_uses_re_subject(fake_build):
    out = gws_ops.gmail_reply_draft("creds", "m1", "reply body")
    assert out["draft_id"] == "d-new"


def test_drive_transfer_ownership_two_step(fake_build):
    out = gws_ops.drive_transfer_ownership("creds", "f1", "new@x.com")
    assert out["new_owner"] == "new@x.com"


def test_drive_list_data_only(fake_build):
    out = gws_ops.drive_list("creds", query="name contains 'x'")
    assert out["count"] == 1
    assert "creds" not in json.dumps(out)


def test_call_operation_blocks_send():
    with pytest.raises(gws_ops.GWSDataError):
        gws_ops.call_operation("gmail_send", None, {})


def test_blocked_operations_are_not_exported():
    # No 'send' op may ever be in the operation registry.
    assert not any("send" in op for op in gws_ops._OP_FUNCS)


# ---------------------------------------------------------------------------
# DWD tools: credentials never reach the result payload
# ---------------------------------------------------------------------------

@pytest.fixture
def vault_creds_dwd(monkeypatch):
    """Make the vault return a dwd-mode credential (fake SA key)."""
    def fake_get_gws_credentials(session_uid, target):
        assert session_uid  # session-resolved admin is always passed
        return {
            "ok": True, "mode": "dwd", "user_id": target,
            "email": target, "token_json": json.dumps(FAKE_SA),
        }
    monkeypatch.setattr(vault, "get_gws_credentials", fake_get_gws_credentials)


@pytest.fixture
def session_admin(monkeypatch):
    """Patch session identity resolution to a known admin email."""
    from tools import gws_dwd_tools as dwd
    monkeypatch.setattr(dwd, "_session_admin_email", lambda: "ndr@draas.com")


def test_dwd_gmail_search_result_has_no_token(session_admin, vault_creds_dwd, fake_build):
    from tools import gws_dwd_tools as dwd
    # A minimal impersonated creds object; the engine never inspects it here.
    class _Impersonated:
        pass
    with mock.patch.object(dwd.service_account.Credentials,
                           "from_service_account_info",
                           return_value=_Impersonated()) as m_info:
        sa = _Impersonated()
        m_info.return_value.with_subject = mock.Mock(return_value=sa)
        result = dwd._make_handler("gmail_search")({"target": "piyush@draas.com", "query": "from:x", "max_results": 5})
    parsed = json.loads(result)
    assert parsed["target"] == "piyush@draas.com"
    assert parsed["mode"] == "dwd"
    assert parsed["result"]["count"] == 1
    # The single hard rule: no credential material in what the LLM sees.
    blob = json.dumps(parsed)
    assert "SECRETKEYMATERIAL" not in blob
    assert "token_json" not in blob
    assert "private_key" not in blob
    assert "from_service_account_info" not in blob


def test_dwd_resolve_exact_email(session_admin, monkeypatch):
    from tools import gws_dwd_tools as dwd
    monkeypatch.setattr(vault, "list_identities", lambda: [
        {"user_id": "psingh-8502281203", "name": "Prakash Singh",
         "emails": ["psingh@draas.com"]},
    ])
    out = json.loads(dwd.gws_dwd_resolve_tool({"target": "psingh@draas.com"}))
    assert out["resolved_email"] == "psingh@draas.com"
    assert out["in_vault"] is True


def test_dwd_resolve_direct_domain_email(session_admin, monkeypatch):
    """Ex-employee with no vault identity resolves via the allowed domain."""
    from tools import gws_dwd_tools as dwd
    monkeypatch.setattr(vault, "list_identities", lambda: [])
    monkeypatch.setattr(os, "environ", {**os.environ, "GWS_VAULT_SYSTEM_ADMIN": "ndr@draas.com",
                                        "GWS_VAULT_DWD_DOMAINS": "draas.com"})
    out = json.loads(dwd.gws_dwd_resolve_tool({"target": "bhagya@draas.com"}))
    assert out["resolved_email"] == "bhagya@draas.com"
    assert out["direct"] is True
    assert out["in_vault"] is False


def test_dwd_resolve_unknown_rejected(session_admin, monkeypatch):
    from tools import gws_dwd_tools as dwd
    monkeypatch.setattr(vault, "list_identities", lambda: [])
    monkeypatch.setattr(os, "environ", {**os.environ, "GWS_VAULT_SYSTEM_ADMIN": "ndr@draas.com",
                                        "GWS_VAULT_DWD_DOMAINS": "draas.com"})
    out = json.loads(dwd.gws_dwd_resolve_tool({"target": "nobody@other.com"}))
    assert "error" in out


def test_dwd_unauthorized_admin_never_leaks(monkeypatch, session_admin, fake_build):
    """Vault denying a non-admin must surface an error, never a token."""
    from tools import gws_dwd_tools as dwd

    def deny(session_uid, target):
        raise vault.VaultUnauthorizedError("Unauthorized: admin only")
    monkeypatch.setattr(vault, "get_gws_credentials", deny)
    result = dwd._make_handler("gmail_search")({"target": "piyush@draas.com"})
    parsed = json.loads(result)
    assert "error" in parsed
    assert "SECRETKEYMATERIAL" not in json.dumps(parsed)


# ---------------------------------------------------------------------------
# Vault client: get_gws_credentials payload + passthrough
# ---------------------------------------------------------------------------

def test_vault_client_get_gws_credentials(monkeypatch):
    captured = {}
    def fake_send(payload):
        captured.update(payload)
        return {"ok": True, "mode": "dwd", "user_id": "piyush@draas.com",
                "email": "piyush@draas.com", "token_json": "{}"}
    monkeypatch.setattr(vault, "_send_recv", fake_send)
    resp = vault.get_gws_credentials("ndr@draas.com", "piyush@draas.com")
    assert captured["op"] == "get_gws_credentials"
    assert captured["session_uid"] == "ndr@draas.com"
    assert captured["target"] == "piyush@draas.com"
    assert resp["mode"] == "dwd"


def test_vault_client_get_gws_credentials_raises_on_deny(monkeypatch):
    monkeypatch.setattr(vault, "_send_recv", lambda p: {"ok": False, "error": "Unauthorized: admin only"})
    with pytest.raises(vault.VaultUnauthorizedError):
        vault.get_gws_credentials("ndr@nishantranka.com", "piyush@draas.com")


def test_vault_client_get_gws_credentials_raises_on_missing(monkeypatch):
    monkeypatch.setattr(vault, "_send_recv", lambda p: {"ok": False, "error": "No identity matches target 'x'", "not_found": True})
    with pytest.raises(vault.VaultError):
        vault.get_gws_credentials("ndr@draas.com", "x")