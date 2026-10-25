# Multi-Account Project Document Collation ("search everyone's drive/email for <project>")

Reusable runbook when NDR asks to gather EVERYTHING on a property/project (e.g.
Embassy Habitat 914/1503) from his own drive+mail PLUS colleague accounts, compare
against what we hold, categorize (Common / Unit-A / Unit-B), and consolidate new
docs into his Drive. Verified 2026-09-14 on the Embassy Habitat 914/1503 exercise.

## Phase 0 — resolve the accounts FIRST (cheapest failure to catch)

Colleague emails come from voice dictation and are unreliable. Run
`gws_dwd_resolve` on each spoken email — but remember resolve pattern-matches ANY
`x@draas.com` (regex domain check only), so `direct: True` does NOT mean the account
exists. Probe each with a cheap `drive_list` (`query: "name contains 'a'"`):
- invalid_grant → account does not exist (e.g. "SV@DRAST.com" → sv@draas.com FAILS;
  real = rajendra@draas.com, initials in his NAME not his email prefix)
- Verified map: `gws-domain-admin/references/colleague-account-map.md`
- Confirmed 2026-09-15 (Ranka Oasis 5-drive sweep): NDR's voice list "Bhaerat Anbu
  Bhaagya Sinchana Kanteish" maps to **Bharat Havaldar = sales1.blr@draas.com,
  Anbarasan ("Anbu") = pm2.blr@draas.com, Bhagya G = crm.blr@draas.com,
  Sinchana Gowda = sgowda@draas.com, Kantesh B G = kanteshbg@draas.com** — all
  DWD-impersonatable with the drive scope.

## Phase 1 — source of truth on NDR's side (BEFORE searching colleagues)

1. Recursive walk of the project's existing Drive folder (name + folder ID + size +
   owner + parent chain) via per-user token (`_load_credentials_direct('google-draas')`).
2. Save the file-ID set — dedupe later is BY ID, not by name.
3. Also search NDR's OWN gmail (own OAuth token, NOT DWD — DWD on his own account can
   return 0 where the real mailbox has hits): `"Embassy Habitat"`, `"914"`, `"1503"`,
   Vasanthnagar, floor plan, etc. His mail often carries the full purchase/legal chain.
4. Record the ownership split of the existing tree (ndr-owned vs colleague-owned) —
   colleague-owned files already in OUR tree also need ownership transfer later.

## Phase 2 — sweep colleague drives and mailboxes (DWD)

Drive (per account): name-contains queries — the project name, its aliases
(Embassy/Embassy Habitat/habitat), unit numbers ("914", "1503"), area name
(Vasanthnagar), plus "floor plan". Colleague drives mirror his own files → expect
many ID-duplicates (skip them, no point replicating).

Gmail (per account): target the phrase + document-type queries
(`"Embassy Habitat" sale OR deed OR registration OR agreement`,
`"Embassy Habitat" society OR maintenance OR khata OR BESCOM OR tax`). Keep
subject/from/date from the search summaries (already enriched) — do NOT re-fetch
every message. Generic number queries return heavy noise (bills, order receipts,
ITR/Succession threads) — filter subjects with a regex before fetching full threads.

## Phase 3 — walk matched folders with a PRUNE filter

Colleague "project" folders are junk drawers (Bharat's 914 Title Documents folder
contained Ranka Amber, Oasis, Serenity, Sarayu Ayodhya RERA files). When walking:
- PRUNE branches matching other projects (`ranka amber|oasis|serenity|thindlu|
  sarayu|seva...|whatsapp|architectural|creatives...`)
- KEEP files whose name/path matches the project regex
- Verify suspicious generic plan-looking files by downloading + OCR — Sarayu Ayodhya
  approved-layout PDFs looked like building plans but were a UP project.

## Phase 4 — classify + consolidate

- Buckets: Common (society/CAM/agreements/annual reports), unit-specific by unit no.
- Email-attachment-only docs: pull bytes with `gws_dwd_gmail_attachment_get`
  (base64url → `urlsafe_b64decode(data + '=' * (-len % 4))`), verify with pdfinfo,
  upload into the right bucket.
- Drive docs not already owned: use the cross-owner migration sequence
  (`references/cross-owner-bulk-migration.md`): MOVE first via the owner's
  impersonated token → TRANSFER ownership → leave a shortcut in the original spot.
- Deliver a categorized inventory sheet (name, source account, bucket, Drive link).

## Phase 4.5 — build the master inventory sheet (ALL drives, one row per unique file)

