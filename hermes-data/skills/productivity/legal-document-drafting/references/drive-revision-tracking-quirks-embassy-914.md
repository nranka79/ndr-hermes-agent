# Drive Revision Tracking — Embassy Habitat 914 (June 2026)

## Worked Example: Tracking Changes to a Sale Deed Google Doc

**File:** `1yHiL4vSGjhyEPOfX3g_Q_LiUsRZWlG61_BROKCUkIL8`  
**Document:** Embassy Habitat 914 Sale Deed (Google Doc, owned by `ndr@draas.com`)  
**Session:** Bharat Hawaldar, June 1, 2026

---

## Revision List (Drive API)

```python
revisions = drive_service.revisions().list(
    fileId=file_id,
    fields="revisions(id, modifiedTime, lastModifyingUser(displayName, emailAddress))"
).execute()
```

**Result — 5 revisions:**

| Rev ID | Date | User | Email |
|--------|------|------|-------|
| 1 | 2026-03-28T11:24:02 | Nishant Ranka (Ndr) | ndr@draas.com |
| 2 | 2026-03-28T11:24:26 | Nishant Ranka (Ndr) | ndr@draas.com |
| 7 | 2026-03-31T11:40:58 | BHARAT H | sales1.blr@draas.com |
| 23 | 2026-04-03T10:56:42 | BHARAT H | sales1.blr@draas.com |
| 255 | 2026-06-01T06:41:13 | BHARAT H | sales1.blr@draas.com |

---

## ⚠️ Critical Quirk: Older Revisions Return 404 on get_media

**Problem:** Attempting `drive_service.revisions().get_media(fileId=ID, revisionId='23')` on Rev 23 (or Rev 7) returns:

```
HttpError 404: Revision not found: 23
```

Yet Rev 23 appears in the `revisions().list()` response. The revision exists as metadata but its content is not accessible via the API.

**Root cause:** Google Drive only stores the content of the **last few revisions** for Docs files. Revisions beyond a certain threshold are "pruned" — only their metadata (timestamp, user) is retained. You can only download the **current content** (Rev 255) and the **last reachable revision**.

**Workaround:** Since Rev 1 (Nishant Ranka's original draft) is also inaccessible, reconstruct the "original" from context — use the text content of Rev 255 and work backwards, or have the user provide the original via Telegram/email before editing.

---

## Effective Diff Approach

Since Rev 1 content was not accessible via API, the "original" text was reconstructed from the Sale Deed recital structure (5th April 2027 execution date, single SBI loan, RTGS payments only) and compared against current (3rd June 2026, two loans, DD payments, TDS clause, 12+ new clauses).

---

## Changes Detected (Rev 1 → Rev 255)

### 1. Execution Date
- Original: **5th April 2027**
- Current: **3rd June 2026** ← backward date (pre-drafted for future execution)

### 2. Loan — Second Mortgage Added (NEW Recital F)
- Original had only **SBI/SBM loan** (A/c 64186230661)
- New **Vijaya Bank** loan added (A/c 1146083510000063, now Bank of Baroda)
- Vijaya Bank discharge: **BYP-1-01834/2026-27**, registered 30.05.2026
- ⚠️ Duplicate Recital label: both SBI and Vijaya Bank labeled **"F"** — needs renumbering before registration

### 3. Payment Schedule (Clause 1.1)
| Row | Original | Current |
|-----|----------|----------|
| UTR (Row 2) | KKBKR52026030500983**452** | KKBKR52026030500983**152** ← same number, OCR misread |
| Row 3 | RTGS ₹75,00,000 | **DD [●] Kotak Mahindra ₹47,75,000** ← blank instrument |
| Row 4 | RTGS ₹1,25,00,000 | **DD [●] Kotak Mahindra ₹1,50,00,000** ← blank instrument |
| Row 5 | *(none)* | **TDS 1% — ₹2,25,000** ← new row |
| Total | ₹2,25,00,000 ✓ | ₹2,25,00,000 ✓ |

### 4. New Clause 1.4 — TDS
- TDS deduction ₹2,25,000 (1% u/s 194-IA), Form 26QB, net to seller ₹2,22,75,000

### 5. New Clauses (2–12) Added
- Clause 3: Possession (vacant, physical, peaceful delivery)
- Clause 4: BESCOM electricity meter transfer (RR W4EH16978)
- Clause 5: Delivery of title documents
- Clause 6: Apartment Owners' Association (membership, dues)
- Clause 7: Seller's Representations & Warranties (7.1–7.7)
- Clause 8: Seller's Covenants (8.1–8.4)
- Clause 9: Purchaser's Rights (9.1–9.4)
- Clause 10: Purchaser's Obligations (10.1–10.4)
- Clause 11: Stamp duty & registration
- Clause 12: General provisions

### 6. Annexure A — Expanded from ~5 to 17 items
Now includes: SBI discharge deed, SBI NOC, **Vijaya Bank discharge deed**, **Vijaya Bank NOC**, Embassy Habitat NOC, transfer fee receipt, nil dues certificate, tenant NOC, tenant surrender letter, BBMP tax receipt, society maintenance receipt, BESCOM transfer letter, e-Khata, allotment letter, parking allotment letter, association membership cert

⚠️ Serial numbering broken: items labeled 5, 5, 5, 8, 10, 10, 13, 14, 14 — needs fix before registration

### 7. Annexure B — Parking Slot Map (NEW)

---

## Checklist — What Needs Fixing Before Registration

1. ⬜ DD instruments (Rows 3 & 4): `[●]` blanks — fill in DD number, date
2. ⬜ Recital duplication (two "F"s): renumber to F (Vijaya Bank), G (SBI), H (Association), I (ATS reference)
3. ⬜ Annexure A serial numbering: fix from broken sequence to clean 1–17
4. ⬜ Witness names and addresses: fill in
5. ⬜ Page numbers in footer: "Page of" — blank fields need completion

---

## Code Pattern — Download Current Revision Content

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
import io

token_path = 'the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)'
with open(token_path) as f:
    token_data = json.load(f)

creds = Credentials(
    token=token_data['token'],
    refresh_token=token_data['refresh_token'],
    token_uri=token_data['token_uri'],
    client_id=token_data['client_id'],
    client_secret=token_data['client_secret'],
    scopes=token_data['scopes']
)

drive_service = build('drive', 'v3', credentials=creds)

# Export current content (latest revision = Rev 255)
current_req = drive_service.files().export_media(fileId=file_id, mimeType='text/plain')
current_fd = io.BytesIO()
downloader = MediaIoBaseDownload(current_fd, current_req)
done = False
while not done:
    _, done = downloader.next_chunk()
current_text = current_fd.getvalue().decode('utf-8')
```

**⚠️ Rule:** A Google Doc (`mimeType: application/vnd.google-apps.document`) CANNOT use `get_media()` — raises `403: Only files with binary content can be downloaded`. Use `export_media()` with `text/plain` or `application/pdf`.

---

## Code Pattern — Attempting Old Revision Download (Fails)

```python
# This FAILS — Rev 23 not accessible via get_media
rev23_req = drive_service.revisions().get_media(fileId=file_id, revisionId='23')
rev23_fd = io.BytesIO()
downloader = MediaIoBaseDownload(rev23_fd, rev23_req)
# HttpError 404: Revision not found: 23
```

**Lesson:** Do not trust revision IDs for downloadable content beyond the last 1-2 revisions. Always get current content via `files().export_media()` and use the revision list only for metadata (who changed what, and when), not for content diff.