# School "Whom Do I Contact" PDFs — Contact Resolution

## Pattern

User has a school-issued PDF titled "Whom Do I Contact" (or similar) listing contacts by role (Principal, Class Teacher, Counsellor, etc.). User asks to email someone they remember by **a phonetically spelled / partially memorized name**.

## When This Applies

- User says "for my son/daughter [name] at [school]", "whom to contact PDF", "the class teacher is [misspelled name]", etc.
- The contact is on a school "Whom Do I Contact" PDF stored in Drive
- User provides a name with explicit spell-uncertainty: "Ranjita, R-A-N-J-E-T-H-A or R-A-N-J-I-T-H-I will give you typos of both" — a clear "I don't know the exact spelling" signal
- Trigger phrases: "whom to contact", "class teacher", "school contact list", "admission office"

## Workflow

### Step 1 — Drive search for the contact PDF

Known location pattern (Nishant/Ruhi): `Personal/{child_name}/` or root of personal Drive, file named `Whom Do I Contact_<class>_<academic-year>.pdf`. Use both `name contains 'Whom Do I Contact'` AND `fullText contains '<phonetic_name>'` queries to maximize recall.

```python
# Build queries with explicit chr(39) for single quotes — see gws-automation pitfall #6
queries = [
    "name contains " + chr(39) + "Whom Do I Contact" + chr(39),
    "name contains " + chr(39) + "WhomDoIContact" + chr(39),
    "name contains " + chr(39) + "9IGCSE" + chr(39),                # if class known
    "fullText contains " + chr(39) + "Ranjita" + chr(39),          # phonetic variant
    "fullText contains " + chr(39) + "Ranjitha" + chr(39),         # other phonetic variant
]
```

### Step 2 — Download and extract text

```python
# Use pdftotext -layout (always available, handles school PDFs well)
# Fallback to pymupdf if installed in venv
resp = drive.files().get_media(fileId=file_id).execute()
open("/tmp/whom.pdf", "wb").write(resp)
# Then either:
pdftotext -layout /tmp/whom.pdf /tmp/whom.txt
# OR (in /opt/hermes/.venv/bin/python3):
import pymupdf
print(pymupdf.open("/tmp/whom.pdf")[0].get_text())
```

### Step 3 — Surface ALL contacts, not just the one asked about

**CRITICAL pitfall:** School "Whom Do I Contact" PDFs list contacts in a 3-column structure: **Concern | Contact Person | Name & Contact Details**. A single role (e.g. "Classroom Issues → Class Teacher") often has **TWO or more people** co-listed with separate email addresses. The user only remembers one name; they may not know there are two co-teachers.

**Action:** When extracting the asked-for contact, ALWAYS show the full table for that row, so the user can see all co-listed contacts and pick. Don't just answer "here's Ranjitha's email" — show "Class Teacher: Priya Rao + Ranjitha Tikandar" and ask which to address.

## Pitfall: Phonetic / Stub-Spelled Names from Voice Messages

Users who dictate names by voice frequently:
- Drop letters or guess at spellings (Ranjita → could be Ranjitha, Ranjita, Ranjetha, Ranjini, Ranjit)
- Use phonetically-similar wrong names from memory (Ranka Udaya → "Runca Udaya" — already in memory)
- Provide multiple variants explicitly: "R-A-N-J-E-T-H-A or R-A-N-J-I-T-H-I will give you typos of both"

