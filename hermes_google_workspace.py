#!/usr/bin/env python3
"""
Google Workspace integration for Hermes.
Provides Hermes with access to Drive, Gmail, Calendar, Contacts, Sheets, Docs, Tasks, Admin.
Supports multiple accounts via OAuth 2.0.
"""

import os
import json
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# All required scopes
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
    "https://www.googleapis.com/auth/contacts.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/admin.directory.user.readonly",
    "https://www.googleapis.com/auth/admin.directory.group.readonly",
]

# Default account
DEFAULT_ACCOUNT = "ndr@draas.com"

# Account OAuth credential file paths
ACCOUNT_CONFIGS = {
    "ndr@draas.com": {
        "cred_file": "/data/hermes/oauth-draas.json"
    },
    "nishantranka@gmail.com": {
        "cred_file": "/data/hermes/oauth-gmail.json"
    },
    "ndr@ahfl.in": {
        "cred_file": "/data/hermes/oauth-ahfl.json"
    }
}

def get_credentials(account_email=None):
    """Get OAuth credentials for a specific account from file."""
    if account_email is None:
        account_email = DEFAULT_ACCOUNT

    if account_email not in ACCOUNT_CONFIGS:
        raise ValueError(f"Unknown account: {account_email}")

    config = ACCOUNT_CONFIGS[account_email]
    cred_file = config["cred_file"]

    # Read credential file
    if not os.path.exists(cred_file):
        raise FileNotFoundError(
            f"Credential file not found for {account_email}: {cred_file}\n"
            f"Make sure setup_oauth_credentials.py has run at startup."
        )

    try:
        with open(cred_file, "r") as f:
            cred_data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in credential file {cred_file}: {e}")

    # Create credentials from file data
    credentials = Credentials(
        token=None,
        refresh_token=cred_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=cred_data.get("client_id"),
        client_secret=cred_data.get("client_secret"),
        scopes=SCOPES
    )

    # Refresh to get valid access token
    credentials.refresh(Request())
    return credentials

# ============================================================================
# DRIVE API
# ============================================================================

