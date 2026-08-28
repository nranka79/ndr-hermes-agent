# School Document Filing Workflow

**Trigger:** User sends a school document (PDF/image) for their child(ren) and asks to file it on Drive and remember it.

**Applicable to:** Ranka family — Ruhan Ranka (Std. 9 IGCSE, Aditi International School, Yelahanka).

---

## Workflow

### Step 1 — Read the Document
Convert PDF to image and extract content via `vision_analyze` BEFORE any naming or uploading:
```python
from pdf2image import convert_from_path
pages = convert_from_path('/path/to/doc.pdf', dpi=150)
for i, page in enumerate(pages):
    page.save(f'/tmp/doc_page_{i+1}.jpg', 'JPEG', quality=85)
```
Then `vision_analyze` to extract key content (contact names, roles, email addresses).

### Step 2 — Identify or Create the Child's Folder
Search in `Personal/` folder (ID: `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE`) for child's folder:
```python
results = drive.files().list(
    q="'0B1Oc8cSaJXPGYkQtYXJDQWVBUVE' in parents and name contains 'ChildFirstName'",
    fields="files(id, name)"
).execute()
```
If no folder exists, create it:
```python
folder_metadata = {
    'name': 'ChildFirstName',
    'mimeType': 'application/vnd.google-apps.folder',
    'parents': ['0B1Oc8cSaJXPGYkQtYXJDQWVBUVE']
}
result = drive.files().create(body=folder_metadata, fields='id').execute()
child_folder_id = result['id']
```

### Step 3 — Upload with Original Filename
Keep the original filename as provided by the school — it carries meaning (e.g., `Whom Do I Contact_9IGCSE_2026-27.pdf`). Do NOT rename to the user's naming convention (`YYYYMMDD Project Entity DocumentType`) — school document filenames are institutional and should be preserved as-is.

```python
from googleapiclient.http import MediaFileUpload
metadata = {
    'name': '<original-filename>',
    'parents': [child_folder_id]
}
media = MediaFileUpload('/path/to/file.pdf')  # mimetype auto-detected
result = drive.files().create(body=metadata, media_body=media, fields='id,webViewLink').execute()
```

### Step 4 — Extract and Note Key Contacts
From the vision analysis, extract relevant contacts and save to memory (see Step 5).

### Step 5 — Permanent Memory Update
Add an entry under `target: memory`:
- Child's name and school
- Document name and Drive link
- Key contacts (names + email addresses)
- Instruction to search Drive for this file when asked about the child's school affairs

**Memory space constraint:** Memory is limited to ~2,200 chars. When adding a new family member entry, remove or consolidate older entries first. Target: brief but actionable — enough to locate the document and find contacts without re-reading the PDF.

Example memory entry for Ruhan:
```
Ruhan Ranka (Nishant & Roshni's son, Std.9 IGCSE Aditi Yelahanka). School contacts PDF 'Whom Do I Contact_9IGCSE_2026-27.pdf' in Drive Personal/Ruhan/ (https://drive.google.com/file/d/<fileId>/view). Search Drive when asked about Ruhan school contacts. Key contacts: Sathish Jayarajan principal@aditi.edu.in, Joyce Jose joyce.jose@gsuite.aditi.edu.in, Neena David neena.david@gsuite.aditi.edu.in, Radhika Srinivasan radhika.srinivasan@gsuite.aditi.edu.in.
```

### Step 6 — Confirm to User
Report: file location, Drive link, memory updated, key contacts noted.

---

## Key Contacts — Aditi International School Std. 9 IGCSE 2026-27

| Concern | Contact | Email |
|---------|---------|-------|
| Principal | Mr. Sathish Jayarajan | principal@aditi.edu.in |
| Head, High School | Miss Joyce Jose | joyce.jose@gsuite.aditi.edu.in |
| Academic Concerns | Deputy Head Neetika Khurana | neetika.khurana@gsuite.aditi.edu.in |
| College Advice | Higher Education Advisor | principal@aditi.edu.in |
| Administration | Mr. Joel Kribairaj | maisadmn@aditi.edu.in |
| Counselling | Dr. Neena David | neena.david@gsuite.aditi.edu.in |
| Child Safety Officer | Ms. Radhika Srinivasan | radhika.srinivasan@gsuite.aditi.edu.in |
| SUPW | Ms. Simi Hilson | simi.joy@gsuite.aditi.edu.in |
| Finance | Mr. Ganesh Gibson / Ms. Ashwini Prabhakar | ganesh@aditi.edu.in / ashwini@aditi.edu.in |
| Transport | Ms. Sonia Arujah | transport@aditi.edu.in |

**Appointment requests:** Mrs. Samyukta Muralidhar — samyukta@aditi.edu.in / 9686450306
**School main line:** 40447000 (8 a.m. – 4 p.m. on school working days)

---

## Pitfalls

1. **Memory overflow** — Adding a full family member entry (~550 chars) can push memory past the 2,200 char limit. Remove or shorten older entries before adding. Target: brief but sufficient to locate the document.
2. **Wrong folder parent** — Always use `Personal/` folder ID `0B1Oc8cSaJXPGYkQtYXJDQWVBUVE` as parent when creating a child subfolder. Do not search from root — searching `name contains 'Ruhan'` from root returns nothing.
3. **MediaFileUpload mimetype** — Do NOT pass `mimetype=` as a constructor argument. Pass only the file path — mimetype is auto-detected. The old pattern `MediaFileUpload(path, mimetype='application/pdf')` raises `TypeError`.
4. **School document filenames** — Preserve the original school filename. These documents are institutional and renaming them (to the DRAAS `YYYYMMDD Project Entity DocumentType` convention) loses context. Upload with original name.
5. **PDF text extraction via `pdf2image` not subprocess** — Use `python3 -c "from pdf2image import convert_from_path; ..."` in the terminal tool. Do NOT call `pdf2image` as a subprocess CLI — it is a Python module, not a standalone executable.