# Forward Existing Email + Multi-Topic Body (Jun 2026)

**Trigger:** User says "forward my email about [Topic A, sent to Person X] to [Person Y], CC Person X, add body covering topics B/C/D/E/F."

The user has already sent an email about Topic A to Person X. Now they want to forward that email to Person Y (a different stakeholder), CC the original recipient Person X, and add a NEW body covering multiple unrelated business lines — each with context + specific ask.

## Workflow

### Phase 1 — Find the Original Sent Email

Search Gmail for the sent email the user referenced:

```python
from tools.gws_auth import build_service
service = build_service("gmail", "v1")

# Search sent mail by topic + recipient
results = service.users().messages().list(
    userId="me",
    q="from:me to:person_x_subject_or_keyword",
    maxResults=5
).execute()
```

Get the full headers — you need:
- `Message-ID` (for threading the forward)
- `threadId` (to send in-thread)
- Original Subject (use `"Fwd: [original subject]"`)
- Check for attachments in the original

### Phase 2 — Resolve New Recipient's Email

- Search memory, contacts sheet, session history, Gmail for the new recipient
- When the user gives a partial clue ("yellow something email"), search past sessions for the resolved address
- **Confirm the email with the user before sending** — especially when the user was uncertain about the address themselves

### Phase 2.5 — Grant Document Access (if applicable)

When the forward involves sharing legal opinions, financial models, or analysis documents referenced in the original email:

1. **Identify the specific documents** from the original email context (Drive links, attachments, referenced file names)
2. **Grant Viewer access** to the new recipient on each document (use `drive.permissions().create()`)
3. **Set 1-week expiration** — the user typically expects temporary access: `expirationTime` in RFC 3339 format (e.g. `"2026-07-06T04:24:06.000Z"`)
4. **List each document with its survey number / identifier and link** in the email body so the recipient can open them directly
5. **Attach the main analysis document** to the email itself (MIME attachment) when the user says "put the analysis in the email"
6. **Verify access was granted** — check the permission response

**⚠️ Expiration format pitfall:** Google Drive API accepts `expirationTime` as an RFC 3339 datetime string (`"2026-07-06T04:24:06.000Z"`), NOT as epoch milliseconds (`1783311829101`). Epoch ms format returns `400 Invalid value`.

**Pitfall:** Don't grant access without telling the user. Show the list of documents and expiration period in the draft presentation so the user knows what was shared.

### Phase 3 — Structure the Multi-Topic Body

The user typically enumerates items as numbered topics ("item one... item two... number three..."). Preserve this structure — each topic should be a clear `###` section with:

1. **Context** — brief 1-2 sentence update on where things stand
2. **Ask** — specific question or request for the recipient
3. **Why it matters** — brief connection to the bigger picture, if relevant

