---
name: messaging-links
description: |
  Generate WhatsApp deep links (api.whatsapp.com/send — never wa.me) and similar pre-filled messaging links.

  ## Formatting — Nishant's preference

  When generating a WhatsApp message for Nishant use bullet points (•) for lists, break into short sections, put each thought on its own line, address people by name, use bold for key items, and end with a clear call-to-action. Never one wall-of-text paragraph.
  (sms:, mailto:) for NDR. WhatsApp is the dominant channel for Indian real-estate
  follow-ups, and WhatsApp deep links are how Hermes "sends" WhatsApp messages — Hermes
  cannot programmatically post to WhatsApp, so it produces a link the user taps
  to open WhatsApp with the message pre-filled. Covers individual contacts and
  group messages (no phone, just text). Trigger: "WhatsApp [name]", "message
  [name] on WhatsApp", "WhatsApp the group", "draft a WhatsApp message",
  "open a chat for [name]". Also covers sms: and mailto: fallbacks.
metadata:
  hermes:
    tags: [messaging, whatsapp, wa-me, communication, outreach, follow-up]
category: communication
version: 1.0.0
author: ndr@draas.com
---

# Messaging Links (WhatsApp / SMS / mailto)

## CRITICAL: How to call the tool

There is no manual `wa.me` URL construction. There is one and only one sanctioned
way to produce a WhatsApp link, and that is the `whatsapp_link` Hermes tool. The
tool has **no safe ampersand handling** — it converts raw `&` characters in the
source text to a **fullwidth ampersand** (U+FF06, URL-encoded as `%EF%BC%86`).
This produces `R＆D` instead of `R&D` in the WhatsApp compose box, which reads
as a broken character on some mobile WhatsApp clients. **The rule is absolute:
rewrite EVERY `&` to "and", "plus", "and/or", or an em-dash in the source text
BEFORE passing it to the tool.** Do not assume the tool's handling is safe — it
is not in this case. Treat the fullwidth conversion as data corruption that you
must prevent at the source level.

ALWAYS call `whatsapp_link` — never hand-construct wa.me URLs in
`execute_code`/`urllib.parse`/string concatenation. Manual encoding has been
observed to break on mobile WhatsApp clients.

### Terminal fallback when tool isn't registered

The `whatsapp_link` tool belongs to the **messaging** toolset, which may not be
loaded in every session (especially Telegram gateway sessions where the toolset
is restricted). If the tool isn't in your available tools list, do NOT
hand-encode the URL. Instead, call the tool function directly via the Hermes
venv:

```python
# From terminal() or execute_code:
result = terminal(""cd /opt/hermes && .venv/bin/python3 -c '
import sys, json
sys.path.insert(0, \".\")
from tools.whatsapp_link_tool import whatsapp_link_tool

args = {
    \"phone\": \"+919999673483\",
    \"text\": \"Your message here — no raw & allowed\",
    \"platform\": \"telegram\"
}
result = json.loads(whatsapp_link_tool(args))
print(\"URL:\", result[\"url\"])
print(\"Display:\", result.get(\"display_link\", \"\"))
'"", timeout=15)
```

The handler takes an `args` dict (phone, text, platform) and returns a JSON
string with `url` and optionally `display_link` (for Telegram). This is the
**only** acceptable fallback — it uses the same encoding logic as the
registered tool, so the ampersand workaround and all other encoding rules are
preserved. Never bypass to urllib.parse or string concat.

## 1. Trigger Conditions

Activate when the user says anything like:
- "WhatsApp Sunny Sadhwani — [content]"
- "Send a message to [name] on WhatsApp"
- "WhatsApp the group with [names]"
- "Draft a WhatsApp message for [recipient(s)] about [topic]"
- "Open a chat for [name] with this message"
- "SMS [name] [content]" (use sms: fallback)
- "Send a text to [number] saying [content]"

## 2. Stage 1 — Resolve the recipient

### For an individual contact

Use Google Contacts lookup — but search **ALL three vault accounts**, not just
google-draas. Government / phone-added / spouse contacts can live in
`google-ahfl` (confirmed 2026-08-14: **Nagarajappa JDTP North exists ONLY in
google-ahfl**, and Lokesh Gandhi / Nachiketh Gowda in google-draas). The People API path is
`people.people().searchContacts(query=..., readMask=...)` — never a flat
`connections().list()` (see MEMORY).

```python
from tools.gws_auth import build_service
service = build_service('people', 'v1', service_name='google-draas')
results = service.people().searchContacts(
    query='Sadhwani',
    readMask='names,emailAddresses,phoneNumbers,organizations,biographies,nicknames'
).execute()
```

When a name has aliases (e.g. "Sunny Sadhwani, also known as Rajesh Sadhwani"),
the search returns one contact with both names — treat them as the same person,
do not ask the user to disambiguate. Present the canonical display name + the
email + the E.164 phone.

### Fallback: Contact not in Google Contacts — check the NDR DRAAS Contact Sheet

For NDR, the **NDR DRAAS Contact Sheet** (Google Sheets ID `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`)
often has phone numbers & labels that aren't returned by the People API
search (contacts may be in the sheet but not synced to Google Contacts, or
stored with different spellings). If `searchContacts` returns zero results,
**always query this sheet before falling through to Gmail extraction**.

**Important: contact found in sheet but no phone number.** The sheet may
contain a row for the person with only name + email and no phone columns
filled. In that case, do NOT fall through to Gmail extraction yet — first
check honcho memory for a phone number (see below). If honcho also has no
phone, inform the user the contact exists in the sheet (name + email) but
you need their phone number to generate the WhatsApp link. Show the draft
message text so they can copy-paste it, or send it once they provide the
number.

Sheet structure (header row 1):
- Col A: First Name, Col B: Middle Name, Col C: Last Name
- Col Q (index 16): Labels (e.g. "FrndA ::: * myContacts")
- Col AC (index 28): Phone 1 - Value (the phone number)
- Col AB (index 27): Phone 1 - Label (e.g. "Mobile")
- Email columns start at Col R (index 17)

