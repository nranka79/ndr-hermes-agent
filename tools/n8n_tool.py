#!/usr/bin/env python3
"""
N8N Tool — routes Google Workspace operations through N8N workflows.

Each N8N workflow uses its own stored OAuth credential (predefinedCredentialType),
so Hermes does NOT need to generate or pass Google tokens. N8N manages token
refresh automatically.

Architecture:
  Hermes → POST JSON payload to N8N webhook
  N8N workflow → authenticates with stored Google credential → calls Google API
  N8N workflow → returns {success: true, data: {...}}

All executions visible in N8N UI at https://transcribe.ahfl.in

Registered as: n8n_tool
Toolset: google_workspace

Services and webhook paths:
  sheets   → hermes-sheets   (Google Sheets API — range-based)
  gmail    → hermes-gmail    (Gmail)
  drive    → hermes-drive    (Google Drive — list/get/create metadata)
  calendar → hermes-calendar (Google Calendar)
  docs     → hermes-docs     (Google Docs)
  tasks    → hermes-tasks    (Google Tasks)
  contacts → hermes-contacts (Google People/Contacts API)

NOTE: Binary file uploads to Drive bypass N8N — use drive_upload_tool or
      google_workspace_manager for that (google-api-python-client handles
      multipart uploads; N8N HTTP Request cannot carry binary payloads).
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


# ── Core dispatcher ───────────────────────────────────────────────────────────

def _call_n8n(service: str, payload: dict) -> str:
    """
    POST payload to the N8N webhook for the given service.
    N8N uses its stored Google OAuth credential — no token needed from Hermes.
    """
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
        "N8N authenticates with stored Google OAuth credentials — no token management needed. "
        "All executions logged in N8N UI at https://transcribe.ahfl.in\n\n"

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
        toolset="general",
        check_fn=_check_n8n_available,
        description="Route Google Workspace calls through N8N (Sheets/Gmail/Drive/Calendar/Docs/Tasks/Contacts).",
    )


_register()
