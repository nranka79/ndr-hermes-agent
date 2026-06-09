#!/usr/bin/env python3
"""
N8N Tool — Google Workspace operations with per-user OAuth isolation.

Architecture — two modes depending on whether a Telegram session user is active:

  PER-USER MODE (HERMES_SESSION_USER_ID is set):
    1. Calls hermes-token-for-request N8N webhook → gets short-lived access_token
    2. Sets token in session context (_shared._session_gws_token)
    3. Calls Google APIs directly in Python using that token
    Token NEVER stored to disk; lives in RAM for duration of one API call.

  ORG-LEVEL MODE (no session user):
    Proxies through N8N webhooks which use stored ndr@draas.com credential.

All N8N executions visible at https://transcribe.ahfl.in

Registered as: n8n_tool
Toolset: google_workspace

Services: sheets | gmail | calendar | docs | tasks | contacts
(Drive: use google_workspace_manager — binary uploads not supported here)
"""

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Dict

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

_N8N_BASE_URL = os.environ.get("HERMES_N8N_BASE_URL", "https://transcribe.ahfl.in")

_SERVICE_PATHS: Dict[str, str] = {
    "sheets":   "hermes-sheets",
    "gmail":    "hermes-gmail",
    # drive is intentionally absent — all Drive operations (read AND write)
    # go through google_workspace_manager which handles binary uploads correctly.
    # n8n hermes-drive can only handle JSON metadata; it cannot receive binary
    # file bytes from Railway's local filesystem, so uploads always end up 0 bytes.
    "calendar": "hermes-calendar",
    "docs":     "hermes-docs",
    "tasks":    "hermes-tasks",
    "contacts": "hermes-contacts",
}


# ── Per-user token broker ─────────────────────────────────────────────────────

