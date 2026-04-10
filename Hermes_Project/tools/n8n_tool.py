#!/usr/bin/env python3
"""
N8N Tool — routes Google Workspace operations through N8N workflows for
traceability, multi-user support, and debuggability.

Architecture:
  1. Hermes generates a fresh Google OAuth2 access token locally
     (reuses load_credentials from tools.gws._shared — same as google_workspace_manager)
  2. Sends the ready-made token in the request body to the N8N webhook
  3. N8N workflow receives token + params, calls Google REST API, returns result
  4. All executions are visible in the N8N UI at https://transcribe.ahfl.in

N8N workflows require NO credential configuration — they receive a pre-authenticated
token from Hermes on every call. This avoids N8N env var access restrictions.

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
             summary="Meeting re: Ranka Amber",
             start="2026-04-10T10:00:00",
             end="2026-04-10T11:00:00")
"""

import json
import logging
import os
import time
import urllib.request
import urllib.error
from typing import Dict

logger = logging.getLogger(__name__)

# ── Configuration ─────────────────────────────────────────────────────────────

_N8N_BASE_URL  = os.environ.get("HERMES_N8N_BASE_URL", "https://transcribe.ahfl.in")
_DEFAULT_USER  = "ndr@draas.com"

_SERVICE_PATHS: Dict[str, str] = {
    "sheets":   "hermes-sheets",
    "gmail":    "hermes-gmail",
    "drive":    "hermes-drive",
    "calendar": "hermes-calendar",
}

# ── Token cache (avoids a refresh call on every tool invocation) ──────────────

_token_cache: Dict[str, tuple] = {}   # user_email → (access_token, expiry_timestamp)


def _get_google_token(user_email: str = _DEFAULT_USER) -> str:
    """
    Return a valid Google OAuth2 access token for user_email.
    Caches tokens for up to 55 minutes (tokens are valid for 60 min).
    Falls back to service account JWT if OAuth2 creds aren't available.
    """
    cached = _token_cache.get(user_email)
    if cached and cached[1] > time.time() + 60:
        return cached[0]

    token = _load_oauth_token(user_email)
    _token_cache[user_email] = (token, time.time() + 3300)  # 55-minute cache
    return token


def _load_oauth_token(user_email: str) -> str:
    """Load from the same OAuth2 credential files used by google_workspace_manager."""
    try:
        from tools.gws._shared import load_credentials
        creds = load_credentials(user_email)
        return creds.token
    except Exception as e:
        logger.warning("OAuth2 load failed (%s), trying SA key fallback: %s", user_email, e)

    return _sa_token_fallback(user_email)