NDR contacts are stored in both Google Contacts and this sheet (always in
tandem). The sheet was the primary storage before Google Contacts sync was
added, so it often holds contacts that predate the sync or were entered
manually by NDR's team.

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4', service_name='google-draas')
# Use a broad search: scan all rows checking First/Last name match
all_data = sheets.spreadsheets().values().get(
    spreadsheetId='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
    range='A:DA'
).execute()
rows = all_data.get('values', [])
headers = rows[0] if rows else []
for i, row in enumerate(rows[1:], 2):
    first = (row[0] if len(row) > 0 else '').lower().strip()
    last = (row[2] if len(row) > 2 else '').lower().strip()
    if search_term.lower() in first or search_term.lower() in last:
        phone_idx = 28  # Phone 1 - Value column
        label_idx = 16  # Labels column
        phone = row[phone_idx] if len(row) > phone_idx else ''
        labels = row[label_idx] if len(row) > label_idx else ''
        print(f'Sheet row {i}: {row[0]} {row[2] or ""} | Phone: {phone} | Labels: {labels}')
```

**Important**: The sheet is 4000+ rows and the full read is ~2 seconds.
Read the whole column range once and iterate in Python — do NOT make
multiple paginated calls. The range `A:DA` covers all known columns.

**Pitfall**: A name can appear in Google Contacts but not in the sheet,
or vice versa. Always check BOTH sources. When the sheet has the number
but People API didn't return it, use the sheet's number — it's the one
NDR's team entered directly.

### Supplementary check: Honcho memory — before Gmail extraction

After querying both Google Contacts and the NDR DRAAS Contact Sheet (and
before falling through to Gmail signature extraction), always run
`honcho_search` for the person's name. Honcho memory captures:

- **User-confirmed phone numbers** from prior conversations — e.g. Nishant
  may have said "Anbu's DRA number is +918150029900" in a past session,
  which honcho saves but never makes it into Google Contacts or the sheet.
- **Context about who the person is** — their role, project involvement,
  email address, which helps confirm you have the right person when the
  sheet shows multiple matches.
- **Email addresses and alternate spellings** that help refine what you
  search for next.

```python
results = honcho_search(query="Anbarasu Anbu DRAAS phone")
```

**When to skip Gmail entirely:** If honcho returns a phone number that was
explicitly stated and confirmed by the user in a prior conversation, use
it directly. Honcho-confirmed numbers carry the user's own verification —
they are more reliable than a Gmail signature extraction.

**Pattern from this session:** For Anbu/Anbarasu (DRAAS employee involved
in RERA), Google Contacts returned only a "Guru Tiles (Anbu)" entry with
a different number. The Contact Sheet had "Anbarasan" at row 250 but with
a murky phone. Honcho memory returned the exact confirmed DRA number
(+918150029900) that Nishant himself stated in a prior session: *"Anbarasan
(Anbu) has username pm2.blr, phone +918150029900, and is WhatsApp-only for
site."* This saved a Gmail search and provided the correct number directly.

### Fallback: Contact not in Google Contacts or Sheet — extract from Gmail signature

If **both** Google Contacts `searchContacts` and the NDR DRAAS Contact Sheet
return zero results for the person's name (including phonetic variants),
the person may still be in the user's email history with a phone number in
their email signature. Use the Gmail-signature extraction technique:

1. Search Gmail for the person's name (and phonetic/domain variants) via
   `gws_skill_bridge.call('gmail_search', query=..., max=5)`
2. Find an email **FROM** the person (check the `from` field in results)
3. Use `gws_skill_bridge.call('gmail_get', message_id=..., format='full')`
   to read the full body — the signature block usually sits at the bottom
4. Scan for phone numbers (lines starting with `+`) labelled "WhatsApp"
   or "Mobile"
5. Pass the WhatsApp-specific number to `whatsapp_link()`

**Parameter gotcha:** `gmail_get` takes `message_id=`, not `id=`. See
`references/contact-from-gmail-signature.md` for the full procedure,
phone-number selection rules, and all pitfalls.

For phone numbers, prefer `phoneNumbers[].canonicalForm` (already E.164) over
the raw value. The wa.me path needs the country code with no `+`, no spaces, no
dashes (the `whatsapp_link` tool strips non-digits for you, but if you read
the canonical form directly it is cleanest to pass).

### For a group

The user picks the group in WhatsApp after tapping the link. Pass an **empty
phone** to the tool so the URL has no `phone=` parameter. The text is the
message; the group is selected by the user at compose time.

```python
args = {"phone": "", "text": group_message, "platform": "telegram"}
result = json.loads(whatsapp_link_tool(args))
# → url starts with https://api.whatsapp.com/send?text=...
```

## 3. Stage 2 — Draft the message (no raw `&`)

Voice messages from the user are messy. The job here is to extract the
intent, organize it into numbered points or natural paragraphs, and rewrite
all `&` characters to a safe alternative.

### Voice → text cleanup checklist

- Replace `&` with one of: `and`, `plus`, `with`, `and/or`, em-dash (`—`).
  Examples: "Premium FAR & TDR" → "Premium FAR plus TDR"; "Amit & Saurabh"
  → "Amit and Saurabh"; "FAR 4.0 & 4.5" → "FAR 4.0 and 4.5".
- Replace `Rs.` / `INR` with `Rs` (no trailing period) for encoding safety.
- Keep currency as `Rs XX Cr` (the rupee symbol `₹` is fine in source — the
  tool URL-encodes it correctly — but `Rs` is universally readable on
  mobile).
- Preserve the user's voice — don't add boilerplate greetings, don't strip
  filler, don't "AI-ify" the phrasing.
- **Technical terms the recipient will ACT on must be corrected, not
  reproduced** — when the user misnames a technical term and the recipient
  needs the right term to act safely (observed 2026-08-14: NDR said "HIPAA
  filters" meaning **HEPA**; the air-purifier cleaning message must say HEPA
  or the cleaning instructions are meaningless), write the CORRECT term in
  the message and tell NDR you corrected it. Reproducing the misnomer costs
  a correction round; the recipient acts on the wrong word.
- Address each named recipient in a separate short paragraph (the user
  will paste into a group, so named addressing is helpful for context).
- For voice messages containing multiple distinct topics (the typical
  NDR follow-up pattern), use numbered points (1), 2), 3)) — the user
  mentally tracks items by number.

### NDR-specific tone patterns

- **Broker / agent / chief style**: open with the nickname or
  "Chief" / "Boss" if the user used it; numbered items; "Awaiting your
  update" / "Please advise" close; no greeting.
- **Godrej Venture / institutional style**: open with "Good morning
  [name], [name], [name]" (voice-message form), then numbered items
  with sub-points; close with "Awaiting your update and feedback".
- **Personal / family**: warmer, no subject prefix, no numbering.
- **Senior government official / Joint Commissioner**: formal and respectful. Open with "Respected Sir," (or "Respected Madam,"). Use full honorifics and deferential phrasing ("Request you to kindly...", "What do you advise, sir?"). Close with "Regards," and full name. Structure the message to acknowledge the official's position and the relationship history before making the ask. The goal is to make the recipient feel inclined to help — not pressured. Use phrases like "under your advice and guidance," "as assured by you," "I hope you understand our position." Tone: cooperative, not demanding; the passage of time is stated as fact, not as accusation. Sign off with company name as "DRA Group" not "DRAAS".
- **Personal doctor / known medical professional** (user-corrected Aug 2026): warm and personal before stating the medical context. Open with a greeting — "Hey doctor, how is it going?" — not straight into business. Reference the prior patient relationship as shared context: "As you know, you have seen [child] before." State the known medical pattern factually (chronic condition, viral → asthmatic flare-up). Explain why the certificate/document is needed — external pressure (school SOP, board requirements), not your preference. Make the specific ask with bullet points. Add urgency if relevant (exam tomorrow). Offer to draft it for them with a 😉 to keep it light and collaborative. Close warmly: "Thank you as always, doctor!" No numbered items, no competitive pressure. Structure: greeting → context → situation → ask with bullets → offer to help → warm close.
- **New contact introduction** (after meeting someone for the first time): direct but warm — open with "Pleasure meeting you." Then share Nishant's contact details in plain structure: Name, Role, Phone, Email. Close with a specific reference to the project discussed (shows you were listening). No numbered items, no greeting boilerplate. Example:

```
Hello [Name],

