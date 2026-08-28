# User-Specific Delivery & Review Preferences

Different users at DRAAS have distinct approval workflows before a draft (WhatsApp link or email draft) can be delivered. Consult this file based on the current `HERMES_SESSION_USER_ID` before composing any outgoing message.

## Bharat Hawaldar ([REDACTED-TID] — sales1.blr@draas.com)

### "Draft-first for Nishant & external stakeholders"

Bharat requires **all drafts intended for Nishant (ndr@draas.com) or any external stakeholder to be shown to him for review first** before generating the link or delivering the message.

**Workflow:**
1. Compose the draft (WhatsApp message or email text)
2. **Present the full draft text in Telegram** for Bharat to review
3. Wait for explicit approval: "go ahead", "approved", "correct", "looks good", "send"
4. Only after approval: generate the wa.me link or create the Gmail draft
5. Never skip to delivery — Bharat explicitly corrected this pattern (Jul 2026): when a draft was sent to Nishant without prior review, he said "No, no, no. Just stop it."

**What this covers:**
- WhatsApp messages intended for Nishant or clients
- Email drafts to Nishant or third parties
- Summaries or reports meant for Nishant's review
- Any communication where Bharat is the intermediary between Hermes and the recipient

**Client-facing emails — even creating the Gmail draft is premature (verified 2026-08-25):** For emails Bharat will send to external clients/customers, do NOT call `draft_create` (or any Gmail action) on first pass. Bharat corrected this explicitly — after a draft was auto-created in his own Drafts folder (sales1.blr@draas.com) with account details for a client, he said "Before sending that email, I want you to share me the final draft over here" and "I don't want you to send any email first thing... let's make a draft properly." Workflow that satisfies him:
1. Compose the full email text
2. **Present the complete draft text in Telegram** (To / Subject / Body) — the deliverable is the text itself
3. He reviews, may dictate changes (greeting, tone, placeholders), and may ask for it as a Word doc + Drive link ("Maybe I can do this draft on a word and share the link")
4. Only on his explicit go-ahead: create the Gmail draft (or the .docx) — he still sends it himself

**Exception:** If Bharat says "send this directly", "you can send", "go ahead" — explicit permission overrides the review requirement. Do NOT re-ask.

### "First tell me the process" — Decision transparency

Bharat prefers to understand the proposed workflow before execution. When he asks "tell me the process first", provide a concise step-by-step outline of what you plan to do, then pause for confirmation before executing. Pattern confirmed in multiple sessions.

### Phone number display: no `+` prefix

When displaying phone numbers in Excel cells, Sheets cells, or any written output, use `91XXXXXXXXXX` (12 digits, no `+`). This is a cosmetic preference — confirmed Jul 2026.

## Nishant Ranka ([REDACTED-TID] — ndr@draas.com)

### "Direct + efficient"

Nishant prefers minimal confirmations and fast turnaround. For his drafts:
- Compose and present one variant (don't offer multiple options)
- Generate the wa.me link or draft immediately when the tone register is clear
- Skip the review step unless the content is complex or involves legal/new third parties
- He still needs Kelsa OAuth authorization for pipeline queries — be prepared to send the Auth button promptly

## Roshni Ranka (7249813913 — rnr@draas.com)

No specific delivery preferences captured yet. Default to the skill base workflow (show draft, confirm, then deliver).

## Key principle

When the current session user is NOT the intended recipient of the draft, **always default to showing the draft to the session user first** before any external delivery. The session user is your direct interlocutor — they control what leaves their channel.
