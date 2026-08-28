# Entity Name Search Across Scanned Property Documents

**Trigger:** User shares a Drive folder with scanned property documents (sale deeds, gift deeds, agreements) organized by survey number, and asks you to find every document mentioning a specific developer/party/builder name, then compile results into a spreadsheet.

**Core pattern:** OCR-extract text from each scanned PDF → search for the entity name → extract registration/document number → build a Google Sheet with results.

---

## Workflow

### Phase 0 — Verify OAuth & User Identity

Before touching any GWS data, confirm whose data you're accessing:

```python
import os, sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

gmail = build_service('gmail', 'v1')
profile = gmail.users().getProfile(userId='me').execute()
email = profile.get('emailAddress', 'Unknown')
uid = os.environ.get('HERMES_SESSION_USER_ID', 'UNKNOWN')
print(f"Session user: {uid} → GWS account: {email}")
```

**If the GWS account doesn't match the user's claimed email:**
The OAuth token was authorized for a different Google account. Tell the user:
> *"Your session shows as [claimed email] but the stored OAuth token is for [resolved email]. This means the authorization link was opened while signed into a different Google account. I'll generate a fresh link — please open it and sign in as your correct account."*

Generate the fresh URL:
```python
from tools.gws_auth import get_auth_url
url = get_auth_url(uid)
```

### Phase 1 — Recursively List All Files

The folder is typically organized by survey number subfolders (Sy.no.41/17, Sy.no. 41/14, etc.). List everything:

```python
def get_all_files(drive, fid, path=""):
    results = []
    pt = None
    while True:
        resp = drive.files().list(
            q=f"'{fid}' in parents and trashed=false",
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageToken=pt, pageSize=200
        ).execute()
        for f in resp.get('files', []):
            fp = f"{path}/{f['name']}" if path else f['name']
            if f['mimeType'] == 'application/vnd.google-apps.folder':
                results.extend(get_all_files(drive, f['id'], fp))
            else:
                results.append({**f, 'path': fp})
        pt = resp.get('nextPageToken')
        if not pt:
            break
    return results

all_files = get_all_files(drive, FOLDER_ID)
```

**Extract survey number from the path** using a regex:
```python
import re
survey_pat = re.compile(r'(?:Sy\.?|survey)\s*[Nn][Oo]?\.?\s*([\d,/\s]+)')

def get_survey_no(path):
    for part in path.split('/'):
        m = survey_pat.search(part)
        if m:
            return m.group(0).strip()
    return "General"
```

### Phase 1.5 — Drive full-text search optimization (BEFORE OCR)

For targeted name searches, **try Drive's built-in full-text search first** — it's dramatically faster than downloading + OCR-ing hundreds of PDFs. Drive indexes text content of PDFs and Google Docs automatically:

```python
page_token = None
while True:
    resp = drive.files().list(
        q="fullText contains 'Satvik Developer' and trashed=false",
        fields="nextPageToken, files(id, name, mimeType, size, owners)",
        pageToken=page_token,
        pageSize=100
    ).execute()
    for f in resp.get('files', []):
        print(f"  {f['name']} — {f['id']}")
    page_token = resp.get('nextPageToken')
    if not page_token:
        break
```

**Limitations:**
- Only indexes text-layer PDFs (digitally created, not scanned). Scanned PDFs are invisible to full-text search.
- Search is by token/stem — exact phrase matching may miss variants. Use the shortest unique name term.
- Results are across the **entire Drive**, not restricted to one folder. Add folder conditions: `and '{folder_id}' in parents`.

**When to use full-text vs OCR:**

| Approach | Speed | Best for |
|----------|-------|----------|
| Drive full-text search | Seconds | Text-layer PDFs, Google Docs, specific known names |
| pdftotext + OCR | Slow (per doc) | Scanned registered deeds, old documents |
| Both combined | Fast | Query Drive first, then OCR the remaining candidates |

### Phase 2 — Filter Candidates

Focus on documents most likely to contain an entity/buyer/seller name (sale deeds, gift deeds, agreements, absolute sale deeds, release deeds, powers of attorney):

```python
key_keywords = ['sale deed', 'agreement', 'gift', 'absolute sale', 
                'release', 'partition', 'confirmation', 'power of attorney',
                'gpa', 'general power']
candidates = [f for f in all_files 
              if any(k in f['name'].lower() for k in key_keywords)]
```

