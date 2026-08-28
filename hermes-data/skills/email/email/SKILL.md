---
name: email
description: "Complete Gmail email workflow: inbox triage and analysis, drafting new emails, threaded replies with custom To/Cc, forwarding, attachments, and account management. Use for any email operation."
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [email, gmail, draft, analysis, triage, communication, reply]
    related_skills: [google-workspace]
---

# Email — Gmail Workflow

Comprehensive class-level skill covering all Gmail operations: inbox analysis/triage, drafting new emails, threaded replies, forwarding, attachments, and multi-account management.

## When to Use

Load this skill for any email operation:
- **Analysis/Triage** — "analyze my inbox", "check my email", "triage last N hours"
- **Drafting** — "email [name]", "draft an email to [name] about [topic]"
- **Replies** — "reply to [name]'s email", "reply all except [person]"
- **Forwards** — "forward that email to [new recipients]"
- **Attachments** — "reply with these PDFs attached"
- **Multi-account** — "check my ahfl.in email", "use my Gmail account"

## Account Resolution

Default: `ndr@draas.com` (service: `google-draas`). Always resolve first:

```python
gws_resolve_account(account="ndr@draas.com")
```

Other accounts: `nishantranka@gmail.com` (service: `google-gmail`), `ndr@ahfl.in` (service: `google-ahfl`). Use only when explicitly asked.

