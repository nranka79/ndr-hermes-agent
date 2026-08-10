#!/usr/bin/env python3
"""List current SPAM folder contents (date | From | Subject) for manual review.

Companion to check-spam.py — use when the cron report needs to show what is
sitting in spam so potentially-important unmatched senders (land JV
proposals, lead notifications, known contacts) can be flagged for the user
to whitelist. Same vault get_creds() pattern as check-spam.py (canonical
uid via resolve(), token's own scopes — NOT HERMES_GWS_SCOPES).

Usage:
    /opt/hermes/.venv/bin/python3 scripts/list-spam.py [max_results]

Pitfall: can intermittently hang 60-300s on first invocation (see SKILL.md
"Aug 2, 2026 — Intermittent hang on first run"); retry once before
diagnosing any auth issue.
"""
import json
import sys

sys.path.insert(0, "/opt/hermes")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from tools.gws_vault_client import get_token, resolve

DRAAS_UID = "ndr@draas.com"
DRAAS_SERVICE = "google-draas"
MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 200


def get_creds():
    uid = resolve("email", DRAAS_UID)
    tok = json.loads(get_token(uid, DRAAS_SERVICE, session_uid=uid))
    creds = Credentials.from_authorized_user_info(tok, tok.get("scopes"))
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def main():
    creds = get_creds()
    gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    prof = gmail.users().getProfile(userId="me").execute()
    print(f"Gmail account: {prof.get('emailAddress', '?')}")

    spam = gmail.users().messages().list(
        userId="me", labelIds=["SPAM"], maxResults=MAX
    ).execute()
    msgs = spam.get("messages", [])
    print(f"{len(msgs)} spam messages:")
    for s in msgs:
        m = gmail.users().messages().get(
            userId="me", id=s["id"], format="metadata",
            metadataHeaders=["From", "Subject", "Date"]
        ).execute()
        h = {x["name"]: x["value"] for x in m["payload"]["headers"]}
        print(f"  - {h.get('Date', '?')[:22]} | {h.get('From', '?')[:70]} | {h.get('Subject', '(none)')[:60]}")


if __name__ == "__main__":
    main()