**Document type filtering strategy — what to SKIP:**
Skip mutation registers, ECs (Encumbrance Certificates), RTCs (Record of Rights, Tenancy and Crops), Aakarbands/Akarbandh (survey sketches), Pakka books, Hissa books, Aadhar copies, family tree certificates, death certificates, village maps, survey sketches, and Patta/Receipts — these are government records without developer/party names. This can reduce scan volume by 70-80%.

### Phase 3 — Download & OCR

For each candidate PDF, download to `/tmp/` and attempt OCR:

```python
import subprocess, os

def extract_text_from_pdf(drive, file_id, local_path):
    """Download PDF and extract text. Returns '' if scanned."""
    # Download
    request = drive.files().get_media(fileId=file_id)
    with open(local_path, 'wb') as f:
        f.write(request.execute())
    
    # Try pdftotext first (fast, works on text-layer PDFs)
    result = subprocess.run(
        ['pdftotext', '-layout', local_path, '-'],
        capture_output=True, text=True, timeout=30
    )
    text = result.stdout.strip()
    if len(text) > 50:
        return text  # Text PDF — done
    
    # Scanned — use pdftoppm + tesseract
    page_dir = f"/tmp/pages_{os.urandom(4).hex()}"
    os.makedirs(page_dir, exist_ok=True)
    
    # Render first 3 pages only (entity name usually on page 1-2)
    subprocess.run(['pdftoppm', '-png', '-r', '200', 
                    '-l', '3', local_path, f"{page_dir}/page"],
                   capture_output=True, timeout=60)
    
    ocr_text = ""
    for img in sorted(os.listdir(page_dir)):
        if img.endswith('.png'):
            base = img.replace('.png', '')
            result = subprocess.run(
                ['tesseract', f"{page_dir}/{img}", f"{page_dir}/{base}",
                 '-l', 'eng', '--psm', '6'],
                capture_output=True, timeout=60
            )
            if os.path.exists(f"{page_dir}/{base}.txt"):
                with open(f"{page_dir}/{base}.txt") as f:
                    ocr_text += f.read() + "\n"
    
    # Cleanup
    import shutil
    shutil.rmtree(page_dir, ignore_errors=True)
    return ocr_text
```

**Performance tip:** Render only the first 3 pages (entity/party names appear on page 1-2 of any registered deed). For very small documents (<5 pages), render all pages.

### Phase 4 — Search for Entity Name

```python
entity_name_lower = "satvik developer"

def search_document(text, entity_name):
    """Return match locations or empty list."""
    text_lower = text.lower()
    if entity_name.lower() in text_lower:
        # Find surrounding context
        lines = text.split('\n')
        matches = []
        for i, line in enumerate(lines):
            if entity_name.lower() in line.lower():
                matches.append(line.strip()[:150])
        return matches
    return []
```

**Search name variants:** Also search for just the first word ("Satvik") and common misspellings ("Satwik"). Party names in deeds can be abbreviated (e.g. "M/s Satvik Developers" vs "Satvik Developer").

### Phase 5 — Extract Registration Number

Indian registered deeds have a document number in the format `Doc No. XXXX/YYYY` or `No. XXXX` or similar. Extract with regex:

```python
doc_no_pattern = re.compile(
    r'(?:Doc(?:ument)?\s*(?:No\.?|#)\s*|No\.?\s*)([\d]+(?:/\d+)?(?:\s+of\s+\d+)?)',
    re.IGNORECASE
)

def extract_doc_numbers(text):
    matches = doc_no_pattern.findall(text)
    return matches[0] if matches else ""
```

Also try to extract the **date** of the deed:
```python
date_pattern = re.compile(r'(?:dtd?\.?|dated?)\s*(?:(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4}))')
```

### Phase 6 — Build Google Sheet

