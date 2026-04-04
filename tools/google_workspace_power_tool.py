#!/usr/bin/env python3
"""
Google Workspace Manager Tool — thin facade over tools/gws/ package.

All service logic lives in tools/gws/*.py (modular, one file per service).
This file: availability check, dispatcher, schema, registry.

Supported services:
  gmail     messages / drafts / attachments / threads / labels
  drive     files / permissions / folders / about
  sheets    values / spreadsheets / sheet (tabs) / permissions
  docs      documents / permissions
  calendar  events / calendars / acl
  contacts  people / otherContacts
  tasks     tasks / tasklists
  admin     users / groups / members  (ndr@draas.com Super Admin only)

Accounts:
  ndr@draas.com (PRIMARY/default)
  ndr@ahfl.in
  nishantranka@gmail.com

OAuth re-authorization needed for:
  - docs     → requires scope documents (ndr@draas.com only)
  - admin    → requires scopes admin.directory.user + admin.directory.group (ndr@draas.com only)
"""

import logging
import os
import shlex

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Import all service handlers
# ---------------------------------------------------------------------------

from tools.gws import (
    handle_gmail,
    handle_drive,
    handle_sheets,
    handle_calendar,
    handle_contacts,
    handle_tasks,
    handle_docs,
    handle_admin,
)
from tools.gws._shared import ACCOUNTS

# ---------------------------------------------------------------------------
# Service dispatch table
# ---------------------------------------------------------------------------

_SERVICE_HANDLERS = {
    "gmail":    handle_gmail,
    "drive":    handle_drive,
    "sheets":   handle_sheets,
    "calendar": handle_calendar,
    "contacts": handle_contacts,
    "tasks":    handle_tasks,
    "docs":     handle_docs,
    "admin":    handle_admin,
}


# ---------------------------------------------------------------------------
# Availability check
# ---------------------------------------------------------------------------

def _check_gws_available() -> bool:
    """Tool is available when the primary credential file exists and google-auth is installed."""
    if not os.path.exists(ACCOUNTS["ndr@draas.com"]):
        return False
    try:
        import google.oauth2.credentials   # noqa: F401
        import googleapiclient             # noqa: F401
        return True
    except ImportError:
        return False


# ---------------------------------------------------------------------------
# Main dispatcher
# ---------------------------------------------------------------------------

def _handle_google_workspace_manager(args: dict, **kwargs) -> str:
    """Dispatch a gws-style command string to the appropriate Google API handler."""
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
# Tool schema
# ---------------------------------------------------------------------------

