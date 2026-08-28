# Legal Case Email Thread Tracing

Trace a specific legal case's email thread by case reference number, identify which law firm member has/hasn't responded, and report the latest status. Commonly requested for cases like CMA No. 742/2026, WP No. 20411/2023, etc.

## Trigger

User says something like:
- "Find the email chain for [case number / party name] and check if [person] has responded"
- "I sent an email to [firm] about [matter] — did they reply?"
- "Follow up on the [case name] matter — has there been any update from [lawyer's name]?"

## Stage 1 — Identify the Case and Participants

From the user's voice, identify:
- **Case reference**: CMA No. 742, WP 20411, etc. — use this as the primary search term
- **Law firm / counsel name**: CMS IndusLaw, Ashlar Law, etc.
- **Specific person to check**: "Jee Vivekananda" (G Vivekanand / Vivek G), "Apsaraa", etc.
- **Opposing party**: "Pawan Kumar", "Saveganapalli Land Partners", etc.

The user often garbles names in voice. Known mapping:
| Voice | Actual |
|-------|--------|
| "Jee Vivekananda" | G Vivekanand / Vivek G — vivek.g@cms-induslaw.com |
| "Rite petition" | Writ petition |
| "Indus Law" | CMS IndusLaw (cms-induslaw.com domain) |

## Stage 2 — Search Gmail

Search broadly with the case reference number and party name:

```python
from tools.gws_auth import build_service

gmail = build_service('gmail', 'v1', service_name='google-draas')

# Primary search — case number + party
results = gmail.users().messages().list(
    userId='me',
    q='CMA No. 742 Pawan Kumar',  # adapt per case
    maxResults=10
).execute()
```

If that returns nothing, broaden:
- Search just the case number: `'CMA 742'`
- Search the law firm domain: `'cms-induslaw.com CMA'`
- Search the lawyer name: `'Vivekanand'` or `'vivek.g@'`

## Stage 3 — Map All Messages in the Thread

Find the thread ID from any returned message, then get all messages:

```python
thread = gmail.users().threads().get(
    userId='me', id=THREAD_ID,
    format='metadata',
    metadataHeaders=['From','To','Cc','Subject','Date']
).execute()

for msg in thread['messages']:
    hdrs = {h['name']: h['value'] for h in msg['payload']['headers']}
```

Present a chronological list with sender, date, and subject.

## Stage 4 — Identify Response Status per Participant

For each named participant (e.g. "G Vivekanand", "Apsaraa"):
- Did they send any message in the thread?
- When was their last message?
- Has the user sent a follow-up that went unanswered?

**Common pattern:** The user may have CC'd a senior partner (Vivekanand) but only received a reply from an associate (Apsaraa). Report this distinction clearly:
> "Apsaraa Sridhar (Associate) responded on 10 July with a status update. G Vivekanand (Partner) has not personally responded since 3 June 2026."

## Stage 5 — Extract the Latest Substantive Update

If a response exists, extract the key information from the body:

```python
def extract_plain_text(msg):
    """Walk payload parts to find text/plain body."""
    def _walk(parts):
        for p in parts:
            if p.get('mimeType') == 'text/plain' and p.get('body', {}).get('data'):
                import base64
                return base64.urlsafe_b64decode(
                    p['body']['data'] + '=='
                ).decode('utf-8', errors='replace')
            if 'parts' in p:
                result = _walk(p['parts'])
                if result:
                    return result
        return None

if 'parts' in msg['payload']:
    return _walk(msg['payload']['parts'])
elif msg['payload'].get('body', {}).get('data'):
    import base64
    return base64.urlsafe_b64decode(
        msg['payload']['body']['data'] + '=='
    ).decode('utf-8', errors='replace')
```

Summarise the update concisely — bullet points, one per key fact.

## Stage 6 — Report to User

Format:
1. **Thread found** — subject line, date range, participant list
2. **Response status per person** — who responded, who didn't
3. **Latest substantive update** — bullet points from the last response
4. **Gap / next step** — what's still pending (e.g. "They said they're working on strategy but haven't shared it yet")

## Known Participants (CMS IndusLaw — Saveganapalli/Pawan Kumar matter)

