# PDF Form Correction from Gmail Attachment — End-to-End Pipeline

When the user discovers a mistake in a PDF form they already filled and sent, the fix requires re-generating from the original blank — the user's filled version is a scanned/image PDF and cannot be edited in-place.

## Trigger

- User: "I put [X] on the form but it should be [Y]"
- User: "Can you change [field] on that PDF I sent?"
- User: "I made a mistake on the form — fix it and give me a new one"

## Full Pipeline

### Step 1: Find the Original Email + PDFs

The filled (wrong) version was usually sent as an attachment in a Gmail reply. The blank original is often in the **same email thread** as a separate attachment from the sender.

```python
from tools.gws_auth import build_service
svc = build_service('gmail', 'v1', service_name='google-draas')

# Search by context keywords
results = svc.users().messages().list(
    userId='me', q='query keywords OR sender newer_than:Nd').execute()
thread_id = results['messages'][0]['threadId']

# Get the full thread
thread = svc.users().threads().get(userId='me', id=thread_id, format='full').execute()
for msg in thread['messages']:
    for part in msg['payload'].get('parts', []):
        if part.get('filename') and part.get('mimeType') == 'application/pdf':
            print(f"msg_id={msg['id']} filename={part['filename']}")
```

### Step 2: Download the Blank Form's PDF

Find the blank form (the original from the school/institution — not the user's filled version). Download it:

```python
msg = svc.users().messages().get(userId='me', id=BLANK_MSG_ID, format='full').execute()
for part in msg['payload']['parts']:
    if part.get('filename') == 'Blank_Form.pdf':
        att_id = part['body'].get('attachmentId')
        att = svc.users().messages().attachments().get(
            userId='me', messageId=BLANK_MSG_ID, id=att_id).execute()
        pdf_bytes = base64.urlsafe_b64decode(att['data'])
        with open('/tmp/blank_form.pdf', 'wb') as f:
            f.write(pdf_bytes)
```

### Step 3: Extract Text Positions

Use PyMuPDF to find field label coordinates:

```python
import fitz
doc = fitz.open('/tmp/blank_form.pdf')
page = doc[0]
blocks = page.get_text('dict')['blocks']
for b in blocks:
    if b.get('type') == 0:  # text
        for line in b.get('lines', []):
            for span in line.get('spans', []):
                bbox = span.get('bbox')
                print(f'"{span.get("text")}" at ({bbox[0]:.0f},{bbox[1]:.0f}) size={span.get("size")}')
```

Look for the field labels (e.g. "Child's name:", "Child's grade:") and note their right-edge position to place filled text right after.

### Step 4: Overlay Corrected Text

```python
page.insert_text(
    fitz.Point(LABEL_X1 + 2, LABEL_Y0 + FONTSIZE),  # baseline = top + size
    'Corrected Value',
    fontname='helv',
    fontsize=11,  # match original
    color=(0, 0, 0)
)
```

- `insert_text` positions the **baseline** — use `label_y0 + fontsize` to match the label's vertical alignment
- Helvetica (`helv`) is the safe cross-platform fallback font
- For checkboxes, draw a tick with shape.draw_line() — the ✓ character doesn't render in Helvetica

**Checkmark using shape.draw_line():**
```python
shape = page.new_shape()
shape.draw_line(fitz.Point(x+2, y+14), fitz.Point(x+6, y+19))
shape.draw_line(fitz.Point(x+6, y+19), fitz.Point(x+12, y+6))
shape.finish(width=1.5, color=(0, 0, 0), fill=None)
shape.commit()
```

### Step 5: Verify

Extract text from the corrected PDF to confirm overlay positions. Optionally render to image for visual check:

```python
pix = page.get_pixmap(dpi=150)
pix.save('/tmp/verification.png')
```

### Step 6: Deliver

Two options — do both:

**A. Upload to Drive TMP folder** (user's convention for all incoming/processed documents):

```python
drive = build_service('drive', 'v3', service_name='google-draas')
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload('/tmp/corrected.pdf', mimetype='application/pdf', resumable=True)
uploaded = drive.files().create(
    body={'name': 'Corrected_Form.pdf', 'parents': ['TMP_FOLDER_ID']},
    media_body=media, fields='id, webViewLink'
).execute()
```

TMP folder ID: `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`

**B. Send file via Telegram** using the `MEDIA:` tag in your response — this lets the user download directly on their phone.

### Step 7: Clean Up (if applicable)

If the corrected PDF replaces one already sent as a Gmail draft, delete the old draft:

```python
gmail.users().drafts().delete(userId='me', id=OLD_DRAFT_ID).execute()
```

## Pitfalls

- **The filled version is usually a scanned image** — the user printed, filled, signed, and scanned back. Cannot edit individual letters. Always start from the original blank form.
- **Find the blank in the same thread** — the school/institution usually sends the blank form as an attachment. The user's signed copy is in the reply (also an attachment in the same thread).
- **Checkmark characters don't render** — `✓` (U+2713) becomes a bullet `·` in Helvetica. Always draw tick marks with line shapes.
- **Coordinate confusion**: `insert_text` uses baseline, not top. `y = label_bbox[1] + fontsize` is the right baseline value.
- **PyMuPDF may not be installed** — `uv pip install PyMuPDF` to add it.
- **Password-protected PDFs**: Some financial/insurance PDFs are password-protected. See the main SKILL.md's "Password-Protected PDFs" section for common bank password patterns.
