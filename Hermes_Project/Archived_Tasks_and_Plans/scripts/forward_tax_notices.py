# -*- coding: utf-8 -*-
"""
Forward Advance Tax notices to accounts with CCs.
"""
import sys, io, os, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import date

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request

# Added .send scope
SCOPES     = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.send"]
TOKEN_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_token.json"
CREDS_PATH = r"C:\Users\ruhaan\AntiGravity\gmail_credentials.json"

def get_service():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_PATH, "w", encoding="utf-8") as fh:
            fh.write(creds.to_json())
    return build("gmail", "v1", credentials=creds)

def create_message(to, cc, subject, body):
    message = MIMEMultipart()
    message["to"] = to
    message["cc"] = cc
    message["subject"] = subject
    msg = MIMEText(body)
    message.attach(msg)
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    return {"raw": raw}

def forward_emails():
    service = get_service()
    today = date.today().strftime("%Y/%m/%d")
    
    # Search for the same 2 emails
    print("Searching for Advance Tax emails...")
    result = service.users().messages().list(
        userId="me", q=f"after:{today} in:inbox subject:\"Advance Tax\"", maxResults=5
    ).execute()
    messages = result.get("messages", [])

    if not messages:
        print("No emails found to forward.")
        return

    to_addr = "accounts@draas.com"
    cc_addr = "rnr@draas.com, echamundeshwari@draas.com"
    
    print(f"Found {len(messages)} email(s). Forwarding...")
    
    for ref in messages:
        msg = service.users().messages().get(userId="me", id=ref["id"], format="full").execute()
        hdrs = {h["name"].lower(): h["value"] for h in msg["payload"].get("headers", [])}
        orig_subject = hdrs.get("subject", "Income Tax Notice")
        snippet = msg.get("snippet", "")
        
        fwd_subject = f"URGENT ACTION: Fwd: {orig_subject}"
        fwd_body = f"""Hi Team,

Please review the below Advance Tax notice received from the Income Tax Department for urgent action. This needs to be checked and addressed before the 15th March deadline.

---------- Forwarded message ----------
From: {hdrs.get('from')}
Date: {hdrs.get('date')}
Subject: {orig_subject}

{snippet}... (Full details in the original notice on the portal)

---
Sent via Automation
"""
        raw_msg = create_message(to_addr, cc_addr, fwd_subject, fwd_body)
        sent = service.users().messages().send(userId="me", body=raw_msg).execute()
        
        sent_id = sent["id"]
        link = f"https://mail.google.com/mail/u/0/#all/{sent_id}"
        print(f"\nForwarded: {orig_subject}")
        print(f"Sent Link: {link}")

if __name__ == "__main__":
    forward_emails()
