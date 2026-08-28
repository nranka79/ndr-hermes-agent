# Legal Opinion Intake & Cataloguing

Recurring workflow when DRAAS receives batch legal opinions from advocate (e.g., D.M. Shiva Shankar, M. Jeevanandam, K. Velayudham, N. Manjunath, J. Sudha Reddy — all Hosur/Krishnagiri advocates) for land parcels.

## Trigger

User sends multiple scanned PDF legal opinions (often via Telegram/PDF upload) and asks to identify which are new vs already on record, rename them, and file them in the right Drive location.

**User's stated rule (Jul 2026):** *"If the other opinions already are not signed and sealed, then this one will supersede those other opinions."* So you must also compare signed/sealed status of new vs existing.

## Step-by-Step Workflow

### 1. OCR the PDF first (if scanned)

Most Hosur advocate opinions are scanned/image PDFs with no text layer. Check with pymupdf — `sum(1 for p in doc if p.get_text().strip())` should return 0 for fully scanned. OCR the first 2-3 pages to extract identifying data:

```bash
ocrmypdf -l eng --pages 1-3 -O 0 --sidecar /tmp/ocr.txt input.pdf /tmp/out.pdf
# Use --skip-big if jbig2 permission error
# Use -O 0 for fastest mode; -O 1 for better quality
```

The sidecar text file contains the OCR text. Read it to find:
- **Advocate name + Notary Public status** (header)
- **Date of opinion**
- **Survey numbers** (in "Description of the Property" / "Schedule" section)
- **Extent** (Hec/Acre/Cents)
- **Present Owners** (vendor names or entity like "M/s. Sevaganapalli Land Partners")
- **Village, Taluk, District** (e.g., "Sevaganapalli Village, Hosur Taluk, Krishnagiri District")
- **Signature / Notary seal** on last page (OCR last 1-2 pages too)

### 2. Classify the opinion

Each opinion falls into one of these categories — get this right before searching Drive:

| Category | Identifying clue | Action |
|---|---|---|
| **Vendor-side** | Present owners are individual land sellers (e.g., "Prakash Reddy S/o Subba Reddy") | File under the relevant DRA project, NOT the buyer's project |
| **Acquirer-side** | Present owners are the DRA entity (e.g., "DRA Thindulu Land Partners" or "Sevaganapalli Land Partners") | File under the relevant DRA project |
| **Consolidated / multi-parcel** | Covers many survey numbers (e.g., 15+ items) | This is usually the master opinion for the entire project |
| **Single-parcel** | Covers 1-3 survey numbers | Subset opinion for a specific vendor |

**Vendor-side vs acquirer-side for the same survey are NOT duplicates** — they cover the same property but from different stakeholder perspectives. File both, in different subfolders.

### 3. MD5-based duplicate detection (CRITICAL — same survey ≠ same file)

Survey-number matching alone misses duplicates where the same opinion lives in two places. **Always check MD5:**

```python
import hashlib, os
def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

# Compare new upload's MD5 against all files in candidate folders
new_md5 = md5("/data/hermes/document_cache/doc_xxx.pdf")
# For each candidate, Drive returns md5Checksum in files.get()
```

Drive's `files.get` returns `md5Checksum` field — compare against local MD5 of the new upload. Same MD5 = exact byte-for-byte duplicate. Trash the duplicate, keep one in the canonical folder.

**Common duplicate patterns:**
- Same opinion saved by user in My Drive root AND in project folder
- Same opinion in legacy "Serenity Estate" folder (renamed project) AND in current "Ranka Udaya" folder
- Same opinion uploaded twice by the same advocate on different dates

### 4. Signed-and-sealed status

For each opinion, check the last page for:

| Status | What to look for | Hierarchy |
|---|---|---|
| **Advocate & Notary Public** (strongest) | "Roll No: MS xxx/yyyy" + "Notary Public, Govt. of India" | Supersedes unsigned |
| **Advocate & Notary** (Hosur City Standing Counsel) | "Ms.No: xxx" + "Hosur City Municipal Corporation Standing Counsel" | Supersedes unsigned |
| **Advocate only** (signed) | Advocate's personal stamp + signature | Older pattern — keeps for history but new notary opinion supersedes |
| **Firm letterhead** (no individual seal) | "CMS IndusLaw" / firm letterhead, dated, signed by attorney | Treat as TSR (Title Scrutiny Report), file separately |

**Workflow: when new opinion is signed/sealed AND existing opinions for the same surveys are not:**
1. File the new opinion in the canonical Legal_Opinions folder
2. Trash the exact-MD5 duplicate only (do NOT trash unsigned originals — they have historical value)
3. Note the supersession in the new opinion's description (Drive `description` field)

### 5. DRAAS Naming Convention for Legal Opinions

```
YYYYMMDD <AdvocateSurname> Legal Opinion <Village> <Entity/Seller> <Extent> <SignedSealed>.pdf
```

Examples:
- `20240921 Velayudham Legal Opinion Sevaganapalli Prakash Reddy Family 1.75 Acres Signed Sealed.pdf`
- `20251213 Jeevanandam Legal Opinion Sevaganapalli SLP 7.51 Acres Signed Sealed.pdf`
- `20241019 Legal Opinion J Sudha Reddy For Sy No 158-1C 167-2C.pdf`

**Key conventions:**
- **Prefix with date** of opinion (not received date)
- **Advocate surname** for traceability
- **Survey sub-divisions** hyphen-separated, slashes removed (158/1C9A → 158-1C9A)
- **Extent** in Acres (decimal) or Hectares
- **Suffix `Signed Sealed`** if it's a Notary Public / Standing Counsel opinion; otherwise just signed/stamped
- **For vendor-side opinions, append `(Vendor Side - <FamilyName>)`**

### 6. Target folder — DRAAS 6-bucket project structure

Per user direction (Jul 2026), every DRAAS real estate project follows this hierarchy:

```
DRA Projects /
  └─ [Entity] (DTLP / DRA Satvik / etc.) /
       └─ [Project Name] (e.g., Ranka Udaya, Ranka Oasis, Ranka Amber) /
            ├─ 01_Title_and_Legal_Opinions/
            │    ├─ Legal_Opinions/          ← LEGAL OPINIONS GO HERE
            │    ├─ Sale_Deeds/
            │    ├─ Encumbrance_Certificates/
            │    ├─ Patta_FMB_Records/
            │    └─ JDA_GPA_SPA/
            ├─ 02_Approvals/
            ├─ 03_Marketing_Collaterals/
            ├─ 04_Sanction_Drawings/
            ├─ 05_Execution_Documents_and_Drawings/
            └─ 06_Customer_Documents/
```

**Never drop a new file into My Drive root.** Even if the project is "scattered," find the canonical project folder first and put it there. If no canonical folder exists, ask the user before creating one.

### 7. Cross-Reference with Drive Inventory

Search the candidate project folder for existing opinions:

```python
from tools.gws_auth import build_service
drive = build_service("drive", "v3", service_name="google-draas")

resp = drive.files().list(
    q=f"'{folder_id}' in parents and trashed = false",
    fields="files(id, name, mimeType, size, version, md5Checksum, modifiedTime)",
    supportsAllDrives=True, includeItemsFromAllDrives=True
).execute()
```

Match:
- **MD5** (exact duplicates)
- **Survey numbers in filename** (subset duplicates — same opinion, different naming)
- **Survey numbers + advocate + date** (different versions of the same opinion)

### 8. Present findings to user, get sign-off

Before uploading or trashing, present:
- What's NEW (with proposed name + target folder)
- What's a DUPLICATE (with MD5 evidence + which one to trash)
- What SUPERSEDES what (signed/sealed comparison)
- **Wait for explicit go-ahead** — don't move/trash on your own

