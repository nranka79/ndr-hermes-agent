#!/usr/bin/env python3
"""
Google Workspace Manager Tool — direct Python API calls via google-api-python-client.

Replaces the gws CLI subprocess approach which had persistent PATH/binary
installation issues on Railway.  Pure Python: no subprocess, no PATH
dependency, no Rust binary, works on every platform.

Supported command prefix → API mapping:
  gmail   messages list/get/send, threads list, labels list, profile
  drive   files list/get/create/delete, about
  sheets  values get/update/append, spreadsheets get/batchUpdate
  calendar  events list/get/insert, calendars list
  contacts  people list/get  (People API)
  tasks   tasklists list, tasks list/insert/update
  admin   users list/get  (Directory API, admin scope)

Command syntax (same as gws CLI so agent prompts don't change):
  "<service> <resource> <action> [--flag value ...]"

Flags:
  --params    JSON string merged into list/get query params
  --body      JSON string used as request body for create/update
  --spreadsheetId   (sheets)
  --range           (sheets values)
  --valueInputOption (sheets values update, default USER_ENTERED)
  --calendarId      (calendar, default "primary")
  --fileId          (drive)
  --messageId       (gmail)
  --userId          (gmail/admin, default "me")
  --maxResults      integer shortcut (equivalent to --params '{"maxResults":N}')
"""

import json
import logging
import os
import shlex

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Account credential mapping
# ---------------------------------------------------------------------------

ACCOUNTS = {
    "ndr@draas.com":          "/data/hermes/oauth-draas.json",
    "nishantranka@gmail.com": "/data/hermes/oauth-gmail.json",
    "ndr@ahfl.in":            "/data/hermes/oauth-ahfl.json",
}

# Google OAuth2 token endpoint
_TOKEN_URI = "https://oauth2.googleapis.com/token"

# Required scopes — broad enough to cover all services
_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
]


# ---------------------------------------------------------------------------
# Credential loading
# ---------------------------------------------------------------------------

