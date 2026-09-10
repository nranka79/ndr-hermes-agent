"""GWS operations engine — data-only Google Workspace operations.

This module implements Gmail + Drive operations as pure functions that take a
``google.oauth2.Credentials`` object plus operation parameters and return
**data only** (plain JSON-serializable dicts). No function here ever returns a
credential, token, or key — the credential is a function argument that stays in
the calling process.

Two thin tool layers build on top of this engine (both run in the trusted
Hermes gateway process, never in the execute_code sandbox):

  * ``tools/gws_dwd_tools.py`` — domain-wide-delegation tools. The handler
    resolves the acting admin from the *session*, asks the vault for the DWD
    service-account key, impersonates the ``target`` (name/email, may be a
    non-vault Workspace account), executes the engine op, and returns only the
    data. The key is a local variable in the handler and is never part of the
    returned payload.
  * ``tools/gws_ops_tools.py`` — OAuth (session-user) tools. Same ops against
    the session user's own account via their own vault token.

Sending email is intentionally NOT implemented: ``send`` is permanently
blocked for the whole stack (see ``tools/gws_skill_bridge.py`` and SOUL.md).
"Send" always means create a draft.
"""

from __future__ import annotations

import base64
import email.message
import email.mime.multipart
import email.mime.text
import email.utils
import re
from typing import Any, Optional

# Scopes the DWD service account uses when impersonating (mirrors
# tools/gws_admin.py). Gmail.modify, Drive, Docs, Contacts (gdata m8).
GMAIL_SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
DRIVE_SCOPES = ["https://www.googleapis.com/auth/drive"]
DOCS_SCOPES = ["https://www.googleapis.com/auth/documents"]
CONTACTS_SCOPES = ["https://www.google.com/m8/feeds/"]
DEFAULT_SCOPES = sorted(set(GMAIL_SCOPES + DRIVE_SCOPES + DOCS_SCOPES + CONTACTS_SCOPES))

# Cap on the number of search results / drafts returned by default.
DEFAULT_MAX = 25


class GWSDataError(RuntimeError):
    """Raised for user-facing operation errors (safe to show the model)."""


def _build(api: str, version: str, creds) -> Any:
    """Lazily build a googleapiclient service so tests can mock discovery."""
    from googleapiclient.discovery import build
    return build(api, version, credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------------------
# Gmail
# ---------------------------------------------------------------------------

def _subject_of(msg: dict) -> str:
    headers = {h.get("name", "").lower(): h.get("value", "") for h in (msg.get("payload", {}) or {}).get("headers", []) or []}
    return headers.get("subject", "")


def _from_of(msg: dict) -> str:
    headers = {h.get("name", "").lower(): h.get("value", "") for h in (msg.get("payload", {}) or {}).get("headers", []) or []}
    return headers.get("from", "")


def _to_of(msg: dict) -> str:
    headers = {h.get("name", "").lower(): h.get("value", "") for h in (msg.get("payload", {}) or {}).get("headers", []) or []}
    return headers.get("to", "")


def _date_of(msg: dict) -> str:
    headers = {h.get("name", "").lower(): h.get("value", "") for h in (msg.get("payload", {}) or {}).get("headers", []) or []}
    return headers.get("date", "")


def _message_id(msg: dict) -> str:
    return msg.get("id", "")


def _message_summary(msg: dict) -> dict:
    """A compact, data-only summary of a Gmail message (no body/attachments)."""
    return {
        "id": _message_id(msg),
        "threadId": msg.get("threadId", ""),
        "snippet": msg.get("snippet", ""),
        "date": _date_of(msg),
        "from": _from_of(msg),
        "to": _to_of(msg),
        "subject": _subject_of(msg),
        "labelIds": msg.get("labelIds", []),
    }


def _walk_parts(payload: dict):
    """Yield (mime_type, body_dict, is_attachment, filename) for payload parts."""
    mime = payload.get("mimeType", "")
    filename = payload.get("filename", "") or ""
    body = payload.get("body", {}) or {}
    if payload.get("parts"):
        for part in payload.get("parts", []):
            yield from _walk_parts(part)
        return
    yield mime, body, bool(filename), filename


def _decode_body(body: dict) -> str:
    """Best-effort decode of a Gmail message body (base64url)."""
    data = body.get("data", "")
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data.encode("ascii")).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _message_full(msg: dict) -> dict:
    """Data-only full view: headers + decoded text/plain body + attachment list.

    Attachment *content* is never included — only id/filename/mimeType/size —
    so a message read can never bloat context with binary data.
    """
    payload = msg.get("payload", {}) or {}
    text_parts: list[str] = []
    attachments: list[dict] = []
    for mime, body, is_att, filename in _walk_parts(payload):
        if is_att or mime.startswith("image/") or mime in (
            "application/pdf", "application/octet-stream",
        ):
            attachments.append({
                "filename": filename,
                "mimeType": mime,
                "size": body.get("size", 0),
                "attachmentId": body.get("attachmentId", ""),
            })
            continue
        if mime in ("text/plain", ""):
            decoded = _decode_body(body)
            if decoded:
                text_parts.append(decoded)
    return {
        **_message_summary(msg),
        "body": "\n\n".join(text_parts).strip(),
        "attachments": attachments,
    }


