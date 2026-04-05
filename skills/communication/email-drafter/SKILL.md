---
name: email-drafter
description: |
  Drafts new emails or threaded replies using Gmail via google_workspace_manager.
  For replies, finds the Gmail thread, extracts threadId and all participants,
  and sends with --threadId so the reply stays in the same thread (not a new one).
  Supports plain text and HTML formatting. Same work/personal tone rules as whatsapp-drafter.
  Default account: ndr@draas.com. Use Gmail account (nishantranka@gmail.com) only when explicitly asked.
  Trigger: "email [name]", "reply to [name]'s email", "respond to the thread about [topic]",
           "draft an email to [name]", "reply all to...", "send [name] an email"
metadata:
  hermes:
    tags: [email, gmail, draft, communication, reply, thread, html]
category: communication
version: 1.0.0
author: ndr@draas.com
---

# Email Drafter

## 1. Trigger Conditions

Activate when the user says anything like:
- "Email Raghu about the land valuation"
- "Reply to Nishant Prakash's email about Oasis"
- "Respond to the thread about Allalsandra survey"
- "Draft an email to Manohar about the project update"
- "Reply all to the email from Bhavesh"

**Default account:** `ndr@draas.com` for ALL emails unless the user explicitly says:
- "use my Gmail account" → `nishantranka@gmail.com`
- "use AHFL account" or "send from AHFL" → `ndr@ahfl.in`

---

## 2. Stage 1 — Context Gathering

### For a NEW email (no existing thread)

Look up the contact's email address via the People API:
```
google_workspace_manager(
  command="contacts people search --query 'Raghu Iyer' --personFields emailAddresses,names,organizations",
  account_email="ndr@draas.com"
)
```

Extract: full name, all email addresses (with labels: work, personal, etc.).

Present:
> Found: **Raghu Iyer** — Director, [Company]
> - Work: raghu@example.com
> - Personal: raghu.iyer@gmail.com
>
> Drafting to raghu@example.com (work). *(Say if you want a different address.)*

---

### For a REPLY or RESPOND (existing thread)

Search Gmail for the thread:
```
google_workspace_manager(
  command="gmail messages list --maxResults 5 --params '{\"q\":\"from:raghu OR to:raghu subject:land valuation\"}'",
  account_email="ndr@draas.com"
)
```

Pick the most relevant result. Then get the full thread to extract all participants:
```
google_workspace_manager(
  command="gmail threads get --id THREAD_ID",
  account_email="ndr@draas.com"
)
```

From the thread, extract:
- `threadId` — **critical, must be stored for the send step**
- `messageId` of the most recent message
- `From`, `To`, `CC`, `BCC` headers of the most recent message
- Subject line

**Present the thread context:**
> Found thread: **"Land Valuation — Allalsandra Survey"**
> - Last message: from Raghu Iyer on [date]
> - Participants: Raghu Iyer, Nishant Ranka, [CC: Bhavesh Bafna]
> - Thread ID: `[id]`
>
> Drafting a reply. Reply-all? (yes/no)

If reply-all: include all To and CC participants from the original message.
If reply (not all): reply only to the sender (From address).

---

## 3. Stage 2 — Draft the Message

Same formatting rules as WhatsApp Drafter — work vs personal tone:

### Work email (project/entity/land/accounting/legal/marketing topic)

**Subject line** (new emails): concise, factual — mirror the WhatsApp caption format:
`[Project/Entity Name]: [one-line description]`

**Body format:**
```
[No greeting — go straight to the point]

[Opening sentence: what this email is about]

[Numbered tasks/asks if any:]
1. [Task] — by [deadline]
2. ...

[Key data points as bullets if any:]
- [Point]

[Closing — optional, one line only if needed: "Please revert by [date]." or "Look forward to your confirmation."]
```

**For HTML email** (when formatting/bold deadlines are important):

Use `--bodyHtml` with the HTML version alongside `--body` for plain text fallback:
```html
<p>[Opening sentence]</p>
<ol>
  <li>[Task 1] — by <strong>[deadline]</strong></li>
  <li>[Task 2]</li>
</ol>
<ul>
  <li>[Data point]</li>
</ul>
```

Rules:
- No "Hope you're well", "Dear [name]", "I trust this email finds you..." UNLESS explicitly asked
- Deadlines in HTML: `<strong>date</strong>`. In plain text: wrap in asterisks for clarity
- Keep it direct; if it's a task list, number it clearly

---

### Personal / casual email

- No subject prefix
- Warmer tone
- Still no boilerplate opener unless asked
- Plain text is fine; HTML not needed unless the content benefits from it

**Special rule — Roshni Ranka / "RO":** Always personal tone.

---

### Present the draft

Show the draft subject and body separately for easy review:

> **Subject:** `Ranka Oasis: Site Visit — Confirming Date and Access`
>
> **Body:**
> ```
> Please confirm your availability for a site visit this week.
>
> 1. Confirm date — by Wednesday 5pm
> 2. Arrange access to the south plot
> 3. Send updated survey report before the visit
>
> Please revert by end of day Tuesday.
> ```
>
> Ready to send? (Say "send" to send, or give me edits first.)

---

## 4. Stage 3 — Send

### New email

```
google_workspace_manager(
  command="gmail messages send-with-attachment --to raghu@example.com --subject 'Ranka Oasis: Site Visit' --body 'Please confirm...' --bodyHtml '<p>Please confirm...</p><ol>...'",
  account_email="ndr@draas.com"
)
```

Omit `--bodyHtml` if plain text is sufficient (personal emails, short messages).

---

### Threaded reply — CRITICAL: must include --threadId

```
google_workspace_manager(
  command="gmail messages send-reply --to raghu@example.com --cc 'bhavesh@example.com' --subject 'Re: Land Valuation — Allalsandra Survey' --body 'Thanks for the update...' --threadId THREAD_ID_HERE",
  account_email="ndr@draas.com"
)
```

**Why `--threadId` is mandatory for replies:**
- The Gmail API uses `threadId` in the request body to place the message in the existing thread
- Without it, Gmail creates a brand-new separate thread — the reply gets lost
- The `--threadId` flag sets BOTH the MIME `In-Reply-To` header AND the API `threadId` field

**Subject for replies:** prefix with `Re: ` only if not already present in the original subject.

---

### After sending

Confirm to the user:
> Sent! **Message ID:** `[id]` | **Thread ID:** `[threadId]`
>
> View thread: `https://mail.google.com/mail/u/0/#inbox/[threadId]`

---

## 5. Rules Checklist

- **ALWAYS** include `--threadId` for replies — omitting it creates a new disconnected thread
- **NEVER** add boilerplate greetings unless explicitly asked
- **ALWAYS** confirm the contact/thread before drafting
- **For reply-all:** include ALL participants from the original To/CC (not just the sender)
- **Subject for replies:** add `Re: ` prefix only if not already there
- **Default account:** `ndr@draas.com` — switch to Gmail or AHFL only on explicit instruction
- **HTML email:** use `--bodyHtml` when the content has tasks, deadlines, or structured data; include `--body` plain text fallback always
- **For new emails to a contact:** use People API to get the email address; don't guess
- **Never send without confirmation** — always present the draft and wait for "send" or equivalent
