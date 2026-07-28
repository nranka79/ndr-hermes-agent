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

- photos_* operations (Picker API + Photos Library API) are likewise our own,
  implemented via AuthorizedSession raw REST (those endpoints aren't served
  by the discovery client). Post-2025-03-31 Google restriction: pre-existing
  library content is reachable ONLY through a Picker session the USER drives
  in the Google Photos UI; the Library API sees app-created content only, and
  no deletion endpoint exists at all. See the Photos section below for the
  full migration flow. Requires photos scopes in gws_auth.HERMES_GWS_SCOPES —
  accounts authorized before those scopes were added must re-auth once.

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
    return gws_auth.load_credentials(_current_service_name)


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
# Google Photos — Picker API + Library API (raw REST via AuthorizedSession).
#
# Since 2025-03-31 the broad photoslibrary scopes no longer exist: the Library
# API can only see content Hermes itself uploaded, and reading the user's
# pre-existing library is Picker-API-only — the USER selects items in the
# Google Photos UI (pickerUri), then Hermes reads exactly that picked set.
# There is NO deletion endpoint in either API (photos_trash below explains).
#
# Migration flow (e.g. move 2021 photos google-draas -> google-gmail):
#   photos_picker_create -> send pickerUri to user -> user picks & hits Done
#   -> photos_picker_status until mediaItemsSet -> photos_inventory ->
#   photos_quota (destination) -> photos_copy_batch (repeat, advancing skip)
#   -> photos_get on destination ids to verify.
#
# AuthorizedSession (not the discovery client) because the Picker API and the
# Library `uploads` byte endpoint aren't served by googleapiclient discovery.
# Auth still routes through gws_auth/vault exactly like every other op, and
# every function returns printed JSON only — Credentials objects never leave
# function/module scope and API responses carry no token material.
# ---------------------------------------------------------------------------

_PICKER_API = "https://photospicker.googleapis.com/v1"
_LIBRARY_API = "https://photoslibrary.googleapis.com/v1"


def _photos_session(service_name: str = ""):
    """AuthorizedSession for one account — same vault path as everything else."""
    from google.auth.transport.requests import AuthorizedSession
    creds = gws_auth.load_credentials(service_name or _current_service_name)
    return AuthorizedSession(creds)


def _photos_check(resp, op: str):
    """Turn non-2xx into a legible error (403 here almost always means the
    account was authorized before the photos scopes were added — re-auth)."""
    if resp.status_code >= 400:
        raise RuntimeError(f"{op}: HTTP {resp.status_code} {resp.text[:500]}")
    return resp


def _picker_items(session, session_id: str, cap: int | None = None):
    """Yield the user-picked media items of one Picker session, paginated."""
    page_token = None
    yielded = 0
    while True:
        params = {"sessionId": session_id, "pageSize": 100}
        if page_token:
            params["pageToken"] = page_token
        resp = _photos_check(
            session.get(f"{_PICKER_API}/mediaItems", params=params),
            "picker mediaItems.list",
        )
        data = resp.json()
        for item in data.get("mediaItems", []):
            yield item
            yielded += 1
            if cap is not None and yielded >= cap:
                return
        page_token = data.get("nextPageToken")
        if not page_token:
            return


def _download_url(item) -> str:
    """Original-bytes download URL for a picked item. Picker baseUrls are
    short-lived (~60 min) and require the SOURCE account's OAuth header."""
    media_file = item.get("mediaFile", {})
    suffix = "=dv" if item.get("type") == "VIDEO" else "=d"
    return media_file.get("baseUrl", "") + suffix


def _content_length(session, url: str) -> int | None:
    """Byte size via HEAD (falling back to a streamed GET header read) —
    neither Photos API exposes file size in metadata."""
    try:
        resp = session.head(url, allow_redirects=True)
        if resp.status_code < 400 and resp.headers.get("Content-Length"):
            return int(resp.headers["Content-Length"])
    except Exception:
        pass
    try:
        resp = session.get(url, stream=True)
        try:
            if resp.status_code < 400 and resp.headers.get("Content-Length"):
                return int(resp.headers["Content-Length"])
        finally:
            resp.close()
    except Exception:
        pass
    return None