def list_drive_files(max_results=10, query=None, account_email=None):
    """List files from Google Drive for a specific account."""
    try:
        credentials = get_credentials(account_email)
        service = build("drive", "v3", credentials=credentials)

        files = []
        page_token = None

        while len(files) < max_results:
            results = service.files().list(
                spaces="drive",
                pageSize=min(10, max_results - len(files)),
                pageToken=page_token,
                q=query,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)",
                orderBy="modifiedTime desc"
            ).execute()

            files.extend(results.get("files", []))
            page_token = results.get("nextPageToken")

            if not page_token:
                break

        return {"success": True, "files": files}

    except HttpError as error:
        return {"success": False, "error": str(error)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_drive_file_content(file_id, account_email=None):
    """Get metadata for a Drive file for a specific account."""
    try:
        credentials = get_credentials(account_email)
        service = build("drive", "v3", credentials=credentials)

        file_metadata = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size, modifiedTime, owners, webViewLink"
        ).execute()

        return {"success": True, "file": file_metadata}

    except HttpError as error:
        return {"success": False, "error": str(error)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# GMAIL API
# ============================================================================

def list_gmail_messages(max_results=5, query=None, account_email=None):
    """List recent Gmail messages for a specific account."""
    try:
        credentials = get_credentials(account_email)
        service = build("gmail", "v1", credentials=credentials)

        results = service.users().messages().list(
            userId="me",
            maxResults=max_results,
            q=query or ""
        ).execute()

        messages = results.get("messages", [])
        message_list = []

        for msg in messages:
            msg_data = service.users().messages().get(
                userId="me",
                id=msg["id"],
                format="metadata",
                metadataHeaders=["From", "Subject", "Date"]
            ).execute()

            headers = {h["name"]: h["value"] for h in msg_data["payload"].get("headers", [])}
            message_list.append({
                "id": msg["id"],
                "from": headers.get("From", "Unknown"),
                "subject": headers.get("Subject", "(no subject)"),
                "date": headers.get("Date", "Unknown")
            })

        return {"success": True, "messages": message_list}

    except HttpError as error:
        return {"success": False, "error": str(error)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# CALENDAR API
# ============================================================================

def list_calendar_events(calendar_id="primary", max_results=10, time_min=None, account_email=None):
    """List upcoming calendar events for a specific account."""
    try:
        credentials = get_credentials(account_email)
        service = build("calendar", "v3", credentials=credentials)

        if not time_min:
            from datetime import datetime, timezone
            time_min = datetime.now(timezone.utc).isoformat()

        results = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
            fields="items(id, summary, start, end, attendees)"
        ).execute()

        events = results.get("items", [])
        event_list = []

        for event in events:
            event_list.append({
                "summary": event.get("summary", "(untitled)"),
                "start": event.get("start", {}).get("dateTime", event.get("start", {}).get("date")),
                "end": event.get("end", {}).get("dateTime", event.get("end", {}).get("date")),
                "attendees_count": len(event.get("attendees", []))
            })

        return {"success": True, "events": event_list}

    except HttpError as error:
        return {"success": False, "error": str(error)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# CONTACTS API
# ============================================================================

def list_contacts(max_results=10, account_email=None):
    """List contacts from Google Contacts for a specific account."""
    try:
        credentials = get_credentials(account_email)
        service = build("people", "v1", credentials=credentials)

        results = service.people().connections().list(
            resourceName="people/me",
            pageSize=max_results,
            personFields="names,emailAddresses,phoneNumbers"
        ).execute()

        connections = results.get("connections", [])
        contacts = []

        for person in connections:
            name = person.get("names", [{}])[0].get("displayName", "Unknown")
            emails = [e["value"] for e in person.get("emailAddresses", [])]
            phones = [p["value"] for p in person.get("phoneNumbers", [])]

            contacts.append({
                "name": name,
                "emails": emails,
                "phones": phones
            })

        return {"success": True, "contacts": contacts}

    except HttpError as error:
        return {"success": False, "error": str(error)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# SHEETS API
# ============================================================================

def list_spreadsheets(max_results=5, account_email=None):
    """List spreadsheets from Google Drive for a specific account."""
    try:
        result = list_drive_files(
            max_results=max_results,
            query="mimeType='application/vnd.google-apps.spreadsheet'",
            account_email=account_email
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

def read_sheet_values(spreadsheet_id, range_name="Sheet1!A1:Z100", account_email=None):
    """Read values from a Google Sheet for a specific account."""
    try:
        credentials = get_credentials(account_email)
        service = build("sheets", "v4", credentials=credentials)

        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()

        values = result.get("values", [])
        return {"success": True, "values": values}

    except HttpError as error:
        return {"success": False, "error": str(error)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# TASKS API
# ============================================================================

def list_tasks(tasklist_id="@default", max_results=10, account_email=None):
    """List tasks from Google Tasks for a specific account."""
    try:
        credentials = get_credentials(account_email)
        service = build("tasks", "v1", credentials=credentials)

        results = service.tasks().list(
            tasklist=tasklist_id,
            maxResults=max_results,
            fields="items(id, title, due, status)"
        ).execute()

        tasks = []
        for task in results.get("items", []):
            tasks.append({
                "title": task.get("title", "(untitled)"),
                "due": task.get("due", "No due date"),
                "status": task.get("status", "unknown")
            })

        return {"success": True, "tasks": tasks}

    except HttpError as error:
        return {"success": False, "error": str(error)}
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================================================================
# MAIN - For CLI testing
# ============================================================================

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python3 hermes_google_workspace.py <command> [args]")
        print("\nAvailable commands:")
        print("  list-drive [max_results]")
        print("  list-gmail [max_results]")
        print("  list-calendar [max_results]")
        print("  list-contacts [max_results]")
        print("  list-tasks")
        print("  list-sheets")
        sys.exit(1)

    command = sys.argv[1]
    max_results = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    if command == "list-drive":
        result = list_drive_files(max_results)
    elif command == "list-gmail":
        result = list_gmail_messages(max_results)
    elif command == "list-calendar":
        result = list_calendar_events(max_results=max_results)
    elif command == "list-contacts":
        result = list_contacts(max_results)
    elif command == "list-tasks":
        result = list_tasks()
    elif command == "list-sheets":
        result = list_spreadsheets(max_results)
    else:
        result = {"error": f"Unknown command: {command}"}

    print(json.dumps(result, indent=2, default=str))
