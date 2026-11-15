---
name: google-workspace
description: "Gmail, Calendar, Drive, Docs, Sheets via gws CLI or Python.
Calendar event built from a WhatsApp/PDF invitation (and adding an attendee with sendUpdates=all):
references/calendar-event-from-whatsapp-invite.md.
'Give me links to those emails' → references/gmail-message-permalinks.md (API hex ids and Gmail
web ids are different ID spaces; `#all/<hex>` dies on a cold click; use `#search/rfc822msgid`). Finding a doc across Gmail+Drive and proving what a file is:
references/locating-documents-across-gmail-and-drive.md + scripts/inspect_drive_file.py.
Deleting Drive files from a Sheet row (a delete button next to each row), plus Sheets
checkbox/validation quirks: references/drive-file-deletion-and-sheet-delete-queues.md — only the
OWNER can trash a file, so a bound Apps Script cannot delete other people's files; use a checkbox
plus a domain-wide-delegation worker."
version: 1.2.0
author: Nous Research
license: MIT
platforms: [linux, macos, windows]
required_credential_files: []  # vault-only: no token or client-credential files exist on disk (see SOUL.md universal rule, Aug 2026)
metadata:
  hermes:
    tags: [Google, Gmail, Calendar, Drive, Sheets, Docs, Contacts, Email, OAuth]
    homepage: https://github.com/NousResearch/hermes-agent
    related_skills: [himalaya]
---

# Google Workspace

**🚨 HARD RULE — CREATE EVERYTHING IN TMP FIRST (NDR, 2026-09-17):** every Drive artifact a chat session creates (Doc, Sheet, Slides, PDF, HTML, MD, uploaded file, output folder) must be created INSIDE the root **`TMP`** folder — id `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`. Never at My Drive root (`0AFOc8cSaJXPGUk9PVA`), never directly in a project/entity folder. Files move out of TMP only when NDR explicitly names a destination. Full rule + root-pollution sweep recipe: `skill_view("draas-drive-organization")`.
  - **Per-user TMP for NON-ndr sessions (verified 2026-10-07, psingh):** the global TMP id above is ndr-owned — `files().copy(..., body={'parents':[<global TMP>]})` under a psingh session 404s (`File not found: <TMP id>`). Employee sessions must resolve their OWN TMP folder first (`drive.files().list(q="'root' in parents and name contains 'TMP'")`). psingh's is `155SBzMDhM5pebj3wLz8o_9310ZsFwqh6`.

Gmail, Calendar, Drive, Contacts, Sheets, and Docs — through Hermes-managed OAuth and a thin CLI wrapper. When `gws` is installed, the skill uses it as the execution backend for broader Google Workspace coverage; otherwise it falls back to the bundled Python client implementation.

> **LEGACY NOTE (Aug 2026):** This skill predates the gws-vault migration. Tokens for ALL Google accounts now live ONLY in the gws-vault daemon and are reached via `tools.gws_auth.build_service(...)` (see SOUL.md universal rule). Any mention of `google_token.json` / `client_secret.json` files in this document is legacy and stale — do NOT create, read, or search for such files. The setup flow below writes no credential files; credentials come from the environment (client ids/secrets) and the vault (tokens).

## References

- `references/genre-apps-script-in-sheet-automation.md` — **Apps Script inside Sheets/Docs/Drive** ("add a button to my sheet", "script to delete the row and the file", "automate this spreadsheet"): in-sheet buttons, custom menus, installable triggers, destructive row actions (delete file + row — ordering matters), laying down checkboxes/notes by API, and verifying before delivery. Hard constraints you must state up front rather than improvise around. Starter: `templates/sheet_row_delete_cleanup.gs`; detail: `references/sheet-ui-and-row-actions.md`. Absorbed the `google-apps-script` skill (2026-11-01).

