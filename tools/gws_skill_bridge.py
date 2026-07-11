"""
GWS Skill Bridge — wraps the bundled google-workspace skill's Gmail/Calendar/
Drive/Sheets/Docs/Contacts operations with Hermes' own vault-backed,
multi-account credentials (tools.gws_auth), instead of the skill's own
single-account ~/.hermes/google_token.json (which is never set up in this
deployment — see CLAUDE.md).

Design
------
- The skill file (skills/productivity/google-workspace/scripts/google_api.py)
  is loaded via importlib WITHOUT being modified on disk. Its only credential
  entry point, get_credentials(), is monkeypatched at the module-object level
  to pull from tools.gws_auth.load_credentials() (vault, session-scoped,
  multi-account) instead of reading a local token file. Every one of the
  skill's operation functions calls build_service(api, version), which calls
  get_credentials() — Python resolves that name from the module's __dict__ at
  CALL time, so the patch applies to all of them uniformly, with zero edits
  to the skill file itself.

- gmail_send / gmail_reply (the skill's own real-send functions) are
  PERMANENTLY BLOCKED in call() below and can never be dispatched through
  this bridge. "Sending" email through this bridge always means creating a
  Gmail draft (draft_create / draft_reply_create) — Hermes must never
  autonomously deliver an email to a recipient. See hermes-data/SOUL.md,
  "Email Sending — HARD RULE".

- draft_create/get/list/delete, gmail_trash, gmail_thread_get, and
  gmail_batch_modify are NOT present in the underlying skill at all — they're
  implemented here directly against the Gmail API, in the same code shape as
  the skill's own functions (take an `args` namespace, print() a JSON result).

Usage (via execute_code, after calling gws_resolve_account to pick service_name):

    from tools.gws_skill_bridge import call
    print(call("draft_create", service_name="google-draas",
                to="x@y.com", subject="Hi", body="Hello",
                cc="", from_header="", html=False))

    print(call("gmail_search", service_name="google-draas",
                query="from:ranjit@example.com", max=5))
"""

from __future__ import annotations

import base64
import contextlib
import importlib.util
import io
import json
import types
from pathlib import Path
from email.mime.text import MIMEText

from hermes_constants import get_hermes_home
from tools import gws_auth

_SKILL_RELATIVE_PATH = "skills/productivity/google-workspace/scripts/google_api.py"


def _skill_path() -> Path:
    return get_hermes_home() / _SKILL_RELATIVE_PATH