def gmail_search(creds, query: str, max_results: int = DEFAULT_MAX) -> dict:
    """Search the target's mailbox. Returns message summaries (id/thread/subject).

    The list endpoint returns only id/threadId/snippet, so each hit is enriched
    with a lightweight metadata fetch to surface From/To/Subject/Date.
    """
    service = _build("gmail", "v1", creds)
    resp = service.users().messages().list(
        userId="me", q=query, maxResults=int(max_results or DEFAULT_MAX),
        fields="messages(id,threadId,snippet)",
    ).execute()
    msgs = resp.get("messages", [])
    summaries = []
    for m in msgs:
        try:
            detail = service.users().messages().get(
                userId="me", id=m.get("id", ""), format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            ).execute()
            summaries.append(_message_summary(detail))
        except Exception:
            summaries.append(_message_summary(m))
    return {"query": query, "count": len(summaries), "messages": summaries}


def gmail_get(creds, message_id: str) -> dict:
    """Fetch one message in full (headers, body, attachment metadata)."""
    service = _build("gmail", "v1", creds)
    msg = service.users().messages().get(userId="me", id=message_id, format="full").execute()
    return _message_full(msg)


def gmail_thread_get(creds, thread_id: str) -> dict:
    """Fetch a thread (conversation) with its messages."""
    service = _build("gmail", "v1", creds)
    thread = service.users().threads().get(userId="me", id=thread_id, format="full").execute()
    return {
        "id": thread.get("id", ""),
        "historyId": thread.get("historyId", ""),
        "count": len(thread.get("messages", [])),
        "messages": [_message_full(m) for m in thread.get("messages", [])],
    }


def gmail_list_labels(creds) -> dict:
    service = _build("gmail", "v1", creds)
    resp = service.users().labels().list(userId="me").execute()
    labels = []
    for label in resp.get("labels", []):
        labels.append({
            "id": label.get("id", ""),
            "name": label.get("name", ""),
            "type": label.get("type", ""),
        })
    return {"count": len(labels), "labels": labels}


def gmail_labels_modify(creds, message_ids: list, add_label_ids: Optional[list] = None,
                        remove_label_ids: Optional[list] = None) -> dict:
    """Add/remove labels on one or more messages."""
    service = _build("gmail", "v1", creds)
    body = {}
    if add_label_ids:
        body["addLabelIds"] = add_label_ids
    if remove_label_ids:
        body["removeLabelIds"] = remove_label_ids
    if not body:
        raise GWSDataError("nothing to do: provide add_label_ids and/or remove_label_ids")
    ids = [str(i) for i in (message_ids or [])]
    if not ids:
        raise GWSDataError("message_ids is required")
    applied = []
    for mid in ids:
        service.users().messages().modify(userId="me", id=mid, body=body).execute()
        applied.append(mid)
    return {"modified": applied, "addLabelIds": add_label_ids or [], "removeLabelIds": remove_label_ids or []}


def gmail_trash(creds, message_id: str) -> dict:
    """Move a message to Trash (this is the stack's 'delete')."""
    service = _build("gmail", "v1", creds)
    service.users().messages().trash(userId="me", id=message_id).execute()
    return {"trashed": message_id}


def gmail_untrash(creds, message_id: str) -> dict:
    service = _build("gmail", "v1", creds)
    service.users().messages().untrash(userId="me", id=message_id).execute()
    return {"untrashed": message_id}


