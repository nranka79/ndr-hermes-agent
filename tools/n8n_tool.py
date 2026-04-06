#!/usr/bin/env python3
"""
N8N Tool — routes Google Workspace operations through N8N workflows for
traceability, multi-user support, and debuggability.

Each service (sheets, gmail, drive, calendar) maps to an N8N webhook workflow
at https://transcribe.ahfl.in. Every request is authenticated with the
HERMES_WEBHOOK_TOKEN and carries the operation + params as JSON.

The N8N workflows authenticate to Google using the service account key
(GOOGLE_SA_KEY env var on the N8N Railway service) and return structured
responses. Execution logs are visible in the N8N UI for debugging.

Registered as: n8n_tool
Toolset: google_workspace

Usage:
    n8n_tool(service="sheets", operation="values.get",
             spreadsheetId="...", range="projects!A:C")

    n8n_tool(service="gmail", operation="messages.list",
             query="from:raghu@example.com", maxResults=10)

    n8n_tool(service="drive", operation="files.list",
             query="name contains 'Ranka Amber'")

    n8n_tool(service="calendar", operation="events.create",
             calendarId="ndr@draas.com",
             summary="Meeting re: Ranka Amber",
             start="2026-04-10T10:00:00",
             end="2026-04-10T11:00:00")
"""

import json
import logging
import os
import urllib.request
import urllib.error
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

_N8N_BASE_URL = os.environ.get("HERMES_N8N_BASE_URL", "https://transcribe.ahfl.in")
_N8N_TOKEN    = os.environ.get("HERMES_N8N_TOKEN",    "hermes-n8n-secret-2024")

# Map service name → webhook path
_SERVICE_PATHS: Dict[str, str] = {
    "sheets":   "hermes-sheets",
    "gmail":    "hermes-gmail",
    "drive":    "hermes-drive",
    "calendar": "hermes-calendar",
}

# Default Google account to impersonate per service
_DEFAULT_USER = "ndr@draas.com"


# ── Core dispatcher ───────────────────────────────────────────────────────────

