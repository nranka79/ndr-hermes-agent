# RERA Affidavit Correction Workflow (DOCX in Drive)

## When to Use

When the user asks you to correct RERA affidavits stored as .docx files in a Google Drive folder — typically the 6 standard KRERA affidavit types for a project.

## The 6 Standard Affidavits (Ranka Amber Example)

| # | Document | Has Landowners? | Has End Date? |
|---|----------|----------------|---------------|
| 1 | **FORM B** — Affidavit cum Declaration (Rule 3(4)) | Yes (brief mention) | Yes |
| 2 | **BANK AFFIDAVIT** — 100%/70%/30% bank account details | No | Yes |
| 3 | **JDA AFFIDAVIT** — Affidavit cum Declaration re JDA | Yes (2-3 mentions) | Yes |
| 4 | **No Mortgage AFFIDAVIT** | Yes | No |
| 5 | **non-litigation Affidavit** | Yes | No |
| 6 | **Section 3(1) No-Violation AFFIDAVIT** | No | No |

## Common Correction Types

### 1. IFSC Code Corrections (Cross-Document)

RERA affidavits often have inconsistent IFSC codes across documents. The 100% Collection Account and 70% Designated Account may reference different branches.

**Key data points (Ranka Amber):**
- 100% Collection A/c: 8551119387, IFSC: KKBK0000431 (Indiranagar)
- 70% Designated A/c: 8551119394, IFSC: KKBK0000431
- 30% Operative A/c: 8551119370, IFSC: KKBK0000431

Watch for: 70% A/c No field showing an IFSC (KKBK0000431) instead of an account number (8551119394). The 70% IFSC may erroneously show KKBK0008068 (100 Feet Road branch). The **FORM B** affidavit is the authoritative source for the correct IFSC.

### 2. GPA Reference Insertion for NRI/OCI Landowners

When landowners are NRI/OCI (e.g., Australian passport + OCI cardholders), add a GPA (General Power of Attorney) reference where the landowners are described.

**Standard text to insert:**
> ", as represented by their GPA Holder M/s DRA Realty Private Limited vide General Power of Attorney registered as Document No. DRO/SJN/GPA/1088/2025-2026 dated 12.08.2025 at the office of the District Registrar, Shivajinagar, Bangalore"

**Where to insert:**
- After the property description (e.g., after "Bangalore East" in "situated at... Bangalore East")
- After the first mention of "plot" in "the Landowners of the plot having valid right, title and interest..."
- In FORM B: restructure the sentence — `"Mrs. Farida Iyer and Mr. Raghu Iyer... the Landowners, [GPA TEXT], have the legal title to the land"`

### 3. Project End Date Updates

Update all occurrences of the old date to the new one. Common old dates → new:
- `10-12-2027` → `30-12-2028`

Documents that contain end dates: FORM B, BANK AFFIDAVIT, JDA AFFIDAVIT.

### 4. Typo Fixes

- "character account in practices" → "chartered accountant in practice"
- Also fix "in practices" → "in practice" (plural to singular) after the chartered accountant correction

## Technical Approach (Raw XML)

These affidavits are .docx files stored in Drive (MIME: `application/vnd.openxmlformats-officedocument.wordprocessingml.document`). Use raw XML manipulation via zipfile + ElementTree rather than python-docx — the run-splitting in these template documents makes python-docx unreliable.

See `gws-automation` skill → `references/docx-modify-reupload-drive.md` → "Alternative: Raw XML Manipulation" section for the full code patterns.

### Recommended Workflow

1. **List files in the folder** to confirm which .docx files exist
2. **Read each document** via zipfile + XML to identify current content and what needs changing
3. **Plan all replacements** for each document before coding — group simple text replacements and paragraph-level inserts separately
4. **Apply ALL changes to each document in ONE pass** from the original — do NOT do incremental uploads
5. **Verify** by re-reading the uploaded document and checking each correction

### Key Snippet — Read Docx Text

```python
request = drive.files().get_media(fileId=file_id)
content = request.execute()
z = zipfile.ZipFile(io.BytesIO(content))
xml_bytes = z.read("word/document.xml")
root = ET.fromstring(xml_bytes)
texts = []
for p in root.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}p'):
    para_text = ''.join(t.text or '' for t in p.iter(
        '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}t'))
    if para_text.strip():
        texts.append(para_text.strip())
```

## Pitfalls

1. **Run splitting is extreme** — Text like "the Landowners" may be split as `' t'`, `'he Landowner'`, `'s'`, `' of the'` across 4 separate `<w:t>` elements. Always inspect raw XML runs before coding replacements.

2. **Multiple uploads corrupt** — Each re-upload to the same file compounds run fragmentation. Always build ONE corrected version from the original.

3. **FORM B landowner text** — The sentence "That Mrs.Farida Iyer... have the legal title" is a single run but has no space after "Mrs." and no comma after "Iyer". When inserting the GPA reference, rewrite the full sentence rather than patching in-place.

4. **JDA has 2-3 landowner mentions** — The first mentions the Plot No. 1-B property description; the second mentions "the plot having valid right, title and interest". Insert GPA after "Bangalore East" in the first and after the first "plot" in the second. The third mention ("We, the Land Owners...") may not need the GPA if it just starts an indemnity list.

5. **Don't forget Section 3(1)** — This affidavit has NO landowners and NO end date. It may already have placeholders filled. Only modify if explicitly asked.

6. **Date format consistency** — KRERA uses `DD-MM-YYYY` format (e.g., `30-12-2028`). Use hyphens, not slashes or dots, unless the existing document uses a different convention.

7. **Upload as new file, keep originals** — Use `drive.files().create()` with a UPDATED suffix name rather than `update()`. This preserves the original file and lets the user compare changes.
