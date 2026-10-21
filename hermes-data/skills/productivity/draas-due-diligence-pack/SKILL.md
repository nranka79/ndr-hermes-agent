---
name: draas-due-diligence-pack
description: "When ndr asks for a survey-number-level cross-reference of which legal opinion (CMS IndusLaw, J Sudha Reddy, D M Shiva Shankar, Sai Law Associates, or any other advocate) covers which Ranka Oasis / Ranka Udaya / Ranka Amber / Saveganapalli / SLP / JDA parcel — build a per-survey-number link table by walking the project's Legal folder on Drive, OCRing scanned opinions, and matching survey numbers to opinion recitals. Use when the user says 'which opinion covers this JDA land', 'title-clarity for each survey number', 'legal opinion cross-reference', 'due-diligence pack for Jiraaf / a bank / an investor', 'which advocate confirmed which title', or supplies an Excel with JDA / SLP parcels and asks for a per-parcel link to the confirming opinion. Distinct from `vendor-product-research` (third-party product evaluation) and `ranka-udaya-leads-pipeline` (DRAAS sales funnel)."
tags: [real-estate, due-diligence, draas, jiraaf, legal-opinion, title-search, india, tamil-nadu, karnataka]
metadata:
  hermes:
    tags: [real-estate, due-diligence, draas, jiraaf, legal-opinion, title-search, india, tamil-nadu, karnataka]
    category: productivity
    related_skills: [karnataka-land-title-due-diligence, property-title-due-diligence, real-estate-legal-compliance, google-workspace, ocr-and-documents, vendor-product-research, ranka-udaya-leads-pipeline]
---

# DRAAS Due-Diligence Pack Assembly

Cross-reference and verify project documents — legal opinions, area statements, architect certificates, execution plans, and approved sanctions — for DRAAS projects (Ranka Amber, Oasis, Udaya, NorthStar, Sevaganapalli / SLP land bank).

This skill is a project-specific LOOKUP against existing opinions/documents for the named DRAAS projects above — "which opinion already covers this parcel". For a fresh, ground-up title investigation on a parcel that doesn't already have a mapped opinion, use `karnataka-land-title-due-diligence`; for BBMP/MCA/Drive mechanics or khata/EC analysis, use `property-title-due-diligence`.

## When to load

**Legal opinion / title cross-reference:**
- ndr says: "give me a link for each survey number to the legal opinion that confirms title", "title-clearance for the JDA parcels", "due-diligence pack for Jiraaf", "which opinion covers 166/1 / 167/1G / 168/1B", "is there a title opinion for 177/1B", or any phrasing that implies "for each parcel, find me the document that confirms title".
- ndr supplies an Excel / sheet with a per-parcel list (survey no., extent, owner) and asks for a column of links to the title-clearing source.
- ndr mentions three or more named advocates / firms in one breath ("IndusLaw, Sudha Reddy, Shiv Shankar opinions") and asks for a per-parcel cross-reference against them.

**Area statement / project document verification:**
- Prakash or ndr shares a customer area statement PDF (Annexure-A format with unit-wise table) and asks to "verify it", "confirm it's correct", or "cross-check against source documents".
- The ask references multiple source documents by name: "architect area statement", "approved plan", "Supplementary Sharing Agreement (SSA)", "execution plan", "sanctioned plan".
- Any request to reconcile unit-wise area figures from a customer-facing document against architect-certified values — even if "due diligence" is not mentioned explicitly.

**Customer / case evidence pack from Gmail + Drive (beyond survey-number cross-refs):**
- ndr says: "build an evidence pack for this customer", "pull all emails + drive documents relating to <customer>, only relevant ones", "we need the readable PDFs of the emails", "clean up this folder, keep only docs related to <customer>".
- Full worked recipe in `references/customer-evidence-pack-emails-drive.md` (Mirabilis B1-203 / Sabyasachi Behera CMP/200628/0006093): eml → per-email folder (WeasyPrint PDF + email.txt + Attachments/), body-level relevance cleanup, process-sharded Drive uploads, dedupe rules for copies from colleague drives.

## Source locations (Drive, ndr@draas.com)

The full project / legal-folder inventory (cached from the 2026-07-13 Ranka Oasis work; re-verify on each invocation — folders move):

### Master legal folder
- `01_Legal_and_Title_Docs` (`1EmWRUvpjVb_BVxC-kl9JzSgaJhSt6hEN`) — the canonical hub. Contains `Legal_Opinions/`, `JDA_GPA_SPA/`, `Sale_Deeds/`, `Encumbrance_Certificates/`, `Patta_FMB_Records/`, `Litigation/`, `Saveganapalli Legal Docs/`, `Certified_Copies/`, `Gift_Deeds/`.

### Per-project Ranka Oasis folders (there are several duplicates; the canonical one is)
- `Ranka Oasis` (`1w947jyUeOH-k40qm4rrNwIc2j1BHwUTO`) — has subfolder `Legal/` (`1wD1kMPJ6RZNohMOVs8UF1qiPQL8LDnxI`) with per-SLP-parcel opinions.
- `Ranka Oasis Approvals` (`17pqfdNEW6leLDVfPGH62oNJ0bhFl5Id1`) — DTCP / RERA approvals.
- `Saveganapalli Legal Docs` (`1jOcoVXgUTdHc4qcoQduLTr3aSeArTPgx`) — sale deeds, ECs, FMBs, UDRs.
- `Sevaganapalli` (`1t4zCkyZBCIjOC1tAb0tofUu5V72F3kni`), `Sevaganapalli Project` (`1nqaW4PD3ehwVns0liy2M5TU5en2geXik`), `Sevaganapalli-Proposed Villa Project` (`16SKNX_hqau0Ye0lgr8GnmuN_vixLdrcA`), `DRA Sevaganapalli` (`1sTIJwqBROf8TgtQgndvKwuFN-_QopBhu`).

### The four named legal opinions on Ranka Oasis / Saveganapalli land (as of 2026-07-13)
1. **CMS IndusLaw Preliminary Title Report** (`1q3GVWG0KGbOB28KY6irKEcwNIL9D-NFT`, 63 pages, dated Oct 2025) — covers the 12.74 acres (SLP + DRA owned + discusses Ramesh Reddy JDA parcels in body).
2. **CMS IndusLaw Title Queries Revert** (`17ENOHaOE5EgTTxU2SlBQ7syWvqp8aILX`, dated 2026-06-02).
3. **J Sudha Reddy, Adv.** (`1Roo4fyMdEJgOYHj3Yv0iEmqxMoiHCE-h`) — covers 158/1C3, 158/1C4, 158/1C6, 158/1C9A, 167/2C (SLP owned).
4. **D M Shiva Shankar, Adv.** (`1p8qfavHXg4EMHB4_AZyrJVcEj4I7YRCW` "kencha reddy" 2021-01-19; `1UVxkEIEFw-32YAWIycGpbB_FQRD2rQE2` 2024-01-19 covering 176/1B2 etc.) — DRA Realty owned.
5. **Adv. N Manjunath (Sai Law Associates, Hosur)** opinions — multiple, e.g. `1kMYi1QKmCMb5KdbUA7lvpkk1Ss9NL779` "Legal Opinion_ S.No.167-1, Sevaganapalli" — **this is the one that covers 167/1G and 168/1B explicitly**.