Other users on this Hermes instance (per-user vault tokens, each user resolves their OWN email to a vault service):
- Anbarasan M / Anbu (pm2.blr@draas.com) → service `google-draas` (same key as ndr's default, but a SEPARATE per-user token in the vault). Always `gws_resolve_account(account="pm2.blr@draas.com")` first — do not assume the ndr token covers him.

## Skill Sections

### 1. Email Analysis

Triage inbox, identify pending actions, detect bounces, find sent mail awaiting replies, flag drafts.

**Core flow:**
1. Resolve account → build Gmail service
2. Fetch messages from last N hours (default 48)
3. Classify: project/business, replies, bounces, financial, marketing
4. Check sent mail, pending inbox replies, drafts
5. Compile structured report with 🔴🟡 sections

Key pattern for bounce detection — Gmail delivery failures are SEPARATE threads, not replies:
```python
# Search bounces separately
bounces = gmail.users().messages().list(userId='me',
    q='from:mailer-daemon@googlemail.com after:{timestamp}').execute()
```

Detailed reference: `skill_view(name="email", file_path="references/email-triage-code-patterns.md")`
Credential/password recovery search ("did vendor X ever send me a password?", "find my login for service Y in mail") across all accounts: `skill_view(name="email", file_path="references/credential-search-patterns.md")`
Sent mail verification ("did I send X to Y with that PDF?"): `skill_view(name="email", file_path="references/sent-mail-verification.md")`
Legal case thread tracing: `skill_view(name="email", file_path="references/legal-case-thread-tracing.md")`
Forensic "who was marked on that email" lookup (find a specific past email from a fuzzy/voice description, resolve mis-transcribed names/amounts, report exact To/Cc of original vs forward vs reply; sender-domain sweeps when only the sender is known; financial-artifact tracing and threads.get-404 fallback): `skill_view(name="email", file_path="references/email-forensic-thread-lookup.md")`
Attachment content verification (verify JPG/PDF attachment content type via vision analysis when filenames don't match reality — e.g. signature pages labelled as floor plans): `skill_view(name="email", file_path="references/attachment-content-verification.md")`

### 2. Email Drafting

Draft new emails or threaded replies. NEVER send autonomously — always create Gmail drafts.

**New email:**
```python
from tools.gws_skill_bridge import call
call("draft_create", service_name="google-draas",
     to="name@example.com", subject="Subject", body="Body")
```

**Threaded reply:**
```python
call("draft_reply_create", service_name="google-draas",
     message_id="...", body="Reply body")  # NOT thread_id!
```

**Reply-All (with CC):**
```python
call("draft_reply_create", service_name="google-draas",
     message_id="...",
     body="Reply body",
     cc="recipient1@domain.com, Recipient2 <r2@domain.com>")
```

The `cc=` parameter adds a Cc header to the draft. Extract the CC list from the original message's CC headers. Use comma-separated email addresses (with or without display names). The To field is auto-populated from the original sender — no need to pass it.

Key patterns:
- Always use `message_id` (not `thread_id`) for `draft_reply_create`
- Verify draft landed in Drafts, NOT Sent
- Contact resolution via `contact_resolver` tool, never guess emails
- Reply-From-Same-Inbox rule: match the `From:` to the inbox where the original was received
- For attachments: use `MIMEMultipart` with `MIMEBase` parts
- **HTML formatting for complex emails**: For business-critical or family emails covering multiple commercial terms (property transactions, legal agreements, partnership terms), the user prefers **clean HTML+CSS formatting** — section headers, highlighted callout boxes, consent boxes, bullet lists, and organised layout. Use `call("draft_create", ..., html=True)` with inline CSS. Keep the tone conversational for family (first names, "Hi All", "Warmly") but structured enough that each commercial term is visually scannable. See `references/html-email-templates.md` for patterns and reusable CSS snippets.

Special workflows:
- Medical PAP OTP followup: `skill_view(name="email", file_path="references/medical-pap-otp-followup.md")`
- Visiting card → Contact → Draft: `skill_view(name="email", file_path="references/visiting-card-to-draft.md")`
- Regulatory research for drafting: `skill_view(name="email", file_path="references/bangalore-regulatory-sources.md")`
- Data-heavy approval verification: `skill_view(name="email", file_path="references/refund-approval-verification.md")`

### 3. Attachments & PDF Handling

For threaded replies with file attachments, build MIMEMultipart:
```python
import base64
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from tools.gws_auth import build_service

gmail = build_service('gmail', 'v1', service_name='google-draas')
msg = MIMEMultipart()
msg['To'] = 'recipient@example.com'
msg['Subject'] = 'Re: ...'
msg['In-Reply-To'] = orig_hdrs['Message-ID']
msg.attach(MIMEText(body_text))
# Attach PDFs...
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(
    userId='me', body={'message': {'raw': raw, 'threadId': thread_id}}
).execute()
```

For PDF highlighting/annotation before attaching:
`skill_view(name="email", file_path="references/pdf-highlighting.md")`

### 4. Gmail Scope Fallback

If `gws_skill_bridge.call("draft_create")` throws `invalid_scope` (the Gmail scope is broken in the vault but other Google APIs work), fall back to:
1. Compose the email as a structured Google Doc in TMP folder
2. User copies body from Doc into Gmail compose

```python
docs = build_service('docs', 'v1', service_name='google-draas')
created = drive.files().create(body={'name': '...', 'parents': [TMP]}, ...)
```

### 5. Sender Blacklisting (Auto-Cleaner)

When the user wants to blacklist senders so future mail lands in spam, there are two approaches:

**A. Native Gmail Filters (requires `gmail.settings.sharing` scope):**
- Create a filter via the Gmail API: `gmail.users().settings().filters().create(...)`
- This needs the user to re-authorize their Google account with the additional scope
- Run `send_oauth_url` with a label explaining the new scope after adding it to `HERMES_GWS_SCOPES` in `tools/gws_auth.py`
- The scope to add: `https://www.googleapis.com/auth/gmail.settings.sharing`

**B. Auto-Cleaner (fallback, no extra scopes needed):**
When native filter creation isn't available, use a cron-scheduled Python script that:
1. Queries the inbox for messages from target senders (via Reply-To header or From address)
2. Moves matching messages to SPAM using `gmail.users().messages().modify(addLabelIds=['SPAM'])`
3. Runs every 15 minutes

See the full reference script at: `skill_view(name="email", file_path="references/gmail-sender-blacklist.md")`

**Sender matching strategy:**
- For emails received via group forwards (e.g. `ndr@draas.com`), the `Reply-To` header often carries the actual sender address — search by that
- For direct emails, use the `From` header
- Always log which senders were matched and which messages were moved for audit

**Corner cases:**
- Gmail's `modify` with `addLabelIds=['SPAM']` silently skips messages already in SPAM
- Rate limits: batch deletions via `batch()` instead of one-by-one for large inbox sweeps
- The auto-cleaner cannot retroactively un-spam messages — that needs the whitelist approach (`references/not-spam-whitelist.md`).

### Attachment Content Verification

See `references/attachment-content-verification.md` for the workflow of verifying whether email attachments match their claimed content type (e.g., "floor plan" vs actual "signature sheet"), cross-referencing with other threads for the real documents, and organizing on Drive.

## Repository Layout

```
/data/hermes/skills/email/email/
├── SKILL.md
└── references/
    ├── email-triage-code-patterns.md
    ├── legal-case-thread-tracing.md
    ├── pdf-highlighting.md
    ├── email-forensic-thread-lookup.md
    ├── attachment-content-verification.md
    ├── medical-pap-otp-followup.md
    ├── sent-mail-verification.md
    ├── credential-search-patterns.md
    ├── refund-approval-verification.md
    ├── html-email-templates.md
    ├── bangalore-regulatory-sources.md
    ├── visiting-card-to-draft.md
    ├── gmail-sender-blacklist.md
    └── not-spam-whitelist.md
```

## Common Pitfalls

0. **First-time OAuth for a new user is async + throttled** — when `gws_resolve_account` shows `has_token: false` for the user's own email:
   - Send ONE `send_oauth_url` (login_hint = their email, label states the email).
   - After the user says done, RE-CHECK `gws_resolve_account` before building the service — token registration can lag the user's "successful" confirmation by tens of seconds. Wait ~45s and re-check rather than assuming failure.
   - Do NOT resend `send_oauth_url` repeatedly: Telegram flood control blocks re-sends for ~9 minutes (`Flood control exceeded. Retry in 553 seconds`). If the first send failed AND the vault still has no token, ask the user to re-tap the original button, or wait out the cooldown — don't hammer.
   - A fetch like `gws_fetch_token(service_name=...)` returning "No <service> token for user <uid>" confirms the user hasn't authorized yet — it is NOT a vault outage. Distinguish via `gws_resolve_account` first.
0a. **`draft_reply_create` auto-populates To from the message's SENDER — NOT the intended reply-all audience.** Confirmed Aug 2026: replying to a message whose last sender was an internal colleague (Eshwari → cc chain) produced To: Eshwari, not the external party the user wanted. The bridge is only safe when the original message's From IS the target recipient (e.g. replying to an insurer's own email). For any reply-all with a custom recipient set — especially when the last message in a thread came from a colleague or was addressed to a third party — use the **direct MIME pattern**: `gmail.users().drafts().create()` with an `email.mime.multipart.MIMEMultipart` that sets explicit `To`/`Cc` headers AND `In-Reply-To`/`References` from the target message's `Message-ID`, plus `threadId` in the draft body, so threading is preserved but recipients are exact. Verify the draft's To/Cc via `drafts().get(format='full')` before presenting.
0b. **`drafts().get()` does NOT accept `metadataHeaders`** — `gmail.users().drafts().get(userId='me', id=..., format='metadata', metadataHeaders=[...])` raises `TypeError: Got an unexpected keyword argument metadataHeaders`. Use `format='full'` and parse `payload.headers` yourself.
1. **`message_id` vs `thread_id`** — `draft_reply_create` needs `message_id` (Gmail message ID), NOT the thread ID
2. **Account mismatch** — never silently use the default account when user names another; surface expired tokens
3. **Draft promotion to Sent** — Gmail may move drafts to SENT; always verify after creating
4. **Bridge returns strings** — `gws_skill_bridge.call()` returns JSON strings, not dicts; use `json.loads()`
5. **Bounces are separate threads** — delivery failure notifications are not threaded with the original sent message
6. **Voice/chat names are often wrong** — verify from the actual email thread before drafting. This cuts BOTH ways: (a) before *drafting* to a person, confirm their real address from the thread; (b) when *locating* a specific past email from a voice-memo description, do NOT search the verbatim spoken entity name / amount / person name — voice transcription mangles them (e.g. user said "Reformers Collective" → real entity "Red Soul Farmers Collective"). Triangulate with phonetic/substring variants. And when asked "who was marked on that email," the **original, the forward, and the reply each have their own To/Cc** — check each variant's own top-level headers (a forward to a third party is frequently `Cc: None`, even when the embedded original body shows a Cc). See `references/email-forensic-thread-lookup.md`.