When NDR asks for a master inventory ("which account, which drive, whole chain,
file name, link, type, what it's about") as a FIRST step before consolidation:

1. **Dedupe by file ID, not by name/account.** The same shared file surfaces in
   every account that can see it — the Ranka Oasis 5-drive sweep had 5,477 raw
   hits collapsing to 3,151 unique items (2,862 files + 289 folders). Keep a
   `found_in: [account labels]` list per file ID; sheet column "Also Found In".
2. **Resolve owner chains, not viewer chains.** The canonical row is the OWNER's
   chain: walk `parents` up to root with the owner's DWD token (or any account
   token that can read the file — parents resolve the same). Render root as
   `My Drive` when `driveId` is empty, else the shared-drive name.
3. **Columns that worked** (validated 2026-09-15, Ranka Oasis sheet):
   `File Name | Type | What It Is (Description) | Owner Account (Display) |
   Owner Email | Drive | Folder Chain (My Drive > ... > file) | Size | Modified |
   Also Found In | File ID | Link` — Link column written as
   `=HYPERLINK("url","open")` with `USER_ENTERED`.
4. **Descriptions matter to NDR — enrich them, don't echo filenames.** Tiered:
   (a) Google Docs/Sheets → read first content chunk via docs/sheets API on the
   owner's token (real snippet like "TERM SHEET Proposed Commercial Arrangement");
   (b) filename+path classifier for plans (parse orientation East/West, sqft,
   Type T1–T3, NON STD, OPT-2 from names like `OASIS- EAST (1800 sqft ) NON STD 32`);
   (c) acronym expansion for SPA/WO/PO/GPA/ATS/EC/FMB/RERA/BOQ/MoU/RTC/GST/PAN;
   (d) last resort, name-derived label. Target zero "see folder context" rows.
5. **Summary tab** (generated counts): unique files vs folders, BY OWNER ACCOUNT
   table, BY FILE TYPE table, target-folder IDs, and NDR's stated next steps so
   the sheet is self-documenting for the consolidation round.

## Phase 5 — file TYPE/description classification helpers

- Once the master inventory exists, the NEXT step NDR asks for is per-row bucket mapping ("map each file into the target project folders, add the column, row by row") — see `references/inventory-bucket-mapping.md` (two-pass classifier, content-check leftovers via DWD media download, 14-bucket Oasis taxonomy verified 2026-09-15).

- MIME map for Google-native + office types (folder/doc/sheet/slides/shortcut/
  xlsx/docx/pptx...), with `.dwg`/`.dxf`/`.skp`/`.rvt` fallbacks. Shortcuts are
  type `Shortcut` (36 of 3,151 in the Oasis sweep — they matter for migration).

## Pitfalls hit

- **`includeItemsFromAllDrives=True` is INVALID on `files().get()` — only
  `supportsAllDrives=True` is accepted there** (hit 2026-09-15). Passing both
  kwargs makes EVERY parent lookup fail with `Got an unexpected keyword argument
  includeItemsFromAllDrives`, which silently poisons parent-chain resolution for
  the whole inventory. `includeItemsFromAllDrives` is a `files().list()` kwarg;
  on `get()` drop it and keep only `supportsAllDrives=True`. Fix = delete the
  kwarg; 5,477 chains resolved instantly.
- **Fresh spreadsheet's default tab is "Sheet1", not "Inventory"** — writing to
  `Inventory!A1` before renaming throws `Unable to parse range: Inventory!A1`.
  After `spreadsheets().create()`, rename tab 0 via `updateSheetProperties`
  (fetch `sheetId` from the create response) then write.
- **Voice-collation account probes:** `gws_dwd_resolve` pattern-matches any
  @draas.com — an `unauthorized_client` error on a candidate address means the
  account EXISTS but isn't impersonatable at that address; `invalid_grant` means
  no such account. Probe each candidate with a cheap drive_list (`name contains 'a'`).

- `gws_dwd_drive_list` with an account KEY ("mdr") instead of email → VaultError.
  Always pass the actual email.
- DWD drive walk caps listing at 100 per folder page; walk recursive subtrees for
  full coverage but keep the PRUNE filter or you drown in other projects.
- `vision_analyze` may 503 mid-sweep (no provider configured) — rotate scan pages
  180° and retry, or fall back to tesseract; don't loop on the same image.
- WeasyPrint/DWD note: DWD `gmail_get`/`thread_get` still return attachment metadata
  only for the READ — bytes come from `gws_dwd_gmail_attachment_get`.