| Role | Name | Email |
|------|------|-------|
| Partner | G Vivekanand (Vivek G) | vivek.g@cms-induslaw.com |
| Associate | Apsaraa Sridhar | apsaraa.sridhar@cms-induslaw.com |

## Pitfalls

### P1. The user says "Jee" but the actual name is "G Vivekanand"

The user pronounces "G Vivekanand" as "Jee Vivekananda" — both the initial "G" (hard to hear) and the spellings differ. Search for both `vivek.g@` and the full name `Vivekanand` across cms-induslaw.com domain.

### P2. Case participants may have moved firms

The engagement may have started with one lawyer at one firm, then shifted to another firm or another lawyer at the same firm. Check multiple threads:
- Thread 1: Initial engagement (e.g. with G Vivekanand in June)
- Thread 2: Active handling (e.g. with Apsaraa in July)

The user's understanding of "who is handling this" may be outdated — the thread will show the actual current handler.

### P3. "Rite petition" = "Writ petition"

The user's voice transcription regularly renders "writ petition" as "rite petition" or "right petition". Always search both.

### P4. Voice says "Echo Green" → actual is "Aqua Green"

The user's voice regularly renders "Aqua" (as in Ranka Aqua Green) as "Echo" or "Aqua Green" → "Echo Green". Always search for both `Aqua` and `Echo` variants when the user references a project name containing "Aqua" via voice memo.

## Stage 7 — Download Attachments from the Latest Email

When the thread contains a new court filing (IA, application, affidavit) as an attachment:

```python
# Find the latest message with an attachment
msg = gmail.users().messages().get(userId='me', id=MSG_ID, format='full').execute()

def find_attachment_part(payload, target_name=None):
    """Walk payload parts to find PDF attachments."""
    if 'parts' in payload:
        for p in payload['parts']:
            fn = p.get('filename', '')
            if fn and p.get('body', {}).get('attachmentId'):
                if not target_name or target_name.lower() in fn.lower():
                    return p
            r = find_attachment_part(p, target_name)
            if r:
                return r
    return None

att_part = find_attachment_part(msg['payload'])
if att_part:
    att_id = att_part['body']['attachmentId']
    fn = att_part['filename']
    attachment = gmail.users().messages().attachments().get(
        userId='me', messageId=MSG_ID, id=att_id).execute()
    data = base64.urlsafe_b64decode(attachment['data'] + '==')
    with open(f'/tmp/{fn}', 'wb') as f:
        f.write(data)
```

Check for PDF attachments in ALL messages, not just the latest — sometimes the attachment email is the second-to-last (forwarded within the thread). Use `format='full'` and walk `parts` recursively.

## Stage 8 — OCR Scanned PDFs

Many court filings are scanned images, not text-layer PDFs:

```bash
# Check page count and if text exists
pdfinfo <file.pdf> | grep Pages
pdftotext <file.pdf> - | head -20  # empty output = scanned

# OCR key pages (first 10 for structure, last 10 for prayer/order)
for p in $(seq 1 10); do
    pdftoppm -f $p -l $p -r 200 -png <file.pdf> /tmp/ocr/page
    tesseract /tmp/ocr/page-$p.png /tmp/ocr/page$p 2>/dev/null
    echo "=== PAGE $p ==="
    cat /tmp/ocr/page$p.txt
done
```

For 92-page-plus documents, OCR the opening pages (title, background, prayer) and the last pages (prayer, affidavits in support). The middle pages are usually annexures/exhibits and can be sampled selectively.

## Stage 9 — Identify the Correct Drive Folder and File

DRAAS litigation documents follow two filing conventions depending on the folder:

| Folder Type | Convention | Example |
|---|---|---|
| **Litigation case folder** (e.g. "RRP vs SPV", OS 553) | Numbered-prefix `NN_Description.pdf` | `32_Orders_IA_No5to7_15Feb2025.pdf` |
| **Consumer Forum Cases / NCDRC folder** (RAQ matters) | YYYYMMDD naming | `20260819_Ranka_Aqua_Green_IA_9783_2026_Complainant_Amendment.pdf` |