**Workflow response:**
1. **Read the PDF first** before telling the user the spelling is wrong
2. **Do fullText search for ALL plausible variants** in a single pass
3. **Surface the actual spelling(s) found** in the PDF (often the user's "wrong" spelling is close to correct, just off by one vowel)
4. **Never silently correct** — show the PDF's actual spelling so the user can confirm

## Pitfall: Multiple Contacts Per Role

| Role | Co-listed contacts (typical) |
|------|------------------------------|
| Class Teacher | 2 teachers (Priya Rao + Ranjitha Tikandar — Aditi 9-IGCSE 2026-27) |
| Head of Section | 1 person + 1 Deputy |
| Counsellor | 1 Head + 1 separate Child Safety Officer |
| Finance | Head + Department staff |

Always list all co-listed contacts for the role in your reply, and ask the user:
- Send to ALL or pick one?
- Who to CC (parent, child, school admin)?

## Pitfall: User's Child's "School Email" May Not Exist

Nishant mentioned "Peadly shark or something email address he has" for Ruhan — most Indian schools do **NOT** issue student email addresses for primary/secondary. The PDF won't have it. Confirm with user before treating a non-existent email as real. If the school does issue student emails, they usually follow the format `<firstname>.<lastname>@<gsuite-domain>.aditi.edu.in` (or similar Google Workspace tenant) — but verify from the PDF or a recent school communication, not from the user's memory.

## Pitfall: Finding a Personal Email When User Only Has a Fragment

User often remembers their child/spouse/contact's personal email as a fragment — "Peadly shark" / "pebbly shark" / "Pebble shark" — not the full address. Don't ask the user to type it; the value of asking is zero because they already admitted they don't know. Instead:

**Search Gmail correspondence for the fragment.** Multiple query patterns work in parallel:

```python
queries = [
    "from:<fragment>",          # search From: header
    "to:<fragment>",            # search To: header
    "<fragment>",               # full-text body search
    "ruhaan -aditi.edu.in -gsuite.aditi.edu.in",   # name minus school domain
]
```

**Why the third / fourth queries matter:** the school domain dominates results for the child's name. Stripping `-aditi.edu.in` and `-gsuite.aditi.edu.in` from the query surfaces the personal account (Gmail / Outlook / Yahoo) the user is actually asking about.

**Confirmed working example (June 2026, Nishant's Ruhan):**
- User: "his email is something like pebblyshark" + "gmail.com"
- `from:pebblyshark` → 0 results
- `pebblyshark` → 0 results
- `ruhaan -aditi.edu.in -gsuite.aditi.edu.in` → 30 results, second hit was a forwarded travel booking email CC'd to `Ruhaan Ranka <pebblyshark69@gmail.com>`. Confirmed by two other threads (Kannada class invitation Feb 2026, and a Feb 16 Roshni Murjani email).
- Resolved: **pebblyshark69@gmail.com** — save this address. School email (Aditi gsuite) is NOT issued for students; the personal Gmail is the right one to CC.

Gmail search syntax notes:
- `from:` and `to:` are header-only searches (won't match body text)
- Bare word search runs against body, subject, AND headers
- `-` operator negates a term (excludes matching messages)
- Always pass `userId="me"` when calling `users().messages().list()` — the SDK enforces it
- `static_discovery=False` on the `build()` call avoids a runtime cache miss in some environments

## Confirm-Before-Draft Checklist (MUST do before composing email)

After extracting addresses, present this to the user — don't draft yet:

1. **TO field strategy:** "Send to [X] only / Send to all co-listed ([X, Y]) / Send to [X] and CC [Y]?"
2. **CC field:** Confirm Roshini's email from user profile / Sheet (e.g. `rnr@draas.com`) — don't assume
3. **CC student email:** If school issues student emails, confirm exact address; if not, omit
4. **Subject + body:** State the user's intent back (e.g. "informing class teacher that Ruhan will attend the Math exam on 8 June 2026") and confirm any specific wording the user wants
5. **AI disclaimer footer:** Append `*(Sent by AI on behalf of [User's Full Name])*` per `messaging-drafts` "User Preference: Review Before Send" — confirmed format for Nishant Ranka.

## Pre-Send Confirmation Axes (MUST verify before firing the Gmail API)

After the user approves the draft, do NOT just call `users().messages().send()`. Surface the four confirmable axes one more time and wait for the green light. User explicitly stated this workflow: *"prepare the draft, confirm it with me and then we send it out."*

The four axes, each of which the user can override:

1. **Sender account** — which Gmail account sends the email (e.g. `ndr@draas.com`). Auto-detected from session context, but confirm explicitly because multiple identities share the same Google account.
2. **Tone** — formal vs warm. Most school / professional comms default to formal. The user will often say "Tone formal" or "make it warmer" — capture their override and re-draft before sending.
3. **Sign-off** — single name ("Nishant Ranka") vs couple ("Nishant & Roshini Ranka") vs full name + phone + designation. User will specify per-recipient.
4. **Date / fact accuracy** — the user often dictates dates from memory. Echo the date back in the draft and confirm before sending. A wrong exam date is a worse outcome than a 30-second confirmation.

Only after all four are confirmed should the script build the MIME message, call `users().drafts().create()`, and then `users().drafts().send()` (NOT `users().messages().send()` — see the pattern in the "Email — Send" section of the umbrella SKILL.md).

## Session Example (June 2026)

- **User:** Nishant Ranka
- **Asked-for name:** "Ranjita, R-A-N-J-E-T-H-A or R-A-N-J-I-T-H-I" — voice message, phonetic spellings
- **PDF found:** `Whom Do I Contact_9IGCSE_2026-27.pdf` (Drive ID `1Kned8mnIwoRkKuD8wV3jkYiVhY26YTqC`)
- **PDF actual spelling:** Ranjitha Tikandar (not Ranjita)
- **Co-listed class teacher found:** Priya Rao (also listed as class teacher alongside Ranjitha)
- **Pause point:** Asked user to pick (A) send to both, (B) Ranjitha only, (C) Priya only — and to confirm Ruhan's school email (he has one, format unknown) and Roshini's email (rnr@draas.com — verify)

## Related Reference Files

- `references/contacts-lookup.md` — full contact resolution order (Sheet → People API → Drive PDFs)
- `references/drive-pdf-contact-discovery.md` — generic Drive-PDF contact extraction (doctor, dentist)
- `../productivity/gws-automation/SKILL.md` — Drive search pitfalls, OAuth setup, single-quote `q=` trap
- `messaging-drafts/SKILL.md` "User Preference: Review Before Send" — confirm before composing/sending
