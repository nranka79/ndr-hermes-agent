# -*- coding: utf-8 -*-
"""
Fetch full body of Advance Tax emails.
"""
import sys, io, re, base64
from datetime import date

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_token.json"
SCOPES     = ["https://www.googleapis.com/auth/gmail.readonly"]

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

creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
svc   = build("gmail", "v1", credentials=creds)

today = date.today().strftime("%Y/%m/%d")
result = svc.users().messages().list(
    userId="me", q=f"after:{today} in:inbox subject:\"Advance Tax\"", maxResults=20
).execute()
messages = result.get("messages", [])

print(f"Found {len(messages)} Advance Tax email(s)\n")

for ref in messages:
    msg  = svc.users().messages().get(userId="me", id=ref["id"], format="full").execute()
    hdrs = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
    subj = hdrs.get("subject", "")
    frm  = hdrs.get("from", "")
    dt   = hdrs.get("date", "")
    body = get_body(msg["payload"]).strip()
    link = f"https://mail.google.com/mail/u/0/#all/{ref['id']}"

    print("=" * 72)
    print(f"Subject : {subj}")
    print(f"From    : {frm}")
    print(f"Date    : {dt}")
    print(f"Link    : {link}")
    print("-" * 72)
    print(body if body else msg.get("snippet",""))
    print()
