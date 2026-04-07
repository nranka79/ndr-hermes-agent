# -*- coding: utf-8 -*-
"""
Gmail Email Analyzer
Fetches today's received emails and categorizes them using the Gmail API.
"""

import os
import sys
import io
import base64
import re
from datetime import date

# Force UTF-8 output on Windows so emojis / special chars don't crash
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding and sys.stderr.encoding.lower() != "utf-8":
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES     = ["https://www.googleapis.com/auth/gmail.readonly"]
TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_token.json"
CREDS_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_credentials.json"

# ── Category keyword patterns ────────────────────────────────────────────────
MASS_EMAIL_PATTERNS = [
    r"unsubscribe", r"newsletter", r"no.?reply", r"noreply",
    r"marketing", r"promotion", r"offer", r"deal", r"sale",
    r"list-unsubscribe", r"bulk", r"campaign", r"notification@",
    r"donotreply", r"do-not-reply", r"alert@", r"news@", r"info@",
    r"notifications@", r"updates@", r"support@",
]

WORK_KEYWORDS = [
    r"meeting", r"project", r"deadline", r"report", r"invoice", r"contract",
    r"proposal", r"budget", r"review", r"feedback", r"agenda", r"standup",
    r"sprint", r"release", r"deploy", r"jira", r"confluence", r"slack",
    r"zoom", r"call", r"sync", r"team", r"colleague", r"client", r"task",
    r"milestone", r"deliverable", r"update", r"status", r"approval",
    r"quarterly", r"annual", r"hr", r"payroll", r"ticket", r"pull request",
]

ACTION_KEYWORDS = [
    r"please\s+(review|confirm|approve|respond|reply|complete|fill|sign|check|update|send)",
    r"action\s+required", r"action\s+needed", r"response\s+needed",
    r"response\s+required", r"reply\s+by", r"respond\s+by",
    r"confirm\s+(your|the)", r"please\s+let\s+(me|us)\s+know",
    r"can\s+you\s+(please\s+)?(review|confirm|send|check|update|provide|share|look)",
    r"awaiting\s+your", r"your\s+(feedback|input|response|approval)\s+is",
    r"due\s+(today|tomorrow|soon|by)", r"asap", r"urgent",
    r"kindly\s+(review|confirm|reply|respond)",
    r"follow.?up", r"following\s+up", r"reminder:",
]

INFORMATIONAL_KEYWORDS = [
    r"fyi", r"for your information", r"just\s+wanted\s+to\s+(let|share|inform)",
    r"heads.?up", r"announcement", r"update\s+on", r"new\s+feature",
    r"release\s+notes", r"changelog", r"blog", r"article", r"report\s+is\s+ready",
    r"digest", r"recap", r"summary", r"weekly", r"monthly", r"daily",
]

# Category labels (ASCII-safe)
CAT_ACTION = "[ACTION] Action / Reply Needed"
CAT_WORK   = "[WORK]   Work-Related"
CAT_MASS   = "[MASS]   Mass / Marketing / Notifications"
CAT_INFO   = "[INFO]   Informational"
CAT_OTHER  = "[OTHER]  Personal / Other"

PRINT_ORDER = [CAT_ACTION, CAT_WORK, CAT_INFO, CAT_MASS, CAT_OTHER]


# ── Auth / API ────────────────────────────────────────────────────────────────

def get_gmail_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CREDS_PATH):
                print(f"\nERROR: credentials file not found:\n  {CREDS_PATH}")
                sys.exit(1)
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())

    return build("gmail", "v1", credentials=creds)


# ── Email helpers ─────────────────────────────────────────────────────────────

def get_email_body(payload):
    body = ""
    if "parts" in payload:
        for part in payload["parts"]:
            body += get_email_body(part)
    else:
        if payload.get("mimeType") == "text/plain":
            data = payload.get("body", {}).get("data", "")
            if data:
                body += base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    return body


