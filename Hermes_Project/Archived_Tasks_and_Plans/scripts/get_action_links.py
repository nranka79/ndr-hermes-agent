# -*- coding: utf-8 -*-
"""
Fetch action-needed emails with direct Gmail web links.
"""
import sys, io, re, base64
from datetime import date

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_token.json"
SCOPES     = ["https://www.googleapis.com/auth/gmail.readonly"]

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

MASS_PATTERNS = [
    r"unsubscribe", r"newsletter", r"no.?reply", r"noreply",
    r"marketing", r"promotion", r"donotreply", r"do-not-reply",
    r"notifications@", r"updates@", r"list-unsubscribe",
]

def get_body(payload):
    body = ""
    if "parts" in payload:
        for p in payload["parts"]:
            body += get_body(p)
    elif payload.get("mimeType") == "text/plain":
        data = payload.get("body", {}).get("data", "")
        if data:
            body += base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    return body

def matches(text, patterns):
    t = text.lower()
    return any(re.search(p, t) for p in patterns)

creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
svc   = build("gmail", "v1", credentials=creds)

today = date.today().strftime("%Y/%m/%d")
result = svc.users().messages().list(
    userId="me", q=f"after:{today} in:inbox", maxResults=100
).execute()
messages = result.get("messages", [])

print(f"\nChecking {len(messages)} emails for action items...\n")

action_emails = []
for ref in messages:
    msg = svc.users().messages().get(userId="me", id=ref["id"], format="full").execute()
    hdrs    = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    subject = hdrs.get("subject", "(no subject)")
    sender  = hdrs.get("from", "(unknown)")
    date_s  = hdrs.get("date", "")
    snippet = msg.get("snippet", "")
    body    = get_body(msg["payload"])
    combined = f"{subject} {sender} {body[:2000]}"

    is_mass   = matches(combined, MASS_PATTERNS)
    is_action = matches(combined, ACTION_KEYWORDS)

    if is_action and not is_mass:
        msg_id = ref["id"]
        # Gmail web URL — works for both personal and Workspace accounts
        gmail_link = f"https://mail.google.com/mail/u/0/#all/{msg_id}"
        action_emails.append({
            "subject": subject,
            "sender":  sender,
            "date":    date_s,
            "snippet": re.sub(r"\s+", " ", snippet).strip()[:180],
            "link":    gmail_link,
        })

print("=" * 70)
print(f"  ACTION / REPLY NEEDED  ({len(action_emails)} emails)")
print("=" * 70)
for i, e in enumerate(action_emails, 1):
    print(f"\n  [{i}] {e['subject']}")
    print(f"       From   : {e['sender']}")
    print(f"       Date   : {e['date']}")
    print(f"       Preview: {e['snippet']}")
    print(f"       Link   : {e['link']}")

print("\n" + "=" * 70)