def _load_credentials(account_email: str):
    """Load and return a google.oauth2.credentials.Credentials from the JSON file."""
    try:
        from google.oauth2.credentials import Credentials
        from google.auth.transport.requests import Request as GoogleRequest
    except ImportError:
        raise RuntimeError(
            "google-auth and google-api-python-client are required. "
            "Add them to pyproject.toml and redeploy."
        )

    cred_file = ACCOUNTS.get(account_email)
    if not cred_file:
        raise ValueError(f"Unknown account: {account_email}")
    if not os.path.exists(cred_file):
        raise FileNotFoundError(
            f"Credentials file not found at {cred_file}. "
            "Ensure Railway env vars (DRAAS_OAUTH_*, GMAIL_OAUTH_*, AHFL_OAUTH_*) are set."
        )

    with open(cred_file) as f:
        data = json.load(f)

    creds = Credentials(
        token=None,
        refresh_token=data["refresh_token"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        token_uri=_TOKEN_URI,
        scopes=_SCOPES,
    )
    # Refresh immediately to get a valid access token
    creds.refresh(GoogleRequest())
    return creds


def _build(service: str, version: str, account_email: str):
    """Build and return a Google API service client."""
    from googleapiclient.discovery import build
    creds = _load_credentials(account_email)
    return build(service, version, credentials=creds, cache_discovery=False)


# ---------------------------------------------------------------------------
# Flag parser
# ---------------------------------------------------------------------------

def _parse_flags(argv: list) -> dict:
    """Parse --key value pairs from an argv list. Returns dict."""
    flags = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok.startswith("--"):
            key = tok[2:]
            if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                flags[key] = argv[i + 1]
                i += 2
            else:
                flags[key] = True
                i += 1
        else:
            i += 1
    return flags


def _json_flag(flags: dict, key: str, default=None):
    """Return parsed JSON from a flag, or default."""
    raw = flags.get(key)
    if raw is None:
        return default
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return default


# ---------------------------------------------------------------------------
# Service handlers
# ---------------------------------------------------------------------------

def _handle_gmail(parts: list, account_email: str) -> str:
    """gmail <resource> <action> [flags]"""
    svc = _build("gmail", "v1", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = _parse_flags(parts[2:])
    user_id  = flags.get("userId", "me")
    params   = _json_flag(flags, "params", {})

    if flags.get("maxResults"):
        params.setdefault("maxResults", int(flags["maxResults"]))

    if resource == "messages":
        if action in ("list", ""):
            result = svc.users().messages().list(userId=user_id, **params).execute()
            # Enrich with snippet for readability
            msgs = result.get("messages", [])
            enriched = []
            for m in msgs[:params.get("maxResults", 10)]:
                detail = svc.users().messages().get(
                    userId=user_id, id=m["id"],
                    format="metadata",
                    metadataHeaders=["From", "To", "Subject", "Date"]
                ).execute()
                headers = {h["name"]: h["value"]
                           for h in detail.get("payload", {}).get("headers", [])}
                enriched.append({
                    "id": m["id"],
                    "threadId": m.get("threadId"),
                    "subject": headers.get("Subject", "(no subject)"),
                    "from":    headers.get("From", ""),
                    "to":      headers.get("To", ""),
                    "date":    headers.get("Date", ""),
                    "snippet": detail.get("snippet", ""),
                })
            return json.dumps({"messages": enriched, "resultSizeEstimate": result.get("resultSizeEstimate", 0)}, indent=2)

        if action == "get":
            msg_id = flags.get("id") or flags.get("messageId") or (parts[2] if len(parts) > 2 else None)
            if not msg_id:
                return "Error: --id required for messages get"
            result = svc.users().messages().get(userId=user_id, id=msg_id, **params).execute()
            return json.dumps(result, indent=2)

        if action == "send":
            body = _json_flag(flags, "body", {})
            result = svc.users().messages().send(userId=user_id, body=body).execute()
            return json.dumps(result, indent=2)

    if resource == "threads":
        if action in ("list", ""):
            result = svc.users().threads().list(userId=user_id, **params).execute()
            return json.dumps(result, indent=2)

    if resource == "labels":
        if action in ("list", ""):
            result = svc.users().labels().list(userId=user_id).execute()
            return json.dumps(result, indent=2)

    if resource in ("profile", "users"):
        result = svc.users().getProfile(userId=user_id).execute()
        return json.dumps(result, indent=2)

    return f"Error: unsupported gmail operation '{resource} {action}'"


def _handle_drive(parts: list, account_email: str) -> str:
    """drive <resource> <action> [flags]"""
    svc      = _build("drive", "v3", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = _parse_flags(parts[2:])
    params   = _json_flag(flags, "params", {})

    if resource == "files":
        if action in ("list", ""):
            result = svc.files().list(
                fields="files(id,name,mimeType,modifiedTime,size,owners,webViewLink)",
                **params
            ).execute()
            return json.dumps(result, indent=2)

        if action == "get":
            file_id = flags.get("fileId") or flags.get("id")
            if not file_id:
                return "Error: --fileId required for drive files get"
            result = svc.files().get(fileId=file_id, **params).execute()
            return json.dumps(result, indent=2)

        if action == "delete":
            file_id = flags.get("fileId") or flags.get("id")
            if not file_id:
                return "Error: --fileId required for drive files delete"
            svc.files().delete(fileId=file_id).execute()
            return json.dumps({"deleted": file_id})

    if resource == "about":
        result = svc.about().get(fields="user,storageQuota").execute()
        return json.dumps(result, indent=2)

    return f"Error: unsupported drive operation '{resource} {action}'"


def _handle_sheets(parts: list, account_email: str) -> str:
    """sheets <resource> <action> [flags]"""
    svc      = _build("sheets", "v4", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = _parse_flags(parts[2:])

    sheet_id = flags.get("spreadsheetId") or flags.get("spreadsheet")

    # sheets values get
    if resource == "values":
        if not sheet_id:
            return "Error: --spreadsheetId required"
        rng = flags.get("range", "Sheet1!A:Z")

        if action == "get":
            result = svc.spreadsheets().values().get(
                spreadsheetId=sheet_id, range=rng
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("update", "set"):
            body = _json_flag(flags, "body", {})
            value_input = flags.get("valueInputOption", "USER_ENTERED")
            result = svc.spreadsheets().values().update(
                spreadsheetId=sheet_id, range=rng,
                valueInputOption=value_input, body=body
            ).execute()
            return json.dumps(result, indent=2)

        if action in ("append", "+append"):
            body   = _json_flag(flags, "body", {})
            values = flags.get("values")
            if values and not body:
                body = {"values": [values.split(",")]}
            value_input = flags.get("valueInputOption", "USER_ENTERED")
            result = svc.spreadsheets().values().append(
                spreadsheetId=sheet_id, range=rng,
                valueInputOption=value_input, body=body
            ).execute()
            return json.dumps(result, indent=2)

    # sheets +append shortcut (gws CLI style)
    if resource == "+append":
        rng    = flags.get("range", "Sheet1")
        values = flags.get("values", "")
        body   = {"values": [values.split(",")]} if values else {}
        result = svc.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=rng,
            valueInputOption="USER_ENTERED", body=body
        ).execute()
        return json.dumps(result, indent=2)

    # sheets spreadsheets get / batchUpdate
    if resource == "spreadsheets":
        if not sheet_id:
            return "Error: --spreadsheetId required"

        if action == "get":
            result = svc.spreadsheets().get(spreadsheetId=sheet_id).execute()
            return json.dumps(result, indent=2)

        if action == "batchUpdate":
            body = _json_flag(flags, "body", {})
            result = svc.spreadsheets().batchUpdate(
                spreadsheetId=sheet_id, body=body
            ).execute()
            return json.dumps(result, indent=2)

    return f"Error: unsupported sheets operation '{resource} {action}'"


def _handle_calendar(parts: list, account_email: str) -> str:
    """calendar <resource> <action> [flags]"""
    svc      = _build("calendar", "v3", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = _parse_flags(parts[2:])
    cal_id   = flags.get("calendarId", "primary")
    params   = _json_flag(flags, "params", {})

    if resource == "events":
        if action in ("list", ""):
            result = svc.events().list(calendarId=cal_id, **params).execute()
            return json.dumps(result, indent=2)

        if action == "get":
            event_id = flags.get("eventId") or flags.get("id")
            if not event_id:
                return "Error: --eventId required"
            result = svc.events().get(calendarId=cal_id, eventId=event_id).execute()
            return json.dumps(result, indent=2)

        if action in ("insert", "create"):
            body = _json_flag(flags, "body", {})
            result = svc.events().insert(calendarId=cal_id, body=body).execute()
            return json.dumps(result, indent=2)

    if resource == "calendars":
        if action in ("list", ""):
            result = svc.calendarList().list().execute()
            return json.dumps(result, indent=2)

    return f"Error: unsupported calendar operation '{resource} {action}'"


def _handle_contacts(parts: list, account_email: str) -> str:
    """contacts (People API) <resource> <action> [flags]"""
    svc      = _build("people", "v1", account_email)
    resource = parts[0] if parts else "people"
    action   = parts[1] if len(parts) > 1 else "list"
    flags    = _parse_flags(parts[2:])

    if resource in ("people", "connections", "list", ""):
        person_fields = flags.get("personFields", "names,emailAddresses,phoneNumbers,organizations")
        result = svc.people().connections().list(
            resourceName="people/me",
            personFields=person_fields,
            pageSize=int(flags.get("maxResults", 100))
        ).execute()
        return json.dumps(result, indent=2)

    return f"Error: unsupported contacts operation '{resource} {action}'"


def _handle_tasks(parts: list, account_email: str) -> str:
    """tasks <resource> <action> [flags]"""
    svc      = _build("tasks", "v1", account_email)
    resource = parts[0] if parts else ""
    action   = parts[1] if len(parts) > 1 else ""
    flags    = _parse_flags(parts[2:])

    if resource == "tasklists":
        result = svc.tasklists().list().execute()
        return json.dumps(result, indent=2)

    if resource == "tasks":
        list_id = flags.get("tasklist", "@default")
        if action in ("list", ""):
            result = svc.tasks().list(tasklist=list_id).execute()
            return json.dumps(result, indent=2)
        if action in ("insert", "create"):
            body = _json_flag(flags, "body", {})
            result = svc.tasks().insert(tasklist=list_id, body=body).execute()
            return json.dumps(result, indent=2)

    return f"Error: unsupported tasks operation '{resource} {action}'"


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

_SERVICE_HANDLERS = {
    "gmail":    _handle_gmail,
    "drive":    _handle_drive,
    "sheets":   _handle_sheets,
    "calendar": _handle_calendar,
    "contacts": _handle_contacts,
    "tasks":    _handle_tasks,
}


def _check_gws_available() -> bool:
    """Tool is available when the primary credential file exists and google-auth is installed."""
    if not os.path.exists(ACCOUNTS["ndr@draas.com"]):
        return False
    try:
        import google.oauth2.credentials  # noqa: F401
        import googleapiclient           # noqa: F401
        return True
    except ImportError:
        return False


def _handle_google_workspace_manager(args: dict, **kwargs) -> str:
    """Dispatch a gws-style command to the appropriate Google API."""
    command       = args.get("command", "").strip()
    account_email = args.get("account_email") or "ndr@draas.com"
    extra_args    = args.get("args", "") or ""

    if extra_args:
        command = command + " " + extra_args

    if not command:
        return "Error: 'command' is required."

    try:
        parts = shlex.split(command)
    except ValueError as e:
        return f"Error parsing command: {e}"

    service_name = parts[0].lower() if parts else ""
    handler = _SERVICE_HANDLERS.get(service_name)
    if not handler:
        return (
            f"Error: unknown service '{service_name}'. "
            f"Supported: {', '.join(sorted(_SERVICE_HANDLERS))}"
        )

    try:
        return handler(parts[1:], account_email)
    except Exception as e:
        logger.exception("google_workspace_manager error for command %r", command)
        return f"Error calling Google API ({command}): {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

_GWS_SCHEMA = {
    "name": "google_workspace_manager",
    "description": (
        "Access Google Workspace services: Gmail, Drive, Calendar, Sheets, Contacts, Tasks. "
        "Use the 'command' field with the service name followed by resource and action, "
        "e.g. 'gmail messages list', 'drive files list', "
        "'sheets values get --spreadsheetId ID --range Sheet1!A:Z', "
        "'calendar events list --calendarId primary'. "
        "Mandatory for all Workspace operations — do not write custom Python scripts."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": (
                    "Service + resource + action + flags. Examples:\n"
                    "  gmail messages list --params '{\"maxResults\":20,\"q\":\"is:unread\"}'\n"
                    "  gmail messages list --params '{\"maxResults\":10,\"q\":\"after:2026/03/31\"}'\n"
                    "  gmail messages get --id MESSAGE_ID\n"
                    "  drive files list --params '{\"q\":\"name contains \\\"report\\\"\"}'\n"
                    "  sheets values get --spreadsheetId SHEET_ID --range contacts!A:Z\n"
                    "  sheets values update --spreadsheetId SHEET_ID --range Sheet1!A1 "
                    "--body '{\"values\":[[\"hello\"]]}'\n"
                    "  sheets +append --spreadsheet SHEET_ID --range projects "
                    "--values 'Name,,,,,,Active,'\n"
                    "  calendar events list --calendarId primary --params '{\"maxResults\":10}'\n"
                    "  contacts list\n"
                    "  tasks tasks list"
                ),
            },
            "account_email": {
                "type": "string",
                "enum": ["ndr@draas.com", "nishantranka@gmail.com", "ndr@ahfl.in"],
                "description": (
                    "Account to use. "
                    "ndr@draas.com — default, use for 'my email/drive/calendar/documents' or no qualifier; "
                    "voice variants: draas/drast/drus/dross/DRaaS all map here. "
                    "ndr@ahfl.in — use for 'AHFL email/drive/calendar'. "
                    "nishantranka@gmail.com — use for 'gmail' or 'personal email'. "
                    "Ask if ambiguous."
                ),
            },
            "args": {
                "type": "string",
                "description": "Extra flags appended to command, e.g. '--maxResults 5'.",
            },
        },
        "required": ["command"],
    },
}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

from tools.registry import registry  # noqa: E402

registry.register(
    name="google_workspace_manager",
    toolset="google_workspace",
    schema=_GWS_SCHEMA,
    handler=_handle_google_workspace_manager,
    check_fn=_check_gws_available,
    requires_env=["DRAAS_OAUTH_REFRESH_TOKEN"],
    is_async=False,
    description=_GWS_SCHEMA["description"],
    emoji="📧",
)