_GWS_SCHEMA = {
    "name": "google_workspace_manager",
    "description": (
        "Access Google Workspace services: Gmail, Drive, Docs, Calendar, Sheets, "
        "Contacts, Tasks, and Admin Directory. "
        "Use the 'command' field with service + resource + action + flags. "
        "MANDATORY for all Workspace operations — never write custom Python scripts. "
        "Default account is ndr@draas.com unless specified."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "command": {
                "type": "string",
                "description": (
                    "Service + resource + action + flags. Examples by service:\n"
                    "# GMAIL — messages\n"
                    "  gmail messages list --params '{\"maxResults\":20,\"q\":\"is:unread\"}'\n"
                    "  gmail messages get --id MSG_ID\n"
                    "  gmail messages send-with-attachment --to alice@example.com --subject \"Hi\" --body \"Hello\" --attachmentPath /tmp/file.pdf\n"
                    "  gmail messages delete --id MSG_ID\n"
                    "  gmail messages modify --id MSG_ID --addLabels '[\"READ\"]'\n"
                    "# GMAIL — drafts\n"
                    "  gmail drafts list\n"
                    "  gmail drafts create --to alice@example.com --subject \"Draft\" --body \"Hello\"\n"
                    "  gmail drafts send --id DRAFT_ID\n"
                    "  gmail drafts delete --id DRAFT_ID\n"
                    "# GMAIL — attachments\n"
                    "  gmail attachments extract --messageId MSG_ID --toDrive\n"
                    "# DRIVE — files\n"
                    "  drive files list --params '{\"q\":\"name contains \\\"report\\\"\"}'\n"
                    "  drive files create --name \"report.txt\" --mimeType text/plain\n"
                    "  drive files create --name \"New Doc\" --googleMime application/vnd.google-apps.document\n"
                    "  drive files update --fileId ID --name \"renamed.txt\"\n"
                    "  drive files copy --fileId ID --name \"Copy\"\n"
                    "  drive files move --fileId ID --folderId FOLDER_ID\n"
                    "  drive files delete --fileId ID\n"
                    "# DRIVE — permissions (sharing)\n"
                    "  drive permissions list --fileId ID\n"
                    "  drive permissions create --fileId ID --email alice@example.com --role writer\n"
                    "  drive permissions update --fileId ID --permissionId PERM_ID --role reader\n"
                    "  drive permissions delete --fileId ID --permissionId PERM_ID\n"
                    "# DOCS — documents\n"
                    "  docs documents create --title \"Meeting Notes\"\n"
                    "  docs documents get --documentId ID\n"
                    "  docs documents batchUpdate --documentId ID --body '{\"requests\":[{\"insertText\":{\"location\":{\"index\":1},\"text\":\"Hello\"}}]}'\n"
                    "  docs documents rename --documentId ID --name \"New Title\"\n"
                    "  docs documents export --documentId ID --mimeType text/plain\n"
                    "  docs permissions create --documentId ID --email alice@example.com --role writer\n"
                    "  docs permissions delete --documentId ID --permissionId PERM_ID\n"
                    "# SHEETS — values\n"
                    "  sheets values get --spreadsheetId SHEET_ID --range contacts!A:Z\n"
                    "  sheets values update --spreadsheetId SHEET_ID --range Sheet1!A1 --body '{\"values\":[[\"hello\"]]}'\n"
                    "  sheets values append --spreadsheetId SHEET_ID --range projects --body '{\"values\":[[\"Name\"]]}'\n"
                    "  sheets values clear --spreadsheetId SHEET_ID --range Sheet1!A1:Z100\n"
                    "  sheets +append --spreadsheet SHEET_ID --range projects --values 'Name,,Active'\n"
                    "# SHEETS — management\n"
                    "  sheets spreadsheets create --title \"Q2 Budget\"\n"
                    "  sheets sheet list --spreadsheetId SHEET_ID\n"
                    "  sheets sheet add --spreadsheetId SHEET_ID --title \"April\"\n"
                    "  sheets sheet delete --spreadsheetId SHEET_ID --sheetId 123456789\n"
                    "  sheets sheet rename --spreadsheetId SHEET_ID --sheetId 123456789 --title \"March\"\n"
                    "  sheets permissions create --spreadsheetId SHEET_ID --email alice@example.com --role writer\n"
                    "# CALENDAR\n"
                    "  calendar events list --calendarId primary --params '{\"maxResults\":10}'\n"
                    "  calendar events create --summary 'Meeting' --start 2026-04-01T09:00:00+05:30 --duration 60 --timeZone Asia/Kolkata\n"
                    "  calendar events update --eventId EVENT_ID --summary 'New Title' --timeZone Asia/Kolkata\n"
                    "  calendar events patch --eventId EVENT_ID --start 2026-04-01T10:00:00+05:30\n"
                    "  calendar events delete --eventId EVENT_ID\n"
                    "  calendar calendars insert --summary 'Work Calendar' --timeZone Asia/Kolkata\n"
                    "  calendar acl create --calendarId ID --email bob@example.com --role reader\n"
                    "  calendar acl delete --calendarId ID --ruleId RULE_ID\n"
                    "# CONTACTS\n"
                    "  contacts list\n"
                    "  contacts people create --name 'Alice Smith' --email alice@example.com\n"
                    "  contacts people search --query 'Alice'\n"
                    "  contacts people delete --resourceName people/ID\n"
                    "# TASKS\n"
                    "  tasks tasklists list\n"
                    "  tasks tasks list\n"
                    "  tasks tasks insert --title 'Review contract'\n"
                    "  tasks tasks complete --id TASK_ID\n"
                    "  tasks tasks delete --id TASK_ID\n"
                    "# ADMIN (ndr@draas.com Super Admin only)\n"
                    "  admin users list --domain draas.com\n"
                    "  admin users create --body '{\"primaryEmail\":\"new@draas.com\",\"name\":{\"givenName\":\"First\",\"familyName\":\"Last\"},\"password\":\"Pass123!\"}'\n"
                    "  admin groups list\n"
                    "  admin members add --groupKey group@draas.com --email user@draas.com --role MEMBER\n"
                ),
            },
            "account_email": {
                "type": "string",
                "enum": ["ndr@draas.com", "nishantranka@gmail.com", "ndr@ahfl.in"],
                "description": (
                    "Account to use. Default: ndr@draas.com. "
                    "ndr@draas.com — PRIMARY. Use for 'my email', 'my drive', 'my calendar', "
                    "'my documents', 'my contacts', or when no qualifier is given. "
                    "Voice variants draas/drast/drus/dross/DRaaS all map here. "
                    "ndr@ahfl.in — use for 'AHFL email/drive/calendar/docs'. "
                    "nishantranka@gmail.com — use for 'gmail', 'personal email', 'personal drive'. "
                    "Do NOT ask which account — default to ndr@draas.com unless clearly specified otherwise."
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
