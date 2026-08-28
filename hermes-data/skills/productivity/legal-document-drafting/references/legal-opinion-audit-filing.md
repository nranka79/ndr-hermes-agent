# Legal Opinion Audit & Filing — Drive Workflow

When the user drops a legal opinion (signed + sealed, or just a draft) into the chat and says "file it appropriately" or "supersedes the old one" or "discard if duplicate", this is the workflow. Distinct from `document-receipt-naming-filing.md` (which covers *receiving* documents from counterparties); this covers *auditing* and *filing* existing legal opinions that may supersede others in Drive.

## When this applies

Triggers: "I just received a signed legal opinion from Velayudham for 240/3", "find existing opinions for Ranka Oasis and file this correctly", "this should supersede the older unsigned one", "if it's a duplicate, discard it", "look at the survey numbers and rename it appropriately", "look at our Drive for the same survey numbers".

User is handing over a finished opinion (usually scanned PDF, possibly with Notary Public seal) and asking for two things in one pass:
1. **Classify** — which project, which survey number, which lawyer, signed or not
2. **File correctly** — find existing opinions in the same project, detect duplicates or supersession, then file the new one (and trash duplicates)

## The 6-step workflow

### 1. Read content BEFORE any decision (no exceptions)

Legal opinions are almost always scanned PDFs with no text layer. `pdftotext` returns near-empty. Use ocrmypdf with sidecar output for the first 2 pages + last 2 pages only — that's enough to identify the lawyer, parties, survey numbers, and check for signature/seal.

```bash
# First 2 pages (lawyer letterhead, parties, property description)
ocrmypdf -l eng --pages 1-2 -O 0 --sidecar /tmp/ocr_head.txt \
  "<input.pdf>" /tmp/ocr_out.pdf

# Last 2 pages (signature, notary seal, opinion conclusion)
ocrmypdf -l eng --pages N-1-N -O 0 --sidecar /tmp/ocr_tail.txt \
  "<input.pdf>" /tmp/ocr_out.pdf
```

`-O 0` = skip OCR for pages that already have text. `--sidecar` writes the text to a `.txt` file you can grep for survey numbers and party names.

**What to extract from the OCR:**
- Lawyer name + Roll No / Enrolment No (from letterhead on page 1)
- Date of opinion
- Survey number(s) covered
- Village + Taluk + District
- Present owner(s) (the "for whom" the opinion is given)
- **Signature + seal status** (last 2 pages) — Notary Public seal + signature is stronger than just an Advocate stamp; this is the "signed and sealed" question that drives the supersession decision

### 2. Classify by survey number → project mapping

The classification is **survey-number-driven**, not filename-driven. Same village, same project, but a different survey number can mean a different land parcel under a different partnership entity.

Common Sevaganapalli / Ranka Oasis / DRA Thindulu mapping (Jul 2026 snapshot — confirm before assuming):

| Survey numbers in Sevaganapalli | Project / entity | Drive root folder |
|---|---|---|
| 158/1C*, 166/1, 166/3*, 167/1G, 167/2*, 168/1B, 176/2B4A, 176/1B2D, 177/1A1* | **Ranka Oasis** / Sevaganapalli Land Partners + DRA Realty | `Sevaganapalli Land Partners` (id `104VWF9-XdeLX612NjHE9s2-92KTpmz77`) → `01_Legal_and_Title_Docs` → `Legal Opinions` (id `1JVVcYPZDuPR9GyAVIwmiZpWiJzWw0FnX`) |
| 240/3 (Ac.1.75 cents) | **Ranka Udaya** / DRA Thindulu Land Partners | `Ranka Udaya (DRA Tindlu Land partners Master Folder)` (id `10sk0X6dq9-Rzo2BajJKNFkEts_pfRxLT`) → `Legal Reports` (id `1gfmcuREMa5zaCRddwXWl0zXZh9rXhfg5`) |

**Pitfall — same village, different projects:** Sevaganapalli has multiple land parcels under different entities. A 240/3 opinion is NOT a Ranka Oasis opinion even though both are in the same village. Always classify by survey number first, not village.

**Pitfall — legacy project name rebranding:** "Serenity Estate" was the old name for the project now called Ranka Udaya / DRA Thindulu Land Partners. If you see "Serenity Estate" in a filename or folder, treat it as Ranka Udaya. (The same is NOT true for "Serenity Hill View" / "Serenity Hillview" — that is a separate, active 2026 project unrelated to 240/3.)

### 3. Search Drive for existing opinions in the same project

For each target survey number, do a **broad full-text search** — not just on the survey number, but on party names, lawyer names, project names, and acronyms:

```python
import sys
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

drive = build_service("drive", "v3", service_name="google-draas")

search_terms = [
    "Velayudham",          # lawyer
    "Jeevanandam",         # another Hosur advocate
    "Sevaganapalli",       # village
    "240/3",               # specific survey
    "Ranka Oasis",         # project
    "Ranka Udaya",         # newer project name
    "SLP",                 # Sevaganapalli Land Partners
    "DRA Thindulu",        # older spelling
    "Legal Opinion",
    "Legal Scrutiny",
]

for term in search_terms:
    r = drive.files().list(
        q=f"fullText contains '{term}' or name contains '{term}'",
        pageSize=30,
        fields="files(id,name,mimeType,parents,modifiedTime,size,md5Checksum,version,webViewLink)",
        supportsAllDrives=True, includeItemsFromAllDrives=True,
    ).execute()
    for f in r.get("files", []):
        print(f"  [{term}] {f.get('name')} | {f.get('id')} | v{f.get('version','?')} | mtime={f.get('modifiedTime','?')[:10]}")
```

**Why full-text, not just filename:** Existing opinions might be filed under cryptic names like `240926-sevaganapalli land partners legal opinion for sy.no-7.22 Acres.pdf` — survey number is in the filename but only as part of a longer string. Full-text search catches that.

**Why so many terms:** Same project may have opinions from multiple lawyers (Velayudham, Jeevanandam, N. Manjunath, J. Sudha Reddy, CMS IndusLaw). Each one is a different entry point. Skim all the results, then narrow down to the project + survey number.

### 4. Compare existing opinions to the new one — MD5, then content

**MD5 first (fast, definitive):** Get the new file's MD5, compare to existing file MD5s in the same project. An exact MD5 match means it's the same file — definitively a duplicate, can be trashed if the existing copy is in the right place.

```python
import hashlib
def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as fh:
        for chunk in iter(lambda: fh.read(8192), b''):
            h.update(chunk)
    return h.hexdigest()
```

**If MD5 differs (the common case):** Compare content. Look for:
- **Survey number coverage** — does the existing opinion cover the same survey(s)?
- **Sign + seal status** — is the existing one signed+sealed (Notary Public seal + signature) or just stamped (Advocate stamp only)? A Notary Public seal carries more legal weight — the new one supersedes if it adds that.
- **Date** — newer is generally better, but a newer unsigned opinion does NOT supersede an older signed+sealed one
- **Parties** — same owner or different? A vendor-side opinion (for the seller family) is a different document from an acquirer-side opinion (for the buyer) — they cover the same survey but serve different purposes, BOTH should be kept

**The "supersedes" decision matrix:**