### 9. Upload + trash (only after approval)

```python
# Upload
from googleapiclient.http import MediaFileUpload
media = MediaFileUpload(local_path, mimetype="application/pdf")
f = drive.files().create(
    body={"name": new_name, "parents": [target_folder_id],
          "description": "<signed by whom, covers which surveys, supersedes what>"},
    media_body=media, fields="id,name,webViewLink,size",
    supportsAllDrives=True
).execute()

# Trash duplicate (recoverable for 30 days)
drive.files().update(fileId=dup_id, body={"trashed": True},
                      supportsAllDrives=True).execute()
```

### 10. Update analysis document (if one exists for this project)

Some projects have a comprehensive analysis HTML (e.g., `20260628_LegalOpinion_Analysis_BalajiLand_RelbyHoldings_Sevaganapalli.html`). When a new opinion is added:

- **Total acres** — increase by the new opinion's extent
- **Survey sub-divisions count** — increase
- **Total opinions count** — increase
- **Remove "UNACCOUNTED GAP"** row if the gap was filled
- **Add new opinion row** in the Land Extent Summary table
- **Add new opinion section** in Legal Opinions Overview (key differences row)
- **Update the "Prepared" meta** line date

## Known DRAAS Patterns

- **Hosur advocates** (D.M. Shiva Shankar, M. Jeevanandam, K. Velayudham, N. Manjunath, J. Sudha Reddy) typically use **scanned/image PDFs** — always OCR before extracting data.
- **Multiple sellers**: Not all opinions are for one entity. Some parcels are owned by individuals (e.g., "Prakash Reddy and others"). These are separate title chains that need their own opinion section in the analysis.
- **Batch receipt**: Legal opinions often arrive in batches of 2-5 PDFs at once. One is usually the "consolidated master" covering all surveys, others are vendor-specific subsets.
- **Renamed projects**: A "Serenity Estate" opinion is the SAME project as "Ranka Udaya" — opinion files may carry either name. MD5 catches the duplicates; survey numbers identify the property.
- **Cross-village confusion**: Survey numbers like 158/1, 166/3 exist in multiple villages. Always verify village + taluk + district in the opinion, not just survey number.
- **Three different DRA entities for Sevaganapalli**:
  - `Sevaganapalli Land Partners (SLP)` — Nishant Ranka + partners (Ranka Oasis project)
  - `DRA Realty Pvt Ltd` — Nishant Ranka's company (often joint owner)
  - `DRA Thindulu Land Partners (DTLP)` — for the 240/3 Ranka Udaya project (different parcel)
  - Don't conflate opinions from these three entities even if they cover adjacent surveys.
- **Existing MD5 duplicates**: The same opinion may appear in 2-3 places. Common pattern: one in My Drive root, one in the project folder, one in a legacy-named folder. Trash the loose copies, keep the one in the project folder.

## gws_skill_bridge drive_search Bug Workaround

**`gws_skill_bridge.call("drive_search", ...)` is currently broken** — it crashes with `AttributeError: 'types.SimpleNamespace' object has no attribute 'raw_query'` because the skill function checks for an arg the bridge doesn't pass.

**Workaround — use `gws_auth.build_service` directly:**

```python
from tools.gws_auth import build_service

def drive_query(q, page_size=30):
    service = build_service("drive", "v3", service_name="google-draas")
    if not q:
        r = service.files().list(pageSize=page_size, fields="...").execute()
    else:
        r = service.files().list(
            q=f"fullText contains '{q}' or name contains '{q}'",
            pageSize=page_size, fields="files(id,name,mimeType,parents,modifiedTime,md5Checksum,webViewLink,size),nextPageToken",
            supportsAllDrives=True, includeItemsFromAllDrives=True,
        ).execute()
    return r.get("files", [])
```

This works for everything `drive_search` should have done. The same pattern works for `gmail_search` and other bridge ops if you hit the same bug.
