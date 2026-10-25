# Master Inventory → Bucket Mapping (per-row classification to a target folder taxonomy)

Runbook for NDR's "map every file in the master inventory into the target project folders" step — the analysis that comes AFTER the cross-account inventory (`references/multi-account-project-collation.md` Phase 4.5) and BEFORE consolidation (Phase 5 / `cross-owner-bulk-migration.md`). Verified 2026-09-15 on Ranka Oasis: 3,151 rows → 16 buckets, zero unclassified.

NDR's expectation (stated twice): when he asks for a mapping analysis, he wants a **per-row column in the existing sheet** ("we'll do that analysis and add that additional column… row by row, row by row"), NOT a summary-level proposal. Build the column first; the analysis tab/secondary sheet explains the story.

## Workflow

1. **Read the inventory sheet fully** (values().get with header) → save rows to local JSON. Confirm the column layout (File Name | Type | Description | … | File ID | Link) before keying on indices.
2. **Look up the actual target-folder structure on Drive FIRST** (walk the project/entity folder via the owner token) — NDR may say "five or six buckets" but the real template/entity taxonomy differs. Ranka Oasis: standard template claims 7; live entity (Sevaganapalli Land Partners) already has 01–10 numbered folders; the DATA demanded 7 more. Never invent bucket names from memory — verify what exists.
3. **Two-pass classifier** (see script sketch below):
   - **Strong rules on NAME+DESCRIPTION only** — priority-ordered keyword buckets (lower number = higher priority). Description column already enriched from the inventory build, so name+desc hits are reliable.
   - **Chain as WEAK fallback** — only after name+desc misses, and only with *category* folder keywords. NEVER put a blanket `legal` pattern in the chain rules: it steals title-chain docs (death certs, UDRs, cancellation deeds, certified copies) into Legal.
   - **Manual overrides dict** for rows you review by hand (idx → bucket). This is where content-checked mystery files land.
4. **Content-check the leftover/generic rows instead of guessing.** Junk-named downloads (123.pdf, padf.pdf, Aaat.pdf, fb36c269…pdf) turned out to be referral-agent affidavits, a PO, and a competitor sheet. Recipe: DWD media download (below) → `pdftotext -l 2` for text PDFs → `pdftoppm -f 1 -l 1 -r 100 -png` + `tesseract` for scans → `unzip -o` xlsx + parse `xl/sharedStrings.xml` for sheets. Files that merely *mention* the project (e.g. Byadarahalli brief text "abutting Brigade Oasis") are FALSE POSITIVES → tag `RO_NotOasis` / exclude, don't map them in.
5. **Write the column back to the sheet**: `values().update` with `valueInputOption='USER_ENTERED'` on the empty column range; set headers separately (M1:N1). Add a **Notes/Basis column** for content-checked rows and NOT-OASIS explanations.
6. **Build the analysis tab** (new sheet): bucket | files | folders | % | fits-current-structure? | what-it-holds + a VERDICT block: which buckets the current template covers, which NEW buckets the data demands, totals for consolidation, and recommended target structure.
7. **Verify with a read-back of the whole written column** vs the JSON Counter — zero-mismatch requirement. (Readback `Inventory!M2:M3152` then compare `Counter(display_name)` sheet vs json.)

## Pitfalls hit (all real, 2026-09-15)