def _copy_one(item, src_session, dst_session, album_id: str = "") -> dict:
    """Server-side copy of ONE picked item: download bytes with SOURCE creds,
    upload with DESTINATION creds (raw uploads endpoint -> batchCreate).
    Both Credentials objects live only inside their AuthorizedSessions."""
    media_file = item.get("mediaFile", {})
    filename = media_file.get("filename", "") or item.get("id", "photo")
    mime_type = media_file.get("mimeType", "application/octet-stream")

    download = _photos_check(
        src_session.get(_download_url(item)), "photos download (source baseUrl)"
    )
    payload = download.content

    upload = _photos_check(
        dst_session.post(
            f"{_LIBRARY_API}/uploads",
            data=payload,
            headers={
                "Content-Type": "application/octet-stream",
                "X-Goog-Upload-Content-Type": mime_type,
                "X-Goog-Upload-Protocol": "raw",
            },
        ),
        "photos uploads (destination)",
    )
    upload_token = upload.text.strip()

    body = {
        "newMediaItems": [
            {"simpleMediaItem": {"uploadToken": upload_token, "fileName": filename}}
        ]
    }
    if album_id:
        body["albumId"] = album_id
    created = _photos_check(
        dst_session.post(f"{_LIBRARY_API}/mediaItems:batchCreate", json=body),
        "mediaItems.batchCreate (destination)",
    )
    result = (created.json().get("newMediaItemResults") or [{}])[0]
    dest_item = result.get("mediaItem", {})
    return {
        "source_id": item.get("id", ""),
        "filename": filename,
        "bytes": len(payload),
        "dest_id": dest_item.get("id", ""),
        "status": "OK" if dest_item else result.get("status", {}).get("message", "FAILED"),
    }


def photos_picker_create(args):
    """Start a Picker session. Send the returned pickerUri to the user — they
    open it logged into the SOURCE account, select photos in the Google Photos
    UI (date search works there), and hit Done. The API forbids programmatic
    selection of pre-existing library content; this is the only entry point."""
    session = _photos_session()
    resp = _photos_check(
        session.post(f"{_PICKER_API}/sessions", json={}), "picker sessions.create"
    )
    data = resp.json()
    print(json.dumps({
        "session_id": data.get("id", ""),
        "pickerUri": data.get("pickerUri", ""),
        "expireTime": data.get("expireTime", ""),
        "note": "User must open pickerUri in a browser logged into the source "
                "account, select photos, and tap Done. Then poll "
                "photos_picker_status until media_items_set is true.",
    }, indent=2))


def photos_picker_status(args):
    """Check whether the user finished picking (mediaItemsSet)."""
    session = _photos_session()
    resp = _photos_check(
        session.get(f"{_PICKER_API}/sessions/{args.session_id}"),
        "picker sessions.get",
    )
    data = resp.json()
    print(json.dumps({
        "session_id": data.get("id", ""),
        "media_items_set": bool(data.get("mediaItemsSet")),
        "expireTime": data.get("expireTime", ""),
    }, indent=2))


def photos_list(args):
    """List the items the user picked in a Picker session (metadata only —
    baseUrls are short-lived and deliberately not surfaced)."""
    session = _photos_session()
    items = [
        {
            "id": item.get("id", ""),
            "type": item.get("type", ""),
            "createTime": item.get("createTime", ""),
            "filename": item.get("mediaFile", {}).get("filename", ""),
            "mimeType": item.get("mediaFile", {}).get("mimeType", ""),
        }
        for item in _picker_items(session, args.session_id, cap=getattr(args, "max", 1000))
    ]
    print(json.dumps({"count": len(items), "mediaItems": items}, indent=2))


