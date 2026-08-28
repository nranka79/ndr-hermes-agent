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
version: 2.4.0
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

If `google_workspace_manager` is not exposed in the current session's tool list, fall back to `terminal` with the Hermes venv Python:

```
# Example: create a threaded reply draft
cd /opt/hermes && /opt/hermes/.venv/bin/python3 -c "
from tools.gws_skill_bridge import call
result = call('draft_reply_create',
    service_name='google-draas',
    message_id='...',
    to='Recipient <email@example.com>',
    cc='Other <email2@example.com>',
    body='Email body text',
    html=False)
print(result)
"
```

The bridge mirrors these operations: `call("draft_create", service_name="google-draas", ...)`, `call("draft_reply_create", ...)`, `call("gmail_thread_get", ...)`, etc.

**IMPORTANT — do NOT use `execute_code` for gws bridge calls.** The `execute_code` sandbox lacks the `gws_fetch_token` import needed by the vault credential loader. Gmail/Calendar/Drive operations through the bridge will fail with `ImportError: cannot import name 'gws_fetch_token'`. Always use `terminal` with `/opt/hermes/.venv/bin/python3` instead.

**To search Gmail or read thread content when `google_workspace_manager` is unavailable**, use the raw Gmail API directly from terminal:

```bash
cd /opt/hermes && /opt/hermes/.venv/bin/python3 << 'PYEOF'
from tools.gws_auth import build_service
import base64, json

service = build_service("gmail", "v1", service_name="google-draas")

# Search for messages
results = service.users().messages().list(
    userId='me', q='from:someone subject:"topic"', maxResults=5
).execute()

for msg in results.get('messages', []):
    detail = service.users().messages().get(
        userId='me', id=msg['id'], format='metadata',
        metadataHeaders=['Subject','From','To','Cc','Date']
    ).execute()
    h = {x['name']: x['value'] for x in detail['payload']['headers']}
    print(f"Thread: {detail['threadId']} | Subject: {h.get('Subject')}")

# Read full body from a message
full = service.users().messages().get(userId='me', id=MSG_ID, format='full').execute()
def get_body(payload):
    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain' and part['body'].get('data'):
                return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            if 'parts' in part:
                nested = get_body(part)
                if nested: return nested
        if payload['body'].get('data'):
            return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    elif payload['body'].get('data'):
        return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    return None
body = get_body(full['payload'])
PYEOF
```