def parse_headers(headers_list):
    return {h["name"].lower(): h["value"] for h in headers_list}


def matches_any(text, patterns):
    t = text.lower()
    return any(re.search(p, t) for p in patterns)


def categorize(subject, sender, body):
    combined = f"{subject} {sender} {body[:2000]}"
    is_mass   = matches_any(combined, MASS_EMAIL_PATTERNS)
    is_action = matches_any(combined, ACTION_KEYWORDS)
    is_work   = matches_any(combined, WORK_KEYWORDS)
    is_info   = matches_any(combined, INFORMATIONAL_KEYWORDS)

    cats = []
    if is_action and not is_mass:
        cats.append(CAT_ACTION)
    if is_work:
        cats.append(CAT_WORK)
    if is_mass:
        cats.append(CAT_MASS)
    if is_info and not is_mass:
        cats.append(CAT_INFO)
    if not cats:
        cats.append(CAT_OTHER)
    return cats


def fetch_todays_messages(service):
    today_str = date.today().strftime("%Y/%m/%d")
    query = f"after:{today_str} in:inbox"
    messages, page_token = [], None
    while True:
        params = {"userId": "me", "q": query, "maxResults": 100}
        if page_token:
            params["pageToken"] = page_token
        result = service.users().messages().list(**params).execute()
        messages.extend(result.get("messages", []))
        page_token = result.get("nextPageToken")
        if not page_token:
            break
    return messages


def get_details(service, msg_id):
    msg = service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    hdrs    = parse_headers(msg["payload"].get("headers", []))
    subject = hdrs.get("subject", "(no subject)")
    sender  = hdrs.get("from", "(unknown)")
    date_s  = hdrs.get("date", "")
    body    = get_email_body(msg["payload"])
    snippet = msg.get("snippet", "")
    return {"id": msg_id, "subject": subject, "sender": sender,
            "date": date_s, "snippet": snippet, "body": body}


# ── Output ────────────────────────────────────────────────────────────────────

def print_summary(categorized, total):
    W = 74
    print("\n" + "=" * W)
    print(f"  TODAY'S EMAIL SUMMARY  |  {date.today().strftime('%A, %d %B %Y')}")
    print(f"  {total} email(s) received in inbox")
    print("=" * W)

    for cat in PRINT_ORDER:
        emails = categorized.get(cat, [])
        if not emails:
            continue
        print(f"\n  {cat}  ({len(emails)} email{'s' if len(emails) != 1 else ''})")
        print("  " + "-" * (W - 2))
        for idx, e in enumerate(emails, 1):
            print(f"\n  [{idx}] Subject : {e['subject']}")
            print(f"       From    : {e['sender']}")
            print(f"       Date    : {e['date']}")
            print(f"       ID      : {e['id']}")
            snippet = re.sub(r"\s+", " ", e["snippet"]).strip()
            if snippet:
                preview = snippet[:160] + ("..." if len(snippet) > 160 else "")
                print(f"       Preview : {preview}")

    print("\n" + "=" * W + "\n")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    print("Authenticating with Gmail ...")
    service = get_gmail_service()

    print("Fetching today's inbox emails ...")
    messages = fetch_todays_messages(service)

    if not messages:
        print("\nNo emails received today in your inbox.")
        return

    total = len(messages)
    print(f"Found {total} email(s). Fetching details ...")

    categorized = {}
    for i, msg_ref in enumerate(messages, 1):
        sys.stdout.write(f"\r  Processing {i}/{total} ...")
        sys.stdout.flush()
        try:
            details = get_details(service, msg_ref["id"])
            for cat in categorize(details["subject"], details["sender"], details["body"]):
                categorized.setdefault(cat, []).append(details)
        except HttpError as err:
            print(f"\n  WARNING: Skipping message {msg_ref['id']}: {err}")

    print()
    print_summary(categorized, total)


if __name__ == "__main__":
    main()