def photos_inventory(args):
    """Aggregate view of the picked set: count, type/format mix, date range,
    total bytes (per-item HEAD on the download URL — metadata has no size
    field; pass with_bytes=False to skip that and return instantly)."""
    session = _photos_session()
    with_bytes = getattr(args, "with_bytes", True)
    count = 0
    total_bytes = 0
    bytes_unknown = 0
    by_type: dict = {}
    by_mime: dict = {}
    earliest = latest = ""
    for item in _picker_items(session, args.session_id):
        count += 1
        by_type[item.get("type", "?")] = by_type.get(item.get("type", "?"), 0) + 1
        mime = item.get("mediaFile", {}).get("mimeType", "?")
        by_mime[mime] = by_mime.get(mime, 0) + 1
        created = item.get("createTime", "")
        if created:
            earliest = min(earliest, created) if earliest else created
            latest = max(latest, created) if latest else created
        if with_bytes:
            size = _content_length(session, _download_url(item))
            if size is None:
                bytes_unknown += 1
            else:
                total_bytes += size
    print(json.dumps({
        "count": count,
        "by_type": by_type,
        "by_mime": by_mime,
        "date_range": {"earliest": earliest, "latest": latest},
        "total_bytes": total_bytes if with_bytes else None,
        "total_gb": round(total_bytes / 1e9, 2) if with_bytes else None,
        "bytes_unknown_count": bytes_unknown if with_bytes else None,
    }, indent=2))


def photos_quota(args):
    """Destination storage check via Drive about.get (storageQuota covers the
    whole Google account, Photos included). Uses the drive scope — works even
    before the account is re-authorized for the new photos scopes."""
    service = _build_service("drive", "v3")
    about = service.about().get(fields="storageQuota,user").execute()
    quota = about.get("storageQuota", {})
    limit = int(quota.get("limit", 0) or 0)
    usage = int(quota.get("usage", 0) or 0)
    print(json.dumps({
        "account": about.get("user", {}).get("emailAddress", ""),
        "limit_bytes": limit,
        "usage_bytes": usage,
        "free_bytes": (limit - usage) if limit else None,
        "limit_gb": round(limit / 1e9, 2) if limit else None,
        "usage_gb": round(usage / 1e9, 2),
        "free_gb": round((limit - usage) / 1e9, 2) if limit else None,
    }, indent=2))


def photos_upload(args):
    """Copy ONE picked item from source account to destination account.
    args: session_id, media_item_id, destination (required),
    source (defaults to service_name), album_id (optional, app-created album
    on the destination). The item is re-fetched from the Picker session —
    baseUrls expire, so ids are the only stable handle."""
    source = getattr(args, "source", "") or _current_service_name
    destination = getattr(args, "destination", "")
    if not destination:
        raise ValueError("photos_upload: 'destination' service_name is required")
    src_session = _photos_session(source)
    dst_session = _photos_session(destination)
    for item in _picker_items(src_session, args.session_id):
        if item.get("id") == args.media_item_id:
            result = _copy_one(item, src_session, dst_session,
                               getattr(args, "album_id", ""))
            print(json.dumps(result, indent=2))
            return
    raise ValueError(
        f"photos_upload: media_item_id {args.media_item_id!r} not found in "
        f"picker session {args.session_id!r} (session expired, or item not picked)"
    )