Pleasure meeting you. Here are my contact details:

Nishant Ranka
CEO — DRA Group

Mobile: +91 98800 55634
Email: ndr@draas.com

Looking forward to working together on the [Project Name].

Thanks,
Nishant
```

The WhatsApp link is generated using the contact's phone number (just looked up from the new contact record). This pattern always follows visiting card processing (see `google-workspace` skill: Visiting Card Import Workflow).

### Message layout preference (USER-CORRECTED)

The user explicitly prefers WhatsApp messages formatted with **visual structure**:
bullet lists for enumerations, line breaks between distinct sections, and clear
separation of topics. A wall-of-text single-paragraph message will be corrected.

**Formatting rules (in priority order):**

1. **Bullet any list of 2+ items** — email addresses, file types, action items,
   people names. Each bullet on its own line.
2. **Blank-line separate each logical section** — don't cram multiple topics into
   one paragraph. A message about "files shared + close out DD + originals pickup"
   should have 3 sections separated by blank lines, not one run-on sentence.
3. **Lead with the key action** in the first line, not a preamble. The user
   reads the first line to decide urgency.
4. **Label each bulleted item** with a short descriptor in parentheses when the
   raw value needs context (e.g. email addresses → "(you)" / "(Advocate Vinod)"),
   so the recipient instantly sees who each line refers to.
5. **Keep the link title concise** — the Telegram display text should be enough
   to convey the message. The detailed formatting (bullets, line breaks, sections)
   matters in the WhatsApp compose box after the user taps the link, not in the
   Telegram link title itself. The `display_link` from the tool already shows the
   full text, so structure it there.

**Worked example of the preferred layout** (from user's explicit correction):

```
Nishant Prakash — I've shared 1-month viewer access to all the Serenity Hillview
legal DD files (43 files) to the following 4 email addresses:

• nishantprakash@theyelloweye.com (you)
• nishantprakash@me.com (you)
• vinod@advocatev.in (Advocate Vinod)
• hemanthpanagar07@gmail.com (Advocate Vinod)

Request you to please close out the entire legal DD today. Everything has been
given and clarified in the email to Vinod as well.

As far as original scrutiny is concerned — I've requested you and Manohar to
follow up with Vikram and pick up all originals ASAP.
```

**When NOT to use this layout:** single-sentence voice-message summaries for
recipients who prefer brevity (e.g. "Chief — no update from Bhuvanesh yet,
following up again"). The structure rule applies to *informational* and
*action-list* messages, not to one-liners.

## 4. Stage 3 — Call the tool and report

### Individual contact

When the tool IS loaded in your toolsets, call it by name. When it is NOT
(terminal fallback — see the Terminal fallback section above):

```python
import sys, json
sys.path.insert(0, "/opt/hermes")
from tools.whatsapp_link_tool import whatsapp_link_tool

args = {
    "phone": "+919999673483",       # E.164 with or without +
    "text": cleaned_message,        # NO raw `&`
    "platform": "telegram"          # optional, for MarkdownV2-safe output
}
result = json.loads(whatsapp_link_tool(args))
url = result["url"]
display_link = result.get("display_link", "")
```

Present to the user as a markdown link: `[Open WhatsApp to Sunny](url)`.
Also include the raw URL in parentheses for users who want to copy it.

### Group

Same reporting pattern, but the link text should make clear that the
**user needs to select the group after tapping**:
> [Open WhatsApp with this message pre-filled — pick the group to send it to](url)

The handler call is identical to the individual contact case — simply omit
the phone number:

```python
args = {"phone": "", "text": cleaned_message, "platform": "telegram"}
result = json.loads(whatsapp_link_tool(args))
```

## 4a. Batch multi-recipient runs — one link per person (NDR pattern, Aug 2026)

When the user asks for the same message to N people ("a separate WhatsApp message for each one so I can send it to each one by clicking"):

1. **Resolve all contacts in ONE script.** Query People API `searchContacts` across BOTH `google-draas` and `google-ahfl` for every name in one pass, print name + phones. This beats running `find_contact.py` N times. (Contacts like "Nagarajappa Jdtp North" live only in google-ahfl; employees in google-draas.)
2. **Two numbers on one contact:** use the first/primary listed, then list ALL used numbers in the final summary reply and flag the alternates so the user can correct (e.g. "Aravind had two numbers — I used X, say the word for the alternate"). Do not silently pick.
3. **Generate ALL links in ONE terminal script** calling `tools.whatsapp_link_tool` directly (the sanctioned fallback — same encoding logic), looping over `(name, phone)` and printing `### Name | url`. This keeps 14 × ~4KB URLs out of context; a parallel 14-call tool-invoke would flood it. Handle `"split": true` per link if it appears.
4. **Deliver each link as its OWN Telegram message** via `send_message` — one bubble per person with a short label: `[Open WhatsApp — <Name> (voice recording)](url)`. NEVER combine N links in a single reply: N × ~4KB URLs blow past Telegram's 4096-char cap and links get truncated. This extends the P5 split rule to multi-link runs (verified Aug 2026: 14-link broadcast delivered as 14 bubbles, all intact).
5. Same message body for all, personalized salutation (first name only). Use the appropriate tone pattern — for internal urging, Pattern D (cooperative-but-firm) from `personal-messaging`.

