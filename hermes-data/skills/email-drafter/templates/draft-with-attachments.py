#!/usr/bin/env python3
"""
Template: Create a Gmail draft reply with PDF attachments, properly threaded.

Use this when draft_reply_create / draft_create (gws_skill_bridge) can't handle
attachments. Builds MIME multipart manually and calls the Gmail API directly.

REQUIRED edits before use:
  1. SERVICE_NAME — set to the correct vault key (google-draas, google-ahfl, google-gmail)
  2. THREAD_ID — from gmail_thread_get() or earlier metadata read
  3. PDF paths and filenames
  4. Body HTML content
  5. To / Cc / Bcc addresses
"""
import os, sys, base64, json

# ── Hermes bootstrap ──────────────────────────────────────────────────
sys.path.insert(0, '/opt/hermes')
os.chdir('/opt/hermes')
from tools.gws_auth import build_service
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

# ── CONFIGURE THESE ───────────────────────────────────────────────────
SERVICE_NAME = "google-draas"       # resolve via gws_resolve_account()
THREAD_ID    = "1a04247149b6c94b"   # from the existing thread
MESSAGE_ID   = None                 # last message in thread (for In-Reply-To)

# Attachment paths and display names
ATTACHMENTS = [
    ("/tmp/document1.pdf", "Certificate.pdf"),
]

# Recipients
TO_ADDR  = 'Teacher <teacher@school.edu>'
CC_ADDR  = 'Parent <parent@example.com>, Child <child@example.com>'
BCC_ADDR = ''  # e.g. 'Admin <admin@school.edu>' — set to '' if not needed
FROM_ADDR = 'Nishant Ranka <ndr@draas.com>'

# ── Build service ─────────────────────────────────────────────────────
service = build_service("gmail", "v1", service_name=SERVICE_NAME)

# Get original message headers for threading (needs MESSAGE_ID)
orig_msg_id = None
if MESSAGE_ID:
    original = service.users().messages().get(
        userId="me", id=MESSAGE_ID, format="metadata",
        metadataHeaders=["From", "Subject", "Message-ID"],
    ).execute()
    hdrs = {h["name"].lower(): h["value"] for h in original.get("payload", {}).get("headers", [])}
    orig_msg_id = hdrs.get("message-id", "")
    subject = hdrs.get("subject", "")
else:
    # No MESSAGE_ID — get the thread and find the last message
    thread = service.users().threads().get(userId='me', id=THREAD_ID, format='metadata',
        metadataHeaders=['From', 'Subject', 'Message-ID']).execute()
    last = thread['messages'][-1]
    hdrs = {h["name"].lower(): h["value"] for h in last["payload"]["headers"]}
    orig_msg_id = hdrs.get("message-id", "")
    subject = hdrs.get("subject", "")

subject = subject if subject.lower().startswith("re:") else f"Re: {subject}"

# ── Build MIME multipart ──────────────────────────────────────────────
msg = MIMEMultipart("mixed")
msg["From"] = FROM_ADDR
msg["To"] = TO_ADDR
msg["Cc"] = CC_ADDR
if BCC_ADDR:
    msg["Bcc"] = BCC_ADDR
msg["Subject"] = subject
if orig_msg_id:
    msg["In-Reply-To"] = orig_msg_id
    msg["References"] = orig_msg_id

# HTML body part
body_html = """<div dir="ltr">
<p>Dear [Name],</p>
<p>Your email content here.</p>
</div>"""
msg.attach(MIMEText(body_html, "html"))

# Attach files
for filepath, display_name in ATTACHMENTS:
    with open(filepath, "rb") as f:
        data = f.read()
    part = MIMEBase("application", "pdf")
    part.set_payload(data)
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", "attachment", filename=display_name)
    msg.attach(part)

# ── Create draft ──────────────────────────────────────────────────────
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft_body = {"message": {"raw": raw, "threadId": THREAD_ID}}
result = service.users().drafts().create(userId="me", body=draft_body).execute()
draft_msg = result.get("message", {})

print(json.dumps({
    "status": "draft_created",
    "draft_id": result["id"],
    "message_id": draft_msg.get("id", ""),
    "threadId": draft_msg.get("threadId", ""),
    "subject": subject,
    "to": TO_ADDR,
    "cc": CC_ADDR,
    "bcc": BCC_ADDR if BCC_ADDR else "(none)",
    "attachments": [fn for _, fn in ATTACHMENTS],
}, indent=2))

# Verify thread ID matches
print(f"\nVerified: threadId = {draft_msg.get('threadId')} (expected {THREAD_ID})")