### The JDA agreements (the only thing covering the K Harish JDA parcels 177/1B and 177/2A1)
- `JDA NO 6157 Btwn DRA Realty & K Harish` (`1Rt0huyG-7ReWT9v0I3110yA3TKMP-CS9`, 2025-09-25, 12.7 MB)
- `GPA No 6158 Association with Harish JDA` (`1PNW7VGd3oEE4kPC36pQV_W4XvV05V5r8`)
- `JDA NO 7963 Betwn DRA Realty & Ramesh Reddy` (`15UQ6kfLKKv8qfIBSudP6LiwD_NmbuOeC`, 2025-10-31) — covers 166/1, 167/1G, 168/1B
- `GPA No 915 Ramesh Reddy & DRA Realty` (`1MA2TNiVF7gonOf4lOWGQHNSK2NyUnZIh`, 2026-02-10)
- `2nd JDA Ramesh Reddy & DRA Realty` (`1MjyaChczwfFMYQV3Aw_lEqRYEPPq2OcH`, 2025-12-23)

### The Excel source
`20260707_DRA_Group_Investor_Portfolio_All_Projects` (Sheets id `1wDKS0SxtY0EF_-JUe2BfXzLSSwh4J5fo4y0sI_brFfw`). The `Ranka Oasis` tab has sections H, I, J, K, L, M listing per-parcel survey numbers, extent, owner, ownership type, and Legal Opinion notes. The JDA-only rows (ownership = "JDA" in column F) are the input to the per-parcel link table.

