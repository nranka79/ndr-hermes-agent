---
name: email-drafter
description: |
  Drafts new emails or threaded replies for ndr@draas.com using the google_workspace_manager Hermes tool.
  For replies, finds the Gmail thread, extracts threadId, and sends with --threadId so the reply stays in thread.
  Supports plain text and HTML. Default account: ndr@draas.com.
  Use nishantranka@gmail.com only when explicitly asked. Use ndr@ahfl.in only when explicitly asked.
  Trigger: "email [name]", "reply to [name]'s email", "draft an email to [name]", "send [name] an email"
metadata:
  hermes:
    tags: [email, gmail, draft, communication, reply, thread]
category: communication
version: 2.0.0
author: ndr@draas.com
---

# Email Drafter

## CRITICAL: How to call google_workspace_manager

`google_workspace_manager` is a **registered Hermes tool** — call it via the tool API, exactly like `terminal` or `memory`.
**NEVER run it as a shell command. NEVER try to import it as a Python module.**

Call it like this (tool_use API):
```
tool: google_workspace_manager
input:
  command: "gmail messages list --params '{\"maxResults\":20,\"q\":\"is:unread after:2026/05/01\"}'"
  account_email: "ndr@draas.com"
```

---

## 1. Trigger Conditions

Activate when the user says anything like:
- "Email Raghu about the land valuation"
- "Reply to Nishant Prakash's email about Oasis"
- "Draft an email to Manohar about the project update"
- "Reply all to the email from Bhavesh"

**Default account:** `ndr@draas.com` for ALL emails unless the user explicitly says:
- "use my Gmail account" → `nishantranka@gmail.com`
- "use AHFL account" → `ndr@ahfl.in`

---

## 2. Stage 1 — Context Gathering

### For a NEW email

**Always use `contact_resolver` tool** — never guess email addresses.

Call the tool:
```
tool: contact_resolver
input:
  query: "[name as typed/heard]"
  context: "[project or topic, if any]"
```

When `auto_selected` is true, confirm with user:
> Found: **Raghu Iyer** — Director, [Company]
> Drafting to raghu@example.com (work). Say if you want a different address.

When no match: report clearly, do not fall back to any sheet read.

---

### For a REPLY (existing thread)

Search Gmail for the thread using the `google_workspace_manager` tool:
```
tool: google_workspace_manager
input:
  command: "gmail messages list --params '{\"maxResults\":5,\"q\":\"from:raghu subject:land valuation\"}'"
  account_email: "ndr@draas.com"
```

Then fetch the full thread:
```
tool: google_workspace_manager
input:
  command: "gmail threads get --id THREAD_ID"
  account_email: "ndr@draas.com"
```

Extract from thread: `threadId`, sender, all To/CC participants, subject line.

Present context:
> Found thread: **"Land Valuation — Allalsandra Survey"**
> Last message: from Raghu Iyer on [date]
> Participants: Raghu Iyer, Nishant Ranka, CC: Bhavesh Bafna
> Drafting a reply. Reply-all? (yes/no)

---

## 3. Stage 2 — Draft

### Work email tone
- No greeting, go straight to the point
- Numbered tasks if there are asks, deadlines in bold if HTML
- No boilerplate ("Hope you're well", "Dear [name]") unless explicitly asked
- Subject: `[Project/Entity Name]: [one-line description]`

### Personal / casual tone
- Warmer, no subject prefix
- Plain text is fine
- **Roshni Ranka / "RO":** Always personal tone

Present the draft for confirmation before sending:
> **Subject:** `Ranka Oasis: Site Visit — Confirming Date and Access`
>
> Please confirm your availability for a site visit this week.
>
> 1. Confirm date — by Wednesday 5pm
> 2. Arrange access to the south plot
>
> Ready to send?

---

## 4. Stage 3 — Send

### New email
```
tool: google_workspace_manager
input:
  command: "gmail messages send --to raghu@example.com --subject 'Ranka Oasis: Site Visit' --body 'Please confirm...'"
  account_email: "ndr@draas.com"
```

For HTML: add `--bodyHtml '<p>...</p>'` flag alongside `--body`.

### Threaded reply — MUST include --threadId
```
tool: google_workspace_manager
input:
  command: "gmail messages send-reply --to raghu@example.com --subject 'Re: Land Valuation' --body 'Thanks...' --threadId THREAD_ID_HERE"
  account_email: "ndr@draas.com"
```

Without `--threadId` Gmail creates a brand-new disconnected thread. Always include it for replies.

After sending:
> Sent! Message ID: `[id]` | Thread: `https://mail.google.com/mail/u/0/#inbox/[threadId]`

---

## 5. Rules

- ALWAYS call `google_workspace_manager` as a Hermes tool, never as a shell command
- ALWAYS include `--threadId` for replies
- NEVER add boilerplate greetings unless asked
- ALWAYS confirm contact/thread before drafting
- NEVER use People API for contact lookups — use `contact_resolver` tool
- NEVER send without showing draft and getting confirmation