```python
from tools.gws_auth import build_service
sheets = build_service('sheets', 'v4')

# Create sheet in the same parent folder
sheet = drive.files().create(body={
    'name': f'YYYYMMDD_Satvik_Developer_Document_Search.xlsx',
    'mimeType': 'application/vnd.google-apps.spreadsheet',
    'parents': [PARENT_FOLDER_ID]
}, fields='id,name,webViewLink').execute()
SHEET_ID = sheet['id']

# Headers
header = ['Survey No', 'Document Name', 'Document Link', 'Type', 
          'Registration No', 'Date', 'Match Context']
rows = [header]

# Populate
for match in matches:
    link = f"https://drive.google.com/file/d/{match['file_id']}/view"
    rows.append([
        match['survey_no'],
        match['doc_name'],
        link,
        match['doc_type'],
        match.get('reg_no', ''),
        match.get('date', ''),
        match.get('context', '')
    ])

sheets.spreadsheets().values().update(
    spreadsheetId=SHEET_ID,
    range='Sheet1!A1',
    valueInputOption='USER_ENTERED',
    body={'values': rows}
).execute()

# Make readable
drive.permissions().create(
    fileId=SHEET_ID, 
    body={'type': 'anyone', 'role': 'reader'}
).execute()

print(f"Sheet created: {sheet['webViewLink']}")
```

### Phase 7 — Report to User

Present results concisely:

> **Done.** Scanned [N] documents across [M] survey numbers.
> **Found [X] documents mentioning "Satvik Developer":**
> - Survey 41/17: Sale Deed dtd 02-03-2017 — Doc No. 10739/2017
> - Survey 192/2: Gift Deed No 9423/2019
> ...
> 
> **📊 Sheet:** [link]
> 
> **Survey numbers with NO match:** [list]

---

## Pitfalls

- **Token mismatch before even starting:** Always verify which GWS account the OAuth resolves to first. A wrong-account token serves the wrong person's Drive/Gmail. The API calls succeed, the results are just from the wrong user's data.
- **Survey number normalization:** Some folders use `Sy.no.41/17`, others `Sy.no. 41/14` (with space, different separators). The `get_survey_no()` regex handles this, but verify against the actual folder names.
- **pdftotext returns 0-10 chars on scanned PDFs** — this is the signal to use tesseract. Threshold at 50 chars to avoid false negatives.
- **Old deeds (pre-2000) have poorer OCR quality** — handwriting, faded text. accept partial matches. Tesseract `--psm 6` (uniform block) works better than default on deed body text.
- **Distinguishing individual vs company purchaser:** When searching for a person's name (e.g. "C R Nagendra"), the name may appear as:
  - **Party as individual:** "IN FAVOUR OF Mr. C. R. Nagendra" — direct purchaser
  - **Party as company representative:** "SATVIK DEVELOPERS ... represented by its Partner Mr. C. R. Nagendra" — company purchaser
  Always check the surrounding text (especially "IN FAVOUR OF" or "For" lines) to determine whether the person bought as an individual or on behalf of a firm.
- **Deed registration number format varies by state/era.** Karnataka deeds may have format `{Year}-{Number}` or `No. 1234/2023-24`. Always extract the most document-number-like token near the preamble.
- **Very large folders (800+ docs):** OCR-ing every single document is slow. Focus on sale deeds, agreements, and gift deeds first — these are the documents where a developer/buyer name would appear. RTCs, ECs, Mutation Registers, and Aakarbands are government records without party names.
- **Don't rerender pages:** If you already downloaded and OCR'd a PDF, cache the result. Avoid redownloading from Drive on retries.
- **600-second timeout limit on large OCR batches:** Scanning 100+ scanned documents via pdftoppm + tesseract routinely exceeds the 300-600s timeout limit. Solutions:
  1. Use Drive full-text search first (Phase 1.5) to find text-layer matches instantly
  2. Use `delegate_task` for heavy batches — subagents get their own timeout budget
  3. Process in small batches (20 docs at a time) with intermediate result saves
  4. Focus only on the document types most likely to contain party names (sale deeds, agreements, GPAs)
- **Search across entire Drive, not just one folder:** When a name yields 0 results in a specific folder, broaden the search to the user's entire Drive using `fullText contains 'Name'` with no folder restriction. The document may be in a different project folder.
- **Subagent delegation for heavy batches:** For 100+ candidate documents, delegate to a subagent with `toolsets=["terminal","file","coding"]` — it can batch the OCR in parallel and return results. The key limitation is that subagents cannot call `build_service` from the main process, so pass the folder ID and file list to the subagent context. Note: subagents also have a timeout limit (600s default), so for very large folders (800+ docs) you may need to split across multiple subagents or use cron jobs.
- **Sheets API `update` vs `append`:** Use `update` with the full header+data array (writes in one shot). `append` adds rows below existing data which can cause duplicates if called multiple times.
- **Clean up temp files:** After the job, `rm -rf /tmp/pages_* /tmp/intake_*.pdf` — these accumulate quickly with 800+ documents.