def _call_n8n(service: str, payload: dict) -> str:
    """
    POST payload to the N8N webhook for the given service.
    Returns the response body as a JSON string (success or error).
    """
    path = _SERVICE_PATHS.get(service)
    if path is None:
        return json.dumps({"error": f"Unknown service '{service}'. Valid: {list(_SERVICE_PATHS)}"})

    url = f"{_N8N_BASE_URL}/webhook/{path}"

    # Inject auth headers into the body so the N8N Code node can read them
    # (N8N webhook nodes surface request headers via $input.first().json._headers)
    payload["_headers"] = {"authorization": f"Bearer {_N8N_TOKEN}"}

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=req_data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8")
            # N8N wraps the Google API response in {success: true, data: {...}}
            parsed = json.loads(body)
            if isinstance(parsed, dict) and parsed.get("success"):
                # Unwrap: return just the Google API data directly
                return json.dumps(parsed.get("data", parsed), ensure_ascii=False)
            return body
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        logger.error("N8N %s HTTP %d: %s", service, e.code, err_body[:500])
        return json.dumps({
            "error": f"N8N workflow returned HTTP {e.code}",
            "detail": err_body[:500],
        })
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
      service   : "sheets" | "gmail" | "drive" | "calendar"
      operation : service-specific operation (see below)

    Sheets operations:
      values.get      — spreadsheetId, range
      values.append   — spreadsheetId, range, values (list of lists)
      values.update   — spreadsheetId, range, values (list of lists)
      values.batchGet — spreadsheetId, ranges (list of range strings)

    Gmail operations:
      messages.list      — query, maxResults (default 10)
      messages.get       — messageId
      threads.get        — threadId
      messages.send      — to, subject, body, cc? (new email)
      messages.send-reply— to, subject, body, threadId, cc? (reply in thread)

    Drive operations:
      files.list   — query, fields?, pageSize?
      files.get    — fileId, fields?
      files.create — name, mimeType?, parents?

    Calendar operations:
      events.list   — calendarId?, timeMin?, timeMax?, query?, maxResults?
      events.get    — calendarId?, eventId
      events.create — calendarId?, summary, start, end, attendees?, description?, location?, timeZone?
      events.update — calendarId?, eventId, updates (dict of fields to change)
      events.delete — calendarId?, eventId

    Optional args (any operation):
      _user : Google account to impersonate (default: ndr@draas.com)
    """
    service = (args.get("service") or "").lower().strip()
    if not service:
        return json.dumps({"error": "Missing required argument: service"})

    operation = (args.get("operation") or "").strip()
    if not operation:
        return json.dumps({"error": "Missing required argument: operation"})

    # Build payload — everything in args except 'service' goes to N8N
    payload = {k: v for k, v in args.items() if k != "service"}
    payload.setdefault("_user", _DEFAULT_USER)

    return _call_n8n(service, payload)


# ── Tool registration ─────────────────────────────────────────────────────────

_N8N_TOOL_SCHEMA = {
    "name": "n8n_tool",
    "description": (
        "Routes Google Workspace operations (Sheets, Gmail, Drive, Calendar) through "
        "N8N workflows for traceability and multi-account support. "
        "Replaces google_workspace_manager for all Google API calls. "
        "Each call is logged in the N8N UI for debugging.\n\n"
        "Services: sheets | gmail | drive | calendar\n\n"
        "Sheets operations: values.get, values.append, values.update, values.batchGet\n"
        "Gmail operations: messages.list, messages.get, threads.get, "
        "messages.send, messages.send-reply\n"
        "Drive operations: files.list, files.get, files.create\n"
        "Calendar operations: events.list, events.get, events.create, "
        "events.update, events.delete"
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "service": {
                "type": "string",
                "enum": ["sheets", "gmail", "drive", "calendar"],
                "description": "Which Google service to use.",
            },
            "operation": {
                "type": "string",
                "description": (
                    "The operation to perform. "
                    "Sheets: values.get | values.append | values.update | values.batchGet. "
                    "Gmail: messages.list | messages.get | threads.get | messages.send | messages.send-reply. "
                    "Drive: files.list | files.get | files.create. "
                    "Calendar: events.list | events.get | events.create | events.update | events.delete."
                ),
            },
            # ── Sheets params ──────────────────────────────────────────────
            "spreadsheetId": {
                "type": "string",
                "description": "Google Sheets spreadsheet ID (for Sheets operations).",
            },
            "range": {
                "type": "string",
                "description": "A1 notation range e.g. 'projects!A:C' (values.get / values.append / values.update).",
            },
            "ranges": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of A1 ranges for values.batchGet.",
            },
            "values": {
                "type": "array",
                "items": {"type": "array"},
                "description": "2D array of values for values.append or values.update.",
            },
            # ── Gmail params ───────────────────────────────────────────────
            "query": {
                "type": "string",
                "description": "Gmail/Drive search query string.",
            },
            "maxResults": {
                "type": "integer",
                "description": "Maximum number of results to return.",
            },
            "messageId": {
                "type": "string",
                "description": "Gmail message ID for messages.get.",
            },
            "threadId": {
                "type": "string",
                "description": "Gmail thread ID for threads.get or messages.send-reply.",
            },
            "to": {
                "type": "string",
                "description": "Recipient email address for messages.send / messages.send-reply.",
            },
            "cc": {
                "type": "string",
                "description": "CC email addresses (comma-separated) for send operations.",
            },
            "bcc": {
                "type": "string",
                "description": "BCC email addresses (comma-separated) for send operations.",
            },
            "subject": {
                "type": "string",
                "description": "Email subject for send operations.",
            },
            "body": {
                "type": "string",
                "description": "Plain text email body for send operations.",
            },
            # ── Drive params ───────────────────────────────────────────────
            "fileId": {
                "type": "string",
                "description": "Drive file ID for files.get.",
            },
            "name": {
                "type": "string",
                "description": "File name for files.create.",
            },
            "mimeType": {
                "type": "string",
                "description": "MIME type for files.create (e.g. 'application/vnd.google-apps.document').",
            },
            "parents": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Parent folder IDs for files.create.",
            },
            "fields": {
                "type": "string",
                "description": "Comma-separated field mask for Drive responses.",
            },
            "pageSize": {
                "type": "integer",
                "description": "Max files to return for files.list.",
            },
            # ── Calendar params ────────────────────────────────────────────
            "calendarId": {
                "type": "string",
                "description": "Calendar ID (default: ndr@draas.com).",
            },
            "eventId": {
                "type": "string",
                "description": "Calendar event ID for events.get / events.update / events.delete.",
            },
            "summary": {
                "type": "string",
                "description": "Event title for events.create.",
            },
            "description": {
                "type": "string",
                "description": "Event description for events.create.",
            },
            "start": {
                "type": "string",
                "description": "ISO 8601 start datetime for events.create (e.g. '2026-04-10T10:00:00').",
            },
            "end": {
                "type": "string",
                "description": "ISO 8601 end datetime for events.create.",
            },
            "timeZone": {
                "type": "string",
                "description": "IANA timezone (default: Asia/Kolkata).",
            },
            "attendees": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of attendee email addresses for events.create.",
            },
            "location": {
                "type": "string",
                "description": "Event location for events.create.",
            },
            "timeMin": {
                "type": "string",
                "description": "ISO 8601 lower bound for events.list.",
            },
            "timeMax": {
                "type": "string",
                "description": "ISO 8601 upper bound for events.list.",
            },
            "updates": {
                "type": "object",
                "description": "Dict of fields to patch for events.update.",
            },
            # ── Auth override ──────────────────────────────────────────────
            "_user": {
                "type": "string",
                "description": "Google account to impersonate (default: ndr@draas.com).",
            },
        },
        "required": ["service", "operation"],
    },
}


def _check_n8n_available() -> bool:
    """Return True if the N8N base URL is reachable."""
    try:
        req = urllib.request.Request(
            f"{_N8N_BASE_URL}/healthz",
            headers={"User-Agent": "hermes-healthcheck"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def _register():
    from tools.registry import registry

    registry.register(
        name="n8n_tool",
        schema=_N8N_TOOL_SCHEMA,
        handler=_handle_n8n_tool,
        toolset="google_workspace",
        check_fn=_check_n8n_available,
        description="Route Google Workspace calls through N8N for traceability.",
    )


_register()