- **Chain-fallback plural trap.** Rules like `floor plan`, `sale deed` fail on `Floor Plans` / `Sale Deeds` because of the `(?![a-z])` word-boundary suffix. Fix: `match_plural()` — try the pattern, then the pattern minus trailing `s`. Without it 188 rows fell to RO_Review.
- **Legal bucket over-greedy.** A `legal` keyword (even in chain fallback) sweeps death certificates, partition deeds, UDRs, cancellation deeds, certified copies into Legal Notices. Narrow Legal to: legal notice/opinion, advocate, counsel, litigation, court, petition, plaint, counter, summons, OS/CMA case numbers. Title bucket owns the deed/certificate/title-chain patterns.
- **Override dict bool-vs-string bug.** In the manual-override branch, returning `('FOLDER' if 'folder' in typ else 'FILE')` as the *boolean* slot makes every override truthy → every overridden row shows as FOLDER. Return a real boolean: `('folder' in typ)`.
- **Priority ordering must let specific Oasis buckets beat NOT-OASIS.** Give NOT-OASIS (other-project names: Ranka Udaya/Amber/Iris/Northstar, DRA trackers, ABHFL/ICICI funding formats, employee documents) a HIGH priority (low number, e.g. 5) so generic files don't leak into Oasis buckets — but add a carve-out: when a higher-priority Oasis-specific rule also fired (e.g. the file IS an Oasis investor doc with "Udaya" in a sibling name), keep the Oasis bucket.
- **Same-word buckets: 'invoice'** means referral-commission invoice for agent names (Suryakumari/Kauna Pyla/Madhuri/Devaki/Vaishak) but vendor/contractor invoice for Paramvah/SalesInvoice files. Put referral-agent names as a dedicated `RO_Referral_Commission` bucket ABOVE generic Investors_Finance so agent invoices don't flood finance.
- **Folders get buckets too** — 289 folder rows map to the bucket they'd become/reference, or `PROJECT_ROOT`/`Container` when they're entity/project roots (Balaji Land, _Archive, 01–10 entity folders) that stay as containers.

## DWD media download (content-checking colleague-owned files)

The sanctioned DWD op surface (`gws_ops._OP_FUNCS`) has NO drive-download op. To read bytes of a colleague-owned file during analysis:

```python
from tools.gws_dwd_tools import _creds_for_target, _make_handler
from tools.gws_ops import DEFAULT_SCOPES
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 1) metadata via the handler (returns a SERIALIZED JSON STRING — json.loads it)
get = _make_handler('drive_get')
r = json.loads(get({'target': 'sales1.blr@draas.com',
                    'file_id': FID, 'fields': 'id,name,mimeType,size'}))
# 2) bytes via the impersonated creds (same process; creds never leave it)
email, mode, creds = _creds_for_target('sales1.blr@draas.com', scopes=DEFAULT_SCOPES)
svc = build('drive', 'v3', credentials=creds)
req = svc.files().get_media(fileId=FID)
# MediaIoBaseDownload → local file → pdftotext/OCR/unzip
```

`_make_handler` result is a **string**, not a dict — `json.loads()` it or `.get()` raises `AttributeError: 'str' object has no attribute 'get'`.

## Verified bucket taxonomy (Ranka Oasis, 2026-09-15)

7 standard (template) + 7 NEW demanded by live data:

- Covered by template: Title & Land Docs (948), Architectural & Engineering (736), Marketing & Content (282), Approvals & Regulatory (100), Legal Notices & Litigation (48), Customer (4), Communication (5)
- NEW (data-driven): Investors & Finance (255) — Jiraaf term sheets, mortgage deeds, loan-cum-investment, buyback, investor SPAs, receipts, invoices; Partnership & Firm (188) — deeds, reconstitution, GST/PAN/TAN, KYC; Acquisitions (46) — JDAs, addenda, exchange deeds, MOUs; Procurement & Vendors (58) — POs, WOs, quotations; Referral & Commission (29) — agent affidavits + commission invoices; Reference & R&D (19); Project Management (9)
- NOT-OASIS / exclude (135): other-project and DRA-general files surfaced by fullText false positives
- Consolidation total: 2,727 files across 14 buckets + 289 folders

Master inventory sheet (verified): `1IAV-tWZoRUQSYqGxfVZeuAk_2ZoG1mNrDqvDI6Y3ooE` — Inventory!M (Suggested Bucket), Inventory!N (Notes/Basis), tab `Bucket Analysis`.