def _load_skill_module():
    """Load google_api.py as a module WITHOUT running its main()/CLI parser
    (that only executes under `if __name__ == "__main__"`, which is false
    when the file is imported like this). File on disk is never modified."""
    path = _skill_path()
    spec = importlib.util.spec_from_file_location("_gws_skill_api", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_skill = _load_skill_module()

# Mutated by call() immediately before each dispatch. Safe across concurrent
# requests because each execute_code invocation runs in its own fresh
# sandboxed subprocess — there is no shared long-lived process state here.
_current_service_name = "google-draas"


def _vault_credentials():
    """Replaces the skill's own get_credentials(). Sources from Hermes'
    gws-vault, keyed by the CURRENT session's user (HERMES_SESSION_USER_ID,
    same env var gws_auth.py reads everywhere else) + whichever service_name
    call() set for this dispatch."""
    telegram_id = gws_auth._current_telegram_id()
    return gws_auth.load_credentials(telegram_id, _current_service_name)


# The entire patch. Every one of the skill's 25 operation functions calls
# build_service(api, version) -> get_credentials() — this one assignment
# redirects all of them, with zero edits to the skill file on disk.
_skill.get_credentials = _vault_credentials


def _build_service(api: str, version: str):
    """Same choke point as the skill's own build_service(), used by our own
    operations below (drafts, trash, threads, batchModify)."""
    from googleapiclient.discovery import build
    return build(api, version, credentials=_vault_credentials())


# ---------------------------------------------------------------------------
# Safety: gmail_send / gmail_reply are the skill's own real-send functions.
# They are NEVER reachable through call(), under any operation name.
# "Sending" email through this bridge always means creating a draft.
# ---------------------------------------------------------------------------
_BLOCKED_OPERATIONS = frozenset({"gmail_send", "gmail_reply"})

_BLOCKED_MESSAGE = (
    "'{op}' is permanently disabled in tools/gws_skill_bridge.py — Hermes "
    "must never send email directly (see hermes-data/SOUL.md, 'Email Sending "
    "— HARD RULE'). Use 'draft_create' for a new email or 'draft_reply_create' "
    "for a reply — both create a Gmail draft only. The human sends it "
    "themselves from their own Drafts folder."
)


# ---------------------------------------------------------------------------
# Our own operations — not present in the underlying skill at all.
# Same code shape/style as the skill's functions: take an `args` namespace,
# print() a JSON result (not return — call()'s stdout capture handles this,
# see module docstring and the Design section above).
# ---------------------------------------------------------------------------

def draft_create(args):
    """Create a new Gmail draft. NEVER sends. This is the sole 'compose a
    new email' operation exposed by this bridge."""
    service = _build_service("gmail", "v1")
    message = MIMEText(args.body, "html" if getattr(args, "html", False) else "plain")
    message["To"] = args.to
    message["Subject"] = args.subject
    if getattr(args, "cc", ""):
        message["Cc"] = args.cc
    if getattr(args, "from_header", ""):
        message["From"] = args.from_header

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft_body = {"message": {"raw": raw}}

    result = service.users().drafts().create(userId="me", body=draft_body).execute()
    msg = result.get("message", {})
    print(json.dumps({
        "status": "draft_created",
        "draft_id": result["id"],
        "message_id": msg.get("id", ""),
        "threadId": msg.get("threadId", ""),
    }, indent=2))


def draft_reply_create(args):
    """Create a Gmail draft that replies to an existing message, correctly
    threaded (In-Reply-To/References/Subject 'Re:'). NEVER sends."""
    service = _build_service("gmail", "v1")
    original = service.users().messages().get(
        userId="me", id=args.message_id, format="metadata",
        metadataHeaders=["From", "Subject", "Message-ID"],
    ).execute()
    headers = {
        h["name"].lower(): h["value"]
        for h in original.get("payload", {}).get("headers", [])
        if h.get("name")
    }

    subject = headers.get("subject", "")
    if not subject.startswith("Re:"):
        subject = f"Re: {subject}"

    message = MIMEText(args.body, "html" if getattr(args, "html", False) else "plain")
    message["To"] = getattr(args, "to", "") or headers.get("from", "")
    message["Subject"] = subject
    if getattr(args, "cc", ""):
        message["Cc"] = args.cc
    if getattr(args, "from_header", ""):
        message["From"] = args.from_header
    if headers.get("message-id"):
        message["In-Reply-To"] = headers["message-id"]
        message["References"] = headers["message-id"]

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    draft_body = {"message": {"raw": raw, "threadId": original["threadId"]}}

    result = service.users().drafts().create(userId="me", body=draft_body).execute()
    msg = result.get("message", {})
    print(json.dumps({
        "status": "draft_created",
        "draft_id": result["id"],
        "message_id": msg.get("id", ""),
        "threadId": msg.get("threadId", ""),
    }, indent=2))


def draft_get(args):
    """Read a single draft's full content."""
    service = _build_service("gmail", "v1")
    draft = service.users().drafts().get(userId="me", id=args.draft_id, format="full").execute()
    msg = draft.get("message", {})
    headers = {
        h["name"].lower(): h["value"]
        for h in msg.get("payload", {}).get("headers", [])
        if h.get("name")
    }
    print(json.dumps({
        "draft_id": draft["id"],
        "message_id": msg.get("id", ""),
        "threadId": msg.get("threadId", ""),
        "to": headers.get("to", ""),
        "subject": headers.get("subject", ""),
        "body": _skill._extract_message_body(msg),
    }, indent=2, ensure_ascii=False))


def draft_list(args):
    """List drafts (optionally filtered by Gmail search syntax via args.query)."""
    service = _build_service("gmail", "v1")
    result = service.users().drafts().list(
        userId="me",
        maxResults=getattr(args, "max", 20),
        q=(getattr(args, "query", "") or None),
    ).execute()
    drafts = result.get("drafts", [])
    output = [
        {
            "draft_id": d["id"],
            "message_id": d.get("message", {}).get("id", ""),
            "threadId": d.get("message", {}).get("threadId", ""),
        }
        for d in drafts
    ]
    print(json.dumps(output, indent=2))


def draft_delete(args):
    """Delete a draft permanently (does not touch the thread it was replying to)."""
    service = _build_service("gmail", "v1")
    service.users().drafts().delete(userId="me", id=args.draft_id).execute()
    print(json.dumps({"status": "deleted", "draft_id": args.draft_id}))


def gmail_trash(args):
    """Move a message to Trash (recoverable for ~30 days, standard Gmail behavior)."""
    service = _build_service("gmail", "v1")
    result = service.users().messages().trash(userId="me", id=args.message_id).execute()
    print(json.dumps({
        "status": "trashed",
        "message_id": result.get("id", args.message_id),
        "labels": result.get("labelIds", []),
    }, indent=2))


def gmail_thread_get(args):
    """Read a full thread (all messages in it), not just one message."""
    service = _build_service("gmail", "v1")
    thread = service.users().threads().get(userId="me", id=args.thread_id, format="full").execute()
    messages = []
    for msg in thread.get("messages", []):
        headers = {
            h["name"].lower(): h["value"]
            for h in msg.get("payload", {}).get("headers", [])
            if h.get("name")
        }
        messages.append({
            "id": msg["id"],
            "from": headers.get("from", ""),
            "to": headers.get("to", ""),
            "date": headers.get("date", ""),
            "subject": headers.get("subject", ""),
            "body": _skill._extract_message_body(msg),
        })
    print(json.dumps({"threadId": thread["id"], "messages": messages}, indent=2, ensure_ascii=False))


def gmail_batch_modify(args):
    """Add/remove labels across multiple messages in one call.
    args.message_ids: list[str]. args.add_labels / args.remove_labels:
    comma-separated label ID strings (same convention as the skill's
    gmail_modify)."""
    body = {"ids": args.message_ids}
    if getattr(args, "add_labels", ""):
        body["addLabelIds"] = args.add_labels.split(",")
    if getattr(args, "remove_labels", ""):
        body["removeLabelIds"] = args.remove_labels.split(",")

    service = _build_service("gmail", "v1")
    service.users().messages().batchModify(userId="me", body=body).execute()
    print(json.dumps({"status": "modified", "count": len(args.message_ids)}, indent=2))


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

_OWN_OPERATIONS = {
    "draft_create": draft_create,
    "draft_reply_create": draft_reply_create,
    "draft_get": draft_get,
    "draft_list": draft_list,
    "draft_delete": draft_delete,
    "gmail_trash": gmail_trash,
    "gmail_thread_get": gmail_thread_get,
    "gmail_batch_modify": gmail_batch_modify,
}


def call(operation: str, service_name: str = "google-draas", **kwargs) -> str:
    """Dispatch one operation by name — either one of our own (above) or one
    of the underlying skill's 23 non-send operations (gmail_search, gmail_get,
    gmail_labels, gmail_modify, calendar_list/create/delete, drive_search/
    get/upload/download/create_folder/share/delete, contacts_list, sheets_
    get/update/append/create, docs_get/create/append) — all running against
    Hermes' vault credentials, not the skill's own local token file.

    Returns the JSON text the operation printed (skill functions print, they
    don't return a value — see module docstring, "Design").
    """
    global _current_service_name

    if operation in _BLOCKED_OPERATIONS:
        raise PermissionError(_BLOCKED_MESSAGE.format(op=operation))

    func = _OWN_OPERATIONS.get(operation)
    if func is None:
        func = getattr(_skill, operation, None)
        if func is None or not callable(func):
            raise AttributeError(f"Unknown gws_skill_bridge operation: {operation!r}")

    _current_service_name = service_name
    args = types.SimpleNamespace(**kwargs)

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        func(args)
    return buf.getvalue()