**Structural rules from observed user preference:**
- Number or bullet each topic clearly (### or **bold** headers work)
- Use `---` horizontal rules to visually separate topics
- Each topic is its own independent ask — do not cross-reference between topics unless the user did
- End each section with the specific request, formatted as a question or call to action
- Plain text is fine — "no need to use your email text itself is good enough" means no HTML needed for internal/comprehensive status updates

**Example structure from this session:**
```
### 1. Balaji Land Acquisition
[Context: ~4 acres opinion received, balance pending]
[Ask: next steps, site visit, final go-ahead]
[Offer: project plan, cash flow, IRR available]

### 2. Century Regalia — Your Personal Units
[Context: units recipient wanted to buy personally]
[Ask: have you reviewed floor plans? made a decision?]
[Why: this cash flow enables equity for Giraffe investments]

### 3. Serenity Hill View
[Context: Manohar pushing for reconstitution]
[Ask: title update, closure from investors, anything pending from our end?]
```
Preserve the user's ordering — they thought about it in that sequence for a reason.

### Phase 4 — Present Draft for Confirmation

Show the full draft with:
- **To:** [new recipient's full email]
- **Cc:** [original sender's full email]
- **Subject:** `Fwd: [Original Subject]`
- Body with all topics
- List of documents shared with access + expiration (if Phase 2.5 was executed)
- Attachment details (if any)
- **Wait for explicit confirmation before sending or saving**

Include a quick-reference confirmation note for the new recipient's email if the user was uncertain about it:
> Quick reference — [Name]'s email: [email] (the one you mentioned)

**⚠️ Expect a correction cycle.** The user will catch several things — project name spelling, recipient reference format, document links, greeting style, or tone. This is normal. Wait for corrections, apply them, and present the updated draft again. Do NOT send on the first draft unless the user explicitly says "looks good, send it."

**Common corrections observed in session:**
- ❌ Fluff greeting ("Hope you're doing well") → ✅ Removed entirely. User said "I don't insert that in any of my communication unless I explicitly ask for."
- ❌ Wrong project name ("Gold Airport Road Property") → ❌ "OLD No. 5" (agent misheard "Old Airport Road" as "OLD number 5") → ✅ "Old Airport Road" (voice disambiguation needed when digits sound like road names)
- ❌ Wrong spelling ("Certainty Hill View") → ✅ "Serenity Hill View"
- ❌ Wrong person reference ("Manu Ittina") → ✅ "Manu" (just the name, they know which Manu)
- ❌ Missing document links/attachments → Embed links directly in the email body + attach analysis files

### Phase 4.5 — Save as Draft vs Send

The user may want either delivery mode. Listen for their instruction:

| User says | Action |
|-----------|--------|
| "send it", "go ahead", "send the email" | Send directly via `gmail.users().messages().send()` |
| "put it in draft", "create a draft", "I'll send it out from there" | Save as Gmail draft via `gmail.users().drafts().create()` |
| "prepare the new draft and put it in the draft email of Gmail" | Save as draft — user reviews in Gmail, edits, sends manually |

**Save-as-draft flow:**
```python
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode("ASCII")
draft_body = {"message": {"raw": raw}}
draft = gmail.users().drafts().create(userId="me", body=draft_body).execute()
```
The draft appears in Gmail → Drafts where the user can edit and send manually.

**Attachments in drafts:** If the email needs an attachment (HTML analysis, PDF, spreadsheet), include it in the MIME message before saving as draft — Gmail preserves attachments in drafts.

### Phase 5 — Compose, Attach, and Send/Save

Send as a threaded forward using the original email's threadId and Message-ID:

```python
import base64, email
from email.message import EmailMessage
from email.mime.base import MIMEBase
from email import encoders

# Get the original message for forwarding
orig = service.users().messages().get(userId="me", id=orig_id, format="raw").execute()
raw_bytes = base64.urlsafe_b64decode(orig["raw"].encode("ASCII"))
orig_msg = email.message_from_bytes(raw_bytes)
orig_subject = orig_msg["Subject"]
orig_msg_id = orig_msg["Message-ID"]

# Build the forward
msg = EmailMessage()
msg.set_content("Multi-topic body text...")
msg["To"] = "New Recipient <email@domain.com>"
msg["Cc"] = "Original Sender <email@domain.com>"
msg["From"] = "Nishant Ranka <ndr@draas.com>"
msg["Subject"] = f"Fwd: {orig_subject}"
msg["In-Reply-To"] = orig_msg_id
msg["References"] = orig_msg_id

# Optional: attach a file (HTML analysis, PDF, etc.)
with open(local_path, "rb") as f:
    data = f.read()
att = MIMEBase("text", "html", filename=filename)
att.set_payload(data)
encoders.encode_base64(att)
att.add_header("Content-Disposition", "attachment", filename=filename)
msg.attach(att)

raw_b64 = base64.urlsafe_b64encode(msg.as_bytes()).decode("utf-8")

# MODE A — Send directly
sent = service.users().messages().send(userId="me", body={"raw": raw_b64}).execute()
print(f"✅ Sent! ID: {sent['id']}")

# MODE B — Save as Draft
draft_body = {"message": {"raw": raw_b64}}
draft = gmail.users().drafts().create(userId="me", body=draft_body).execute()
print(f"✅ Draft saved! ID: {draft['id']}")
```

**Note for draft mode:** When saving as a forward draft, the `In-Reply-To` header links it to the original thread. The draft will appear in Gmail → Drafts → with the same subject line as the original forwarded email, so the user can send it and it lands in the same conversation.

## Pitfalls

- **Don't guess the new recipient's email** — the user said "yellow something" indicating they're uncertain. Cross-reference past sessions before asking them to reconfirm. The resolved address from a past session (`nishantprakash@theyelloweye.com`) may be correct.
- **Don't combine topics into a single paragraph** — the user enumerated them separately. Respect the separation.
- **Don't write HTML** — plain text body is preferred for these multi-topic internal/partner updates. The user said "your email text itself is good enough."
- **Don't forget the original subject** — the forward should preserve it as `"Fwd: [original subject]"` so the recipient sees the thread context.
- **Don't start the body with a greeting** to the original recipient (Anbu) — the new body is addressed to the new recipient. The forwarded email below contains the original communication.
- **Confirm the CC** — when adding the original recipient as CC, confirm with the user that they want them included.
- **Post-session vocab update** — After completing, offer to compile corrected terms (project names, person names, corrected spellings) into the user's STT vocabulary. See `references/stt-vocabulary-update-workflow.md` for the full workflow.
