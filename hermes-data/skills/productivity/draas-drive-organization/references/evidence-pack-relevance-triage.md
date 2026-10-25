# Evidence-pack relevance triage ("keep only what relates to <person/matter>")

Trigger phrases: "this folder has a lot of unrelated documents", "go through every document
and make sure the only documents we keep are anything related to <customer>",
"re-analyze and delete anything not related to <name> from this folder". Usually aimed at a
case/evidence pack built for a lawyer, where a search sweep dumped the whole project's
documents in alongside the one customer's.

## Pack shape (DRAAS evidence packs)

```
20260909_<Matter>_EvidencePack/          <- pack root (the link NDR shares)
├── README.md                            <- how the pack was built; often claims doc sets that AREN'T actually in it
├── Manifests/                           <- per-account CSV: file, message_id, thread_id, date, from, to, cc, subject
├── Documents_Collected/                 <- the Drive docs (this is what "documents collected" means)
├── Emails_NDR_<account>/                <- raw .eml dumps, can be 100s of MB–GBs
└── Emails_<colleague>_<account>/
```

Read README.md + Manifests/*.csv FIRST. The manifests give you metadata for every email
without downloading anything, so email folders can be triaged by metadata before you touch
bodies. Beware: metadata-only filtering over-captures (same-surname people, non-person
homonyms) — bodies must be scanned before actually trashing emails.

## Workflow

1. **Enumerate recursively** (`files().list`, pageSize=200, `trashed=false`,
   `supportsAllDrives=True`) and keep the full `name` + `id` map. Do not trust a previous
   session's listing — re-walk.
2. **Download every doc** to `/tmp/<pack>/`, sanitising filenames
   (`re.sub(r'[^A-Za-z0-9._-]', '_', name)`). Track `{name: id}` separately so the sanitised
   path never becomes your key.
3. **Extract text per type** (see matrix). Stdlib only — no openpyxl/pymupdf needed.
4. **Keyword-scan** case-insensitively for: full name, first name, surname, co-allottee /
   co-applicant names, flat/unit number, case/complaint number, email local-part.
5. **Classify with an explicit rule you state in the report.**
6. **Trash, don't delete** — recoverable. Restore is `body={'trashed': False}`.
7. **Verify** by re-listing, then report kept / trashed-grouped-by-reason / judgment calls /
   gaps / remaining duplicates.

## Text-extraction matrix (no third-party deps)

| Type | Method |
|---|---|
| `.pdf` | `pdftotext -layout -f 1 -l 25 file -`; if result `<80` chars → `pdftoppm -r 150 -gray -png` pages 1–2 then `tesseract` (method tagged `ocr2pg`) |
| `.xlsx` / `.xlsm` | `zipfile` → read `xl/sharedStrings.xml` + `xl/worksheets/sheet*.xml`, strip tags. Full cell coverage, no openpyxl. |
| `.docx` | `zipfile` → `word/document.xml`, strip tags |
| `.doc` / `.bin` / `.mpp` / `.xls` | `strings -n 4` |
| `.html` | strip `<style>…</style>` and `<script>…</script>` FIRST, then tags |
| `.jpg` / `.png` | `tesseract file stdout` |
| `.csv` / `.md` / `.txt` | read directly |

Run inside `terminal()` with `HERMES_SESSION_USER_ID=ndr` and
`/opt/hermes/.venv/bin/python3` (the sandbox `execute_code` has no vault socket). Re-runnable
extractor: `scripts/drive-doc-pack-extract.py`.

## Classification rule that matches NDR's intent

KEEP if the document:
- names the person **or a co-allottee/co-applicant** (for a booked flat, always search the
  co-applicant too — the file may be in the co-applicant's name, e.g. "Damayanthi Behara &
  Sabyasachi Behara"); or
- is single-unit / single-matter specific about their unit or case (their judgement, notice,
  objection, writ, demand notice, unit sheet, possession/handover letter); or
- is a multi-customer tracker that **contains their name** — NDR's own rule: *"even if it
  pertains to multiple other customers, but there is <X> in it, only then we must keep it."*

DELETE if it is: a project-level instrument (JDA, GPA/PoA, legal opinions, sanctions,
builder NOC, EC, tax/betterment receipts, bank loan agreements, cost sheets, templates,
marketing collateral), another buyer's document, or a project-wide multi-unit list where the
only hit is an anonymous unit number with no name.

Judgment calls (state them explicitly in the report and offer to reverse): documents that list
the subject's unit among many without naming them (SPOA listing flats, project area/inventory
statements, UDS sheets). Default: delete, flag, offer restore — all four went to trash in the
Behera pack and were called out by name in the report.

## Pitfalls

- **NEVER derive your keep-set key from a display tag like `mimeType.split('.')[-1]`.** For
  macro-enabled files that yields artifacts such as `"[12]"` (from
  `application/vnd.ms-excel.sheet.macroEnabled.12`). A listing printed that way produced a
  keep-list entry `"[12] Mirabilis Customer Statement Invoice Generator 15MAR2020.xlsm.xlsm"`
  which never matched the real Drive `name`, and the cleanup script trashed a file that should
  have been kept. Key on the Drive `name` field verbatim, always; verify `KEEP not found: {...}`
  is empty before executing, and re-list afterwards.
- **Snippet, not hit-count.** High hit counts on financial workbooks are usually rupee amounts
  or row IDs, not names. And numeric identifiers false-positive hard: an Aadhaar number
  contained `6093`, and amount columns contain `-6093.0`. Always read ±70 chars around each
  hit and print snippets, not just counts.
- **Homonyms and same-surname people.** In one folder: `Ipsita Behera` (a *different*
  customer, flat A-1002 — her on-boarding emails are not the subject's), a 2017 sales *lead*
  named "sabyasachi", and a jewellery brand email ("Tata CLiQ … Sabyasachi Fine Jewellery").
  Classify by context, never by the token alone.
- **Names split across XML runs.** In `.xlsx`/`.docx` a name can be split across `<t>` runs, so
  a regex for the full first name can miss while the surname matches. Cross-check with surname
  and unit number.
- **Scanned PDFs are only OCR'd pages 1–2 in the fast pass.** Report those as "no text /
  first-N-pages only" — do not assert they are irrelevant. Say so as a limitation.
- **Never judge by filename.** In the Behera pack the "SALE DEED No1127/1150/1161/1194" files
  were Ooty/Tamil Nadu deeds, "RERA Mirabilis Agreement.pdf" was a different allottee's
  agreement (Sunny Mullackal), and "Possession Certificate.pdf" was for Mrs Mamata S. Kanavi.
  Extract and read before classifying.
- **A "kept" set can still hold duplicates** (`…UDS-Sheet.xlsx` + `Copy of …UDS-Sheet.xlsx`,
  `…Kannada.pdf` + `…Kannada_Original.pdf`, two vintages of the same workbook). Report them
  separately and offer to dedupe — don't silently dedupe when the ask was relevance.
- **Report gaps.** If the README claims a doc set exists but it isn't in the folder, say so
  (the Behera README claimed the B1-203 sale deed was included; it was not — the registered
  deed No. 236/2023-24 is missing and only booking/UDS sheets evidence the transaction).

## Report shape NDR wants

Lead with the count change ("140 files down to 27"), state the test used, group what was
removed by *reason* (not a bare list), name the judgment calls and offer to reverse them,
confirm everything is in the bin and restorable, then flag gaps and duplicates as next steps.
Mention that a separate folder (the email dumps) was NOT touched, with sizes and an offer to
do it — do not silently expand scope. When the user says yes to cleaning the emails, load the
sibling reference `email-corpus-relevance-cleanup.md` (body-level classifier on email.txt,
sharded trash, per-account verify).
