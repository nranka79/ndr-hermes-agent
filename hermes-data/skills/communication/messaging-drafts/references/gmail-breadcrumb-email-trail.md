# Gmail Breadcrumb Email Trail — Follow Referenced Emails to Find Documents

**Trigger:** The user says "check email from [Person X] — they refer to a [document/list] they sent in an earlier email dated [date]." Or: "[Person] says they sent a list on [date]. Find it."

## Problem

A recent email from Person A references an earlier email they sent on a specific date containing a requisition list, document, or attachment. You need to:
1. Find Person A's recent email
2. Extract the referenced date from it
3. Find the older email from that date
4. Extract the attachment to understand what was asked for

## Workflow (4 phases)

### Phase 1: Find the Recent Email from Person A

Search Gmail using multiple strategies:

```python
# Strategy 1 — direct email search
results = gmail.users().messages().list(
    userId='me',
    q='from:person@domain.com after:2025/06/01',
    maxResults=5
).execute()

# Strategy 2 — name variants (voice transcription mangling)
# Person A may have multiple email aliases or names
results = gmail.users().messages().list(
    userId='me',
    q='person.name OR person.name@ OR domain.com',
    maxResults=10
).execute()

# Strategy 3 — if the person's name was voice-dictated, try phonetic variants
# "Jan Patan Chetty" → "Jayanth Pattanshetti" / "Pattanshetti Law Office"
# "Krishna BR" → "B. R. Krishna" / "krishna@brklaw.in"
```

**Important:** Get the FULL body text (not just metadata) — the referenced date is typically in the body, not the subject line. Use `format='full'` and extract `text/plain` parts.

### Phase 2: Extract the Referenced Email Date

From the email body, look for phrases like:
- "as per our additional list dated **06/11/2025**"
- "sought for vide our additional list dated **06/11/2025**"
- "per my email of **28 October 2025**"
- "further to my earlier communication dated **...**"

Note the exact date format used (DD/MM/YYYY vs MM/DD/YYYY vs DD Month YYYY).

### Phase 3: Find the Referenced Older Email

Search Gmail for emails from the same sender or organization around that date:

```python
# Search by sender + date range
results = gmail.users().messages().list(
    userId='me',
    q='from:person@domain.com after:2025/11/05 before:2025/11/08',
    maxResults=10
).execute()

# If the sender email changed, also search by:
# - Organization domain (pattanshetti.in, brklaw.in)
# - Subject keywords ("requisition", "additional list", "Sy. No. 40")
# - CC recipients from the recent email (they may have been on the original too)
results = gmail.users().messages().list(
    userId='me',
    q='"requisition list" OR "Sy. No. 40" after:2025/10/25 before:2025/11/15',
    maxResults=10
).execute()
```

**Pitfall — different email accounts:** The referenced email may have been sent to a different address (ndr@drahomes.in vs ndr@draas.com). If you're authenticated as one and can't find it, try the other by:
- Searching for forwarded copies in the account you have access to
- Checking if Dharmesh or another family member forwarded it
- Asking the user for context

### Phase 4: Extract and Read Attachments

Once you find the older email, check for attachments:

```python
# Check all parts for filenames
for part in msg['payload'].get('parts', []):
    fn = part.get('filename', '')
    if fn:
        att_id = part['body'].get('attachmentId')
        if att_id:
            att = gmail.users().messages().attachments().get(
                userId='me', messageId=msg_id, id=att_id
            ).execute()
            data = base64.urlsafe_b64decode(att['data'])
```

**Attachment types and how to read them:**

| Type | Ext | How to Read |
|------|-----|-------------|
| Word docx | .docx | Use `python-docx` library (`docx.Document(path)` then `[p.text for p in doc.paragraphs]`) |
| Word doc (old) | .doc | Compiled OLE2 format — cannot extract text easily from Gmail API alone. Try: `antiword`, `catdoc`, `LibreOffice --headless`, or fall back to reading the email body for context clues |
| PDF | .pdf | Download → `pdftotext` or pymupdf |
| Excel | .xlsx/.xls | Use `openpyxl` or `pandas` |
| Image | .jpg/.png | Save → `vision_analyze` |

**Fallback when .doc extraction fails:**
- The email body text itself often contains the key details (property description, what was requested)
- The accompanying email or the more recent email from the same person may clarify what was asked for
- Present what you DO know (from email text + context) to the user, noting that the exact attachment couldn't be parsed

### Real Example (Jun 2026)

**User request:** "Check email from Krishna BR (Jan Patan Chetty office) — he refers to a requisition list he sent in an earlier email dated [date]."

**Execution:**
1. Searched `from:krishna@brklaw.in` → found email from B. R. Krishna dated 10 Jun 2026
2. Body contained: *"documents/clarifications/information/details sought vide our additional list dated **06/11/2025**"*
3. Searched `from:ananya.s@pattanshetti.in after:2025/11/05 before:2025/11/08` → found email "Additional Requisition List" dated 6 Nov 2025
4. Email body described the property (Survey No. 40, Gunjur Village, 18 acres 21 guntas)
5. Attachment: `Sy_No_40_Add_Req_Ltr_AS.doc` (old Word format — binary, couldn't extract text via API)
6. Also found the original Requisition List from 28 Oct 2025 with similar `Sy_No_40_Req_Ltr_AS.doc` attachment
7. Presented findings with:
   - What the recent email asked for (summary from body text)
   - What the attached list referenced (property details from email body)
   - Note that the actual .doc attachment contents couldn't be parsed via API
   - Advised user to open the attachment directly from the email

## Key Principles

1. **Always read the full body** of the recent email first — the referenced date is usually in the body text, not the subject line
2. **Search backwards in time** — from the recent email's date backward to the referenced date
3. **Search broadly** — the older email may have a different subject line or sender email than the recent one
4. **Multiple accounts** — if the older email isn't in the current account, check for forwarded copies or ask the user
5. **Attachment may not be parseable** — old .doc format, password-protected files, or large attachments may not be extractable via Gmail API. Note this clearly to the user rather than spending excessive tool calls trying.
6. **Present the full picture** — even if the attachment can't be read, the email body text + the recent email context usually give enough information for the user to understand what was requested.
