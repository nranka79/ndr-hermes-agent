---
name: draas-drive-organization
description: "DRAAS Drive folder structure, project document workflows, and file management patterns. HARD RULE: every chat-session file starts in the root TMP folder (never My Drive root, never directly in a project); moves only on NDR's explicit instruction. Also: TMP → project folders, permission quirks, cross-account handling. Access-audits: references/drive-access-audit-grant.md."
version: 1.0.0
author: Hermes (DRAAS)
---

# DRAAS Drive Organization

DRAAS Drive conventions: project organization, writable vs read-only copies, TMP → project moves.

**Reference files:**
- `references/brand-and-statutory-assets.md` — logo taglines, GSTIN; +`office-file-in-place-editing.md`, `project-sales-cost-mis.md`.
- `references/drive-shortcut-targets-and-checklist-copy.md` — shortcut targets, xlsx checklist copy.
- `references/bulk-upload-to-drive.md` — bulk uploads → TMP; `collateral-folder-hygiene.md`.
- `references/tmp-duplicate-file-dedup.md` — TMP dupes: md5 + already-filed check.
- `references/ranka-udaya-rg-scheme-assets.md` — RU RG render map.
- `references/rera-submission-side-by-side-comparison.md` — our RERA submission
  vs a comparable's (given as a Drive folder).
  `@draas.com` from external users, risk-rank public-link grants (`anyone`+`writer` first),
  the "adding an expiry" pattern, the trap where removing a public link cuts off the principal's
  own access, and the HTML-email report structure + proposed reorganization. Read for any
  "find all the Ranka-<X> folders / who is this shared with / reorganize this project" task.
- `references/cross-account-ownership-and-moves.md` — ownership transfer when you're not the owner
  (DWD-from-owner fix; `transferOwnership` silently no-ops and still returns 200), the
  real-permission-id trap, diagnosing a 404 as wrong-ID vs wrong-account, shortcut creation and
  the `targetId` field-selection pitfall, idempotent folder create, empty-folder-only delete,
  trash-over-hard-delete, and the tree-walk verification recipe.

## Entity-level folder convention — `Legal & Compliance` (NDR, 2026-09-18)

**Projects** carry their own legal subfolders (as before). **Entities** (DRA REN, DRA KAAJ,
DRA Satvik, DRA Realty, and every future holding/firm entity) each carry ONE common
`Legal & Compliance` folder for non-project legal documents.

Canonical shape — entities sit in parallel under `BusDev > Bangalore`:

```
BusDev > Bangalore
├── DRA REN Development Partners
│   ├── Legal & Compliance
│   │   ├── NOC
│   │   ├── Registration & Registrar of Firms
│   │   ├── GST, PAN & TDS
│   │   ├── Statutory Notices
│   │   └── Litigation
│   └── (project folders)
└── DRA KAAJ Development Partners
    ├── Legal & Compliance
    │   └── (same five subfolders)
    └── (project folders)
```

Rules:
- **Entity != project.** Entity NOCs, firm registration, GST/PAN/TDS, statutory notices and
  litigation live under `Legal & Compliance`. Land/title/legal work tied to a *parcel* stays
  under that **project's** folder.
- **Verify the entity's parent before assuming it's filed.** Entities can sit orphaned at My Drive
  root (DRA REN/DRA Satvik was). Correct parent is `BusDev > Bangalore`
  (`1oTbaqGWRYqC5JQAd00Lq63xdpxrXSoLV`).
- **Create folders idempotently** — never blind-create; a re-run must not produce a second
  `Legal & Compliance`. Recipe in `references/cross-account-ownership-and-moves.md` §4.
- **When you move a doc, leave a shortcut** at the old location so the previous owner's links and
  muscle memory keep working, and re-share with the previous owner as writer.