## 4b. QR Code generation from WhatsApp link

When the user asks for a **QR code image** containing a WhatsApp link (e.g. "generate a QR code for my WhatsApp number with a message"), the workflow is:

1. **Compose the message** following all rules in Stage 2 (no raw `&`, bullet structure, etc.)
2. **Call `whatsapp_link` first** to get the safe, fully-encoded URL — never hand-construct it, even though you're making a QR code, not a clickable link. The `whatsapp_link` tool's encoding is the authoritative source.
3. **Extract the URL** from the tool's JSON result (`result["url"]`)
4. **Generate the QR code** using `qrcode[pil]`:

```python
import qrcode

# URL from whatsapp_link tool
url = result["url"]  # e.g. "https://api.whatsapp.com/send?phone=919880055634&text=..."

qr = qrcode.QRCode(
    version=None,
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # H = ~30% recovery
    box_size=10,
    border=4
)
qr.add_data(url)
qr.make(fit=True)
img = qr.make_image(fill_color='black', back_color='white')
img.save("/path/to/output.png")
```

5. **Deliver** the image via `MEDIA:/path/to/file.png` in your response. The user can save the image from Telegram to their phone and share it.

**Context:** The user specifically asked for "a QR code using a QR code generating Python library where it's a WhatsApp link" — this is a distinct use case from just sharing a clickable wa.me link. The QR code is meant to be printed, displayed on marketing material, or shared as an image that anyone can scan to open WhatsApp.

### Install the library

```bash
uv pip install qrcode[pil]
```

`qrcode[pil]` includes PIL/Pillow for image rendering. Install in the Hermes environment.

### DELIVERY: Must include message text (USER-CORRECTED)

**Always include a pre-filled message in the QR code's WhatsApp link.** A QR code with only a phone number (no `?text=` parameter) is useless — when scanned, it opens a blank chat with no context, and the user will ask you to regenerate it with the message. This was corrected in session.

The one exception is when the user explicitly says "just the number, no message" — and even then, confirm they really mean it, because they often change their mind once they see the bare QR.

### Pitfalls

- **Install issue:** `uv run python3` may fail to build hermes-agent itself. Use `python3` directly with the venv path added to `sys.path`:
  ```python
  import sys
  sys.path.insert(0, '/opt/hermes/.venv/lib/python3.13/site-packages')
  import qrcode
  ```
- **Platform-specific:** The generated image is a standard PNG — works on all platforms Telegram delivers to (iOS, Android, Desktop).

## 5. Pitfalls

### P0b. DELIVER THE LINK ITSELF — never just the message prose (USER-CORRECTED)

The `whatsapp_link` tool returns the URL in `url` (raw) and `display_link`
(markdown-link form for Telegram). The deliverable is **the link**, not a
restatement of the message text. A reply that only shows the formatted message
prose and says "the WhatsApp message is ready" forces the user to ask again for
the actual link. Corrected Aug 2026 — user: *"Somehow, the message for Rahul got
truncated. Also, I need the WhatsApp link... redo the entire message as multiple
links."*

Delivery rules:
1. When the tool returns a single `display_link`, send it as an inline
   `[text](url)` markdown link in your reply — the user taps it to open
   WhatsApp. Do not paraphrase it away.
2. **Long messages: use a SHORT label, not the full-text display_link (USER-CORRECTED Aug 2026).** For a message of ~500+ chars, the tool's `display_link` labels the link with the ENTIRE message text (MarkdownV2-escaped). Pasted verbatim, Telegram renders the escaped label literally (`\*`, `\.` visible) and it does not read as a tappable link — user: "It's not generated properly as a link. Using the link tool, please." Fix: keep the tool-generated URL but wrap it in a concise label, e.g. `[Open WhatsApp — DRA Realty Group (Robocalling message)](<url>)`. The full text still arrives in the WhatsApp compose box; only the Telegram link title is shortened.
3. When `split: true` is returned, the `parts` array holds one complete
   tappable link per part — deliver EACH part as its own separate Telegram
   message (never combine them into one message; Telegram's 4096-char splitter
   will cut the link). Apply the short-label rule to each part too.