def _fetch_and_set_user_token(telegram_id: str) -> dict:
    """
    Call hermes-token-for-request webhook → get access_token → set in session context.
    Returns {} on success.
    Returns {error, needs_auth, auth_url, message} if user hasn't authorized yet.
    Refresh tokens stay in n8n DB — only the short-lived access_token leaves n8n.
    """
    from tools.gws._shared import set_session_gws_token

    url = f"{_N8N_BASE_URL}/webhook/hermes-token-for-request"
    data = json.dumps({"telegram_id": telegram_id}).encode("utf-8")
    req = urllib.request.Request(
        url, data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return {"error": f"Token broker HTTP {e.code}: {e.read().decode('utf-8', errors='replace')[:300]}"}
    except Exception as e:
        return {"error": f"Token broker unreachable: {e}"}

    if result.get("needs_auth"):
        auth_url = result.get("auth_url", "")
        return {
            "error": "google_auth_required",
            "needs_auth": True,
            "auth_url": auth_url,
            "message": (
                f"Google Workspace access not yet authorized. "
                f"Send user this link to authorize: {auth_url}"
                if auth_url else
                "Google auth required. No auth URL returned — contact admin."
            ),
        }

    access_token = result.get("access_token")
    if not access_token:
        return {"error": "n8n token broker returned neither access_token nor needs_auth — check workflow logs"}

    set_session_gws_token(access_token)
    return {}


# ── Per-user direct Google API dispatch ───────────────────────────────────────

def _call_gws_direct(service: str, payload: dict) -> str:
    """Route to the appropriate Python GWS function using the session-scoped token."""
    try:
        from tools.gws._shared import build_service_for_session
        op = payload.get("operation", "")

        if service == "gmail":
            svc = build_service_for_session("gmail", "v1")
            return _gmail_direct(svc, op, payload)
        elif service == "calendar":
            svc = build_service_for_session("calendar", "v3")
            return _calendar_direct(svc, op, payload)
        elif service == "sheets":
            svc = build_service_for_session("sheets", "v4")
            return _sheets_direct(svc, op, payload)
        elif service == "contacts":
            svc = build_service_for_session("people", "v1")
            return _contacts_direct(svc, op, payload)
        elif service == "tasks":
            svc = build_service_for_session("tasks", "v1")
            return _tasks_direct(svc, op, payload)
        elif service == "docs":
            svc = build_service_for_session("docs", "v1")
            return _docs_direct(svc, op, payload)
        else:
            return json.dumps({"error": f"Per-user mode not supported for service '{service}'"})
    except Exception as e:
        logger.error("GWS direct dispatch error [%s/%s]: %s", service, payload.get("operation"), e)
        return json.dumps({"error": str(e)})


def _gmail_direct(svc, op: str, p: dict) -> str:
    if op == "messages.list":
        res = svc.users().messages().list(
            userId="me", q=p.get("query", ""), maxResults=p.get("maxResults", 10)
        ).execute()
    elif op == "messages.get":
        res = svc.users().messages().get(
            userId="me", id=p["messageId"], format="full"
        ).execute()
    elif op == "threads.get":
        res = svc.users().threads().get(
            userId="me", id=p["threadId"], format="full"
        ).execute()
    elif op in ("messages.send", "messages.send-reply"):
        import base64
        from email.mime.text import MIMEText
        msg = MIMEText(p.get("body", ""), "plain", "utf-8")
        msg["To"] = p.get("to", "")
        msg["Subject"] = p.get("subject", "")
        if p.get("cc"):
            msg["Cc"] = p["cc"]
        if p.get("replyTo"):
            msg["In-Reply-To"] = p["replyTo"]
            msg["References"] = p["replyTo"]
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        body: dict = {"raw": raw}
        if p.get("threadId"):
            body["threadId"] = p["threadId"]
        res = svc.users().messages().send(userId="me", body=body).execute()
    else:
        return json.dumps({"error": f"Gmail op '{op}' not implemented in per-user mode"})
    return json.dumps(res, ensure_ascii=False)


def _calendar_direct(svc, op: str, p: dict) -> str:
    cal_id = p.get("calendarId", "primary")
    if op == "events.list":
        kwargs: dict = {"calendarId": cal_id, "maxResults": p.get("maxResults", 20)}
        if p.get("timeMin"):
            kwargs["timeMin"] = p["timeMin"]
        if p.get("timeMax"):
            kwargs["timeMax"] = p["timeMax"]
        if p.get("query"):
            kwargs["q"] = p["query"]
        res = svc.events().list(**kwargs).execute()
    elif op == "events.get":
        res = svc.events().get(calendarId=cal_id, eventId=p["eventId"]).execute()
    elif op == "events.create":
        body = {
            "summary": p.get("summary", ""),
            "start": {"dateTime": p["start"], "timeZone": p.get("timeZone", "Asia/Kolkata")},
            "end":   {"dateTime": p["end"],   "timeZone": p.get("timeZone", "Asia/Kolkata")},
        }
        if p.get("description"):
            body["description"] = p["description"]
        if p.get("location"):
            body["location"] = p["location"]
        if p.get("attendees"):
            body["attendees"] = [{"email": e} for e in p["attendees"]]
        res = svc.events().insert(calendarId=cal_id, body=body).execute()
    elif op == "events.update":
        existing = svc.events().get(calendarId=cal_id, eventId=p["eventId"]).execute()
        existing.update(p.get("updates", {}))
        res = svc.events().update(calendarId=cal_id, eventId=p["eventId"], body=existing).execute()
    elif op == "events.delete":
        svc.events().delete(calendarId=cal_id, eventId=p["eventId"]).execute()
        res = {"status": "deleted", "eventId": p["eventId"]}
    else:
        return json.dumps({"error": f"Calendar op '{op}' not implemented in per-user mode"})
    return json.dumps(res, ensure_ascii=False)


def _sheets_direct(svc, op: str, p: dict) -> str:
    sid = p.get("spreadsheetId", "")
    if not sid:
        return json.dumps({"error": "spreadsheetId required"})
    svc_ss = svc.spreadsheets().values()
    if op == "values.get":
        res = svc_ss.get(spreadsheetId=sid, range=p["range"]).execute()
    elif op == "values.batchGet":
        res = svc_ss.batchGet(spreadsheetId=sid, ranges=p["ranges"]).execute()
    elif op == "values.append":
        res = svc_ss.append(
            spreadsheetId=sid, range=p["range"],
            valueInputOption="USER_ENTERED",
            insertDataOption="INSERT_ROWS",
            body={"values": p["values"]},
        ).execute()
    elif op == "values.update":
        res = svc_ss.update(
            spreadsheetId=sid, range=p["range"],
            valueInputOption="USER_ENTERED",
            body={"values": p["values"]},
        ).execute()
    else:
        return json.dumps({"error": f"Sheets op '{op}' not implemented in per-user mode"})
    return json.dumps(res, ensure_ascii=False)


def _contacts_direct(svc, op: str, p: dict) -> str:
    if op == "contacts.list":
        res = svc.people().connections().list(
            resourceName="people/me",
            personFields="names,emailAddresses,phoneNumbers,organizations",
            pageSize=p.get("maxResults", 50),
        ).execute()
    elif op == "contacts.search":
        res = svc.people().searchContacts(
            query=p.get("query", ""),
            readMask="names,emailAddresses,phoneNumbers,organizations",
        ).execute()
    elif op == "contacts.get":
        res = svc.people().get(
            resourceName=p["resourceName"],
            personFields="names,emailAddresses,phoneNumbers,organizations",
        ).execute()
    elif op == "contacts.create":
        res = svc.people().createContact(body=p["contactBody"]).execute()
    else:
        return json.dumps({"error": f"Contacts op '{op}' not implemented in per-user mode"})
    return json.dumps(res, ensure_ascii=False)


def _tasks_direct(svc, op: str, p: dict) -> str:
    tl = p.get("tasklistId", "@default")
    if op == "tasklists.list":
        res = svc.tasklists().list().execute()
    elif op == "tasks.list":
        res = svc.tasks().list(tasklist=tl, maxResults=p.get("maxResults", 20)).execute()
    elif op == "tasks.get":
        res = svc.tasks().get(tasklist=tl, task=p["taskId"]).execute()
    elif op == "tasks.create":
        body = {"title": p.get("title", "")}
        if p.get("notes"):
            body["notes"] = p["notes"]
        if p.get("due"):
            body["due"] = p["due"]
        res = svc.tasks().insert(tasklist=tl, body=body).execute()
    elif op == "tasks.update":
        existing = svc.tasks().get(tasklist=tl, task=p["taskId"]).execute()
        for k in ("title", "notes", "status", "due"):
            if p.get(k):
                existing[k] = p[k]
        res = svc.tasks().update(tasklist=tl, task=p["taskId"], body=existing).execute()
    elif op == "tasks.delete":
        svc.tasks().delete(tasklist=tl, task=p["taskId"]).execute()
        res = {"status": "deleted", "taskId": p["taskId"]}
    elif op == "tasks.complete":
        existing = svc.tasks().get(tasklist=tl, task=p["taskId"]).execute()
        existing["status"] = "completed"
        res = svc.tasks().update(tasklist=tl, task=p["taskId"], body=existing).execute()
    else:
        return json.dumps({"error": f"Tasks op '{op}' not implemented in per-user mode"})
    return json.dumps(res, ensure_ascii=False)


def _docs_direct(svc, op: str, p: dict) -> str:
    if op == "documents.get":
        res = svc.documents().get(documentId=p["documentId"]).execute()
    elif op == "documents.create":
        res = svc.documents().create(body={"title": p.get("title", "Untitled")}).execute()
    elif op == "documents.append":
        requests = [{"insertText": {"location": {"index": 1}, "text": p.get("content", "")}}]
        res = svc.documents().batchUpdate(
            documentId=p["documentId"], body={"requests": requests}
        ).execute()
    else:
        return json.dumps({"error": f"Docs op '{op}' not implemented in per-user mode"})
    return json.dumps(res, ensure_ascii=False)


# ── N8N webhook (org-level) ───────────────────────────────────────────────────

def _call_n8n_webhook(service: str, payload: dict) -> str:
    """POST to N8N webhook for org-level operations (ndr@draas.com credential)."""
    path = _SERVICE_PATHS.get(service)
    if path is None:
        return json.dumps({"error": f"Unknown service '{service}'. Valid: {list(_SERVICE_PATHS)}"})

    url = f"{_N8N_BASE_URL}/webhook/{path}"
    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            parsed = json.loads(body)
            if isinstance(parsed, dict) and parsed.get("success"):
                return json.dumps(parsed.get("data", parsed), ensure_ascii=False)
            return body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        logger.error("N8N %s HTTP %d: %s", service, e.code, err_body[:500])
        return json.dumps({"error": f"N8N workflow returned HTTP {e.code}", "detail": err_body[:500]})
    except urllib.error.URLError as e:
        logger.error("N8N %s connection error: %s", service, e.reason)
        return json.dumps({"error": f"Could not reach N8N: {e.reason}"})
    except Exception as e:
        logger.error("N8N %s unexpected error: %s", service, e)
        return json.dumps({"error": str(e)})


# ── Core dispatcher ───────────────────────────────────────────────────────────

def _call_n8n(service: str, payload: dict) -> str:
    """
    Route a GWS operation.

    Per-user session (HERMES_SESSION_USER_ID set):
      → fetch access_token from n8n token broker
      → call Google API directly in Python (no n8n proxy needed)

    Org-level (no session user):
      → proxy through n8n webhook (uses stored ndr@draas.com credential)
    """
    path = _SERVICE_PATHS.get(service)
    if path is None:
        return json.dumps({"error": f"Unknown service '{service}'. Valid: {list(_SERVICE_PATHS)}"})

    session_user_id = os.environ.get("HERMES_SESSION_USER_ID", "")

    if session_user_id:
        # Per-user: get short-lived token from n8n, call Google directly
        token_err = _fetch_and_set_user_token(session_user_id)
        if token_err:
            return json.dumps(token_err)
        return _call_gws_direct(service, payload)

    # Org-level: inject telegram identity for logging, proxy through n8n
    user_name = os.environ.get("HERMES_SESSION_USER_NAME", "")
    if user_name:
        payload = {**payload, "telegram_username": user_name}
    return _call_n8n_webhook(service, payload)


# ── Tool handler ──────────────────────────────────────────────────────────────

def _handle_n8n_tool(args: dict, **kwargs) -> str:
    """
    Main handler called by the tool registry.

    Required args:
      service   : sheets | gmail | drive | calendar | docs | tasks | contacts
      operation : service-specific operation string

    Optional:
      _user : (reserved for future multi-account routing)
    """
    service = (args.get("service") or "").lower().strip()
    if not service:
        return json.dumps({"error": "Missing required argument: service"})

    operation = (args.get("operation") or "").strip()
    if not operation:
        return json.dumps({"error": "Missing required argument: operation"})

    payload = {k: v for k, v in args.items() if k != "service"}
    return _call_n8n(service, payload)


# ── Tool schema ───────────────────────────────────────────────────────────────

_N8N_TOOL_SCHEMA = {
    "name": "n8n_tool",
    "description": (
        "Routes Google Workspace operations through N8N workflows. "
        "N8N manages per-user OAuth credentials keyed to the caller's Telegram ID — "
        "no token handling needed here. "
        "All executions logged in N8N UI at https://transcribe.ahfl.in\n\n"
        "IMPORTANT: If the response contains needs_auth=true and an auth_url, "
        "relay the auth_url to the user immediately so they can authorize Google access. "
        "Do NOT retry the operation until the user has completed authorization.\n\n"

        "Services: sheets | gmail | calendar | docs | tasks | contacts\n\n"
        "DRIVE: Use google_workspace_manager for ALL Drive operations "
        "(list, get, upload, create, move, share). Do NOT use n8n_tool for Drive.\n\n"

        "SHEETS — values.get (spreadsheetId, range), "
        "values.append (spreadsheetId, range, values), "
        "values.update (spreadsheetId, range, values), "
        "values.batchGet (spreadsheetId, ranges)\n\n"

        "GMAIL — messages.list (query, maxResults), "
        "messages.get (messageId), "
        "threads.get (threadId), "
        "messages.send (to, subject, body, cc?), "
        "messages.send-reply (to, subject, body, replyTo, cc?)\n\n"

        "CALENDAR — events.list (calendarId?, timeMin?, timeMax?, query?, maxResults?), "
        "events.get (calendarId?, eventId), "
        "events.create (calendarId?, summary, start, end, attendees?, description?, location?, timeZone?), "
        "events.update (calendarId?, eventId, updates), "
        "events.delete (calendarId?, eventId)\n\n"

        "DOCS — documents.get (documentId), "
        "documents.create (title), "
        "documents.append (documentId, content)\n\n"

        "TASKS — tasks.list (tasklistId?, maxResults?), "
        "tasks.get (tasklistId?, taskId), "
        "tasks.create (tasklistId?, title, notes?, due?), "
        "tasks.update (tasklistId?, taskId, title?, notes?, status?, due?), "
        "tasks.delete (tasklistId?, taskId), "
        "tasks.complete (tasklistId?, taskId), "
        "tasklists.list\n\n"

        "CONTACTS — contacts.list (maxResults?), "
        "contacts.search (query), "
        "contacts.get (resourceName), "
        "contacts.create (contactBody)"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "enum": ["sheets", "gmail", "calendar", "docs", "tasks", "contacts"],
                "description": "Which Google service to use.",
            },
            "operation": {
                "type": "string",
                "description": "Operation to perform (see tool description for full list per service).",
            },
            # ── Sheets ──
            "spreadsheetId": {"type": "string", "description": "Sheets spreadsheet ID."},
            "range":         {"type": "string", "description": "A1 notation range e.g. 'projects!A:C'."},
            "ranges":        {"type": "array", "items": {"type": "string"}, "description": "Ranges for values.batchGet."},
            "values":        {"type": "array", "items": {"type": "array"}, "description": "2D array for append/update."},
            # ── Gmail ──
            "query":     {"type": "string", "description": "Gmail or Drive search query."},
            "maxResults":{"type": "integer", "description": "Max results to return."},
            "messageId": {"type": "string", "description": "Gmail message ID."},
            "threadId":  {"type": "string", "description": "Gmail thread ID."},
            "replyTo":   {"type": "string", "description": "Message/thread ID to reply to."},
            "to":        {"type": "string", "description": "Recipient email."},
            "cc":        {"type": "string", "description": "CC addresses (comma-separated)."},
            "bcc":       {"type": "string", "description": "BCC addresses (comma-separated)."},
            "subject":   {"type": "string", "description": "Email subject."},
            "body":      {"type": "string", "description": "Email body (plain text)."},
            # ── Calendar ──
            "calendarId":  {"type": "string", "description": "Calendar ID (default: ndr@draas.com)."},
            "eventId":     {"type": "string", "description": "Event ID for get/update/delete."},
            "summary":     {"type": "string", "description": "Event title."},
            "description": {"type": "string", "description": "Event description."},
            "location":    {"type": "string", "description": "Event location."},
            "start":       {"type": "string", "description": "ISO 8601 start datetime."},
            "end":         {"type": "string", "description": "ISO 8601 end datetime."},
            "timeZone":    {"type": "string", "description": "IANA timezone (default: Asia/Kolkata)."},
            "attendees":   {"type": "array",  "items": {"type": "string"}, "description": "Attendee emails."},
            "timeMin":     {"type": "string", "description": "ISO 8601 lower bound for events.list."},
            "timeMax":     {"type": "string", "description": "ISO 8601 upper bound for events.list."},
            "updates":     {"type": "object","description": "Fields to patch for events.update."},
            # ── Docs ──
            "documentId": {"type": "string", "description": "Google Doc ID."},
            "title":      {"type": "string", "description": "Document title for documents.create."},
            "content":    {"type": "string", "description": "Text content to append."},
            # ── Tasks ──
            "tasklistId": {"type": "string", "description": "Task list ID (default: @default)."},
            "taskId":     {"type": "string", "description": "Task ID for get/update/delete."},
            "notes":      {"type": "string", "description": "Task notes/description."},
            "due":        {"type": "string", "description": "Task due date (RFC 3339 datetime)."},
            "status":     {"type": "string", "description": "Task status: needsAction | completed."},
            # ── Contacts ──
            "resourceName": {"type": "string", "description": "People API resource name e.g. people/c12345."},
            "contactBody":  {"type": "object","description": "Contact body for contacts.create."},
            # ── General ──
            "_user": {"type": "string", "description": "(Reserved) Google account to act as."},
        },
        "required": ["service", "operation"],
    },
}


# ── Health check ──────────────────────────────────────────────────────────────

def _check_n8n_available() -> bool:
    try:
        req = urllib.request.Request(
            f"{_N8N_BASE_URL}/healthz",
            headers={"User-Agent": "hermes-healthcheck"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


# ── Registration ──────────────────────────────────────────────────────────────

def _register():
    from tools.registry import registry
    registry.register(
        name="n8n_tool",
        schema=_N8N_TOOL_SCHEMA,
        handler=_handle_n8n_tool,
        toolset="google_workspace",
        check_fn=_check_n8n_available,
        description="Route Google Workspace calls through N8N (Sheets/Gmail/Drive/Calendar/Docs/Tasks/Contacts).",
    )


_register()
