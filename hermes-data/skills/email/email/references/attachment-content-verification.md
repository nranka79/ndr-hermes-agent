# Attachment Content Verification — "Is this actually a floor plan?"

Class of request: You sent a file (or received one) that claims to be a specific type of document — "floor plan," "brochure," "agreement," etc. — and you need to **verify the file actually matches its claimed type** using vision analysis, then locate the real documents from other sources and organize them properly.

Typical trigger: "The floor plans we attached to the email were not floor plans — they were signature sheets. Vision-analyze them and confirm."

## Why this is distinct from standard email forensics

Regular forensic lookups answer "who was on the email" or "did this go out." This workflow answers "what did we **actually** send" — the actual content vs. the claimed filename/body description. Email bodies can claim attachments that aren't real, and filenames can be wrong or misleading.

## Step 1 — Download the suspect attachment(s)

Use the Gmail API to download the raw attachment bytes:

```python
from tools.gws_auth import build_service
import base64

gmail = build_service('gmail', 'v1', service_name='google-draas')
full = gmail.users().messages().get(userId='me', id=MSG_ID, format='full').execute()

def find_attachment_id(payload, filename):
    if payload.get('filename') == filename and payload['body'].get('attachmentId'):
        return payload['body']['attachmentId']
    for p in payload.get('parts', []):
        result = find_attachment_id(p, filename)
        if result:
            return result
    return None

att_id = find_attachment_id(full['payload'], 'BR_Floorplan_Widespread.pdf')
att_data = gmail.users().messages().attachments().get(
    userId='me', messageId=MSG_ID, id=att_id
).execute()

data = att_data['data']
padding = 4 - (len(data) % 4)
if padding != 4:
    data = data + ('=' * padding)
file_bytes = base64.urlsafe_b64decode(data)

with open('/tmp/suspect.pdf', 'wb') as f:
    f.write(file_bytes)
```

**Pitfall — Gmail attachment base64 padding:** The `data` field may have length % 4 != 0. Always apply the padding fix before decoding.

## Step 2 — Vision-analyze to determine actual content type

For PDFs: convert to images first with pymupdf, then vision-analyze each page:

```python
import pymupdf
doc = pymupdf.open('/tmp/suspect.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(matrix=pymupdf.Matrix(2, 2))
    pix.save(f'/tmp/suspect_page{i+1}.png')
# Then vision_analyze each page with a specific question
```

For images (JPG/PNG): send directly to `vision_analyze`.

Use a specific question like:
> "Describe exactly what this document page shows. Is it a floor plan (architectural layout with rooms, walls, dimensions, labels) or a signature sheet (legal document with 'IN WITNESS WHEREOF', signature lines, names)? Or something else?"

Key indicators to check for:
- **Floor plan**: Room labels with dimensions (BEDROOM 12'x14'), wall lines, door swings, furniture layouts, key plans, scale notations, "FLOOR PLAN" in title
- **Signature sheet**: "IN WITNESS WHEREOF", "WITNESSES:", role labels (VENDOR, PURCHASER, CONFIRMING PARTY), handwritten signatures, agreement page numbers
- **Technical specs**: "Schedule - E", material/finish tables, no room dimensions
- **Brochure**: Promotional text, "Representative image" tag, lifestyle photography, branding

## Step 3 — Cross-reference with other threads for the REAL documents

If the attachment is mislabeled, find the authentic version from an earlier/source thread:

1. **Search by project name + contact** — e.g., `q='to:msingh@redsoul.co.in Century Regalia'` for a different recipient who has the real docs
2. **Check attachment filename patterns** — Real floor plans often have naming conventions like `*_ScheduleD.*` or `*_FloorPlan.*` with unit numbers
3. **Download the real files** from the correct thread
4. **Verify the real files** using the same vision-analyze process — confirm they ARE actually floor plans

## Step 4 — Organize on Drive

1. **Rename mislabeled files** with a clear indicator — e.g., append `_SignaturePage_NotFloorPlan` to the filename
2. **Upload real files** with proper naming convention (YYYYMMDD_Entity_Description)
3. **Create an info note** as a markdown file in the same folder documenting which files were mislabeled and where the real ones are

## Pitfalls

- **Don't trust filenames** — A file named `*_FloorPlan.jpg` can be a signature sheet. Only vision analysis confirms.
- **Same file attached to multiple emails** — The body may claim "floor plans attached" but the actual attachment may be from a different document entirely (e.g., the brochure PDF contains the floor plans but the JPGs in the same email are signature pages from the agreement).
- **Email chains have variant recipients** — The earlier email to a different contact (Manohar Singh) had the real Schedule D floor plans, while the email to the new contact (Ankush Musaddi) had the signature sheets. Always check other threads with related project names.
- **PNG vs JPG encoding** — Real floor plans from the architect were sent as PNG; mislabeled signature sheets arrived as JPG. This isn't deterministic but can be a clue.
- **Inform the user of the full picture** — Don't just flag the error; show what was sent, what the real documents are, and where they've been placed on Drive.