4. After delivery, one short line of context is fine ("folder + 3 drawings
   linked, deviations note at bottom") — but the link(s) themselves must be
   visible in the response.
5. If the user says the link "got truncated" or "didn't come across", re-call
   the tool (same text) and re-send the `display_link`/`parts` — do not just
   paste the prose again.



When the user says "share document number X with [person]" via WhatsApp, you must resolve which actual Drive files they mean **before** generating the link. The user frequently refers to numbered documents in a series (e.g., Ranka Udaya docs 01–08 in the TMP folder).

**Prerequisite sequence before Stage 1:**

1. **Find the document** — Search the TMP folder (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) for files with `NN_` prefix matching the user's number. Example:
   ```python
   children = drive.files().list(
       q="'18p74II2uL32sNDzDDwXzmlOUdJJOTmE-' in parents and trashed=false",
       fields='files(id,name,webViewLink)', pageSize=100, orderBy='name'
   ).execute()
   ```
2. **Handle missing numbers** — If the user says "07" but no `07_` file exists, the numbering may have shifted. Read document content (export as text/plain, check first 1000 chars) and match by description:
   - "agent briefing" / "tone" / "bucketing users" → `05_FINAL_Agent_Briefing_v3.md`
   - "master brief" / "automation" / "cron jobs" → `08_MASTER_Brief_to_Tech_Agency.md`
3. **Verify access** — Before telling the recipient to "download and share," check the recipient already has writer/editor permission on the doc. Query `drive.files().get(fileId=DOC_ID, fields='permissions')` for their email. If missing, grant it via `permissions().create()` before the WhatsApp message goes out.
4. **Build the message** with numbered doc identifiers matching the user's own numbering, a clear one-line description of each doc, and the Drive link. Example structure:

   > Bharat — please share these 2 documents with [team]. You already have editor access to both.
   >
   > Document 7 — Merged Agent Briefing for Tech Agency: [link]
   > Covers how the AI agent should respond, tone of response, bucketing users.
   >
   > Document 8 — Master Brief to Tech Agency: [link]
   > Covers the total automation stack — cron jobs, enrichment, lead state store.

### P1. Raw `&` in the source text breaks the link (USER-CORRECTED)

This is the single most important rule in this skill. The user explicitly
called this out after the first wa.me link broke: \"you have not used the
WhatsApp tool… it is again breaking around the ampersand sign and in the
tool we have already created special handling for ampersand sign.\"

Fix: rewrite `&` to \"and\" / \"plus\" / \"and/or\" / em-dash in the source
text BEFORE calling `whatsapp_link`. Do not try to URL-encode `&` yourself
in the message string — let the tool's special handling do its job, and
that handling assumes no raw `&` is present.

If you must keep `&` for typographic accuracy (e.g. a legal name like
\"Smith & Co.\"), use a workaround: \"Smith and Co.\" in the message and
note the original spelling in a short preamble the user can drop.

### P2.1. Contact name doesn't match — try phonetic variants and clarify

When the user says a name that returns ZERO contact results, the name may be:
- A **phonetic variant** of a common Indian name (e.g. "Gitu" → "Jitu", "Jitendra", "Jitu Mehta"; "Bappi" → "Bapi"; "Shridhar" → "Sridhar"). Try searching the phonetic alternative before reporting "contact not found."
- A **nickname / term of address** the user uses personally that differs from the contact's stored display name (e.g. user says "Sir" or "Boss" for someone stored as "Dr. Venkatesh"; user says "G2" for someone stored as "Jitu Virwani"). Ask: "Is this person also known as [variant] in your contacts?"
- A **role-based reference** (e.g. "the auditor" → search by email domain, "the Godrej guy" → search by organization name). Don't assume the user will use the stored name.
- **Designation-as-name suffix (correction 2026-08-21):** The user's voice often appends a role/designation suffix to the name: "Mohan ADTP", "Mohan Sir JDTP GBA East", "Nagrajappa JDTP", etc. Standard `contact_resolver` fails because the stored name differs from the voice-compound. **Fix:** Strip the suffix (ADTP, JDTP, BBMP, GBA East, Sir, etc.) AND search People API `searchContacts()` directly with just the first name — the role is often part of the stored display name as a single unstructured field like "Mohan Sir JDTP GBA East". The standard partial-name `contact_resolver` doesn't match these compound forms; direct People API does. For "Mohan ADTP" (this session), the actual contact was found via `searchContacts(query='Mohan')` on google-draas returning "Mohan Sir JDTP GBA East" (+91 98868 85455). Checklist: strip suffix → search bare given name across all three vault accounts → cross-reference role context (land, Northstar, airport NOCs) to confirm the right match.

**Correction history**: The user said "Gitu, sir" for a contact involved in NDA/family settlement work. Initial search for "Gitu" returned nothing. The person was likely "Jitu" (a different contact in the same account) — the user's pronunciation merged dental and retroflex consonants. Always try the alternate dental/retroflex or voiced/unvoiced variant when a name search returns zero results.

Search strategy when initial query fails:
1. Try the phonetic variant (swap G↔J, T↔D, S↔Sh, etc.). Common Indian name confusions: "Nisabharaju" → "Narsimharaju", "Gitu" → "Jitu", "Bappi" → "Bapi", "Shridhar" → "Sridhar", "Vineet" → "Vinay", "Bhuvanesh" → "Bhubanesh".
2. Try partial matches (first 3-4 chars of the name).
3. **Check the NDR DRAAS Contact Sheet** — it often has contacts stored under a different spelling or format than Google Contacts. Scan the First Name column (col A, index 0) for partial string matches. The sheet may store the name in a single field like "Narsimharaju Jt Com IT" while the user says "Nisabharaju". Pattern:
   ```python
   sheets = build_service('sheets', 'v4', service_name='google-draas')
   all_data = sheets.spreadsheets().values().get(
       spreadsheetId='1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g',
       range='A:AR'
   ).execute()
   for i, row in enumerate(all_data.get('values', [])[1:], 2):
       first = (row[0] if row else '').lower()
       if search_term.lower() in first or any(term.lower() in first for term in phonetic_variants):
           # row found — report the detected stored name
   ```
   **Important**: Also search with the user's ORIGINAL pronunciation, not just the phonetic variant. The sheet name might match the user's pronunciation better than the Google Contacts name does.
4. If the person was mentioned in this conversation or a recent session, use `session_search` to find their full name from context.
5. If still not found, ask the user for one of: phone number, email, or the exact name they saved the contact under.

### P2.2. Multiple contacts match — disambiguate with `clarify`

**Before clarify, try Gmail-context disambiguation.** When several same-name candidates exist but the conversation topic is known, run a Gmail query pairing the name with topic keywords (e.g. `Kishan (algo OR AIF OR trading OR Nifty)`). If one candidate's threads are decisive — recurring "Performance Update" emails from their company domain matching the user's story — use that person and skip the clarify round-trip. Worked 2026-08-14: 4 "Kishan" candidates; Kishan Murjani Nair (kishan@flamebackcapital.com) won on thread evidence alone. Fall back to `clarify` only when no candidate has contextual proof.

When a name search returns MULTIPLE contacts and none is an obvious match for the user's intent, use the `clarify` tool to present a shortlist as numbered choices. This is faster than asking open-ended and avoids the user having to read your full prose list.

```python
clarify(
    question="I found several \"Vikram\" contacts — which one?",
    choices=[
        "Vikram Jain Karbawala (+91 98450 70779)",
        "Vikram Talreja / Sparc Studio (+91 98453 99997)",
        "Vikramaditya / Kelsa (+91 77605 03837)",
        ...
    ]
)
```

**When to use this**: you've searched and found 3–10 plausible contacts, none of which has a strong contextual match to the topic the user mentioned (e.g. project name, company name). Do NOT use this when only 1–2 contacts matched — just present the best candidate and ask a yes/no question instead.

**Phone-saved name mismatch**: the user sometimes says "my address is [name]" — meaning their phone's local address book entry. This phone entry name may differ from the Google Contacts display name (e.g. phone says "Vikram Sa" but Google has "Vikram Jain Karbawala"). Search broadly for the given name and use the clarify tool to list the options, rather than assuming the phone's abbreviation will match Google's stored name.

### P2.3. Voice-transcribed names are often wrong — including project/builder names

User's STT regularly corrupts proper nouns. "Sadhwani" comes back
correctly, but "Byadarhalli" → "Bihar Ali", "Vineet" → "Vinay",
"Jiraff Capital" → "Jiraffe Kaya", and **"Legacy Cataleya" → "Century Katalya"** have all been observed.

**For contact names** — verify against the People API (searchContacts returns canonical spelling) and Gmail Sent. Call out which names were corrected.

**For project / builder / company names** — when the user asks you to research a named project and web search returns nothing, the name may be garbled. Follow this workflow:

1. **Search the garbled name** exactly as transcribed — sometimes the STT match is correct and the project is simply not online.
2. **Try phonetic variants** — swap L↔C, K↔C, T↔D, etc. "Century Katalya" → "Century Cataleya", "Century Catalia", "Century Katalia", then try the first word swap: "Legacy Cataleya" (the actual project was "Legacy Cataleya", not "Century Katalya" — every word was wrong).
3. **Search by landmarks** — the user often provides location context. "Kaningam Road" (→ Cunningham Road), "next to Ranka Chambers" helped narrow Cunningham Road as the location.
4. **Search real estate portals** for projects at that landmark — check 99acres, MagicBricks, Housing.com, Commonfloor for projects matching the location, not the name.
5. **Use `clarify` with the closest candidates** — present 3–4 options from what you found at the location. The user will recognise the right one even if they'd accept the garbled name.
6. **Once the correct name is confirmed**, do full research (RERA number, address, survey number, BBMP sanction, status, unit details). Use the RERA portal (rera.karnataka.gov.in) or aggregator sites like aurumproptech.in for structured project data.
7. **Call out which names were corrected** in your response so the user knows the voice transcription was wrong.

**Session example (2026-07-29):** User said "Century Katalya on Kaningam Road next to Ranka Chambers." Web search returned zero results for "Century Katalya." Through phonetic variants and landmark-based searching on real estate portals, the closest match found was "Legacy Cataleya" on Cunningham Road. The user confirmed via clarify. Full project details were then researched from RERA and brokerage sites.

### P3. The tool does not validate the phone number

`whatsapp_link` strips non-digit characters and builds the URL, but it
does not check whether the number is a real WhatsApp account. If the
contact record has a number that is no longer active, the link will
open WhatsApp with the recipient field pre-filled, but the user will
discover at send time. Prefer the **canonical form** from the contact
record (E.164 with the country code) over the raw display value.

### P4. Group messages need an empty phone, not a fake one

When the user says "I'm putting the message in a group," pass `phone=""`
to the tool. Do NOT pass a single recipient's number hoping WhatsApp
will somehow route to the group — it won't, and you'll send a 1:1
message to the wrong person when the user taps the link.

### P5. Long messages still work, but watch the prefill — and the Telegram delivery limit (USER-CORRECTED)

WhatsApp's prefill is robust for messages up to a few thousand
characters. The **Telegram delivery** of the resulting wa.me link is
not. Telegram splits outgoing text at ~4096 characters per message
(both for caption bodies and for the body of a normal text reply). A
long voice-transcribed follow-up — 1–2 KB message + 1–2 KB of URL
encoding on top — easily exceeds 4 KB once you count the markdown
link wrapper. When that happens, Telegram delivers the result as **two
separate bubbles**, the wa.me URL is truncated at the split point, and
the user gets a broken link. The user has corrected this twice:
*"Can you give me Charan's WhatsApp message link again… it did not
come across properly because it got split into two messages here."*

**The tool now auto-splits** (2026-08-07): `whatsapp_link` detects when a
  URL would exceed Telegram's 4096-char single-message cap and returns a
  `parts` array — one complete, independently-tappable link per part, each
  sized so even the `[display text](url)` form fits one bubble. When the
  result has `"split": true`, deliver EACH part as its OWN separate
  Telegram message (e.g. via `send_message`); never paste multiple parts
  into one message or Telegram's splitter will cut a link in half.

**Optional compaction (fewer links = cleaner UX):** after `whatsapp_link`
returns, if the response would contain multiple parts, you may compact
the message first and call the tool again so the user gets one link.
Strategies that work, in order of preference:
  1. **Strip sub-bullets and the closing "Regards / phone" block.**
     Many voice messages end with a long sign-off; the user can add
     that themselves after tapping. Cutting "Regards, Nishant Ranka /
     +91 98800 55634" typically saves 60–80 chars.
  2. **Inline the numbered points as a single line per item** instead
     of multi-line paragraphs. "1. Reporting time — please confirm…
     2. Documentation — please confirm you have…" instead of
     "\n1. Reporting time\n\nPlease confirm…\n\n2. Documentation\n\nPlease confirm…".
     This is the single biggest win — long messages usually have
     paragraph-broken bullets that add ~2× the bytes.
  3. **Drop "Kindly confirm", "Awaiting your revert on this" and
     similar filler** that voice messages accumulate. Each cut saves
     20–40 chars and the user does not miss them.
- After rewriting, call `whatsapp_link` again. The link should fit in
  one Telegram bubble.
- Tell the user the link has the full message and they can scroll
  within the compose box.

**Symptom-recognition rule for an already-split message:** if the user
says the link "didn't come through properly" or "got split into two
messages" right after a `whatsapp_link` reply, this is the cause, not a
bug in the tool. The link is fine; the *delivery* chopped it. Re-send
using the compaction above and confirm in the re-sent message that it
is a single link.

### P5b. Very long messages fail on mobile WhatsApp — deliver an HTML file (USER-CORRECTED)

Distinct from the Telegram-split problem: even when the link arrives as
ONE bubble, a very long `?text=` parameter (~4 KB+ of encoded URL) can
fail to open or pre-fill on the WhatsApp mobile client. The tool's
auto-split (P5) already caps each part's URL at Telegram's 4096-char
budget, so this is now rare — the HTML fallback below remains for
extremely long messages the user wants in ONE tap. The user reported
the link "not working" and the follow-up request was explicit: *"If the
message is too long, let's generate an HTML file in which the link is
kept so I can click it and send the message to the group."*

### P5c. Delivery format preference — code block for copy-paste (USER-CORRECTED 2026-08-21)

When the user asks for WhatsApp links and says they want them "presented
as a code section" / "with all the whatsapp markdowns so I can copy and
paste directly," deliver BOTH:

1. The tappable markdown link: `[Open WhatsApp — Name](url)`
2. A fenced code block containing the raw URL for copy-paste

The user uses the code block to copy the link and paste it into a
different app (group chat, another chat, their notes). Do NOT skip the
code block when this format is requested — the default tappable link
alone isn't sufficient for his workflow.

Example of the requested format:

```
🔗 Person Name — WhatsApp link (tap to open):
[Open WhatsApp — Person Name](<url>)

📋 Copy-paste version:

<url>
```

This format override applies when the user explicitly asks for code
blocks / markdowns / copy-paste ready delivery. It does not replace the
default single-link delivery; it augments it on request.

**Fix pattern (in order):**
1. **Condense the message first** — compact the draft (drop filler,
   inline bullets, shorten sign-off). Short URLs almost always work.
2. **If still long, build an HTML file** at `/opt/data/` (e.g.
   `kelsa_whatsapp_message.html`) containing:
   - A WhatsApp-style chat bubble showing the full message text (so the
     user sees what will be sent), using `white-space: pre-wrap`
   - A large green button (`background:#25d366`, border-radius:50px)
     whose `href` is the **exact URL returned by `whatsapp_link`** —
     never a hand-built URL
   - A smaller "Direct link (copy if needed)" anchor with the same URL
   - A note: "Tap the green button → WhatsApp opens with the message
     pre-filled → choose your group and send"
3. Deliver with `MEDIA:/path/to/file.html` in the response so it arrives
   as a downloadable file the user can open on their phone.
4. Mention that WhatsApp shows `＆` (fullwidth ampersand) in long
   encoded messages — that is correct encoding, don't edit it.

**Percent sign (`%`):** the tool encodes `%` exactly once (`%25`) and emits
`api.whatsapp.com/send` links (never `wa.me`). **BUT the `%` is STILL
corrupted by WhatsApp's own decoder — verified live 2026-08-10.** A short
test link (`api.whatsapp.com/send?phone=…&text=Test%3A%2012.5%25%20tax…`)
that survived Telegram's delivery intact still rendered `�` (U+FFFD)
instead of `%` in the WhatsApp compose box. This is NOT a wa.me redirect
problem and NOT a Telegram-truncation problem — it is WhatsApp's mobile
client re-interpreting the decoded `%` as the start of another escape
sequence. The `&`/`#` fixes in the tool sidestep this exact mechanism by
substituting **fullwidth characters** (`&`→U+FF06 `%EF%BC%86`, `#`→U+FF03
`%EF%BC%83`) whose UTF-8 escapes contain no `%26`/`%23` substrings. The
same fix is needed for percent but is NOT yet in the tool: add
`encoded.replace("%25", "%EF%BC%85")` in `_encode_wa_text()` (U+FF05
FULLWIDTH PERCENT SIGN ％; `%EF%BC%85` contains no `%25`, so no cascade —
a literal `%25` in source encodes to `%2525` and is untouched). Until the
tool is patched, the pragmatic fallback for user-facing messages is to
write "percent" in words (e.g. "12.5 percent") instead of `%`.

**Diagnostic for "broken character in WhatsApp link" reports:** first
generate a SHORT test link (a sentence with the suspect character, no
long message) and have the user tap it. If the short link is clean, the
problem was Telegram truncating the long URL — re-split/re-send. If the
short link is STILL corrupt, the problem is WhatsApp's decoder — apply
the fullwidth-substitution fix for that character (see above).

See `messaging-drafts` skill → `references/whatsapp-chunked-message-html.md`
for the multi-chunk variant when the message itself must be split across
multiple sends.

### P5d. Split-part delivery — the WORKING send_message call shape (2026-08-24)

When `split: true` and you deliver each part via `send_message`, the ONLY call
shape that works for the DM session is **person-to-person addressing**:

```
send_message(recipient_name='Nishant Ranka', platform='telegram', message=<part display_link>)
```

Tried-and-rejected variants (all fail on the Telegram gateway):
- `target='telegram'` → `Cross-user send blocked` (resolves to the home channel, not the session DM)
- `target='origin'` → `Unknown platform: origin`
- bare `message=` with no target → validation error (needs recipient or target)

Also capture NDR's explicit rule from the same session (user: *"I need you to just
generate the WhatsApp link using the WhatsApp link tool, not send the WhatsApp"*):
the deliverable is the **link(s) from `whatsapp_link`** — he taps, picks the group,
and pastes himself. Do NOT spend turns fighting delivery targets or attempting to
post to WhatsApp programmatically (Hermes cannot). Generate the link(s), deliver
them cleanly (one part per bubble), and stop. If delivery tooling is misbehaving,
put the links in the reply and tell him they're ready — don't loop on `send_message`.

### P6. wa.me deep links cannot carry file attachments

The `whatsapp_link` tool only pre-fills text — it cannot pre-attach a PDF, image, or
document to the WhatsApp message. When the user dictates a message that says
"attaching the copy of mom's policy" or "see the attached report", the link will
open WhatsApp with text ready but the **user must tap the attachment (paperclip) icon
and pick the file themselves** before sending. Two patterns:

- **Best for one-off attachments**: draft the text via `whatsapp_link` and tell the
  user "the link has the text — open the chat, tap the paperclip to attach the PDF,
  then send." If the file is on Drive, give them the Drive link to download on
  their phone first.
- **Best when the attachment is the main payload**: skip WhatsApp and use a Gmail
  draft instead (see `email-drafter` skill). WhatsApp + PDF is awkward; email is
  the native channel for files.

Don't promise "the link will attach the file" — it can't, and the user will
discover the gap at send time.

### P7. User dictating a message to a third party is still a "send WhatsApp" task, not impersonation

A common voice-message pattern: the user dictates a message in
**second person** addressed to a named recipient, e.g. "Pratash, urgent.
Re: the Ranka Oasis email..." or "Amit, as per our last telephonic
discussion you were to check with your legal team...". The user is
**dictating instructions TO that person**, not asking Hermes to perform
that person's job.

Default action: this is a `whatsapp_link` task — the user is the sender,
Pratash / Amit / etc. is the recipient. Resolve the contact, draft the
message, generate the link. Do NOT act on the third party's behalf in
external systems (Gmail replies, Drive edits, Sheets updates) — that is
**impersonation**, not delegation.

**Pausing rule — when to clarify with the user**: if the dictated
message references actions that *only* the third party can take — e.g.
"open this Drive file owned by your legal team, attach the legal opinion
links, and reply-all to a thread involving external parties" — pause
and surface the role boundary. A "send a WhatsApp to Pratash with
these instructions" is the right shape; a "do this work as if I were
Pratash" is not.

The same rule applies to dictation that *names* the user in third
person ("Harish" for "Harsimran" in the user's voice, "Dharmesh" for
"DRA" etc.). Verify the intended recipient against the actual contact
record / Gmail thread, and produce a `whatsapp_link` for the
**real** person, not the STT-corrupted one.

### P8. Recipient identifiable but no WhatsApp number available — report the gap honestly

A common pattern: the user says "let's jointly call [Person]" or "send a
message to [Person]" where you can figure out who the person IS (from
Gmail threads, context, or memory) but have no WhatsApp number for them.
This happens with landlords, government officials, and external vendors
whose contact info lives only in email correspondence.

**What to do:**
1. Report what you found — name, email, role, project context.
2. Do NOT fabricate or guess a phone number. The user won't discover the
   broken link until send-time and will be frustrated.
3. For the task at hand: generate the link for the people whose numbers
   you have, and flag the gap for the person without a number. Ask the
   user to provide it, or note that you found their email if that helps.
4. If the person is someone the user will CALL (not WhatsApp), note that
   you don't have their number in your directory and ask the user to
   supply it.

**Session example:** Nishant said "make a joint call to Akbar as well"
for Aamir's message. You identified Akbar as Akber Hussain (AH Group,
akber@ahindia.com, Millers Road landlord) from Gmail threads, but no
phone number exists in Contacts, the Sheet, honcho memory, or email
signatures. Correct action: generate Aamir's link with the full context,
flag that Akbar's number isn't available, and ask the user for it.