def _build_message(to, subject, body, cc="", bcc="", html=False,
                   in_reply_to="", references="") -> str:
    msg = email.mime.multipart.MIMEMultipart("alternative") if html else email.message.EmailMessage()
    if isinstance(msg, email.mime.multipart.MIMEMultipart):
        part = email.mime.text.MIMEText(body, "html" if html else "plain", "utf-8")
        msg.attach(part)
        msg["to"] = to
        msg["subject"] = subject
        if cc:
            msg["cc"] = cc
        if bcc:
            msg["bcc"] = bcc
    else:
        msg["To"] = to
        msg["Subject"] = subject
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc
        msg.set_content(body, subtype="html" if html else "plain", charset="utf-8")
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
    if references:
        msg["References"] = references
    return msg.as_string()


def gmail_draft_create(creds, to: str, subject: str, body: str, cc: str = "", bcc: str = "",
                       html: bool = False) -> dict:
    """Create a Gmail draft. NEVER sends — this is the only 'compose' path."""
    if not to or not subject or body is None:
        raise GWSDataError("to, subject and body are required")
    raw = _build_message(to, subject, body, cc=cc, bcc=bcc, html=html)
    service = _build("gmail", "v1", creds)
    message = {"raw": base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")}
    draft = service.users().drafts().create(userId="me", body={"message": message}).execute()
    return {"draft_id": draft.get("id", ""), "message_id": draft.get("message", {}).get("id", "")}


def gmail_reply_draft(creds, message_id: str, body: str, html: bool = False,
                      cc: str = "", bcc: str = "") -> dict:
    """Create a reply-as-draft to an existing message. NEVER sends."""
    service = _build("gmail", "v1", creds)
    original = service.users().messages().get(userId="me", id=message_id, format="metadata").execute()
    headers = {h.get("name", "").lower(): h.get("value", "") for h in original.get("payload", {}).get("headers", []) or []}
    subject = headers.get("subject", "")
    if subject and not subject.lower().startswith("re:"):
        subject = f"Re: {subject}"
    in_reply_to = headers.get("message-id", "")
    references = headers.get("references", "") or ""
    if in_reply_to and references:
        references = f"{references} {in_reply_to}".strip()
    elif in_reply_to:
        references = in_reply_to
    to = headers.get("from", "")
    raw = _build_message(to, subject, body, cc=cc, bcc=bcc, html=html,
                         in_reply_to=in_reply_to, references=references)
    message = {"raw": base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii"),
               "threadId": original.get("threadId", "")}
    draft = service.users().drafts().create(userId="me", body={"message": message}).execute()
    return {"draft_id": draft.get("id", ""), "message_id": draft.get("message", {}).get("id", ""),
            "thread_id": original.get("threadId", "")}


def gmail_draft_list(creds, max_results: int = DEFAULT_MAX) -> dict:
    service = _build("gmail", "v1", creds)
    resp = service.users().drafts().list(userId="me", maxResults=int(max_results or DEFAULT_MAX)).execute()
    drafts = []
    for d in resp.get("drafts", []):
        drafts.append({"id": d.get("id", ""), "message_id": d.get("message", {}).get("id", "")})
    return {"count": len(drafts), "drafts": drafts}


def gmail_draft_delete(creds, draft_id: str) -> dict:
    service = _build("gmail", "v1", creds)
    service.users().drafts().delete(userId="me", id=draft_id).execute()
    return {"deleted": draft_id}


# ---------------------------------------------------------------------------
# Drive
# ---------------------------------------------------------------------------

def _file_summary(f: dict) -> dict:
    return {
        "id": f.get("id", ""),
        "name": f.get("name", ""),
        "mimeType": f.get("mimeType", ""),
        "parents": f.get("parents", []),
        "modifiedTime": f.get("modifiedTime", ""),
        "createdTime": f.get("createdTime", ""),
        "size": f.get("size"),
        "owners": [o.get("emailAddress") for o in (f.get("owners") or []) if o.get("emailAddress")],
    }


def drive_list(creds, query: str = "", page_size: int = 100, folder_id: Optional[str] = None) -> dict:
    service = _build("drive", "v3", creds)
    q = query or ""
    if folder_id:
        q = f"'{folder_id}' in parents" + (f" and {q}" if q else "")
    resp = service.files().list(
        q=q, pageSize=int(page_size or 100),
        fields="files(id,name,mimeType,parents,createdTime,modifiedTime,size,owners)",
    ).execute()
    files = [_file_summary(f) for f in resp.get("files", [])]
    return {"query": q, "count": len(files), "files": files}


def drive_get(creds, file_id: str) -> dict:
    service = _build("drive", "v3", creds)
    f = service.files().get(fileId=file_id, fields="*").execute()
    summary = _file_summary(f)
    summary["permissions"] = [
        {"id": p.get("id"), "type": p.get("type"), "role": p.get("role"),
         "emailAddress": p.get("emailAddress"), "displayName": p.get("displayName")}
        for p in (f.get("permissions") or [])
    ]
    return summary


def drive_create_folder(creds, name: str, parent_id: Optional[str] = None) -> dict:
    service = _build("drive", "v3", creds)
    body = {"name": name, "mimeType": "application/vnd.google-apps.folder"}
    if parent_id:
        body["parents"] = [parent_id]
    f = service.files().create(body=body, fields="id,name,mimeType,parents").execute()
    return _file_summary(f)


def drive_create_file(creds, name: str, mime_type: str = "text/plain",
                      content: Optional[str] = None, parent_id: Optional[str] = None) -> dict:
    service = _build("drive", "v3", creds)
    body = {"name": name, "mimeType": mime_type}
    if parent_id:
        body["parents"] = [parent_id]
    if content is None:
        f = service.files().create(body=body, fields="id,name,mimeType,parents").execute()
    else:
        from googleapiclient.http import MediaIoBaseUpload
        from io import BytesIO
        media = MediaIoBaseUpload(BytesIO(content.encode("utf-8")), mimetype=mime_type or "text/plain", resumable=False)
        f = service.files().create(body=body, media_body=media,
                                   fields="id,name,mimeType,parents").execute()
    return _file_summary(f)


def drive_move(creds, file_id: str, add_parents: Optional[list] = None,
               remove_parents: Optional[list] = None) -> dict:
    service = _build("drive", "v3", creds)
    if not add_parents and not remove_parents:
        raise GWSDataError("provide add_parents and/or remove_parents (folder ids)")
    f = service.files().update(
        fileId=file_id,
        addParents=",".join(add_parents or []),
        removeParents=",".join(remove_parents or []),
        fields="id,name,mimeType,parents",
    ).execute()
    return _file_summary(f)


def drive_update(creds, file_id: str, name: Optional[str] = None,
                 content: Optional[str] = None, mime_type: Optional[str] = None) -> dict:
    service = _build("drive", "v3", creds)
    body = {}
    if name is not None:
        body["name"] = name
    if mime_type is not None:
        body["mimeType"] = mime_type
    if content is not None:
        from googleapiclient.http import MediaIoBaseUpload
        from io import BytesIO
        media = MediaIoBaseUpload(
            BytesIO(content.encode("utf-8")),
            mimetype=mime_type or "text/plain", resumable=False,
        )
        f = service.files().update(fileId=file_id, body=body or None, media_body=media,
                                   fields="id,name,mimeType,parents").execute()
    else:
        f = service.files().update(fileId=file_id, body=body or None,
                                   fields="id,name,mimeType,parents").execute()
    return _file_summary(f)


def drive_delete(creds, file_id: str) -> dict:
    service = _build("drive", "v3", creds)
    service.files().delete(fileId=file_id).execute()
    return {"deleted": file_id}


def drive_transfer_ownership(creds, file_id: str, new_owner_email: str) -> dict:
    """Two-step ownership transfer: ensure a permission, then promote to owner."""
    service = _build("drive", "v3", creds)
    perm_id = None
    perms = service.permissions().list(
        fileId=file_id, fields="permissions(id,type,role,emailAddress,displayName)",
    ).execute().get("permissions", [])
    for p in perms:
        if str(p.get("emailAddress", "")).strip().lower() == new_owner_email.strip().lower():
            perm_id = p.get("id")
            break
    if perm_id is None:
        created = service.permissions().create(
            fileId=file_id,
            body={"type": "user", "role": "writer", "emailAddress": new_owner_email},
        ).execute()
        perm_id = created.get("id")
    if not perm_id:
        raise GWSDataError("could not establish a permission for the new owner")
    service.permissions().update(
        fileId=file_id, permissionId=perm_id,
        body={"role": "owner"}, transferOwnership=True,
    ).execute()
    return {"file_id": file_id, "new_owner": new_owner_email}


def drive_permissions_list(creds, file_id: str) -> dict:
    service = _build("drive", "v3", creds)
    perms = service.permissions().list(
        fileId=file_id, fields="permissions(id,type,role,emailAddress,displayName)",
    ).execute().get("permissions", [])
    return {"file_id": file_id, "permissions": perms}


def drive_permissions_add(creds, file_id: str, role: str, email: str,
                          perm_type: str = "user") -> dict:
    service = _build("drive", "v3", creds)
    if role not in ("owner", "writer", "reader", "commenter"):
        raise GWSDataError(f"invalid role: {role!r} (owner/writer/reader/commenter)")
    body = {"type": perm_type, "role": role}
    if perm_type == "user":
        body["emailAddress"] = email
    elif perm_type == "domain":
        body["domain"] = email
    p = service.permissions().create(
        fileId=file_id, body=body,
        fields="id,type,role,emailAddress,domain",
    ).execute()
    return {"file_id": file_id, "permission": p}


def drive_permissions_remove(creds, file_id: str, permission_id: str) -> dict:
    service = _build("drive", "v3", creds)
    service.permissions().delete(fileId=file_id, permissionId=permission_id).execute()
    return {"file_id": file_id, "removed_permission": permission_id}


# ---------------------------------------------------------------------------
# Registry of operation callables + parameter schemas, shared by both tool
# layers so DWD and OAuth tools stay exactly in sync.
# ---------------------------------------------------------------------------

_OP_FUNCS = {
    "gmail_search": (gmail_search, {
        "query": {"type": "string", "description": "Gmail search query (e.g. 'from:piyush@draas.com' or 'has:attachment')"},
        "max_results": {"type": "integer", "description": "Max messages to return (default 25)"},
    }),
    "gmail_get": (gmail_get, {
        "message_id": {"type": "string", "description": "Gmail message id"},
    }),
    "gmail_thread_get": (gmail_thread_get, {
        "thread_id": {"type": "string", "description": "Gmail thread id (a conversation)"},
    }),
    "gmail_list_labels": (gmail_list_labels, {}),
    "gmail_labels_modify": (gmail_labels_modify, {
        "message_ids": {"type": "array", "items": {"type": "string"}, "description": "Message ids to relabel"},
        "add_label_ids": {"type": "array", "items": {"type": "string"}, "description": "Label ids to add"},
        "remove_label_ids": {"type": "array", "items": {"type": "string"}, "description": "Label ids to remove"},
    }),
    "gmail_draft_create": (gmail_draft_create, {
        "to": {"type": "string", "description": "Recipient email"},
        "subject": {"type": "string", "description": "Email subject"},
        "body": {"type": "string", "description": "Email body"},
        "cc": {"type": "string", "description": "Cc addresses"},
        "bcc": {"type": "string", "description": "Bcc addresses"},
        "html": {"type": "boolean", "description": "True when body is HTML (default false)"},
    }),
    "gmail_reply_draft": (gmail_reply_draft, {
        "message_id": {"type": "string", "description": "Message id being replied to"},
        "body": {"type": "string", "description": "Reply body"},
        "cc": {"type": "string", "description": "Cc addresses"},
        "bcc": {"type": "string", "description": "Bcc addresses"},
        "html": {"type": "boolean", "description": "True when body is HTML (default false)"},
    }),
    "gmail_draft_list": (gmail_draft_list, {
        "max_results": {"type": "integer", "description": "Max drafts (default 25)"},
    }),
    "gmail_draft_delete": (gmail_draft_delete, {
        "draft_id": {"type": "string", "description": "Draft id to delete"},
    }),
    "gmail_trash": (gmail_trash, {
        "message_id": {"type": "string", "description": "Message id to move to Trash"},
    }),
    "gmail_untrash": (gmail_untrash, {
        "message_id": {"type": "string", "description": "Message id to restore from Trash"},
    }),
    "drive_list": (drive_list, {
        "query": {"type": "string", "description": "Drive query (e.g. \"name contains 'RERA'\"); empty lists everything"},
        "page_size": {"type": "integer", "description": "Max files (default 100)"},
        "folder_id": {"type": "string", "description": "Restrict to files in this folder id"},
    }),
    "drive_get": (drive_get, {
        "file_id": {"type": "string", "description": "Drive file/folder id"},
    }),
    "drive_create_folder": (drive_create_folder, {
        "name": {"type": "string", "description": "Folder name"},
        "parent_id": {"type": "string", "description": "Optional parent folder id"},
    }),
    "drive_create_file": (drive_create_file, {
        "name": {"type": "string", "description": "File name"},
        "mime_type": {"type": "string", "description": "MIME type (default text/plain)"},
        "content": {"type": "string", "description": "Text content (omit to create an empty file)"},
        "parent_id": {"type": "string", "description": "Optional parent folder id"},
    }),
    "drive_move": (drive_move, {
        "file_id": {"type": "string", "description": "File id to move"},
        "add_parents": {"type": "array", "items": {"type": "string"}, "description": "Folder ids to add as parents"},
        "remove_parents": {"type": "array", "items": {"type": "string"}, "description": "Folder ids to remove from parents"},
    }),
    "drive_update": (drive_update, {
        "file_id": {"type": "string", "description": "File id to update"},
        "name": {"type": "string", "description": "New name"},
        "content": {"type": "string", "description": "New text content"},
        "mime_type": {"type": "string", "description": "New MIME type"},
    }),
    "drive_delete": (drive_delete, {
        "file_id": {"type": "string", "description": "File/folder id to delete"},
    }),
    "drive_transfer_ownership": (drive_transfer_ownership, {
        "file_id": {"type": "string", "description": "File id"},
        "new_owner_email": {"type": "string", "description": "Email of the new owner"},
    }),
    "drive_permissions_list": (drive_permissions_list, {
        "file_id": {"type": "string", "description": "File id"},
    }),
    "drive_permissions_add": (drive_permissions_add, {
        "file_id": {"type": "string", "description": "File id"},
        "role": {"type": "string", "description": "owner/writer/reader/commenter"},
        "email": {"type": "string", "description": "Email (user) or domain (domain share)"},
        "perm_type": {"type": "string", "description": "user (default) or domain"},
    }),
    "drive_permissions_remove": (drive_permissions_remove, {
        "file_id": {"type": "string", "description": "File id"},
        "permission_id": {"type": "string", "description": "Permission id to remove"},
    }),
}

# Operations that are deliberately NOT provided anywhere: send / reply-send.
# Composing is draft-only; the human sends from their own Drafts folder.
BLOCKED_OPERATIONS = frozenset({"gmail_send", "gmail_reply", "gmail_send_as", "gmail_reply_send"})


def op_scopes(op_name: str) -> list:
    """Least-privilege scopes needed for one operation.

    Minting an impersonated credential with ALL DEFAULT_SCOPES at once fails
    if ANY one scope is not authorized for DWD in the Admin console (Google
    rejects the whole grant). Per-operation scoping keeps Drive ops working
    even when Gmail isn't yet DWD-authorized, and is the least-privilege
    posture for the system service-account key.
    """
    if op_name.startswith("gmail"):
        return GMAIL_SCOPES
    if op_name.startswith("drive"):
        return DRIVE_SCOPES
    return DEFAULT_SCOPES


def operation_schema(op_name: str, *, prefix: str, target_param: dict) -> dict:
    """Build an OpenAI tool schema for one engine operation.

    ``target_param`` describes the account selector: the target user name/email
    for DWD tools, or the session user's own service_name for OAuth tools.
    """
    func, params = _OP_FUNCS[op_name]
    doc = (func.__doc__ or "").strip().split("\n")[0]
    description = doc or f"{op_name} (Google Workspace operation)"
    properties = dict(params)
    properties[target_param["name"]] = {"type": "string", "description": target_param["description"]}
    required = [target_param["name"]] if target_param.get("required", False) else []
    for key, meta in params.items():
        if meta.get("required"):
            required.append(key)
    return {
        "name": f"{prefix}{op_name}",
        "description": description,
        "parameters": {
            "type": "object",
            "properties": properties,
            "required": required,
        },
    }


def call_operation(op_name: str, creds, args: dict) -> dict:
    """Execute one engine operation with a credential + args dict."""
    if op_name in BLOCKED_OPERATIONS:
        raise GWSDataError(
            f"'{op_name}' is permanently disabled — Hermes never sends email. "
            "Use the draft operations instead."
        )
    func, _params = _OP_FUNCS[op_name]
    kwargs = {k: v for k, v in args.items() if k in _params}
    return func(creds, **kwargs)