- `references/prakash-weekly-sales-activity-report.md` — Prakash Singh's weekly Sales & Marketing activity workbook (Ranka Udaya / Ranka Amber): 11-tab map, sheet ID, psingh identity, data-source sweep order, RAW-write + range-width pitfalls, recurring project facts (Amber channel-partner list, RG collateral deliverables, RG target-lead workbook)
- `references/sheets-embedded-images.md` — **photos inside a Google Sheet**: `=IMAGE()` returns `#REF!` for every URL in this Workspace account (account-level, tested in a fresh sheet) and the Sheets API has no image-insert call — the working route is build an xlsx with openpyxl-anchored images and upload it with conversion to a Google Sheet (captions in their own column to the right of the image band), plus how to prove image links are anonymously readable.
- `references/gmail-search-syntax.md` — Gmail search operators (is:unread, newer_than:, etc.)
- `references/gmail-bounce-delivered-audit.md` — Mark a sheet's email column as DELIVERED / EMAIL ID IS INCORRECT by cross-referencing sent mail + Gmail Delivery Status Notifications (full-history sent sweep, raw-MIME failed-recipient parsing, status-column write + set-equality verify). Verified 2026-10-08 (Hosur SMEs HOSTIA).
- `references/gmail-corporate-compliance-search.md` — Searching for statutory meeting notices (AGM, EGM, Board Meetings) from compliance senders: multi-query strategy, cross-account search, handling attachment-only emails (empty body), and interpreting snippet+subject signals
- `references/sheets-tab-rename-and-copy.md` - Rename a tab / copy a workbook safely: resolve sheetId by title, check `capabilities.canEdit` first (403 otherwise), why `canCopy=true` can still 403 `insufficientFilePermissions`, and the new `gws_sheets_get_tabs` / `gws_sheets_rename_tab` tools.
- `references/drive-calendar-python-api.md` — Programmatic Drive/Calendar/Sheets access via `tools.gws_auth.build_service()`
- `references/csv-upload-to-new-sheet.md` — Local CSV → native Google Sheet in the session user's own Drive: build_service identity check, DictReader (embedded-newline CSV), RAW-only values write, read-back verify, ownership confirm; the `sheets.spreadsheets()` resource-path AttributeError pitfall and make-script-idempotent (REUSE_SHEET_ID) pattern. Verified 2026-09-24 (410-row Hosur project dataset).
- `references/xlsx-to-native-google-sheet.md` — Convert a locally-built **.xlsx to an editable native Google Sheet in ONE Drive call** (`files().create` with `mimeType='application/vnd.google-apps.spreadsheet'` + `MediaFileUpload`) — preserves every tab, colour, width and frozen pane, unlike a rebuild-via-values write. Covers the MIME target map for Docs/Slides too, the `MediaFileUpload`-not-a-dict trap, mandatory `service_name`, per-tab read-back verification, amending the converted sheet afterwards (addSheet + `=HYPERLINK` clickable row links + real `sheetId`), and the em-dash tab-name range escaping. Verified 2026-10-06 (10-tab sales-activity workbook).
- `references/drive-share-pitfalls.md` — Drive share `expirationTime` only works on Shared Drives; cross-user Drive access via vault bypass (upload files, create/patch events, folder operations, cross-sheet VLOOKUP pattern). §4: re-sharing after a recipient changes address (retire the stale permission by permissionId, share from the owning account). **§5b: My Drive is single-parent — `addParents` 403 'Increasing the number of parents is not allowed' even on a file you own; fix with a `application/vnd.google-apps.shortcut` entry in the target folder (live-linked, no snapshot), the `shortcutedFileTargetId`-is-not-a-valid-`q`-field trap, and the reminder that a shortcut grants nobody access — share the target file separately.**
- `references/drive-shortcut-folder-timeboxed-share.md` — **Sharing a folder whose items are all SHORTCUTS + time-boxing the grant for N days**: folder-level permissions do NOT reach shortcut targets (a recipient can be folder-Writer yet open zero files); enumerate shortcuts recursively, resolve `shortcutDetails.targetId`, grant viewer per target file, verify; My Drive has no native permission expiry → schedule a one-shot `no_agent` cron revoke job (script must live in `~/.hermes/scripts/` with a RELATIVE filename; revoke by re-listing perms per file and matching the email, not the stored permissionId) and **NEVER dry-run the revoke script against the live grant list — it deletes the real grants** (hit 2026-10-07: revoked all 57 then re-granted).
- `references/executed-agreement-source-verification.md` — "find the Word/Google Doc source of an EXECUTED agreement, verify it matches the signed/notarized PDF, then share both with viewer access": locate counterparts, trail emails to the canonical editable link, OCR-compare scan-PDF vs docx (pdftoppm + tesseract), detect a DELETED source doc (404 across vault accounts + trash, sibling-sheet proof), never pass off a stale draft as the agreement, inherited-parent permission trap, draft-not-send email pattern. Verified on Ranka Amber SSA 2026-09-22.
- `references/document-to-collaborator-provenance.md` — Recover an unidentified document + a collaborator named only by first name: `in:sent` subject-keyword search on the sending account (not `to:`), reading the covering email as the authoritative change history, walking paragraphs AND tables in the Doc, resolving the collaborator's full name from the document's own credit line, and the `/opt/hermes` sys.path + venv interpreter fix for GWS scripts in `terminal`
- `references/pptx-to-pdf-via-drive.md` — Convert .pptx to PDF by uploading as Google Slides + exporting, useful when LibreOffice is unavailable
- `references/slides-to-pdf-export.md` — Export a Google Slides deck to PDF via Drive `files().export`; vault identity-mismatch diagnostic (deck 404s when build_service authenticates as a different account than the one the deck was shared with) + OAuth re-auth fix
- `references/docx-edit-and-verify-on-drive.md` — Edit .docx files on Drive with python-docx (line spacing, text replacement), re-upload in-place preserving the file ID/link, and visually verify via Drive export → PDF → PNG → vision_analyze.
- `references/drive-deleted-document-recovery.md` — Multi-source search when a known document ID returns 404 or a document isn't where expected: trace via email body links, session history, Drive trash, local backups, and Gmail attachments; covers what to present to the user and pitfalls
- `references/telegram-attachment-source-recovery.md` — Files that arrived as Telegram attachments: session transcript records the `document_cache` path, cache auto-cleans (don't rely on it), full sweep (Drive+trash, all mail accounts, disk), and the only recovery paths (user re-forwards / sender re-shares)
- `references/gmail-cross-account-search-attachment-download.md` — Cross-account Gmail search + PDF attachment download: multiple-query strategy with dedup by message ID, recursive payload walking to identify attachments, `attachments().get()` download, and PDF text extraction via pdftotext/pymupdf. Covers the `tools.gws_auth → gws_fetch_token` standalone-script pattern and the large-attachment truncation pitfall with Drive fallback.
- `references/legal-matter-discovery-sweep.md` — Cross-account Gmail + Drive discovery sweep for a person/entity/case when the matter folder is unknown: voice-variant name resolution + case-number anchoring, multi-account query set, JSON-dump-to-file to avoid stdout truncation, Drive fullText + folder enumeration, get_media vs export (stored HTML raises 403 on export — use get_media), sibling-case-number check. Verified on the Behera/Mirabilis RERA sweep (2026-09-09).
- `references/eml-archive-to-pdf-evidence-pack.md` — Bulk .eml archive → readable PDF evidence pack on Drive: WeasyPrint per-email rendering (header block, embedded inline images), email.txt + Attachments separation, INDEX.csv, big-stack fix for WeasyPrint RecursionError on marketing HTML, process-shard uploads (threads segfault), BODY-LEVEL cleanup classification (filename filters are NOT enough — user correction 2026-09-10), and the Drive empty-folder sweep via the gws CLI wrapper.
- `references/gmail-attachment-to-drive.md` — Download a Gmail attachment (signed PDF, etc.) and upload it to a specific Drive folder, then share with users — full script template with key points and pitfalls
- `references/branded-slides-deck-playbook.md` — Build a complete brand-styled Google Slides pitch deck for NDR's companies: find existing pitch assets, scrape brand from the live website (browser console CSS sweep), source founder bios/photos, python-pptx build, Drive import as native Slides, PDF/OCR verify; plus gws.py arg-name and tab-name pitfalls. Verified 2026-09-14 (O3/Kelsa NVIDIA Inception deck).
- `references/pptx-to-google-slides.md` — Convert .pptx to native Google Slides (editable) via Drive import; reverse (Slides → PPTX download); known pitfalls (Slides API not enabled, bridge param quirks)
- `references/kdr-expense-sheet.md` — DRAAS KDR Monthly Payment & Expense Tracker: sheet structure, append-before-total pattern, common expense categories, and full Python implementation via `build_service`
- `references/gws-bridge-pitfalls.md` — Known gws_skill_bridge issues: SimpleNamespace AttributeErrors, missing kwargs (raw_query, max, output), workarounds for calendar_create, contacts_list, drive_search, drive_download, and the People API direct-usage pattern
- `references/drive-financial-model-search.md` — Drive search query patterns for finding financial/project IRR spreadsheets, keyword reference, naming conventions, combined query examples
- `references/drive-find-newly-created-calc-sheet.md` — Find a user-created calculation workbook ("I made a sheet of workings"): search the personal gmail Drive first, domain-keyword fullText queries, verify identity by reading grid cells before sharing, share from the owner account
- `references/drive-bank-account-search.md` — Drive + email search patterns for finding personal/entity bank account details (IFSC codes, account numbers, bank names). Covers what works, what doesn't, and where personal bank data actually lives.
- `references/gmail-code-password-lookup.md` — Finding passwords/codes/OTPs in Gmail when keyword search fails: subject-first queries, numeric code search, self-note (to:me from:me) search, Drive `fullText` cross-check, and the vault-socket / HERMES_SESSION_USER_ID overrides needed to search a specific user's mailbox.
- `references/drive-update-non-google-file.md` — Update an existing non-Google-native file (HTML, PDF, image) on Drive in-place using `files().update()` to preserve file ID, links, and sharing. Covers `get_media()` vs `export()` download methods and the complete download → edit → re-upload workflow.
- `references/docx-format-edit-in-place.md` — Edit a .docx on Drive in place (fix line spacing, fill placeholder blanks, change dates) while keeping the same link. Docs API refuses Office files ("must not be an Office file"); use lxml on `word/document.xml` (python-docx spacing writes don't persist) + `files().update()`. Covers the multi-run placeholder-replacement duplication pitfall and the no-LibreOffice render pipeline (temp Google Doc → PDF → PNG → vision).
- `references/docx-recital-edit-with-yellow-highlight.md` — Expand a title-chain recital in a .docx on Drive by extracting parties + survey numbers (with extents) from OCR'd scanned deed PDFs, editing with python-docx, and highlighting all additions YELLOW. Covers the tuple-unpacking pitfall (label vs text tuple reversal), surgical OCR of multi-hundred-page scans, and re-upload in place. DRA Group pattern (Bharat / NDR, Ranka Oasis absolute sale deed).
- `references/docx-recital-remove-renumber.md` — Remove one or more recitals from a title-chain .docx, renumber the survivors, and fix stale cross-references. Uses zipfile+lxml on `word/document.xml` (python-docx in-place rewrites don't persist). DRA Group pattern.
- `references/drive-move-rename-reorg.md` — Batch move+rename documents between Drive folders (e.g. TMP → Personal): the `addParents`/`removeParents` comma-joined-string requirement (arrays cause `404 File not found`), move+rename in one `files().update()`, duplicate-folder cleanup, TMP→Personal reorg workflow, and post-move verification. **§P0b: `403 "Increasing the number of parents is not allowed"` — My Drive files are SINGLE-PARENT; do NOT relocate the user's file to satisfy a folder-placement request, create a shortcut inside the destination instead (`application/vnd.google-apps.shortcut` + `shortcutDetails.targetId`); `shortcutedFileTargetId` is an invalid `q` field (400), read the target from the list RESPONSE. Plus cross-identity sharing when the artifact's owner ≠ the working session's vault identity.**
- `references/drive-legal-document-search-and-analysis.md` — Drive search + download + text extraction workflow for legal/court documents: multi-query strategy, folder enumeration, PDF download via `build_service` + `MediaIoBaseDownload`, text extraction with pdftotext/tesseract, keyword search within extracted content
- `references/md-to-docx-drive.md` — Convert a .md file from Drive to a .docx Word document and upload it back with proper naming. Covers download → python-docx parse → upload pipeline, markdown→docx element mapping, and pitfalls (BOM, unicode bullets, horizontal rules). — Multi-sheet workbook inspection and category-based restructuring: detect different column schemas across sheets, map property/entity types to categories (Apartment, Villa, Rowhouse, Plotted), create category-sorted sheets. Handles 14-col detail vs 7-col summary format mixing. Preceded by clarifying questions on scope, format, and existing-sheet disposal.
- `references/sheets-workbook-link-audit-and-restructure.md` — Workbook-wide Drive-link audit + project-wise rebuild: FORMULA-mode ID extraction, per-ID `files().get` verification, label-vs-filename MISMATCH detection, dangling-shortcut and filename-only-reference traps, canonical URL shapes, and the clear→chunked-write→read-back→batchUpdate-format flow for restructuring a checklist into per-project tables.
- `references/sheets-clean-lead-export.md` — Clean messy contact/lead exports (Kelsa WhatsApp-list format `Name-["phone"]-date` / `["+91..."]`) to canonical Name + 91XXXXXXXXXX columns: dump-all-patterns-first, name/phone regexes, unicode-styled name normalization (NFKD), clear → USER_ENTERED write → read-back verification; heredoc-vs-write_file terminal pitfall.
- `references/sheets-multi-tab-block-update.md` — Update a payment-plan / labelled block that lives in MULTIPLE tabs of one workbook ("make changes wherever applicable"): enumerate tabs + grep for block keywords first, rewrite the FULL block (not just overlapping rows), then re-apply PERCENT number format via repeatCell — values().update does NOT carry format to previously-blank rows, and sheetId 0 is not always the tab you think (Ranka Amber cost-sheet: PaymentPlan=687697266, UnitPaymentPlan=1851063261, 0=CostSheet). Verify with FORMATTED read-back.
- `references/sheets-row-reorder-and-date-serial.md` — Reordering rows in a sheet: prefer CLEAR + REBUILD with `=HYPERLINK()` formulas over fragile `moveDimension` permutation math; Excel serial-number dates under en_US locale (11-01-2023 typed as DD-MM silently stored as Nov 1 — cross-check document filename/reg FY, fix cell before sorting); permission ladder for user-shared sheets (read vs batchUpdate 403 = Viewer, need Editor).
- `references/sheets-multi-block-formula-workbook.md` — Building a multi-block, formula-driven sheet (assumption blocks + rate tables + validation tab, cross-tab formulas): the **silent row-drift** failure mode where hand-picked row numbers overwrite labels with duplicate rows and superseded rows linger to poison validation. Layout-map-first, clear-past-block-end, verify in FORMULA mode, numeric invariant assertions, circular-reference and blank-column-returns-0 traps, percent-format-vs-gate comparison, `numberFormatType`-is-not-writable + off-by-one batchUpdate range 400s. Verified 2026-09-25 (8-tab DRAAS incentive workbook).
- `references/docs-batch-replace-text.md` — Bulk find-and-replace in Google Docs via `documents().batchUpdate()` with `replaceAllText`. Fill template placeholders, update numbers/percentages, remove `[●]` markers in legal documents. Unicode handling, verification pattern, execution environment (terminal + Hermes venv). **Also: filling two-party SIGNATURE BLOCKS whose cells hold identical placeholder text (index-targeted delete+insert, `pageBreakBefore` to keep the block on one page, PDF-text-layer verification) + the pre-signature consistency scan NDR expects (entity-vs-signatory header, acronyms checked against source approvals, stale draft caveats).**
- `references/docs-insert-paragraph-with-format.md` — INSERT a new paragraph block (agenda item / resolution / section) into a native Google Doc with typography matched to the existing document: index-map the body, `insertText` at a precise anchor, compute post-insert ranges (len + 1 per `\n`), `updateParagraphStyle`/`updateTextStyle` with explicit `fields`, verify via read-back, render-QA via Drive PDF export + pdftoppm (`-png` required). Real case: DRA Partners Resolution CTC (2026-09).
- `references/rnd-sheet-kml-output.md` — R&D competitor pipeline output: append rows to the Competitors tab (`values().append` + read-back verification), regenerate KML in place on Drive (`get_media` → insert `<Placemark>` → `files().update` same file ID → re-upload verify), plus Places-crawler geocoding notes (Apify). Intended home: `real-estate-portal-research` skill.
- `references/daily-calendar-summary-cron.md` — Daily "summarize my calendar" cron (9 AM IST every day): schedule math on a UTC server (`30 3 * * *`, not `0 9 * * *`), the self-contained cron prompt with the owner-identity guard (`calendars().get(calendarId='primary')` must print ndr@draas.com), Asia/Kolkata day-boundary computation, and the delivered bullet shape. Verified 2026-09-29 (job 38780698a1d4).
- `references/not-spam-cron-run-notes.md` — Daily not-spam Gmail check (cron): canonical script path (`not_spam_check.py`, build_service-based), stale duplicate copies to avoid, duplicate-skill-copy ambiguity pitfall (loader says "not found" while files exist), benign `canonical_uid` fallback warning, and the identity-guard exit (cron env can resolve to psingh@draas.com → re-run with `HERMES_SESSION_USER_ID=ndr`).
- `references/people-api-contact-search.md` — Find a contact's email by name via People API `searchContacts` (works with contacts scope only; `people/me` with `personFields='emailAddresses'` 403s because `profile` scope is not granted). Handles duplicate contact entries and the DRAAS-only contacts rule.
- `references/people-api-update-contact.md` — Updating an existing Google Contact via `updateContact`: the etag MUST be echoed in the body (fetch with `personFields='names'`, never request `etag` as a mask path), adding a Google Maps link via `userDefined` custom field, and the verified NDR DRAAS contacts-sheet 93-column map (Address 1 = AN–AU, Custom Field 1 = CJ/CK) with verify-before-write lesson. Also: **email corrections are usually a RE-SLOT** (read the list first — the "new" address is often already there in the wrong slot), `searchContacts` prefix-match misses on first names → `connections().list()` substring fallback, the sheet's real tab name (`NDR DRAAS Google contacts.csv`, `.csv` included) + the same-named decoy spreadsheet, and `values().clear()` trailing-cell readback illusion.
- `references/people-api-contact-email-update-three-store.md` — quick recipe card for the "update his email in both stores" request: the three write targets (DRAAS People API, contacts sheet, other vault account copies), per-account liveness probe, and the report-the-gap rule.
- `references/people-api-whatsapp-synced-contacts.md` — Contacts created via WhatsApp phone sync appear in People API with phone but NO email (names like "Kranthi Chaitanya Pulluru" / "Soni Thomas MAIS"). Full workflow: `searchContacts` → `connections().list()` fallback for names search misses, Gmail domain search (`from:flameback.com`) to find the email, the DUP-CREATION TRAP (always check existing contacts before `createContact`; delete the duplicate and `updateContact` with etag instead), and the contacts-sheet append pattern.
- `references/oauth-reauth-terminal-pattern.md` — Re-auth a revoked/expired GWS token from a terminal subprocess. Includes the real (deliberately hint-free) `send_oauth_url(service_name, label, task_id)` signature — `login_hint=` raises TypeError; the account email goes in the `label` only.
- `references/email-forward-as-draft.md` — Forward an existing email as a Gmail DRAFT (never auto-send): raw-MIME `EmailMessage` + `drafts().create`, threading via In-Reply-To/References, verify-by-refetch, and attachment-aware message inventory (for "does this email have an Excel attachment?"): `has_token=True` only means presence (not freshness), `send_oauth_url` needs `TELEGRAM_BOT_TOKEN` + session platform/chat env (extract the token from the gateway pid environ), and the authorizing identity comes from session env only.
- `references/calendar-event-link.md` — Giving NDR a Google Calendar event link: pass the API's `htmlLink` VERBATIM — the eid is pure base64 (no space, never re-encode; a manually inserted `%20` broke the link 2026-09-30). Canonical form `https://calendar.google.com/calendar/event?eid=<eid>&ctz=Asia/Kolkata`; `curl -sL` → 200 validates logged-out.

- `references/docs-read-vs-pdf-pan-aadhaar-search.md` — Find PAN, Aadhaar, DIN of a signatory/director embedded within legal agreement Google Docs (not as scanned cards): Drive fullText name search, Docs API structured-body extraction with type variance handling (dict/list/empty), regex extraction with cross-referencing against nearby names/director labels. Verified 2026-10-03 (Perumal Kasi / Shree Mahakasi Enterprises MOU). Also covers when to fall back to .docx or ask NDR.
- `references/docs-revision-marking-in-blue.md` — Produce a Google Doc revision with **changes marked in blue** (NDR's recurring "all updates in blue" instruction): per-run `updateTextStyle` masks, the nested `foregroundColor.color.rgbColor` shape that makes naive verifiers report a FALSE "no styling applied", ground-truth verification via Drive HTML export + hex-colour count, bulk-insert style inheritance (whole body rendered 15pt bold from the title), content-based paragraph matching when index maps drift, deleting list bullets cleanly, and the pre-report checklist.
- `references/docs-letterhead-finalize.md` — Convert an approved/reviewed Google Doc into its FINAL black-letterhead version (NDR: "convert whole thing to black, put it on our letterhead, delete the original"): find the real DRA letterhead template (header/footer image variant), copy it into TMP, rebuild the body with every run forced black, fix the stale "text in blue" revision note, verify via HTML export + PNG, replicate permissions, trash the original. Covers the `insertTable`-vs-`createTable` schema gotcha, the descending-order single-batch table cell fill that prevents corruption, and Docs write-quota handling.
- `references/gmail-draft-account-and-provenance.md` — Answering *"which account did you put the draft in?"* / *"I can't find it in my DRAAS account"*: sweep all vault accounts across drafts + sent + trash, the draft→SENT `threadId` continuity that means "I can't find the draft" may simply mean "it was already sent", choosing between ndr@draas.com and nishantranka@gmail.com, and the rule to NAME the account (and flag letterhead-vs-sender mismatches) in the completion report. **Plus: revising an already-reviewed draft — delete + recreate on the SAME `threadId` (Gmail does not re-thread from `References` when inserting raw MIME), preserving `In-Reply-To`/`References`, the assert-the-anchor-exists rule for string body edits, and the four post-revision verifications (one draft, threadId match, To/Cc unchanged, change visibly rendered).**
- `references/gmail-bounce-deliverability-marking.md` — Mark a contact sheet's email status from Gmail delivery notifications: parse "Delivery Status Notification (Failure)" messages (raw-MIME + X-Failed-Recipients/Final-Recipient/body regex — a plain body-regex pass returns []), sweep ALL `in:sent` (not a window) to classify DELIVERED, expand the grid (`columnCount`) before writing a new status column, and the full-column rebuild off-by-one trap (col[i] → row i+2) with set-equality verification. Verified 2026-10-08 (Hosur SMEs HOSTIA, 29 INCORRECT + 114 DELIVERED).
- `references/gmail-bounce-delivery-status-sheet.md` — "response says ADDRESS NOT FOUND / mark which emails are incorrect / add DELIVERED status": parse Delivery Status Notification (Failure) bounces (raw + stdlib email; regexes for X-Failed-Recipients/Final-Recipient/embedded `To:`), match to sheet rows, three-state status column (DELIVERED / INCORRECT / blank), grid-expand before writing a new column, full-column-rebuild off-by-one pitfall, delivered-first reorder + red highlight. Verified 2026-10-08 (Hosur SMEs HOSTIA).
- `references/gmail-bounce-sheet-marking.md` — Mark bounced email IDs in a leads/SME sheet from Gmail "Delivery Status Notification (Failure)" bounces (user says "response is ADDRESS NOT FOUND — update the sheet"). Full recipe: `format='raw'` bounce parsing (a `format='full'` body walker returns EMPTY failed lists), failed-address regex set (`X-Failed-Recipients` / `Final-Recipient` / "failed permanently" / embedded `^To:` lines), duplicate-email-across-rows handling, bounces belonging to OTHER tabs (report, don't silently mark), and the expand-grid-first step when the status column beyond the grid 400s (`exceeds grid limits ... max columns` → `updateSheetProperties` `columnCount`). Verified 2026-10-08 (Hosur SMEs (HOSTIA) tab — 34 bounces → 29 rows marked "EMAIL ID IS INCORRECT").

## Scripts

- `scripts/setup.py` — OAuth2 setup (run once to authorize)
- `scripts/google_api.py` — compatibility wrapper CLI. It prefers `gws` for operations when available, while preserving Hermes' existing JSON output contract.

## First-Time Setup

The setup is fully non-interactive — you drive it step by step so it works
on CLI, Telegram, Discord, or any platform.

Define a shorthand first (use Hermes venv — system Python is externally managed):

```bash
GSETUP="/opt/hermes/.venv/bin/python3 ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/setup.py"
```

### Step 0: Check if already set up

```bash
$GSETUP --check
```

If it prints `AUTHENTICATED`, skip to Usage — setup is already done.

### Step 1: Triage — ask the user what they need

Before starting OAuth setup, ask the user TWO questions:

**Question 1: "What Google services do you need? Just email, or also
Calendar/Drive/Sheets/Docs?"**

- **Email only** → They don't need this skill at all. Use the `himalaya` skill
  instead — it works with a Gmail App Password (Settings → Security → App
  Passwords) and takes 2 minutes to set up. No Google Cloud project needed.
  Load the himalaya skill and follow its setup instructions.

- **Email + Calendar** → Continue with this skill, but use
  `--services email,calendar` during auth so the consent screen only asks for
  the scopes they actually need.

- **Calendar/Drive/Sheets/Docs only** → Continue with this skill and use a
  narrower `--services` set like `calendar,drive,sheets,docs`.

- **Full Workspace access** → Continue with this skill and use the default
  `all` service set.

**Question 2: "Does your Google account use Advanced Protection (hardware
security keys required to sign in)? If you're not sure, you probably don't
— it's something you would have explicitly enrolled in."**

- **No / Not sure** → Normal setup. Continue below.
- **Yes** → Their Workspace admin must add the OAuth client ID to the org's
  allowed apps list before Step 4 will work. Let them know upfront.

### Step 2: Create OAuth credentials (one-time, ~5 minutes)

Tell the user:

> You need a Google Cloud OAuth client. This is a one-time setup:
>
> 1. Create or select a project:
>    https://console.cloud.google.com/projectselector2/home/dashboard
> 2. Enable the required APIs from the API Library:
>    https://console.cloud.google.com/apis/library
>    Enable: Gmail API, Google Calendar API, Google Drive API,
>    Google Sheets API, Google Docs API, People API
> 3. Create the OAuth client here:
>    https://console.cloud.google.com/apis/credentials
>    Credentials → Create Credentials → OAuth 2.0 Client ID
> 4. Application type: "Desktop app" → Create
> 5. If the app is still in Testing, add the user's Google account as a test user here:
>    https://console.cloud.google.com/auth/audience
>    Audience → Test users → Add users
> 6. Download the JSON file and tell me the file path
>
> Important Hermes CLI note: if the file path starts with `/`, do NOT send only the bare path as its own message in the CLI, because it can be mistaken for a slash command. Send it in a sentence instead, like:
> `The JSON file path is: /home/user/Downloads/client_secret_....json`

Once they provide the path:

```bash
$GSETUP --client-secret /path/to/client_secret.json
```

If they paste the raw client ID / client secret values instead of a file path,
write a valid Desktop OAuth JSON file for them yourself, save it somewhere
explicit (for example `~/Downloads/hermes-google-client-secret.json`), then run
`--client-secret` against that file.

### Step 3: Get authorization URL

Use the service set chosen in Step 1. Examples:

```bash
$GSETUP --auth-url --services email,calendar --format json
$GSETUP --auth-url --services calendar,drive,sheets,docs --format json
$GSETUP --auth-url --services all --format json
```

This returns JSON with an `auth_url` field and also saves the exact URL to
`~/.hermes/google_oauth_last_url.txt`.

Agent rules for this step:
- Extract the `auth_url` field and send that exact URL to the user as a single line.
- Tell the user that the browser will likely fail on `http://localhost:1` after approval, and that this is expected.
- Tell them to copy the ENTIRE redirected URL from the browser address bar.
- If the user gets `Error 403: access_denied`, send them directly to `https://console.cloud.google.com/auth/audience` to add themselves as a test user.

### Step 4: Exchange the code

The user will paste back either a URL like `http://localhost:1/?code=4/0A...&scope=...`
or just the code string. Either works. The `--auth-url` step stores a temporary
pending OAuth session locally so `--auth-code` can complete the PKCE exchange
later, even on headless systems:

```bash
$GSETUP --auth-code "THE_URL_OR_CODE_THE_USER_PASTED" --format json
```

If `--auth-code` fails because the code expired, was already used, or came from
an older browser tab, it now returns a fresh `fresh_auth_url`. In that case,
immediately send the new URL to the user and have them retry with the newest
browser redirect only.

### Step 5: Verify

```bash
$GSETUP --check
```

Should print `AUTHENTICATED`. Setup is complete — token refreshes automatically from now on.

### Notes

- Token is stored in the gws-vault daemon and auto-refreshes — no token files exist on disk.
- Pending OAuth session state/verifier are stored temporarily at `~/.hermes/google_oauth_pending.json` until exchange completes.
- If `gws` is installed, `google_api.py` uses the vault via `tools.gws_auth.build_service(...)`. Users do not need to run a separate `gws auth login` flow.
- To revoke: `$GSETUP --revoke`

## Usage

All commands go through the API script. Set `GAPI` as a shorthand (use Hermes venv — system Python is externally managed):

```bash
GAPI="/opt/hermes/.venv/bin/python3 ${HERMES_HOME:-$HOME/.hermes}/skills/productivity/google-workspace/scripts/google_api.py"
```

### Gmail

```bash
# Search (returns JSON array with id, from, subject, date, snippet)
$GAPI gmail search "is:unread" --max 10
$GAPI gmail search "from:boss@company.com newer_than:1d"
$GAPI gmail search "has:attachment filename:pdf newer_than:7d"

# Read full message (returns JSON with body text)
$GAPI gmail get MESSAGE_ID

# Send
$GAPI gmail send --to user@example.com --subject "Hello" --body "Message text"
$GAPI gmail send --to user@example.com --subject "Report" --body "<h1>Q4</h1><p>Details...</p>" --html
$GAPI gmail send --to user@example.com --subject "Hello" --from '\"Research Agent\" <user@example.com>' --body "Message text"

# Reply (automatically threads and sets In-Reply-To)
$GAPI gmail reply MESSAGE_ID --body "Thanks, that works for me."
$GAPI gmail reply MESSAGE_ID --from '\"Support Bot\" <user@example.com>' --body "Thanks"

# Labels
$GAPI gmail labels
$GAPI gmail modify MESSAGE_ID --add-labels LABEL_ID
$GAPI gmail modify MESSAGE_ID --remove-labels UNREAD
```

### Calendar

```bash
# List events (defaults to next 7 days)
$GAPI calendar list
$GAPI calendar list --start 2026-03-01T00:00:00Z --end 2026-03-07T23:59:59Z

# Create event (ISO 8601 with timezone required)
$GAPI calendar create --summary "Team Standup" --start 2026-03-01T10:00:00-06:00 --end 2026-03-01T10:30:00-06:00
$GAPI calendar create --summary "Lunch" --start 2026-03-01T12:00:00Z --end 2026-03-01T13:00:00Z --location "Cafe"
$GAPI calendar create --summary "Review" --start 2026-03-01T14:00:00Z --end 2026-03-01T15:00:00Z --attendees "alice@co.com,bob@co.com"

**Attendee email resolution (do this BEFORE creating):** people in NDR's
orbit often have 2–3 addresses (personal Gmail, iCloud/me.com, work). Don't
guess which one to invite — resolve it first via `session_search` for that
person's name (past drafts/threads show which address the user intends),
then confirm against the user's phrasing (e.g. "Aamir uses Gmail address"
→ khan.hussain.aamir@gmail.com, not aamirkhan@me.com). Inviting the wrong
address means the invite lands in a mailbox the person never checks.

Worked voice-resolution example (2026-09-12, Hesthetic investment call): voice
"Bhavish Bhavna" had no contact-sheet/People-API hit, but phonetics + Gmail
co-recipient context resolved it to **Bhavesh Bafna <bvbafna@gmail.com>** — NDR
forwards him investment opportunity notes (MSEDCL BESS Tender) and travel bookings.
Rule when a dictated attendee isn't in contacts: (1) search phonetic lookalikes in
People API (e.g. "Bhavish"→Bhavesh, "Bhavna"→Bafna), (2) verify the Gmail via
`from:|to:<email>` co-recipient threads with NDR, (3) STILL present the resolved
name+email for confirmation before insert. Pitfall: the contacts sheet row 621
"Bhavesh Mehta" (bhavesh@drahomes.in) is a DIFFERENT person — do not grab the
sheet's first same-name hit; the user's "has a Gmail address" qualifier points to
the personal Gmail, not a work address. Deal company voice "Aesthetics" → Hesthetic
Life Pvt Ltd (cold-pressed oils, Surat) — resolve the voice-mangled company with the
no-API research ladder (DDG-via-Jina) and present the resolved name so NDR can
confirm it's the deal he meant.

**Surname is voice-mangled but the person has BEEN ON A CALL BEFORE → search
the user's own CALENDAR, not contacts (verified 2026-09-18, two attendees in one
session).** When a dictated attendee name returns nothing from `contact_resolver`,
People API, the contacts sheet, AND Gmail — and the user says they've met/met with
this person — the calendar is the missing source. NDR's calendar carries
`attendees[].displayName` + `attendees[].email` for every past invite, and the
description often names the venue/agenda.

Recipe: `cal.events().list(calendarId='primary', q='<FirstName>', singleEvents=True,
orderBy='startTime', timeMin='<1yr back>Z')`, then print each hit's `summary`,
`start`, `attendees`, `location`, and `description` — the email is in
`attendees[0]['email']` with `displayName` giving the correct spelling.

Worked case 1 — voice **"Harish Bhaksani"** (a surname that exists NOWHERE: no
People API hit across all 3 vault accounts, no contacts-sheet row, no Gmail
thread) resolved via a calendar hit to **Haresh Buxani <haresh@buxani.com>**
(+852 9200 0520), from a prior event titled *"Investment Proposal Discussion
with Harish"* at the SAME venue (DRA Realty Office). Both words were wrong
(Harish→Haresh, Bhaksani→Buxani).

Worked case 2 — voice **"Aamir Khan … he's got Aamir Hussain Khan, Aamir Khan
Hussain, some gmail address"** → the contact-sheet row had THREE addresses
(`aamirkhan@me.com`, `aamirkhan@icloud.com`, `khan.hussain.aamir@gmail.com`).
The user's own garbled recollection of the name *was* the discriminator: his
"khan.hussain.aamir" maps directly onto the Gmail address, so the Gmail one is
the invite target. **When a contact has multiple addresses and the user
fumbles the person's full name out loud, treat that fumbled name as the
address-selection hint** — then state which address you used and list the
alternates you skipped so the user can correct.

Notes: (a) also add the resolved person to the contacts sheet only if the user
asks — resolving an existing contact is not licence to create one; (b) the
calendar only holds people the user has actually invited, so this path covers
"met before / met recently" cases and NOT cold first-time meetings; (c) still
present name + email in the reply so a wrong resolution is cheap to catch
before the invite goes out.

**Deal-team attendee resolution — the SAME-TRANSACTION prior call is the attendee list (verified 2026-09-29, Ranka Oasis 5–7 PM close-pending-issues meeting).** `contact_resolver` returned ambiguous/nothing for ALL THREE dictated attendees ("Vineet, Nishant Prakash, Vishwas"): the authoritative list was the most recent same-deal call — 21 Sep *"Ranka Oasis - Sevaganapalli: Structuring & Funding Call | Vineet (Jiraaf), Vishwas (Vantage Point), Prakash, Nishant"* — carrying Vineet Agrawal <vineet@jiraaf.com>, Vishwas Rao <vishwas@vantagepointadvisors.in>, Prakash M <prakash.m@jiraaf.com>, Nishant Prakash <nishantprakash1@gmail.com>. Voice/typo aliases on this deal: **"Giraffe Capital" = Jiraaf** (also seen as "Jiraffe Capital", "Vinit") — the JV/funding partner, not a separate company. ⚠️ Nishant Prakash has TWO addresses: `nishantprakash1@gmail.com` (transaction calls, 21-Sep) vs `nishantprakash@theyelloweye.com` (older Yellow Eye meetings) — use the one on the most recent relevant thread and SAY which you used. When the requested block overlaps existing events (29-Sep had Bhavik<>Jayram Iris 17:30 and V-Gro Finserv term-sheet 18:30), create the event as asked and FLAG the overlaps; don't block. READ BACK the created event (id, attendees with responseStatus `needsAction`, htmlLink) before reporting.

**A dictated meeting name is often NOT the calendar summary — search by attendee/description terms when `q=<colloquial name>` returns 0 (verified 2026-09-30).** NDR said "change the **Vigro** meeting" — `q='Vigro'` (and `vigro`/`VIGRO`) on google-draas returned **0 events**. The event only surfaced via `q='Vamshi'` (the attendee): summary is the FORMAL name **"V-Gro Finserv — Term Sheet Meeting (projects data by Prakash)"** with attendee Vamshi Raj <vamshiraj@vgrofinserv.com> and coordinator number `+91 86181 20715` in the description. Reusable ladder when a meeting name won't match: (1) try case/spelling variants of the name, (2) search a KNOWN ATTENDEE's first name (`q='Vamshi'`), (3) widen to the deal context (company/people mentioned in recent sessions). Once found, MOVE the event with `events().patch(calendarId='primary', eventId=<eid>, body={'start':…, 'end':…, 'location':…}, sendUpdates='all')` — `sequence` increments and attendees get the update email automatically; report new start/end + htmlLink and note the coordinator contact from the description so NDR knows who still needs to be told the time changed.

**Internal DRA colleague invites — the contacts sheet can LACK the work email; use the Kelsa/vault identity instead (verified 2026-09-30, Gowri Singh).** Adding Gowri Singh to a DRA-internal meeting: the contacts sheet row for her carries `gowrisingh72@yahoo.com` + `gowrisingh1341@gmail.com` and **no gsingh@draas.com** — inviting via the sheet address would send a DRA meeting invite to a personal mailbox the person may not monitor for work. Her actual workspace email is **`gsingh@draas.com`** (confirmed via the Kelsa user record, id 9398). Rule mirror of the existing attendee rule: for DRA-internal colleagues, prefer the **@draas.com / @drahomes.in work address** over personal yahoo/gmail even when the sheet only lists personal; cross-check the Kelsa user list (`list_users(pipeline_id=…)`) or past calendar invites before picking. State which address you used. Same session: Roshini = **rnr@draas.com** (already in memory).

**`entity_resolver` is currently broken** — calling it returns
`[TOOL_ERROR] TypeError: _handle() got an unexpected keyword argument 'task_id'`
(observed 2026-09-18). Do not burn a turn on it: go straight to
`contact_resolver` → People API `searchContacts` across all three vault
accounts → contacts sheet name scan → Gmail → **calendar history** (above).
Report the defect to the user if it blocks resolution.

**Calendar writes via build_service (terminal, not execute_code):** for
programmatic creation with attendees, use
`build_service('calendar', 'v3', service_name='google-draas')` +
`events().insert(calendarId='primary', body={...}, sendUpdates='all')` —
`sendUpdates='all'` sends the invite email to attendees. Verify identity
first with `calendars().get(calendarId='primary')` (prints owner summary)
and **CHECK the printed owner email — if it isn't the intended account,
abort before inserting** (real case 2026-08-13: `build_service(service_name='google-draas')`
resolved the session to psingh@draas.com and the event would have been created
on Prakash Singh's calendar; fix: delete the misplaced event via the same
resolved service, re-run with `HERMES_SESSION_USER_ID=ndr`, re-verify owner
= ndr@draas.com, then insert).
Always pass IST offset `+05:30` for Bangalore events.

**Adding an event to a FAMILY MEMBER's calendar whose Gmail is NOT a linked vault account (verified 2026-09-27, Ruhaan chemistry-review reminder):** `gws_resolve_account('<child>'s@gmail.com')` returns *"Account ... is not associated with your session user"* — the vault only holds the session user's own identities, so you cannot write directly to another person's calendar. Two options: (1) OAuth that account via `send_oauth_url` (the session user taps the button and logs in AS the child once; then you can write to their calendar directly in future), or (2) — the default NDR picks — create the event on the session user's calendar and add the family member as an **attendee/guest**: `ev['attendees']=[{'email': <child>, 'displayName': ...}]` then `events().update(calendarId='primary', eventId=eid, body=ev, sendUpdates='all')` (or include attendees at `events().insert`). Verify read-back: attendee `responseStatus` starts `needsAction`. Report honestly that the invite is in their inbox and the event becomes a firm calendar entry once THEY tap Accept — until then it is a pending invitation. Note: NDR's phrasing *"add them as a guest, that's all you need to do"* explicitly authorizes `sendUpdates='all'` — the calendar guest email is not the draft-only Gmail rule (that rule governs composed messages, not invites the user asked to send).

**⚠️ An attendee with NO email address CANNOT be invited — verify the address EXISTS before promising an invite (verified 2026-09-21).** Google Calendar keys attendees entirely on email; there is no name-only attendee. When the user asks *"has X been added as an attendee?"*, the answer can legitimately be **"no — and X cannot be, because no email exists for X"**. Do the existence check across ALL sources before reporting, and report which you checked:

1. contacts sheet (`NDR DRAAS Google contacts` — 93-col layout, phones at AN–AU, emails at S–Z; a row may carry phone ONLY)
2. People API `searchContacts` on **each** vault account (`google-draas`, `google-ahfl`, `google-gmail`) — `build_service("people","v1",service_name=acct)`, `readMask="names,emailAddresses,phoneNumbers,organizations"`

A contact that returns `emailAddresses: []` from every source has no email, full stop. Worked case 2026-09-21: *"Shreyans Babel"* (Dunkel d'Estate lead source) returned phone `+91 99409 22334` and **zero emails** from the contacts sheet row AND People API on all three accounts — so the 24-Sep meeting event could not carry him as an attendee.

**NEVER synthesise a placeholder email to force a guest onto an event.** Inserting `attendee: {"displayName": "...", "email": "someone@madeup.placeholder"}` puts a bogus address on a real invite — it bounces, may leak the internal meeting to a third party, and looks like a real attendee to everyone else. The correct handling when no email exists:
- leave `attendees` genuinely empty,
- put the person's **phone number** in the event `description` so the organiser can reach them,
- state plainly in your reply that they are NOT an attendee and WHY, then ask the user for the email.

**⚠️ Removing a bad attendee: `attendees: []` is the fix, and an empty list reads back as `None`.** Setting `ev["attendees"] = []` and calling `events().update(...)` does clear it; the subsequent GET shows `attendees` absent/`None`. Do NOT then re-add a placeholder trying to "keep the name visible" — see above.

**Verifying an EXISTING event (the "have we created the event / is X on it / is the location set?" request):** don't trust your memory of creating it — read it back and report each field. `events().list(calendarId='primary', timeMin=<window>, timeMax=<window>, singleEvents=True, orderBy='startTime', maxResults=100)` then print `summary | start | id`, `location`, `attendees`, `description`. A brand-new event with no `attendees` key at all and `location: None` is the signature of "created with summary+description only" — which is exactly what the user is asking you to catch. Worked case 2026-09-21: *"Meeting with Shreyans Babel - Dunkel d'Estate"* existed (created 2 days earlier, 24-Sep 16:00–17:00) but had **no attendee and no location**; the location was then set to the DRA office and the missing-email fact reported.

**⚠️ A dictated venue name can be a mis-hearing — confirm rather than substitute silently.** NDR called the venue the *"VIP Realty office"* while the address on file is the DRA office at **Prizm Greystone, #204-206 Cunningham Road**. Setting a location you inferred without flagging it silently rewrites the user's intent. Set the best-known address AND explicitly tell the user the name they used is unconfirmed, offering to correct it. Same discipline as the attendee-email rule: state what you wrote and what you were unsure about.
`conferenceData: {"createRequest": {"requestId": "<unique-uuid-hex>", "conferenceSolutionKey": {"type": "hangoutsMeet"}}}` to the insert body and call
`events().insert(calendarId='primary', body=evt, conferenceDataVersion=1, sendUpdates='all')` — response carries `hangoutLink` and attendee `responseStatus`. Match the user's standing series title from the calendar first (e.g. recurring Flameback calls are titled "<Person> <> Nishant") instead of inventing a new name; check that day's events for conflicts before inserting (a reminder at 14:30 and a site visit at 15:00 are worth flagging, not blocking).

**Adding Google Meet to an EXISTING event (verified 2026-09-09, Biometric event):** `events().patch(body={'conferenceData': {'createRequest': {...}}}, conferenceDataVersion=1)` **silently drops the conference when you are not the event organizer** — the call returns 200, the response shows `conferenceData: null`, a subsequent GET has no `hangoutLink`, and NO error is raised. This happens when the event sits on YOUR calendar but was created by another mailbox (real case: organizer/creator `admin3.blr@draas.com` — an assistant/shared mailbox — created the event on ndr's calendar). Diagnostic ladder: (1) read `event.organizer` / `event.creator` — if they aren't your authenticated identity, that's the cause; (2) prove your identity CAN create Meets by inserting a scratch event with `conferenceDataVersion=1` and reading its `hangoutLink` (then delete it) — scratch works ⇒ organizer-permission issue, not a scope/token issue. Fix: **recreate the event as the organizer** — `events().insert` on the same calendar with identical summary/description/start/end/attendees/reminders + the `conferenceData` createRequest, then `events().delete` the original. Tell the user: RSVP state resets and attendees see a cancellation (old) + fresh invite (new).

# Delete event
$GAPI calendar delete EVENT_ID
```

### Drive

```bash
# Search existing files
$GAPI drive search "quarterly report" --max 10
$GAPI drive search "mimeType='application/pdf'" --raw-query --max 5

# Get metadata for a single file
$GAPI drive get FILE_ID

# Upload a local file (auto-detects MIME type)
$GAPI drive upload /path/to/report.pdf
$GAPI drive upload /path/to/image.png --name "Logo.png" --parent FOLDER_ID

# Download (binary files download as-is; Google-native files export to a
# sensible default — Docs→pdf, Sheets→csv, Slides→pdf, Drawings→png)
$GAPI drive download FILE_ID
$GAPI drive download DOC_ID --output ~/doc.pdf
$GAPI drive download DOC_ID --export-mime text/plain --output ~/doc.txt

# Create a folder
$GAPI drive create-folder "Reports"
$GAPI drive create-folder "Q4" --parent FOLDER_ID

# Share
$GAPI drive share FILE_ID --email alice@example.com --role reader
$GAPI drive share FILE_ID --email alice@example.com --role writer --notify
$GAPI drive share FILE_ID --type anyone --role reader        # anyone with link
$GAPI drive share FILE_ID --type domain --domain example.com --role reader

**Processing incoming share requests** — NDR's recurring workflow: search Gmail for `drive-shares-dm-noreply@google.com` emails, extract requester + file ID, grant viewer + 30-day expiry, verify, then notify the requester via WhatsApp deep link. See `references/drive-process-share-requests.md`.

# Delete — defaults to trash (reversible). Use --permanent to skip the trash.
$GAPI drive delete FILE_ID
$GAPI drive delete FILE_ID --permanent
```

### Contacts

```bash
$GAPI contacts list --max 20
```

### Sheets

```bash
# Create a new spreadsheet
$GAPI sheets create --title "Q4 Budget"
$GAPI sheets create --title "Inventory" --sheet-name "Stock"

# Read
$GAPI sheets get SHEET_ID "Sheet1!A1:D10"

# Write
$GAPI sheets update SHEET_ID "Sheet1!A1:B2" --values '[[\"Name\",\"Score\"],[\"Alice\",\"95\"]]'

# Append rows
$GAPI sheets append SHEET_ID "Sheet1!A:C" --values '[[\"new\",\"row\",\"data\"]]'
```

### Docs

```bash
# Read
$GAPI docs get DOC_ID

# Create a new Doc (optionally seeded with body text)
# Note: Docs API doesn't support a --parent folder parameter.
# Documents land in Drive root; use Drive API to move post-creation.
$GAPI docs create --title "Meeting Notes"
$GAPI docs create --title "Draft" --body "First paragraph..."

# Append text to the end of an existing Doc
$GAPI docs append DOC_ID --text "Additional content to append"
```

### Docs — Surgical Multi-Section Editing (via build_service + batchUpdate)

For editing an existing Google Doc that's more complex than a single find-replace — inserting whole sections between existing ones, rewriting section bodies, adding numbered list items, fixing merged headings:

- Load `references/docs-surgical-edit-multi-section.md` for the full workflow: index mapping, insertText/deleteContentRange/replaceAllText, heading-merge recovery, re-read-between-batches discipline.
- The `google_api.py` CLI wrapper (`$GAPI docs append`) appends only to the end. For surgical insertions anywhere in the middle, use the raw Python API via `build_service('docs', 'v1')` + `batchUpdate`.
- For single-paragraph inserts with formatting preservation, see `references/docs-insert-paragraph-with-format.md`.

## Output Format

All commands return JSON. Parse with `jq` or read directly. Key fields:

- **Gmail search**: `[{id, threadId, from, to, subject, date, snippet, labels}]`
- **Gmail get**: `{id, threadId, from, to, subject, date, labels, body}`
- **Gmail send/reply**: `{status: "sent", id, threadId}`
- **Calendar list**: `[{id, summary, start, end, location, description, htmlLink}]`
- **Calendar create**: `{status: "created", id, summary, htmlLink}`
- **Drive search**: `[{id, name, mimeType, modifiedTime, webViewLink}]`
- **Drive get**: `{id, name, mimeType, modifiedTime, size, webViewLink, parents, owners}`
- **Drive upload**: `{status: "uploaded", id, name, mimeType, webViewLink}`
- **Drive download**: `{status: "downloaded", id, name, path, mimeType}`
- **Drive create-folder**: `{status: "created", id, name, webViewLink}`
- **Drive share**: `{status: "shared", permissionId, fileId, role, type}`
- **Drive delete**: `{status: "trashed" | "deleted", fileId, permanent}`
- **Contacts list**: `[{name, emails: [...], phones: [...]}]`
- **Sheets get**: `[[cell, cell, ...], ...]`
- **Sheets create**: `{status: "created", spreadsheetId, title, spreadsheetUrl}`
- **Docs create**: `{status: "created", documentId, title, url}`
- **Docs append**: `{status: "appended", documentId, inserted_at, characters}`

## Rules

1. **Never send email, create/delete calendar events, delete Drive files, share files, or modify Docs/Sheets without confirming with the user first.** Show what will be done (recipients, file IDs, content, share role) and ask for approval. For `drive delete`, prefer the default trash (reversible) over `--permanent`.
2. **Check auth before first use** — run `setup.py --check`. If it fails, guide the user through setup.
3. **Use the Gmail search syntax reference** for complex queries — load it with `skill_view(\"google-workspace\", file_path=\"references/gmail-search-syntax.md\")`.
4. **Calendar times must include timezone** — always use ISO 8601 with offset (e.g., `2026-03-01T10:00:00-06:00`) or UTC (`Z`).
5. **Respect rate limits** — avoid rapid-fire sequential API calls. Batch reads when possible.
6. **When the user insists a file exists ("check again, it was sent by X / it's in the drive or emails"), be exhaustive, don't stop at one failed query.** The user's specificity about the sender, project, and file type is a signal to exhaust all search paths before concluding "not found": search Drive by name variants, fullText, folder listing; search Gmail by sender + attachment keywords, walk all thread messages for attachments and inline images (Content-ID), check trashed files, render PDF pages for visual inspection. Report what you found and what you didn't, with the search paths you tried.

7. **Name the account and the artifact state in every completion report.** More than one Google account is in play (`google-draas`, `google-gmail`, `google-ahfl`), and the user cannot see which mailbox a draft was created in or which Drive account a file was shared from. State it ("the draft is in nishantranka@gmail.com", "editor access went to ck@semlani.com"), and when the sending address differs from a letterhead/signature address, flag the mismatch and offer to align it. An unstated account choice reads as a failure and sends the user hunting in the wrong mailbox — see `references/gmail-draft-account-and-provenance.md`.
8. **Verify rendered formatting before reporting done, and verify it against the RENDER.** For Docs work, export to HTML and count colours (`references/docs-revision-marking-in-blue.md`); for Sheets, read the cells back. A write that returned HTTP 200 can still be invisible to the reader (unstyled runs, wrong cell, stale formatting). When a verification script reports "nothing was applied", suspect the verifier before rebuilding the artifact — read the response shape again first.

9. **Sheets structural edits:** resolve the target tab's `sheetId` by title (never assume 0), check `capabilities.canEdit` before `batchUpdate`, and use `gws_sheets_get_tabs` / `gws_sheets_rename_tab`. A view-only file returns `403 The caller does not have permission`; a `canCopy=true` file can still 403 `insufficientFilePermissions` on `files.copy`. See `references/sheets-tab-rename-and-copy.md`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| **Drive upload via `build_service` fails: `media_filename must be str or MediaUpload`** | `files().create(body=..., media_body={"path": "/tmp/x.pdf"})` is a dict, not a media object — the API refuses it. Wrap with `googleapiclient.http.MediaFileUpload`: `media = MediaFileUpload(local_path, resumable=False); drive.files().create(body={"name": ..., "parents": [folder_id]}, media_body=media, fields="id,name,size").execute()`. Verified 2026-09-22 while building the DRA Projects director-evidence folder (10-file batch). |
| **Google Sheets `values().get()` returns `503 The service is currently unavailable`** (transient — seen on the not-spam whitelist read, 2026-09-06) | Google-side transient, NOT an auth/vault failure. Signature: identity guard prints fine, script reports `fatal: <HttpError 503 ... "The service is currently unavailable">`, `checked: 0`. No scope/token change needed: sleep ~20s and retry — succeeds without code change. Do NOT generate OAuth URLs or declare the vault down. |
| **Drive download fails: `'HttpRequest' object is not iterable`** | `drive.files().get_media(fileId=...)` returns an HttpRequest, NOT an iterable body — you must call `.execute()` on it (`data = drive.files().get_media(fileId=..).execute()`) for files < ~100 MB, or wrap in `MediaIoBaseDownload` for huge files. NEVER do `for chunk in media:` — it raises this exact error. (Verified 2026-09-09 bulk evidence download.) Also see `references/legal-matter-discovery-sweep.md` for the full bulk .eml + docs evidence-pack pipeline. |
| `REFRESH_FAILED` | Token revoked or expired — redo Steps 3-5 |
| `HttpError 403: Insufficient Permission` | Missing API scope — `$GSETUP --revoke` then redo Steps 3-5. **For Gmail filters specifically** (`settings.filters().create()` needs `gmail.settings.sharing`): combo workaround: native filter (`removeLabelIds: ["INBOX"]`) for instant skip-inbox + periodic no_agent cron script using `batchModify(addLabelIds: ["SPAM"])` to sweep All Mail → SPAM. See `references/gmail-blacklist-spam-mover.md`. |
| `AUTHENTICATED (partial)` or "Token missing scopes" | New write capabilities (Drive write/delete, Docs create/edit) require re-authorization. `$GSETUP --revoke` then redo Steps 3-5 to grant the upgraded scopes. |
| **`HttpError 403: Access Not Configured`** | API not enabled — user needs to enable it in Google Cloud Console |
| **`ModuleNotFoundError`** | Run `$GSETUP --install-deps` (or use Hermes venv: `/opt/hermes/.venv/bin/python3 setup.py ...`) |
| **LibreOffice not installed** (`libreoffice --headless --convert-to pdf` fails) | Use weasyprint: extract text+formatting from .docx with python-docx, rebuild as HTML with inline styles, render via `weasyprint`. Full recipe in `references/docx-to-pdf-via-weasyprint.md`. |
| `invalid_grant: Token has been expired or revoked` | Token expired. Re-authorize via the standard gws OAuth flow (`send_oauth_url` / `gws_resolve_account`) — the refreshed token is vault-stored automatically. Do NOT reconstruct or create any credential files. |
| **`gws_auth.has_token(svc)` returns True but `build_service` refresh fails `invalid_grant`** | `has_token` only checks that a token exists in the vault — it does NOT verify freshness. A revoked/expired token still shows `has_token: True`. When you hit `invalid_grant` on refresh, the fix is re-auth via `send_oauth_url`, not vault troubleshooting. See `references/oauth-reauth-terminal-pattern.md`. **Before sending any re-auth link, LIVE-PROBE each account the user might mean** (e.g. gmail `users().getProfile()`, people `connections().list()`) — the user often names the wrong account, and a dead token only reveals itself under a real call (real case 2026-09-05: user asked to re-authorize "my gmail.com"; nishantranka@gmail.com was healthy, ndr@ahfl.in was invalid_grant — probed both, sent the button only for the dead one). |
| **`send_oauth_url` from a terminal subprocess fails: "TELEGRAM_BOT_TOKEN not set"** | The bot token lives in the gateway process env, not the shell env. Extract it from `/proc/<gateway_pid>/environ` and pass `TELEGRAM_BOT_TOKEN=... HERMES_SESSION_PLATFORM=telegram HERMES_SESSION_CHAT_ID=<user chat id>` so the tool delivers the Telegram button. The authorizing identity comes ONLY from `HERMES_SESSION_USER_ID` — set it to the slug (e.g. `ndr`) so the refreshed token files under the right vault entry. See `references/oauth-reauth-terminal-pattern.md`. |
| **User says "yes, go ahead" but no token landed / user can't see the OAuth button / repeated sends hit "Flood control exceeded"** | (1) Re-check `gws_resolve_account` no-args before running the blocked op — "yes" ≠ authorized; if still `has_token: false`, the flow never completed. (2) The button may be delivering to the profile Home channel, not the user's DM (Home id can be ANOTHER person's telegram id) — re-deliver via terminal subprocess with explicit `HERMES_SESSION_CHAT_ID=<user's own telegram id>` (from `list_identities()` `telegram` field) + `HERMES_SESSION_USER_ID=<vault slug>` (discover via `list_identities()`, never guess from display name — Roshini = `rnr`, not `roshini`). (3) Repeated sends hit Telegram flood control (~10 min cooldown, `Retry in ~594 seconds`) — schedule ONE background retry sleeping past the cooldown with the explicit env, don't spam. Full recipe in `references/oauth-reauth-terminal-pattern.md` §First-time authorization. |
| **People API `people/me` with `personFields='emailAddresses'` → 403 "requires one of the following scopes: [profile]"** | The granted contacts scope does NOT include `profile`. Use `people().people().searchContacts(query=..., readMask='names,emailAddresses,phoneNumbers')` instead — it works with the contacts scope and is the correct way to look up a contact's email by name. See `references/people-api-contact-search.md`. |
| `externally-managed-environment` error in setup.py | System Python (`/usr/bin/python3`) is PEP 668 managed. Always run setup.py via `/opt/hermes/.venv/bin/python3` — Google API deps are pre-installed there. |
| Advanced Protection blocks auth | Workspace admin must allowlist the OAuth client ID |
| **gws_skill_bridge bridge AttributeError** (any operation) | The bridge converts kwargs to SimpleNamespace — optional fields accessed with bare `if args.xxx:` throw AttributeError. See `references/gws-bridge-pitfalls.md` for the exact kwarg workaround per operation. |
| **Hand-rolled Gmail body walker returns EMPTY bodies for messages that clearly have text (`format='full'`)** | The Gmail API stores base64 body data at `part['body']['data']`, NOT at the top level of the part dict. A walker that tests `if 'data' in part:` (or decodes `part['data']`) silently finds nothing and returns empty — even when the MIME dump shows `text/plain body_size=7536 data=True`. Fix: test `part.get('body', {}).get('data')` and decode that. Prefer text/plain parts; strip tags from text/html only if plain is empty (HTML-only messages are common from business senders). Session hit 2026-09-16 while fetching all 5 Flameback Sep-15 email threads: every body came back empty until the walker was fixed. |
| **`gmail_get` via bridge returns empty body + no attachments** | The bridge's `gmail_get` extracts headers and text body only — it does NOT return attachments. This is by design: the DWD ops (`gws_dwd_gmail_get`, `gmail_thread_get`) return attachment metadata (name, size, mimeType) but deliberately strip attachment bytes. Two escape hatches: (A) use `build_service('gmail', 'v1')` with `format='full'`, walk `payload.parts` for `filename` + `body.attachmentId`, then `attachments().get()` — see `references/gmail-attachment-to-drive.md`. (B) use `format='raw'` which returns the complete RFC822 message as a base64 string, then parse with `email.parser.BytesParser()` — better for deeply-nested MIME or when the `payload.parts` walk is fragile (large messages, complex inline/attachment mix). See `references/gmail-attachment-to-drive.md` §Raw-MIME alternative. |
| **DWD Gmail returns `unauthorized_client` even though the Admin Console shows `mail.google.com` scope granted** | Scope strings are exact-match in Google's DWD. The Admin Console may show the **legacy** `https://mail.google.com/` scope while the Hermes DWD tool requests the **granular** `https://www.googleapis.com/auth/gmail.modify` — these are DIFFERENT strings, so token minting fails. Diagnosis: probe each concrete scope string against the live vault building a gmail service with each scope variant. If `mail.google.com` works but `gmail.modify` fails, the Admin Console grant needs updating (add the granular scope) or the tool code needs patching to use the legacy scope string. Verified 2026-09-12 on piyush@draas.com and crm.blr@draas.com — `mail.google.com` returned 200, all granular scopes returned `unauthorized_client`. Same root cause for ANY DWD scope mismatch. Use the `format='raw'` escape hatch (`references/gmail-attachment-to-drive.md` §Raw-MIME) to download attachments when the metadata-only DWD tool layer blocks the happy path. |\n| **A reply draft created with `drafts().create(raw=...)` + In-Reply-To/References lands in its OWN new thread** (`threadId` returned = the draft's own message id, not the original thread) | Gmail does NOT re-thread from the `References` header when you insert raw MIME. Pass the original thread explicitly: `drafts().create(userId='me', body={"message": {"raw": raw, "threadId": "<original threadId>"}})` where `threadId` comes from `messages().get(id=<any message in the thread>, format='minimal')['threadId']`. ALWAYS verify after creating: refetch with `drafts().get(format='metadata')` and assert `message['threadId'] == original`. Fixing after the fact means delete the mis-threaded draft (`drafts().delete`) and recreate — you cannot re-parent a draft. Verified 2026-09-17 (Prakash Singh reply on the Ranka Udaya thread). |
| **`drafts().get()` raises `TypeError: Got an unexpected keyword argument metadataHeaders`** | `metadataHeaders` is a `messages().get` parameter ONLY — `drafts().get` does not accept it. Verify a draft with `drafts().get(userId='me', id=..., format='metadata')` and read the returned `payload.headers` (From/To/Subject come back by default). Real case 2026-09-09 (post-`draft_create` verification). |
| **Gmail `messages().get()` 404 "Requested entity was not found" for an ID that EXISTS in search results** | Gmail message IDs are **account-scoped, not global**. If a search ran across all three vault accounts (google-draas / google-ahfl / google-gmail) and you fetch a hit's ID using a DIFFERENT account's service than the one whose search produced it, you get a 404 even though the message plainly exists (verified Aug 2026: 2011 "Prestige Hermitage" threads listed under google-gmail 404'd when fetched via google-draas; refetching via google-gmail worked). Rule: **fetch each message with the exact account whose search returned the ID** — in a cross-account loop, keep `service_name` from the account that produced the hit, don't reuse the first service. Old personal threads (2011-era) almost always live in google-gmail (nishantranka@gmail.com), not the work accounts. |
| **Drive share: `Expiration dates cannot be set on this item`** (at `permissions().create()` time) | Do NOT conclude My Drive can't do expiry — it can, just not on CREATE. Create the share plain, then PATCH it: `permissions().update(fileId=..., permissionId=pid, body={"role": "reader", "expirationTime": "<RFC3339>"}, supportsAllDrives=True)`. `role` is **required** in that body (400 `The permission role field is required` otherwise), and the update response does **not** echo `expirationTime` — verify with a separate `permissions().list(fields="permissions(id,emailAddress,role,expirationTime)")` before reporting. Verified 2026-09-26 on a My Drive FILE (30-day reader grant). See `references/drive-share-pitfalls.md` §1. |
| **Drive share update fails `403 Cannot modify a permission on an item to be less than the inherited access from a direct or indirect parent`** | The recipient already holds a STRONGER role inherited from a parent folder (e.g. writer on the folder → writer on every file inside). You cannot downgrade the file-level permission below the inherited level — even when you are the file owner. Fix at the PARENT level (remove/downgrade the folder share) or move the file out of the shared folder; otherwise writer (which includes view) is in place and that is the correct report to the user. Do NOT loop retrying the file-level update. Verified 2026-09-22 on Ranka Amber executed SSA PDFs for sales1.blr@draas.com ("Bharat needs viewer only"). See `references/executed-agreement-source-verification.md` for the full safe-sharing workflow. |
| **`File not found` on a folder you know exists** | The session user's Drive account may differ from the file owner's. `build_service()` always uses the current session user — bypass via vault token (see `references/drive-share-pitfalls.md` §2). |
| **GWS auth: hand-rolling vault-client socket calls, or `GWS_VAULT_SOCKET is not set` in `execute_code`** | Use the sanctioned wrapper `tools.gws_auth.build_service(api, version, service_name=...)` (e.g. `service_name='google-draas'`) — do NOT call `tools.gws_vault_client.get_token()`/`resolve()` directly in ad-hoc scripts (Nishant corrected this Aug 2026: "just run the GWS client using the GWS client tool"). Run GWS scripts via `terminal()`, not `execute_code` — the sandbox lacks the vault socket env var (the not-spam cron script `not_spam_check.py` documents this exact failure: the sandbox's hermes_tools stub has no `gws_fetch_token` import, so `tools.gws_auth.load_credentials()` raises ImportError there; terminal has `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock` and works). Former "maintained exception" retired Aug 2026: the not-spam whitelist check now uses the standard `build_service(service_name='google-draas')` path like everything else — canonical script: `skills/productivity/not-spam-whitelist/scripts/not_spam_check.py`. See `references/not-spam-cron-run-notes.md`. |
| **User asks "why python?" for a Drive/Gmail op — expected to use the gws client tool** | Before writing a bespoke `build_service` script for a QUICK Drive/Gmail operation (search, list children, trash/delete a few files, create folder), use the existing thin CLI wrapper at `/opt/data/gws.py` (cron-thin wrapper around `tools.gws_skill_bridge.call` / `tools.gws_auth`): `python3 /opt/data/gws.py <op> google-draas '{"query":"...","raw_query":true,"max":1000}'` — ops include resolve, drive_search, drive_get, drive_delete, drive_create_folder, drive_upload, drive_download, gmail_search, etc. NDR corrected 2026-09-10 ("use gws_client.py tool…why python?") while sweeping empty folders — the wrapper exists precisely so quick ops don't need hand-rolled auth code. Verified empty-folder sweep pattern (recursive children walk via raw-query `'<id>' in parents and trashed=false`, bottom-up trash, repeat to fixpoint; folders whose children are ALL trashed "look" empty in the UI — the trashed=false walk catches them; trashed folder shells remain in Drive trash) in `references/eml-archive-to-pdf-evidence-pack.md` §5. |
| **Calendar event silently created on the WRONG user's calendar** | `build_service('calendar','v3', service_name='google-draas')` can resolve the session to a different vault user than the requester (observed Aug 2026: session resolved to psingh@draas.com even though `gws_resolve_account` reported google-draas/ndr has_token:true; the event was created on Prakash Singh's calendar with NO error). ALWAYS verify `calendars().get(calendarId='primary')` prints the intended owner BEFORE `events().insert`. If wrong: delete the misplaced event (`events().delete`), re-run the insert with `HERMES_SESSION_USER_ID=ndr` (slug form) prefixed to the command, re-verify owner, then confirm the new event id/attendees. Same verify-first rule protects Gmail reads (wrong-user mailbox search returns empty), Drive, and Sheets. |
| **`values().update` fails 400 `Requested writing within range ['Tab'!A16:E25], but tried writing to column [F]`** | The row list is WIDER than the range. Every row must match the range's column count exactly; the error names the offending column (E means rows had 5+ elements into an A:D range, F means 6 elements into A:E). Fix the RANGE, not the data — widen it to the true column count (e.g. `A16:E25`→`A16:F25`). Hit twice in one session (Materials Prepared + Channel Partner Outreach, 2026-10-06). Count columns from the tab's header row first; do not assume 5 columns because the visible table "looks" 5-wide. |
| **Sheets `values().get`/write on a column past the grid fails 400 `Range ... exceeds grid limits. Max rows: N, max columns: M`** | Add the column FIRST with `spreadsheets().batchUpdate` → `updateSheetProperties` (`gridProperties.columnCount`, `fields: "gridProperties.columnCount"`), using the tab's real `sheetId` from `spreadsheets().get()` (never hardcode 0). Then write header + values. Verified 2026-10-08 adding col J to a 9-col sheet; see `references/gmail-bounce-delivery-status-sheet.md`. |
| **Full-column rebuild shifts every status cell one row (ghost INCORRECT marks on wrong rows)** | Loops like `for i in range(1, N): row = i+1` reading `cur_vals[i]` mis-index when data starts at row 2 (cur_vals[i] is the value for row i+2). Always iterate `range(0, row_count)` with `row = i + 2`; rebuild from a CANONICAL expected set (not preserved cell text — stale text keeps ghosts); read back and assert counts AND missing/extra rows against the set. Hit 2026-10-08: 29 INCORRECT marks became 16 + 6 ghosts at rows 675/794 etc. Full recipe: `references/gmail-bounce-delivery-status-sheet.md`. |
| **`0-04-05`-style extent strings written to Sheets become dates (read back as `2000-04-05`)** | Google Sheets auto-converts `H-A-C` (Hec-Ares-Centiares) and `Ac-Cent` notation strings like `0-04-05` into DATE values under `valueInputOption='USER_ENTERED'`. Fix: after the main USER_ENTERED write, re-write ONLY those string-notation columns with `valueInputOption='RAW'` (numeric decimal columns stay USER_ENTERED). Real case: Sevaganapalli survey extent sheet, 2026-08-31. |
| **Phone `+91...` appended to the contacts sheet with USER_ENTERED reads back without the `+` (e.g. `919650317474`)** | Sheets parses a value of `+`+digits as a number and drops the plus. After the main append, re-write only the phone cell(s) with `valueInputOption='RAW'` so `+919650317474` stays a string. Real case 2026-09-09 (Hirendra Assudani, contacts sheet row 4245). **Worse variant (2026-09-20):** the cell can come back as a literal **`#ERROR!`** instead — `USER_ENTERED` re-parses the leading `+` as a formula on EVERY write, so retrying through the same path never fixes it. Bypass the bridge: `b._build_service("sheets","v4")` + `values().update(range="AD2989", valueInputOption="RAW", body={"values":[["+66 95 985 7012"]]})`. Rule: any contacts-sheet cell starting with `+`, `-`, or `=` must be written `RAW`. Details in `references/people-api-update-contact.md`. |
| **`HttpError 400 ... "exceeds grid limits. Max rows: 4250"` when appending a new contact** | The contacts sheet is at its hard row cap. Insert a row dimension FIRST, then write: resolve `sheetId` from `spreadsheets().get()` (never assume 0), then `batchUpdate` with `insertDimension` (`startIndex`= current `gridProperties.rowCount`, 0-based), then write the new `A<last+1>:AU<last+1>` range. Also read `rowCount` before writing to learn the current cap. |
| **Adding a NEW column fails `400 Range ('Tab'!J1:J5) exceeds grid limits. Max columns: 9`** | The grid has no column J — expand it FIRST via `batchUpdate` + `updateSheetProperties`: `{"properties": {"sheetId": <tab sheetId>, "gridProperties": {"columnCount": <old+1>}}, "fields": "gridProperties.columnCount"}`. Resolve the tab's real `sheetId` from `spreadsheets().get()` (never assume 0), then write the new column. Verified 2026-10-08 (Hosur SMEs HOSTIA — added "Email Status" column J to a 9-col grid). |
| **Full-column status rebuild silently shifts every mark one row UP (INCORRECT count 29→16, stale marks at row-1 positions)** | When rebuilding a whole column from a read-back (`J2:J1202` = 1201 rows) plus computed status sets, build `col[i]` for i in 0..N-1 mapping **row = i+2**. A loop starting at 1 (`for i in range(1,N): row=i+1` but reading `cur_vals[i]`) reads the NEXT row's value and shifts every mark up one row; stale cells linger one row off with no error. ALWAYS verify after writing with **SET EQUALITY** (computed row set == read-back row set), not just counts. Verified 2026-10-08. |
| **`HttpError 400 "Range ('Tab'!J1:J5) exceeds grid limits. Max rows: 1202, max columns: 9"` when writing to a NEW column** | The tab's grid is narrower than the range — the destination column doesn't exist yet. Expand the grid FIRST via `batchUpdate` + `updateSheetProperties` (`properties: {sheetId: <real sheetId from spreadsheets().get()>, gridProperties: {columnCount: N}}, fields: "gridProperties.columnCount"`), verify, then write. Do not assume an empty column past the last one; Sheets has no implicit column creation. Verified 2026-10-08 adding an "Email Status" column J to a 9-column leads tab. |
| **`IndexError: list assignment index out of range` while editing a contacts row** | `sheets_get` trims trailing empty cells, so a row read over `A2989:AU2989` can return only 35 elements, not 47. Pad before assigning by index: `r = list(rows[0]); while len(r) < 47: r.append("")`. Never assume a fixed length from the range string. |
| **About to delete duplicate contacts found by name-substring search** | A substring match is NOT an identity match — DRAAS contact names embed roles/contexts, so "Rivaan" also matched `Ramesh Rivaan Kannada Teacher` and `Uma Panicker Rivaan 3 Aditi Panicker` (both different people). Only EXACT-name matches are in scope for deletion; dump full fields for every candidate, pick the survivor by richest data + correct group, and explicitly tell the user which near-misses you left alone. See `references/people-api-update-contact.md`. |
| **`spreadsheets().create()` then batchUpdate fails `Invalid requests[0].updateSheetProperties: No sheet with id: 0`** | The first sheet of a newly created spreadsheet does NOT always have sheetId 0 (real case: 707851286). Always fetch `spreadsheets().get(spreadsheetId=...)` → `sheets[0].properties.sheetId` before any batchUpdate that references a sheetId. Never hardcode 0. | `values().get()` returns rows **0-indexed** (row 0 = header), but cell ranges like `Sheet1!O10` are **1-indexed** (row 1 = header). A project found at list index 9 is spreadsheet row **10**. Writing to `O9:T9` when the target is list-index 9 silently edits the row ABOVE (real case 2026-08-14: overwrote the White Lotus Amanvana row while updating Sobha Oakshire — had to restore from the pre-read). ALWAYS: (1) pre-read the exact target range before writing, (2) map `list_index + 1` → spreadsheet row, (3) write the exact cell ranges, (4) read back and verify the row's project name matches what you intended. Also: cells can hold MULTIPLE `filename\nhttps://...` link pairs on separate lines — when updating one link inside such a cell, rewrite the full cell content including the unchanged links (e.g. T10 held both 102 and 104 layout links; writing only the new 102 silently dropped 104). |
| **Reordering whole rows scrambles when using `moveDimension`** | Row permutation via `moveDimension` is index-math-fragile: moves shift 0-based indices and a wrong permutation succeeds silently (real case 2026-08-17: 10 moves "applied" but interleaved sale/agreement rows). Reliable approach: compute the sorted/grouped table in Python, `values().clear` + `values().update` the whole grid with `=HYPERLINK("url","url")` for link columns, then re-apply section/subtotal formatting via `updateCells`. Verify by reading back. See `references/sheets-row-reorder-and-date-serial.md`. |
| **Date column shows text `11-01-2023` but sorts as Nov (serial 45231)** | Sheet locale `en_US` parsed an Indian DD-MM-YYYY entry as MM-DD. `FORMATTED_VALUE` hides it; check `UNFORMATTED_VALUE` for numeric serials. Cross-check the document filename / registration FY (`12781/22-23` ⇒ FY 2022-23 ⇒ cannot be Nov 2023), then fix the cell to text before sorting. See `references/sheets-row-reorder-and-date-serial.md`. |
| **`batchUpdate` on a freshly created spreadsheet fails `400 ... No sheet with id: 0`** | `sheets.spreadsheets().create()` does NOT guarantee the default sheet has `sheetId: 0`. Fetch the real id first: `meta = sheets.spreadsheets().get(spreadsheetId=sid).execute(); sheet_id = meta['sheets'][0]['properties']['sheetId']` and use it in every `updateSheetProperties`/`updateCells`/`repeatCell` range. Real case 2026-08-31 (Sevaganapalli survey sheet): created sheet id was `707851286`, not 0. |
| **Dash-formatted unit strings (`0-36`, `0-04-05`, `5-79-51`) silently become dates (`2000-04-05`) after `values().update`** | `valueInputOption='USER_ENTERED'` parses `H-A-C` / `A-C` style strings as dates. Fix: write numeric columns with USER_ENTERED, then re-write the text-format columns with `valueInputOption='RAW'` so they stay strings; always read back and confirm the format columns are strings. Real case 2026-08-31 (Hectares-Ares-Cent / Acres-Cents columns in a land-extent sheet). |
| **Sheets via build_service: `AttributeError: 'Resource' object has no attribute 'batchUpdate'/'values'`** | The Sheets service exposes a single top-level collection, `spreadsheets` — ALL calls go through `sheets.spreadsheets()...`: `batchUpdate(...)`, `values().update(...)`, `values().get(...)`. There is NO `sheets.values()` or `sheets.batchUpdate()`. (Contrast with Drive where `drive.files().get(...)` works because `files` IS the top-level collection.) Verified 2026-09-24 while uploading a 410-row project CSV to a new spreadsheet. |
| **Multi-step create→populate spreadsheet script fails midway and rerunning duplicates the file** | Make the script idempotent: read `REUSE_SHEET_ID` from env; when set, skip `spreadsheets().create()` and reuse that id for rename/write/verify. On any later-step error, rerun with `REUSE_SHEET_ID=<printed id>` — the same spreadsheet gets filled instead of a fresh empty one. Always finish with a read-back row-count assert. See `references/csv-upload-to-new-sheet.md`. |
| **Docs API fails on a Drive file the user calls "the Google Doc": `HttpError 400 ... "This operation is not supported for this document. The document must not be an Office file."`** | The file is a .docx on Drive, not a native Google Doc — `documents().get()`/`batchUpdate` cannot touch it. Edit the .docx directly: download → lxml edit of `word/document.xml` (python-docx spacing writes don't persist; write `<w:spacing>` elements explicitly) → `files().update()` re-upload preserving the same file ID/link. Render-verify via temp Google Doc → PDF → PNG. See `references/docx-format-edit-in-place.md`. |
| **Docs batchUpdate 400: `Unknown name "createTable" at 'requests[0]': Cannot find field`** | The Docs API request field is `insertTable`, NOT `createTable` (which exists in other Google APIs). Real case 2026-09-22 letterhead rebuild. |
| **Docs batchUpdate 429: `Quota group for write operations per minute per user` (limit 60/min)** | Docs write quota is ~60 requests/min/user. Sleep ~1.3 s between write calls, retry on 429 with a 20 s sleep, and chunk request lists at ≤90 per call. Real case 2026-09-22 letterhead rebuild. |
| **Table cells filled sequentially end up empty / text piles into cell[0,0]** | Inserting into table cells one at a time with indices captured once shifts every later cell. Build ALL cell requests for the table and submit ONE batchUpdate sorted **descending by base index** (each cell = insertText at empty-paragraph start + per-run updateTextStyle). Real case 2026-09-22 letterhead rebuild — see `references/docs-letterhead-finalize.md`. |
| **Docs batchUpdate 400: `Width type must be provided when updating column width`** | `updateTableColumnProperties` 400s unless `tableColumnProperties` carries `widthType`. Use `{'width': {'magnitude': N, 'unit': 'PT'}, 'widthType': 'FIXED_WIDTH'}` with `fields: 'width,widthType'`. Real case 2026-09-12 Ranka Ankura letterhead cleanup. |
| **A "table helper" returns the body element, not the table object → cells silently never fill** | Helpers that return the element `{'startIndex':…, 'table': {'tableRows': […]}}` break downstream code that calls `.get('tableRows', [])` on the ELEMENT — it gets `[]`, so the fill batch contains only shading/width requests and every cell stays `"\n"`. No error, just an empty table. Always unwrap `el['table']` before reading `tableRows`, and verify AFTER a fill that cells actually hold text (a filled table whose cells all read `"\n"` is the signature). Real case 2026-09-12: the facts table looked "inserted" but had zero text. |
| **Phantom blank second page on a letterhead-copy rebuild** | The template's trailing empty paragraph (often 13pt Tahoma) can spill onto page 2 after a tight one-page letter — PDF shows page 2 with 0 chars but the header/footer images, and pdftoppm renders it as a blank PNG that looks fine. Kill it by targeting the LAST paragraph: `updateTextStyle` fontSize 1pt + `updateParagraphStyle` lineSpacing 50, spaceAbove/spaceBelow 0. Range must be `[startIndex, endIndex)` — the run IS the "\n" so `endIndex - 1 == startIndex` and `[start, end-1)` 400s "range should not be empty". Do NOT pass `spaceAboveEm`/`spaceBelowEm` in textStyle — not valid fields (400 Unknown name). Verify page count with pymupdf (`fitz`) — len(page.get_text()) is 0 on the phantom, which pdftoppm+vision can't distinguish from a real blank. Real case 2026-09-12 Director's letter. |
| **`$GAPI calendar list` shows event IDs truncated — using them directly in API calls gives 404** | The `google_api.py` CLI wrapper (`$GAPI calendar list`) truncates event IDs in its display output. Event `c8r32ob66pi32bb5c8p6` in the wrapper output is actually `c8r32ob66pi32bb5c8p6ab9k69gm6b9p64s64b9p75hjidb36go30d1l68` from the real API. When you need the full event ID for update/delete, use the raw Python API (`build_service('calendar','v3') → events().list()`) and read the `id` field from the response — never copy the truncated ID from `$GAPI` output. |
| **Calendar `htmlLink` "not working" — the eid was hand-edited (verified 2026-09-30)** | NEVER hand-edit/sanitize a Google Calendar `htmlLink` eid. The eid is ONE continuous base64 string = event-id + calendar-email concatenated — e.g. `OGpiMzdxaWlhcHU2M2g3a3JsbmFhZzV1cXMgbmRyQGRyYWFzLmNvbQ` decodes (`base64.b64decode(eid + '==')`) to `8jb37qiiapu63h7krlnaag5uqs ndr@draas.com`. It contains NO literal space and must NOT be percent-encoded; inserting a `%20` corrupts it and the user's tap fails ("calendar link is not working"). Fix: re-fetch the event via `events().get(calendarId=..., eventId=...)` and paste `htmlLink` VERBATIM (optionally append `&ctz=Asia/Kolkata`); do not re-type it — write it to a file and read it back. Verification ladder: (a) decode the eid and match the event id + calendar email (authoritative), (b) `curl -sIL` returns 200, (c) note that an UNAUTHENTICATED browser showing the Google Calendar marketing page is NOT a broken-link signal for a non-public event. |
| **User says they authorized (saw "Authorization successful!") but `gws_resolve_account` lists every service `has_token: false` and `gws_fetch_token` says "No google token for user"** | Check whether the token landed under a **non-default service key** before telling them to re-authorize. Since 2026-09-09 the callback derives the key from the email DOMAIN (`_service_for_email`): any @draas.com → `google-draas`, @ahfl.in → `google-ahfl`, @gmail.com → `google-gmail`. If the account is @draas.com but the token is not under `google-draas`, verify the actual service list first (`gws_resolve_account` no-args / `list_services`). Also note the vault resolve quirk: a raw Telegram id can canonicalize to `psingh-<tid>` while the user's services live under their email uid (e.g. `admin3.blr@draas.com`). |
| **`VaultNoTokenError: No google-draas token for user <X>` on a user's FIRST Google authorization (no token has ever existed)** | The OAuth never completed — not (only) a wrong slug. Diagnostic ladder: 1) `gws_resolve_account` no-args — `has_token: false` across every service means no token exists anywhere; 2) enumerate vault identities + their tokens: `/opt/hermes/.venv/bin/python3 -c "from tools.gws_vault_client import list_identities,list_services; [print(i['user_id'],i.get('slug'),list_services(i['user_id'])) for i in list_identities()]"` — the canonical vault user_id is `<slug>-<telegram_id>` (e.g. `rnr-7245204091`), NOT the bare telegram id that HERMES_SESSION_USER_ID may carry (e.g. `7245204091` is not a vault uid) and NOT a guessed slug (Roshini's slug is `rnr`, not `roshini`); 3) an empty service list means the OAuth callback never stored a token → resend `send_oauth_url`; the user must complete Google sign-in to the **"Authorization successful!"** page. Do NOT treat "yes please" / "I authorized" as proof — re-run `gws_resolve_account` and confirm `has_token` flips true before inserting calendar events. Verified 2026-09-30 (Roshini rnr first auth: accounts listed with emails under google-draas/google-gmail but zero tokens; calendar insert correctly blocked). |
| **`gws_resolve_account`/`build_service` fails: "Vault socket unreachable at /opt/data/gws-vault/run/vault.sock"** | The `GWS_VAULT_SOCKET` env var can be stale — the live socket is at `/run/gws-vault/vault.sock`. Check `ls -la /run/gws-vault/`. Fix per-command: `GWS_VAULT_SOCKET=/run/gws-vault/vault.sock python3 ...` (or export it). The vault daemon itself is usually fine. See `references/gmail-code-password-lookup.md` §Vault. |
| **Searching the WRONG user's mailbox (session env resolves to a different vault user than the requester)** | `build_service()` reads `HERMES_SESSION_USER_ID` from the environment — in cron/forwarded sessions it can point at another user (e.g. ndr) while the requester is sales1.blr. Override it per-command: `HERMES_SESSION_USER_ID=sales1_blr python3 ...` (slug form resolves cleanly; raw id `sales1.blr-[REDACTED-TID]` also works as fallback key but logs a warning). Always verify with `users().getProfile()` → prints the mailbox email. Only ever target the requesting user's OWN account — never another user's. Confirmed for psingh@draas.com (employee): the session telegram id resolves to `ndr-[REDACTED-TID]` in the vault, so employee Drive work must run with `HERMES_SESSION_USER_ID=psingh` (slug) or it authenticates as ndr and 404s on psingh-visible folders. **Calendar can resolve to psingh even when Gmail resolves to ndr (confirmed 2026-08-13):** in a session where `build_service('gmail','v1',service_name='google-draas')` authenticated as ndr@draas.com, the identical calendar call (`build_service('calendar','v3',service_name='google-draas')` + `events().insert(calendarId='primary')`) created the event on psingh@draas.com's calendar. Always verify with `calendars().get(calendarId='primary')` before inserting, and run calendar ops with `HERMES_SESSION_USER_ID=ndr` (slug) to force the right owner. |
| **Calendar event created on the WRONG user's calendar (owner prints psingh@draas.com instead of ndr@draas.com)** | `build_service('calendar','v3',service_name='google-draas')` can resolve to a different vault identity than the requester even in the requester's own session. ALWAYS call `calendars().get(calendarId='primary')` and read the `id` field BEFORE `events().insert()` — and act on it, don't just print it. If wrong: delete the misplaced event (same resolved service can delete it), then re-run with `HERMES_SESSION_USER_ID=ndr` and re-verify the owner before inserting. Confirmed 2026-08-13 — a meeting invite to rnr@draas.com was created on psingh's calendar and had to be deleted + recreated. |
| **`build_service()` without `service_name` fails `No google token for user <uid>` even though `gws_resolve_account` says has_token: true** | `build_service(api, version)` defaults the vault service key to `google`, but DRAAS tokens live under `google-draas` / `google-ahfl` / `google-gmail`. Always pass `service_name='google-draas'` explicitly. Working combo for psingh: `HERMES_SESSION_USER_ID=psingh` + `service_name='google-draas'` → authenticates as psingh@draas.com; omitting either yields ndr identity or a false not-authorized error. |
| **Drive 404 on a deck shared to the user in an earlier session (PDF export fails "File not found")** | `gws_resolve_account(email)` can say `has_token: true` while `build_service` still authenticates as a DIFFERENT account (observed: psingh@draas.com resolved to google-draas has_token:true, but auth came back as sales1.blr@draas.com). Signature: the target deck AND every sibling deck from that same prior session 404 together, search finds nothing. Don't fight it with `HERMES_SESSION_USER_ID` overrides — they didn't change the identity. Fix: `send_oauth_url(login_hint=<email>, label=...)` so the owning/editor account re-authorizes, then re-verify with `about().get(fields="user(emailAddress)")` before exporting. See `references/slides-to-pdf-export.md`. |

## Revoking Access

```bash
$GSETUP --revoke
```
