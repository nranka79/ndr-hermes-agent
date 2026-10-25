# Single user-uploaded document → Drive filing with content-derived naming

**Trigger:** User uploads a PDF/image document via chat/document cache and says
"rename it appropriately and store it in <folder>". This covers the full
single-document pipeline: extract content → derive name → binary upload → clean up.

## 1. Extract content to understand what the document IS

The user says "rename appropriately" — you need to know what's in it first.

**`vision_analyze` rejects PDF paths** — it only accepts real image files. Use:

```bash
# For text-based PDFs:
pdftotext "/path/to/document.pdf" - | head -200

# For scanned/image-based PDFs — render then analyze:
python3 -c "
import pymupdf
doc = pymupdf.open('/path/to/document.pdf')
for i, page in enumerate(doc):
    pix = page.get_pixmap(dpi=200)
    pix.save(f'/tmp/doc_page_{i+1}.png')
    print(f'Rendered page {i+1}')
doc.close()
"
```
Then call `vision_analyze` on each page PNG.

## 2. Derive the name from content + folder context

- Match the naming convention of **existing files in the target folder**.
  List the folder first with `gws_drive_list(folder_id="<id>")` to see the pattern.
- Property/legal doc naming in DRAAS Drive typically uses:
  `{Village}_Sy{SurveyNo}_{Description}_{SignatoryInfo}.pdf`
  e.g. `Palya_Sy9-1_PodiSketch_RoadBoundary_LandownerSigned.pdf`
- Include date prefix if the folder convention uses it.

## 2b. The letterhead wins over the filename — and over what NDR calls it

NDR names the file from memory or from the portal download; the document's own letterhead is
authoritative. **Never file under NDR's label without reading the paper first**, and when the
two disagree, say so in one line and let him choose the wording.

Worked case (2026-10-05): NDR uploaded `cc_BBMP_EoDB_CH_9271_26-27.pdf` and called it the
*"Ranka Amber commencement certificate"*. The letterhead actually reads
**"PLINTH CERTIFICATE (U/s 239 of GBG Act, 2024)"** — under the GBG Act 2024 the plinth
certificate is what supersedes the old commencement certificate, so his description was right
in substance but wrong on the paper. Filed as
`20261005_RankaAmber_BBMP_Plinth_Certificate_GBA_BECC_0540_25-26.pdf`, with the discrepancy
flagged and the alternative ("…CommencementCertificate_Plinth…") offered as a second option.

More BBMP/GBA letterhead-vs-filename traps to expect: a `.pdf` named `cc_*` may be a Plinth
Certificate, CC fee receipt, or demand note; the useful identifiers are the **Project No.**
(`GBA/BECC/0540/25-26`), the **CC/File No.** (`…/PC/01/New` — the `/PC/` segment is the tell
that it's a Plinth Certificate), and the **digital signature block** (signatory, designation,
timestamp). Quote those in the reply — they're how NDR recognises the document.

## 2c. Propose the name and get NDR's confirmation BEFORE uploading

NDR's standing request on any rename-and-file: *"what is the name you are suggesting for it?
Can you please confirm?"* So the correct sequence is:

1. Read the document → extract the naming facts (date, project, type, reference numbers).
2. List the destination folder → match the convention of the files already there.
3. **Reply with: what the document actually is, the facts, the proposed filename, and the
   destination folder — then stop and wait.** Offer 2 filename variants when the terminology is
   arguable, and 2 folder options when the destination is arguable.
4. On his confirmation, execute (upload → move → verify) and return the webViewLink.

Do not upload first and rename afterwards. He wants the name approved, not the file moved.

## 3. THE GWS_DRIVE_CREATE_FILE TRAP — binary uploads

**`gws_drive_create_file` creates an empty `text/plain` file** — it is NOT a
binary upload. Calling it with a PDF path produces a zero-byte file with no content.
The ONLY sanctioned way to upload binary content (PDFs, images, DWGs, etc.) to
Drive is via the `gws.py` wrapper:

```bash
python3 /opt/data/gws.py drive_upload google-draas \
  '{"path":"/path/to/file.pdf","parent":"<folder-id>","name":"Canonical_Name.pdf"}'
```

If you accidentally called `gws_drive_create_file` first (creating an empty text
file), delete the empty placeholder afterward:

```bash
python3 /opt/data/gws.py drive_delete google-draas \
  '{"file_id":"<empty-file-id>"}'
```

The wrapper's response includes `"status": "uploaded"`, the real Drive `id`,
and a `webViewLink` — always report the link to the user.

## 4. Complete worked example (Palya podi sketch, 2026-10-03)

User: uploaded `Sketch 9-1  PALYA Report.pdf` → "rename appropriately and store in Paliya legal"

```
1. pdftotext → empty (scanned PDF)
2. Rendered 5 pages via pymupdf, vision_analyzed each
3. Found: Government Tippan/Akarband sketch, Palya Village,
   Devanahalli Taluk, Sy 9/1-9/3, 12/3, 35-38, 42/1-42/2,
   road boundary along edge of 9/1 across from Sy 8/1
4. Listed PALYA ASHOK JEE LAND folder — existing naming pattern:
   Palya_Sy8-1_..., PALAYA ORIGINAL TIPPAN, etc.
5. Derived name: Palya_Sy9-1_PodiSketch_RoadBoundary_LandownerSigned.pdf
6. ❌ Called gws_drive_create_file — got empty text/plain file
7. ✅ Called gws.py drive_upload — real binary upload, got real file ID
8. ✅ Deleted the empty placeholder from step 6
```

## 5. Pitfalls

- **The filename NDR gives you is a hint, not the truth** — the letterhead decides, and when
  they disagree, flag it and offer both wordings (§2b).
- **Confirm the proposed name with NDR before uploading** — he asks for it explicitly
  ("what is the name you are suggesting? please confirm"), so propose → wait → then execute (§2c).
- **vision_analyze cannot read PDFs directly** — always render to PNG first.
- **pdftotext returns nothing for scanned/image-only PDFs** — that's your signal
  to use pymupdf rendering.
- **gws_drive_create_file is text-only** — never use it for binary uploads.
  It creates a `text/plain` mime type file regardless of your input.
- **The empty placeholder has a different file ID** than the real upload —
  you need two delete/upload calls.
- **Always report the final webViewLink** — the user needs to know where the
  document landed. NDR expects a clickable Drive link.