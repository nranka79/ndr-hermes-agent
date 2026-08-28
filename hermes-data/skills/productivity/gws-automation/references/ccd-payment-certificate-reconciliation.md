# CCD Payment-to-Certificate Reconciliation Workflow

Pattern for tracing Compulsory Convertible Debenture (CCD) investments — who paid what, which tranches were allotted, and which physical certificates exist vs. are missing.

## When to use this

- User asks "what did we invest in / what CCDs do we hold / which certificates have we received"
- User provides a garbled company name (likely a voice-transcription artifact) — check Gmail for near-matches first
- Task involves chasing a paper trail across multiple emails, attachments, and Drive files

## Step-by-step workflow

### 1. Identify the correct entity name

Voice transcriptions of company names are unreliable. When searching:
- Search Gmail with the garbled name first
- If nothing found, try splitting into plausible syllables (e.g. "Borg-mana-tex-worth" → "Bagmane Texworth")
- Use `from:` filters targeting known senders (Vishwas Rao, Bagmane Group CS)
- Check subject-line fragments for domain-specific terms like "RLDA", "lease premium", "CCD ALLOTMENT"

### 2. Find the payment trail in Gmail

```python
gmail = build_service('gmail', 'v1', telegram_id=USER_TG_ID)

# Search for payment-related threads
results = gmail.users().messages().list(
    userId='me', 
    q='from:vishwas@domain "lease premium" or "CCD"',
    maxResults=20
).execute()
```

Key senders to check:
- **Vishwas Rao** (vantagepointadvisors.in) — deal advisor, sends payment workings
- **Venkatesh Iyer** (bagmanegroup.com) — company secretary, sends allotment letters
- **Bagmane Group CS** — resolution documents, PAS-4 offer letters

### 3. Extract full thread content (not just metadata)

Forwarded emails often lose table formatting. Get the `format='full'` message:

```python
msg = gmail.users().messages().get(userId='me', id=MSG_ID, format='full').execute()
```

Extract text from nested MIME parts recursively — forwarded messages are nested inside `multipart/alternative` or `multipart/mixed`.

### 4. Download attachments from forwarded emails

Attachment data is NOT in the message body — it comes from a separate API call:

```python
# Find attachment parts
def find_attachments(part):
    atts = []
    if part.get('filename') and part['filename'] and 'attachmentId' in part.get('body', {}):
        atts.append({
            'filename': part['filename'],
            'attachmentId': part['body']['attachmentId'],
            'size': part['body'].get('size', 0)
        })
    if 'parts' in part:
        for sub in part['parts']:
            atts += find_attachments(sub)
    return atts

# Download each one
for a in find_attachments(msg['payload']):
    att = gmail.users().messages().attachments().get(
        userId='me', 
        messageId=MSG_ID, 
        id=a['attachmentId']
    ).execute()
    data = base64.urlsafe_b64decode(att['data'])
    # Save or process
```

**Pitfall:** The `msg['payload']['body']['data']` for attachments with `attachmentId` is usually empty. You MUST call `attachments().get()` with the attachmentId.

### 5. Search Drive for related documents

```python
drive = build_service('drive', 'v3', telegram_id=USER_TG_ID)

# Search with multiple term combinations
queries = [
    "name contains 'Bagmane' or name contains 'Texworth'",
    "fullText contains 'CCD' and fullText contains 'ROMA'",
    "name contains 'certificate' and (name contains 'Bagmane' or name contains 'CCD')",
]
```

Look for:
- **CCD certificate PDFs** — named like `20240511 CCD ROMA Bagmane Textworth Certificate 5&9.pdf`
- **Payment spreadsheets** — `RLDA Payment Details and Timelines.xlsx`
- **CCD infusion details** — `RLDA BLR CNT Bagmane Texworth Group proposed equity and debt CCD infusion details`
- **Research summaries** — Google Docs titled with "CCD & Investor Terms Summary"

### 6. Read Google Docs via Docs API

```python
docs = build_service('docs', 'v1', telegram_id=USER_TG_ID)
doc = docs.documents().get(documentId=DOC_ID).execute()
full_text = ""
for elem in doc.get('body', {}).get('content', []):
    if 'paragraph' in elem:
        for run in elem['paragraph'].get('elements', []):
            if 'textRun' in run:
                full_text += run['textRun'].get('content', '')
```

### 7. Cross-reference payments with certificates

Build a table:

| Tranche | Lease Premium Instalment | Payment Date | CCD Allotment Date | Amount | Certificate Issued? | Certificate No. |
|---------|-------------------------|-------------|-------------------|--------|-------------------|----------------|
| 1st | T1 | Nov 2023 | 24-Nov-23 | ₹X | Yes | #5 |
| 2nd | T2 | Dec 2023 | 20-Dec-23 | ₹X | ? | ? |
| 3rd | T3 (50% paid) | Apr 2025 | 29-Apr-25 | ₹X | ? | ? |

### 8. Common pitfalls

- **Scanned PDFs can't be text-extracted.** Use `pdftotext` first; if it returns only form feeds, the PDF is image-based and needs OCR.
- **Excel files (.xlsx) are not Google Sheets.** The Sheets API only works with native Google Sheets. Use openpyxl or pandas for .xlsx files.
- **Attachment data is NOT in the message body.** Always use the separate `attachments().get()` call with the `attachmentId`.
- **Forwarded emails lose original attachment names.** The attachment filename is on the forwarding message's MIME part, not the original.
- **Certificate file names may encode certificate numbers.** e.g. "Certificate 5&9.pdf" means certificates #5 and #9 are bundled together. If only certain certificates are present, others may be missing.

## Relationship to email discovery pattern

This is a specialized variant of the broader email+document discovery pattern (see `gmail-itr-document-search`, `drive-document-intake-pipeline`). The key differences:
- Focus on **financial instruments** (CCDs) rather than generic documents
- Requires **cross-referencing payment amounts** from emails with certificate PDFs from Drive
- Involves **verifying physical certificate delivery** — not just digital document availability
