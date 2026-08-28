---
name: draas-drive-organization
description: "DRAAS Drive folder structure, project document workflows, and file management patterns — TMP → project folders, permission quirks, cross-account handling."
version: 1.0.0
author: Hermes (DRAAS)
---

# DRAAS Drive Organization

Drive management conventions specific to DRAAS: how projects are organized, where writable vs read-only copies live, and how to move files from TMP into their final project locations.

## Reference Material

- `references/drh-dra-prime-partners-context.md` — DRH&I / DRA Ranka Holdings / DRA Prime Partners filing context: folder map + IDs (partnership docs, GST cert, PAN), the DRA Finance & Investment → DRA Prime Partners rename thread, loose-at-root deeds, proposed resolution filename
- `references/rlda-blr-cant-project-context.md` — RLDA Bangalore Cantonment (BTPL redevelopment) context: BLR CANT folder IDs, the BTPL→RLDA draft-letter exchange history (2025-05-25 → 2026-08-17, with Drive IDs — several revised letters sit in My Drive root, not BLR CANT), key facts/timeline (FAR 5 chain, BHS declaration/withdrawal, WP 38186/2025, lease-clock clauses), letter naming convention, and the docx text extraction recipe (zipfile + regex on word/document.xml, python-docx not installed)
- `references/rrp-vs-spv-os553-case-context.md` — RRP vs SPV OS 553/2023 litigation context: case folder & index IDs, order chronology, partnership-deed status (deed NOT on court record despite plaint's "Annexure A" claim; s.69 exposure), deed file locations on Drive
- `references/drive-rename-move-pattern.md` — Combined rename + move in one `files().update()` call (avoids separate operations)
- `references/litigation-case-folder-filing.md` — Filing court documents into litigation case folders: numbered-prefix `NN_Description` naming (NOT YYYYMMDD), duplicate-detection workflow against already-filed scans (pdftotext → pdftoppm + tesseract), and the O.S.No.553/2023 RRP vs SPV worked example (folder IDs, document index sheet, orders status)
- `references/permission-patterns.md` — Known Drive permission quirks: DRA Projects vs shared drive, external folder ownership, capability inspection
- `references/tmp-to-project.md` — Complete workflow for moving a file from TMP to a project Customer Documents folder
- `references/bulk-upload-tmp-skip-existing.md` — Bulk upload of a downloaded bundle (RERA plans, doc sets) to a TMP subfolder: skip-existing-by-name so re-runs are idempotent, clean `NN_desc.pdf.pdf` double-extension names, verify count from Drive (not local), deliver folder link + key-doc links. Use for "upload everything to TMP and give me links".
- `references/document-version-chronology.md` — Building a timeline from Drive metadata (createdTime, modifiedTime, owners) to spot version mismatches between plans, inventory sheets, and layout drawings across different accounts
- `references/dtlp-project-structure-and-upload.md` — DRA Thindulu Land Partners (DTLP) numbered-subfolder taxonomy (01_Title…06_Customer), plus the full terminal()-based upload workflow with anyone-link and collaborator permissions
- `references/bulk-file-naming-standardization.md` — Bulk analysis and renaming of Drive files following a convention: discover folder → list files → identify issues (broken extensions, typos, casing, duplicates) → propose standardized names → JSON mapping → rename after approval
- `references/global-dated-sweep-rename.md` — "Rename EVERYTHING we prepared in the last week per our naming convention" sweep ACROSS all folders/incl TMP: query `createdTime >= X and 'me' in owners`, scope decision table (rename docs/artifacts, skip folders/media/other-owners' files), one-pass rename preserving doc IDs/links, deliver summary. Use when the user demands execution (not a review-gated proposal).
- `references/colloquial-property-name-search.md` — Finding properties on Drive by colloquial name via family settlement document cross-reference (DR Schedule A&B, Global Settlement, DR Will)
- `references/property-maintenance-fixtures.md` — Documentation workflow for appliance/fixture issues in leased properties: repair-vs-replace analysis, fit check, price research, Drive folder structure for Fixtures & Fittings, HTML report template with embedded Drive images
- `references/kml-mymaps-export-upload.md` — KML/MyMaps deliverables: where research KMLs live locally (`/data/hermes/output/<project>/`), fast lookup order (scope → local glob → Drive query → upload if missing), upload pattern with KML/KMZ mimetypes + anyone-reader, and the user-frustration pitfall (deliver links quickly in code blocks; don't expand into trash/cross-account audits)
- `references/zip-extract-upload-share.md` — Zip archive processing pipeline: download large zips from TMP → extract → create structured project subfolder → bulk upload with correct MIME types → set team/anyone permissions → create threaded email draft with Drive link. Covers the Godrej BuxRanka 4.5 FAR plan submission pattern.
- `references/kml-mymaps-reorganize.md` — Reorganize/dedupe/filter a Google My Maps via its KML export: fetch with `forcekml=1`, dedupe by identical coords + normalized name (keep priced copy), classify SUBJECT/PREMIUM/INFRA/REMOVE, rebuild layered KML preserving Styles, upload KML+KMZ; also re-adding deck projects with deck pricing. ElementTree `findtext` namespaces-kwarg pitfall.
- `references/apf-checklist.md` — (absorbed from apf-checklist skill, 2026-08-16) Fill the Axis Bank APF (builder login) document checklist for DRA projects as a marked PDF: marking scheme (green/amber/white), bank template structure (Title / Region Specific / Plan-Approvals / Other Documents Sr numbering incl. 12.1-12.3 sub-items), known projects (Ranka Amber — DRA Realty; Ranka Udaya — DRA Thindlu Land Partners), reportlab build + pdftotext verification, string-vs-int Sr set pitfall.
- `references/slides-embed-interactive-map.md` — Embed a My Maps into a Google Slides deck when the Slides API is disabled: clean embed-URL screenshot (not viewer), python-pptx slide add + `pic.click_action.hyperlink.address`, Drive PPTX→Slides import, and post-conversion verification of the external link in slide rels.
- `references/mymaps-clean-reorganize.md` — Restructuring a Google My Maps KML: download via `maps/d/u/0/kml?mid=...&forcekml=1`, parse (ElementTree `namespaces=` kwarg trap), dedupe by coordinates + name, classify projects/infrastructure/subject land, drop non-premium, rebuild KML preserving Style elements, add projects from a Slides deck (PPTX → slide XML → pin descriptions), KMZ build + upload. Use for "separate the projects, remove repeated/non-premium" and "add the projects from this deck into my map".
- `references/mymaps-clean-reorganize.md` — My Maps cleanup/reorganization: export a shared map via `kml?mid=...&forcekml=1`, ElementTree `namespaces=` kwarg pitfall, coordinate-based dedup, premium classification (≥Rs 5k/sqft or premium brand), KML rebuild (copy Style elements, deepcopy placemarks), Drive upload + import instructions. Use when Prakash says "separate the projects, infrastructure", "remove repeated/non-premium pins" on a My Maps link.
- `references/project-finance-dataroom.md` — Build a bank/project-finance dataroom spreadsheet: company profile, promoter KYC, entity KYC, required-document checklist, per-project document inventory with multi-HYPERLINK formula technique (`link_multi()` with `& CHAR(10) &`), Drive folder discovery, and section-based layout.
- `references/project-noc-approval-lookup.md` — "Do we have the <dept> NOC for <project>?" workflow: search by project + NOC type, parent-chain verification (generic dated NOC PDFs repeat across projects!), NOC index spreadsheets, PDF text verification, Gmail renewal sweep. Includes Ranka Northstar KSPCB/BWSSB/AAI/BESCOM/Fire inventory with file IDs.
- `references/buxranka-brdpl-project-context.md` — BuxRanka / BRDPL Hudson Circle (Godrej JV) context: folder IDs, the two modified-approvals cost sheets (official charges vs liaisoning), the Godrej email thread + participants, and the rename → file → reply-all-with-attachment pattern.
- `references/insurance-policy-details-lookup.md` — "find insurance policy <number> in my emails/drive — full details + registered email": exhaustive search order (exact → variants → Drive fullText → sessions → family), authoritative sources (policy bond PDF via pdftotext carries the registered email), the Life_Policy_Payment_Tracker cross-check, and zero-hit reporting.
- `references/locating-research-across-data-estate.md` — "find the research/records for <land parcel>" / "did I email X about Y": search ladder (sessions → Gmail variants → Drive fullText + parent chains → Kelsa DRA pipelines → gbrain), interpretation rules (missing email = verbal assignment → draft follow-up; survey PDF is the top artifact), and the Siddhapura/Prestige GreenMore worked example (Sy 27/2+27/3, ALOK/PUTTARAJU owners, Sri Ranganatha Nursery, LaraTech survey).
- `references/email-attachment-to-drive-filing.md` — "give me that Word doc from the email with <advocate> re <matter>": locate thread by case no (side-threads have different subjects), walk parts for the attachment, download via attachments().get, verify docx content (zipfile + strip tags) BEFORE delivering, check Drive for existing FILLED/SIGNED versions before uploading, upload native docx with descriptive name, file in the matter folder (DR ITAT map incl. the giving-effect-order letter worked example with thread 19f3b09fb55511df), deliver link + MEDIA copy; vision_analyze-rejects-PDF pitfall.
- `references/requisition-list-to-checklist-sheet.md` — advocate's Word "requisition list" (docs to be procured per survey number) → survey-wise Google Sheets checklist (Survey Number | Document | Priority | Status), filed in the project folder, then a threaded draft email to the assigned colleague with the original forwarded + docx attached + sheet link. Covers voice-name mapping (Prasannakumar→Prasanna Swaminathan, Katnalli→Katenahalli, "Rahul"=Vinod Kumar Das), lxml body-order table parsing incl. multi-survey blocks (125/2-5), existing-tracker check, and the icloud non-Google invite 400 pitfall (anyone-link fallback). Validated 2026-08-25 (Katenahalli V2, 24 tables → 46 rows).
- `references/pscp-kingfisher-towers-context.md` — PSCP folder ("PSC Prestige South City", My Drive root): contents (Hermitage, Golfshire, PrestigeGreenMore, KFT files), and the Kingfisher Towers Flat 14A title chain (UB Factory → UB Holdings → Prestige JDA 2010 → Lakshmi Singh 2017 → Dinesh Ranka confirming → Rahul Ampally 2021) with filing-naming convention.
- `references/folder-index-spreadsheet.md` — Build a per-category spreadsheet index of a Drive folder (one sheet per survey number/project, Sl No / Category / File name / Drive link / Date). Covers the psingh identity override (`HERMES_SESSION_USER_ID=psingh` + explicit `service_name='google-draas'`), thread-local services for parallel large-folder walks (shared service → SSL RECORD_LAYER_FAILURE), survey-number name normalization, and the 90-sheet creation/formatting pattern (chunked batchUpdate, fetch sheetIds after addSheet).
- `references/project-checklist-categories.md` — Per-project "Documents Checklist" workflow (one spreadsheet, one tab per project, NO summary tab — Prakash's hard rule). FLAT date-sorted layout (NOT section-header bands — user corrected 2026-08-13): Category column + per-category row colors, all docs old→new. Covers the category keyword classifier with ordering rules (LAND before REV, FIN before APPROVAL, `\b` word boundaries for firm keywords, `(?<![a-z])ec(?![a-z])` for ECs), filename document-date extraction, parent-folder discovery when the shared link is a "Master data" container, the `updateBorders` `color`-not-`colorSpec` pitfall, the STALE MERGES silent-value-swallow pitfall (recreate fresh, don't reuse formatted sheets), and date-order verification via sort_key not display strings.\n- `references/filename-document-table-parsing.md` — Successor format (2026-08-13): parse STRUCTURED columns out of renamed filenames — `SL NO | Sy NO | DOCUMENT DATE | DOCUMENT NUMBER | DOCUMENT TYPE | PARTIES (from and to) | DRIVE LINK`, date-sorted, multiple survey numbers listed on continuation rows below the same Sl No. Full extraction pipeline: survey normalization (4-digit surveys 1508/1, comma-as-separator NOT terminator, paren lists, shorthand `158/1C3,5,6` → 1C3/1C5/1C6, p.no page-number junk drop), EC-first-year vs others-last-year date fallback, doc-number patterns, type-ordering traps (survey sketch before sale deed), party extraction (between-X-and-Y-without-to, `_to_` FormII, NO_PARTIES_TYPES skip set). ALWAYS re-walk folders first (user renames files between requests).
- `references/survey-wise-docx-index.md` — Survey-no.-wise Word doc index: extract Indian survey numbers from filenames (SyNo, FMB, Patta, UDR, EC) → group by survey → Word doc with tables. Reusable script: `scripts/survey-wise-index.py <FOLDER_ID> <out.docx>`.
- `references/sale-deed-transaction-summary.md` — Extends folder-index-spreadsheet: classify deed files by filename (SALE DEED / ATS / GPA, FY from doc numbers), batch-OCR every PDF in a background job, parse parties/transaction-date/survey-numbers from OCR text, and build a per-document "Transaction Summary" tab. Includes the Bestamanahalli worked example (folder IDs, spreadsheet IDs, Sanchaya aggregation chain) and pitfalls (form-header date stamp 09-05-2003, pdftoppm zero-padded page globs, string Sl No int() cast).
- `references/deed-index-flat-sheet.md` — Flat cross-survey deed index: ONE extra sheet listing all Sale Deeds / ATS / GPA with Drive links (2012 onwards) across a land-document folder. Covers filename classification regex, doc-number + fiscal-year parsing with the century heuristic (2-digit years: >=40 → 19xx, else 20xx), party/reference extraction (Sanchaya, PK, Mahesh, Shivappa, Ramesh, Nahar), duplicate-spreadsheet resolution via session history, scanned-PDF identification via pdftoppm + vision_analyze, and the Sheets API `foregroundColor`-inside-`textFormat` formatting pitfall.
- `references/google-export-docx-edit.md` — Editing Google-Docs-exported .docx files (HR policy tables, etc.): python-docx sees 0 tables because Google wraps cells in content-locked `w:sdt` blocks — use lxml on `word/document.xml` instead; clone-row insertion; the rezip trap (`customXml` vs `customXML` case mismatch — always rezip the whole dir and re-validate); upload companion copy + mirror permissions skipping the `owner` role (403 transferOwnership).
- `references/folder-dedup-clean-set.md` — "Make a new folder with one set of all documents, no duplicates": recursive md5 inventory → group by checksum → pick canonical per group → copy unique set into a new subfolder via files().copy (never move) → verify count + zero dup md5s. Worked example: Oasis - print 305→291.
- `references/doc-number-in-folder-match.md` — "Which of these registration doc numbers are in this Drive folder?": resolve folder by distinctive name word, RE-WALK (never trust stored counts — Oasis-print 891→303 after consolidation), tolerant filename doc-number extraction (`_`, `-`, "of", 2-digit years `3320/16`, date-prefix years `16102023`, far-apart tokens "2025 Gift Deed No 9196", typos '0f'), drive-wide search + parents check for misses, three-bucket reporting (in folder / elsewhere in Drive / missing), flag same-number-different-year and year-label mismatches.
- `references/palya-project-context.md` — Palya Land (Sy 8/1, 2A 6G row villas) project context: folder IDs (TMP working folder with site sketches/concept renders, PALYA ASHOK JEE LAND title docs), the Sinchana master-plan assignment (12 Aug brief, 17 Aug confirmation, nothing delivered on Drive as of 25 Aug), and the repeatable recipe for "pull all plans/renders/concepts for project X" (Drive name+fullText → architect-owner check → Gmail thread state)
- `references/project-design-assets-search.md` — "Pull all plans/renders/concepts for <project> + what <architect> made": Drive name search → architect owner-email search (`'arch@email' in owners` — they file under their own scheme, not the project name) → Gmail assignment thread → delivered-vs-promised status check (Palya/Sinchana worked example). Categorize survey/legal inputs vs our concepts vs competitor R&D.
- `references/voice-search-property-documents.md` — Voice transcription corrections for property name + document type searches on Drive. "Tars" → "Towers", "Flow Plan" → "Floor Plan", KFT acronym rules. Use when the user says "open [property] [doc] from the drive" via voice memo.
- `references/marketing-collateral-lookup.md` — "share the list of links shown by <person>" / "anything called posters/brochures/flex/hoarding" workflow: session_search the person (Gauri→Gowri Singh alias) → Drive `name contains '<noun>'` search → list containing folder for related collateral → deliver clean `/file/d/<ID>/view` links. Includes the Ranka Udaya marketing folder map (folder `129WGpGKBCE12ZqobdQj4CCT5Nxdc1Fgc` at Drive root; Poster 1-8, Flex, Hoarding, Sunpack, Brochure, Video IDs) and the pitfall that inline `python3 -c` in terminal() breaks on escaping — write the .py to /tmp first.
- `references/competitor-project-tracking.md` — Where competitor project data lives (Competitor Material `19AtwWaB6lO9GQzk_2Kv3P3Dh_nI5Ie-w`, RoVilla RERA Prelim per-project pattern `178pFGIFzFvflgOTpB6Hri0N_5SKBs9bC`), the 18 & Oak folder + site plan IDs, batch-filing workflow for new competitor document drops, and pitfalls: stale contact email → Drive share 400 invalidSharingRequest (use Gmail-history-active address), `&` in filenames trips the terminal background-guard (write script to /tmp instead of heredoc), shared-drive membership auto-grants writer on new files.
- `references/drive-folder-docx-index.md` — "List of documents in all folders as a Word file" workflow: recursive Drive walk → per-folder docx tables with clickable file-name hyperlinks + summary. Includes the python-docx hyperlink fix (`doc.part.relate_to(url, RT.HYPERLINK, is_external=True)` — NOT `part.rels.get_or_add`, which raises TypeError) and the Oasis - print worked example. Re-runnable script: `scripts/drive-folder-to-docx.py <FOLDER_ID> <out.docx> [service_name] [root_label]`
- `references/rlda-blr-cantonment-context.md` — RLDA Bangalore Cantonment (BTPL lease) project filing context: BLR CANT folder IDs, draft-letter naming convention + version history, the lease-timeline/Non-Effective Period letter thesis (no penalties, re-declare milestones first), key contacts (Vikram Jain Karbawala)
- `references/drive-share-request-grant.md` — Handling `Share request for '<item>'` emails from `drive-shares-dm-noreply@google.com`: Gmail search pattern, extracting item IDs + `userstoinvite` requester from the body, granting time-limited (expirationTime) viewer access via Drive API, and the verified API-response quirks (create/update responses show `exp=None` but the expiry IS stored; permission id in response unreliable — always verify by `permissions().list`). Re-runnable helper: `scripts/grant-time-limited-access.py <email> <days> <file_id>... [role]`

## Folder Structure

DRAAS projects live under **DRA Projects** (`1wYtUJJwELLu7o1dIr38p_QthRHaMwWvH`), owned by bk@findingform.design (external architect).

| Folder | Parent | Owner | ndr Permission |
|---|---|---|---|
| **Serenity Hill View** (etc.) | DRA Projects | bk@findingform.design | Partial write |

**Key rule:** DRA Projects is owned by an external architect (bk@findingform.design). ndr@draas.com has **partial write access**:
- **CAN** move files INTO existing subfolders (e.g., Legal, Content Marketing, Architectural)
- **CAN** modify/delete contents of existing subfolders
- **CANNOT** create new folders at the project root level (``canAddChildren: false`` on the project folder itself)
- **CANNOT** create new subfolders under DRA Projects project folders (same restriction cascades down)

**Workaround for write restrictions:** To add content to a DRA Projects folder when you can't create new folders:
1. Move files into existing subfolders (always works — the move adds the file to the destination folder's parent list)
2. For content that needs a new subfolder (e.g., Customer Documents): create it in your own Drive root → share with the architect → ask them to move it into place
3. Google Drive shortcuts also work across ownership boundaries -- create the folder in your Drive, then create a shortcut reference

## Shareholder Matters Folder Structure

Nishant's preferred structure for shareholder-related documents across all DRAAS entities:

```
Shareholder Matters/
├── DRA Aadithya (DRAAPPL)/
│   ├── BM/       (Board Meeting Notices & Minutes)
│   ├── AGM/      (Annual General Meeting)
│   ├── EGM/      (Extraordinary General Meeting)
│   └── Minutes/  (general minutes)
├── DRA Aadithya South City (DRAAS)/
│   ├── BM/  AGM/  EGM/  Minutes/
├── Truliv/
│   ├── BM/  AGM/  EGM/  Minutes/
├── DRA Aadithya Southcity Projects (DRAASCPPL)/
│   ├── BM/  AGM/  EGM/  Minutes/
├── Common - Shareholder Matters/  ← Family-related & cross-company documents
└── Gift Deeds/             ← Gift deed documents (merged from Personal & Chennai folders)
```

Key conventions:
- **One root folder** for all shareholder matters — NOT split per-company
- Each company gets its own subfolder with BM/AGM/EGM/Minutes
- **Common/** for family issues and cross-company docs (e.g. share transfer templates, family settlement references)
- **Gift Deeds/** lives inside Shareholder Matters, not under Personal
- Empty old Gift Deed folders should be deleted after migration

## Document Naming Convention

**GLOBAL RULE (NDR, Aug 2026): ALL documents/artifacts created or uploaded on Google Drive for Nishant follow `YYYYMMDD_EntityName_Description`** — not just company/shareholder docs. Applies to every Doc/Sheet/Slides/HTML/MD/PDF in any folder (including TMP). Underscores only — no spaces, no em-dash, no "(DD-MM-YYYY)" suffix. File IDs/links are preserved on rename.

Examples:
- `20260726_DRAASCPPL_Interim_Cooperation_Agreement_Draft_by_NDR`
- `20260618_DRA_Aadithya_Interim_Cooperation_Letter`
- `20260213_BM_DRAAS_Notice_of_Board_Meeting`
- `20260825_Ranka_Oasis_Jiraaf_Term_Sheet_Key_Terms_v1.0`

Rules:
- **YYYYMMDD** prefix for sorting
- **Underscores** between words (not spaces or hyphens)
- Entity abbreviation (DRAAS, DRAAPPL, DRAASCPPL, project name, etc.) right after date
- Descriptive suffix starting with document type or topic; version allowed as `_vX.Y`
- Google Docs uploaded with a properly formatted name stay as-is after creation

**Translation naming rule:** When a document has both an AI-generated and a human-produced translation, append the translator source as the final suffix:
- ✅ `YYYYMMDD_Village_SyNo_Document_AI_Generated_English_Translation.pdf`
- ✅ `YYYYMMDD_Village_SyNo_Document_Summary_Human_Translation`
- Never mix — each suffix is exclusive. The human translation is always the authoritative version.

**Exception — litigation case folders use numbered-prefix naming:** court-case folders (e.g. "RRP vs SPV", OS 553) keep a `NN_Description.pdf` sequence (01, 02, …), NOT the YYYYMMDD convention. When filing into a case folder, follow its existing numbered sequence (next = highest NN + 1) and read `references/litigation-case-folder-filing.md` first. **Always duplicate-check before filing uploaded court orders** — scans of the same order are often already filed under different names; verify with pdftotext (text-layer copies) or pdftoppm + tesseract OCR (scans), then file only genuinely-new orders and report dupes to the user with their existing links.

## Root-File Cleanup Pattern

When documents end up in "My Drive" root (common after upload), they should be:
1. Identified by search (recently modified, name matching known entities)
2. Reviewed for correct destination (Shareholder Matters > Company > Subfolder)
3. Moved via `files().update(fileId, addParents=targetId, removeParents=rootId)`
4. Related versions of the same document should be consolidated in the same folder

## Serenity Hill View — Content Type → Folder Mapping

Example project with documented taxonomy (Nishant, Jul 2026):

| Content Type | Correct Folder | Wrong Folder |
|---|---|---|
| Architectural renders (F1-F8 PNGs, Revit, Sketchup, AutoCAD) | Architectural > Renders | — |
| Drone footage (DJI .MP4, aerial stills) | Drone Footage | — |
| **Brand Film / AV** (emotion-arousing, warm, aspirational video — no specs/pricing) | **Marketing Collaterals** | ❌ Architectural > Renders |
| Brochure (PDF) | Brochure | — |
| Marketing content briefs, copy | Content Marketing | — |
| Title docs, RTCs, sale deeds, legal petitions | Legal | — |

**"Same folder" pitfall — verify the destination by walking the tree, not by taking the first search hit (2026-08-24).** Uploading "the follow-up questions file… in the same folder" misfiled into `Vendor Drone Footage(Re shoot)- Serenity Hill View 2` because the folder-picker fell back to the first `name contains 'Serenity'` folder result when the expected "GBT - Documents" name didn't surface. The correct destination was **Serenity Hill View → Legal** (id `1t335m5vJcYJmCMwmc3D38t1_qrTwCCGX`) — which holds all GBJT revenue records (RTCs, sale deeds, trust deed, ECs), the OS 4595 case tracker, and `20260715_Complete_Check_List_Assudani_Legal_Due_Diligence.pdf`. Fix pattern: (1) list children of the project root, (2) pick the subfolder whose EXISTING CONTENTS match the document type you're filing (Legal for legal opinions/checklists/revenue records), (3) after upload verify `parents` contains the intended folder, (4) if misfiled, `files().update(fileId, addParents=<correct>, removeParents=<wrong>)` moves it in one call.
| Investment documents, term sheets | Investor | — |
| Structural drawings | Structural | — |

**Brand Film naming convention:** A warm, emotion-arousing video that sets tone/aspiration without specifics (pricing, location details, unit specs) should be named:
- ✅ `Serenity Hill View - Brand Film.mp4`
- ❌ Explainer Video
- ❌ Walkthrough
- ❌ Promotional Video

The distinction: Brand Films are about *feeling* (what life could be like). Explainer/Walkthrough videos are about *facts* (location, pricing, layout, specs). Keep them in separate folders under Marketing Collaterals.

### Creating a Marketing Collaterals folder

```python
from tools.gws_skill_bridge import call
r = call('drive_create_folder', service_name='google-draas',
         name='Marketing Collaterals', parent_id=PROJECT_FOLDER_ID)
```

Under a DRA Projects folder (owned by bk@findingform.design), the `drive_create_folder` call uses your own Drive's create capability, not the project folder's — so it may succeed or fail depending on the token's actual write permissions. See "Write Restrictions" above.

## Common Patterns

### 0. Signed Document Receipt & Filing

When the user receives scanned signed/executed paper documents by courier/post, **or returns a digitally-signed PDF you created** — vision-identify (scanned), rename (YYYYMMDD_*), upload to correct folder (project > Title Documents for land docs, Shareholder Matters > Entity > BM/AGM for corporate docs), optionally create draft email reply on thread with attachment. Full workflow in `references/signed-document-receipt-and-filing.md`.

**CRITICAL:** Always confirm the target folder with the user before filing. Do NOT proceed without confirmation.

### 1. Move file from TMP → Customer Documents

```
TMP/ → Serenity Hillview/ → Customer Documents/ → [Customer Name]/ → [File]
```

1. Search TMP for the file
2. Identify the correct project — look for ndr-owned version (check `owners[0].me == true`)
3. Verify `capabilities.canAddChildren` before attempting writes
4. Create intermediate folders (Customer Documents > CustomerName)
5. Move with `files().update(fileId, addParents=newId, removeParents=oldId)`

### 2. Searching scanned document archives for customer records

When a project has FILE-1-to-N folders of batch-scanned PDFs (e.g. AHFL Stelo Dharwad), customer names and unit numbers rarely appear in filenames. Full workflow in `references/scanned-document-customer-search.md` — the key insight is to find the project's **customer payment/index spreadsheet** rather than searching PDF filenames.

```python
# Quick search: check project index spreadsheets first
call('drive_search', query=f"name contains 'Index' and '{project_folder_id}' in parents",
     raw_query=True, max=20, service_name='google-draas')
```

### 3. Checking folder permissions

Always inspect before writing:
```python
f = svc.files().get(fileId=ID, fields='id,name,owners,capabilities').execute()
if f['capabilities'].get('canAddChildren'):
    # safe to create/move
else:
    # find the alternate writable copy
```

### 4. Merging duplicate folder structures

When a project has folders in two places (e.g., root-level + DRA Projects), use this workflow:

1. **Inventory both** — list all subfolders and count items in each
2. **Match subfolders** — identify which exist in both locations (e.g., Architectural, Legal, Brochure)
3. **Identify unique content** — files that exist only in the non-canonical copy
4. **Move files, not folders** — use `files().update(fileId, addParents=correctId, removeParents=wrongId)` per file
5. **Delete empty subfolders** after their contents are moved out
6. **Delete the wrong folder** — `files().delete()` permanently removes it

See `references/permission-patterns.md` → "Merging Two Parallel Folder Structures" for detailed steps and pitfalls.

### 6. Google Doc placeholder copy + fill

When a template Google Doc has placeholders like `[NAME]` or `[●]`, create filled copies per-person:

```python
# 1. Copy the source document
copy = drive.files().copy(fileId=SOURCE_ID, body={'name': f'{prefix} - {person_name}'}).execute()
new_id = copy['id']

# 2. Move to target folder
drive.files().update(fileId=new_id, addParents=TARGET_FOLDER_ID, removeParents=OLD_PARENT, fields='id').execute()

# 3. Batch-replace placeholders — API field is 'replaceText', NOT 'replaceWith'
requests = []
for old_text, new_text in replacements:
    requests.append({
        'replaceAllText': {
            'containsText': {'text': old_text, 'matchCase': True},
            'replaceText': new_text
        }
    })
docs.documents().batchUpdate(documentId=new_id, body={'requests': requests}).execute()
```

⚠️ **The Google Docs API field is `replaceText`, not `replaceWith`.** Using `replaceWith` gives a confusing `Cannot find field` error even though every other part is correct.

### 7. Creating folder hierarchies in a single pass

To create a nested folder structure (e.g. Shareholder Matters → companies → subfolders):
1. Create the root folder via `drive.files().create(body={'name': name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parentId]})`
2. Collect its ID
3. Create subfolders one at a time with that ID as parent
4. No need for `capabilities` check on your own Drive (always writable)
5. To create sub-subfolders (BM, AGM, EGM), create each inside the company folder

### 8. Project NOC / Sanction Audit + Granting Colleague Access

Recurring request: "check if we have the PCB/KSPCB NOC for project X", "find the latest BBMP sanction plan", "give <colleague> access to the project folders". Full workflow with the Ranka Northstar (Allalasandra) worked example in `references/project-noc-sanction-audit.md`.

Key steps:
1. **Search name variants** — projects live under multiple spellings on Drive: `Northstar`, `North Star`, `North star`, `Allalasandra`, `Allalsandra`. Run several queries: `name contains` variants + `fullText contains` for the project name.
2. **Verify folder parents before attributing any NOC set to a project** (CRITICAL). Same-looking NOC bundles (dated BESCOM/BWSSB/BSNL/KSPCB/DGP/AAI letters) exist for DIFFERENT projects. Example: the 2010 KSPCB NOC (`NOC dated 23.11.2010 issued by KSPCB`) lives under **Veracious Vani Vilas** — NOT Ranka Northstar. Always walk `files().get(parents)` up 2-4 levels and confirm the project folder before reporting.
3. **Check NOC index/expiry spreadsheets** — projects often have a "Noc Documents and Expiry Status" or "Lattest NOC & Sanction Plan Index" sheet that maps NOC → date → expiry → Drive link in one row. Read it via Sheets API before reading every PDF.
4. **Identify the sanctioned plan** by signature markers: a BBMP plan sanction has `Project No.: PRJ/xxxx/yy-YYIN`, `FileNo: BBMP/...`, digitally signed by JDTP, and "Approval Condition" text. Sanctioned plan ≠ submitted drawings (2026 DWG/SHEET files are applications in flight, not sanctions).
5. **Grant colleague viewer access + verify** (see reference for code):
   ```python
   svc.permissions().create(fileId=fid,
       body={'type': 'user', 'role': 'reader', 'emailAddress': 'colleague@draas.com'},
       sendNotificationEmail=False, supportsAllDrives=True).execute()
   # ALWAYS verify: list permissions and confirm the reader entry exists
   ```
   Check existing perms first (`permissions().list`) — the colleague may already have reader on *some* subfolders but not the root; grant on the root + the key subfolder, then verify both.

### 9. Filing court orders into a numbered case folder

Court-matter folders (e.g. `RRP vs SPV`, the OS 553 Devanahalli case folder) use a `NN_Description.pdf` numbering convention (01–31+), NOT the YYYYMMDD convention — follow the folder's own scheme for new filings.

1. **Check for duplicates BEFORE filing.** The folder often already contains the same order under a different name (scans vs text-layer uploads). Identify by content, not filename:
   - Compare page counts (`pdfinfo | grep Pages`) — same count is a strong signal
   - Extract text (`pdftotext`) — if the existing copy is a scan (empty text) and the upload has text, OCR the existing first page with **tesseract** (`pdftoppm -r 100 -png` then `tesseract img stdout`) and compare against the upload's known content — same court header/case number/operative order = duplicate
   - Do NOT create duplicate files; tell the user the doc is already on file and name the existing file
2. **Name the new one with the next number** in the folder's sequence (e.g. new IA order → `32_Orders_IA_No5to7_15Feb2025.pdf`)
3. Upload via `files().create(body={'name': ..., 'parents': [folder_id]}, media_body=...)`, then **verify parent chain** (file → folder → grandparent) and confirm `canAddChildren` first.
4. Some matter folders also have a Document Index **spreadsheet** with a compiled-bundle page-range scheme — ask before updating it (its numbering may not match the folder file names).

### A. File staged in "Temp" vs "TMP" — check the right staging folder

When NDR says "I added it to temp" / "I uploaded it to the temp directory", the file is in the Drive **"Temp" folder** (id `0B1Oc8cSaJXPGMFFCRWtqQ2lqSDQ`), NOT the local filesystem `/tmp` or the agent's "TMP" staging folder. See `references/temp-vs-tmp-folders.md` for the full workflow.

**Critical pitfall avoided (Aug 2026):** I searched the local `/tmp` directory first and found nothing. The file was in Drive's "Temp" folder all along. Always search Drive first when NDR says "temp".

### 10. Full case-record sweep ("did they ever mention X in the record?")

To answer a "was X ever pleaded/filed" question about a litigation (e.g. partnership deed, registration, s.69 challenge):

1. Download the ENTIRE matter folder (all PDFs + docx) to `/tmp/<case>/`
2. `pdftotext -layout` every PDF; flag empty ones as scans; extract docx via zipfile `word/document.xml`
3. OCR all scans with tesseract in a background job (`pdftoppm -r 150 -gray -png` per page → `tesseract` → append to txt), `notify_on_complete=true`
4. Grep the corpus for the term + variants (`partnership|registered|registration|section 69|annexure`), then read the exact passages
5. Verify plaint assertions against physical record: a plaint saying "copy produced at Annexure X" does NOT mean the annexure is in the filed bundle — check the plaint PDF's actual pages (it often ends at verification/schedules with no annexures)
6. Check what the OPPOSING party conceded — their own filing may admit the point you're worried about (e.g. defendants affirming plaintiff's registration)

## Pitfalls

- **Telegram gateway drops `.html` uploads — rename to `.txt` to get them in (2026-08-17).** The gateway's `SUPPORTED_DOCUMENT_TYPES` allowlist is only `.pdf`, `.md`, `.txt`, `.csv`. An `.html` attachment is probed, logged as `Unsupported document type: .html`, and the bytes are DISCARDED (not saved to document_cache) — no recovery path. Workaround: ask the user to rename the file to end in `.txt` (e.g. `letter.html.txt`) and resend; the HTML content comes through intact and can then be converted/imported (Google Doc via HTML import, LibreOffice, etc.). Do NOT keep polling the cache waiting for a rejected file.

- **Auth email can flip mid-session (ndr → psingh).** `_load_credentials_direct('google-draas')` returned ndr@draas.com for earlier calls in the same conversation, then silently started returning psingh@draas.com, making the case folder 404. ALWAYS print `svc.about().get(fields='user')` at the top of every GWS script and run with `HERMES_SESSION_USER_ID=ndr` (or whichever canonical uid) prefixed — do not trust that the previous call's identity persisted.

- **Drive 404 "File not found" ≠ folder is gone — it may be another user's folder. Check WHOSE token build_service is actually loading (2026-08-10).** Prakash (psingh) shared a Drive folder link; `files().get` under ndr's token returned 404, and the browser redirect showed sign-in (not public). `gws_resolve_account` listed only ndr's accounts (psingh isn't a separate vault service — psingh@draas.com resolves to service `google-draas`), and after psingh authorized, `build_service('drive','v3',service_name='google-draas')` STILL loaded ndr@draas.com's token — because the Telegram session id ([REDACTED-TID]) maps to canonical uid `ndr-[REDACTED-TID]`, not psingh's. The vault had a fresh psingh token under `psingh-[REDACTED-TID]/google-draas` (expiry just refreshed), but the session user is ndr. **Fix: run GWS scripts with `HERMES_SESSION_USER_ID=psingh` env prefix** so `build_service` resolves to Prakash's canonical uid and loads his token. Verify which account a token actually is with `svc.about().get(fields='user')` → `emailAddress`, not by trusting service_name. Diagnostic order: (1) `gws_resolve_account` to see has_token, (2) check vault identity/uid mapping via `resolve('telegram', tid)` + `get_identity`, (3) confirm token email via about().get. Do NOT tell the user the vault is down — this is an identity-mapping issue, and the wrong-service-name symptom is identical to "not authorized".

- **Google API "file disappeared" ≠ auth problem — diagnose 403/404 per-file (2026-08-10).** When a spreadsheet/file that previously worked suddenly returns **Sheets 403 "The caller does not have permission"** and **Drive 404 on `files().get`**, while OTHER files on the same account still work, the token is FINE — it is a file-level access problem (file moved/deleted, access revoked, or wrong fileId). Diagnostic order: (1) `gws_resolve_account` → `has_token: true`; (2) `gws_fetch_token` → token not expired; (3) read a known-good sibling file with the same service → works; (4) target file → 403/404. Then STOP blaming auth and find the file: search Drive by name variants (`name contains 'Sevaganapalli'` / `'TSR'` / `'FlowOnTitle'`), check `trashed=true`, check permissions via `files().get(fields='permissions')`, and grep session history (`session_search`) for the spreadsheet's real title/ID. If the file is genuinely gone from the account's view, tell the user the file needs to be re-shared/moved back — do NOT try to reconstruct the whole workbook from memory. Worked example 2026-08-10: the Sevaganapalli DocMatrix `1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc` 404'd while the legal-docs index `1QlhTySrhDnT_nid9J3VUobi9dpuPa7iGG8F0rirrEnU` (same account) read fine — access loss, not token expiry.

- **Two folders, one name.** Drive allows duplicate folder names — always distinguish by ID, never by name alone
- **Generic-named NOC PDFs are not project-attributable by filename.** "NOC dated 23.11.2010 issued by KSPCB" style files repeat across projects with near-identical names (the 2010 KSPCB/BESCOM/BWSSB/BSNL/AAI/DGP NOC set belongs to Veracious Vani Vilas, not Ranka Northstar). Always trace `parents` up 3–4 levels to the top project folder before citing a NOC for a project. See `references/project-noc-approval-lookup.md`
- **`canAddChildren: false`** is the signal that you're looking at the read-only (DRA Projects) copy
- **`supportsAllDrives=True`** may be needed when working with shared drive files
- **`files().update()` with `removeParents`** removes from the old parent — you don't need a separate delete
- **Cross-owner file: rename OK, MOVE FAILS (403) — copy instead (2026-08-01).** When a sheet/file is owned by ANOTHER user (e.g. `sales1.blr@draas.com` / Bharat) and shared with ndr as writer, `files().update(addParents=<ndr-folder>, removeParents=...)` fails with `HttpError 403` — `capabilities.canAddMyDriveParent: false` because the file lives in the owner's drive, not NDR's. Renaming (`files().update(body={'name': ...})`) works fine, but relocating into NDR's My Drive folders does not. Fix: `drive.files().copy(fileId=src, body={'name': ..., 'parents': [target_folder]})` — creates an NDR-owned copy in the right place (new ID/link, keep the original where it is). Check `owners[0].me` BEFORE attempting a move; if false and the move 403s, use copy and tell the user a copy was filed (original stays with its owner).
- **File stays in TMP's trash?** No — `removeParents` just unlinks it from TMP; it's not deleted
- **`drive_search` via `gws_skill_bridge.call()`** requires `raw_query=True` when passing a raw Drive API query string. Without it, the bridge wraps the query as `fullText contains '{query}'` which breaks compound queries like `'folder_id' in parents and trashed=false`. Always pass `raw_query=True` for non-text-search queries.
- **`execute_code` sandbox does NOT propagate `GWS_VAULT_SOCKET`** — the vault Unix socket and its env var are absent from the sandboxed process. `gws_skill_bridge.call()` and `gws_auth.load_credentials()` will fail with `cannot import name 'gws_fetch_token'` or `GWS_VAULT_SOCKET is not set`. The **working pattern** is to use `terminal()` (not `execute_code`) for all GWS operations — the vault socket IS available in the terminal environment. Inside a `terminal()` script:
  
  ```python
  import sys; sys.path.insert(0, '/opt/hermes')
  from tools.gws_auth import _load_credentials_direct
  from googleapiclient.discovery import build
  creds = _load_credentials_direct('google-draas')
  service = build('drive', 'v3', credentials=creds)
  ```
  
  **Use `/opt/hermes/.venv/bin/python3`, NOT bare `python3`** — system python (3.13, PEP 668) has no `googleapiclient`, so the script dies with `ModuleNotFoundError` (verified 2026-08-14). Full working invocation: `cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 - <<'EOF' ... EOF`. Also pass `HERMES_SESSION_USER_ID=<uid>` (e.g. ndr) so `_load_credentials_direct` resolves the right vault token.

  Do NOT try to set `os.environ['GWS_VAULT_SOCKET']` from within `execute_code` — the socket path is `/opt/data/gws-vault/run/vault.sock` but the bind-mount itself isn't available in the sandbox namespace, so setting the env var alone won't fix it. Just use `terminal()`.

- **Vault daemon down → GWS tools / `gws_resolve_account` return "Vault socket unreachable ... Connection refused"** — the gws-vault daemon is NOT s6-supervised (absent from `/etc/s6-overlay/s6-rc.d/`); it dies on gateway restarts and must be manually restarted as a tracked background process. Fix (verified Jul 2026):
  1. Confirm it's actually down: `ps aux | grep [g]ws_vault` returns nothing (socket file may still exist with zero listeners)
  2. Restart via `terminal(background=true)` — do NOT use setsid/`&` (Hermes blocks foreground backgrounding):
     ```
     cd /opt/hermes && GWS_VAULT_TOKEN_DIR=/opt/data/gws-vault/tokens \
     GWS_VAULT_IDENTITY_DIR=/opt/data/gws-vault/identities \
     GWS_VAULT_SOCKET=/opt/data/gws-vault/run/vault.sock \
     python3 /opt/hermes/bin_gws_vault_server_live.py
     ```
  3. Verify with `gws_resolve_account` — it should return `has_token: true/false` per account, not a socket error
  If it reports `has_token: false` for all accounts, no token is stored — the user must re-authorize via `send_oauth_url` (a dead socket at callback time means no token was ever written). Empty `tokens/` + `identities/` dirs under `/opt/data/gws-vault/` confirm this state.
  
- **`gws_skill_bridge.call('drive_search', ...)` from `terminal()`** — the skill bridge's `drive_search` requires `raw_query=True` for custom Drive API query strings, else it wraps the query as `fullText contains '{query}'` which breaks compound queries. Same pitfall applies, just route through `terminal()` instead.

- **`drive_upload` via googleapiclient (from `terminal()`):** Use `MediaFileUpload` with the folder ID as parent. After upload, set `anyoneWithLink` (reader) for public sharing and individual `user` (writer) for collaborators who need edit access. Example:
  
  ```python
  from googleapiclient.http import MediaFileUpload
  media = MediaFileUpload(local_path, mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
  uploaded = service.files().create(body={'name': name, 'parents': [folder_id]}, media_body=media, fields='id, name, webViewLink, parents').execute()
  # Anyone with link
  service.permissions().create(fileId=uploaded['id'], body={'type': 'anyone', 'role': 'reader', 'allowFileDiscovery': False}, sendNotificationEmail=False).execute()
  # Individual editor
  service.permissions().create(fileId=uploaded['id'], body={'type': 'user', 'role': 'writer', 'emailAddress': 'user@example.com'}, sendNotificationEmail=False).execute()
  ```

- **Scanned PDFs (no embedded text)** — `pdftotext` returns empty. Use `pdftoppm` to render the first page as PNG, then `vision_analyze` for OCR. For multi-page: `pdftoppm file.pdf /tmp/page -f N -l N -r 200 -png` per page. Full scanned reports (178+ pages) typically just need the first page to identify the document.
- **`vision_analyze` not configured → use tesseract directly.** If vision_analyze errors with "No LLM provider configured for task=vision", don't loop on it — tesseract is installed (`/usr/bin/tesseract`). Batch OCR: `pdftoppm -r 150 -gray -png file.pdf /tmp/pg` then `tesseract /tmp/pg-N.png stdout` per page, appending to one txt with `---PAGEBREAK---` separators. Enough to identify orders, compare duplicate scans, and grep pleadings for legal terms (partnership/registration/annexure etc.). Render at 150 dpi for speed; only go 200+ dpi for tiny print.

- **Reading a Google Slides deck's text when the Slides API is disabled (403 `SERVICE_DISABLED`)** — the Slides API often isn't enabled in the GCP project, but the Drive API is. Don't block on it; export the deck to PPTX via Drive and parse the slide XML:
  1. Export: `svc.files().export_media(fileId=<presentation_id>, mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')` → download to `/tmp/deck.pptx` (use `MediaIoBaseDownload`).
  2. Unzip: `unzip -o /tmp/deck.pptx -d /tmp/pptx_x`
  3. Extract text: for each `ppt/slides/slide<N>.xml`, `re.findall(r'<a:t>([^<]*)</a:t>', content)` and join runs — gives slide-by-slide text including tables, in slide order.
  This is the reliable way to identify which land/property a Prakash "R&D" market-research deck covers (see `kelsa-land-proposal` skill → "Mapping an R&D PPT to a Kelsa proposal"). Slide 2-3 usually carry the village/taluk/survey-number facts; the closing slide says "Prepared by".
