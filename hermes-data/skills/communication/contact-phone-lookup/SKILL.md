---
name: contact-phone-lookup
description: "Reliable phone number lookup for DRAAS contacts — avoids Telegram ID mixup"
version: 1.6.0
---

# Contact Phone Number Lookup

**Problem:** Telegram IDs are numeric and look like phone numbers, leading to incorrect WhatsApp links. Some contacts have multiple numbers (DRA, mobile, personal) and the wrong one gets used.

## Verified Table Hygiene — Google Contacts + Sheet Are Authoritative (user rule, Aug 2026)

**NDR's explicit rule: do NOT duplicate contacts into the skill's Verified
Phone Numbers table when they already live in Google Contacts (People API)
and/or the NDR DRAAS contacts sheet.** Those stores are the source of truth;
a copy in the skill table only drifts stale and gets trusted wrongly.

- Before adding ANY contact to the verified table, check: is it resolvable
  live via People API (`searchContacts` / `connections().list`) or the NDR
  DRAAS contacts sheet? If yes → do NOT add to the table. Just look it up
  live when needed.
- The table exists ONLY for: (a) numbers with special encoding quirks (wa.me
  digit traps, space-to-zero), (b) contacts NOT findable in live sources,
  (c) user corrections that override live data.
- Real example (Aug 2026): Akber Hussain (akber@ahindia.com, +91 98947 87515,
  PA Atheeq Sulaiman) was carried in the table as a fallback. NDR: "There is
  no reason for adverse contact in the contact phone lookup skill... it is
  there in my Google contact and online contact sheet. That's good enough."
  Deleted from the table; live lookup (People API) covers him. Note: Akber is
  in Google Contacts but NOT in the sheet; Atheeq is in the sheet row ~484 —
  check BOTH live sources, each covers different people.
- When you remove a table entry per this rule, say so in your report so the
  user knows the skill was cleaned.

## Lookup Order (priority)

When you need a contact's phone number (or office address / attendee email for
calendar invites), the same source order applies — see
`references/dra-office-address-and-attendee-resolution.md` for the DRA Realty
office address (contacts sheet Address 1 columns 39–47) and the Gmail
`from:`-header fallback that resolves "FirstName Company" people (e.g. Balaji
Natarajan balaji.n@drahomes.in, distinct from Balaji G balaji@drahomes.in):

1. **Google Contacts (People API)** — search with `people.people().searchContacts(query=NAME, readMask='names,phoneNumbers')`
   - **ALWAYS** prefer `type == 'DRA'` or `type == 'work'` labeled numbers FIRST
   - Only fall back to `type == 'mobile'` if no DRA/work number exists
   - NEVER use a number labeled `Defunct`, `Obsolete`, or `old`
   - Note: `searchContacts()` only searches "My Contacts", not "Other Contacts". Empty results != contact doesn't exist.