### Jiraaf Due Diligence Pack — "Ranka Deal Documents" (Oct 2026)
- The consolidated pack built for the Jiraaf investment review is **"Ranka Oasis — Jiraaf Due Diligence Pack (Oct 2026)"**, folder `1bAmETnOvt4fc8MBOQRh39BQOQOyKo8Uc` (owner ndr@draas.com), subfolders numbered **01–06 in the same order as Jiraaf's requirement list** (01 Project Location & RERA → 06 Agreements). Final structure after Sarthak's review pass (2026-10-07): 01 Project Location & RERA (RERA cert, OSS Master Plan 03.08.26-Sheet1, brochure, specs), 02 Sanctioned Layout & Approvals, 03 Land Schedule, 04 Title Reports & Legal Opinions, 05 Title Documents survey-wise, 06 Agreements.
- **Sensitive content was moved OUT of the pack before external sharing** (folder 07 Group & Enterprise Data, folder 08 Project Cost & Revenue): the enterprise sheet, DPRs, and the integrated cash-flow model went to a staging folder **`Z_Internal — NOT for external share (Giraffe DD removals)`** (id `1n7FPfPthJh4t6gvEMa3QWq8U_OI3XUNa`) — MOVE, don't delete, when internal users (Sarthak) still need editor access. Then delete the empty folder shells. No financial-model link ever goes into the outbound email; section 9 shows consolidated figures only.
- **Do not include in a lender/investor pack**: financial models, enterprise data, DPRs with costing (conflicts with email figures), any case-related docs (notices, affidavits, petitions), mortgage deeds between SLP and investors, and JDAs marked confidential (K. Harish JDA/GPA was removed — keep only the Ramesh Reddy JDA 7963/2025 + GPA 915 + GPA 16643/2023 + SPA). Keep ALL lawyer title opinions (IndusLaw + Jeevanandam + Manjunath etc). Move brochure + project specs into folder 01, not title docs.
- **Outbound email figures = Sarthak-corrected figures** (2026-10-07): structure & infrastructure **48.09 cr (Rs 48,08,70,000)**, finishing **18.74 cr (Rs 18,74,25,000)**, DRA free-sale revenue **139.74 cr (Rs 1,39,74,00,000)**; recomputed totals: future cost **122.09 cr**, projected revenue **212.35 cr** (NOT the pre-correction 134.86 / 204.83). Investor allotments: **15 plots+villas** at Rs 3,500 (east) / 3,300 (west) per sq.ft. — referral register shows 13 and the CF model says 14, flag this to Prakash rather than silently picking one.
- **Outbound reply thread**: Gmail thread `1a10c71519ac4760` ("Fwd: Ranka Deal Documents" from Nishant Prakash, 2026-10-05, forwarding Kanishk Sharma's requirement list). Final fresh draft `r6665899269779430470` (To Nishant Prakash, Cc kanishk.s@jiraaf.com, vineet@jiraaf.com, prakash.m@jiraaf.com, nishantprakash1@gmail.com) carries the master-folder link up top plus per-section subfolder links. **When re-drafting on a thread that already holds an older draft, delete the stale draft first** so the thread carries only one (deleted `r3020989636002646597`).
- Canonical internal review copy: Gmail thread `1a10c8bafc62632f`, "Re: Ranka Deal Documents — Jiraaf DD pack: draft reply for your review" (2026-10-05) — still the richest documentation table (RERA TNRERA/30/LO/3130/2026, JDA schedule, cost breakdown heads, 12-quarter timeline) even though its totals are the pre-correction ones; recheck against Sarthak's figures before quoting.
- **Jiraaf external users cannot be granted Drive access**: their Workspace admin blocks outside-org shares (kanishk.s@jiraaf.com, vineet@jiraaf.com, prakash.m@jiraaf.com fail) — needs NDR's call on link-share vs re-host. Nishant Prakash (nishantprakash@theyelloweye.com + nishantprakash1@gmail.com) is granted viewer 90 days and routes the docs.
- NDR voice: "giraffe" = **Jiraaf**.
- **Ranka Oasis × Jiraaf term-sheet family** (all in Balaji Land folder `1pKvhDHDFvMNJsEnveaRl-VGJ4tAuAKog`): v1.1 Key Terms `1bKUUKT35wx3SRPTa35kw4AsIWPHRlVWp2vS9zKw0icY` is the live/shared version (keep team access: Sarthak, Roshini, Nishant Prakash, Prakash etc). Older v0.1–v1.0 (`1z1q7dkR96tqM7quVCufJMb6RDIRC2xNztLaFhQQfdx4`, `1-WAsmpcrDJebCn1K6iOzERlE01Vz4z2TxFRrEiSIRcA`, `1Tv-NAta_LCFtwKk-HLs-gOsWf9TyYspJw_335Rou_Gg`, `1r9Nxo49V6gjJtcwm8uXTNiFavzWenolZT373JGmjjoQ`, `1fbImOTPrmKNk0GyGx9oaH3eimrGNig_iIeUOM-MMvtc`) were moved to private My Drive folder `1urBPARda5_iMlQavQNsajU7sB0zcYM2b` (owner-only, 2026-10-08) because they inherit the shared-folder team grants — see `draas-drive-organization` → `references/inherited-permission-removal.md`. The 25-Aug-2026 "Ranka Oasis x Jiraaf Capital - Structuring Mandate" email to Vishwas carried v1.1 as PDF; v0.4 was the Drive link given to Nishant Prakash.
- Access changes on this pack (e.g. grant viewer to internal staff): `draas-drive-organization` → `references/drive-access-audit-grant.md`.
- **Round-2 re-send: formatting from one mail, content from another (2026-10-08).** NDR sends a version himself, then asks for a fresh draft "in the formatting of <earlier email I sent>, content from <later email>". These are two different mails and **the later one's styling is normally lost** (it goes out flat after he re-pastes). He identifies them by **Cc list + rough time**, never by ID. Formatting source for this thread = the 5-Oct internal review mail (thread `1a10c8bafc62632f`, To Prakash Singh, Cc Roshini/Nishant Prakash/Bharat/Sarthak; Calibri, Google-ish palette, 13 × h3, 9 tables — drop its **FOR PRAKASH** yellow box); content source = the 7-Oct sent mail (msg `1a116ee0ea90db0d`, 12 × h2, no styling). Round-2 recipients: **To Nishant Prakash; Cc Prakash Singh + Sarthak Sharma only** (not Roshini/Bharat, not the Jiraaf team). Full recipe, HTML-part extraction code, and the Section 9/10 number history: `references/jiraaf-dd-pack-round2-email.md`.
- **Section 9 figures move — never publish a set NDR has not chosen.** Sarthak revised twice (6-Oct: 48.09 / 18.74 cr, DRA free-sale 139.74 cr; **8-Oct: structure & infra 57.48 cr, finishing 24.65 cr, HR & corporate 12.90 cr, BUA 2,94,780 sqft, Jiraaf saleable 95.12 cr, DRA free-sale 181.10 cr, clubhouse 5.50 cr**). The 8-Oct set supersedes — surface both and let him pick.
- **Destructive Drive work: plan first, execute after a yes.** NDR asks for "exactly step by step everything you are going to do — add, delete, move" before any cleanup. Then, after an edit pass, show back **only the changed sections** for review and only then draft the mail.
- **Round-3 outbound structure (2026-10-09): Section 10 (MIS / booking particulars) is DELETED, and the rest renumbers.** NDR's instruction: drop the "Investor allotments booked / rate allotted / villa size / contracted value / received to date / plots allotted" block entirely, so **10 = Expected timelines** and **11 = Approval status** (11 sections + Project snapshot; the header row "10. MIS" must be absent). The old Section 10 was where the 15-vs-13-villa discrepancy lived — removing it was how NDR closed that open item, so don't re-raise it. Round-3 draft: `r7010525338867523716` in thread `1a10c71519ac4760`, To Nishant Prakash, Cc Prakash Singh + Sarthak Sharma, HTML from the 5-Oct styling rebuilt over the 7-Oct content.
- **NEVER publish Section 9 without reconciling it to the LIVE model.** The email's cost heads are a coarse subset of the model and do NOT sum to the model's totals. Reading `Assumptions` + `12Qtr_Cash_Flow` in `1SubaopapjqfAVGbEoIYzaG-kftb50jkbga-XsDWuYU4` on 2026-10-09 showed the round-3 mail's rows tied to **140.68 cr** future cost while the model's own `TOTAL OUTFLOWS (B)` was **148.93 cr** — and HR, the strongest-cost line, sits at **12.68 cr** in the model against Sarthak's stated **12.90 cr**. Publish the figure set NDR chose, but compute and report the delta; see `references/jiraaf-dd-pack-round2-email.md` → "Round 3".
- **Verify every outbound link resolves before drafting, and scan the HTML for banned content.** Run `scripts/verify_dd_email_links.py` against the built body — it resolves each Drive folder/file ID and asserts no folder-07/08 ID, no spreadsheet ID, and no case/mortgage/JDA-6157 strings. 10/10 links verified this way on the round-3 mail.

## Standard workflow (4 steps, in order)

### Step 1 — Locate the canonical sheet, not the attachment
When the user says "the Excel in the email", the .xlsx is in Gmail (`messages.attachments().get()`). The same file usually lives natively in Drive as a Google Sheet — search Drive for `name contains 'DRA_Group_Investor_Portfolio'` and pick the one whose `mimeType` is `application/vnd.google-application/spreadsheet`. The Sheets API gives you per-cell access, stable IDs, and updates if anyone edits. (See `google-workspace` skill rule 6.)

### Step 2 — Extract the JDA-parcel list from the sheet
The Ranka Oasis tab is a structured questionnaire; JDA parcels are NOT in one block. They are scattered:
- Section I (rows ~131-150): every survey no. in the approved plan, with ownership type in col F ("Owned" vs "JDA"). JDA rows: **166/1, 167/1G, 168/1B**.
- Section K (rows ~165-181): "free from encumbrances" — repeats the same JDA rows with cumulative totals (Ac 0.95 = 35+7+53 cents).
- Section M (rows ~196-200): "Summary of JDA Land Area in the not approved plan" — **177/1B (32.3 cents) and 177/2A1 (17.7 cents) = 50 cents (Ac 0.50)**.

A good extraction query in the search later: `grep -F '177/1B\\|177/2A1\\|166/1\\|167/1G\\|168/1B\\|JDA'`.

### Step 3 — OCR the named opinions and grep for each survey number
Most of the opinions are scanned (image-based). Use the `ocrmypdf --skip-text -l eng` + `pdftotext -layout` pipeline from the `ocr-and-documents` skill, then `grep -F` for each JDA survey number. **Drive the OCR with the vault — `tools.gws_auth.build_service('drive', 'v3', service_name='google-draas')`, then `drive.files().get_media(fileId=...)` to download. Never read Drive OAuth tokens in plain text — see `google-workspace` skill section "Using Google Workspace API inside Hermes (Python Environment)".**

OCR time budget: ~2-5s/page on CPU. A 63-page opinion takes 3-5 minutes. Run the OCR for the big opinions in the background with `notify_on_complete=True` and use the time to look at the smaller ones (5-12 pages each, done in seconds).

### Step 4 — Assemble the per-parcel link table
For each JDA survey number, identify the documents that establish title:
- **Strong evidence**: a legal opinion whose schedule explicitly lists the survey number, or whose body walks the title chain through the registered Pattadhar.
- **Medium evidence**: a JDA agreement whose Schedule Item names the survey number and contains the owner's title warranty ("clear, absolute, and marketable title"). This is contractual, not an advocate's opinion, but it is what the bank sees.
- **Weak evidence**: a title report that names the survey number only as a boundary neighbour. The IndusLaw 2026-10 report is like this for 166/1, 167/1G, 168/1B — they appear as adjacent lands, not as properties for which title is opined on.
- **Missing evidence**: a JDA parcel with no opinion anywhere — **flag this loudly**. K Harish JDA parcels (177/1B, 177/2A1) are in this bucket as of 2026-07-13. Real exposure for any bank / investor diligence.

Output table format for Telegram:
- One bullet per survey number: `• 166/1 (Ramesh Reddy JDA, 35 cents) — [IndusLaw TR](url), [Legal Op S.No.167-1](url), [JDA No.7963/2025](url)`
- End with a "Gaps" section listing parcels with no opinion coverage.

## Survey-wise Legal Documents Matrix (TSR → DocMatrix spreadsheet)

When ndr/Prakash asks to build or restructure the per-survey legal documents matrix from a Title Search Report (TSR) — e.g. the Sevaganapalli / Ranka Oasis DocMatrix — the canonical spreadsheet is:

- **`20260809 Ranka Oasis - Survey-wise Legal Documents Matrix`** (Sheets id `1eVqckk3cCWdN06RNGISTP99WSz-aToCmGcNPIIqaicc`, service `google-draas`)

Sheet inventory (rebuilt 2026-08-10): `SUMMARY`, `PART_I_DocFurnished`, `PART_III_Schedule`, 34 `Sy_<survey>` sheets (one per survey no, 21 doc-type checklist rows each), `FLOW_CHARTS` (box-drawing tree per survey series), `PART_V_FlowOnTitle`, `PART_V_Flat_Backup`, `MISSING_DOCUMENTS`, `Documents as per CMS report`.

### PART_V_FlowOnTitle — accepted structure (Prakash, 2026-08-10)
Prakash's flow-on-title preference is **family-grouped row blocks** with box-drawing **origin → sub-division** trees. NOT family-grouped survey COLUMNS / checkmark matrices (that version was rejected earlier — see memory). Per family:
- Family header row (bold + colored, one per F1..F14 group).
- Each survey gets an **ORIGIN row** (`┌── 158/1A1`, UDR record: original pattadar, patta, extent), a **SURVEY HEADER row** (current owner, current patta, status, and the revenue-doc links — FMB / UDR A-Register / Adangal / EC / Patta-Chitta — in dedicated columns), then **chronological transaction rows** (`├──` / `└──` tree) each with its deed link.
- 19-column schema: `Family | Survey(stage) | Flow Tree | # | Date | Event/Doc Type | Doc No | Party From (owned what) | Party To (received what) | Extent | Patta | Transaction Summary (who owned → transferred/sold → to whom) | Deed Link | FMB | AReg | Adangal | EC | PattaLink | Status`.
- Status column color-coded: green = ACQUIRED / DRA REALTY, red = NOT DRA, amber = ⚠️ issues / errors.

### MISSING_DOCUMENTS sheet (companion deliverable)
Build alongside the flow sheet whenever Prakash asks for "missing / balance documents": columns `S.No | Survey No(s) | Document Missing | Why Required | Source/Basis | Priority (HIGH/MEDIUM/LOW) | Action Needed`. Compile from: (1) PART I rows marked "File not matched", (2) TSR Part V ⚠️ observations (death/LHC not furnished, extent discrepancies, patta errors, GPA not provided), (3) survey sheets with zero unique files. Group by gap type (Death/LHC, revenue docs, ECs, patta errors, missing deeds, zero-file surveys).

### TSR Part I → Drive folder audit ("does this folder have all furnished docs / duplicates / per-survey FMB-patta coverage")
Full worked recipe in `references/tsr-part1-folder-audit.md` (Sevaganapalli Oct-2025 TSR vs "Oasis - print" folder, 262 files, 107 Part I items). Core moves: match docno+year ANYWHERE in filename (strict regex false-negatives on `doc no 1834 dtd 26-04-1990`, `No 12988 0f 2017`); patta numbers live in the PDF text layer (`pdftotext` → `Patta No`), filenames only name the survey — "patta 1581c3.pdf" = Patta 1843; bare "Copy of <survey>.pdf" files are online FMBs (verify via pdftoppm → vision, which can't read PDFs directly); dedup by byte-size grouping THEN MD5 download-verify (same-size TN patta templates are NOT duplicates; MD5 is the arbiter); online pattas hide under "Land Registered in DRA Realty…" filenames.

### TSR Part I → Drive folder audit ("does the folder have all furnished docs?")

When Prakash/ndr sends a TSR PDF + a Drive folder link and asks "does this folder have all the documents furnished / any duplicates / all survey FMBs and pattas / list missing" — this is a distinct sub-workflow from building the DocMatrix sheets. Full worked example (Oasis - print, 262 files vs 107 Part I items, 2026-08-11) in `references/tsr-part1-folder-audit.md`. Key rules:

- **Folder 404 under ndr's token → it's likely psingh's folder.** Run GWS scripts with `HERMES_SESSION_USER_ID=psingh` prefix; verify the loaded account with `svc.about().get(fields='user')`. (Prakash owns "Oasis - print"; ndr's token can't see it.)
- **Bare "Copy of \<survey\>.pdf" files are ONLINE FMBs** (TN Survey & Settlement e-print: "Survey and Settlement Department … Survey No: 167/1G"). "FMB" does NOT appear in their filenames — do not report them missing. Spot-verify with `pdftoppm` + `vision_analyze` if unsure.
- **Patta PDFs are TN e-services printouts with text layers.** The real patta number lives inside the PDF ("Patta No : 1843"), NOT in the filename — e.g. "Copy of patta 1581c3.pdf" is actually Patta 1843, and "Copy of Patta 1672B.pdf" is Patta 204 (Billa Reddy). Batch-download all patta-named files and `pdftotext` each to build the real patta-number → survey map. TSR-listed patta numbers (1842, 281, 459…) may not appear in ANY filename.
- **Duplicate detection: group by normalized name, then MD5-verify.** Same byte-size alone is NOT proof of duplication — TN patta templates share identical sizes across different pattas/surveys (e.g. 156420 bytes for both 158(1A5) and 158(1A6)). Download candidates and hash before declaring duplicates.
- **Doc matching: extract (docno, year) pairs from filenames with MULTIPLE regex patterns**, not one strict pattern. Filenames vary wildly: "doc no 1834 dtd 26-04-1990", "Sale deed no. 4515", "No 12988 0f 2017" (letter-O typo), "no 248 1995". Fall back to bare docno match when year can't be extracted.
- **Same docno + DIFFERENT year = mismatch, not a match** (folder "1706/1980" vs TSR "1706/1986" — same number, wrong document). Flag it.
- **Death/LHC matching is person-name fuzzy, with false-positive traps**: Goova Reddy = Guvva Reddy (TSR spelling), "Nagareddy son of Guvareddy" = G.Nagi Reddy LHC, but Yellamma ≠ Yella Reddy (prefix match collides — verify the person is the same).

### Drive-folder vs TSR Part I audit (does the folder have all furnished documents?)
When Prakash/Nishant sends a TSR PDF **plus a Drive folder** and asks "does this folder have all the documents", "are there duplicates", "are all survey FMBs/pattas there", "list the missing documents" (worked example: Sevaganapalli TSR 20251014 vs psingh's "Oasis - print" folder, 262 flat files):

1. **Extract TSR text**: CMS-IndusLaw TSRs have a text layer — `pdftotext -layout` works, no OCR. Part I = "DOCUMENTS FURNISHED", numbered items 1..107, parse with regex `^\s*(\d{1,3})\.\s*(.*)$` (multi-line descriptions continue until the next numbered line).
2. **List the folder** recursively with Drive API (`includeItemsFromAllDrives=True`, pageSize 1000). DRA folders like "Oasis - print" are FLAT — 250+ files, zero subfolders.
3. **Identity override**: if the folder 404s under ndr's token, re-run the whole script with `HERMES_SESSION_USER_ID=psingh` (psingh-owned folders — see `draas-drive-organization` pitfall). Always confirm the acting account via `about().get(fields='user')`.
4. **Match by docno+year tokens anywhere in the filename**, not just "No. XXXX of YYYY" patterns. Filenames vary wildly: "doc no 1834 dtd 26-04-1990", "Sale deed no. 4515", "No 12988 0f 2017" (typo "0f"), "5585/1980", "GPA 12434 From Sarojaamma" (no year). Extract all `\d{3,6}` number tokens + `(19|20)\d{2}` year tokens per file; TSR "Document No. X" matches a file containing X (and year Y if the TSR states it). First pass with strict regex produces ~60 false "missing" — always do the token-anywhere pass before reporting.
5. **FMB items**: TSR lists Manual + Online FMB per survey. In DRA folders the bare "Copy of <survey>.pdf" files (e.g. "Copy of 167 1G.pdf", ~145–160 KB) ARE the online FMBs (TN Survey & Settlement Dept printouts). Verify ONE by rendering page 1 to PNG (`pdftoppm -f 1 -l 1 -r 120`) + vision, then trust the pattern. Do NOT report an FMB missing just because the filename lacks "FMB".
6. **Patta items — filenames lie; extract the text layer.** TN e-services patta PDFs have text ("Patta No : 1843", owners, survey rows). Folder files name pattas by SURVEY, not patta number — "Copy of patta 1581c3.pdf" is actually **Patta 1843** (Y. Suresh/Manjunath). Batch-download every patta-named file, `pdftotext -layout`, regex `Patta No\s*:?\s*([\w/-]+)` before declaring a TSR patta item missing. Same patta number repeats across survey files (Patta 25 = 158/1B3 + 158/1B4 + 167/2C + 158/1A5 + 158/1A6). The "Copy of Land Registered under DRA Realty..." files are the online pattas (Patta 2058 = DRA Realty).
7. **Duplicates**: exact filename dupes are rare; verify CONTENT dupes by MD5 of downloaded files. **Same byte-size ≠ duplicate** — TN patta templates share identical sizes across different content (156,418/156,420-byte pattas are different documents). Download same-size groups and hash before calling them dupes. In the Sevaganapalli audit, 16 same-size groups → 12 true MD5-identical pairs.
8. **Spelling variants**: Guvva/Goova Reddy, G.Nagi Reddy = "Nagareddy", Kencha/Kenchappa. But Yellamma ≠ Yella Reddy — match by first-name fragment but eyeball gender/naming before declaring a match.
9. **Report format**: verdict count (e.g. 31/107 missing), missing list GROUPED by type (FMBs, deeds, certificates, pattas), a survey-wise FMB/Patta coverage matrix from TSR Part III (34 surveys), and the MD5-verified duplicate list. Offer to log into MISSING_DOCUMENTS.

### Link verification when integrating docs into FlowOnTitle / PART_I (user requirement)
When Prakash says "add all the documents from this index/drive into FlowOnTitle" he ALSO expects **every Drive link verified against the document it claims to be**. Two checks per link:
1. **Resolvability**: `drive.files().get(fileId=..., fields='id,name,size,mimeType')` per unique link; a 404 = broken link (file deleted/access removed). In the 2026-08-10 audit, 12/136 links were 404 — report them as a broken-link list for the team to re-upload, don't silently drop them.
2. **Match**: file name/mimeType should confirm the claimed doc (e.g. a row claiming "Sale Deed 21201/2023" should point at a PDF whose name contains that deed number; a "Patta" link should not resolve to an EC). Flag mismatches — they are usually wrong-link-paste errors.
Only merge verified links into the flow rows; annotate broken/mismatched ones in MISSING_DOCUMENTS or a separate audit note. Also dedupe by normalized file ID when the same deed (e.g. 21201/2023 SLP sale) is the terminal transfer for many surveys — one link, many rows.

### PART_I_DocFurnished — NEW DOCS MUST GO UNDER THEIR SURVEY NUMBERS (Prakash correction, 2026-08-10)
When adding documents to PART_I from an external source (e.g. the Drive index spreadsheet), **do NOT append them as a flat list at the bottom**. Prakash's explicit rule: place each document **against the specific survey number(s) it belongs to** — either in the matching survey-numbered row/section, or in the document description so the survey no. is the first thing visible. A bulk "here are 49 new docs" append was rejected; the docs must be traceable per survey. If the source gives no survey mapping, derive it from the filename/description (`20230413-syno-158-1c9B…`, `Patta no.1006 [158/1A1]`) and annotate that survey. Highlight newly added rows (yellow fill + bold) and add a legend note.

### APPROVED_VS_NONAPPROVED classification (approved plan vs the rest, 2026-08-10)
When Prakash sends an approved plan (DTCP layout, TSR Part III schedule, CLU order) and asks to "separate the non-approved survey nos" across the workbook:

**SOURCE OF TRUTH = THE LAYOUT PLAN APPROVAL, NOT THE TSR PART III SCHEDULE.** On 2026-08-10 Prakash corrected us: "The approved survey nos are ones taken layout plan approval. Those in the approved layout to be separated." We had classified 34 surveys as APPROVED based on TSR Part III — that was WRONG and had to be rebuilt. The authoritative approved set is the **DTCP Layout Plan Approval** documents on Drive (they exist for the Sevaganapalli / Ranka Oasis layout: `20260113 Ranka Oasis Sevaganapalli Layout Plan – DTCP Krishnagiri` and the `20260330 ... Layout Planning Sanction – Sevaganapalli Panchayat & DTCP`, layout refs **SWP/DTCP/KRISHNAGIRI/LAYOUT NO. 03/2026 & 02/2026, dt. 13.01.2026, 130 plots, 30,416 sq.m / 7.52 Ac**).

**Ask the user per project which approval is the operative one.** A TSR Part III schedule lists the parcels in the title search — this is NOT the same as a DTCP/panchayat layout-approval list. The approved set is whichever layout/sanction grants plotting rights. Before classifying, confirm with the user (or by checking whether a DTCP layout approval exists on Drive) which document defines "approved".

1. **Extract the approved list from the OPERATIVE layout approval** (DTCP layout plan approval letter — it has an English schedule of survey nos + extents, even when the drawings are scanned Tamil; the approval letter itself usually has a clean text layer). If the DTCP approval letter is a scan, OCR it with the `ocr-and-documents` pipeline; the letter's English table of surveys is authoritative over garbled Tamil drawing labels. If NO layout approval exists, fall back to the TSR Part III and say so explicitly. When regexing a TSR: isolate the `PART – III` → `PART – IV` slice before regexing. A naive regex over the whole TSR catches the same survey numbers dozens of times (boundary descriptions "North By … East By …" repeat them) and pollutes the list. Item blocks split on `Item No. \d+`; each `Survey No. XXX measuring Y Acres`. Note the `176/1B2D part` variant with `0.03 ½` spacing — adjust the regex or add it manually.
2. **Classify every survey token found in every sheet** into three buckets:
   - **APPROVED** (green) = in the operative layout-approval schedule. For Sevaganapalli/Ranka Oasis the DTCP layout approval covers **19 surveys** (7.52 Ac / 30,416 sq.m / 130 plots): 158/1C9A, 158/1C9B, 166/1, 166/2B2, 166/3A, 166/3B, 166/3C, 166/3D, 166/3E1, 166/3E2, 166/3F, 167/1G, 167/2C, 167/2D, 168/1B, 176/1B2D, 176/2B4A, 177/1A1A, 177/1A1B. NOTE: this set differs from TSR Part III in BOTH directions — 166/1, 166/2B2, 167/1G, 168/1B, 177/1A1A are approved but were NOT in TSR Part III; ~20 TSR Part III surveys (158/1A1A–1C7, 167/1A–1I, 167/2B, 168/1A) are owned but OUTSIDE the approved layout (likely Phase 2 / future layout — offer to check the layout Phase 1 & 2 drawing).
   - **NON-APPROVED** (red) = parent/origin surveys (158/1, 158/1A1, 166/3, 176/1, 177/1A — the roots your approved sub-divisions come from) + adjacent/boundary surveys (158/1C8, 167/1G, 176/2B4B, 177/1A1A, 168/1B — mentioned only as boundary references, NOT owned).
   - **NOT A SURVEY** (grey) = false positives: doc registration numbers (`248/1995`, `300/2004`, `03/2016`, `14/95`), fractions (`1/3rd`, `2/3`, `1/10th`), combined notations (`167/1E/167/1F`, `158/1C9B/159/1C9B` = rename note, `176/177` = range shorthand). Filter these before reporting — otherwise the "non-approved" list is full of noise and alarms the user.
3. **Deliver in three places**: (a) new consolidated `APPROVED_VS_NONAPPROVED` reference sheet (S.No | Survey | Status | Extent | Reason | Sheets where it appears), color-coded by status; (b) a status column on the main flow sheets (PART_V_FlowOnTitle col U, PART_V_Flat_Backup col T) marking each row ✅ APPROVED / ❌ NON-APPROVED; (c) a `✅ APPROVED` badge appended to every `Sy_*` sheet's row-1 header. Key message for the user: non-approved ≠ title defect — they're parents + boundary parcels outside the approved schedule extent. **Ordering preference (Prakash, 2026-08-10): place the approved survey nos FIRST in the sheet, then the non-approved.** Don't sort by survey number — group by status, approved block on top.

See `references/tsr-approved-vs-nonapproved.md` for the worked example (approved list, full false-positive table, classification code pattern).

### Build mechanics (Sheets API)
- **Backup first**: copy the current sheet's values into a `PART_V_Flat_Backup` sheet before rebuilding — Prakash iterates on this structure; nothing gets lost.
- Build rows in Python, write via `values().update(..., valueInputOption='USER_ENTERED')`, then format via `batchUpdate`.
- **`foregroundColor` for cell TEXT lives inside `textFormat.foregroundColor`, NOT top-level `userEnteredFormat.foregroundColor`** (400 "Unknown name" otherwise). Background color IS top-level `backgroundColor`.
- Batch `batchUpdate` requests ~100 per call with `time.sleep(1)` between (Sheets 60/min limit, 429 → 60s).
- **Color-coding many rows: GROUP CONSECUTIVE SAME-STATUS ROWS into one range, don't emit one `repeatCell` per row.** 720 single-row color requests exceeded the 60/min write quota mid-batch; collapsing runs of identical status into contiguous `startRowIndex:endRowIndex` ranges cut it to 24 requests. Implement with a run-length encoder over the status column, then batchUpdate the few ranges. Same trick applies to any per-row formatting (colors, bold, borders).
- Freeze header row (`gridProperties.frozenRowCount: 1`), set `pixelSize` column widths, `wrapStrategy: WRAP` on summary/party columns.
- Build the per-survey doc-link map once by reading all `Sy_*` sheets and de-duplicating files by Drive link — survey sheets repeat the same file under every doc-type heading, so classify by filename (fmb/adangal/udr/ec/patta/sale deed…) rather than trusting the heading row.

See `references/tsr-docmatrix-flowontitle.md` for the full family list, exact headers, and the 2026-08-10 worked example.

### Folder audit vs TSR Part I (DOCUMENTS FURNISHED) — "does the folder have all the documents?"
When Prakash/ndr sends a TSR PDF + a Drive folder link and asks whether the folder holds everything on the
furnished-documents list, checks for duplicates, or wants a per-survey FMB/patta coverage + missing list,
use `references/tsr-folder-audit.md` (worked example: Sevaganapalli TSR vs `Oasis - print` folder). Key moves:
parse Part I via `pdftotext -layout` + numbered-line regex; match by docno+year tokens ANYWHERE in filenames
(not just `No X of Y`); confirm duplicates by MD5 (same size alone is NOT proof — TN patta templates share
sizes); extract patta numbers from the PDF text layer (survey-named files carry the real patta no, e.g.
`patta 1581c3.pdf` = Patta 1843); bare `Copy of <survey>.pdf` files are online FMBs. psingh-owned folders
need `HERMES_SESSION_USER_ID=psingh`.

### EC documents → PART_I sheet → Drive folder availability (2026-08-13)
When Prakash uploads EC PDFs, gets the parsed per-survey transaction tables
(see `ocr-and-documents` ref `tn-ec-transaction-parsing.md`), then asks
"are these documents in PART_I?" and "are the not-available ones in this
Drive folder?" — full recipe in `references/ec-part1-drive-availability.md`.
Core moves: extract (docno, year) pairs from PART_I rows with MULTIPLE regex
patterns (incl. date-column-year fallback and "3427/3428 related" pairs);
date+description fuzzy match for ext-index rows without doc numbers (watch the
**YYYYMMDD month/day swap**: `20240302` → 2024-03-02, not 2024-02-03);
**same-date ≠ same-doc** (19345/2023 listed but EC also has 19344/19346/19356/2023;
4515/1995 vs 4512/1995; 12569/2023 GPA vs 12669/2023 release) — verify date-fuzzy
hits manually; recursively walk the Drive folder (891 files incl. "Unique Set (291)")
and match docnos from filenames with number-only fallback + type/context verification.
Deliver as NEW color-coded tabs (green available / red missing), never modify
existing sheets; a second tab when the Drive check is requested after PART_I.

## Physical Document Binder Indexes

Many DRAAS projects maintain **master index spreadsheets** that track documents in **physical binders** (File 1, File 2, etc.). These binders hold original or photocopy documents — sale deeds, endorsements, DC letters, gift deeds, ECs, patta records — organized by sl-no and indexed with document reference numbers.

**When to use this workflow:**
- The user asks about document numbers that look like government refs (e.g. `LLN(NY)SR 60/16-17`, `ALN/NAY/SR/60-2016-17`)
- The user asks "do we have this document" or "find this file number" across a project
- A compiled PDF on Drive turns out to be a scanned collection of physical binder documents

**Where to find the index:**
Search Drive for a spreadsheet whose name contains `Index` and the project name. For Allalsandra NorthStar, the canonical sheet is `Allalsandra Index inc MDR & Anup Doc's`. The index sheet typically has columns: Sl No | Doc Type | Doc No | Date | Pages | Original/Photo | File No (physical binder number). Each binder (File 4, File 5, File 7) maps to a range of serial numbers.

**Workflow (4 steps):**

1. **Search the index spreadsheet for the ref number first.** Parse the index sheet's rows looking for the requested document number, its variant spellings (`LLN(NY)SR` / `ALN/NAY/SR` / `ALN(NAY)SR`), and partial matches (just the number like `60/16-17`). Record which File binder and Sl No it lives in.

2. **Report the physical binder location explicitly.** Always say "File 4, Sl No 172-175" or "File 5, Sl No 193-194" — never just "it's in the index". Cite the exact sheet name and row numbers. (See sourcing pitfall below.)

3. **Check if a compiled PDF on Drive contains it.** Compiled PDFs (often named `Allalsandra Docs Legal Set.pdf`, `Allalsandra North Star Legal Opinion.pdf`) are NAPS2-scanned versions of the physical binder documents. Check them only AFTER the index confirms the document exists — the compiled PDFs may not have all the binder contents, and their scan quality may be too poor for any automated OCR tool (tesseract, vision_analyze, pymupdf).

4. **Be honest about limitations.** If the compiled PDF scan quality is trash (faded typewriter, handwritten Kannada, 150 DPI scans), tell the user: "This document exists in the physical binder at File N, Sl No X-X. The compiled PDF scan on Drive is too poor for automated reading — you'll need to check manually."

**Scan quality reality check (verified Aug 2026):** Allalsandra Docs Legal Set.pdf (291 pages, NAPS2 at 150 DPI) — tesseract kan+eng and vision_analyze both return mojibake on most pages. This is a source-document limitation, not a tool failure. When both OCR and vision fail, report the limitation and direct the user to manual inspection or the physical binder. Do NOT keep retrying.

## Pitfalls

- **Always cite the exact index sheet name and sl-no when reporting document locations from a physical binder index.** Never say "File 4/File 5 in the index" without specifying the spreadsheet sheet name and the row numbers. The user will ask "which index and which row" if you hand-wave. Example: "Allalsandra Index inc MDR & Anup Doc's sheet, Sl No 172-175 in File 4" not just "File 4".

- **Don't assume the named opinions cover the JDA parcels.** When ndr says "industrial / Sudha Murthy / Shivkumar opinions", verify by grep, not by file name. The IndusLaw = industrial confusion burned us in 2026-07-13 (the user corrected "industrial → Indus Law") and the J Sudha Reddy / D M Shiva Shankar opinions turn out to cover the SLP / DRA owned land, not the JDA. The 7.22-acre IndusLaw opinion is the **most recent** one and only mentions the JDA parcels as boundary descriptions.
- **OCR can be slow on big legal opinions.** A 63-page opinion = 3-5 minutes on CPU. Either accept the wait (start it backgrounded, work on smaller docs meanwhile) or OCR only the first 5-10 pages if ndr just wants the cover, schedule, and opinion paragraphs. The schedule is usually on page 2-3; the opinion/conclusion on the last 2-3 pages.
- **Don't conflate "title report" with "title opinion".** A title report is a chain-of-title narrative. A title opinion is the advocate's final statement ("we are of the opinion that the title is clear, marketable, and free from encumbrances subject to …"). The IndusLaw 2026-10 document is a title REPORT, not a title opinion — its final paragraph is the schedule of properties, not an opinion. The 2024-09-26 SLP opinion (`1Gmkw7Dr2uhl-bJrFLNbljP0uCue5dikj`) is closer to an opinion for the SLP land.
- **Multiple folders for the same project.** Drive has 3-4 different "Ranka Oasis" folders, 2-3 different "Sevaganapalli" folders, and at least 2 "Legal Opinions" folders. Walk the master `01_Legal_and_Title_Docs` first, then fall back to the per-project folders. Don't pick a folder at random — it will likely be a stale duplicate.
- **Voice transcription mangles Indian proper nouns.** "Industrial" → "Indus Law", "Sabji" → "Sahabji", "GPD" → "GPT", "Dham" → "D M". Before you rephrase a user's mention of a firm / person / place, **check the actual documents on Drive** for the canonical spelling. The legal-opinion file names always use the correct spelling; the user's voice note is the unreliable source.
- **Voice memo may describe a chain of recipients in shorthand.** "we sent it to Vinith and Nishant" might be To: Vineet Agrawal, Cc: Nishant Prakash (and Prakash Singh). Always fetch the full message with `format='full'` (not the search-result snippet) before answering questions about who was on the email. The Gmail bridge's `gmail_get_message` doesn't exist — use `gmail_thread_get` or call `build_service('gmail','v1').users().messages().get(format='full')` directly. See `google-workspace` pitfalls.
- **The .xlsx attachment vs the Drive-native Sheet** — see google-workspace rule 6. Always read the Sheet, not the attachment, for anything that may have been edited since the email was sent.
- **Survey numbers with prefixes (158/1C1 vs 158/1C2 vs 158/1C)** are DIFFERENT parcels. Grep the full string with `grep -F` to avoid partial matches. The same applies to letter-suffixed subdivisions: 168/1A vs 168/1B.
- **JDA parcel ownership is in column F, scattered across sections.** On the Ranka Oasis tab the JDA rows are not in one block. Section I (rows ~131-150) lists every survey in the approved plan; JDA rows have col F = "JDA". Section K (rows ~165-181) repeats the approved-plan JDA rows (166/1, 167/1G, 168/1B) with cumulative totals. Section M (rows ~196-200) is the not-approved-plan JDA (177/1B, 177/2A1). Extract all three sections, dedupe by survey number, and union the result. Don't trust a single section.
- **Don't share the JDA agreements publicly without ndr's confirmation.** The JDA agreements contain personal details of the landowners (Ramesh Reddy, K Harish Family), financial terms, and parties' addresses. They are confidential to DRA and the landowner. Share links inside Drive (with appropriate access) only; do not download-and-send to a third party.

## Related skills
- `google-workspace` — vault-isolated GWS access (read this first; OAuth is non-trivial).
- `ocr-and-documents` — `ocrmypdf --skip-text` + `pdftotext -layout` is the OCR pipeline you'll use 80% of the time.
- `ranka-udaya-leads-pipeline` — sibling class for the DRAAS sales-funnel side; the DRA Drive folder inventory overlaps.
- `messaging-drafts` → `references/personal-messaging-workflow.md` — once the table is built, ndr often wants a WhatsApp message to Vineet Agrawal / Nishant Prakash summarising the result. Use the `whatsapp_link` tool, never hand-encode wa.me URLs.
- `email-drafter` — for the email-back to ndr / Nishant Prakash / Vineet with the link table. When NDR asks for a re-send "in the formatting of <an earlier mail of mine>, content from <a later mail>", use `email-drafter` → `references/mail-formatting-source-reuse.md` (locate both mails by their Cc lists; the bridge body is text/plain only and hides styling, so extract the real `text/html` part with `format='full'`).

## Drive Filing Convention

After processing a legal document, see `references/drive-naming-convention-for-legal-docs.md` for the DRAAS document naming rules: project name first, abbreviated entity, case number, no survey numbers where context makes them obvious.

## Reference
- `references/physical-binder-index-workflow.md` — worked example (2026-08-21): cross-referencing physical document binders (File 4, File 5, File 7) against a master index spreadsheet and compiled PDFs for Allalsandra NorthStar. Load this when the user asks about document ref numbers like `LLN(NY)SR 60/16-17` or any query involving physical binder indexes.
- `references/ranka-oasis-jda-link-table.md` — worked example from the 2026-07-13 session: the per-parcel link table for 166/1, 167/1G, 168/1B, 177/1B, 177/2A1, with the specific IndusLaw, J Sudha Reddy, D M Shiva Shankar, Adv. N Manjunath, and JDA / GPA file IDs and Drive links. Read this as a template the next time a similar table is needed.
- `references/tsr-approved-vs-nonapproved.md` — worked example (2026-08-10): extracting the approved survey schedule from a TSR Part III, the 3-bucket APPROVED/NON-APPROVED/NOT-A-SURVEY classification with the full false-positive table, and the rate-limit grouping trick for coloring hundreds of rows in Sheets.
- `references/ec-part1-drive-availability.md` — worked example (2026-08-13): EC master list (131 docs) vs PART_I_DocFurnished vs a Drive folder — multi-regex docno extraction, date-fuzzy matching pitfalls (YYYYMMDD swap, same-date-different-doc), and the two-tab color-coded delivery pattern.
- `references/karnataka-title-opinion-reading.md` — worked example (2026-09-03, Gunjur Sy 40 / Pattanshetti / BRK Law): reading a scanned 24-page Preliminary Title Report page-by-page with vision_analyze, the continuation-sheet structural map (discussion→endorsements→EC→Opinion 9.x→Annexures), the opinion-strength ladder ("absolute owner" vs "valid and marketable" vs "may be considered valid ... subject to verification"), the standard caveat/blocker list (grant order/saguvali chit, EC gaps, old O.S. records), and filing the report + fee bill into the source-document Drive folder with YYYYMMDD naming. Load this when scanning an advocate's title report from an email attachment.
- `references/customer-evidence-pack-emails-drive.md` — worked example (2026-09-09/10, Mirabilis B1-203 Behera RERA case): full eml→PDF evidence-pack pipeline (WeasyPrint render, per-email folders with attachments, body-level relevance cleanup), the RecursionError big-stack fix, process-sharded Drive uploads, and the pack folder layout. Load for any "evidence pack for this customer/case" ask.
- `references/area-statement-verification.md` — verified 2026-08-19 (Ranka Amber): cross-verify a customer area statement PDF against the architect-certified area statement (DOCX), execution plan (Sheet), and approved plan sanction. Unit-by-unit comparison, overall totals reconciliation, and common pitfalls (balcony discrepancies, common area loading apportionment, Floor/FSI/UDS checks). Load this reference when the task matches the "Area statement / project document verification" trigger conditions.
- `references/jiraaf-dd-pack-round2-email.md` — the Jiraaf DD-pack outbound-email playbook, rounds 2 AND 3 (2026-10-08/09): the "formatting from one mail, content from another" recovery recipe (identify both mails by Cc list, extract the real `text/html` part), the Section 9 figure history, the Section 10 deletion + 10/11 renumbering, and **the model-vs-email reconciliation table**. Load this for any re-send on the Jiraaf / lender thread.

### Scripts
- `scripts/verify_dd_email_links.py` — pre-flight check on a BUILT HTML email body: resolves every Drive folder/file link, scans for banned content (cash-flow model, enterprise-data folder, case documents, mortgage deed, pulled JDAs) and asserts the section renumbering. Run with `cd /opt/hermes && PYTHONPATH=/opt/hermes python3 scripts/verify_dd_email_links.py <body.html>`; exit 1 means do not draft. Adapt `BANNED_STRINGS` per matter.