**Folder discovery ladder:**
1. Search Drive for the case number: `"CC. No. 1230/2016"` or `"CCNo 1230-2016"`
2. Check under `Legal > Consumer Forum Cases > NCDRC` for NCDRC matters
3. Check under `Current Properties > RAQ > RankaAquagreens > RAQ Legal` for property-level RAQ legal docs
4. For a new IA/application filed at NCDRC, the **NCDRC folder** under Consumer Forum Cases is the correct location

**Document naming for NCDRC filings:**
`YYYYMMDD_Project_IA_No_Year_Description.pdf`
- `20260819_Ranka_Aqua_Green_IA_9783_2026_Complainant_Amendment.pdf`

Upload via Drive API with `MediaFileUpload` and verify the parent chain after upload.

## Stage 10 — Analyze the Legal Document and Draft Strategy Email

After OCR'ing the document, produce a structured analysis covering:

1. **What the opponent is saying** — their claims, arguments, and legal basis
2. **What the court has already observed** — extract from the latest hearing report email (not just the IA)
3. **Our rebuttal positions** — identify the key grounds of attack
4. **Gaps / questions for the advocate** — specific technical legal questions (estoppel, limitation, res judicata, maintainability)

Then draft a threaded email reply to the advocate with:
- **To:** the handling advocate (e.g. Harshavardhan Kotla)
- **CC:** the associate + other counsel on the thread
- **Subject:** `Re: [original subject]` (preserves threading)
- **Body:** structured sections: analysis of the IA, key observations, specific questions on rebuttal strategy, legal pathway, next steps, costs

Build the email as a MIME draft (NEVER send directly):

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

msg = MIMEMultipart('alternative')
msg['To'] = 'Advocate <advocate@lawfirm.com>'
msg['Subject'] = f'Re: {orig_subject}'
msg['In-Reply-To'] = orig_msg_id
msg['References'] = orig_msg_id
msg['Cc'] = 'associate@lawfirm.com, other.counsel@lawfirm.com'
msg.attach(MIMEText(body, 'plain'))

raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
draft = gmail.users().drafts().create(
    userId='me',
    body={'message': {'raw': raw, 'threadId': thread_id}}
).execute()
```

Verify the draft's To/Cc/Subject by reading it back with `drafts().get(format='full')`.

## Pitfalls — Stages 7-10

### P5. The attachment filename from Gmail is often garbage
Gmail attachment filenames often have leading spaces, odd characters, or are truncated (` I.A. 9783:2026pdf.pdf`). Always rename the file to the proper YYYYMMDD convention before uploading to Drive — do NOT use the Gmail filename as-is.

### P6. Scanned PDFs can have blank first pages
Many scanned court filings start with a blank page (the unprinted cover sheet). If OCR returns empty for page 1, check page 2+. The title page may be page 3 onwards.

### P7. The email body (hearing report) is often more insightful than the IA itself
The advocate's covering email (Stage 7) contains the court's oral observations and the actual hearing outcome — it may be more strategically valuable than the IA document. Always extract and read the email body text from the same message AND the previous messages in the thread. The hearing report is typically in the second-to-last message (sent before the IA attachment message).

### P8. Thread is long (25-30+ messages) — read the tail, not the head
For legal threads spanning 2+ years, the key messages are the last 5-10 (latest hearing reports, latest IA filings) and the first 2-3 (original complaint, initial strategy). Middle messages are procedural (affidavit drafts, notary instructions, cost discussions). Don't waste context reading every message.

### P9. NDR prefers concise call-focused strategy emails, not detailed questionnaires
When drafting a legal strategy email to counsel, NDR's preference (corrected Aug 2026 on the Ranka Aqua Green matter) is:
- **Short body** — 2-3 paragraphs: confirm the IA was reviewed, note the key court observation, confirm the IA is filed on Drive, then ask for a call
- **No detailed bullet-point questionnaires** — don't list 10+ specific legal questions in the email body
- **Save the deep dive for the call** — the detailed questions (rebuttal strategy, probability assessment, costs, etc.) should be discussed on the phone, not written into the email
- **Template:** "I reviewed [doc]. Key observation: [one-liner]. Filed on Drive. Would like to get on a call to discuss the plan of action going forward. Kindly let me know a convenient time."

This applies to ALL legal strategy emails to advocates — the email is for scheduling, not for litigating the case in writing.