Use `build_service` from `tools.gws_auth` (NOT the bridge's internal `_build_service`) when you need the full Gmail API surface — searching, reading bodies, fetching threads with format='full', etc. The `gws_skill_bridge` is sufficient for creating drafts once you have the thread context.

## Trigger Conditions

Activate when the user says anything like:
- "Email Raghu about the land valuation"
- "Reply to Nishant Prakash's email about Oasis"
- "Draft an email to Manohar about the project update"
- "Reply all to the email from Bhavesh"
- "File an insurance claim", "reimbursement claim", "pre-operative expenses" → load `references/insurance-claim-reimbursement.md` for the document inventory checklist and completeness validation
- **TPA asks for originals / portal re-submission** → load `references/irdai-original-documents-guidelines.md` for IRDAI regulatory citations to push back

**Default account:** `ndr@draas.com` for ALL emails unless the user explicitly says:
- "use my Gmail account" → `nishantranka@gmail.com`
- "use AHFL account" → `ndr@ahfl.in`

**Bharat's lead-outreach emails — sender is `sales1.blr@draas.com` (verified 2026-08-25):** When the session user is Bharat and the email targets a Ranka Udaya / portal lead customer (booking-amount account details, project handoff, title-deed follow-up), draft from his SALES mailbox, NOT ndr@draas.com. Verified recipe:

```bash
HERMES_SESSION_USER_ID=sales1_blr GWS_VAULT_SOCKET=/run/gws-vault/vault.sock \
  /opt/hermes/.venv/bin/python3 -c "
from tools.gws_skill_bridge import call
call('draft_create', service_name='google-draas',
     to='customer@example.com',
     subject='Ranka Udaya - Block 5 - ...',
     body='...', html=False)"
```

Lands as `BHARAT H <sales1.blr@draas.com>` with label DRAFT (verify via `drafts().list()`). Before drafting to a lead, look the customer up in **Kelsa Pipeline 10 by name** to address them properly — e.g. `roy.pragyajyoti@gmail.com` resolved to Pragya Joythi (lead #54917102, Hot, assigned to Bharat). The customer's email supplied by the user in chat is authoritative for `To`; create as DRAFT only, never auto-send.

**Plot booking-confirmation emails (congrats + booking-amount receipt + legal pack + receipt-follows-EOD):** full proven workflow in `references/plot-booking-confirmation-email.md` — pull the booking amount from the Kelsa lead notes (never invent it), attach the compressed legal pack via raw Gmail API (bridge has no attachment support), draft-only from the sales mailbox.

**Booking-confirmation / congrats emails — quote the EXACT amount from the lead's notes (2026-08-25):** When Bharat dictates a congrats email ("congratulate him for booking, confirm receipt of the amount transferred"), the authoritative figure is the Kelsa lead's notes, NOT memory or the voice dictation: `list_lead_notes(pipeline_id=10, lead_id=...)` — Bharat logs settlements like "The client has transferred the ₹50,000 booking amount, and the same has been received and confirmed with the client." Quote that exact figure in the draft ("We confirm the receipt of your booking amount of ₹50,000"). If the notes contain no received amount, ask Bharat — never guess or leave a placeholder. Booking-congrats emails follow the dictated structure: congratulations → amount-received confirmation → attached legal docs (per commitment) → receipt follows by stated EOD.

**NDR uses ONLY ndr@draas.com as his work account (user-stated 2026-08-17).** If the user asks to find a work email and it's not in draas.com, do NOT keep re-attempting ahfl.in or ask them to re-auth it — he does not use ndr@ahfl.in for work at all. Skip it.

**"Did I email X about Y?" search pattern (validated 2026-08-17, Siddhapura/Glenmore case):**
1. Search draas.com FIRST with ALL spelling variants (people search on "Siddhapura" returned 0 while "Siddapura" returned hits; place names garble in memory/voice).
2. Check sent, inbox AND drafts (a draft is a legit "I wrote it" artifact).
3. If it's genuinely absent, say so plainly and pivot — do NOT just stop. Check the other stores where the context may live (Drive fullText, gbrain, Kelsa pipelines, session history), collect the artifacts, and offer to draft the follow-up email (To the colleague, CC the user-named others) since the assignment was clearly made verbally.
4. Verify every recipient via find_contact.py before drafting.

**Sender must match recipient family — AND topic:** Family emails split on content, not just relationship:
- **Personal/family matters** (kids' school, health, social) → use `nishantranka@gmail.com` (confirmed 2026-07-13)
- **DRA business / company / legal matters** (succession petitions, shareholder agreements, family settlements, court filings) → use `ndr@draas.com` even when the recipient is extended family (brother-in-law, sister, sister-in-law). The content is DRA-governance, not personal, so the work account is correct (validated 2026-08-27, Ranjeeth Rathod/Mamata Rathod/Roshni Ranka succession petition email)
- **When ambiguous:** confirm with the user before drafting.

**DRA-group / director work always uses `ndr@draas.com`** (user correction 2026-07-13: "No use ndr@draas.com for all work"): even if the user is a director of a DRA-group entity (DRA Aadithya / DRAAPPL, DRA Aadithya South City / DRAAS, Truliv, DRA Homes, etc.) AND is reading the notice in personal Gmail, the draft + Drive filing + Calendar event must all go in `ndr@draas.com`. The personal Gmail is just the inbox where the notice arrived; the work artefacts live in the work account. Confirm work account explicitly when the user says "file this" or "draft this" about a director-of notice and the inbox is personal Gmail.

- **IRDAI original-documents pushback:** When drafting an insurance-related reply where the TPA/insurer demands original medical records or portal re-submission, load `references/irdai-original-documents-guidelines.md` for the specific Master Circular citations and rebuttal language. Add these citations to the email body as a factual paragraph before the escalation ask.
- **Drug-alternative request to doctors** (drug out of stock, need alternative generic recommendation): load `references/charitra-medical-communication.md` for the correct account (google-draas, NOT ahfl), doctor emails (samdoc_mamc@yahoo.com for Dr. Sameer, anniekbaa@gmail.com for Dr. Annie), active thread, and drug-alternative email pattern. Verify every recipient from thread headers — never guess medical email addresses.

- **DEFER** to the `regulatory-complaint-escalation` skill if the email is:
- A formal complaint to a regulated counterparty (insurer, bank, NBFC, telco)
- Escalating to a GRO / Principal Nodal Officer / Internal Ombudsman
- Citing IRDAI / RBI / TRAI / SEBI regulations with a regulator-portal threat
- Part of a multi-month dispute where normal channels have been exhausted
The complaint skill produces a structured 5-section email + a Google Doc plan, which is wrong shape for the normal business reply path here.

## 2. Stage 1 — Context Gathering

### For a NEW email

**ALWAYS use the contact lookup tool FIRST — HARD RULE (corrected 2026-07-31).** Any email-address lookup starts with `scripts/find_contact.py` from the `personal-messaging` skill, in the same session, immediately:

```bash
/opt/hermes/.venv/bin/python /data/hermes/skills/productivity/personal-messaging/scripts/find_contact.py "<name or number>"
```

The script queries Google People API AND both DRA contacts sheets in one shot (with automatic vault-socket recovery) and prints labelled phones + emails. If it finds the person, confirm the address with the user before drafting (matches may be ambiguous or outdated). Never guess an email address, never rely on memory alone, never fall back to a raw sheet read.

Only if the tool returns nothing: escalate down the chain (memory spelling cross-check → Gmail thread search → ask the user). Full priority chain lives in the `personal-messaging` skill.

When a match is found, confirm with user:
> Found: **Raghu Iyer** — Director, [Company]
> Drafting to raghu@example.com (work). Say if you want a different address.

When no match: report clearly and ask for the address — do not invent one.

**Pitfall — contact-sheet address can be stale/dead (2026-08-12):** find_contact.py may return an old address that the person no longer uses (e.g. Anbu/Anbarasan → sheet says anbarasandraass@gmail.com, last used 2017 and defunct; his ACTIVE address is anbarasan@draas.com from Jul–Aug 2026 threads). Before drafting, cross-check the person's most recently used address by searching Gmail (`q=<name>` via `build_service('gmail', 'v1')`, inspect latest To/From). A dead address also fails Drive permission grants with HttpError 400 `invalidSharingRequest` — same fix applies. When you use a non-sheet address, tell the user why (e.g. "the gmail.com address in the sheet is stale — using the active draas.com one").

**Pitfall — in-house staff and long-standing partners have NO contacts-sheet row at all (2026-08-25):** find_contact.py (and contact_resolver) return zero matches for internal DRAAS people and frequent external partners — e.g. Sinchana Gowda (sgowda@draas.com, in-house architect/design covering Palya, Serenity Hill View, Oasis) and Arvind Jain (arch_arvind2000@yahoo.co.in, A.J. Architects). These people don't live in the contacts sheet, so "tool returns nothing" must NOT stop the draft. Resolve them from Gmail: `q='"Full Name" OR from:<domain>'` and read From/To/Cc headers across recent threads (`q='sinchana'`, `q='from:arch_arvind2000'`). Headers are the authoritative address for both the To field and Drive permission grants. Only after a Gmail search also fails should you ask the user for the address.

### For a REPLY (existing thread)

**Pitfall — the email to reply to is a FORWARD where the original thread is NOT in the user's mailbox (2026-08-27, Ruhaan school absence):** When a family member (Roshini) forwards a school/third-party email to NDR saying "please handle this," the original thread (teacher ↔ Roshini) is NOT in NDR's mailbox — only the single forwarded message exists there. This breaks the standard reply flow:

1. There is no threadId to use for a threaded reply from NDR's account. `draft_reply_create` cannot work because the source message_id belongs to Roshini's mailbox.
2. Recipients must be extracted from the forwarded body text — parse the "Begin forwarded message" block for From, To, Cc, and Subject. Do NOT search for a thread that doesn't exist.
3. The draft must be composed as a FRESH message (`draft_create`, not `draft_reply_create`), with:
   - To = the teacher (From of the forwarded original)
   - Cc = original Cc (minus self), plus the family member who forwarded it (Roshini), plus any additional people the user names (e.g. Ruhaan, Joel)
   - Bcc = any person the user wants blind-copied
   - Subject = `Re: <original subject from the forwarded block>`
4. There is no In-Reply-To/References to set — this is a new message on a new thread. The subject prefix `Re:` is a courtesy convention only.
5. Verify recipients with the user: the person who forwarded the email often knows who should be included that isn't obvious from the forwarded headers (e.g. Joel the administrator, Ruhaan himself).
6. When the user names an ADDITIONAL recipient who is NOT visible in the forwarded headers (e.g. "BCC Joel, he's also an administrator"), check the contacts sheet first via contact_resolver. If the contact exists but has NO email (common — phone-only entries), search Gmail history across ALL accounts (google-draas, google-ahfl, google-gmail) for the person's name. An old CC'd email from years ago is often the only source for their email. Pattern that worked (Aug 2026, Joel Kribairaj at Aditi school):
    - contact_resolver confirmed the contact existed: phone +919972072401, no email
    - Gmail search across all accounts with query `q="joel" AND (gsuite.aditi.edu OR aditi.edu.in)` and `q="kiribayaraj OR kiruba"`
    - Found in a March 2024 Science Club email from Jayashree KG: `Joel Kribairaj <joel@aditi.edu.in>` (CC'd)
    - Update the contacts sheet row with the found email via contact_learner/update
    - Use it for BCC in the draft
    - If Gmail search across all accounts returns nothing, THEN ask the user.
7. Before finalising, verify the person's email via a real message header (not the contacts sheet value) — confirm the spelling matches the mailbox (Kribairaj vs Kiribayaraj). The user's voice transcription of the name may differ from the sheet's canonical form.

Search pattern for forwarded emails: the user says "there's an email from Ruhan's school" or "reply to this email." Check if it arrived as a forwarded message (Subject: "Fwd: ...") or a direct email. If forwarded, the original may be in another mailbox — work with the forwarded body, don't hunt for a non-existent thread.

**Pitfall — reply to the ORIGINAL email, not your forward of it (2026-08-27, Viraj Godrej 4.5 FAR Drawings):** When the user receives an email from someone, forwards a copy of it to a colleague for action, and then later asks you to "reply all" to the original sender — there are now TWO copies of that email in the mailbox: the original thread and the user's forward. The user will explicitly clarify: "reply all to the email received from [sender], not the one I forwarded to [person]."

1. Search by the **sender's email address**, not by subject keywords — the forward has the same subject but different sender (the user themself).
2. Verify the thread belongs to the original sender: check the `From` header of the first message in the thread.
3. If the user mentions having forwarded the email to someone earlier in the same session, proactively ask which thread they mean before drafting — "The original from Viraj, or the copy you forwarded to Anbu?" This saves a correction.
4. When the user says "reply all to the email received from [name]" — that unambiguously means the original thread, not the forward.

**Related: SharePoint/OneDrive link access problem (2026-08-27, Viraj Godrej 4.5 FAR Drawings):** When the user can't download a file from a SharePoint/OneDrive link (requires Microsoft sign-in, and the user's domain — e.g. ndra.dra.homes.in — has no Microsoft login), the email draft will:
- State the problem factually: "I tried signing in but [domain] is just a domain name — I don't have a Microsoft login there."
- Request the file via an alternative: "please attach the file and send it, or share it via VTransfer / any other modality from which I can download it."
- Explain what it's for: "I will share it with the [team] so they can give us a quotation to get the process started."
- Add urgency: "This is a bit urgent… we have already lost enough time on this matter."

**Pitfall — the counterparty's reply may NOT be in the thread you sent from (confirmed 2026-08-13, Sanjay Sethia succession-certificate matter):** the recipient replied from the same domain (sanjay@lawsquare.in → nishanth@lawsquare.in) but as a NEW email — different subject ("Succession Certificate (Dinesh Ranka)" vs our "Priority: … Review of Draft Petition"), `In-Reply-To: None`, its own thread ID. Listing only the sent thread misses their response entirely. When the user says "we got a reply", search the whole account by domain/name (`q='lawsquare.in newer_than:7d'`) across ALL vault accounts (google-draas, google-gmail, google-ahfl) before concluding. Draft the reply against the counterparty's message ID so it threads on THEIR side.

**Pitfall — email body attachment lists can lie (2026-08-13):** the sent email claimed "Attached: petition, death certificate, family tree, Aadhaar cards" but only 3 files were actually attached (Aadhaar was listed, never sent). When the user asks "did the attachment actually go?", do not trust the body — walk the message payload via `messages().get(format='full')` and enumerate `payload.parts[].filename` for each message in the thread.

Search Gmail for the thread using the `google_workspace_manager` tool:
```
tool: google_workspace_manager
input:
  command: "gmail messages list --params '{\"maxResults\":5,\"q\":\"from:raghu subject:land valuation\"}'"
  account_email: "ndr@draas.com"
```

**Pitfall — `q='threadId:...'` silently returns nothing (confirmed 2026-08-01):** the Gmail API
`messages().list(q='threadId:XXX')` search operator is unreliable — it returns an EMPTY result even
when the thread exists. Do not use it to locate thread messages. Instead fetch the thread directly:

```python
from tools.gws_auth import build_service
service = build_service("gmail", "v1", service_name="google-draas")
t = service.users().threads().get(userId='me', id=THREAD_ID, format='metadata').execute()
for msg in t['messages']:
    h = {x['name']: x['value'] for x in msg['payload']['headers']}
    print(msg['id'], h.get('Date'), h.get('From'))
```

This also gives you the message IDs needed for `draft_reply_create(message_id=...)` when the last
message in the thread is from the user themselves (see "Threaded reply — last message is from you").

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
- **Family (kids, spouse, parents):** Always personal tone; same content can go to multiple family members in ONE email using To + CC — do NOT create a separate draft per recipient (user correction 2026-07-13: "I need only one draft email. Why four drafts? This is one email.")
- **Extended family (brother-in-law, sister, sister-in-law):** Personal tone and family address ("Dear Jai ji") even when the content is business/legal — use warm opening but structured body with numbered items. Sender is ndr@draas.com when the content relates to DRA governance/estate matters (validated 2026-08-27, Ranjeeth/Mamata/Roshni succession petition email). See `references/family-legal-document-sharing.md` for the full pattern.

### School / authority communication tone (polite-cooperative, 2026-08-27)
Used when emailing teachers, school administrators, or any institutional authority (government offices, regulatory bodies, RERA authorities). The goal is to express a concern or push back politely while remaining cooperative and seeking understanding — NOT confrontational or demanding.

Structure and language principles:
- **Open with appreciation:** Thank them first — acknowledge their response, accommodation, or effort before raising the question. This sets a collaborative tone.
- **State the medical/known context factually:** "Ruhaan has an established medical pattern — whenever he contracts a viral infection, it triggers an asthmatic flare-up resulting in a persistent cough. This is a known, recurring issue." Frame it as context-sharing, not excuse-making.
- **Explain the action taken (and why no doctor visit):** "Following our doctor's standing advice for this known pattern, we have started him on azithromycin without a hospital visit this time. There may be no clinical benefit in taking him to a doctor unless his condition deteriorates."
- **Acknowledge their requirement/position:** "We fully understand the school's need to maintain proper records."
- **Express the concern as a question, not an objection:** Frame it as seeking understanding: "We would like to understand the basis for this requirement — is it mandated by IGCSE/board rules, or is it a school policy for record-keeping?" Never say "this is unnecessary" — say "an unnecessary visit would put him under additional strain and risk of infection for a known medical issue."
- **Offer alternatives proactively:** "We are happy to share a video or any other form of proof. If there is an alternative medium that satisfies your requirement without a medical visit, we would be grateful for your guidance."
- Close with warmth and cooperation: "We would be grateful for your guidance so we can find the best way forward for Ruhaan."

**Related:**  `references/school-absence-medical-cert-required.md` — full workflow when the school insists on a certificate as SOP (Grade 9+ board requirements, known chronic condition, WhatsApp the family doctor, reply with attached cert + BCC admin).
**Related:** For a simpler notification-only absence + exam-accommodation email (not challenging a policy, just informing and requesting), see `references/school-absence-exam-accommodation.md`.

**Discovery tip — school Welcome PDFs are the authoritative source for teacher roles:** When emailing a school and unsure who the actual class teachers are (versus who handles attendance), search Gmail for the school's welcome/introductory email at the start of the academic year — `subject:"Welcome" from:<school-domain>`. The attached PDF usually lists class teachers + teaching team explicitly. Run `pdftotext` or `pymupdf` on the attachment to extract the names. Example: Aditi Std 07 SS Welcome PDF showed Neetu Shrivastava + Subath Senan as class teachers, while the person handling the leave note (Ranjitha Tikandar) was not a class teacher at all. This avoids the common trap of assuming the attendance-contact person is a class teacher.

Key distinctions from vendor-feedback tone:
- ❌ No competitive pressure ("commissioned a parallel test")
- ❌ No disappointment framing ("we are extremely disappointed")
- ❌ No consequences set ("this is our last effort")
- ✅ Positive, cooperative, appreciative throughout
- ✅ Frame the underlying question as seeking understanding
- ✅ Offer alternatives before asking for exceptions

### Vendor-feedback / frank escalation tone (user preference, 2026-08-17)
Used when delivering formal feedback to a vendor/service provider whose product has underperformed. NDR's explicit direction: "as frankly as possible without doing any threats."

Structure:
1. **State the situation factually** — what was tested, how many calls/transcripts, what methodology (recorded → transcribed → cross-checked against verified data).
2. **Name the failures concretely** — data errors, latency, missing features. Quote specific numbers (percentages, call counts) so the feedback is undeniable.
3. **Mention alternatives if they exist** — "we have commissioned a parallel test with another provider. In the very first cut, it was absolutely brilliant — correct accent, facts right, conversation handled naturally." This frames the conversation as competitive, not remedial.
4. **Express disappointment factually** — "we are extremely disappointed that your product experience is so poor, especially for a team that advertises heavily. Right now it feels half-baked — not even an alpha."
5. **Set a clear consequence as a fact, not a threat** — "This is our last effort to get a product that meets basic requirements. If this still fails, we will withdraw from this pilot." NEVER say "we may be forced to reconsider" or "we have limited bandwidth" — that's hedging, not frankness. State the consequence plainly.
6. **Close with an action request** — "kindly do the needful urgently so we can test again." Professional, no anger, just clarity.

Key rules:
- No threats, no aggression, no rhetorical questions. The evidence does the work.
- Mentioning another provider is acceptable and adds competitive pressure without threatening language.
- If the vendor advertises heavily, it's fair to note the gap between marketing and delivered product — this is a factual observation, not a personal attack.
- Keep attachment evidence (PDF feedback, data sheets) bundled in the email so they can verify every claim.

### One draft, multiple recipients (To + CC)
When the same content goes to several people, create a single draft with multiple To addresses and CC the rest. Do NOT spawn one draft per recipient.

`google_workspace_manager` supports this directly:
```
tool: google_workspace_manager
input:
  command: "gmail messages send --to a@example.com,b@example.com --cc c@example.com,d@example.com --subject '...' --body '...'"
  account_email: "nishantranka@gmail.com"
```

For HTML: add `--bodyHtml '<p>...</p>'` alongside `--body`. Confirm the full recipient list (To + CC) with the user before drafting.

If using the underlying `gws_skill_bridge` Python module instead (e.g. from a venv script), `draft_create` accepts flat `to=`, `cc=`, `subject=`, `body=` kwargs:
```python
from tools.gws_skill_bridge import call
call("draft_create", service_name="google-gmail",
     to="rankarivaan@gmail.com,pebblyshark69@gmail.com",
     cc="rnr@draas.com,Rmurjani@gmail.com,nishantranka@gmail.com",
     subject="⚽ FIFA World Cup 2026 — Polymarket & Kalshi odds",
     body=html_body,
     html=True)   # <-- required when body is HTML; without it the draft is plain-text and your markup is sent as raw literal characters
```
The bridge handles MIME multipart and base64 internally — no need to build MIMEMultipart yourself. Use comma-separated addresses (no `Name <addr>` formatting needed; the bridge adds display names from contacts if you pass bare emails).

**Full workflow reference:** `references/drive-to-draft-pipeline.md` — covers finding files on Drive, downloading, categorizing, building the MIME message, and deduplicating. Use it whenever the draft needs multiple Drive-sourced attachments.

**New-draft-from-Gmail-attachments:** `references/gmail-to-drive-to-draft.md` — covers extracting attachments from prior Gmail emails, renaming per NDR naming convention (YYYYMMDD_Entity_Description), uploading to the right Drive folder for archival, then creating a fresh draft to a NEW recipient with those Drive files attached. Use this when the user says "find the floor plans I sent to [person], rename and file them, and send to [new recipient]."

**Repurposing a prior chain to a new recipient** ("send the same briefing + attachments to advocate Y"): `references/repurpose-email-chain.md` — search multi-thread by subject keyword, read all bodies, collect attachments across ALL messages/threads (petition may be on one thread, supporting docs on another), rebuild MIME with raw Gmail API, verify via `drafts().list()`. Session-validated Aug 2026 (succession certificate → Sanjay Sethia).

**Pitfall — `threads().get(format='raw')` is NOT a valid parameter (confirmed 2026-08-02):**
The Gmail API `threads().get()` only accepts `format` values `['full', 'metadata', 'minimal']` — passing `'raw'` raises `TypeError: Parameter "format" value "raw" is not an allowed value`. This traps you when building a threaded reply draft that needs the latest message's `Message-ID`/`References` headers. The fix is a two-step fetch:
```python
t = service.users().threads().get(userId='me', id=THREAD_ID, format='metadata').execute()
latest_msg_id = t['messages'][-1]['id']
latest = service.users().messages().get(userId='me', id=latest_msg_id, format='raw').execute()
raw_bytes = base64.urlsafe_b64decode(latest['raw'].encode('ascii'))
# then regex Message-ID / References out of the raw text
```
`messages().get()` DOES support `format='raw'`; only the thread-level call rejects it.

**Pitfall — raw-regex Message-ID extraction is fragile; use metadataHeaders instead (2026-08-25):** `re.search(rb'Message-ID:\s*(\S+)', raw_bytes)` on the raw MIME once captured garbage (`subject:date:mime-version:from`) instead of the real Message-ID, silently producing a malformed In-Reply-To/References on a threaded draft. Prefer fetching headers directly — no raw decode, no regex:

```python
latest = service.users().messages().get(userId='me', id=latest_msg_id, format='metadata',
    metadataHeaders=['Message-ID','References','In-Reply-To']).execute()
heads = {x['name'].lower(): x['value'] for x in latest['payload']['headers']}
src_mid = heads.get('message-id','').strip()
assert src_mid.startswith('<') and src_mid.endswith('>'), f"BAD MID: {src_mid!r}"
```

**Pitfall — `draft_reply_create`/`draft_create` do NOT support BCC (2026-08-27, Ruhaan school email):**
Neither operation in `gws_skill_bridge` accepts a `bcc` parameter. If the user wants someone blind-copied, you MUST fall back to the raw Gmail API using `email.message.EmailMessage`:

```python
from email.message import EmailMessage
import base64
from tools.gws_auth import build_service

svc = build_service('gmail', 'v1', service_name='google-draas')

msg = EmailMessage()
msg.set_content('Email body text here')
msg['To'] = 'Primary <primary@example.com>'
msg['Cc'] = 'Cc1 <cc1@example.com>, Cc2 <cc2@example.com>'
msg['Bcc'] = 'Blind <blind@example.com>'
msg['Subject'] = 'Re: Original Subject'

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii')
draft = svc.users().drafts().create(userId='me', body={
    'message': {'raw': raw}
}).execute()

# Verify
verify = svc.users().drafts().get(userId='me', id=draft['id'], format='full').execute()
headers = {h['name']: h['value'] for h in verify['message']['payload']['headers']}
assert 'Bcc' in headers, 'BCC header missing in draft — use raw API, not bridge'
assert 'DRAFT' in verify['message'].get('labelIds', []), 'Not a draft!'
```

The Bcc header MUST be set on the `EmailMessage` object before encoding — it will NOT appear in the `drafts().get()` returned headers on Gmail's side (Gmail strips Bcc from API responses for security), but it IS present in the MIME and will be sent correctly. Verify by checking that the draft shows up in the correct mailbox with correct To/Cc visible.

**Pitfall — `draft_reply_create`/`draft_create` do NOT support attachments (2026-07-15):**
Neither operation in the `gws_skill_bridge` accepts file attachments. The MIMEText-based body construction has no provision for multipart/mixed. If your draft needs a PDF, image, or any file, you MUST fall back to the raw Gmail API:

1. Build a `MIMEMultipart("mixed")` message manually (HTML body part + MIMEBase attachment parts)
2. Base64-encode the whole message and call `service.users().drafts().create()` directly with `threadId`
3. Use `tools.gws_auth.build_service("gmail", "v1", service_name=...)` — NOT `gws_skill_bridge._build_service()` (see next pitfall)

See `templates/draft-with-attachments.py` in this skill for the full working recipe.

**Pitfall — Gmail attachment cap is on the ENCODED size, not the raw file (2026-08-25):**
`draft_create`/`draft_reply_create` build MIME internally — the size that decides
sendability is the base64url-encoded `raw` field, which is ~16/9 ≈ 1.78× the raw
PDF (base64 inside MIME ×4/3, then the MIME itself base64url-encoded ×4/3 for the
API). The Gmail API cap is **35 MB encoded**, so the attachment PDF must be
≤ ~20 MB — do NOT treat "25 MB" as the raw-file limit, and do NOT trust a
36 MB → 25 MB /ebook compression as "done" (observed: 36 MB pack → 25.18 MB with
/ebook → `len(raw)` = 43.3 MB = would FAIL on send).

Always print the encoded size from the build script
(`print(round(len(raw)/1048576, 1))`) and confirm ≤ 35 MB before declaring the
draft done. If you already created the draft with an oversized attachment:
`drafts().delete(userId='me', id=<draft resource id, NOT message id>)`, then
recreate with the compressed file (same mailbox, verified via drafts().get walk
of payload.parts for the attachment filename + size).

**Recipe that actually got a 225-page / 36.4 MB compiled pack to 19.2 MB legible (2026-08-25, Ranka Udaya pack):**
`/ebook` alone only reached 25.2 MB → still 43.3 MB encoded (FAIL). The pass that
worked combined `/screen` with explicit image downsampling:

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \
  -dColorImageDownsampleType=/Bicubic -dColorImageResolution=90 \
  -dGrayImageDownsampleType=/Bicubic -dGrayImageResolution=115 \
  -dMonoImageResolution=160 -dNOPAUSE -dBATCH -dQUIET \
  -sOutputFile=out.pdf in.pdf
```

19,156,889 bytes (19.2 MB) → `len(raw)` = 32.9 MB → SAFE. Verify legibility before
attaching: render 2–3 sample pages with `pdftoppm -png -r 100 -f N -l N` and OCR/
vision-check that text still extracts. 100–130 DPI grayscale keeps scanned deed
text readable; below ~90 DPI it degrades.

For a 30–40 MB multi-page scanned legal pack, `/ebook` is insufficient — use
`/screen` with explicit downsampling (observed: 36 MB → 19.2 MB → encoded
32.9 MB = PASS, 225 pages preserved):

```bash
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/screen \
  -dColorImageDownsampleType=/Bicubic -dColorImageResolution=90 \
  -dGrayImageDownsampleType=/Bicubic -dGrayImageResolution=115 \
  -dMonoImageResolution=160 -dNOPAUSE -dBATCH -dQUIET \
  -sOutputFile=out_email.pdf in.pdf
pdfinfo out_email.pdf | grep Pages   # must match pdfinfo in.pdf
```

After aggressive compression, spot-check legibility before attaching:
`pdftoppm -png -r 100 -f <p> -l <p> out_email.pdf /tmp/p` on 2–3 pages (title +
a scanned deed page + one mid-pack page) and OCR/vision them — scanned deeds
degrade fast below ~115 DPI grayscale; if unreadable, raise GrayImageResolution
and re-verify.

Attach the compressed copy but keep the ORIGINAL customer-facing name in the
MIME display filename (local file can be `*_email.pdf`, display as e.g.
`Ranka Udaya - Legal Document Pack.pdf`). Observed (Gunjur Will chain email):
29 MB 12-page 1990 sale deed → 2.7 MB, 12 pages preserved, sent fine.

**Pitfall — attaching a Google-native file (Sheets/Docs/Slides) requires export FIRST (2026-08-01):**
A Google-native spreadsheet has no binary payload to attach — `MIMEBase` needs a real file on disk. Export it via the Drive API to xlsx before building the MIME message:

```python
from googleapiclient.http import MediaIoBaseDownload
import io

req = drive.files().export(
    fileId=SHEET_ID,
    mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)
fh = io.BytesIO()
dl = MediaIoBaseDownload(fh, req)
done = False
while not done:
    status, done = dl.next_chunk()
open('/tmp/charges.xlsx', 'wb').write(fh.getvalue())
```

Then attach `/tmp/charges.xlsx` as a MIMEBase part with `Content-Disposition: attachment` and the human-friendly filename (spaces/dashes OK). This is the pattern for "attach this Google Sheet to my reply" requests — the recipient receives a real .xlsx, not a link.

**Pitfall — Gmail 25 MB attachment cap: compress scanned PDFs before MIME build (2026-08-25).** Certified-deed scans routinely exceed the cap (observed: 1990 Doddaballapur sale deed = 29 MB / 12 pages → draft rejected on send). Compress first with `gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dBATCH -dQUIET -sOutputFile=out.pdf in.pdf` (29 MB → 2.7 MB on a 12-page scan), then verify `pdfinfo` page count matches the original BEFORE building the MIME message — never attach an un-checked compressed copy. Keep the original Drive file as the source of truth; the compressed copy is for sending only.

**Pitfall — `_build_service` vs `build_service` account resolution (2026-07-15):**
`gws_skill_bridge._build_service(api, version)` does NOT accept a `service_name` parameter and defaults to `google-draas` (ndr@draas.com). If your thread lives in a different account (e.g. `google-ahfl` for ndr@ahfl.in), the API call for `messages().get()` will return HttpError 404 because the message doesn't exist in the default account.

Fix: import from `tools.gws_auth` directly:
```python
from tools.gws_auth import build_service
service = build_service("gmail", "v1", service_name="google-ahfl")
```
Resolve the correct service_name first via `gws_resolve_account(account="ahfl")`. Never use the bridge's internal `_build_service` for cross-account operations.

### Counterparty replied with a NEW email, not a threaded reply (2026-08-13)

Law firms / advocates often reply from a DIFFERENT person's mailbox with a NEW subject and no In-Reply-To (observed 2026-08-12: original went to Sanjay Sethia sanjay@lawsquare.in; reply came from Nishanth Adv nishanth@lawsquare.in — same domain — with subject changed from "Priority: Succession Certificate ..." to "Succession Certificate (Dinesh Ranka)", In-Reply-To: None). When the user says "reply in the same email" after such a reply:

1. Find the LATEST counterparty message by **domain**, not just name: `q='lawsquare.in newer_than:7d'` across ALL accounts (google-draas, google-gmail, google-ahfl). The replier may be a colleague of the original addressee, so a name search for the original recipient misses it.
2. Check its `In-Reply-To` / `threadId`. If it's a fresh thread (In-Reply-To: None), the correct "same email" is the counterparty's NEW message — reply to THAT message (`draft_reply_create` with that message_id), not the original sent thread. This threads the reply from their side and keeps the rest of the firm on Cc.
3. Derive To/Cc from the new message: To = its `From`; Cc = its `To` (minus self) + its `Cc` — reproduces Gmail's reply-all for the actual message being answered. Verify the draft (drafts().get: Subject `Re: <their subject>`, In-Reply-To set, DRAFT label, present in drafts().list()).

### Email body claimed attachments ≠ actually attached (2026-08-13)

Before answering "was the petition/documents actually attached to our email?", do NOT trust the body's attachment list. Walk the real MIME parts:

```python
def walk(payload):
    if payload.get('filename'):
        print('ATTACH:', payload['filename'], payload.get('body', {}).get('size'))
    for p in payload.get('parts', []):
        walk(p)
```

Observed: sent email body listed 4 docs ("Draft petition, Death certificate, Family tree, Aadhaar cards") but only 3 were actually attached — the Aadhaar cards were listed yet never attached. When the counterparty says "documents were not attached", report the discrepancy precisely (which attachments exist, which claimed one is missing) so the reply states facts accurately (here: petition WAS attached; only Aadhaar cards missing — so the reply corrected them while confirming we'd send the missing set).

### Threaded reply — last message is from you

When replying in a thread where the **most recent message was sent by you** (the user), the `draft_reply_create` helper defaults its `To` to the `From` of the last message — which is the user themselves. This creates a self-reply draft.

**Fix:** Scan the thread to find the last message FROM the other participant (not the user), and set `To` explicitly:
```python
thread = service.users().threads().get(userId='me', id=THREAD_ID, format='metadata').execute()
reply_to = None
for msg in reversed(thread['messages']):
    h = {hdr['name'].lower(): hdr['value'] for hdr in msg['payload']['headers']}
    frm = h.get('from', '')
    if 'ndr@' not in frm and 'nishantranka' not in frm:
        reply_to = frm
        break
# Now use reply_to as the To address
```

### Reply-all — derive recipients from the LATEST message (2026-08-01)

For a "reply all in this thread" request, derive To/Cc from the **most recent message in the thread** (the one you're actually answering), not the thread's first message or the draft helper's default:

```python
latest = sorted(thread['messages'], key=lambda m: m.get('internalDate', 0))[-1]
h = {x['name'].lower(): x['value'] for x in latest['payload']['headers']}
me = 'ndr@draas.com'
def split(addrs): return [a.strip() for a in (addrs or '').split(',') if a.strip()]
# Standard Gmail reply-all: original SENDER goes to To; original To (minus me)
# + original Cc (minus me) go to Cc. Verified 2026-08-11 (Bajaj Life reply:
# To=Rohit.Sundarka@bajajlife.com, Cc=rnr@draas.com, echamundeshwari@draas.com).
to = [h['from']] if h.get('from') and me not in h['from'] else [a for a in split(h.get('to','')) if me not in a]
cc = [a for a in split(h.get('to','')) if me not in a] + [a for a in split(h.get('cc','')) if me not in a]
cc = [a for a in cc if a not in to]   # don't duplicate the sender between To and Cc
```

- The latest-message `To` field still contains the user's own address (they were a recipient) — **strip self** from To before drafting.
- The original sender goes to **To** (that's who you're answering); everyone else from the latest To/Cc (minus self) goes to **Cc** — this matches Gmail's reply-all.
- Preserve display-name form (`Name <email>`) — don't strip it; it keeps the draft readable in Gmail.
- Verify the final draft with `drafts().get()`: To/Cc should contain every intended participant exactly once, and no excluded party should appear.

### Reply-all — "everyone from all the email chains" (2026-08-12)

When the user says to include everyone who appeared across the different emails (e.g. "his PA was in earlier emails… make sure everyone who was there in the email chains across the different emails are all added"), deriving from the LATEST message alone is NOT enough — a PA/assistant may have been on older threads but dropped from the most recent message (real case: Millers Road — Atheeq padirector@ahindia.com was Akber's PA/accounts and had to be added even though the latest revert email listed only Akber + Aamir).

1. Search Gmail for ALL threads matching the person/subject keyword (e.g. `q='(from:akber OR to:akber) Millers'`), and collect every To/Cc across every message in every matching thread.
2. Dedupe by person; keep ONE address per person — prefer the address used in the MOST RECENT thread. People change addresses mid-deal (Aamir: aamirkhan@me.com in Jun–Jul → khan.hussain.aamir@gmail.com in Aug 2026). Do not CC both old and new.
3. To = the person the user names ("we send it to Akbar"); Cc = everyone else in the union (PA + Aamir).
4. Reply in the LATEST thread (where the counterparty most recently reverted), with proper In-Reply-To/References.
5. Contact rule still applies: every address used must be verifiable in the thread history / NDR's contacts — never invent one.

### Voice-transcription disambiguation before drafting (2026-08-17)

NDR dictates drafts by voice; the transcript garbles names and terms. Observed same-session examples:
- "Aamir" → meant BOTH the lessor **Akber Hussain** (akber@ahindia.com, To) AND advisor **Aamir Khan** (khan.hussain.aamir@gmail.com, Cc) — both were on the thread, and "reply all" resolved the ambiguity
- "online visa agreement" → lease agreement; "the laser" → the lessor; "ETO" → ETA; "FR" → FAR; "Ajayarchitect" → A.J. Architects / Arvind Jain; "7 above 14 bar 1" → Sy. No. 7/1 & 14/1
- **Money figures render from lakh/crore phrasing, not the digit garble (2026-08-20):** "one fifty from GB Jat" → ₹1.5 crore; "a thirty" → ₹30 lakh; "twenty five lakh rops" → ₹25,00,000. DRAAS/RSFC deals talk in lakhs/crores, so "one fifty"/"one point five" = ₹1.5 Cr and "a thirty" = ₹30 L. Cross-check against the actual transaction figures (refund amount on the thread) before locking them in.
- **Entities garble as phonetically-different words (2026-08-20):** "regsorformers collective" → **Red Soul Farmers Collective**; "DRA Realty Private Limited" (user dictation) vs the thread's "DRA Thindulu Land Partners" — when the user names an entity that partially matches the thread scope, flag the difference and offer to broaden (don't silently pick one).
- **"Bhavish Bhavna" → "Bhavesh Bafna" (2026-08-21):** Voice transcription can garble BOTH first and last names simultaneously. The contact sheet has Bhavesh Bafna (bvbafna@yahoo.co.in / bvbafna@gmail.com) — "Bhavish" is the garbled first name and "Bhavna" is the garbled last name. When both names come out wrong, search the contact sheet by first-name-only substrings ("bhav" → "Bhavesh"), cross-check with Gmail thread history, and surface the candidate to the user rather than guessing.
- **Recipient "Saurabh VK the CA" / "accounting group where Nitin is part"** resolve via contact sheet entries carrying job-tag suffixes (e.g. `Saurabh CA Ref VK`, `Nitin Osthwal Saurabh CA`) — these exact tags disambiguate the CA from the many other Saurabhs/Nitins. Pull the phone from the tagged entry, not a generic name match.

- **Legal/estate voice garble (2026-08-25):** "debt certificate" → death certificate; "sevdhanapalli" / "SEV Ganapalli" → **Sevaganapalli** (Ranka Oasis village, Hosur Taluk); "Tushas" / "Vishwas" → resolve via find_contact (Vishwas Rao, Vantage Point Advisors, vishwas@vantagepointadvisors.in); "Giraffe Capital" → Jiraaf Capital. When the user names a clause to remove from a deal doc ("profit of 15% to Nishant Prakash"), read the ACTUAL latest doc first — the clause text may differ from the dictation, and verifying the real content before editing is a hard user expectation on deal docs.
- **Email address merging from voice dictation (2026-08-27, Kanta Ranka TPA query reply):** When the user says something like "Mark Sarthak at admin3.blr@draas.com" during voice dictation, the transcript produces a single concatenated string: "Sarthakadmin3.blr@draas.com". This is NOT a valid email — the name ("Sarthak") merged with the email prefix ("admin3") because the speaker paused in the wrong place. Do NOT use the merged string. Resolve each recipient's actual email from:
   1. Gmail thread headers (the person was already on the CC of a prior message in the thread)
   2. The `contact_resolver` tool
   3. Prior drafts on the same thread
  In this case, `admin3.blr@draas.com` is the correct email for Sarthak Sharma — never construct a combined form.
- **Removing a money term from a deal doc — flag the economic side-effect (2026-08-25).** When the user says "remove the ₹2 Cr goodwill / the 15% profit clause" from a term sheet, the headline numbers move (net consideration ₹33.34 Cr → ₹35.34 Cr). State the new headline in your reply so the user can confirm before the doc goes out to a consultant — do not let a clause removal silently change the deal economics.

**Rules when drafting from a voice note:**
1. Resolve every person/entity name against the ACTUAL thread headers (From/To/Cc of the latest + earlier messages) before choosing recipients — never trust the transcript name alone.
2. When the spoken name could match two people (Akber vs Aamir Khan), prefer **reply-all to the thread** — it covers both interpretations.
3. Numbers/technical terms ("7/1 & 14/1", "1.75 FAR", "25% setback relaxation") — render from the deal context in the thread, not the garble.
4. Before finalizing, surface the uncertain items to the user: "Survey numbers: I rendered 7/1 and 14/1 — correct?" / "The ADTP name came through unclear — I wrote just ADTP." Do NOT silently guess.

### Updating an existing draft's body content

The Gmail API has no direct `draft.update()` endpoint for modifying body text. To update an existing draft, you must **delete and recreate**:

```python
from tools.gws_auth import build_service
import base64

service = build_service('gmail', 'v1', service_name='google-draas')

# Step 1: List drafts to find the correct draft resource ID (≠ message ID)
result = service.users().drafts().list(userId='me').execute()
target_draft = None
for d in result.get('drafts', []):
    msg = service.users().messages().get(userId='me', id=d['message']['id'],
                                          format='metadata',
                                          metadataHeaders=['Subject', 'To']).execute()
    h = {hdr['name']: hdr['value'] for hdr in msg['payload']['headers']}
    if 'target-subject' in h.get('Subject', '') and 'target@email' in h.get('To', ''):
        target_draft = d  # d['id'] is the draft resource ID, d['message']['id'] is the message ID
        break

# Step 2: Delete old draft using draft resource ID (NOT message ID)
service.users().drafts().delete(userId='me', id=target_draft['id']).execute()

# Step 3: Recreate with updated body
message = {
    'raw': base64.urlsafe_b64encode(
        f"Subject: Re: Original Subject\r\n"
        f"To: recipient@example.com\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: text/plain; charset=\"UTF-8\"\r\n"
        f"\r\n"
        f"{updated_body_text}".encode('utf-8')
    ).decode('utf-8')
}
created = service.users().drafts().create(userId='me', body={'message': message}).execute()
```

**Pitfall — draft resource ID vs message ID:** When listing drafts from `users().messages().list(q='in:drafts')`, the returned `id` is the **message ID**, not the draft resource ID. Using it in `drafts().delete()` returns `HttpError 404`. Always use `users().drafts().list()` to get the draft resource ID (`d['id']`). The message ID is at `d['message']['id']`.

**Pitfall — `draft_delete` in `gws_skill_bridge`:** The bridge exposes `draft_delete(draft_id=..., service_name=...)` — if using the bridge, pass the draft resource ID, not the message ID.

### Forwarding emails with recipient exclusions

When the user asks to forward an existing email to a subset of the original recipients (e.g. "forward to Aamir and CC Prasanna, but remove Sangam"):

1. **Fetch the original message** with `format='raw'` to get the full MIME content, thread ID, and Message-ID header.

2. **Build the new message** by writing a **fresh script to `/tmp/` and running via terminal** (do NOT use `execute_code` — the sandbox lacks `gws_fetch_token`):
   ```python
   import base64, email.mime.text
   from tools.gws_auth import build_service
   service = build_service('gmail', 'v1', service_name='google-draas')

   # Get original message
   orig = service.users().messages().get(userId='me', id=MESSAGE_ID, format='raw').execute()
   raw_bytes = base64.urlsafe_b64decode(orig['raw'])

   # Build new MIME message
   msg = email.mime.text.MIMEText(new_commentary + forwarded_original, 'plain', 'utf-8')
   msg['To'] = 'Aamir Khan <aamirkhan@icloud.com>'
   msg['Cc'] = 'Prasanna Swaminathan <prasannaswaminathan91@gmail.com>'
   msg['Subject'] = 'Re: ' + original_subject  # keep on same thread
   msg['In-Reply-To'] = original_message_id
   msg['References'] = original_message_id

   draft_body = {
       'message': {
           'raw': base64.urlsafe_b64encode(msg.as_bytes()).decode('ascii'),
           'threadId': original_thread_id
       }
   }
   service.users().drafts().create(userId='me', body=draft_body).execute()
   ```

3. **Key rules for forwarding:**
   - **Use the same thread ID** so Gmail nests it correctly (`threadId` in the draft body)
   - **Set `In-Reply-To` and `References`** to the original Message-ID — both are required for proper threading
   - **Exclude unwanted recipients** by simply not including them in the new message's `To`/`Cc` headers. The forwarded email text will reference their names (that's fine) — what matters is who receives the new message
   - **Write the new message content ABOVE** the forwarded original (not inline reply)
   - **Include the forwarded email as a "---------- Forwarded message ---------" block** in the body text

4. **Verify the draft** — call `service.users().drafts().get(id=draft_id)` and check:
   - `To` and `Cc` headers contain only the intended recipients
   - No excluded recipient email appears in `To` or `Cc`
   - `threadId` matches the original thread
   - `In-Reply-To` is set

5. **Pitfall — forward vs reply semantics:** A forward is NOT a reply-all with recipients removed. The user wants a NEW message on the same thread that introduces the original email to a new audience, with their own commentary. The forwarded content is context, not the primary message body.

### Forwarding an OWN sent email as FYI (new audience, no send to originals)

When the user says "forward the email I sent to X to Y & Z, FYI" — the source is the user's OWN sent message, and the point is to give Y/Z visibility into that decision/transaction, NOT to elicit a reply. Steps (validated 2026-08-20, Red Soul Farmers Collective refund):
1. Locate the original by subject (`q='subject:"..."'`) — report its To/Cc separately from each forwarded copy; users often forward the same mail to multiple people one-by-one, so each forward is its own message with its own Cc.
2. Fetch the original with `format='raw'`, extract its Message-ID + subject.
3. Build a fresh `EmailMessage`: From = ndr@draas.com, To = the FYI audience, Subject = `Fwd: <orig subject>`, In-Reply-To + References = the original's Message-ID. Body = short "FYI — please find below the email I sent regarding …" note, then the full "---------- Forwarded message ---------" block (From/Date/Subject/To/Cc + body).
4. Create as DRAFT only (always), verify recipients + body, then tell the user it's ready in Drafts. Never auto-send.
Tip: users often ask "who was marked on that email?" first, then "forward it to Y & Z FYI" — run the recipient trace before drafting so you can confirm exactly who the FYI gain should copy and that you're forwarding the RIGHT one (original vs a forward).

### Find email with attachment → download → forward to new recipient (2026-08-21)

When the user says "find the latest email from [person] about [topic] — there's a PDF/presentation attached — send it to [someone else]":

1. **Locate the sender by email domain/address** — search with `q='from:arch_arvind2000@yahoo.co.in'` or the sender's domain. If the user says "AJ Architect" or a short name, resolve it via entity_resolver/contact_resolver first (e.g. "AJ Architect" → A.J. Architects / Arvind Jain, arch_arvind2000@yahoo.co.in).
2. **Identify the right thread by topic keywords** — scan subject lines for the topic the user named (e.g. "farm home design" → "Proposed farmhouse presentation"). There may be multiple threads from the same sender; pick the LATEST one that matches the topic.
3. **Check for attachments** — fetch the thread with `format='full'` and walk `payload.parts[].filename` for each message. The attachment may be on a forwarded/resent version (e.g. your Fwd: of their original), not the original sender's message. Check the latest message in the thread first.
4. **Download the attachment** — use `messages().attachments().get(attachmentId=..., messageId=...)`. Verify with a magic-bytes check: `data[:4] == b'%PDF'` (or the appropriate MIME header for the file type).
5. **Forward to new recipient** — either:
   - **Create a fresh email draft** with the PDF as a MIME attachment (via raw Gmail API with `MIMEMultipart("mixed")`), body describing the attachment and asking for feedback. The user's spoken message becomes the email body.
   - **Forward the original email thread** (see "Forwarding emails with recipient exclusions" above) if the user wants the full context.
6. **Key difference from the FYI-forward pattern**: the source is a THIRD-PARTY email (not the user's own sent message), and the user wants to share it with a new audience for feedback/review — not as a FYI broadcast. The body should introduce the scheme/design and ask for their opinion.

### SharePoint/OneDrive link extraction from Gmail

When the user needs a sharing link from a vendor's email (e.g. SharePoint invite from Godrej, Microsoft 365 file share), the link lives in the HTML body, NOT the plain-text part. Navigate the MIME `multipart/alternative` structure, decode the `text/html` part, and regex for `sharepoint.com` hrefs. Full recipe in `references/gmail-sharepoint-link-extraction.md`.

### Read-only email forensics: "who was marked / does it have the attachment?"

Recurring for transaction/refund emails (investor transfers, reimbursements). Two read-only checks via `build_service('gmail','v1',service_name='google-draas')`:
- **Recipient trace**: search by subject, then for EACH message in the result print `From`/`To`/`Cc`/`Date` separately (`format='metadata'`, metadataHeaders=['From','To','Cc','Subject','Date']). Originals and forwards are separate messages — report each. A forward sent to just one person has `Cc: None` even if the original had a Cc list.
- **Attachment presence/type**: walk `payload.parts[].filename` + `.mimeType` + body `.size` to confirm an email has (e.g.) an `.xlsx` with investor details. Do NOT trust the body prose ("please find attached…") — enumerate the real parts. Fetch with `format='full'` (not 'metadata' — metadata drops parts).
The email body usually states what the attachment contains ("amount to be returned to each investor + account number, IFSC, branch") — quote that alongside the filename so the user knows it matches their need before you download/parse it.

**Pitfall — `drafts().get(format='full')` returns NO `raw` key (2026-08-20)**

After creating a draft, `service.users().drafts().get(userId='me', id=..., format='full').execute()` gives you `message.payload` but does NOT include `message['raw']` — trying `base64.urlsafe_b64decode(msg['raw'])` raises `KeyError: 'raw'`. To verify the draft BODY text, read it from the payload with the recursive text walker (the same `extract_text(payload)` you use for messages). Headers are verifiable from `payload.headers`; only the body needs the walker. (If you must decode raw MIME, pass `format='raw'` explicitly to `drafts().get()`.)

**Pitfall — `drafts().create()` may assign the WRONG threadId even with correct In-Reply-To/References (2026-08-20).** When building a threaded reply-all draft (ITR follow-up), I set `In-Reply-To` + `References` to the source message's Message-ID correctly, but Gmail auto-assigned `threadId: 1a01de64f31d5b61` while the source thread was `1a0193d4df586045` — a mismatch that would have sent the reply as a disconnected new thread. Fix: pass the source thread's `threadId` EXPLICITLY in the draft body and verify it on the returned resource:

```python
draft = service.users().drafts().create(userId='me', body={
    'message': {'raw': raw, 'threadId': source_thread_id}
}).execute()
assert draft['message']['threadId'] == source_thread_id
```

Verify after creation with `drafts().get(id=...)` — the returned `message.threadId` must equal the source thread, not a fresh id. If you already created (and confirmed mismatched) a draft, delete it (`drafts().delete`) and recreate with the explicit `threadId`. This is NOT the same as the SENT-label problem above (that's a malformed-References issue); this is purely the thread-join determination.

**Pitfall — user says "the draft isn't part of the thread, make it reply-all in the same thread" (confirmed 2026-08-27, Ranka Aqua Green NCDRC):** A draft created from scratch (plain `draft_create` / `drafts().create()` with no threadId) with subject `Re: <original>` does NOT join the original conversation — Gmail shows it in Drafts as its own separate thread, even though the subject looks like a reply. The user noticed this and asked to keep it in the same thread. Fix (delete + recreate as a THREADED reply):
1. `drafts().delete(userId='me', id=<draft resource id>)` — draft resource id from `drafts().list()`, NOT the message id.
2. Find the LATEST counterparty (non-self) message in the target thread: `threads().get(threadId=..., format='metadata')`, walk `t['messages'][-1]`, check the From header isn't ndr@/nishantranka. Take that message's id.
3. Fetch `messages().get(userId='me', id=<that id>, format='metadata', metadataHeaders=['Message-ID','References'])`; set `In-Reply-To` = its Message-ID, `References` = existing References + Message-ID (dedupe).
4. `drafts().create(userId='me', body={'message': {'raw': raw, 'threadId': <source thread id>}})` — **explicit threadId is mandatory** (without it Gmail may spawn a new thread).
5. Verify: returned `draft['message']['threadId'] == <source thread id>` AND the draft shows under the original thread in Gmail UI. Report the drafts-inbox link. This is the same pattern as "Pitfall — drafts().create() may assign the WRONG threadId", but triggered by the user-visible symptom "this draft is separate from the thread — reply-all it".

### Legal / advocate consultation emails — "in between" structure (NDR preference, validated 2026-08-27)

When NDR asks to email his counsel / advocate about a live matter (call request, strategy discussion, case status), his preferred structure sits between the two failure modes:
- ❌ **Too basic** — "I've reviewed the IA, let's have a call, tell me a time." Reads dismissive; gives the counsel nothing to prepare on.
- ❌ **Too detailed** — a multi-part questionnaire with 10+ legal sub-questions and cited case law in every line. Reads like homework; NDR himself called the earlier 5-part version too much and asked for a replacement.

✅ **The "in between" structure that landed (Ranka Aqua Green IA 9783/2026 call request to Harshavardhan Kotla):**
1. **Open** — one line: reviewed the filing (name the document) + the latest hearing update, want a call to discuss strategy.
2. **"Our analysis of the current position"** — 2–3 short paragraphs: what the Bench observed (quote the operative direction + next date), what the opposing side's new filing appears to be attempting (1–2 sentences), and any estoppel/annexure claims they raised. Plain account of the state of play — this is what tells the counsel you've done your homework.
3. **"Our rebuttal stance / key legal points"** — 3–5 labelled bullets, each one argument with the supporting authority inline (e.g. `a) Section 12(1)(b) — maintainability; Brigade Enterprises v. Anil Kumar Virmani (2021)`). One line per argument; no mini-essays. Correct the user's own stated timeline if wrong (user said "filed 10 years after handover" — the 10 years was case PENDENCY 2016–2026, the OC-to-complaint gap was ~2 years; state the corrected figure in the email so the counsel works from accurate facts).
4. **"Key information we need from you on the call"** — 5–6 numbered concrete questions, each one sentence: strength of our primary argument at the next date, how to counter their estoppel argument, whether res judicata from individual cases is pleadable, probability/advisory opinion, settlement consideration given pendency, strategic-delay advice while the opposing side decides whether individuals step forward.
5. **Close** — document filed on Drive for reference (one line), ask for a convenient time this week. No boilerplate pleasantries beyond the initial "I hope this email finds you well."

Recipients: derive To/Cc from the latest thread message (reply-all; NDR may have added family members — e.g. Manish/MDR, Dharmesh — into the Cc; preserve whatever recipients are already on the draft/thread).

## 5. Rules

- Use `tools.gws_auth.build_service("gmail", "v1", service_name=...)` directly (see Pitfalls for account resolution)
- Build a `MIMEMultipart("mixed")` message with MIMEText (body) + MIMEBase (attachments)
- Call `service.users().drafts().create()` with the full MIME message
- **Template:** `templates/draft-with-attachments.py` in this skill — copy and configure
**Full workflow reference:** `references/drive-to-draft-pipeline.md` — covers the entire search → download → organize → build MIME → create draft pipeline, including deduplication and completeness checking.

**Statutory/corporate form filling (MGT-11 proxy, consent forms, "fill the proxy form", "prepare a form for signature"):** `references/statutory-form-pdf-pipeline.md` — download the template from Gmail, read legacy .doc via `strings` (no LibreOffice on VPS), extract member/shareholder data from the notice PDF, rebuild the filled form as a typed PDF with reportlab, attach to a forward draft via raw Gmail API. Validated 2026-08-13 (DRA Aadithya AGM proxy for Roshni).

**Architect/consultant fee proposal comparison (2026-08-21):** `references/fee-proposal-comparison.md` — workflow for comparing a new/revised fee proposal against the original work order. Covers: finding the latest email, extracting the signed WO PDF from email attachments, comparing rates AND basis (SBUA vs Built-Up Area), identifying double-dipping, assessing justification given actual scope change, and recommending a negotiation position. Validated 2026-08-21 (Ranka North Star — Arvind Jain additional fees).
- **Google Doc text cleanup (force all text black) before attaching:** `references/google-doc-text-cleanup.md` — Docs API pitfalls: `rgbColor {}` = black not white (default-channel check), `suggestionsViewMode` allowed values, batchUpdate to black, PDF-render verification, confirming the right doc via `lastModifyingUser`

**Threaded reply-all via raw Gmail API** — When the bridge or `google_workspace_manager` tool can't deliver a properly threaded reply-all draft, use the raw API. Full recipe in `references/threaded-reply-raw-api.md`. Key steps: get the most recent message in the thread via `format="raw"`, extract `Message-ID` + `References` headers, build an `EmailMessage` with `In-Reply-To` and `References` set correctly (both required for Gmail nesting), then create the draft via `service.users().drafts().create()`. Always clean header values with `re.sub(r'\s+', ' ', val).strip()` to remove newlines before passing to `EmailMessage.__setitem__`.

**Pitfall — `threads().get()` does NOT accept `format='raw'` (confirmed 2026-08-02):** `service.users().threads().get(userId='me', id=THREAD_ID, format='raw')` raises `TypeError: Parameter "format" value "raw" is not an allowed value in "['full', 'metadata', 'minimal']"`. To read the latest message's raw MIME for Message-ID/References: fetch the thread with `format='metadata'`, take `t['messages'][-1]['id']`, then `messages().get(userId='me', id=that_id, format='raw')` — the raw fetch must go through the **messages** endpoint, not the thread endpoint. Only after this can you build In-Reply-To/References and call `drafts().create()` with `threadId`.

**Pitfall — `drafts().create()` with malformed References can produce SENT label instead of DRAFT (confirmed 2026-07-30):**
When creating a threaded reply draft via the raw Gmail API (`service.users().drafts().create()`), the message can end up with label `['SENT']` instead of `['DRAFT']` if the `References` header contains non-Message-ID content. This happens when extracting References from raw email with an overly broad regex that captures DKIM signature content. The API interprets the malformed header as a send instruction.

Fix: always sanitize References to contain only Message-IDs wrapped in angle brackets, then verify the draft has `DRAFT` label:
```python
import re
clean_refs = ' '.join(re.findall(r'<[^>]+>', existing_refs)) if existing_refs else ''
```
Verify immediately: `verify['message'].get('labelIds', [])` must contain `'DRAFT'`. If SENT, delete and recreate with clean References.

**Extended finding (2026-08-10): even a clean, immediately-verified draft can end up SENT.** Two drafts created this way (MOU reply + insurance reply) each showed `labels: ['DRAFT']` right after creation — sanitized References, verified via `drafts().get()` — yet when the user later said "I can't see the draft", `drafts().list()` returned neither of them and a subject search found both in **SENT** with real Message-IDs and In-Reply-To headers. Causes: (a) the user sent them from the Gmail UI before checking, or (b) delayed auto-send behaviour. Either way the lesson is the same:

**The authoritative "is it still a draft" check is `users().drafts().list()` — NOT the label on a draft resource fetched by ID.** A `drafts().get(id=...)` can return `labelIds: ['DRAFT']` at creation and that same resource can later read back as SENT.

**Diagnostic when user reports a missing draft:**
1. `users().drafts().list(userId='me')` — if the draft isn't there, it is NOT in Drafts, full stop.
2. Search the whole account by subject (`q='subject:"<keyword>"'`) and inspect `labelIds`. If the message is `['SENT']`, the email went out — tell the user it was sent (give time, To, Cc) and do NOT recreate a fresh draft (that creates a duplicate the user then sends twice).
3. Report plainly: "It's not in Drafts — it's in Sent (sent at HH:MM)." This matches the user's own recollection in most cases ("I might hv sent it").

**Pitfall — `html=True` is required for HTML drafts (user correction 2026-07-13):**
The `gws_skill_bridge.draft_create` operation defaults to `MIMEText(body, "plain")` if you don't pass `html=True`. The result: the recipient sees your entire HTML document (`<!DOCTYPE html>`, `<table>`, `<tr>`, `<td>`) as raw literal text in the email body. The user said: "you have taken HTML code and stuck it into the email body rather than creating the email body itself as an HTML using HTML so it looks like a nice rendered email." Fix: pass `html=True` to the bridge call, OR if using `google_workspace_manager`, use the `--bodyHtml` flag (not `--body`) for HTML content. Always verify a draft by calling `draft_get` and inspecting the MIME structure (`payload.mimeType` should be `text/html`) before declaring it done.

Present the draft for confirmation before sending:
> **Subject:** `Ranka Oasis: Site Visit — Confirming Date and Access`
>
> Please confirm your availability for a site visit this week.
>
> 1. Confirm date — by Wednesday 5pm
> 2. Arrange access to the south plot
>
> Ready to send?

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

### Who am I? — verify the mailbox before ANY draft (confirmed 2026-08-17)

Terminal subprocesses in this deployment can inherit a wrong `HERMES_SESSION_USER_ID` (observed `8502281203`), making `build_service('gmail','v1',service_name='google-draas')` resolve to **psingh@draas.com** instead of ndr@draas.com. A draft created under that state lands in Prakash's mailbox — a data-isolation breach that looks like success. ALWAYS run a whoami check before touching Gmail/Drive via terminal:

```python
svc = build_service('gmail', 'v1', service_name='google-draas')
who = svc.users().getProfile(userId='me').execute()['emailAddress']
assert who == 'ndr@draas.com', f'WRONG MAILBOX: {who}'
# fix if it fails: prefix the shell command with  HERMES_SESSION_USER_ID=7449813913
```
Gateway tools (`gws_resolve_account`, `execute_code` sandbox, `gws_fetch_token`) use the correct session identity — only raw terminal python can flip. Also verify drafts after creation with `drafts().get()`: From must be Nishant Ranka <ndr@draas.com>.

**Pitfall — Gmail attachment download base64 padding:** `messages().attachments().get()` returns the attachment data as a base64url-encoded string whose length may not be a multiple of 4 (e.g. `len(data) % 4 == 1`). `base64.urlsafe_b64decode(data)` raises `binascii.Error: Incorrect padding` in this case. Fix with explicit padding before decode:
```python
padding = 4 - (len(data) % 4)
if padding != 4:
    data = data + '=' * padding
file_data = base64.urlsafe_b64decode(data)
```
Always add this guard when downloading attachments from Gmail — it accounts for the trailing-padding variation in Gmail's base64 output.

`messages().attachments().get()` base64 payloads can arrive truncated (observed on a 24 KB docx: header bytes OK, central directory missing → `BadZipFile`; base64 length mod 4 == 1 → decode error). Do NOT retry more than twice — the same file almost always exists in Drive (it was attached to an email that also got saved/exported there). Fetch the Drive copy instead:

```python
raw = drive.files().export(fileId=DOC_ID, mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document').execute()
# for native binary files: drive.files().get_media(fileId=...).execute()
```
Live lesson: Millers Road v6 lease attachment was corrupt via Gmail; the v5 base + edited copy exported cleanly from Drive (Drive's `files().export` / `get_media` don't go through the JSON gateway that truncated the attachment response). Validate any downloaded .docx/.zip by checking the PK header AND opening with zipfile before building a draft attachment.

### HTML email formatting — when to use (user preference, 2026-08-21)

When the email carries more than 3 Drive links, multiple sections (approvals, NOCs, drawings, queries), or is an instruction brief to a colleague — ALWAYS use HTML with inline CSS so hyperlinks render clickable. Plain text with bare URLs forces the recipient to copy-paste each link manually, which the user explicitly flagged as broken.

**Pattern that worked for the Ranka North Star approval-queries email:**
- Use a `<table>` for the summary header (project name, LP number, total land, area under sanction, key contacts)
- Use a coloured `<div>` per query (different background colour per numbered question) to visually separate the 5 items
- Every document reference is a clickable `<a href="...">` link — never a bare URL in parentheses
- Inline CSS only (no `<style>` block — many email clients strip it): `style="color:#...;background:#...;padding:...;margin:..."`
- End with a reference-document link and a "Documents referenced in this email:" section listing everything in one place
- The `gws_skill_bridge.call("draft_create", ..., html=True)` flag MUST be set; without it the HTML source is rendered as literal text
- Verify the draft after creation: `drafts().get()` → `payload.mimeType` should be `text/html`, and the body should render links not literal `<a>` tags

**Fee-revision / negotiation confirmation emails — HTML with color-coded highlighted figures (NDR preference, validated 2026-08-25):** After an in-person fee discussion, NDR wants the follow-up email as a structured HTML draft with each agreed term in its own color-coded box and every key number visually highlighted. Working pattern from the Arvind A.J. Architects fee revision (Ranka North Star):
- One `<div>` per agreed item, each with a distinct left-border + light background color family: rework scope (blue), enhanced base fee math (green), fixed-price scope add-on (red), payment adjustment (amber/yellow), unchanged terms (grey).
- Highlight the key rupee figures with `<span style="background:#fff3cd; font-weight:bold; padding:1px 5px;">` — and strike the superseded original rate (`text-decoration: line-through`).
- Reconstruct the arithmetic explicitly so the vendor can verify: "38 + 5 + 4 = ₹47" with each addend explained (e.g. MEP+structural ₹13/sqft BUA × 1.2 = ₹15.6 − ₹11 already factored ≈ ₹4.6 → rounded ₹5).
- **Payment-adjustment clause — always include when past payments exist:** "All payments made to date will be adjusted while computing the new payable; fees recomputed at the new rate, all earlier payments deducted and adjusted accordingly — only the balance will be payable." NDR explicitly required this highlighted in its own section.
- Plain-text multipart alternative required (same content, no markup); `email.message.EmailMessage` + `set_content` + `add_alternative(html, subtype='html')` produces the multipart/alternative that Gmail drafts need.
- Create as threaded reply against the vendor's ORIGINAL proposal Message-ID (In-Reply-To + References + explicit `threadId`), delete any earlier plain-text draft on the same thread so there is exactly one draft.
- Same agreement goes into the record: post the identical terms as a Kelsa note on the PO-WO lead (pipeline 537) so the PO record and the email match. See `references/fee-proposal-comparison.md` for the negotiation groundwork; the confirmation-email pattern above is the follow-up half of the same workflow.

### Advisor / consultant mandate emails — attach PDF, HTML, highlighted ask (NDR, 2026-08-25, Vishwas Rao/Jiraaf case)

When emailing a briefing to a structuring/tax consultant or advisor with a term sheet / engagement scope:
1. **Attach the exported PDF — do NOT give a Drive link.** NDR explicitly: "download and attach the term sheet for now instead of giving him a link." Export the Google Doc → PDF via Drive `files().export()` and attach as MIMEBase.
2. **Open with the user's exact briefing line** (e.g. "As I had discussed with you some time ago, I am in discussion with closing a commercial arrangement with Jiraaf Capital… I am sharing with you the term sheet that we have signed"). Use his framing, not generic boilerplate.
3. **HTML body with color-coded sections** — one colored `<div>` per scope area (land/structure, key commercial terms, structuring considerations, regulatory/RERA, GST-opinion) and a **final highlighted callout box** (yellow bg `#fff8e1`, bold `<span style="background:#fff3cd">`) carrying the specific ask: review in the next couple of hours → call with the counterparty team today → drive to conclusion → total timeline → priority/fees separate. NDR: "make sure all those points are specifically neatly highlighted… redo the entire email using HTML so that everything is properly highlighted and properly captured and it's easy to read."
4. **If the user says they've made an edit to the doc since last export, re-fetch the doc and adopt the live edit** into the email text and the attached PDF (user edited v1.1's uplift % to 20% in-place; the attachment must carry it).
5. Rebuild flow: `drafts().delete(draft_id)` with the draft resource ID (not message ID), then `drafts().create()` — never leave the superseded draft behind.

### Architect / consultant briefs with an R&D reference collection — share-then-link, don't attach (2026-08-25, Palya row villas → Arvind Jain)

When the brief references a COLLECTION of competitor/R&D material (RERA summaries, sanction plans, brochures, layout plans — dozens of PDFs), attaching everything blows the 25 MB cap and buries the ask. Pattern that worked:

1. **Grant Drive access BEFORE creating the draft** — `drive.permissions().create(fileId=..., body={'type':'user','role':'writer','emailAddress':...})` to the external partner AND the internal coordinator who gets Cc'd. Verify each call returns `role: writer`. Only share the specific subfolders/sheets the brief references — avoid sharing catch-all parent folders that contain unrelated files (the Palya R&D lived in a mixed Aug-2026 folder; the row-villa subfolder alone was shared).
2. **Write the email as color-coded HTML sections** (project brief / concept anchor / design targets / reference materials / landscape / what-we-need) with the FAR, rate and sq-ft figures highlighted (`<span style="background:#fff3cd;font-weight:bold">`), and every Drive folder/sheet as a clickable link — never bare URLs.
3. **Attach only single decisive documents if any**; the folder links carry the collection.
4. **Flag drift between the brief and existing internal models** in your reply to the user (e.g. Palya IRR model still assumed FAR 1.05 @ ₹12k/sf while the brief asked for 1.8 @ ₹15k/sf) — do not silently align the email to the stale model, and warn that the model needs a refresh.

**User refinement on review — second round (2026-08-25, same Palya brief):** When NDR reviewed the draft he narrowed it down sharply. Encode these in any follow-up/revised brief:
- **One attachment only** — the decisive comparison sheet, exported to xlsx via Drive `files().export()` and attached as MIMEBase. Drop auxiliary summary-sheet LINKS from the body (he removed the RERA summary sheet link entirely); keep the collection folder + working folder as links so the architect's team has the full reference.
- **Embed the comparison as a TABLE in the email body** — columns: Project | Subtype | Achieved FAR | link to the specific plan showing that FAR. The sheet alone is not enough; the data must be visible in the email itself.
- **Quote the FAR measured off the sanctioned plan's title block**, not the RERA registered number — they differ (Sattva La Vita STP layout plan = **1.27** vs RERA 1.35; The Roots Development Plan = **1.93** vs RERA 2.0). For The Roots the FAR lives on the DEVELOPMENT PLAN, not the STP plan — check which plan in the folder actually carries the FAR before linking it.
- **Design-consequence callouts belong in the email as highlighted question boxes** — e.g. The Roots reaches 1.93 with basement + G + 1 + 2 + partly covered terrace ≈ G+3 ⇒ a lift/elevator becomes mandatory; without one G+2 + terrace is difficult. Frame as "we want your professional view on storey count vs FAR" rather than asserting the answer.
- **Long HTML bodies: write the body in part files** (`/tmp/email_part1.html` … part3) via separate write_file calls, then concatenate inside the build script — one giant write_file times out the stream. Verify final draft has exactly one html part + the attachment part list.

### WhatsApp vs Email dual-channel pattern (user-defined 2026-08-21):
When sending project instructions to an employee (Vinod, Prakash, etc.) about approval queries:
1. **WhatsApp** = short, high-level, ask-only. State the 3-5 questions in brief numbered form. Tell them a detailed email is incoming with full references. Use `personal-messaging` / `whatsapp_link` tool.
2. **Email** = full detailed brief, with every fact, figure, approval reference, link to all documents (Drive folders/files), and document access instructions. Use HTML with all hyperlinks rendered. CC relevant colleagues.
The WhatsApp primes the recipient. The email is their working document. Do NOT try to merge the two into one channel.

**Sub-case — stale-thread follow-up (email draft + WhatsApp ping, validated 2026-08-28, 18 & Oak DTCP):** When following up on an email that received no reply for 2+ weeks, the dual-channel split is different:
1. **Email** = reply-all draft on the original thread, with numbered questions asking for a status update (who spoken to, contact details, why each resource can help, current progress).
2. **WhatsApp** = short notification ping: "I've sent a follow-up email on the same thread — please check." Not a separate brief.
Full reference: `references/stale-thread-follow-up-whatsapp-ping.md`

**Variant — same content, different audience split (2026-08-27, Ranka Oasis collaterals):**
When requesting project assets (renders, walkthroughs, master plans) from an architect/designer AND the same information needs to reach colleagues who are CC'd on email but don't need a WhatsApp blast:

1. **WhatsApp to individual contributors** — send the identical brief to each person separately (Sinchana gets her own link, Bharat gets his own link). Keep the content the same: what's needed + urgency framing + who's marked.
2. **Email to the primary contact** — same content as WhatsApp, sent to the person who will do the work, with CCs to the stakeholders. The email is the working document; WhatsApp is the immediate ping.
3. **Do NOT send WhatsApp to people who are only CC'd on email** — they only need the email for visibility.
4. **Key distinction in the request: "basis renders vs marketing renders"** — when asking for architectural renders/collaterals, the user explicitly distinguishes between:
   - **Basis renders** (what you want): the actual architectural output from SketchUp/V-Ray with all materials matching the architect's plan — used for costing and engineering coordination
   - **Marketing renders** (not what you want here): the polished brochure-ready content already developed separately
   Always clarify which one is being requested; mixing them up leads to wrong deliverables.

## 5. Rules

- ALWAYS call `google_workspace_manager` as a Hermes tool, never as a shell command
- ALWAYS include `--threadId` for replies
- NEVER add boilerplate greetings unless asked
- ALWAYS confirm contact/thread before drafting
- NEVER guess email addresses — ALWAYS run the contact lookup tool first (`find_contact.py` from `personal-messaging`, HARD RULE 2026-07-31) for any phone/email lookup
- NEVER send without showing draft and getting confirmation
- For vendor-feedback escalation emails: see `messaging-drafts` skill → `references/vendor-feedback-escalation.md` for the full dual-channel workflow (Google Doc → email draft with attachments → WhatsApp group follow-up). The tone guidance in Stage 2 — Draft (Vendor-feedback / frank escalation tone) applies to the email body.
