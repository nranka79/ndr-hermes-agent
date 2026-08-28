# Worked Example: DOCX Modification After Comparison (Miller's Road, Jul 17 2026)

Session date: 2026-07-17
Task: After comparing two versions of a lease deed, produce an updated DOCX with cosmetic changes applied and structural definitions restructured.

## Context

The user received a lease deed back from the counterparty with changes marked in red text. After delivering an HTML comparison table and getting the user's approval (via "continue"), we needed to:

1. Accept all cosmetic changes (PAN numbers, names, LESSOR→LESSORS pluralisation)
2. Restructure the Commencement Date definition per the user's instructions
3. Reject commercial changes the user didn't agree with (keep our original language)
4. Deliver a clean, ready-to-send DOCX

## Phase 5 Workflow

### Step 1: Re-download original DOCX

```python
from tools.gws_auth import build_service
import base64, os

gmail = build_service('gmail', 'v1', service_name='google-draas')
msg = gmail.users().messages().get(userId='me', id=MESSAGE_ID, format='full').execute()

def get_attachments(parts):
    files = []
    for part in parts:
        if part.get('filename') and part.get('body', {}).get('attachmentId'):
            att = gmail.users().messages().attachments().get(
                userId='me', messageId=MESSAGE_ID, id=part['body']['attachmentId']
            ).execute()
            files.append((part['filename'], base64.urlsafe_b64decode(att['data'])))
        if 'parts' in part:
            files.extend(get_attachments(part['parts']))
    return files

os.makedirs('/tmp/lease_compare', exist_ok=True)
for fname, data in get_attachments(msg['payload'].get('parts', [])):
    with open(f'/tmp/lease_compare/{fname}', 'wb') as f:
        f.write(data)
```

### Step 2: Apply cosmetic changes (set_para_text pattern)

```python
from docx import Document

doc = Document('/tmp/lease_compare/original.docx')

def set_para_text(idx, new_text):
    para = doc.paragraphs[idx]
    if para.runs:
        para.runs[0].text = new_text
        for run in para.runs[1:]:
            run.text = ''
    else:
        para.add_run(new_text)

# Names + PANs
set_para_text(7, '(1) Mr. M Akber Hussain, PAN: AASPH6349B, holding an undivided 30% share;')
set_para_text(10, '(4) Mrs. Sara Banu Hussain, PAN: ANLPS1653F, holding an undivided 20% share;')

# LESSOR → LESSORS (global)
for idx in [12, 22, 28, 33, 41, 52, 55, 67, 69, 70, 71, 76, 87, 99, 107, 108, 109, 112, 113, 114, 115, 123]:
    t = doc.paragraphs[idx].text
    set_para_text(idx, t.replace('LESSOR', 'LESSORS'))
```

### Step 3: Restructure definitions (Commencement Date pattern)

The user wanted to split the old combined "Commencement Date" into two distinct concepts:

```python
# Before (original combined definition):
# P35: "This Lease Agreement shall commence from the date of execution of this Deed (the "Commencement Date"), subject to a maximum outer limit of Six (6) months..."
# P36: "(i) the date of occupation... or (ii) 6 months... 7 years from the Commencement Date..."

# After (restructured):
set_para_text(35, 'This Lease Agreement shall commence from the date of execution of this Deed (the "Lease Commencement Date").')

set_para_text(36, 'For the purposes of computing all timelines, rent periods, and the Lease Term under this Agreement, the term "Effective Date" shall mean the earlier of: (i) the date the LESSEE takes occupation of the Leased Premises, or (ii) the date falling Six (6) months from the Lease Commencement Date. The lease shall be valid for a period of Seven (7) years from the Effective Date (the "Lease Term"), unless earlier terminated in accordance with the provisions of this Agreement. The LESSORS shall not have the right to terminate this Lease before the expiry of the 7-year period except for LESSEE\'s material breach.')

# Update all rent timeline references
for idx in [42, 43, 44]:  # rent schedule paragraphs
    t = doc.paragraphs[idx].text
    set_para_text(idx, t.replace('from the date of executing and registering this deed', 'from the Lease Commencement Date'))

# Update rent-free period reference
t = doc.paragraphs[37].text
set_para_text(37, t.replace('from the Date of executing and registering this deed', 'from the Lease Commencement Date'))
```

### Step 4: Reject counterparty's commercial changes (preserve our original)

For changes the user rejected, simply **don't apply them** — leave the original paragraph text unchanged. The key changes we preserved:

| Clause | Counterparty Wanted | Our Action |
|--------|-------------------|------------|
| Security Deposit (P60-61) | Rs. 12L GF, Rs. 36L total | Kept our Rs. 6L GF, Rs. 30L total |
| Renewal (P73) | "can request for renew" | Kept "right to renew" |
| Sub-letting (P101) | "+subject to prior approval" | Kept "absolute and unconditional right" |
| Clause 11.3 (P113) | Accidentally deleted entire clause | Kept original statutory charges clause |
| Exit after lock-in (P71) | Added "not eligible for fit-out costs" | Kept our 3-month-notice-only clause |

### Step 5: Fix drafting issues

Several paragraphs had overlapping edits or typos from the counterparty's editing process:

```python
# Fix double word
t = doc.paragraphs[96].text
set_para_text(96, t.replace('subject subject', 'subject'))

# Fix period placement
t = doc.paragraphs[37].text
set_para_text(37, t.replace('Date.(the "Rent-Free Period")', 'Date (the "Rent-Free Period")'))
```

### Step 6: Save and deliver

```python
doc.save('/tmp/lease_compare/20260709_LeaseDeed_v5_UPDATED.docx')

# Verify key paragraphs
doc2 = Document('/tmp/lease_compare/20260709_LeaseDeed_v5_UPDATED.docx')
for idx in [7, 10, 12, 35, 36, 37, 42, 43, 73, 101, 113]:
    print(f"P{idx:03d}: {doc2.paragraphs[idx].text[:150]}")

# Deliver via Telegram
print("MEDIA:/tmp/lease_compare/20260709_LeaseDeed_v5_UPDATED.docx")
```

## Pitfalls Specific to DOCX Modification

1. **Smart quotes break string replacement.** Always `print(repr(para.text[:50]))` first to see what quote characters the document uses. Indian legal docs universally use `'` (RIGHT SINGLE QUOTATION MARK, U+2019) for possessives like "LESSOR's". Match the exact Unicode character in your replacement string.

2. **Removing runs, not clearing them.** Setting `run.text = ''` on subsequent runs (runs[1:]) preserves empty run elements. This is fine — the paragraph renders as the first run's full text. Trying to delete runs can corrupt the XML if other runs reference shared formatting.

3. **Pagination may shift.** Modifying paragraph text changes its length. A short paragraph that was on page 1 might now span two lines and push content to the next page. This is acceptable for a draft — the user's Word app will re-paginate on open.

4. **Tables need cell-level iteration.** Lease deeds often have rent schedules or property descriptions in tables. Use `doc.tables[ti].rows[ri].cells[ci].paragraphs` to find and modify text within table cells — the standard `set_para_text` won't reach them.

5. **File size after modification.** A cosmetic-only DOCX edit typically produces a file 5-10% smaller than the original. If the output is suspiciously large (comparable to the counterparty's bloated version), check that `doc.save()` isn't embedding the counterparty's scan images — load from OUR version, not theirs.