## 6. Fallback: SMS via `sms:` URI

If WhatsApp is unavailable or the recipient is on a non-WhatsApp number,
fall back to a standard `sms:` URI. This is a hand-constructed URL —
there is no special tool, and ampersand handling is not an issue
because sms: URIs do not use `&` as a parameter separator (they use
`?body=` with a single body parameter).

```python
import urllib.parse
phone_digits = "919845070013"
body = cleaned_message
sms_url = f"sms:+{phone_digits}?body={urllib.parse.quote(body)}"
```

On Android the user gets a chooser; on iOS the URL opens Messages.app.
Report as a markdown link the same way as a wa.me link.

## 7. Fallback: mailto: for email-only follow-ups

When the user wants a "send a message" but the recipient is email-only
(landlords, government, regulators), use a `mailto:` URI. No special
tool needed; the same encoding rules apply (rewrite `&` in the body to
"and" first to be safe across email clients that may mis-split on `&`).

```python
import urllib.parse
mailto_url = (
    f"mailto:{recipient}?subject={urllib.parse.quote(subject)}"
    f"&body={urllib.parse.quote(body)}"
)
```

Note: `mailto:` legitimately uses `&` as a parameter separator (e.g.
`?cc=...&bcc=...`). The rewrite rule applies to `&` **inside the body
or subject**, not to the `&` between parameters — that one is correct
and required.