def photos_copy_batch(args):
    """Migration workhorse: copy up to `limit` picked items (after skipping
    `skip`) from source to destination, one at a time, continuing past
    per-item failures. Re-run with next_skip to advance through the set —
    each call is one bounded, user-confirmed batch."""
    source = getattr(args, "source", "") or _current_service_name
    destination = getattr(args, "destination", "")
    if not destination:
        raise ValueError("photos_copy_batch: 'destination' service_name is required")
    limit = getattr(args, "limit", 50)
    skip = getattr(args, "skip", 0)
    album_id = getattr(args, "album_id", "")
    src_session = _photos_session(source)
    dst_session = _photos_session(destination)

    results = []
    succeeded = failed = 0
    total_bytes = 0
    for index, item in enumerate(_picker_items(src_session, args.session_id)):
        if index < skip:
            continue
        if len(results) >= limit:
            break
        try:
            result = _copy_one(item, src_session, dst_session, album_id)
            if result["dest_id"]:
                succeeded += 1
                total_bytes += result["bytes"]
            else:
                failed += 1
        except Exception as exc:
            result = {
                "source_id": item.get("id", ""),
                "filename": item.get("mediaFile", {}).get("filename", ""),
                "status": f"ERROR: {exc}",
                "dest_id": "",
            }
            failed += 1
        results.append(result)
    print(json.dumps({
        "attempted": len(results),
        "succeeded": succeeded,
        "failed": failed,
        "total_bytes": total_bytes,
        "next_skip": skip + len(results),
        "results": results,
    }, indent=2))


def photos_get(args):
    """Fetch one Library mediaItem's metadata. Post-2025 the Library API only
    sees items HERMES uploaded — use this on DESTINATION ids returned by
    photos_upload/photos_copy_batch to verify copies landed. It cannot read
    arbitrary pre-existing library items (403/404 for those)."""
    session = _photos_session()
    resp = _photos_check(
        session.get(f"{_LIBRARY_API}/mediaItems/{args.media_item_id}"),
        "mediaItems.get",
    )
    data = resp.json()
    print(json.dumps({
        "id": data.get("id", ""),
        "filename": data.get("filename", ""),
        "mimeType": data.get("mimeType", ""),
        "creationTime": data.get("mediaMetadata", {}).get("creationTime", ""),
        "productUrl": data.get("productUrl", ""),
    }, indent=2))


def photos_create_album(args):
    """Create an album (app-created, so batchCreate may target it) — e.g. a
    'Migrated from draas 2021' album on the destination account."""
    session = _photos_session()
    resp = _photos_check(
        session.post(f"{_LIBRARY_API}/albums", json={"album": {"title": args.title}}),
        "albums.create",
    )
    data = resp.json()
    print(json.dumps({
        "id": data.get("id", ""),
        "title": data.get("title", ""),
        "productUrl": data.get("productUrl", ""),
    }, indent=2))


def photos_trash(args):
    """Not implementable: the Google Photos APIs have NEVER exposed a trash or
    delete endpoint (before or after the 2025 restrictions). Registered so the
    agent gets this explanation instead of 'unknown operation'."""
    raise RuntimeError(
        "photos_trash is impossible via API — Google Photos has no trash/delete "
        "endpoint (never had one). After verifying copies on the destination "
        "account (photos_get), the user deletes the originals manually in the "
        "Google Photos UI (trash there is recoverable for 60 days)."
    )


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
    "photos_picker_create": photos_picker_create,
    "photos_picker_status": photos_picker_status,
    "photos_list": photos_list,
    "photos_inventory": photos_inventory,
    "photos_quota": photos_quota,
    "photos_upload": photos_upload,
    "photos_copy_batch": photos_copy_batch,
    "photos_get": photos_get,
    "photos_create_album": photos_create_album,
    "photos_trash": photos_trash,
}


def call(operation: str, service_name: str = "google-draas", **kwargs) -> str:
    """Dispatch one operation by name — either one of our own (above: drafts,
    gmail_trash/thread/batch_modify, photos_picker_create/status, photos_list/
    inventory/quota/upload/copy_batch/get/create_album/trash) or one of the
    underlying skill's 23 non-send operations (gmail_search, gmail_get,
    gmail_labels, gmail_modify, calendar_list/create/delete, drive_search/
    get/upload/download/create_folder/share/delete, contacts_list, sheets_
    get/update/append/create, docs_get/create/append) — all running against
    Hermes' vault credentials, not the skill's own local token file.

    Two-account photos ops (photos_upload, photos_copy_batch) take explicit
    source=/destination= service names in kwargs; service_name= remains the
    default/source account for everything else.

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
