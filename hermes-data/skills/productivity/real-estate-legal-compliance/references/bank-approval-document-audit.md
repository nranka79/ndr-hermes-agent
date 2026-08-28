# Bank Approval Document Compliance Audit

**Trigger:** User forwards an email from a bank (ICICI, SBI, HDFC, Axis, etc.) listing documents required for project APF/construction finance approval. Task is to check what's available in Drive against the bank's list and produce a gap analysis.

## Workflow

### Phase 1: Capture the Bank's Requisition List

1. **Read the full email thread** — the bank's original email often contains the property description (khatha/survey number, village, taluk, extent). Capture these details — they identify which variant of "Ranka North Star" documents to search for.

2. **Extract every checklist item** — number them. Banks often mix specific registered-document references (e.g., "Will registered as Doc No. 46/1981-82") with generic document types (e.g., "BESCOM NOC"). Keep the bank's exact wording.

3. **Note the property identifiers** — from the bank's email:
   - Khatha / PID number
   - Survey number(s)
   - Village, Hobli, Taluk
   - Total extent
   - Project name (as the bank spells it — may differ from internal DRAAS folder name)

### Phase 2: Search Strategy

**Search approach** — run two parallel passes:

#### Pass A: Search by Document Type (per checklist item)

For each item on the checklist, search Drive with the document type term (e.g., "RERA", "BESCOM", "BWSSB", "tax paid", "fire NOC", "encumbrance"). Use `gws_auth.build_service('drive', 'v3')` directly (not `gws_skill_bridge`) to avoid the SimpleNamespace parameter bug.

For each term, search:
1. **Project-specific** — `name contains '<term>' and name contains '<project_name>' and trashed=false`
2. **General** — `name contains '<term>' and trashed=false` (catch documents not labeled with project name)

#### Pass B: Inspect the Project's Document Folders

Not all relevant documents have obvious filenames. List the contents of every project-related folder:
- Main project folder
- Legal docs folder
- Approval folder (often has RTCs, MRs, khata, tax receipts, akarbandh)
- Sanction Plan folder
- Land Owner subfolders
- Any folder with "approval", "document", "legal", or the project name

### Phase 3: Classification

| Status | Meaning | Example |
|--------|---------|---------|
| ✅ **Found** | File exists in Drive, clearly matching | `current TAX PAID RAnka north star allasandra.pdf` for "Tax Paid 2026-27" |
| ⚠️ **Needs Verification** | Exists but needs checking — wrong date, expired, partial, wrong survey | 2015 Fire NOC when bank asked for current; re-grant cert with different ref |
| ❌ **Missing** | No trace anywhere in Drive for this project | Death Certificate of Melda Hanumaiah |
| ❓ **Unclear** | Similar files exist but for OTHER projects, not the target | BESCOM NOC found for Amber but not North Star |

### Phase 4: Deeper Verification for ⚠️ Items

Check:
- **Expiry dates** — Fire NOCs, Height Clearance NOCs, pollution consents (2015 doc likely expired)
- **Document registration numbers** — "Will Doc No. 46/1981-82" ≠ re-grant cert with different ref
- **Survey number** — Bank asked for Sy 14/1; found RTC may be for Sy 93/2
- **Project name** — "BESCOM NOC Ranka Amber" ≠ "BESCOM NOC Ranka North Star"
- **Date range** — EC "1969-1989" ≠ found EC covering "2004-2025"

### Phase 5: Report Structure

1. **Summary table** — every item with status + one-line explanation
2. **Key gaps** — critical missing items (blockers for bank approval)
3. **Expiring items** — near-expiry / renewal-needed documents
4. **Recommendations** — what to tell the project coordinator

Lead with the table. Expand only on gaps. Don't repeat the bank's full email.

## Common Pitfalls

- **Project name ambiguity** — Bank may spell differently ("RANKA NORTH STAR") than Drive folders ("Ranka North Star", "North star Documents"). Search ALL variants.
- **NOC validity** — Banks require current NOCs (issued within 1-3 years). Flag old ones.
- **Same doc type, different project** — KSPCB/BESCOM/BWSSB files may exist for other DRAAS projects but NOT for the target. Verify project association.
- **Re-grant/conversion orders are document-number specific** — Different reference number = different document. Classify as ⚠️ or ❌.
- **Encumbrance Certificate date ranges** — Bank specifies two periods. A single general EC covering neither is insufficient.
- **Death certificates of specific individuals** — May not have the name in filename. Search by given name AND surname separately.
- **gws_skill_bridge fails for drive_search** — `call('drive_search', ...)` raises `AttributeError: 'SimpleNamespace' object has no attribute 'raw_query'`. Use `gws_auth.build_service('drive', 'v3')` directly.

## Verified Example: ICICI Bank — Ranka North Star (Jul 2026)

**Property:** Sy.No. 14/1, Allalasandra Village, Yelahanka Hobli, Bangalore North — 1 Acre 8½ Guntas

| # | Item | Status | Notes |
|---|------|--------|-------|
| 1 | RERA Certificate | ❌ | Not found for North Star |
| 2 | Tax Paid 2026-27 | ✅ | `current TAX PAID RAnka north star allasandra.pdf` |
| 3 | KSPCB Consent | ❌ | Not found for North Star |
| 4 | SEIAA NOC | ❌ | Not found for North Star |
| 5 | BESCOM NOC | ❌ | Not found for North Star |
| 6 | BWSSB NOC | ❌ | Not found for North Star |
| 7 | AAI Height Clearance | ✅ | `GFTS Jakkur Height Clearance NOC` |
| 8 | Fire NOC | ⚠️ | Found but dated 2015 — likely expired |
| 9 | Building License & Plan | ⚠️ | DWG plans exist; sanctioned license unclear |
| 10 | Relinquish deed | ⚠️ | Found for other properties, not Allalsandra NS |
| 11 | RTC 2018-2026 (Sy 14/1) | ✅ | `RTCs (1).pdf` in approval folder |
| 12 | Re-grant order HOA 83/68-69 | ⚠️ | Different ref: LNDPR 71/65-66 |
| 13 | Will 46/1981-82 | ⚠️ | Wills exist but not verified for this number |
| 14 | Death Cert — Melda Hanumaiah | ❌ | Not found anywhere |
| 15 | MR 36/1980-81 | ⚠️ | `MRs (1).pdf` exists — needs page-level check |
| 16 | Rectification deed 1088/2014-15 | ⚠️ | One rect deed from 2013 exists |
| 17 | Rectification deed 1069/2014-15 | ⚠️ | Same as #16 |
| 18 | Conversion order 06/01/2018 | ❌ | Specific number ALN(NAY)SR/60/2016-17 not found |
| 19 | Sharing agreement | ✅ | JDA + Profit Share Agreement exist |
| 20 | EC 1969-1989 | ❌ | Not found for this period |
| 21 | EC 2020-till date | ❌ | Not found for this period |