| New opinion status | Existing opinion status | Decision |
|---|---|---|
| Signed + Notary sealed | Unsigned / advocate-stamp only, same surveys | **Supersedes** — file new, trash old |
| Signed + Notary sealed | Signed + Notary sealed, same surveys, newer date | **Supersedes** — file new, trash old |
| Signed + Notary sealed | Signed + Notary sealed, same surveys, older date | Keep both, file new alongside |
| Signed + Notary sealed | Covers different surveys only | File new, no action on old |
| Vendor-side (seller) | Acquirer-side (buyer) | Both kept — different perspectives, same property |
| Same MD5 as existing | — | Pure duplicate, trash new (or trash existing copy that's in the wrong place) |

### 5. Two-phase execution — file the new, then SEPARATELY plan the larger reorg

The user often says "file this opinion, and if applicable clean up the folder". These are **two different risk levels**:

- **Phase A — file the new opinion + trash exact-MD5 duplicates:** Low risk, single-purpose, easily reversible (Drive trash retains 30 days). Execute in one batch.
- **Phase B — broader folder reorg (rename, restructure, move 20+ files):** Higher risk, larger blast radius, may need user approval on every rename.

**Rule:** Always execute Phase A immediately. For Phase B, deliver a **separate HTML reorg plan to TMP** with:
- Current tree (AS-IS) with file IDs and sizes
- Proposed tree (TO-BE) with renamed files
- A "Decisions Required" table (typically 4-5 multiple-choice items: new subfolders? rename pattern? trash empty source folder?)
- Reversibility note: "all moves and deletes go to Drive Trash first, recoverable for 30 days"

Wait for explicit user approval before executing Phase B.

### 6. Don't trash anything that is NOT a verified duplicate

The user (Nishant) was explicit about this in the Jul 2026 Sevaganapalli reorg: "Don't trash anything that is not a duplicate. So like you have that MyDrive route, there is a folder, legal opinion, Ranka OSS, land partners, Sabhanapalli land partners, legal opinion for survey number in MyDrive route, which you confirm is a duplicate, same MD5, only then trash it."

**Rule:** Trash ONLY files that have a verified same-MD5 counterpart in the correct destination. Even if a file looks redundant (e.g. unsigned 2024 opinion for same survey as new signed 2025 opinion), prefer to **leave it as historical record** unless the user explicitly says to remove it.

## Drive folder locations (Jul 2026 snapshot)

| Project | Folder path | Folder ID |
|---|---|---|
| Ranka Oasis / SLP (root) | `My Drive / Sevaganapalli Land Partners` | `104VWF9-XdeLX612NjHE9s2-92KTpmz77` |
| Ranka Oasis → Legal Opinions | `Sevaganapalli Land Partners / 01_Legal_and_Title_Docs / Legal Opinions` | `1JVVcYPZDuPR9GyAVIwmiZpWiJzWw0FnX` |
| Ranka Udaya / DRA Thindulu (root) | `My Drive / Ranka Udaya (DRA Tindlu Land partners Master Folder)` | `10sk0X6dq9-Rzo2BajJKNFkEts_pfRxLT` |
| Ranka Udaya → Legal Reports | `Ranka Udaya (DRA Tindlu Land partners Master Folder) / Legal Reports` | `1gfmcuREMa5zaCRddwXWl0zXZh9rXhfg5` |
| TMP / Temp (staging) | `My Drive / TMP` | `18p74II2uL32sNDzDDwWzmlOUdJJOTmE-` |

## Naming convention for filed opinions

```
YYYYMMDD <Lawyer> <DocType> <Project> <SurveyNos> [<Coverage>] [<Status>].pdf
```

Examples (from the Jul 2026 Sevaganapalli reorg):
- `20240921 legal report K Velayudham for Sy No 240-3 (Vendor Side - Subba Reddy Heirs).pdf`
- `20251213 Jeevanandam Legal Opinion Sevaganapalli SLP 7.51 Acres Signed Sealed.pdf`

**Date source:** the opinion's own date (not the upload date). If the opinion is dated 2025-12-13 but the user shares it on 2026-07-13, use `20251213` in the filename.

**Status tags:** `Signed`, `Sealed`, `Signed Sealed`, `Vendor Side`, `Acquirer Side`, `Draft`. These tags disambiguate when multiple opinions for the same survey exist.

## Pitfalls

- **The lawyer is NOT a project indicator.** Hosur advocates (Velayudham, Jeevanandam, N. Manjunath, J. Sudha Reddy, CMS IndusLaw) routinely issue opinions for multiple unrelated projects. "Velayudham opinion" could be for 240/3 (DRA Thindulu) or 158/1 (Ranka Oasis) — classify by survey number, not lawyer.

- **Multiple parties on the same survey ≠ duplicate.** A vendor-side opinion (Subba Reddy heirs) and an acquirer-side opinion (DRA Thindulu + DRA Realty) cover the same Sy.No.240/3 but from different sides of the transaction. KEEP BOTH. The "(Vendor Side)" and "(Acquirer Side)" filename tags make the distinction explicit.

- **Scanned legal opinions in Drive often have NO text layer.** A 27-page Jeevanandam opinion returns 0 chars from `pdftotext`. Don't assume the file is empty or broken — it's just scanned. OCR with `ocrmypdf --sidecar` for the first/last 2 pages only.

- **Notary Public seal vs. Advocate stamp is a real legal distinction.** A "Notary Public" has been appointed by the Government of India (Roll No shown on letterhead) and has authority to administer oaths, attest documents, and provide certified copies. An "Advocate" is a court lawyer. For title opinions used in property transactions, a Notary Public seal is what makes the opinion legally admissible as evidence. Don't conflate the two when deciding supersession.

- **Existing "Legal Opinions" folders often have stale names.** The SLP folder was named "Legal Opinions" with one trailing space. Don't trip on whitespace when matching folder names.

- **The Drive's `files().list` `parents='X' in parents` query is unreliable** (known quirk, see `gws-automation` skill → "Pitfall — `parents='FOLDER_ID' in parents` returns 0"). If listing a known folder returns 0 results, use full-text search across all of Drive instead. The folder ID is correct; the query syntax is buggy.

- **MD5 comparison only works for binary files (PDF, DOCX, etc.).** Google-native Docs/Sheets/Slides have no MD5 — they can only be compared by name. Tag native files as "Google-Doc" in any duplicate-detection table.

- **Don't conflate "Serenity Estate" with "Serenity Hill View" / "Serenity Hillview".** "Serenity Estate" is the legacy name for Ranka Udaya 240/3 project (deprecated, user wants it removed). "Serenity Hillview" is a separate 2026 project with its own folder tree. Treat them as completely unrelated.

- **When trashing, use `files().update(body={'trashed': True})` not `files().delete()`.** The former moves to Drive Trash (recoverable for 30 days). The latter is permanent and irreversible.

- **ID truncation kills you.** When printing file IDs for readability (`f.get('id')[:25] + "..."`), the truncated form is not usable in subsequent API calls. Always preserve the full ID in a variable, never inline-truncate.

- **See also:** `document-receipt-naming-filing.md` (for receiving new documents from counterparties), `savaganapalli-ranka-oasis-case-cluster.md` (project-specific context), `drive-duplicate-analysis-workflow.md` (broader Drive-wide duplicate detection patterns).
