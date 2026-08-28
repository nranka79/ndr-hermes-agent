# WhatsApp Chat → Interactive HTML Transcript with Drive-Linked Media

Convert a WhatsApp export (`.txt` + media files) into a court-submittable HTML conversation transcript where every shared file is hyperlinked to its Drive location.

## When to use

- User has a WhatsApp chat export (zip or individual files) that needs to go into evidence
- User wants to rename garbled WhatsApp media filenames (DOC-*, IMG-*) to human-readable descriptions
- User wants a single HTML document showing the full conversation with clickable media links

## Input format

WhatsApp exports (without media in zip) produce:
- `WhatsApp Chat with X.txt` — the conversation text
- `DOC-YYYYMMDD-WA####.` — documents (likely PDFs that lost their extension)
- `IMG-YYYYMMDD-WA####.jpg` — images
- `*.pdf` — direct PDFs

Check file magic bytes to identify DOC-* files — they're often PDFs with missing `.pdf` extension.

## Workflow

### Phase 1: Extract & Inspect

```bash
unzip export.zip -d /tmp/whatsapp_workdir/
cd /tmp/whatsapp_workdir
```

Read the full `.txt` file to understand the conversation flow. Identify every media attachment via lines like:

```
27/05/2026, 11:54 - Nishant Ranka: DOC-20260527-WA0045. (file attached)
```

The line immediately following often gives context (e.g., Lithika replies "Bank statement" at 12:20).

### Phase 2: Rename Media Files

Build a mapping from chat context:

| Original | Context from Chat | New Name |
|----------|------------------|----------|
| DOC-20260527-WA0045. | Sent by Nishant → Lithika says "Bank statement" | `Bank Statement - Salary Account.pdf` |
| IMG-20260612-WA0080.jpg | Sent by Lithika → "Pls answer this question sir" | `Bajaj Questions - Page 1.jpg` |

Rules for naming:
- **PDFs from Nishant**: descriptive of what the document is (bank statement, salary slip, questionnaire)
- **JPGs from Lithika**: describe what the screenshot shows (MER screenshot, clarification draft, requirement screenshot)
- Clean encoding issues (em-dashes, non-ASCII characters)
- Add `.pdf` extension to DOC-* files confirmed as PDFs by magic bytes

### Phase 3: Upload to Drive

Upload renamed files to the target Drive folder. Use `gws_auth.build_service('drive', 'v3', service_name='...')` directly (the gws_skill_bridge has known parameter bugs with `drive_search` and `drive_upload`).

```python
from tools.gws_auth import build_service
from googleapiclient.http import MediaFileUpload

service = build_service('drive', 'v3', service_name='google-draas')
media = MediaFileUpload(local_path, mimetype=mime_type, resumable=True)
uploaded = service.files().create(
    body={'name': new_name, 'parents': [folder_id]},
    media_body=media,
    fields='id,name'
).execute()
```

Record each file's Drive ID for the HTML linking step.

### Phase 4: Build Interactive HTML Transcript

Create a standalone HTML file that renders the conversation as WhatsApp-style bubbles:

**HTML Structure:**
- WhatsApp-green header with title, subtitle, media count
- Date separators: formatted as `Wednesday, 27 May 2026`
- Message bubbles:
  - Outgoing (Nishant) → green background, right-aligned
  - Incoming (Lithika) → white background, left-aligned
  - System messages (encryption, security code changes) → centered gray
- Sender name labels
- Timestamps in smaller gray text

**Media rendering within chat:**
Each media attachment appears as a card inside the message bubble where it was shared:
- Icon (📷 for images, 📄 for PDFs)
- Clickable hyperlink to the Drive file URL: `https://drive.google.com/file/d/FILE_ID/view`
- Human-readable descriptive name as link text
- Original filename shown in smaller text

**Append the EML→PDF evidence** at the bottom as a reference table if relevant to the same case.

**CSS/Design notes:**
```css
.message-bubble.outgoing { background: #d9fdd3; border-top-right-radius: 2px; }
.message-bubble.incoming { background: white; border-top-left-radius: 2px; }
.date-separator span { background: #e1f3fb; border-radius: 8px; }
```

### Phase 5: Upload HTML to Drive

Upload the transcript HTML file back to the same folder with a descriptive name like:
`WhatsApp Chat with X - Interactive Transcript.html`

## Pitfalls

- **Missing file extensions**: WhatsApp export drops `.pdf` extension from DOC-* files always. Check magic bytes (`%PDF`) before renaming.
- **Encoding in filenames**: WhatsApp exports from iOS on Linux may have em-dashes (—), smart quotes, or non-breaking spaces. Normalize with `unicodedata.normalize('NFKD', name)`.
- **PLACEHOLDER URLs**: Write the HTML with placeholder Drive URLs first, then do a single mass replacement once all files are uploaded and you have real Drive file IDs.
- **Duplicate files in Drive**: The same media may have been uploaded earlier under its original WhatsApp name. Upload renamed versions alongside originals — the court uses the descriptive names.
- **Large chats**: For chats with 50+ messages, the HTML can grow large. Split into date-range sections if needed.
- **fpdf2 multi_cell bug**: After calling `multi_cell(0, ...)`, reset `pdf.set_x(pdf.l_margin)` before the next `multi_cell` to avoid "Not enough horizontal space" error.
- **gws_skill_bridge bugs**: `drive_search` is missing `raw_query` attribute; `drive_upload` is missing `mime_type`. Always use `gws_auth.build_service` directly for Drive uploads.
