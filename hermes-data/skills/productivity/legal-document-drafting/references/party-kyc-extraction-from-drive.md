# Party KYC Extraction from Drive — Building the PARTIES Section

**Use when:** You're drafting a new sale deed and need to build the PARTIES (Vendor/Vendee) section from scratch. The user has either shared a Drive folder link, or you need to search Drive for PAN/Aadhaar/address docs for each party.

**Do not confuse with:** `sale-deed-party-detail-verification.md` (verifying an already-written deed against sources — an AUDIT workflow). This is a CONSTRUCTION workflow.

## Trigger Phrases

- "Nagendra address details and PAN" + Drive folder link
- "Find the party KYC docs in the folder"
- User shares a Drive folder and says numbered items (e.g., "1,2,3")

## The Workflow

### Step 1 — Identify the Party from Source Deeds

The source sale deeds (the ones that convey the property to the vendor's predecessor) contain:
- **Full name** of the vendor (from the source deed's PURCHASER section)
- **Father's name**
- **Aadhaar number** (often embedded in the source deed text)
- The name you find in the source deed must match the name on the KYC docs

Example from this session: Source deed shows "Mr. C. R. Nagendra s/o Chintamani Somasundar Rao Ramarao, Aadhaar No. 3272 7980 6914" — the PAN card confirms "CHINTAMANI RAMARAO NAGENDRA" and the Aadhaar confirms "C R Nagendra" with the same number.

### Step 2 — Navigate the User-Shared Drive Folder

User shares a Drive URL: parse the folder ID from it.

```python
# Folder URL pattern: https://drive.google.com/drive/folders/<FOLDER_ID>
folder_id = '1jxTeU0PZWO7Ag_OYzTb3G-K_NazD-Vle'  # from the URL

from tools.gws_auth import build_service
drive = build_service('drive', 'v3', service_name='google-draas')

# List all files in the folder
results = drive.files().list(
    q=f"'{folder_id}' in parents",
    fields="files(id, name, mimeType, size, modifiedTime)",
    orderBy="name"
).execute()
files = results.get('files', [])
```

**Identify the KYC docs by filename patterns:**
- `*PAN*`, `*PAN_CARD*`, `*PAN Card*` — PAN card
- `*Aadhaar*`, `*AADHAR*`, `*Aadhar*` — Aadhaar card
- Prefer files with the party's name/initials (e.g., `CRNagendra_PAN.pdf` over generic `NAG PAN CARD.pdf`)
- Check dates — prefer the most recent

### Step 3 — Download and Extract

**For text-based PDFs** (rare — PAN/Aadhaar are usually scanned images):
```python
import pymupdf
doc = pymupdf.open('/tmp/file.pdf')
text = ""
for page in doc:
    text += page.get_text()
# If text is empty / mostly whitespace → it's a scanned image, use vision_analyze
```

**For scanned (image) PDFs** (typical for KYC docs):
```bash
# Step A: Convert to PNG
pdftoppm -png -r 300 input.pdf /tmp/output_prefix

# Step B: Analyze with vision
# Use vision_analyze(image_url='/tmp/output_prefix-1.png', question='Extract all details...')
```

**What to extract from each document:**

| Document | Data Points |
|----------|-------------|
| **PAN Card** | PAN number, Full name (matching the entity/individual), Father's name, DOB |
| **Aadhaar Card** | Aadhaar number, Full name, DOB/Age, Gender, **Residential address** (this is your primary source for the party's address in the deed) |
| **Certificate of Registration** (firm/company) | Registration number, Date of registration, Registered office address |

### Step 4 — Cross-Reference Identity

Before using any extracted data, confirm the identity linkage:
1. Does the name on the PAN card match the name from the source deed?
2. Does the Aadhaar number on the card match what's in the source deed recitals?
3. If a firm's PAN, does the entity name on PAN match the firm name in the source deed?

If names don't exactly match (e.g., "CHINTAMANI RAMARAO NAGENDRA" on PAN vs "C. R. Nagendra" in source deed), note the formal name from PAN and use the short form from source deeds — both are the same person.

### Step 5 — Also Get Firm/Entity KYC

When the property flows through a dissolved firm (e.g., Satvik Developers), also extract:
- **Firm PAN card** — confirms PAN: ADLFS4825K
- **Certificate of Registration** — confirms firm name, registration number (e.g., SJN-F 1336/2016-17), registered address, date of registration

These are needed for the Recital section (WHEREAS C — describing the firm's dissolution and partition).

### Step 6 — Build the PARTIES Block

Standard Karnataka format for an individual Vendor:

```
**MR. [FULL NAME AS ON PAN]**
(Full Name: [LEGAL NAME FROM PAN])
S/o. [FATHER'S NAME],
Aged about [AGE] years (DOB: [DOB FROM AADHAAR/PAN]),
Residing at [ADDRESS FROM AADHAAR],
PAN: [PAN NUMBER],
Aadhaar: [AADHAAR NUMBER],
```

### Step 7 — Update Remaining Placeholders Table

After extracting and filling party details, compile a clean table of what's STILL missing:

| Field | Status |
|-------|--------|
| Date of execution | [●] |
| Vendee's PAN/Aadhaar/address | [●] |
| Total sale consideration | [●] |
| Witness details | [●] |

### Step 8 — Populate a Google Docs Template (Partnership Deed, Draft Deed)

When the target draft is a Google Doc with placeholder paragraphs like `[FIRST PARTNER NAME], son/daughter of [Father's Name]...`:

1. **Never `replaceAllText` the placeholder blindly.** The identical tail text (`son/daughter of [Father's Name], aged about _____ years...`) repeats in EVERY party paragraph (FIRST PARTNER, SECOND PARTNER, ...). replaceAllText would write the same person into all of them. Target exact element indices instead.
2. Read the doc via `docs.documents().get()` (`service_name='google-draas'` for psingh@draas.com). Each paragraph's `startIndex`/`endIndex` are document-wide absolute char offsets, and `endIndex` includes the trailing `\n`. A placeholder paragraph is usually split into multiple text runs (bold name span, plain tail span, bold quoted term) — don't assume a single run.
3. **Pattern: delete → insert → restyle**
   - `deleteContentRange` on (startIndex, endIndex) of the placeholder paragraph.
   - `insertText` at the SAME startIndex with the fully-built party block.
   - `updateTextStyle` with `{"bold": True}` on the name span and the quoted `"FIRST PARTNER"` span (template keeps those bold).
   - **After delete/insert, indexes shift** — compute style ranges relative to the insertion index (`insert_idx + offset_into_new_text`), never the pre-delete positions.
4. Read back with `documents().get()` and print the paragraph(s) to confirm before telling the user it's done.

**Verified principal KYC (extracted 2026-08 from latest Drive copies — NDR PAN `1kp86mmaApPuMYQs7vW1XYA8a7pIsPfmF` / Aadhaar `1M_MMyMneXUGJi9tRsge6Q-Gt7JQTfzh-`):**
- NDR = **MR. NISHANT DINESH RANKA** (PAN name: NISHANT RANKA), s/o **Dinesh Devraj Ranka**, DOB **18/12/1979**, PAN **AHVPR5168E**, Aadhaar **4159 0535 2796**, address: C/o Dinesh Ranka, Flat No. 1503, Embassy Habitat, No. 59, Palace Road, Bengaluru – 560 001.

## Common Pitfalls

- **Vision_analyze rejects PDF directly**: You MUST convert to PNG first. `vision_analyze` only accepts real image files, not PDFs.
- **pdftoppm not installed**: Use `which pdftoppm` to check. Falls back to `python3 -c "from pdf2image import convert_from_path; ..."` if Pillow is configured.
- **Aadhaar address format**: The Aadhaar e-letter may have the address split across multiple lines with odd spacing — normalize it into a clean one-per-line format for the deed.
- **Firm name mismatch**: The Certificate of Registration and PAN card may use slightly different entity names (e.g., "SATVIK DEVELOPERS" vs "M/s. Satvik Developers"). Use the formal name from the registration certificate as the canonical form.
- **User says "1,2,3" or similar shorthand**: This usually means items 1, 2, 3 in the Drive folder listing (sorted by name). Check the filename patterns and ask for clarification if ambiguous.
- **Docs API `replaceAllText` clobbers repeated placeholder tails**: In multi-party template docs (FIRST PARTNER / SECOND PARTNER), the tail text after the name is identical in every block. `replaceAllText` would write the same details everywhere. Use index-targeted `deleteContentRange` + `insertText` per paragraph instead.
- **Bold spans survive replacement only if you reapply them**: The template's name span and the quoted `"FIRST PARTNER"` / `"SECOND PARTNER"` term are bold runs separate from the plain tail. After delete+insert, re-issue `updateTextStyle` with `{"bold": True}` for those exact ranges, computed from the insertion point (indexes shift after insert).

## Verified Against

- Byadarahalli Sale Deed draft (Aug 2026) — extracted C.R. Nagendra's PAN (ABBPN5581H), Aadhaar (3272 7980 6914), and address (B-41 Zonasha Paradiso, Bengaluru) from user-shared Drive folder, then populated the PARTIES section of the draft.