2. **NDR DRAAS Google contacts sheet** (ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`) 
   - Check columns 27-38 for phone numbers
   - Column 27 = Phone 1 Label, Column 28 = Phone 1 Value, etc.

3. **Old contacts sheet** (ID: `1KQe9CQyfpLXR16hYFLWNwwJ0NPEsv2q0PQwL4sEy8vU`) — fallback for contacts not in the resolver sheet
   - Fewer columns, but may have data the resolver sheet lacks

4. **Memory** — check stored contact info for known phone numbers

## Cross-Check
- If a number looks like it could be a Telegram ID (9-10 digits), verify it against the contacts sheet or People API
- Telegram user IDs have no relation to phone numbers — never assume they're the same
- When in doubt, use the DRA/work number from People API
- Contacts sheet data can be stale — always verify with the user before generating a WhatsApp link

### Pitfall — contacts_list Bridge Function is Unreliable

The `contacts_list` operation via `gws_skill_bridge.call("contacts_list", ...)` returns **garbage data** — same unrelated results regardless of the query. Observed Jul 2026: queries for "Aamir", "Akbar", "Sunder", "Padmanabhan" all returned the same 10 unrelated contacts.

**Fix:** Use the Google People API directly instead.

```python
from tools.gws_auth import build_service
# build_service returns a ready-to-use service Resource, NOT credentials
svc = build_service('people', 'v1', service_name='google-draas')
results = svc.people().searchContacts(
    query="Akber",
    readMask="names,emailAddresses,phoneNumbers"
).execute()
```

**Note:** `searchContacts()` only searches "My Contacts", not "Other Contacts". Empty results doesn't mean the contact doesn't exist — it may be in "Other Contacts" or only on the user's phone.

### Pitfall — contact_resolver returns unrelated filler matches; fall back to direct Sheets scan (Aug 2026)

The `contact_resolver` gateway tool can degrade into garbage matches: `query='Arvind Jain'` (context 'Palya Row Villas A.J. Architects') returned five **unrelated** contacts — all `A <surname>` rows (A Raju, A Ramesh, A Vishwanatha…) with score 90. It appears to have tokenized the query down to the first letter and matched the entire surname column; it did NOT surface "Arvind Jain Architect" (row 417) at all. This mirrors the known-unreliable `contacts_list` bridge.

**Fix — direct Sheets API scan of the contacts spreadsheet with keyword filtering:**

```python
svc = build_service('sheets', 'v4', service_name='google-draas')
SHEET_ID = '1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g'
# NOTE: list sheet titles FIRST — a guessed range name like 'Contacts' 400s
# with "Unable to parse range: Contacts". Actual title: 'NDR DRAAS Google contacts.csv'
meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
title = meta['sheets'][0]['properties']['title']
rows = svc.spreadsheets().values().get(spreadsheetId=SHEET_ID, range=f"'{title}'").execute()['values']
for i, row in enumerate(rows, 1):
    joined = ' | '.join(str(c) for c in row if c)
    if any(k in joined.lower() for k in ('arvind', 'architect', 'aj arch')):
        print(f"Row {i}: {joined}")
```

Worked 2026-08-25: found **Arvind Jain Architect** — arch.arvind2000@gmail.com, Arch_arvind2000@yahoo.co.in, **Mobile +91 98451 57101** (row 417). When the resolver output clearly doesn't match the name you queried (all same-letter filler), don't keep looping it — go straight to the sheet scan.

**Also:** `contact_resolver` may error `no gws_service configured in their profile` for the session user — call `gws_resolve_account` to get the valid account email, then pass `account_email=<email>` explicitly to the resolver.

### Pitfall — Multi-word searchContacts can MISS; retry with surname-only tokens (Aug 2026)

`searchContacts(query='Sanjay Sethia')` returned **no results** even though the contact existed — but the surname-only query `query='Sethia'` found it instantly (`Sanjay Sethia Advocate`). Same for `query='lawsquare'` (email domain): no hit. The People API tokenizes multi-word queries strictly; if the stored name/displayName doesn't match the full phrase, you get zero results and wrongly conclude the person isn't in contacts.

**Fix — when a full-name search comes back empty, retry with partial tokens BEFORE falling to a full `connections().list()` scan:**
1. surname alone: `query='Sethia'`
2. first name alone: `query='Sanjay'`
3. email domain: `query='lawsquare'`

This is cheap (3 API calls) and surfaces contacts whose displayName differs from how you'd phrase the query. Loop the partial tokens across all three accounts (google-draas, google-ahfl, google-gmail) exactly like the full-name loop. Confirmed live Aug 2026: Sanjay Sethia was found via google-draas with `query='Sethia'` after `'Sanjay Sethia'` and `'lawsquare'` both returned nothing — the contact had `givenName: 'Sanjay Sethia Advocate'` (a single unstructured name field), which the multi-word query didn't match.

### Pitfall — searchContacts() Returns Empty For Known Contacts

`searchContacts()` only searches "My Contacts" in Google — contacts in "Other Contacts" (imported from CSV, SIM card, or other sources) are invisible to this API. Empty results ≠ contact doesn't exist.

**Workaround — use `connections().list()` to scan ALL My Contacts:**

```python
from tools.gws_auth import build_service
service = build_service("people", "v1", service_name="google-draas")

# List ALL My Contacts
resp = service.people().connections().list(
    resourceName='people/me',
    pageSize=200,  # max per page
    personFields='names,phoneNumbers,emailAddresses'
).execute()
connections = resp.get('connections', [])
for person in connections:
    names = person.get('names', [])
    name = names[0].get('displayName', '') if names else ''
    # Fuzzy-match the name
    if 'gow' in name.lower()[:5] or 'singh' in name.lower():
        phones = person.get('phoneNumbers', [])
        phone = phones[0].get('canonicalForm', '') if phones else ''
        print(f"{name}: {phone}")
```

**Limitations of `connections().list()`:**
- Cannot search/filter by query — returns ALL contacts, you must iterate client-side
- Max 200 per page — paginate via `nextPageToken` if you need more
- Only returns contacts in "My Contacts", not "Other Contacts"
- Slower than `searchContacts()` for narrow queries — use as fallback only

**When to use this workaround:**
- `searchContacts("Gowri")` returns empty but you're confident the contact exists
- You want to scan for alternative spellings (Gauri, Gowre, Gowri Singh, etc.)
- The contact was imported and lives in a different name format than what you searched

### Pitfall — People API "Primary" Label is NOT WhatsApp-Preferred

**Critical: The People API `searchContacts()` returns `primary: true` on one phone number per contact. This is the contact's "default" display number in Google Contacts — NOT the best number for WhatsApp.**

WhatsApp messages to a "primary mobile" number will fail silently if that number isn't actually on WhatsApp, or if the contact uses a different number for business messaging. **The `type` label (`DRA` / `Work` / `Mobile`) is authoritative; `primary: true` is not.**

**Rule:** When a contact has BOTH a `type: DRA` or `type: Work` number AND a `type: mobile` number:
1. Use DRA first, then Work, then mobile — regardless of which has `primary: true`
2. Only fall back to `type: mobile` if NO DRA/Work number exists for that contact
3. If a `type: mobile` with `primary: true` matches a previous verified number in the table below, use that instead (the table overrides the label heuristic)

**Real failure (Jul 2026, Prakash Singh):** The People API returned:
- `primary: true, type: mobile, value: +919739932078` (primary mobile)
- `primary: false, type: DRA, value: +919900093816` (DRA)

The agent chose the `primary: true` mobile number and generated a wa.me link with `919739932078`. But the skill's verified table explicitly shows `9739932078` was wrong in a prior session and `919900093816` (DRA) is the confirmed WhatsApp number. **Don't let `primary: true` override the type-based preference — DRA > Work > mobile, every time.**

### Pitfall — Cross-Check Against Verified Table Before Delivering

After picking a phone number via the lookup order above, **before** generating the WhatsApp link:

1. Check the "Verified Phone Numbers" table below for this contact
2. If the table has an entry, use THAT number (it was confirmed in a prior session)
3. If your selected number differs from the table entry, note the discrepancy but use the table's number — it was verified by the user
4. Inline this verification into the WhatsApp drafting workflow: it takes 5 seconds and prevents silent wrong-number bugs

## CRITICAL: User Expectation — Exhaustive Search Before Asking

The user expects you to find the phone number yourself from available sources. **Do NOT ask the user for a number until you have exhaustively searched ALL sources** (People API -> resolver sheet -> old sheet -> memory). Asking prematurely will cause frustration signals like "What happened??".

If all sources fail or return outdated/invalid numbers:
1. Search session history for previous messages from/to this contact
2. Check if the user mentioned the contact in a WhatsApp forward (the forwarded message header shows the sender's name but not the number)
3. Only THEN ask the user — and explain what you tried so they know you didn't skip the work

### Pitfall — Don't Assume Past Session Content = Current Request

**Critical failure mode (Jul 2026):** The user said "I want a WhatsApp message for Kishan." A past session (June 18) had extensive content about NSE shares with Kishan. The assistant incorrectly pulled that old content and generated a message about NSE IPO details — but the user's current request was about something completely different (a philosophy message).

**Rule:** When a user says "I want a message for [contact]" followed by a voice dictation or two voice dictations that you need to combine, that spoken content IS the message. Do NOT search past sessions for old message drafts about that contact. The user is telling you the message content right now.

**Exception:** Only search past sessions if the user explicitly says "remember the message from before" or "repeat the message I sent last time."

## When the User Says a Number is Wrong

Present the raw search results from each source you queried:
- State WHICH source(s) you searched and what query you used
- Show the exact result(s) returned (redact other contact info if needed)
- Let the user identify the correct source, or share the right number directly

Example: "I searched the resolver sheet (query='Ravi') and People API (query='Ravi Vijay'). Results: resolver sheet -> Ravi Vijaysarthy: Mobile +91 99800 84646, Work +91 80 23367588. People API -> same numbers + email rvgroup89@gmail.com. Which one should I use?"

### Pitfall — Never Claim Work Without Tool Calls

When the user says a number is wrong and asks you to search again, **actually execute the search immediately in the same response**. Do NOT say "I've dispatched a background search" or "I'll look that up" without making tool calls. The user can see the conversation — claiming work that wasn't done erodes trust and wastes a round-trip.

**Correct pattern:** Immediately search the resolver sheet + People API simultaneously (they're independent), then present all results at once.

### Pitfall — wa.me Phone Segment Digit Count (CRITICAL)

`wa.me` accepts ONLY digits — no `+`, no spaces, no dashes. A doubled, dropped, or space-to-zero-converted digit is the most common way to silently break a "send via WhatsApp" workflow.

| Country | Format | wa.me segment | Digit count |
|---|---|---|---|
| India | `+91 94497 84569` | `919449784569` | 12 (91 + 10) |
| US | `+1 415 555 1234` | `14155551234` | 11 (1 + 10) |
| UK | `+44 7700 900123` | `447700900123` | 13 (44 + 11) |

**Bug the user caught in practice (Jul 2026, KDR pre-op):** A trailing `9` was double-encoded into `wa.me/9194497845699` (13 digits). The HTML page worked mechanically but every button failed with "phone number not on WhatsApp". The user had to ask me to re-verify against both the Haldipur letterhead (circled, needed 300 DPI re-OCR) and the Google Contacts entry to find the correct 12-digit segment.

### Pitfall — Space-to-Zero Digit Conversion (CRITICAL, Jul 2026)

When passing a phone number to `whatsapp_link`, a **space between digit groups** in the source data can be mistaken for or converted to `0` instead of being stripped. This silently produces a 13-digit wa.me segment for Indian numbers.

**Example from this session (Sunny Sadhwani, Jul 2026):**

| Step | What happened | wa.me segment |
|---|---|---|
| Contacts sheet shows | `+91 98450 70013` | — |
| **Correct** | strip all spaces: `919845070013` | **12 digits ✅** |
| **Wrong** | space converted to 0: `9198450**0**70013` | **13 digits ❌** |

The contacts sheet stores numbers with formatted spaces (e.g. `+91 98450 70013`). When copying the number into a tool call, the space between `98450` and `70013` was unconsciously replaced with `0` instead of removed, creating an 11-digit local number (`98450070013`) that with the `+91` prefix became 13 digits.

**Fix:** When you see a phone number with spaces in contacts data, mentally strip ALL spaces before constructing the argument:
- `+91 98450 70013` → `+919845070013` (NOT `+9198450070013`)
- `+91 94497 84569` → `+919449784569` (NOT `+9194497784569`)

**Pre-delivery verification:** After building any wa.me URL, parse the path segment (after `wa.me/`) and count its digits. If the count doesn't match the country's expected length, the encoding is wrong — fix before delivering. For India, the wa.me segment must be exactly 12 digits (`91` + 10-digit mobile). Any other length means a digit was doubled, dropped, or a space was turned into a digit.

### Pitfall — Hash/Pound (#) and Ampersand (&) in WhatsApp Message Text (CRITICAL, Jul 2026)

**Even when URL-encoded by the `whatsapp_link` tool, `#` and `&` characters in the message text can break the wa.me link on WhatsApp mobile.** The tool properly encodes `#` as `%23` and `&` as `%26` in the URL parameter, but WhatsApp's mobile client may still fail to render or send the pre-filled message when these characters are present.

**Real failure (Jul 2026):** A message containing `#750` (e.g., "PO-WO item (#750 — AM Office Solutions)") was properly URL-encoded as `%23750` in the wa.me URL. When the user tapped the link on their phone, WhatsApp opened but the message was garbled or failed to pre-fill. The user had to request a regenerated link without the `#` character.

**Rule:** When composing message text for `whatsapp_link`:
- **Avoid `#` entirely** in the message body — it's the most common breaker
- Avoid bare `&` in embedded URLs — if a URL has query parameters (e.g. `?key=val&page=2`), shorten it or use a link shortener
- Test messages that contain `#`, `&`, `?`, or `=` by generating the link and manually reviewing the encoded URL before delivering

**Fix when you cannot avoid these characters:**
1. Remove or rephrase to eliminate `#` (e.g. `#750` → `item 750`)
2. For embedded URLs with query strings, pass a cleaned/redirect URL or just the base domain with context in the prose
3. The `whatsapp_link` tool itself is the correct tool — the issue is the TEXT CONTENT, not the tool choice

**Pre-delivery check:** Before presenting a wa.me link to the user, scan the raw `text` parameter for `#` or bare `&`. If present, rewrite to remove them and regenerate.

### Pitfall — Hash/Pound (#) and Ampersand (&) in WhatsApp Message Text (CRITICAL, Jul 2026)

**Even when URL-encoded by the `whatsapp_link` tool, `#` and `&` characters in the message text can break the wa.me link on WhatsApp mobile.** The tool properly encodes `#` as `%23` and `&` as `%26` in the URL parameter, but WhatsApp's mobile client may still fail to render or send the pre-filled message when these characters are present.

**Real failure (Jul 2026):** A message containing `#750` (e.g. "PO-WO item (#750 — AM Office Solutions)") was properly URL-encoded as `%23750` in the wa.me URL. When the user tapped the link on their phone, WhatsApp opened but the message was garbled or failed to pre-fill. The user had to request a regenerated link without the `#` character.

**Rule:** When composing message text for `whatsapp_link`:
- **Avoid `#` entirely** in the message body — it is the most common breaker
- Avoid bare `&` in embedded URLs — if a URL has query parameters (e.g. `?key=val&page=2`), shorten it or use a link shortener
- Test messages that contain `#`, `&`, `?`, or `=` by generating the link and manually reviewing the encoded URL before delivering

**Fix when you cannot avoid these characters:**
1. Remove or rephrase to eliminate `#` (e.g. `#750` → `item 750`)
2. For embedded URLs with query strings, pass a cleaned/redirect URL or just the base domain with context in the prose
3. The `whatsapp_link` tool itself is the correct tool — the issue is the TEXT CONTENT, not the tool choice

**Pre-delivery check:** Before presenting a wa.me link to the user, scan the raw `text` parameter for `#` or bare `&`. If present, rewrite to remove them and regenerate.

### Pitfall — Two-Source Phone Verification Protocol (CRITICAL)

When a phone number is given by the user (in voice or text) OR is being reused from a non-OCR source, **always cross-check from TWO independent sources before generating any wa.me URL**:

1. **The document where the number physically appears** (letterhead, prescription, business card, ID card). If the number is hand-circled or hand-annotated, re-render the page at 300 DPI and vision-OCR it — circled digits are commonly absorbed into the adjacent digit by OCR (e.g. `9449784569` with a circle around the `9` comes out as `944978456` and the `9` is lost).
2. **A live lookup source** — Google Contacts (People API) OR the NDR DRAAS contacts sheet (col 28 for `Phone 1 - Value`, or any other `Phone N - Value` column with `Phone N - Label` = `Mobile` / `Work`).

If both sources agree, the number is confirmed. If they disagree, the live source wins and you should flag the discrepancy to the user.

**Session-validated examples (Jul 2026, KDR pre-op workflow):**
- Sridhar: letterhead circled `9449784569` + Google Contacts `+91 9449784569` → wa.me `919449784569` ✅
- Charan: contacts sheet row 717 `+91 98452 52011` + user-given `+919845252011` → wa.me `919845252011` ✅ (voice said "Chetan" but the number itself was correct; the NAME was the voice-to-text error)

**When the user replies that a number is wrong:** Do not blindly re-encode. Re-run the two-source verification (re-OCR the letterhead, re-search contacts), present both sources' raw values, and let the user confirm before regenerating. The "wrong" number from the user's perspective often means the NAME on the message is wrong, not the number — distinguish by asking or by re-reading the user's complaint.

### Pitfall — Stale Memory Entries

The lookup order lists memory as step 4 (last resort), but a common failure mode is treating memory as authoritative. Memory entries can be wrong — they're hand-typed during a session and never synced to the source of truth.

**Before generating any WhatsApp link, always verify the phone number against a live source:**

1. Search the NDR DRAAS Google contacts sheet (resolver) — this is the canonical contact database
2. Cross-reference with Google Contacts (People API)
3. Only use the number from memory if BOTH live sources are unreachable

If the memory entry matches one of the live sources, it's confirmed. If it doesn't, trust the live source and update memory.

**Session evidence (Jun 2026):** Memory had Ravi Vijaysarthy's number as +91 98450 33470. Both the resolver sheet and People API showed +91 99800 84646. The memory entry was wrong — probably from a voice transcription error or a different person's number. Using memory without verification caused a wrong WhatsApp link, user frustration, and an extra round-trip to correct.

## Contacts Sheet Column Map (Complete)

The NDR DRAAS Google contacts sheet has many columns beyond phone numbers. The full column map critical for message addressing:

| Col | Field | Purpose |
|-----|-------|---------|
| 0 | First Name | Primary name. May include nickname in parentheses e.g. "Vinod Kumar Das (Rahul)" |
| 1 | Middle Name | Middle name |
| 2 | Last Name | Last name |
| 8 | Nickname | Google Contacts nickname field (often empty) |
| 10 | Organization Name | Company/org |
| 27 | Phone 1 - Label | Phone 1 label (DRA, Mobile, Work, Home, etc.) |
| 28 | Phone 1 - Value | Phone 1 number |
| 29-38 | Phone 2-6 Label+Value | Additional phone pairs |
| 82 | Alias | **Comma-separated nicknames/aliases** — e.g. "anbu, unbhu" for Anbarasan. Use the first alias (trimmed) when addressing the person in a message. This is the user-preferred addressing name. |

**Critical rule — Use Alias (col 82) for message addressing:**

When composing a message to a contact from the sheet:
1. Check **col 82 (Alias)** first — if non-empty, use the first alias value (trimmed) as the person's name in the message
2. If col 82 is empty, check if the **First Name (col 0)** contains a nickname in parentheses — e.g. "Vinod Kumar Das (Rahul)" → use "Rahul"
3. Fall back to **First Name (col 0)** as-is
4. Always use the sheet-resolved name, never a guess or memory-recall name, when the user says "send a message to [person]"

**Real session example (Jul 2026):** Anbarasan has Alias = "anbu, unbhu" in col 82. Nishant said "send message to Anbarasan, Anbu" — the alias confirmed he should be addressed as "Anbu" in the message.

## Voice Transcription Pitfall — Name Verification Required

Voice-to-text frequently mangles contact names. This session's examples:
- "Raj, Ranjit Rathor" -> **Ranjeeth Rathod** (brother-in-law)
- "Anuras" -> **Piyush** (piyush@draas.com)
- "Unverta" -> garbled, could be **Anbu** or a vendor
- "Ampersand" -> **Ashok** (ashok = A + &?)
- "Shekar as per visiting card pic" -> Visiting card showed **Mushtaq Ahmed (CBRE)**, not Shekar. The user may have been thinking of a different card, or voice mis-transcribed the cardholder's name. Never assume a visiting card image contains the name the user says — if the name and the card don't match, tell the user and ask for clarification.
- "Srinjana" -> **Sinchana Gowda** (sgowda@draas.com, architect). Voice merged "Sinchana" → "Srinjana" (consonant metathesis). Common Indian name pattern where 'nch' vs 'nj' sounds swap in transcription. Resolve by checking DRAAS team roster, email, or project context.
- "Vinay Rera" -> **Vinay T** (Venu and Vinay, Chartered Accountant). The original contact entry had "Rera" as the surname because his office is above the RERA office — someone entered the location label as a name component. When the user says "that name is wrong, here's the real one," treat it as a correction to both the display name AND the org/title fields, not just a spelling fix. Pattern: label-as-name misattribution.
- "Nachiket Gaurav" -> **Nachiketh Gowda** (+918548007007, JDTP land partner for Ranka Northstar). Voice-to-text swapped the consonants: the user's voice said "Nachiketh" but the transcription rendered "Nachiket" (missing the 'h'), and "Gowda" was transcribed as "Gaurav" (phonetically similar but a different name entirely). This is a consonant-dropping + name-substitution dual error. Resolve by checking DRAAS contacts sheet for JDTP/land contacts associated with Ranka Northstar — the org/notes context (Assistant ADTP Bangalore North, NOCs for Jakkur Yelahanka Air Force) always identifies the right person.
- **PLACE names get mangled too** — "Alala Sindhra" (voice) = **Allalasandra** (village where Ranka Northstar sits, Yelahanka Hobli). Voice renders "Allalasandra" as "Alala Sindhra" / "Alala Sandra" / "Alalasandra" variants. When a transcribed place doesn't match any known location, cross-check against DRA project locations (Allalasandra, Yelahanka, Jakkur, Puttenahalli, Horamavu, Whitefield, Krishnagiri) before asking the user — Drive folder search usually resolves it instantly.

**Rule:** Always search Drive folder names, email addresses, and existing contacts before trusting a voice-transcribed name. If the transcription doesn't match any known contact OR the visible visiting card, ask the user for clarification rather than guessing.

**New sub-rule (Jun 2026):** When the user says "[Name] as per visiting card pic" and you look at the image but the name they said doesn't appear on any card visible in the image, report the discrepancy immediately. The user may have sent multiple cards in different messages, the wrong image may be referenced, or the voice transcription may have produced a different name. Do NOT silently search for a person who doesn't match the image data.

## Verified Phone Numbers (from memory + cross-reference)

| Contact | DRA/Work | Mobile | Notes |
|---------|----------|--------|-------|
| **Rahul — Vinod Kumar Das** | +91 99000 93813 (DRA) | +91 82770 17221 (Other), +91 97395 43436 (Mobile) | vkdas@draas.com (also c2vdas@gmail.com, vkdas@drahomes.in). Sheet entry literally "Vinod Kumar Das (Rahul)" — voice "Rahul of Vinod Kumar Das" = this person. Succession-certificate / legal follow-ups. Confirmed via People API + sheet Aug 2026. wa.me: `919900093813`. |
| **Nitin Osthwal (Saurabh CA)** | — | +91 80889 79777 | CA handling 281 applications. Stored as "Nitin Osthwal Saurabh CA" in Google Contacts (Saurabh is reference name). Confirmed Jul 2026 via People API. |
| Prakash Singh | +91 99000 93816 | +91 85022 81203 | psingh@draas.com. DRA = 9900093816 (confirmed Jun 2026). Both psingh and 9739932078 were wrong rounds — use 9900093816 for WhatsApp |
| Anbu (Anbarasan) | +91 81500 29900 | — | pm2.blr@draas.com. TG:pm2.blr is NOT a phone |
| Bharat Hawaldar | +91 99000 29200 | +91 83173 20327 | sales1.blr@drahomes.in |
| Piyush Ranka | +91 98441 23300 | — | piyush@draas.com |
| Ashok Kumar | — | +91 97311 66998 | kaajashok@gmail.com |
| Nishant Ranka | — | +91 98800 55634 | ndr@draas.com |
| Pankaj Kumar | — | +91 93790 95455 | pankaj@bluehatsolutions.com |
| Ranjeeth Rathod | drr@drahomes.in | +91 98842 29091 | Brother-in-law. Spelled Ranjeeth Rathod (not "Ranjit Rathor") |
| Aamir Khan | +91 98458 81652 | — | aamirkhan@me.com. Direct LLP |
| Roshini Ranka (Ro) | rnr@draas.com | +91 98450 26390 | Maiden name: Murjani. Nishant's wife. Sometimes called "Roshni Murjani" in voice. NOT roshini@drahomes.in |
| **Kishan Murjani Nair** | kishan@flamebackcapital.com / kishan_99@hotmail.com | +91 98450 20921 | S/o Maya Nair, Roshni's cousin. Labels: RelA. Voice transcription 'Kishan Murjani Nair' merges Murjani (separate family) — actual name in sheet is 'Kishan Nair'. Verified Jul 2026 via People API. |
| **Arjun Murjani Nair** | nair-9@hotmail.com / an67289@gmail.com | +91 98447 67289 | Brother of Kishan. Confirmed Jul 2026 via People API. |
| **Charitra Murjani** | charitra_murjani@yahoo.com | +91 96201 11672 | Single mom, boys Kabir+Zack. Teacher@Presidency 12yr. ASPS patient |
| Charitra Murjani | charitra_murjani@yahoo.com | +91 96201 11672 | Single mom, boys Kabir+Zack. Teacher@Presidency 12yr. ASPS patient |
| C.R. Nagendra | — | (not in contacts) | ABBPN5581H. B-41 Zonasha Paradiso |
| Satvik Developers | — | (use Ashok's number) | ADLFS4825K. sdgroup1516@gmail.com |
| Anwar Fazal | alwaysnew.realty@gmail.com | +91 98440 42680 | Real estate broker. Embassy Habitat 914 deal. Husband of Somaya/Sumaya. |
| Sumaya Anwar | — | +91 98447 91842 | Wife of Anwar Fazal. Listed as "Sumaya Anwar" in contacts sheet. |
| Ravi Vijaysarthy (Ravi Vijay Sarthi) | +91 80 23367588 | +91 99800 84646 | ALS bedridden. Son Rahul (+91 98455 26765). Email: rvgroup89@gmail.com |
| Bhuvanesh S Krishnan | bk@findingform.design | +91 86677 69108 | Design Form — architect/designer for DRAAS projects (Riverstone, interiors) |
| Sinchana L Gowda | sgowda@draas.com | +91 9008720170 | Architect — Riverstone & architectural. Voice variant: "Srinjana" → Sinchana |
| **Sridhar** (Dr. Deepak V. Haldipur's op coordinator) | — | +91 94497 84569 | Trustwell Hospital, J.C. Road, Bangalore — Operations Coordinator - Dr. Deepak Haldipur (ENT). wa.me segment: `919449784569` (12 digits, `91`+`9449784569`). Source of truth: circled annotation on Haldipur's consultation advice letterhead + Google Contacts entry added 9 Jul 2026. NOTE: when extracted via vision OCR at 300 DPI the circled `9` may be lost and the number comes out as `944978456` — always cross-check against the Google Contacts entry. Never double the trailing digit. |
| **Charan** (Dr. Deepak V. Haldipur's insurance coordinator) | — | +91 98452 52011 | Trustwell Hospital Insurance Desk — Insurance Coordinator. wa.me segment: `919845252011` (12 digits, `91`+`9845252011`). Referred by Sridhar (9 Jul 2026). Voice variants: "Chetan" / "Charan" — always cross-check against the contacts sheet (row 717 in NDR DRAAS Google contacts). Spelled **Charan**, NOT Chetan — voice-to-text swaps `r`/`t` in Indian speech. |
| **Nishant Prakash** | — | +91 99996 73483 | nishantprakash@theyelloweye.com, nishantprakash@me.com, nishantprakash1@gmail.com. Address: #001 Raheja Plaza, Commissariat Rd, Bangalore 560025. Verified via contacts sheet row 2316 + People API. Century Regalia contact. |
| **Sunny Sadhwani** (Ritesh Sadhwani) | — | +91 98450 70013 | rsadhwani13@gmail.com. Real name Ritesh Sadhwani, Sunny is nickname. Verified via contacts sheet row 3690 + People API. Landline: +91 80 41329366. CENTURY REGALIA CONTACT NOTE: Number is stored as `+91 98450 70013` in contacts — when encoding for wa.me, use `919845070013` (strip spaces, NOT convert to 0). |
| **Sunder Padmanabhan** (Ranka Northstar landowner, Site 4) | +91 98204 35939 (Wapp) | +91 93226 50429 (Mobile) | sunderp_2002@hotmail.com. Also Home: +91 22 25216549 (Mumbai landline). Label "Wapp" in contacts sheet = WhatsApp-preferred. Mobile label also present. Verified via contacts sheet row range A:AM (Cols 28=Mobile, 30=Home, 32=Wapp), Jul 2026. wa.me for WhatsApp: `919820435939` (12 digits). |
| **Ritesh Sadhwani** (Sunny Sadhwani) | — | +91 98450 70013 | rsadhwani13@gmail.com. Real name Ritesh Sadhwani, Sunny is nickname. Verified via contacts sheet row 3690 + People API. Landline: +91 80 41329366. CENTURY REGALIA CONTACT NOTE: Number is stored as `+91 98450 70013` in contacts — when encoding for wa.me, use `919845070013` (strip spaces, NOT convert to 0). |
| **Sunder Padmanabhan** (Ranka Northstar landowner, Site 4) | +91 98204 35939 (Wapp) | +91 93226 50429 (Mobile) | sunderp_2002@hotmail.com. Also Home: +91 22 25216549 (Mumbai landline). Label "Wapp" in contacts sheet = WhatsApp-preferred. Mobile label also present. Verified via contacts sheet row range A:AM (Cols 28=Mobile, 30=Home, 32=Wapp), Jul 2026. wa.me for WhatsApp: `919820435939` (12 digits). |
| **Jitu Virwani** (Chairman, Embassy Group) | +91 98440 65000 | — | jitu@embassyindia.com. Confirmed via People API (Jun+Jul 2026). Senior business figure — always use Register B tone (Sir, 🙏, deferential). wa.me: `919844065000`. |
| **Eshwari** (Accounts team) | — | +91 81230 28716 | DRAAS accounts team. Stored as "Eshwari Jio" in NDR DRAAS contacts sheet (row 1001, Mobile). SHEET-ONLY contact — NOT in Google Contacts (People API). Verified Jul 2026 via contacts sheet. wa.me: `918123028716`. |\n| **Saurabh CA Ref VK** | — | +91 98864 89873 | CA contact stored as "Saurabh CA Ref VK" in NDR DRAAS contacts sheet (row 3246, Mobile: +919886489873). Different from "Nitin Osthwal (Saurabh CA)" above — these are two separate entries. User refers to this as "Saurabh CA". |\n| **Nachiketh Gowda** (JDTP land partner) | — | +91 85480 07007 | JDTP contact. Verified via NDR DRAAS contacts sheet + People API, Jul 2026. wa.me: `918548007007`. |
| **Khushroo Engineer (KFE)** | — | +91 93437 17070 (WApp), +91 83103 45998 (Mobile) | khushroo@draas.com / khushroo@drahomes.in / kfengineer67@gmail.com. DRAAS tax/accounts (TDS, GST, Income Tax, ROC). Verified via People API Aug 2026 — WApp label = WhatsApp-preferred, use `919343717070`. Not in the contacts sheet row search by "Khushroo" — People API is the reliable source. |
| **Salman Khalid** (Redifice Developers) | +91 98454 32593 (Work) | +91 98455 32593 (Mobile) | salman@redificedevelopers.com. Terra Greens partner. Katenahalli/Riverstone JV. Verified via People API Jul 2026. Two entries: "Salman khalid" (Work) and "Salman Khalid Redifice" (Mobile). Use mobile for WhatsApp. wa.me: `919845532593`. |
| **Vineet Agrawal** (Jiraaf) | — | +91 97390 99290 | Vineet@jiraaf.com. Co-founder of Jiraaf (bond investment platform). Voice-to-text often produces "Vinit Agarwal" and "Jiraffe Capital" — correct name is **Vineet Agrawal**, company is **Jiraaf**. Verified via NDR DRAAS contacts sheet row 4073 + People API, Jul 2026. wa.me: `9197399099290`. |

### Pitfall — Sheet Range Must Include Phone Value Columns (A:AC minimum)

When querying the NDR DRAAS Google contacts sheet via `sheets_get`, the range you pass determines which columns are returned. **The phone columns start at Col 27 (Phone 1 - Label) and Col 28 (Phone 1 - Value).** Using an insufficient range silently drops phone values.

| Range | Cols Included | Covers | Misses |
|-------|--------------|--------|--------|
| `A:Z` | 0–25 | Names + emails | ALL phone columns (27+) |
| `A:AB` | 0–27 | Names + Phone 1 **Label** | Phone 1 **Value** (Col 28) + all other phone values |
| `A:AC` | 0–28 | Names + Phone 1 Label + **Value** | Phone 2–6 values |
| `A:AM` | 0–38 | Names + ALL 6 phone pairs (Cols 27–38) | Addresses + custom fields |
| `A:ZZ` | 0+ | Everything | — |

**Real failure (Jul 2026, Sunder Padmanabhan):** 
- First query with `range="A:Z"` → no phone columns returned at all
- Second query with `range="A:AB"` → shows `Col 27: Phone 1 - Label = Mobile` but **Col 28 is absent** — the label appears but the value is not in the range
- Third query with `range="A:AC"` → `Col 28: Phone 1 - Value = +919322650429` finally visible

**Rule:** Always pass `range="A:AC"` at minimum when looking for phone numbers. For full contact completeness, use `range="A:AM"` to capture all 6 phone pairs. Do not trust a phone label (Col 27) as evidence a number exists — the value may be in Col 28 which requires range `A:AC` or wider.

### Pitfall — Label Set But Phone Value Column Empty

**Critical:** When searching the NDR DRAAS Google contacts sheet (ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`), a contact may have a **Phone Label** (Col 27 = "Phone 1 - Label", e.g. "Mobile") but the **Phone Value** (Col 28 = "Phone 1 - Value") may be **empty**. Having a label does NOT mean a number is stored.

**Real example:** When searching the contacts sheet for a new contact, a phone label with no value in the adjacent value column means the label was created (dropdown selected) but no number was ever typed in. The `Phone 1 - Label` showing "Mobile" with `Phone 1 - Value` being blank is the most common occurrence. Don't assume a number exists just because the label column is filled.

**Phone column map in the NDR DRAAS Google contacts sheet:**

| Col | Label | Value |
|-----|-------|-------|
| 27 | Phone 1 - Label |   |
| 28 | Phone 1 - Value |   |
| 29 | Phone 2 - Label |   |
| 30 | Phone 2 - Value |   |
| 31 | Phone 3 - Label |   |
| 32 | Phone 3 - Value |   |
| 33 | Phone 4 - Label |   |
| 34 | Phone 4 - Value |   |
| 35 | Phone 5 - Label |   |
| 36 | Phone 5 - Value |   |
| 37 | Phone 6 - Label |   |
| 38 | Phone 6 - Value |   |
| 82 | Alias | Comma-separated nicknames. E.g. "anbu, unbhu" for Anbarasan. **Use first alias when addressing the contact in a message.** |

When iterating the sheet rows to find a contact's phone, iterate ALL 6 phone pairs (cols 27-38) and report every label-value pair where VALUE is non-empty. Do not stop at the first label-found pair.

## Contacts Sheet Access — SA Key Unavailable Fallback

**Problem:** The contacts sheet (ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`) is normally accessed via `tools.gws_sa.build_service("sheets", "v4", "ndr@draas.com")`. In some execution contexts (execute_code sandbox, certain cron runners), the `GOOGLE_SA_KEY` environment variable may not be set, causing `gws_sa.build_service` to fail with `KeyError: 'GOOGLE_SA_KEY'`.

**Fix — use OAuth (gws_auth) instead:**

```python
import os, sys
sys.path.insert(0, '/opt/hermes')
os.environ['HERMES_SESSION_USER_ID'] = 'ndr'  # Nishant's Telegram ID
from tools.gws_auth import build_service
sheets = build_service("sheets", "v4")
SHEET_ID = '1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g'
result = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range="'NDR DRAAS Google contacts.csv'"
).execute()
```

**Key details:**
- Sheet name within the spreadsheet: `NDR DRAAS Google contacts.csv`
- Phone number columns: 27-38 (Phone 1 Label at col 27, Phone 1 Value at col 28, etc.)
- Name columns: 0-10 (First Name at col 0, Middle Name at col 1, Last Name at col 2, etc.)
- Row 1 is the header with column labels
- Total rows: ~4200+ as of June 2026
- Row data is 0-indexed: Row 0 = header, Row 1 = first contact entry

## People API Limitations

The Google People API `searchContacts()` method has important constraints:
- **Only searches "My Contacts"** — contacts saved under "Other Contacts" are NOT included in results
- **`searchContacts()` returns empty string** if no match is found in My Contacts — this does NOT mean the contact doesn't exist, it may be in Other Contacts or saved only on the user's phone (not synced to Google)
- **`otherContacts().search()` requires different OAuth scopes** and may return `403 ACCESS_TOKEN_SCOPE_INSUFFICIENT`
- **`connections().list()` with `resourceName='people/me'`** returns 0 connections if contacts are stored in "Other Contacts" rather than "My Contacts" — this is a Gmail contacts storage design, not an API bug

**Workaround:** If People API returns no results for a known contact, check:
1. The NDR DRAAS Google contacts sheet for the person's phone/email
2. Memory for previously saved contact info
3. Gmail search for email threads from that person (their email will be in the From header)
4. Just ask the user for the number — faster than guessing

### Pitfall — Phone-added contacts land in google-ahfl; scan ALL 3 accounts (Aug 2026)

When the user says "I just added a contact on my phone", the fresh contact
syncs under the **google-ahfl** account, NOT google-draas — `searchContacts()`
on google-draas returns empty. Confirmed live (Ketan Vyas, Aug 2026): found at
`people/c6345992331010789330` only under google-ahfl. New phone-added contacts
may also have no `type` on their phoneNumbers and no biography yet.

**Search pattern that works — loop all three accounts with `connections().list`:**

```python
for svc in ['google-draas', 'google-ahfl', 'google-gmail']:
    people = build_service('people', 'v1', service_name=svc)
    token = None
    while True:
        resp = people.people().connections().list(
            resourceName='people/me', pageSize=200,
            personFields='names,phoneNumbers,emailAddresses,biographies,organizations',
            pageToken=token or '').execute()
        for p in resp.get('connections', []):
            name = (p.get('names') or [{}])[0].get('displayName', '')
            if 'ketan' in name.lower() or 'vyas' in name.lower():
                ...  # fuzzy match, collect
        token = resp.get('nextPageToken')
        if not token: break
```

`otherContacts().search()` returns 403 (`ACCESS_TOKEN_SCOPE_INSUFFICIENT`) with
the gws token — don't rely on it.

**Update rule:** update the Google Contacts entry via the account where the
contact lives (`service_name='google-ahfl'` for phone-added contacts), but keep
writing the registry sheet with `service_name='google-draas'` (sheet owner). The
two writes are on different accounts in this scenario — don't assume the contact
is in the same account as the sheet.

**People API `updateContact` — `formatted` is output-only (Aug 2026):**
when adding an address, do NOT include `'formatted'` in the `addresses[]`
payload — Google rejects with `HttpError 400 Unknown name "formatted" at
'person.addresses[0]'`. Send only the component fields (`streetAddress`, `city`,
`region`, `postalCode`, `country`, `type`) and read back `formattedValue` to
verify. Confirmed live on the Ketan Vyas work-address update.

## Contact Creation — Dual Flow

When the user gives you a new contact's details (name, email, phone, company), you must add them to **both** Google Contacts (People API) **and** the NDR DRAAS contacts sheet. These stores are independent — adding to one does not sync to the other.

See `references/contact-creation-dual-flow.md` for the complete workflow, column layout, code snippets, and pitfalls.

## Contact Update — Dual Flow

When the user corrects or enriches an existing contact (name was wrong, address needs adding, org/title need updating), update **both** Google Contacts and the sheet. The update flow differs from creation:

- **Google Contacts:** `updateContact()` requires the resourceName and a current `etag` — always fetch the existing contact first
- **Sheet:** `batchUpdate()` with cell-level ranges (not `append()`) — address fields map to columns AN–AU
- Common scenario: user provides corrected name + additional details after reviewing the existing entry

See `references/contact-update-dual-flow.md` for the complete workflow, People API update parameters, sheet column map, and session example.

### Phone Labels & Profile Photos

- **People API phone labels are enum-only.** `PhoneNumber` has NO `customType` field — sending `{'type': 'custom', 'customType': 'IND'}` fails with `HttpError 400 ... Unknown name "customType" at 'person.phone_numbers[0]'`. Google Contacts can only store standard types (`mobile`, `work`, `home`, `homeFax`, ...). Free-text labels like `USA` / `IND` are only possible in the contacts sheet (cols 27-38 are free text). When the user asks for custom phone labels: set standard types in Google Contacts, put the custom labels in the sheet, and tell the user about the asymmetry.
- **Profile photos:** `updateContactPhoto(resourceName=..., body={'photoBytes': <base64>})` returns a SPARSE response (`resourceName: None`, `photos: None` often) — do NOT treat that as failure. Verify by re-fetching the contact and comparing the photo `url`; a changed URL means the photo was replaced.
- **Extracting a contact avatar from a phone screenshot** works without a vision model: PIL pixel-scan finds the circle (white corners + photo content center), crop a square, then `updateContactPhoto`. Phone numbers on the same screenshot read cleanly via `tesseract <img> stdout`.

Full recipes and code: `references/contact-phone-label-and-photo.md`.

## Consolidated Contact Dossier — Find All Contacts for a Person/Entity

When the user asks for "all contacts related to [doctor/hospital/company]", do NOT just look up one person. Search ALL sources (People API x3 accounts, contacts sheet, Gmail) for the primary name AND associated entities. Compile every coordinator, assistant, insurance desk, and hospital contact into a clean WhatsApp-copyable markdown block.

See `references/consolidated-contact-dossier.md` for the complete protocol: search steps, output format, technical approach, and session example.