## 8. Verification

After presenting the link, do a quick sanity check:

1. The link starts with `https://api.whatsapp.com/send?` (or `sms:+` /
   `mailto:`). A `wa.me` URL is a sign of a stale/legacy path — regenerate.
2. The source text you passed had no raw `&` characters.
3. For individual contacts, the phone number is in the URL
   (`...send?phone=<digits>&text=...`).
4. For group messages, the phone number is NOT in the URL (only `?text=`).
5. The phone number has the country code (91 for India, no leading `+`).
6. If the result has `"split": true`, deliver each `parts[i]` as its own
   separate Telegram message.
7. The recipient is named in the message body or the surrounding prose
   so the user knows who they are sending to.

## 9. References

- `references/voice-transcribed-project-research-legacy-cataleya.md` — worked example of resolving a voice-garbled project name ("Century Katalya" → Legacy Cataleya) through phonetic search, landmark matching, clarify, and multi-source research (RERA, broker sites). Implements P2.3.
- `references/web-research-via-terminal.md` — Wikipedia REST API and
  MediaWiki API via curl: structured text extraction without web_search.
  Use this for the "research a topic, then WhatsApp" pattern the user
  frequently bundles in a single voice message.
- `references/ndr-followup-patterns.md` — 10 worked patterns from real
  sessions: broker/chief single-recipient, institutional group-message,
  WhatsApp + email pair, apology/delay-with-reason, hospital insurance,
  landowner progress update, and single-ask review/confirmation. Includes
  a cheat sheet of `&`-to-`and` rewrites and a pitfall for resolving
  DRAAS colleagues not in Google Contacts. Use this for the
  follow-up-message patterns that NDR uses most often.
- `references/contacts-sheet-naming-edge-cases.md` — parenthetical name suffixes and employee-style contacts that block People API / contact_resolver. When resolver returns only same-first-letter false matches, fall back to direct sheet search.
- `references/voice-firm-name-gmail-discovery.md` — resolve a voice-garbled FIRM name
  ("Balan & Nambisar" → Balan + Nambisan Architects / BN Architects) when contacts sheets
  return nothing: search the raw voice spelling in Gmail, read NDR's own narration emails for
  the spelled-out name, search the email domain to enumerate the team, and extract
  phone/address from signatures. Includes the BN Architects contact card (Janice Rodrigues
  lead; HAL 2nd Stage; +91-80-25217543/44).