def _sa_token_fallback(subject: str) -> str:
    """
    Generate an access token from the service account key with domain-wide delegation.
    Used when OAuth2 credentials aren't available (e.g. local development).
    """
    import base64

    sa_paths = [
        os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", ""),
        "C:/Users/ruhaan/.config/gcloud/workspace/service-account-key.json",
        "/root/.config/gcloud/workspace/service-account-key.json",
    ]
    sa_key = None
    for p in sa_paths:
        if p and os.path.exists(p):
            with open(p) as f:
                sa_key = json.load(f)
            break

    if sa_key is None:
        raise RuntimeError(
            "No Google credentials found. "
            "Expected OAuth2 file at /data/hermes/oauth-draas.json or "
            "SA key at GOOGLE_APPLICATION_CREDENTIALS."
        )

    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import padding
    except ImportError:
        raise RuntimeError(
            "cryptography package required for SA JWT fallback. "
            "Install it or provision OAuth2 credentials at /data/hermes/oauth-draas.json."
        )

    scope = " ".join([
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/gmail.modify",
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/calendar",
    ])
    now = int(time.time())
    claims = {
        "iss": sa_key["client_email"], "sub": subject, "scope": scope,
        "aud": "https://oauth2.googleapis.com/token", "iat": now, "exp": now + 3600,
    }

    def b64url(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode()

    header_b64  = b64url(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    payload_b64 = b64url(json.dumps(claims).encode())
    signing_input = f"{header_b64}.{payload_b64}"

    private_key = serialization.load_pem_private_key(sa_key["private_key"].encode(), password=None)
    signature   = private_key.sign(signing_input.encode(), padding.PKCS1v15(), hashes.SHA256())
    jwt = f"{signing_input}.{b64url(signature)}"

    import urllib.parse
    data = urllib.parse.urlencode({
        "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
        "assertion": jwt,
    }).encode()
    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token", data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())["access_token"]


# ── Core dispatcher ───────────────────────────────────────────────────────────

def _call_n8n(service: str, payload: dict) -> str:
    """
    POST payload to the N8N webhook for the given service.
    The Google access token is pre-generated here and included in the body.
    N8N workflows just use it — no credential handling needed in N8N.
    """
    path = _SERVICE_PATHS.get(service)
    if path is None:
        return json.dumps({"error": f"Unknown service '{service}'. Valid: {list(_SERVICE_PATHS)}"})

    user_email = payload.get("_user", _DEFAULT_USER)

    try:
        payload["_google_token"] = _get_google_token(user_email)
    except Exception as e:
        return json.dumps({"error": f"Failed to get Google token: {e}"})

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
      service   : "sheets" | "gmail" | "drive" | "calendar"
      operation : service-specific operation (see schema description)

    Optional:
      _user : Google account to act as (default: ndr@draas.com)
    """
    service = (args.get("service") or "").lower().strip()
    if not service:
        return json.dumps({"error": "Missing required argument: service"})

    operation = (args.get("operation") or "").strip()
    if not operation:
        return json.dumps({"error": "Missing required argument: operation"})

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
        "Each call is logged in the N8N UI at https://transcribe.ahfl.in for debugging.\n\n"
        "Services: sheets | gmail | drive | calendar\n\n"
        "Sheets: values.get (spreadsheetId, range), values.append (spreadsheetId, range, values), "
        "values.update (spreadsheetId, range, values), values.batchGet (spreadsheetId, ranges)\n\n"
        "Gmail: messages.list (query, maxResults), messages.get (messageId), "
        "threads.get (threadId), messages.send (to, subject, body, cc?), "
        "messages.send-reply (to, subject, body, threadId, cc?)\n\n"
        "Drive: files.list (query, fields?, pageSize?), files.get (fileId, fields?), "
        "files.create (name, mimeType?, parents?)\n\n"
        "Calendar: events.list (calendarId?, timeMin?, timeMax?, query?, maxResults?), "
        "events.get (calendarId?, eventId), "
        "events.create (calendarId?, summary, start, end, attendees?, description?, location?, timeZone?), "
        "events.update (calendarId?, eventId, updates), events.delete (calendarId?, eventId)"
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
                "description": "Operation to perform (see tool description for full list).",
            },
            "spreadsheetId": {"type": "string", "description": "Sheets spreadsheet ID."},
            "range": {"type": "string", "description": "A1 notation range e.g. 'projects!A:C'."},
            "ranges": {"type": "array", "items": {"type": "string"}, "description": "List of ranges for values.batchGet."},
            "values": {"type": "array", "items": {"type": "array"}, "description": "2D array for values.append / values.update."},
            "query": {"type": "string", "description": "Gmail or Drive search query."},
            "maxResults": {"type": "integer", "description": "Max results to return."},
            "messageId": {"type": "string", "description": "Gmail message ID."},
            "threadId": {"type": "string", "description": "Gmail thread ID."},
            "to": {"type": "string", "description": "Recipient email for send operations."},
            "cc": {"type": "string", "description": "CC addresses (comma-separated)."},
            "bcc": {"type": "string", "description": "BCC addresses (comma-separated)."},
            "subject": {"type": "string", "description": "Email subject."},
            "body": {"type": "string", "description": "Plain text email body."},
            "fileId": {"type": "string", "description": "Drive file ID for files.get."},
            "name": {"type": "string", "description": "File name for files.create."},
            "mimeType": {"type": "string", "description": "MIME type for files.create."},
            "parents": {"type": "array", "items": {"type": "string"}, "description": "Parent folder IDs for files.create."},
            "fields": {"type": "string", "description": "Field mask for Drive responses."},
            "pageSize": {"type": "integer", "description": "Max files for files.list."},
            "calendarId": {"type": "string", "description": "Calendar ID (default: ndr@draas.com)."},
            "eventId": {"type": "string", "description": "Event ID for get/update/delete."},
            "summary": {"type": "string", "description": "Event title for events.create."},
            "description": {"type": "string", "description": "Event description."},
            "start": {"type": "string", "description": "ISO 8601 start datetime."},
            "end": {"type": "string", "description": "ISO 8601 end datetime."},
            "timeZone": {"type": "string", "description": "IANA timezone (default: Asia/Kolkata)."},
            "attendees": {"type": "array", "items": {"type": "string"}, "description": "Attendee email addresses."},
            "location": {"type": "string", "description": "Event location."},
            "timeMin": {"type": "string", "description": "ISO 8601 lower bound for events.list."},
            "timeMax": {"type": "string", "description": "ISO 8601 upper bound for events.list."},
            "updates": {"type": "object", "description": "Fields to patch for events.update."},
            "_user": {"type": "string", "description": "Google account to act as (default: ndr@draas.com)."},
        },
        "required": ["service", "operation"],
    },
}


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
