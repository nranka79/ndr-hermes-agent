# Send Property Unit Pitch Email (AOS Floor Plans → Gmail)

**Trigger:** User wants to email a prospective buyer/broker with a list of property units they hold, including floor plan images extracted from AOS PDFs and a sales pitch.

## Workflow

### 1. Find documents on Drive

Search for the project's AOS PDFs, brochures (e-brochure, floor plan booklet), and any document index/sheet.

```python
# Search by project name
query = "(name contains 'Regalia' or name contains 'AOS' or name contains 'Brochure') and trashed=false"
# Search the project's dedicated folder
query = f"'{folder_id}' in parents and trashed=false"
```

**Key folders to check:**
- Project documents folder (e.g. `Century Regalia Documents`)
- Project brochure folder (e.g. `Century Regalia Brochure`)
- Document index spreadsheet (may list all files and their SBUAs)

### 2. Download AOS PDFs + Extract Floor Plans

Each AOS (Agreement of Sale) is a scanned PDF. The **last page** is typically Schedule D — the floor plan drawing.

```python
import fitz  # PyMuPDF
import io
from googleapiclient.http import MediaIoBaseDownload

# Download from Drive
request = drive.files().get_media(fileId=file_id)
pdf_bytes = io.BytesIO()
downloader = MediaIoBaseDownload(pdf_bytes, request)
done = False
while not done:
    _, done = downloader.next_chunk()

# Extract floor plan (last page)
pdf_bytes.seek(0)
doc = fitz.open(stream=pdf_bytes.read(), filetype="pdf")
last_page = doc[-1]
pix = last_page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x for decent quality
pix.save(f"/tmp/{unit_name}_FloorPlan.png")
```

**Floor plan image sizing:**
- `Matrix(2, 2)` → fine for email attachments (~400KB JPEG at 1780×2478)
- `Matrix(3, 3)` → higher quality (~400-500KB)
- Convert to JPEG before attaching for smaller size: render as PNG, save as JPEG with `quality=85`

### 3. Collect project info (location + online link)

Search the web for the project's address and a link (developer website, project page).

**Typical sources:** developer's own site (e.g. `centuryrealestate.in/projects/century-regalia`), realty aggregators.

**Key info to include:**
- Project address (canonical: locality, main road, city, pincode)
- Nearby landmarks (tech parks, golf courses, lakes, hospitals)
- Project scale (acreage, open %, amenities)
- Developer track record

### 4. Compose and send via Gmail API

Build a MIME multipart email with:
- Plain text body (location info + unit table + sales pitch)
- Floor plan images as attachments
- Optional: brochure PDFs as attachments

```python
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import base64

msg = MIMEMultipart('mixed')
msg['To'] = 'recipient@example.com'
msg['From'] = 'ndr@draas.com'
msg['Subject'] = 'Project Name — Units Available for Sale'

# Body — concise, sales-focused
body = """
Dear [Name],

We hold the following units at [Project Name], [Location] — [brief location hook: near Golf Course, tech park, etc.].

[2-3 line project highlights: acreage, open space, amenities, developer]

Available Units:
1. Unit X — N sft (BHK) — Buyer Name(s)
2. ...

Key highlight: [Unit A] + [Unit B] can be combined to create ~N sft premium residence — ideal for [target buyer profile: golf club members, HNIs looking for large format].

Floor plans for each unit are attached.

If you or your prospects are seeking a well-located property at a price better than what [Developer] can offer today, happy to discuss.

Project link: https://...

Warm regards,
[Your Name]
DRAAS
"""
msg.attach(MIMEText(body, 'plain'))

# Attach floor plan images
for img_path in floorplan_images:
    with open(img_path, 'rb') as f:
        part = MIMEBase('image', 'jpeg')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(img_path)}"')
        msg.attach(part)

# Attach brochure PDFs
for pdf_path in brochure_pdfs:
    with open(pdf_path, 'rb') as f:
        part = MIMEBase('application', 'pdf')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{os.path.basename(pdf_path)}"')
        msg.attach(part)

# Encode and send
raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')
result = gmail.users().messages().send(userId='me', body={'raw': raw}).execute()
```

### 5. Content preferences (Nishant Ranka style)

When drafting property pitch emails for Nishant:

| Do include | Do NOT include |
|---|---|
| Project location + online link | MOU summary/terms |
| Floor plans (as image attachments) | RERA registration number |
| Highlights (acreage, amenities, developer) | Legal analysis |
| Units table (unit #, buyers, SBUA) | Payment schedules |
| Sales pitch (especially combo units) | Loan/encumbrance details |
| Target buyer cue (golf club, HNIs, etc.) | Regulatory fine print |

**Pitch framing for Crissa 401+404 combo:** "~4,800 sft premium residence on one floor — ideal for [golf club members] looking for a large-format home at a price better than the developer's current ask."

## Follow-up emails (resend with corrections)

When the user says "send this to a different email" or asks for a follow-up:

1. **CC pattern:** If the user mentions a colleague to CC, add `msg['Cc']` to the MIME header
2. **Multiple recipients:** The user may give additional email addresses later — resend the same content to the new address(es)
3. **Email content corrections:** The user may say "remove MOU data, keep only location + units + pitch" — strip the content accordingly, don't just add more content on top
4. **Follow-up tone:** When resending (e.g. after an earlier email went to wrong address or with wrong attachments), the follow-up should:
   - Apologize briefly for the "series of emails" or the earlier mix-up
   - State clearly what this version improves (e.g. "coloured floor plans for better reference")
   - Keep the same units/pitch but present the improved materials
5. **Multiple sends to same person:** If the same person has received multiple emails from you in quick succession, the follow-up should acknowledge it and position itself as the definitive version

## Known Issues / Pitfalls

- **Per-user token must have Gmail scope** (`gmail.modify`). Verify before sending.
- **Floor plan page identification:** In AOS PDFs (scanned), the last page is typically Schedule D = floor plan. All pages render as 1 image each — no extractable text, so you can't search for "Schedule D" in text. The last page heuristic is reliable.
- **MIME size limits:** Gmail's 25MB limit applies to the base64-encoded message. 5-6 floor plan JPEGs (~400KB each) + a 2.5MB brochure PDF = well within limits.
- **Image format:** use JPEG for floor plans (smaller than PNG), not larger than 500KB each.