- **Do not treat an orphaned root-level "Statutory Compliances" folder as usable.** If it exists,
  check `owners[]` first — a personal-Gmail-owned folder cannot be governed under company policy.
  (Verified 2026-09-18: the only such folder was owned by `manish8484447@gmail.com` — a personal
  account — and held Manish Ranka's ITRs. Not adoptable; build the entity folders fresh instead.)

## Naming documents after a counterparty change (2026-09-18)

When the issuer/counterparty in a document changes (e.g. a property is transferred and an NOC is
now issued by the NEW owner, not the original developer), **the filename must change too** — a
stale `Prizm_Developers_NOC_*` filename for a Feroz Ahmed NOC misleads every future search.

Convention: `YYYYMMDD <Issuer> NOC - <Recipient> [.ext]`
→ `20260918 Feroz Ahmed NOC - DRA KAAJ Development Partners.docx`

- Keep the **date prefix** so the set sorts and versions cleanly.
- Apply the rename to the **document AND every shortcut of it** (shortcuts keep the old name and
  become orphaned search hits otherwise).
- **Rename only — never re-create.** The rename must preserve the file ID, the links already
  circulated on WhatsApp/email, and the revision history. `files().update(body={'name': ...})`.
- Do a **whole-Drive search for the old prefix before and after** renaming to prove no duplicate
  copies were spawned (NDR explicitly worries about Drive pollution).

## 🚨 HARD RULE — EVERYTHING IS CREATED IN TMP FIRST (NDR, 2026-09-17)

**Default (and only) creation location for agent/chat-session output on Drive is the `TMP` folder at My Drive root.**

- **TMP folder ID: `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`** (name `TMP`, parent = My Drive root `0AFOc8cSaJXPGUk9PVA`)
- ANY file/folder a chat session creates — Google Docs, Sheets, Slides, PDFs, HTML, MD, KML, DOCX/XLSX uploads, output subfolders — goes **inside TMP**, never at My Drive root, never dropped straight into a project folder.
- My Drive **root is NOT a staging area**. Root stays clean. A file appearing at root is a bug, not a filing choice.
- Moving TMP → project/entity folder happens **only when NDR explicitly asks** ("move it to Ranka Oasis", "file this under X"). Until then it stays in TMP.
- When creating a folder for a multi-file deliverable, create it **inside TMP** (e.g. `TMP/20260917_DRAAS_Devanahalli_SH96_...`), not at root.
- Applies to every account's delivery pass: if the target account has a root-level `TMP` folder, use it.

**Monthly/on-demand audit command** (root pollution sweep — run whenever NDR says "files are landing on the root again"):

```python
# recent items sitting at My Drive root
r = svc.files().list(q="'root' in parents and trashed = false and createdTime >= 'YYYY-MM-DDT00:00:00'",
                     fields='files(id,name,mimeType,createdTime)', pageSize=200).execute()
# fix: one call per item, then verify parents
svc.files().update(fileId=fid, addParents=TMP, removeParents=ROOT, fields='id,parents').execute()
```

**Re-runnable script (preferred — dry-run unless `--apply` is passed):**
`scripts/drive-root-pollution-sweep.py --since YYYY-MM-DD [--account google-draas] [--apply] [--passes N]`
— lists root items created on/after `--since`, moves them into TMP, loops the pass (default 3), verifies `parents` per item, and prints what is still stuck at root. Run it from `terminal()`, never `execute_code` (vault socket).
It also encodes two field pitfalls: `parents` is NOT selectable in a `files().list` fields mask (`files().get` per file instead), and `'root' in parents` is the account-agnostic root alias (`about().get(fields='rootFolderId')` 400s).

- Re-run the sweep **2–3 times** — a parallel chat session creating files mid-sweep will drop new ones at root between passes (verified 2026-09-17: 2 files appeared at root during the first pass; a third pass found a further 5 from an earlier day).
- Moving to TMP is non-destructive (`removeParents` just unlinks from root — nothing is deleted, links/IDs preserved).
- After the sweep, re-query and confirm `remaining == 0` before reporting.

**Verified sweep 2026-09-17:** 12 root-polluting session artifacts (09-13 → 09-17: income-tax case docs, Ranka Oasis master inventory ×2, Prestige Hermitage action plan, DNR JDA opinion PDF+HTML ×2, police complaint PDF, AI presentation demo pack folder) all relocated into TMP; root confirmed clean.

## Reference Material

- **Locating a JDA area-sharing / area-allocation agreement on Drive** — the registered
  `Supplementary Sharing Agreement` (two signed originals, one per party) that fixes ratio,
  unit-wise allotment and parking for a JDA project. The filename does NOT contain "area sharing",
  so the opening `name contains 'area sharing'` / `'SSA'` / `'area allocation'` searches legitimately
  return ZERO — search `'Sharing'` / `'Supplementary'` instead, and treat `fullText` hits as a
  discovery net only. Full search ladder, scanned-PDF OCR pipeline, cross-check rules, and the
  floor-attribution drift pitfall: `apartment-area-uds-statement` →
  `references/jda-area-sharing-agreement.md`.
- `references/corporate-profile-portfolio-lookup.md` — "Latest corporate profile / DRA Portfolio" lookup: search name contains 'profile' AND 'portfolio' (NDR uses the words interchangeably — the real latest file was named DRA Portfolio Updated.pdf, not *Profile*), image-heavy marketing PDFs have near-zero text layer → verify coverage via OCR keyword sweep, known DRA corporate deck corpus (dates, sizes, IDs, which projects each covers), and the pdftoppm output-glob pitfall. Re-runnable: `scripts/ocr-keyword-sweep.py <file.pdf> <outdir> [keywords...]`
- `references/dr-itat-matter-context.md` — DR ITAT matter (ITA 2786/BANG/17 AY 2011-12, late Shri Dinesh Devraj Ranka): thread IDs, DR ITAT folder contents + refund-computation sheet, CA/advocate/accounts participant map, matter chronology (assessment → ITAT → HC → OGE), Arun Kumar fee + ledger handoff, Sheetal Ranka disallowance open item, computation figures
- `references/dra-corporate-profile-lookup.md` — "find the latest DRA corporate profile / portfolio PDF": the file is named **Portfolio** (not Profile) — canonical file IDs + content maps of every version, the search-name-variant strategy, and the image-PDF OCR-sweep verification pattern (Drive fullText can't index image-only PDFs). Script: `scripts/ocr-sweep-keywords.py`
- `references/family-lou-cooperation-letters-context.md` — DRA family LOU / cooperation / comfort letters: voice-name mapping ("Raj"=Ranjeeth Rathod, "Mantah"=Mamata Rathod), the 4-party LOU emailed 27-Aug-2026, Raj's split into Chennai comfort letter + Bangalore cooperation letter, folder map (Family Settlement - Final - 2025, Chennai shares gifting, Shareholder Matters), "I uploaded it to the drive" junk-name workflow, and the LOU-vs-split comparison verdict template
- `references/drh-dra-prime-partners-context.md` — DRH&I / DRA Ranka Holdings / DRA Prime Partners filing context: folder map + IDs (partnership docs, GST cert, PAN), the DRA Finance & Investment → DRA Prime Partners rename thread, loose-at-root deeds, proposed resolution filename
- `references/dra-family-settlement-context.md` — DRA Ranka/Rathod family settlement context (2025-26): parties + voice aliases (Raj=Ranjeeth Rathod, Mantah=Mamata Rathod), Gunjur/Kothnur/Mantri asset map, folder IDs (Family Settlement - Final - 2025 canonical bundle, FSA Addendum Kothnur), original LOU + Raj's returned cooperation letter + comparison HTML IDs, and the open negotiation gaps in Raj's returned version
- `references/rlda-blr-cant-project-context.md` — RLDA Bangalore Cantonment (BTPL redevelopment) context: BLR CANT folder IDs, the BTPL→RLDA draft-letter exchange history (2025-05-25 → 2026-08-17, with Drive IDs — several revised letters sit in My Drive root, not BLR CANT), key facts/timeline (FAR 5 chain, BHS declaration/withdrawal, WP 38186/2025, lease-clock clauses), letter naming convention, and the docx text extraction recipe (zipfile + regex on word/document.xml, python-docx not installed)
- `references/rrp-vs-spv-os553-case-context.md` — RRP vs SPV OS 553/2023 litigation context: case folder & index IDs, order chronology, partnership-deed status (deed NOT on court record despite plaint's "Annexure A" claim; s.69 exposure), deed file locations on Drive
- `references/dra-realty-constitutional-docs.md` — "Does the DRA Realty Pvt Ltd MOA/AOA permit partnerships / investing immovable property as capital?" exact answer + workflow: canonical folder/file IDs (`Firm - DRA Realty Private Limited` + duplicate "Copy of" sets), entity history (Southcity Retail Plus → DRA Realty, 08-Dec-2020 rename; EGM 16-Nov-2020 object amendments), full MOA object summary (NO partnership clause found), standard amendment clause wording for partnership + property-as-capital, and the garbled-OCR-text-layer pitfall on scanned MOA/AOA (pdftotext word-salad — verify at page level with tesseract)
- `references/drive-rename-move-pattern.md` — Combined rename + move in one `files().update()` call (avoids separate operations)
- `references/bin-restore-rename-relocate.md` — "I deleted it, restore it from bin into the right folder": trash search → `trashed:False` restore → rename (descriptive, not the old recipient name) → move, with the cross-owner 403 pitfall (target must be ndr-owned — sales1/admin2-owned folders block `addParents`) and post-restore stale-permission check (Harsha Naidu reader on restored Ranka Iris folder)
- `references/litigation-case-folder-filing.md` — Filing court documents into litigation case folders: numbered-prefix `NN_Description` naming (NOT YYYYMMDD), duplicate-detection workflow against already-filed scans (pdftotext → pdftoppm + tesseract), and the O.S.No.553/2023 RRP vs SPV worked example (folder IDs, document index sheet, orders status)
- `references/bulk-scan-case-docs-identify-rename-index.md` — Bulk "examine + rename + spreadsheet index" workflow for a folder of unattributed scanned case PDFs (`pdf.1.pdf … pdf.N.pdf`): render page1(+2/last) → tesseract → identify → `NN_Description` rename (re-fetch name→id in-script, never hand-copy IDs) → index sheet in the same folder. Verified 2026-09-12 on the 32-doc OS 553 "Rajesh Shah Vs SP Partners" bundle (incl. Ronald Colaso impleadment O1R10, 08.04.2025)
- `references/permission-patterns.md` — Known Drive permission quirks: DRA Projects vs shared drive, external folder ownership, capability inspection
- `references/tmp-to-project.md` — Complete workflow for moving a file from TMP to a project Customer Documents folder
- `references/bulk-upload-tmp-skip-existing.md` — Bulk upload of a downloaded bundle (RERA plans, doc sets) to a TMP subfolder: skip-existing-by-name so re-runs are idempotent, clean `NN_desc.pdf.pdf` double-extension names, verify count from Drive (not local), deliver folder link + key-doc links. Use for "upload everything to TMP and give me links".
- `references/document-version-chronology.md` — Building a timeline from Drive metadata (createdTime, modifiedTime, owners) to spot version mismatches between plans, inventory sheets, and layout drawings across different accounts
- `references/dtlp-project-structure-and-upload.md` — DRA Thindulu Land Partners (DTLP) numbered-subfolder taxonomy (01_Title…06_Customer), plus the full terminal()-based upload workflow with anyone-link and collaborator permissions
- `references/ranka-project-folder-taxonomy.md` — NDR's agreed Entity→Project→Category folder structure and its current state across **Ranka Amber / Ranka Udaya / Ranka Oasis**: entity root IDs (DRA Realty, DTLP, Sevaganapalli Land Partners, DRA Projects), per-project subfolder IDs, the two working styles (named-category vs numbered 01–06), Oasis's 3-copy mess, and the reusable recipe for "show me the folder structure for <project>" (name sweep → disambiguate by owner + parent chain → recursive count walk). Also records that **"Ranka Vasis" = voice garble of Ranka Oasis**.
- `references/ranka-udaya-project-structure.md` — Ranka Udaya (DRA Thindlu Land Partners) Drive folder map: multiple same-name folders with different owners, canonical writable folder ID (`1sdDX5htwSKF2SSe_re-jjYb-8SsFCk8Z`), 02_Approvals subfolder ID, upload pitfall (403 on read-only BK@fnw.homes folder), and permission-verification pattern.
- `references/cross-owner-bulk-migration.md` — "Move everything related to <project> from <colleague>'s drive into mine, leave shortcuts": bulk ownership consolidation via DWD drive-scope impersonation (session_uid=<owner-email>, drive scope ONLY). Sequence per file: MOVE first (via original owner's token) → TRANSFER ownership → SHORTCUT in original location. Dedup against target (name+size) before moving; external-owner files (findingform, IamHere) copy-only; recursive walk mandatory (Master Folder children rarely carry the project name); idempotent resume + per-file verify (owner + parent + shortcut). Verified 2026-09-10: 166 moved + 7 vendor copies + 48 dup-skipped + 19 excluded, 238 shortcuts, zero failures. SUPERSEDES the old copy-only pitfall for on-domain (draas.com) employee files.
- `references/temp-vs-tmp-folders.md` — Drive "Temp" folder vs local /tmp distinction
- `references/ranka-northstar-allalasandra-sy14-records.md` — Ranka Northstar (Allalasandra, Yelahanka) Sy 14/1–14/5 survey-record inventory: RTCs/MRs/Akarbandh/hakka bukha/Atlas/village-map file IDs in "North star approval folder 2026 April", FMB sketch, Judicial Layout plan pair, Sy 14/1 Guidance Value, Title Deeds dd-checklist sheet, and the scanned-Kannada no-text-layer caveat. Use when NDR asks for "podi/satbara/tippani/sketches for Sy 14/1" or file IDs for Ranka Northstar records.
- `references/ranka-northstar-predcr-context.md` — **Ranka North Star (Allalasandra) pre-DCR / sanction context + the floor-plan review checklist**: NDR's pre-DCR thesis (show BOTH roads — 30 ft front + ~38/40 ft rear — include them in the site area ~53–54k sq ft, relinquish them → 1.75 FAR on the ENTIRE site area; G+4 / 15 m / 5 m setback), the UNRECONCILED G+7-2.8-FAR figures in his 12-Sep mail, the airport/AAI + PCB/BWSSB NOC parallel track, the ADLR sketch question, the team/counterparty address table (Anbu, Kantesh, Sinchana, Bharat, Rahul=vkdas, Arvind Jain, Shrinidhi GV + Theertha of AJ Architects, landowners), the three deliverables he chases (floor plan for review, BOQ, area statement), the voice corrections (**"Srinithi"→Shrinidhi GV**, "flow plan"=floor plan, **"Rahul"=Vinod Kumar Das**), the unresolved "Nagraj sir", and the full 11-section **Floor_Plan_Design_Compliance_Checklist** (Drive id `1fW1wAdrLwoTZ_cBvoGvfix78TTUayyLC`) plus the extra criteria NDR always names (unit-to-unit window privacy, door positions/swings, unit-wise Vastu). Load for any North Star / Allalsandra / pre-DCR / floor-plan-review / area-statement ask.
- `references/swaminathan-allalsandra-gpa-poa-inventory.md` — Swaminathan family GPA/POA docs for Allalsandra (Ranka NorthStar): voice-name correction ("Kanikshita"→**Kankshita**), the 3 GPAs + POA No. 142 + 28-Mar-2025 Board Resolution (with the BK-LV 321-vs-320 doc-number inconsistency), and the key finding that all powers run **daughter/family → DRA Projects**, not daughter→father.
- `references/global-dated-sweep-rename.md` — "Rename EVERYTHING we prepared in the last week per our naming convention" sweep ACROSS all folders/incl TMP: query `createdTime >= X and 'me' in owners`, scope decision table (rename docs/artifacts, skip folders/media/other-owners' files), one-pass rename preserving doc IDs/links, deliver summary. Use when the user demands execution (not a review-gated proposal).
- `references/html-file-inventory-and-reorg.md` — "give me a list of everything with links, exact folder, entire chain, as an HTML table" + file-by-file reorganization: live recursive walk with skip-set, chain-up-to-My-Drive (ROOT `0AFOc8cSaJXPGUk9PVA`), md5 dedupe audit (MOVE / EXACT-DUP / NAME-DUP content-diff), move = addParents+removeParents with post-verify, trash-only-after-empty, `.html.txt` twin for Telegram (gateway drops `.html`), rerun verification after interrupted runs. Worked: DR Villa/R99 v1→v2 (10-Sep-2026).
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
- `references/buxranka-brdpl-project-context.md` — BuxRanka / BRDPL Hudson Circle (Godrej JV) context: folder IDs, the two modified-approvals cost sheets (official charges vs liaisoning), the Godrej email threads + participants, the rename → file → reply-all-with-attachment pattern, **plus the Sep-2026 4.5 FAR pre-DCR strand** — Manju DS `<dsmanju15@gmail.com>` (quotation 04-09-2026 via "Excel Consulting Services", ₹5,90,000 total / ₹3,50,000 advance / Canara A/c 0472201001821), Harsimran Singh (Godrej), Anbu = Anbarasan M `pm2.blr@draas.com`, the misspelled thread subject "Bux ranka quatation" (`1a08ea566eef0676`), and the **"get `<third party>` to write to `<counterparty>`" → internal instruction email to our own colleague + verbatim block** pattern.
- `references/ranka-chambers-lease-context.md` — Ranka Chambers (31 Cunningham Rd) lease terms: 1984 lease-cum-construction deed (60 yrs from 4-Aug-1984 → ~Aug 2044) + 1986 adjoining lease (58 yrs → ~Jun 2044), file IDs, and the OCR/vision technique for 1980s scanned deeds. Load for any "when does the Ranka Chambers lease end" / lease-expiry question.
- `references/insurance-policy-details-lookup.md` — "find insurance policy <number> in my emails/drive — full details + registered email": exhaustive search order (exact → variants → Drive fullText → sessions → family), authoritative sources (policy bond PDF via pdftotext carries the registered email), the Life_Policy_Payment_Tracker cross-check, and zero-hit reporting.
- `references/locating-research-across-data-estate.md` — "find the research/records for <land parcel>" / "did I email X about Y": search ladder (sessions → Gmail variants → Drive fullText + parent chains → Kelsa DRA pipelines → gbrain), interpretation rules (missing email = verbal assignment → draft follow-up; survey PDF is the top artifact), and the Siddhapura/Prestige GreenMore worked example (Sy 27/2+27/3, ALOK/PUTTARAJU owners, Sri Ranganatha Nursery, LaraTech survey).
- `references/tdr-drc-certificate-lookup.md` — "find the TDR / development rights certificate (DRC) for <project> / transferred from <person> to <company>": Bangalore DRC naming (cert files are called DRC, not TDR — search `name contains 'DRC'`), counter-folio BACK-SIDE transfer table (handwritten — vision_analyze, not tesseract), OCR the project's BBMP sanction plan for the "TDR Utilized" table (cert no + transferor/transferee), companion DRC surrender letter ties cert → project via LP No. Worked example: Ranka Iris DRC 001498, Dinesh Ranka → DRA Developers & Projects Pvt Ltd (util 22.5.13, bal 4036.14 sqm).
- `references/email-attachment-to-drive-filing.md` — "give me that Word doc from the email with <advocate> re <matter>": locate thread by case no (side-threads have different subjects), walk parts for the attachment, download via attachments().get, verify docx content (zipfile + strip tags) BEFORE delivering, check Drive for existing FILLED/SIGNED versions before uploading, upload native docx with descriptive name, file in the matter folder (DR ITAT map incl. the giving-effect-order letter worked example with thread 19f3b09fb55511df), deliver link + MEDIA copy; vision_analyze-rejects-PDF pitfall.
- `references/requisition-list-to-checklist-sheet.md` — advocate's Word "requisition list" (docs to be procured per survey number) → survey-wise Google Sheets checklist (Survey Number | Document | Priority | Status), filed in the project folder, then a threaded draft email to the assigned colleague with the original forwarded + docx attached + sheet link. Covers voice-name mapping (Prasannakumar→Prasanna Swaminathan, Katnalli→Katenahalli, "Rahul"=Vinod Kumar Das), lxml body-order table parsing incl. multi-survey blocks (125/2-5), existing-tracker check, and the icloud non-Google invite 400 pitfall (anyone-link fallback). Validated 2026-08-25 (Katenahalli V2, 24 tables → 46 rows).
- `references/pscp-kingfisher-towers-context.md` — PSCP folder ("PSC Prestige South City", My Drive root): contents (Hermitage, Golfshire, PrestigeGreenMore, KFT files), and the Kingfisher Towers Flat 14A title chain (UB Factory → UB Holdings → Prestige JDA 2010 → Lakshmi Singh 2017 → Dinesh Ranka confirming → Rahul Ampally 2021) with filing-naming convention.
- `references/prestige-hermitage-context.md` — Prestige Hermitage (Ulsoor Rd, 23 floors × 1 unit/floor, pre-RERA OC Mar-2017): PSCP→Hermitage folder + full file-ID map (floor plans, brochure, as-built survey, OC, LO share/car-park/cost sheets), the **AREA answer** (SBA 7,481 sq ft + UDS 2,322 sq ft per unit from the sale deeds; **no official carpet area exists** — portal figure 5,386 sq ft is third-party), unit↔floor numbering (2201 = 22nd floor), LO-vs-PG unit split, the Apr-2026 asset-sale deeds (2201→Roshni, 2101→Manish, 2301→Dharmesh) with consideration + deferred-payment guarantees, and the no-text-layer brochure pitfall.
- `references/folder-index-spreadsheet.md` — Build a per-category spreadsheet index of a Drive folder (one sheet per survey number/project, Sl No / Category / File name / Drive link / Date). Covers the psingh identity override (`HERMES_SESSION_USER_ID=psingh` + explicit `service_name='google-draas'`), thread-local services for parallel large-folder walks (shared service → SSL RECORD_LAYER_FAILURE), survey-number name normalization, and the 90-sheet creation/formatting pattern (chunked batchUpdate, fetch sheetIds after addSheet).
- `references/project-checklist-categories.md` — Per-project "Documents Checklist" workflow (one spreadsheet, one tab per project, NO summary tab — Prakash's hard rule). FLAT date-sorted layout (NOT section-header bands — user corrected 2026-08-13): Category column + per-category row colors, all docs old→new. Covers the category keyword classifier with ordering rules (LAND before REV, FIN before APPROVAL, `\b` word boundaries for firm keywords, `(?<![a-z])ec(?![a-z])` for ECs), filename document-date extraction, parent-folder discovery when the shared link is a "Master data" container, the `updateBorders` `color`-not-`colorSpec` pitfall, the STALE MERGES silent-value-swallow pitfall (recreate fresh, don't reuse formatted sheets), and date-order verification via sort_key not display strings.\n- `references/filename-document-table-parsing.md` — Successor format (2026-08-13): parse STRUCTURED columns out of renamed filenames — `SL NO | Sy NO | DOCUMENT DATE | DOCUMENT NUMBER | DOCUMENT TYPE | PARTIES (from and to) | DRIVE LINK`, date-sorted, multiple survey numbers listed on continuation rows below the same Sl No. Full extraction pipeline: survey normalization (4-digit surveys 1508/1, comma-as-separator NOT terminator, paren lists, shorthand `158/1C3,5,6` → 1C3/1C5/1C6, p.no page-number junk drop), EC-first-year vs others-last-year date fallback, doc-number patterns, type-ordering traps (survey sketch before sale deed), party extraction (between-X-and-Y-without-to, `_to_` FormII, NO_PARTIES_TYPES skip set). ALWAYS re-walk folders first (user renames files between requests).
- `references/survey-wise-docx-index.md` — Survey-no.-wise Word doc index: extract Indian survey numbers from filenames (SyNo, FMB, Patta, UDR, EC) → group by survey → Word doc with tables. Reusable script: `scripts/survey-wise-index.py <FOLDER_ID> <out.docx>`.
- `references/sale-deed-transaction-summary.md` — Extends folder-index-spreadsheet: classify deed files by filename (SALE DEED / ATS / GPA, FY from doc numbers), batch-OCR every PDF in a background job, parse parties/transaction-date/survey-numbers from OCR text, and build a per-document "Transaction Summary" tab. Includes the Bestamanahalli worked example (folder IDs, spreadsheet IDs, Sanchaya aggregation chain) and pitfalls (form-header date stamp 09-05-2003, pdftoppm zero-padded page globs, string Sl No int() cast).
- `references/deed-index-flat-sheet.md` — Flat cross-survey deed index: ONE extra sheet listing all Sale Deeds / ATS / GPA with Drive links (2012 onwards) across a land-document folder. Covers filename classification regex, doc-number + fiscal-year parsing with the century heuristic (2-digit years: >=40 → 19xx, else 20xx), party/reference extraction (Sanchaya, PK, Mahesh, Shivappa, Ramesh, Nahar), duplicate-spreadsheet resolution via session history, scanned-PDF identification via pdftoppm + vision_analyze, and the Sheets API `foregroundColor`-inside-`textFormat` formatting pitfall.
- `references/google-export-docx-edit.md` — Editing Google-Docs-exported .docx files (HR policy tables, etc.): python-docx sees 0 tables because Google wraps cells in content-locked `w:sdt` blocks — use lxml on `word/document.xml` instead; clone-row insertion; the rezip trap (`customXml` vs `customXML` case mismatch — always rezip the whole dir and re-validate); upload companion copy + mirror permissions skipping the `owner` role (403 transferOwnership).
- `references/folder-dedup-clean-set.md` — "Make a new folder with one set of all documents, no duplicates": recursive md5 inventory → group by checksum → pick canonical per group → copy unique set into a new subfolder via files().copy (never move) → verify count + zero dup md5s. Worked example: Oasis - print 305→291.
- `references/evidence-pack-relevance-triage.md` — "this folder has a lot of unrelated documents — keep only what relates to <person/matter>" / "re-analyze and delete anything not related to <name> from Documents_Collected": pack shape (README + Manifests CSV + Documents_Collected + raw .eml dumps), the per-type text-extraction matrix (pdftotext → OCR fallback; xlsx/docx via zipfile XML; `strings` for .doc/.bin/.mpp; strip `<style>`/`<script>` BEFORE tags on .html), the keep/delete rule matching NDR's intent (names the person OR a co-allottee OR is single-unit/case-specific OR is a multi-customer sheet containing their name — "even if it pertains to multiple other customers, if <X> is in it, keep"), trash-not-delete + restore, and the pitfalls: never key a keep-list on `mimeType.split('.')[-1]` (yields `[12]` artifacts and trashes a file you meant to keep — verify `KEEP not found: {}` is empty first), read ±70-char snippets not hit counts (Aadhaar/amount `6093` false-positives), same-surname and brand homonyms, names split across XML runs, OCR covers pages 1–2 only, never judge by filename, and report gaps/duplicates rather than silently fixing them. Re-runnable extractor: `scripts/drive-doc-pack-extract.py <FOLDER_ID> '<regex>' [outdir] [service_name]`.
- `references/email-corpus-relevance-cleanup.md` — round-2 sibling: prune the RENDERED email folders (post `eml-archive-to-pdf` + `bulk-drive-tree-mirror-upload`) to the subject only. Body-level classifier design on email.txt (positive signals: unit/name/email/case-number; negatives: same-surname other customer, brand homonyms), the 2017 sales-lead "different person?" timeline check, KEEP audit + dropped-but-mentions QA before deleting, drive-side inventory→sharded-trash→upload-missing→per-account-verify, and the two big pitfalls: **stray uploader from a previous turn resurrects trashed folders (needs a second inventory+trash pass; check `ps aux` first)** and **double-dot .eml stem mismatch**. Verified 2026-09-10: 1,989 → 219 keep, 3,541 trash ops, 0 failures.
- `references/eml-archive-to-pdf.md` — raw `.eml` dump → readable per-email PDFs + extracted `Attachments/` + `INDEX.csv` (\"I don't have a viewer for these email files\"): the WeasyPrint render pipeline, output layout, the **big-stack-thread fix for WeasyPrint `RecursionError` on deeply-nested marketing HTML** (layer 1 big stack + raised recursion limit fixed all 122 failures; layers 2/3 = bs4 depth-cap sanitize, plain-text PDF), idempotent repair pass, the `-maxdepth 3` PDF-count trap, rebuilding `INDEX.csv` statuses after a repair, and the noisy entity-flag caveat (same-surname customers, brand homonyms, colliding IDs).
- `references/bulk-drive-tree-mirror-upload.md` — "put them in <folder> on drive, I need to see the folder structure": publish a large LOCAL tree (thousands of nested folders/files) into an existing Drive folder with structure preserved. Three-script architecture (prep → shard → nohup orchestrator), **shard across PROCESSES not threads (googleapiclient in ThreadPoolExecutor segfaults)**, the one-shot parent pre-list that makes per-item existence checks free, measured 0.22–0.28 emails/s per shard, retry signature, and the Drive-side verification sweep. Verified 2026-09-10: 1,989 folders / ~5,500 files / 3.8 GB, zero failures. Companion to `eml-archive-to-pdf.md` (which builds the tree this publishes).
- `references/mirabilis-rera-behera-case-context.md` — Mirabilis RERA matter (CMP/200628/0006093 → RERA/BEN/6093/2023-24): voice aliases ("Subya/Savya Sachi"/"Baira"→Sabyasachi Behera; no such thing as "Vandre"), parties + co-allottee Damayanthi Behera (search her name too), B1-203 facts (registered 10-04-2023 Deed 236/2023-24, consideration Rs 58,63,690, possession 12-04-2023, car park 105 B1), recovery ladder to the Rs 26,63,278 attachment order of 03-09-2026, the KPDL-never-impleaded asymmetry vs sibling case 5887 (D-607, Abhishek Kumar), counsel (Vinay T VNV / Adv. Jasleen Kaur Smriti Legal — "Justine"=Jasleen), false friends (Ipsita Behera A-1002, 2017 sales lead "sabyasachi", Tata CLiQ brand), the never-served KPDL 48-hour demand notice, and pack/case folder IDs. Load for any Mirabilis / Behera / B1-203 / 6093 question.
- `references/drive-document-pack-compile.md` — "Give me a copy of all <project> <doc-type> documents to send to someone": live Drive re-sweep (never trust session inventories), get_media vs export_media (docs → PDF; .docx raw uploads 403 on export), pymupdf title+index pack compile with all pitfalls (helv-b fontname error, stale page objects after insert_pdf, index page inserted BEFORE docs for accurate numbers, scanned no-text-layer check). Worked example: Ranka Iris OC pack 17 docs / 45 pages.
- `references/doc-number-in-folder-match.md` — "Which of these registration doc numbers are in this Drive folder?": resolve folder by distinctive name word, RE-WALK (never trust stored counts — Oasis-print 891→303 after consolidation), tolerant filename doc-number extraction (`_`, `-`, "of", 2-digit years `3320/16`, date-prefix years `16102023`, far-apart tokens "2025 Gift Deed No 9196", typos '0f'), drive-wide search + parents check for misses, three-bucket reporting (in folder / elsewhere in Drive / missing), flag same-number-different-year and year-label mismatches.
- `references/palya-project-context.md` — Palya Land (Sy 8/1, 2A 6G row villas) project context: folder IDs (TMP working folder with site sketches/concept renders, PALYA ASHOK JEE LAND title docs), the Sinchana master-plan assignment (12 Aug brief, 17 Aug confirmation, nothing delivered on Drive as of 25 Aug), and the repeatable recipe for "pull all plans/renders/concepts for project X" (Drive name+fullText → architect-owner check → Gmail thread state)
- `references/ashok-kumar-wp7542-dggi-gst-context.md` — Ashok Kumar v UOI WP 7542/2025 (HC Karnataka; DGGI GST raid/seizure of records 20.12.2024; WP seeks return of ALL seized docs): DRA KAAJ folder map + Legal - WP 7542-2025 subfolder IDs, filed-doc inventory (names/IDs), key dates (stay 14.03.2025, objections+IA 29.07.2025, oral order 29.07.2026), counsel (Trust Law/Akash for petitioner; Madhu N Rao for DGGI), voice alias "Kaj"→DRA KAAJ (NOT Ren-Kaj), follow-up ownership (Prakash↔Trust Law, NDR↔CA Saurabh 98864 89873)
- `references/project-design-assets-search.md` — "Pull all plans/renders/concepts for <project> + what <architect> made": Drive name search → architect owner-email search (`'arch@email' in owners` — they file under their own scheme, not the project name) → Gmail assignment thread → delivered-vs-promised status check (Palya/Sinchana worked example). Categorize survey/legal inputs vs our concepts vs competitor R&D.
- `references/voice-search-property-documents.md` — Voice transcription corrections for property name + document type searches on Drive. "Tars" → "Towers", "Flow Plan" → "Floor Plan", KFT acronym rules. Use when the user says "open [property] [doc] from the drive" via voice memo.
- `references/ivc-colaso-rrv-rrp-context.md` — IVC / Ronald Colaso case docs ("IBC Colasso" voice) — canonical spelling **Colaso** (not Collaso/Colaco/Coloso), RRV vs RRP entity disambiguation (Colaso deal = Ranka Raj Ventures; NO "Ranka Raj Properties" folder exists; RRP = separate OS 553 matter), and the folder map: the 90-doc case set in **RR Ventures → Ivc kimji** (`1_7Cx0MyZkm7Z5RaNwzqdhJxUHElq8a5a`), RRP vs SPV under IVC-KIMJI-250123 (admin2), and IVC Road Documents as a DIFFERENT Tindlu/SMS Builders matter.
- `references/project-render-workorder-lookup.md` — "find the proposed office/render for <project> that goes with a work order": renders are often filed under a SIBLING or colleague's design folder, BUT **verify the folder's project attribution before using it** (2026-09-14 correction: Bharat's "Ranka Oasis - Design & Marketing" → Marketing Office Renders is the RANKA OASIS office render, NOT Ranka Udaya's — same office scope, different project; the correct Udaya design came from NDR as a chat attachment); Kelsa PO/WO 537 may carry MULTIPLE records for one scope — the issued WO for Ranka Udaya marketing office is **#761 EXOTIC PORTABLE CABINS (₹10.33L, HoD Approved, Issued PO-WO PDF)**, not #750 AM Office Solution (PO-WO Created, never issued); when the wrong render was already sent to a vendor, delete the misplaced copy, resubmit with an explicit "earlier visual was wrong" correction, and recreate the email draft with the correct attachment. Verified 2026-09-14 (Moduli outreach, correction round).
- `references/marketing-collateral-lookup.md` — "share the list of links shown by <person>" / "anything called posters/brochures/flex/hoarding" workflow: session_search the person (Gauri→Gowri Singh alias) → Drive `name contains '<noun>'` search → list containing folder for related collateral → deliver clean `/file/d/<ID>/view` links. Includes the Ranka Udaya marketing folder map (folder `129WGpGKBCE12ZqobdQj4CCT5Nxdc1Fgc` at Drive root; Poster 1-8, Flex, Hoarding, Sunpack, Brochure, Video IDs) and the pitfall that inline `python3 -c` in terminal() breaks on escaping — write the .py to /tmp first.
- `references/competitor-project-tracking.md` — Where competitor project data lives (Competitor Material `19AtwWaB6lO9GQzk_2Kv3P3Dh_nI5Ie-w`, RoVilla RERA Prelim per-project pattern `178pFGIFzFvflgOTpB6Hri0N_5SKBs9bC`), the 18 & Oak folder + site plan IDs, batch-filing workflow for new competitor document drops, and pitfalls: stale contact email → Drive share 400 invalidSharingRequest (use Gmail-history-active address), `&` in filenames trips the terminal background-guard (write script to /tmp instead of heredoc), shared-drive membership auto-grants writer on new files.
- `references/drive-folder-docx-index.md` — "List of documents in all folders as a Word file" workflow: recursive Drive walk → per-folder docx tables with clickable file-name hyperlinks + summary. Includes the python-docx hyperlink fix (`doc.part.relate_to(url, RT.HYPERLINK, is_external=True)` — NOT `part.rels.get_or_add`, which raises TypeError) and the Oasis - print worked example. Re-runnable script: `scripts/drive-folder-to-docx.py <FOLDER_ID> <out.docx> [service_name] [root_label]`
- `references/rlda-blr-cantonment-context.md` — RLDA Bangalore Cantonment (BTPL lease) project filing context: BLR CANT folder IDs, draft-letter naming convention + version history, the lease-timeline/Non-Effective Period letter thesis (no penalties, re-declare milestones first), key contacts (Vikram Jain Karbawala)
- `references/drive-share-request-grant.md` — Handling `Share request for '<item>'` emails from `drive-shares-dm-noreply@google.com`: Gmail search pattern, extracting item IDs + `userstoinvite` requester from the body, granting time-limited (expirationTime) viewer access via Drive API, and the verified API-response quirks (create/update responses show `exp=None` but the expiry IS stored; permission id in response unreliable — always verify by `permissions().list`). Re-runnable helper: `scripts/grant-time-limited-access.py <email> <days> <file_id>... [role]`. **NDR default for external recipients (2026-09-10): when a draft email/WhatsApp message shares Drive links with an outside party (architect, vendor, counsel), grant 30-day viewer access by default — per-user reader permission with `expirationTime` (Google does NOT allow expiry on "anyone with link" shares, so always share to the recipient's email, not an anyone-link).** See also the `permissions().update` role-included pitfall in Pitfalls below.
- `references/drive-inventory-cleanup-sheet.md` — "List my last N drive files / I want to clean up my drive": fetch top-N by createdTime (owned + shared), folder-path walker (root = folder with no parents — `about().get(fields='rootFolderId')` 400s), cleanup heuristics (generic names / root-level / normalized-name dupes / Copy-of), spreadsheet build (HYPERLINK links, freeze, Summary tab), three-pass cleanup approach (dupes → root filing → renames). Re-runnable script: `scripts/drive-inventory-sheet.py`
- `references/google-doc-form-fill-docsapi.md` — Import a blank Word form (.doc/.docx, e.g. BBMP CC application Annex VIII/IX) to Drive as a native Google Doc and PRE-FILL it via the Docs API: legacy .doc text extraction via `strings` (no antiword/libreoffice), one-call Drive import with `mimeType=application/vnd.google-apps.document`, then fill ellipsis placeholders with content-marker paragraph matching + insertText/deleteContentRange. CRITICAL: never fill by hardcoded paragraph indices (they shift → corrupted doc; delete+re-import is cheaper than untangling); re-fetch before every batchUpdate; detect placeholder runs of `…` ONLY (ASCII `.` false-positives on "L.P.").
- `references/markdown-html-to-google-doc-import.md` — Local .md → native Google Doc upload (verified 2026-09-13): `mimetype='text/markdown'` import SILENTLY creates an empty doc (0 chars, no error) — fix is to convert with the `markdown` module (`extensions=['tables','fenced_code']`) and import as `text/html`. NEVER trust the create response; verify by reading the doc back with the recursive walker (text lives in `paragraph.elements[].textRun.content` and inside table cells — a naive top-level `p.get('text')` join returns 0 and falsely signals failure, almost caused deletion of a good doc).
- `references/ranka-amber-project-context.md` — Ranka Amber (DRA Realty) project context: PID 7057785976 / Plot 1-B / Katha 4/124 / Ward 083, BECC approvals (LP GBA/MDP/DDTP/0007/26-27, Project GBA/BECC/0540/25-26, Building Licence BBMP/CC/4247/26-27), architect Anjali Mandhyan (CA/2018/100260), engineer Loganathan M SLVS (BCCL/BL-3.6/E-0293/24-25), CC application form whereabouts, BMTF notice refs. Load before any Ranka Amber approval/CC/RERA/legal work.
- `references/project-drive-audit-access-review.md` — "find ALL the <project> folders across the drives, where are the collaterals, who is it shared with outside draas.com, suggest a reorganization, and email it to <colleague> as HTML": the 6-phase recipe (multi-account name sweep → collaterals hunt incl. architect-owned folders → external-access inventory with the `anyone`/`anyoneWithLink` escalation → colleague editor grants → 6-bucket reorg proposal with a moves table → HTML email), plus the never-quote-a-legal-doc-from-its-filename rule (scanned agreements have no text layer — pdftoppm + vision_analyze to confirm parties).
- `references/o3-kelsa-company-context.md` — O3 Infotech / Kelsa company context for pitch decks, NVIDIA Inception and outreach: legal facts, three founders (Nishant / Manohar / Ashwin Hegde) + photo file IDs, brand kit scraped from kelsa.co.in (colors #F04F63/#4FD1C5/#B38DBC, DM Sans/Inter, logo URL), site stats, client roster, revenue, existing pitch assets (Kelsa Pitch Deck Points doc, O3 Elevator Pitch sheet, Kelsa-Muds.pptx), and the Kelsa-must-not-mention-DRA rule.
- `references/o3-prizm-lease-context.md` — O3 Infotech / Prizm (\"Prism Grasston\") lease-document map: canonical folder `1vPbBkjaEpGbXLJwBg4eMYKctxlBv4nrq` (\"Prizm & O3 Lease Agreements\") with the 14-02-2023 lease deed + 15-05-2023 WHPL sub-lease, related WHPL cancellation copies, and the OPEN item — the O3↔DRA Realty sub-lease (basis for monthly invoices) was NOT found; NDR fallback is an O3 NOC. Load for any \"O3 rental agreement\" / \"Prism lease\" / invoice-basis query.
- `references/invitations-tracking-folder.md` — "move the invite video to the invitations folder + calendar invite + reply": canonical **Invitations** tracker folder (id `10MgC-_yfF03W3TnPHuI4o1ycKxxkscc1`, Temp parent), the 3-folder duplicate-name pitfall (disambiguate by contents), invite-video analysis recipe (ffmpeg frame-grab every ~5s + vision_analyze OCR — details card is mid/late video, video extends the pasted invite text), calendar insert with contact_resolver attendee (worked: Roshini → rnr@draas.com), and Hinglish reply + wa.me (worked: Shripal j Deepika Rahul +91 98450 88235).
- `references/embassy-habitat-914-context.md` — Flat 914 Embassy Habitat (E914, ~914 sq ft second residence being fit out as Maker Space/study/command center, linked to main residence Duplex 1503): folder IDs (Embassy Habitat root `18yM69UTK3lRj7dkoJxG9xbX3ojVqxaos`, 914 `1ola7DIMkCq59dHyMN3xCWJi7hPUn-kUO` with EMPTY Plans/ `15Prc7L5XK52FyPnJoLqN4zdBZ7bqDGuu` + Title Related/, 1503 Plans/ with photos), "Dime 1.4"=914 voice garble, sanction-plan/Scan001/002 are textless scans (no unit layout readable), floor plan NOT on Drive/email (required input), Ruhaan Ranka (pebblyshark69@gmail.com) = design-brief recipient who pastes prompts into his GPT Astra with Blender/SolidWorks MCP. **2026-09-14 collation sweep appended: 914 floor plan confirmed nowhere across 6 colleague drives+mail; new society/1503 docs located (bhagya agreements, CAM/Annual Report from mdr, Sreedevi 1503 khata bundle from rajendra); 97 in-tree files need ownership transfer.**
- `references/multi-account-project-collation.md` — Reusable runbook for "search everyone's drive/email for <project> and consolidate": resolve accounts first (resolve pattern-matches — probe existence), source-of-truth by file ID, drive + gmail sweeps, PRUNE-filtered folder walks, categorize Common/unit buckets, pull email attachments via gws_dwd_gmail_attachment_get (urlsafe b64), migrate per cross-owner-bulk-migration, AND build the cross-account MASTER INVENTORY sheet (dedupe by file ID, owner-chain to My Drive root, description enrichment tiers, validated column layout). Pitfalls: account-key vs email, 100/page caps, junk-drawer colleague folders, vision 503, `includeItemsFromAllDrives` on files().get, Sheet1-rename-before-write.
- `references/inventory-bucket-mapping.md` — POST-inventory step: map every master-inventory row to a target folder bucket and add the column (NDR wants per-row columns, "row by row", not summary proposals). Two-pass classifier (strong name/desc rules, chain as weak fallback), content-check leftover rows via DWD media download (no drive_download op exists — `_creds_for_target` + build service), plural-tolerant chain matching, Legal-bucket-greediness fix, bool-vs-string override bug, Not-Oasis false-positive labeling, and the verified 14-bucket Oasis taxonomy. Verified 2026-09-15 (3,151 rows, 0 unclassified).
- `references/ranka-oasis-survey-extent-extraction.md` — "for each survey number, the exact extent as per the spreadsheet" (sanction-vs-title cross-check): the source-of-truth ladder (Master Data sheet → project breakdown → corroborating sheets → deeds → patta/ILR/FMB), DWD sheets-read via drive-scope creds, and the worked 167/2C resolution — the ~116-signatory first deed's schedule has 19 items = 7.53 ac and does NOT contain 167/2C; patta 2205 (0.145 Ha = 35.8c) settles it as 0.36, not 0.35. Verified 2026-09-16 (18 survey numbers, 7.29 ac total).

## Ranka99 / DR Villa context

- `references/ranka99-dr-villa-context.md` — DR Villa (R99 / L&T South City, Dinesh Ranka) folder map with IDs, file-inventory → HTML table technique (walk surgical subtree, exclude PUSH Deliverables, chain to My Drive root, deliver .html + .html.txt), and the BusDev/root stranded-file locations. Load for any DR Villa / DRVLA / R99 / Ranka99 / South City villa request, or "list every file with link + folder chain".

## Entity-Level "Legal & Compliance" Standard (NDR, 2026-09-18)

**One `Legal & Compliance` folder per ENTITY, alongside (never inside) the project folders.**
Projects keep their own ad-hoc `Legal`/`Legal Docs` subfolders; the firm's own statutory life
(NOCs to the entity, registrar filings, GST/PAN/TDS, notices, litigation) goes to the entity's
`Legal & Compliance` with five category subfolders: `NOC`, `Registration & Registrar of Firms`,
`GST, PAN & TDS`, `Statutory Notices`, `Litigation`. Full spec, folder IDs for the DRA REN /
DRA KAAJ pair, the idempotent `mkfolder` helper, and the pitfall that the one folder literally
named **"Statutory Compliances"** is owned by a personal Gmail (`manish8484447@gmail.com`),
orphaned at root, and must NOT be used: `references/entity-legal-compliance-folder-standard.md`.

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

## R&D Folder Structure (Drive root)

Research & Development material lives in the **R&D** folder at My Drive root (`1wCyEkCHIWYp8q14D5OTzctROLA7203C0`), split by state:

| Folder | ID |
|---|---|
| R&D (root) | 1wCyEkCHIWYp8q14D5OTzctROLA7203C0 |
| R&D → Bangalore | 1JgbbEIAkyEf9hXu6BBVU0w8Dlsml43XT |
| R&D → TN | 1Sy_TQNKOUHJlfCojkF8ryeEGUlMFb7D2 |
| R&D → Research Reports | 1McY0U-OaHcpqdsFHMKKpogMUfTPZJ41m |

User phrase "store it in R&D, Bangalore" → `20260901_BBMP_GBA_Commencement_Certificate_Manual.pdf` style name (YYYYMMDD_Entity_Description) uploaded into the Bangalore subfolder. Verify parents after upload.

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

**Issuance documents name the ISSUER, not the old filename (NDR, 2026-09-18).** When a document is
issued *by* a person *to* an entity — NOCs, consents, authorisations, comfort letters — name it by
the **current actor**, even if the file was created under a previous counterparty's name:

- ✅ `20260918 Feroz Ahmed NOC - REN KAAJ Development Partners.docx`
- ✅ `20260918 Feroz Ahmed NOC - DRA KAAJ Development Partners.docx`
- ❌ `Prizm_Developers_NOC_R3N_1_KAAJ.docx` (the previous lessor had since transferred the premises away)

Pattern: `YYYYMMDD <Issuer> <DocType> - <Recipient>.docx` (spaces + hyphen, per the issuance-doc family).
NDR's reason, verbatim: *"it's no longer Prism Developer, it's just Feroz Ahmed… he is giving the NOC."*
**When the substance of an instrument changes hands, rename the file to match the new reality** — do not
preserve a stale counterparty name for continuity's sake. Rename in place (`files().update(body={'name':...})`)
so the file ID, link and revision history survive; then rename its shortcuts too.

**Also:** never leave multiple copies when "upgrading" a document — NDR explicitly objects to Drive
pollution (*"not multiple copies of it because it starts polluting the drive"*). Edit the original in
place and confirm by a Drive-wide name sweep that no duplicate exists. See
`references/global-dated-sweep-rename.md` for the mass-rename sweep pattern.

Rules:
- **YYYYMMDD** prefix for sorting
- **Underscores** between words (not spaces or hyphens)
- Entity abbreviation (DRAAS, DRAAPPL, DRAASCPPL, project name, etc.) right after date
- Descriptive suffix starting with document type or topic; version allowed as `_vX.Y`
- Google Docs uploaded with a properly formatted name stay as-is after creation

**Content-date-first, metadata fallback for files with NO content date (NDR rule, 2026-09-12):** The YYYYMMDD prefix comes from the document's own content date when readable (sale deeds, ECs, letters). But for files that carry no content date — CAD/DWG drawings, image-only brochure PDFs, renders — use the Drive **createdTime** (or the earliest modifiedTime) as the naming date and rename accordingly. Worked examples (Ranka Northstar): `Fire Sanction.dwg` created 2015-11-13 → `20151113_Fire_Sanction.dwg`; `BBMP_24M_PLAN_NORTHSTAR_R1.dwg` created 2026-04-17 → `20260417_BBMP_24M_PLAN_NORTHSTAR_R1.dwg`; `Ranka NorthStar E-Brochure.PDF` created 2015-06-11 → `20150611_Ranka_NorthStar_E-Brochure.pdf`. DWG binary CAD files CANNOT be vision/OCR'd — date them from Drive metadata alone (`files().get(fields='name,createdTime,modifiedTime,owners')`). If a filename already contains a date (e.g. `WD_24M_DRA_NORTHSTAR_FINAL_MM_07-05-2026.dwg`), leave it as-is — the existing date serves the version indicator; don't prepend another.

**Translation naming rule:** When a document has both an AI-generated and a human-produced translation, append the translator source as the final suffix:
- ✅ `YYYYMMDD_Village_SyNo_Document_AI_Generated_English_Translation.pdf`
- ✅ `YYYYMMDD_Village_SyNo_Document_Summary_Human_Translation`
- Never mix — each suffix is exclusive. The human translation is always the authoritative version.
- **ECI SIR2026 voter notices** get the paired style `YYYYMMDD SIR2026 Voter Notice - <Name> (Kannada Original|English Translation).pdf`, filed under Personal (root or the person's subfolder like RNR). See `references/sir2026-voter-notice-filing.md`.

**ECI SIR2026 voter notices are a deliberate exception to the underscore rule** — established
pairs use `YYYYMMDD SIR2026 Voter Notice - <Name> (Kannada Original|English Translation).pdf`
(spaces + hyphens) and file under Personal or per-person folders (RNR, DDR, Rivaan, Ruhaan,
Murjani, Family). Identify → name → file → calendar pattern + documents-to-carry guidance in
`references/sir2026-voter-notice-filing.md` (verified 2026-09-14, Roshini Ranka + Nazeer Ahamad).

**Exception — litigation case folders use numbered-prefix naming:** court-case folders (e.g. "RRP vs SPV", OS 553) keep a `NN_Description.pdf` sequence (01, 02, …), NOT the YYYYMMDD convention. When filing into a case folder, follow its existing numbered sequence (next = highest NN + 1) and read `references/litigation-case-folder-filing.md` first. **Always duplicate-check before filing uploaded court orders** — scans of the same order are often already filed under different names; verify with pdftotext (text-layer copies) or pdftoppm + tesseract OCR (scans), then file only genuinely-new orders and report dupes to the user with their existing links.

## Root-File Cleanup Pattern

**Preferred state: nothing is ever created at My Drive root.** Anything that lands there is a violation of the TMP hard rule above and gets swept into `TMP` (`18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`) immediately — not filed into a project.

When documents end up in My Drive root (legacy files, or a session that ignored the rule):
1. Identify by search — recent `createdTime`, query `'root' in parents and trashed = false`
2. **Default destination is TMP, not a project folder.** Move to TMP first; NDR re-files from there when he wants it in a project.
   - Exception: an older artifact whose correct project/shareholder folder is unambiguous AND NDR has named the destination — then file it directly (see Shareholder Matters / Serenity Hill View mappings below).
3. Move via `files().update(fileId, addParents=<TMP or targetId>, removeParents=rootId)`
4. Related versions of the same document should be consolidated in the same folder
5. Re-query root after the sweep and confirm zero remaining (repeat 2–3× — concurrent sessions can drop new files mid-sweep)

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

### 6b. Filling an imported Word form (ellipsis placeholders) via Docs API

When the user uploads a blank Word form (BBMP CC application Annex VIII/IX, bank checklists, etc.), converts it to Google Docs, and asks to "fill whatever data you can":

1. **Extract the form text** — legacy `.doc` files are OLE containers; `strings -n 4 file.doc` reveals the full form labels/placeholders without antiword/libreoffice (they may not be installed). A `.doc` often embeds a theme-only zip (word/document.xml absent) — don't waste time unzipping.
2. **Import as native Google Doc in the right project folder** — `MediaFileUpload(..., mimetype='application/msword')` + `mimeType: 'application/vnd.google-apps.document'` + `parents: [folder]` in one `files().create()`. Then rename per YYYYMMDD convention (`20260903_RankaAmber_BBMP_CC_Application_Annexure_VIII_IX_FILLED`), archive the blank original alongside.
3. **Fill placeholders by content-marker paragraph matching, NOT hardcoded indices.** The blank fields are ellipsis runs (`……`) or underline dashes. CRITICAL PITFALLS hit 2026-09-03:
   - **Do NOT fill by paragraph index from an earlier dump** — indices shift as batchUpdates insert text; you will corrupt the doc (values land in wrong paragraphs, "Addres<value>s" mangling). Delete + re-import + fill by marker is cheaper than untangling.
   - **Use `find_para(marker, occ)` semantics**: re-fetch the document before EVERY batchUpdate, locate paragraphs by unique text substring (e.g. `'Ward  No. ………………..   Locality'`), count occurrences — because after Annex VIII gets filled, the Annex IX identical markers drop from occ=2 to occ=1.
   - **Run detection on ellipsis chars ONLY** (`…` U+2026 and friends, min length ≥2). Including ASCII `.` false-positives on "L.P.", "Registration No." and mangled "addres…" strings.
   - **Underline-dash signature blocks**: insert text right AFTER the label (`'Name (In block letters)'` + ' ' + value) rather than replacing the dashes; twin-label paragraphs (Annex IX has two `Name (In block letters)` side by side) need insert after 1st AND 2nd occurrence.
   - Verify by re-dumping every non-empty paragraph + a leftover-ellipsis scan (signature dots are intentional).
4. Update the tracker row (e.g. P-098) with the filled-doc link + a note listing what was filled vs. what needs confirmation (commencement date, architect-vs-engineer choice, plinth status, who files).

Full worked recipe: `references/google-doc-form-fill-docsapi.md`. Ranka Amber approvals data for the CC form: `references/ranka-amber-project-context.md`.

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

### A2. "I uploaded it to the drive" — the file may have a generic auto-name at root

When NDR uploads/imports a document (esp. via Google Docs import), the Drive file can keep a **generic auto-name like `Cooperation_Letter_Bangalore-1`** and sit at **My Drive root** (parent `0AFOc8cSaJXPGUk9PVA`) with no descriptive folder. Don't search by expected filename — find it by **`createdTime` ≈ today** (e.g. `query name contains 'cooperat'`, sort hits by `createdTime` desc, read the newest candidate's content to confirm it's the upload). Then rename per the YYYYMMDD convention and move to the appropriate folder in one `files().update()` (addParents/removeParents), verify `parents` after the move, and report the new name + folder back to NDR (2026-08-31 worked example: `Cooperation_Letter_Bangalore-1` → `20260831_Family_Letter_of_Cooperation_Bangalore_Side_Assets_Raj_Version` filed in Family Settlement - Final - 2025).

### 10. Full case-record sweep ("did they ever mention X in the record?")

To answer a "was X ever pleaded/filed" question about a litigation (e.g. partnership deed, registration, s.69 challenge):

1. Download the ENTIRE matter folder (all PDFs + docx) to `/tmp/<case>/`
2. `pdftotext -layout` every PDF; flag empty ones as scans; extract docx via zipfile `word/document.xml`
3. OCR all scans with tesseract in a background job (`pdftoppm -r 150 -gray -png` per page → `tesseract` → append to txt), `notify_on_complete=true`
4. Grep the corpus for the term + variants (`partnership|registered|registration|section 69|annexure`), then read the exact passages
5. Verify plaint assertions against physical record: a plaint saying "copy produced at Annexure X" does NOT mean the annexure is in the filed bundle — check the plaint PDF's actual pages (it often ends at verification/schedules with no annexures)
6. Check what the OPPOSING party conceded — their own filing may admit the point you're worried about (e.g. defendants affirming plaintiff's registration)

## Pitfalls

- **Drive fullText search does NOT index image/scan-based PDFs (2026-09-02).** Design portfolios and scanned brochures (e.g. the 131 MB DRA Portfolio Updated.pdf) have no searchable text layer: `fullText contains 'Ranka Oasis' and fullText contains 'Northstar'` returns nothing even when the projects are plainly in the deck, and `pdftotext` yields only fragmentary text. Name-search finds them (`name contains 'portfolio'`); to verify content, run the per-page OCR keyword sweep — `scripts/ocr-sweep-keywords.py` (pdftoppm -r 90 + tesseract per page). Full lookup recipe in `references/dra-corporate-profile-lookup.md`.
- **Drive `files().list` fields: `parents` is NOT a selectable subfield and `owners` takes NO subfield in a `fields=` list (hit 2026-09-16).** `fields='files(id,name,mimeType,createdTime,modifiedTime,owners(parents),parents)'` → HttpError 400 `Invalid field selection parents`. The working list-fields form is `files(id,name,mimeType,createdTime,modifiedTime,owners)`. If you need each file's parents, do a follow-up `files().get(fileId=..., fields='id,parents')` per file (that call DOES accept `parents`), or walk the parent chain from the folder listing instead — never put `parents` in the list-call fields.
- **`pdftoppm -f N -l N` does NOT create a single `<root>.png`** — output lands at `<root>-NN.png` (e.g. `pg001-01.png`), so a loop that deletes `<root>.png` after rendering dies with FileNotFoundError. Render all pages in one call and glob `*-*.png`; see `scripts/ocr-sweep-keywords.py`.
- **Telegram gateway drops `.html` uploads — rename to `.txt` to get them in (2026-08-17).** The gateway's `SUPPORTED_DOCUMENT_TYPES` allowlist is only `.pdf`, `.md`, `.txt`, `.csv`. An `.html` attachment is probed, logged as `Unsupported document type: .html`, and the bytes are DISCARDED (not saved to document_cache) — no recovery path. Workaround: ask the user to rename the file to end in `.txt` (e.g. `letter.html.txt`) and resend; the HTML content comes through intact and can then be converted/imported (Google Doc via HTML import, LibreOffice, etc.). Do NOT keep polling the cache waiting for a rejected file.

- **Auth email can flip mid-session (ndr → psingh).** `_load_credentials_direct('google-draas')` returned ndr@draas.com for earlier calls in the same conversation, then silently started returning psingh@draas.com, making the case folder 404. ALWAYS print `svc.about().get(fields='user')` at the top of every GWS script and run with `HERMES_SESSION_USER_ID=ndr` (or whichever canonical uid) prefixed — do not trust that the previous call's identity persisted.

- **Drive 404 "File not found" ≠ folder is gone — it may be another user's folder. Check WHOSE token build_service is actually loading (2026-08-10).** Prakash (psingh) shared a Drive folder link; `files().get` under ndr's token returned 404, and the browser redirect showed sign-in (not public). `gws_resolve_account` listed only ndr's accounts (psingh isn't a separate vault service — psingh@draas.com resolves to service `google-draas`), and after psingh authorized, `build_service('drive','v3',service_name='google-draas')` STILL loaded ndr@draas.com's token — because the Telegram session id ([REDACTED-TID]) maps to canonical uid `ndr-[REDACTED-TID]`, not psingh's. The vault had a fresh psingh token under `psingh-[REDACTED-TID]/google-draas` (expiry just refreshed), but the session user is ndr. **Fix: run GWS scripts with `HERMES_SESSION_USER_ID=psingh` env prefix** so `build_service` resolves to Prakash's canonical uid and loads his token. Verify which account a token actually is with `svc.about().get(fields='user')` → `emailAddress`, not by trusting service_name. Diagnostic order: (1) `gws_resolve_account` to see has_token, (2) check vault identity/uid mapping via `resolve('telegram', tid)` + `get_identity`, (3) confirm token email via about().get. Do NOT tell the user the vault is down — this is an identity-mapping issue, and the wrong-service-name symptom is identical to "not authorized".

- **Google API "file disappeared" ≠ auth problem — diagnose 403/404 per-file (2026-08-10).** When a spreadsheet/file that previously worked suddenly returns **Sheets 403 "The caller does not have permission"** and **Drive 404 on `files().get`**, while OTHER files on the same account still work, the token is FINE — it is a file-level access problem (file moved/deleted, access revoked, or wrong fileId). Diagnostic order: (1) `gws_resolve_account` → `has_token: true`; (2) `gws_fetch_token` → token not expired; (3) read a known-good sibling file with the same service → works; (4) target file → 403/404. Then STOP blaming auth and find the file: search Drive by name variants (`name contains 'Sevaganapalli'` / `'TSR'` / `'FlowOnTitle'`), check `trashed=true`, check permissions via `files().get(fields='permissions')`, and grep session history (`session_search`) for the spreadsheet's real title/ID. If the file is genuinely gone from the account's view, tell the user the file needs to be re-shared/moved back — do NOT try to reconstruct the whole workbook from memory. Worked example 2026-08-10: the Sevaganapalli DocMatrix `1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc` 404'd while the legal-docs index `1QlhTySrhDnT_nid9J3VUobi9dpuPa7iGG8F0rirrEnU` (same account) read fine — access loss, not token expiry.

- **Two folders, one name.** Drive allows duplicate folder names — always distinguish by ID, never by name alone
- **Generic-named NOC PDFs are not project-attributable by filename.** "NOC dated 23.11.2010 issued by KSPCB" style files repeat across projects with near-identical names (the 2010 KSPCB/BESCOM/BWSSB/BSNL/AAI/DGP NOC set belongs to Veracious Vani Vilas, not Ranka Northstar). Always trace `parents` up 3–4 levels to the top project folder before citing a NOC for a project. See `references/project-noc-approval-lookup.md`
- **Acreage in a filename ≠ the document's real acreage (2026-09-16).** `…Village Panchayat Residential Layout Approval 8.52 Acres.pdf` (and its "Approved Plan Drawing" twin) were byte-identical copies of Ranka Oasis's 30,416 sq.m / 7.52 ac sanction letter and DTCP print — the "8.52 Acres" name was wrong. Before quoting an extent from a Drive filename, verify content (byte size matches a known original, or read the letter).
- **A time-limited (30/90-day) grant is IMPOSSIBLE on a file whose parent folder already gives that person access — and you must SAY so, not fake it (hit 2026-09-17, Ranka Amber BMTF notice, "make sure his email has 90 day viewer access").** `permissions().update(permissionId=<inherited perm>, body={'role':'reader','expirationTime':EXP})` → HttpError 403 `Cannot modify a permission on an item to be less than the inherited access from a direct or indirect parent. Leverage limited access…` (`reason: cannotModifyInheritedPermission`). Diagnose FIRST: `permissions().list(fields='permissions(emailAddress,role,permissionDetails(permissionType,role,inherited,inheritedFrom))')` — `inherited: True` means the ACL comes from the folder and cannot be narrowed at file level; the folder's own listing often shows the same person as `inherited: False` (a direct folder grant), which is the proof. Correct response to the user: report that the person already has *stronger* access (writer, permanent) via the folder, that a 90-day cap is therefore not applicable, and that enforcing one would require stripping their folder access — do NOT strip it to satisfy the request, and never claim a grant you couldn't apply. A genuinely time-limited share needs a location the recipient is NOT already shared on.
- Full recipe for the bilingual legal-notice filing + circulation workflow (naming pair, page-level language verification, standalone translation extraction, reply-all draft): `references/bilingual-legal-notice-filing.md`.
- **`permissions().update` with ONLY `expirationTime` → HttpError 400 "The permission role field is required" (2026-09-01).** When sweeping many external (non-@draas.com) viewers to a uniform expiry (e.g. set every reader to 15-day access), the update body MUST include `role` alongside `expirationTime`: `body={'role': 'reader', 'expirationTime': EXP}`. Passing just the expiry is rejected. Note the response shows the new expiry but does NOT echo `role` — verify with a follow-up `permissions().list` (same as the drive-share-request-grant reference). Also: `permissions().create` (new viewer) accepts `role` + `expirationTime` in one call fine. Worked pattern 2026-09-01: add daisykumarsmail@gmail.com as reader + sweep 4 existing readers to 15-day expiry on the "Ranka Iris - Ninth Floor Collaterals" folder (15wD6DBX1OO0rButnWzIZeU6qoX25tlfy).
- **`canAddChildren: false`** is the signal that you're looking at the read-only (DRA Projects) copy
- **`supportsAllDrives=True`** may be needed when working with shared drive files
- **`files().update()` with `removeParents`** removes from the old parent — you don't need a separate delete
- **Cross-owner file: rename OK, MOVE FAILS (403) — copy instead (2026-08-01).** When a sheet/file is owned by ANOTHER user (e.g. `sales1.blr@draas.com` / Bharat) and shared with ndr as writer, `files().update(addParents=<ndr-folder>, removeParents=...)` fails with `HttpError 403` — `capabilities.canAddMyDriveParent: false` because the file lives in the owner's drive, not NDR's. Renaming (`files().update(body={'name': ...})`) works fine, but relocating into NDR's My Drive folders does not. **Update 2026-09-10:** for ON-DOMAIN employees this is now superseded by the DWD drive-scope impersonation path in `references/cross-owner-bulk-migration.md` (impersonate the owner, move + transfer ownership + shortcut). The copy fallback below remains correct ONLY for external-owner files (vendor email addresses you cannot impersonate).
- **Bulk-rename scripts: re-fetch name→id IN the script, never hand-copy IDs from an earlier listing (2026-09-12).** When renaming many files in one loop, keying a `{oldname: newname}` dict against IDs pasted from a previous drive_list call silently mis-maps files (pdf.2/pdf.31/pdf.32 got wrong IDs on first attempt). Fetch `files().list(q="'FOLDER' in parents", fields='files(id,name)')` at the top of the same script and look up by name at rename time — zero drift, links preserved.
- **File stays in TMP's trash?** No — `removeParents` just unlinks it from TMP; it's not deleted
- **Transferring ownership INTO ndr@draas.com from a colleague's file: ndr's own token CANNOT do it — drive it from the OWNER's account via DWD (verified 2026-09-18).** A file created by psingh@draas.com but shared to ndr as **writer** shows `canEdit: true`, `canShare: true` — which looks like enough — but `permissions().update(permissionId=<ndr perm id>, transferOwnership=True)` returns **200 OK and silently does nothing**; `owners` is unchanged on re-read. The cause: transferring ownership requires the **current owner's** authority, and ndr is not the owner. Do not loop on this — diagnose and switch account. Fix path: impersonate the current owner via domain-wide delegation and run the transfer from their side, then retain them as `writer`. Getting the right `permissionId` also needs a two-step (the response `id` is not the email — `permissions().list()` and match on `emailAddress`). **Always re-read `owners` after the call and report only what the re-read shows** — a 200 on a transfer that didn't happen is the exact failure mode to catch. See `references/cross-owner-bulk-migration.md` for the DWD drive-scope impersonation setup.

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
- **Terminal guard rejects heredoc scripts whose string literals contain `&`** (hit 2026-09-15 building the Amber QPR sheet): a `python3 - <<'EOF'` script carrying `&` inside quotes (e.g. "Registration & Identity", "100% + 70% escrow") is flagged as backgrounding — exit -1, "Foreground command uses '&' backgrounding. Use terminal(background=true)". The guard is syntactic, not semantic: `&` inside a Python string still trips it. Fix: `write_file` the script to /tmp first, then `terminal()` runs it — no heredoc, no guard. Same as the existing inline `python3 -c` escaping pitfall; any script with URLs/labels containing `&` should be file-written unconditionally.

- **Sheets API `spreadsheets().get()` rejects `properties.modifiedTime` in `fields` (hit 2026-08-31).** `sheets.spreadsheets().get(spreadsheetId=ID, fields='properties.title,sheets.properties.title,properties.modifiedTime')` → `HttpError 400 "Cannot find matching fields for path 'properties.modifiedTime'"`. modifiedTime is a DRIVE file property, not a spreadsheet property. To list tabs AND get the modified date in one pass: call `spreadsheets().get()` (fields `properties.title,sheets.properties.title` only) for tabs, and `drive.files().get(fileId=ID, fields='id,name,modifiedTime,owners')` for dates/owner. Or simply call `spreadsheets().get()` with no fields param. Common need when identifying "the latest version" of an IRR model across Drive candidates.

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
- **Scanned corporate/legal PDFs may carry a GARBLED OCR text layer — `pdftotext` succeeds but returns word-salad (2026-09-16).** The DRA Realty MOA/AOA scans had an embedded OCR overlay that made `pdftotext -layout` produce interleaved multi-column fragments (half-words, clauses jumbled across lines). Keyword greps "work" but the text cannot be quoted verbatim. ALWAYS verify constitutional-document findings at page level: `pdftoppm -r 200 -png` + `tesseract` per page, with clause-numbering continuity checks (cl. 80→81→82). See `references/dra-realty-constitutional-docs.md`.
- **`vision_analyze` not configured → use tesseract directly.** If vision_analyze errors with "No LLM provider configured for task=vision", don't loop on it — tesseract is installed (`/usr/bin/tesseract`). Batch OCR: `pdftoppm -r 150 -gray -png file.pdf /tmp/pg` then `tesseract /tmp/pg-N.png stdout` per page, appending to one txt with `---PAGEBREAK---` separators. Enough to identify orders, compare duplicate scans, and grep pleadings for legal terms (partnership/registration/annexure etc.). Render at 150 dpi for speed; only go 200+ dpi for tiny print.
- **Default psm silently returns EMPTY on some legal scans — pass `--psm 3` before declaring a page blank (verified 2026-09-16).** On the DRA Realty MOA/AOA + Ranka Oasis gift-deed scans (13–23 pp, ~4–6% dark pixels), bare `tesseract img.png stdout` produced ZERO lines while `tesseract img.png stdout --psm 3` recovered full text (parties, survey schedules, extent blocks). Diagnose an empty first pass with a PIL dark-pixel ratio check; retry `--psm 3` before concluding the page is unreadable.
- **Drive-stored .docx files: `export_media` fails "Export only supports Docs Editors files" — use `get_media`; and their XML may use an `ns0:` namespace prefix, not `w:` (verified 2026-09-16).** Draft deeds uploaded as native .docx (mimeType application/vnd.openxmlformats-officedocument.wordprocessingml.document) cannot be exported via Drive; `files().get_media` returns the zip fine. When parsing, regexes for `<w:p`/`<w:t>` silently match nothing because tags are `ns0:p`/`ns0:t` — strip prefixes (`re.findall(r'<ns0:t[^>]*>([^<]*)</ns0:t>', xml)`) or parse with ElementTree by local-name. Hit on the Ranka Oasis Plot 119 sale-deed drafts.

- **Reading a Google Slides deck's text when the Slides API is disabled (403 `SERVICE_DISABLED`)** — the Slides API often isn't enabled in the GCP project, but the Drive API is. Don't block on it; export the deck to PPTX via Drive and parse the slide XML:
  1. Export: `svc.files().export_media(fileId=<presentation_id>, mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation')` → download to `/tmp/deck.pptx` (use `MediaIoBaseDownload`).
  2. Unzip: `unzip -o /tmp/deck.pptx -d /tmp/pptx_x`
  3. Extract text: for each `ppt/slides/slide<N>.xml`, `re.findall(r'<a:t>([^<]*)</a:t>', content)` and join runs — gives slide-by-slide text including tables, in slide order.
  This is the reliable way to identify which land/property a Prakash "R&D" market-research deck covers (see `kelsa-mcp` → `references/land-proposal-operations.md` → "Mapping an R&D PPT to a Kelsa proposal"). Slide 2-3 usually carry the village/taluk/survey-number facts; the closing slide says "Prepared by".
- **Compiling a single PDF dossier from Drive docs — use `references/pdf-dossier-compilation-pymupdf.md`** (verified 2026-09-02, Ranka Iris OC pack): `import pymupdf` (not fitz), builtin bold font is `hebo` (NOT `helv-b`), stale page-object trap after `insert_pdf` (fill ALL text last, fetch `final[pno]` fresh), index-numbering order, `.docx` export 403 (include the PDF twin instead), and subset extraction (`out.insert_pdf(src, from_page=2, to_page=5)` for "only pages N-M").
