"""
Google Workspace SA DWD helper — Sheets/Contacts/Docs/Tasks ONLY.

Used for accessing shared business data (contacts spreadsheet, etc.).
NOT for Gmail or Calendar — those require per-user OAuth via gws_auth.py.

Usage:
    from tools.gws_sa import build_service
    svc = build_service("sheets", "v4", subject_email)
"""

import json
import os
from google.oauth2 import service_account
from googleapiclient.discovery import build

# SA DWD is intentionally restricted to non-personal APIs.
# Gmail and Calendar are excluded — use gws_auth.py for those.
_ALLOWED_APIS = {"sheets", "contacts", "tasks", "docs", "people", "drive"}

_SCOPES = {
    "sheets":   ["https://www.googleapis.com/auth/spreadsheets"],
    "contacts": ["https://www.googleapis.com/auth/contacts"],
    "tasks":    ["https://www.googleapis.com/auth/tasks"],
    "docs":     ["https://www.googleapis.com/auth/documents"],
    "people":   ["https://www.googleapis.com/auth/contacts"],
    "drive":    ["https://www.googleapis.com/auth/drive"],
}


def build_service(api: str, version: str, subject_email: str):
    """
    Build a Google API client impersonating subject_email via SA DWD.
    Only allowed for shared-data APIs (sheets, contacts, docs, tasks, drive).
    For Gmail/Calendar use gws_auth.build_service() instead.

    Args:
        api:           e.g. "sheets", "people", "docs"
        version:       e.g. "v1", "v3", "v4"
        subject_email: the @draas.com email to impersonate (use sheet owner for shared data)
    """
    if api not in _ALLOWED_APIS:
        raise ValueError(
            f"gws_sa does not support '{api}'. "
            "For Gmail/Calendar use gws_auth.build_service() which enforces per-user OAuth."
        )
    if not subject_email or "@draas.com" not in subject_email:
        raise ValueError(f"subject_email must be a @draas.com address, got: {subject_email!r}")
    sa_key = json.loads(os.environ["GOOGLE_SA_KEY"])
    creds = service_account.Credentials.from_service_account_info(
        sa_key,
        scopes=_SCOPES.get(api, ["https://www.googleapis.com/auth/cloud-platform"]),
    ).with_subject(subject_email)
    return build(api, version, credentials=creds)
