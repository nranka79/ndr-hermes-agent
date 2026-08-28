---
name: confirm-before-actions
description: "Critical rule: Always confirm all details with Nishant before sending any message, email, or creating any calendar event. Companion to messaging-drafts umbrella."
version: 1.1
author: Hermes Agent
---

# Confirm Before Actions — Critical Rule

**This is a hard rule set by Nishant (ndr@draas.com). Never violate it.**

Always load this skill when you are about to send a message, email, or create a calendar event. This is the FIRST step in the messaging-drafts decision tree.

## Rule
Before ANY of the following actions, **present a full draft to Nishant and get explicit confirmation**:

1. **Telegram messages** — Show recipient name, full message text. Confirm before sending.
2. **WhatsApp messages** — Show recipient name, phone number, full message text. Confirm before generating link.
3. **Emails** — Show To/Cc/Subject/Body. Confirm before sending.
4. **Calendar events** — Show title, date/time, location, attendee names AND email addresses. Confirm before creating.

## What to confirm
- ✅ Recipient name(s) — exact spelling
- ✅ Phone number(s) / Email address(es)
- ✅ Full message/email body text
- ✅ For calendar: attendee email addresses, date, time, location
- ✅ For email forwards: original sender, forward recipient, ALL CC addresses, which attachment(s) to include, body text
- ✅ For emails with CC lists from voice dictation: confirm EACH CC address individually — voice easily mangles similar-sounding emails
- ✅ For reply-chain handoff emails (writing to person B based on info from person A's reply): show the context — "Person A provided this contact as the manager handling [topic]. Drafting to Person B based on that." Present both the thread context AND the new email draft for confirmation.

## What NOT to do
- ❌ Never send/create anything without Nishant's explicit go-ahead
- ❌ Never assume details are correct — always present them for verification
- ❌ Never use "I'll send this now" without showing the draft first

## Calendar Event — Specific Confirmation Checklist

Before creating any calendar event, present this structured summary and wait for confirmation:

```
Title: [event title]
Date: [day, date, time with timezone]
Location: [venue]
Attendees:
  • [Display Name] — [email address]
  • [Display Name] — [email address]
```

**Pitfall (Jun 2026):** An event was created with "Prakash Singh (psingh@draas.com)" when the user meant "Nishant Prakash (nishantprakash@theyelloweye.com)". Always confirm both the display name AND email of each attendee.

## Voice-Name Nickname / Alias Resolution

When the user dictates a recipient name in voice that doesn't match any contact, they may be using a **nickname** for someone you already know. Examples from this session:
- "Rahul" → Vinod Kumar Das (vkdas@draas.com)
- "Jaiyat Patan Chetty" → Jayanth Pattanshetti & Associates

Before declaring "person not found," check:
- Telegram DM targets list (nicknames used in voice often match Telegram display names)
- Known DRAAS team aliases (save to memory once resolved)
- Ask: "Is [name] a nickname for someone in the team?"

For **Kelsa (CRM vendor) team members**, People API name-search often misses them — query the domain string `kelsa.io` in People API and/or search Gmail `from:<name>@kelsa.io`. Full directory + resolution order: `references/kelsa-team-email-resolution.md` (e.g. voice "Agne" → Aagney Singh aagney@kelsa.io; "Pawan Kumar" → S Pavan Kumar pavan@kelsa.io).

## Phone Number from Email Signatures — Always Verify

When generating a WhatsApp link using a phone number extracted from someone's email signature, **always confirm the number with Nishant before sharing the link.** Email signature numbers may be outdated, wrong, or belong to a different person.

## Drive File Sharing — Confirm Share Settings Before Applying

Before sharing any Drive file with external or internal users, **present the full share plan** to Nishant for confirmation:

**What to present:**
- File name and link
- Each recipient: name, email, role (viewer/editor/commenter)
- Whether domain-wide access will be added or removed
- Current permissions (before change) + intended permissions (after change)

**Session evidence (Jun 2026):**
- Shared Eshwari (echamundeshwari@draas.com) as Viewer on 3 Ranka Amber docs → removed domain-wide Writer access first, added her as explicit Reader. Confirmed before applying.
- Shared CFS projection with Manish (mdr@draas.com) and Dharmesh (dharmesh.ranka@gmail.com) as Viewer only. Confirmed share settings + email draft together.

**Workflow:**
1. Check current permissions on the file via Drive API
2. Present: "File: [name], Current: [permissions], Plan: Add [X] as [role], Remove domain access [Y/N]"
3. Wait for Nishant's go-ahead
4. Apply permissions, then verify and report final state

## Document/Data Edit Confirmation — Confirm Before Applying Changes

Before editing or updating any document, spreadsheet, or data record (Google Docs, .docx, Sheets, Drive files), **present the proposed changes first and get explicit confirmation before applying them.**

This is separate from message/email sending — it covers workspace edits.

**What to present:**
- Current state (what the doc/data says now)
- Proposed change (what you'll change it to)
- For structured changes (tables, rows, columns): show the before/after in a clear format (table or diff-style view)
- For numerical/financial data: show the calculation or source of each proposed value

**When this applies:**
- ✅ Updating cost figures in a financial document
- ✅ Adding/removing rows or columns in a table
- ✅ Changing dates, names, or amounts in a letter or agreement
- ✅ Restructuring document sections or content
- ❌ NOT needed for simple find-and-replace of obvious typos or the user's own dictated corrections (use judgment)

### Statutory forms with unknown fields — fill known, flag unknowns (Aug 2026)

When filling a legal/statutory form (MGT-11 proxy, consent forms, applications) where some
fields aren't in the user's data (registered address, folio no., share folio):
- Fill every field you can source from the actual documents (shareholding from the notice
  PDF, email, name) — do NOT guess or invent the unknowns.
- Leave unknown fields visibly blank (underscored lines in the PDF) and flag them in the
  delivery message: "Registered address left blank — want me to add it, or leave for her?"
- Do not block the whole deliverable on the unknowns; ship the filled form + the flag.
- Data must come from the document at hand (AGM notice shareholding table), never from
  memory of another company's numbers.

### Drive Sharing Pre-Send Check (Jul 2026)

**When sending an email that contains links to multiple Drive files,** add a pre-send verification step:

1. **List every file** referenced in the email (main document + all supporting files)
2. **Verify** each file has the recipient as a viewer (check permissions before send, not after)
3. **Set 1-month expiry** on the recipient's access permission
4. **Remove unnecessary existing viewers** if the user asked to lock down access
5. **Only then send** the email with clickable links

**Trigger phrases that require this check:** "please give him viewer access on all those files", "send the fresh email", "make sure he has viewer access" when the email references Drive files.

**Why:** Sending the email first without setting permissions forces a corrective follow-up round. The user explicitly corrected this in Jul 2026.

**Session evidence (Jun 2026):** Prakash Singh directed: *"please confirm all data you are adding / updating before applying"* during a Means of Finance letter update session. The document had multiple interrelated figures (land cost, construction cost, source of funds) that needed to balance — presenting the proposed restructure first let him verify the numbers before they were committed.

**Workflow:**
1. Read the current state
2. Determine the proposed changes
3. Present both in a structured comparison (table format preferred)
4. Wait for user go-ahead
5. Execute the changes
6. Verify and report final state

### Source spreadsheet read-only + copy-not-original for legal documents (Aug 2026)

When the user shares a payment tracker/spreadsheet as the DATA SOURCE for filling
a legal document (e.g. reconstitution deed partner schedule):

- NEVER modify the source spreadsheet, even to tidy data — treat it as read-only.
  Extract what you need, edit only the target document.
- For legal documents, do NOT edit the original file in place: build an updated
  COPY (new filename with date suffix), upload it as a new Drive file, and leave
  the original untouched. Report what changed plus every assumption/flag.
- When source data disagrees with the document's draft (plots reassigned, more
  or fewer rows than placeholders, multiple payers per plot), present the
  mapping + mismatch options and get ONE structural decision from the user, then
  execute fully. Correcting every mismatch silently is worse than one confirm.

## Search/Query Result Transparency

When Nishant asks you to look up contact information or search data sources, and he asks about the results, **show the raw query details**:

**What to show:**
- Which API was called (e.g., Google People API v1, Sheets API v4)
- What method/endpoint was used (e.g., `people().searchContacts()`, `spreadsheets().values().get()`)
- The exact query/parameters
- Result count
- Raw result data

**Session evidence (Jun 2026):** Nishant asked why a contact was "not found" in Google Contacts. When the raw API results were displayed — showing the actual People API query, parameters, and result count — it revealed the contact WAS present (my earlier search had a discrepancy). Showing the raw data let him see exactly what the API returned and trust (or question) the results.

**Session evidence (Jun 2026):** Nilesh Prasar's Kotak Bank email signature read `+91-8095506021` but Nishant confirmed this number was incorrect. The number from an external sender's OWN signature cannot be blindly trusted — it may be a desk line, a deprecated number, or simply wrong in the signature.

**Correct workflow:**
1. Extract phone number from email signature (if that's the only source)
2. Present it to Nishant: "I found [number] from [person]'s email signature — is this the right number?"
3. Only generate the WhatsApp link after Nishant confirms or provides the correct number

## When Confirmation Is NOT Needed (User-Given Complete Text)

When the user provides the **complete verbatim message text** in their own instruction AND uses an action verb ("send it", "write back", "reply saying", "forward this"), you MAY execute directly without presenting a draft for confirmation.

**Trigger pattern:** The user says the exact message content in their voice/text instruction, not a description of what they want drafted. Examples:

- ✅ *"Write back to Manohar: I could not meet Ashwin for the past two days due to scheduling conflicts. Will meet him today or Monday."* → Execute directly (user provided the text)
- ❌ *"Draft an email to Manohar about the meeting status"* → Show draft for confirmation (user described the content, didn't provide it)

**Rationale:** When the user provides the exact text verbatim and says "send it" or "write back", they are already confirming the content by specifying it. Presenting a redundant draft wastes a round-trip and frustrates the user.

**Exception to the exception:** Still confirm recipient email addresses if you're unsure about the exact address (e.g., user said a name but you're guessing the domain).

### Pitfall — "Go ahead" Confirms the Text, Not the Number

When the user says "Go ahead" after approving a message draft, they are confirming the **message text** — not the phone number you plan to send it to. You still need to:

1. Look up the recipient's number from **live sources** (contacts sheet, People API) — not from memory alone
2. Present the number you found: "[Name] — sending to [number] — correct?"
3. Only generate the WhatsApp link after the user confirms the number

**Session evidence (Jun 2026):** User approved a thank-you message draft with "Go ahead." Assistant pulled a stale number from memory (98450 33470) and generated a WhatsApp link to the wrong person. The real number (99800 84646) was correct. The draft text was fine — but the number was wrong, costing a round-trip to correct.

## Exception (Legacy)
- Processing uploaded documents (OCR, read, analyze) — action-first is still fine
- Searching/retrieving information — no confirmation needed

## Related Skills
- `messaging-drafts` — umbrella for all messaging tasks; this skill is the first step in that decision tree