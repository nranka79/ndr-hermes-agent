# Google Docs Editing via Docs API — blue-text redline workflow (DRAAS)

Session-proven recipes for the recurring "edit a Google Doc with all changes in BLUE" request
(offer letters, MOUs, contracts, agreements). Companion: `references/gws-automation.md` for
general GWS plumbing (build_service, Drive upload).

## THE user convention: all changes in BLUE
- Every modification/insertion/replacement → blue text RGB(0,0,255):
  `{"foregroundColor": {"color": {"rgbColor": {"red": 0, "green": 0, "blue": 1}}}}`
- Original/unchanged text stays black. Bold+blue when replacing text that was bold
  (name strings in contract boilerplate). Headings: blue+bold.
- Placeholders for unknown data go in blue too: `[TBD]` / `[●]` — user fills during review.
- After editing ALWAYS run a blue audit (chars whose textRun textStyle.foregroundColor ==
  blue / total chars) and report % in the summary. Note: read the color from `textRun.textStyle`,
  NOT from the element level — element-level access returns {} and the audit falsely shows 0%.

## Upload docx (from Gmail attachment) → Drive → Google Doc
1. Fetch attachment: `gmail.users().messages().get(id=..., format='full')`; walk
   `payload.parts` for `attachmentId`; `messages().attachments().get(...)`; base64
   urlsafe_b64decode(data + '=='); save to /tmp.
2. Find folder: `drive.files().list(q="name contains 'temp' and mimeType='application/vnd.google-apps.folder' and trashed=false")`.
   DRA Temp folder = `0B1Oc8cSaJXPGMFFCRWtqQ2lqSDQ` (under RAQ).
3. Upload+convert one shot:
   `drive.files().create(body={'name':..., 'parents':[folder_id], 'mimeType':'application/vnd.google-apps.document'},
   media_body=MediaFileUpload(path, mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'))`
4. Re-read the converted doc structure BEFORE computing indices — conversion restructures
   paragraphs/tables and shifts all indices.

## CRITICAL: batchUpdate indices shift sequentially
Requests apply in order; each request's indices refer to the state AFTER previous requests.
- Filling a fresh table with indices from one pre-read: after the first insertText lands, later
  insert positions shift → ALL text ends up in the first cell (R0C0). API reports success — no error.
- FIX (table fill): `insertTable` → FRESH read of cell start indices → single batch where inserts
  are sorted ascending by original index with running offset:
  `idx = orig_start + running; running += len(text)`.
- For any multi-edit batch: order edits by descending original index, or recompute offsets.

## insertTable / deleteTableRow pitfalls
- insertTable at a stale index lands mid-paragraph, splitting text: "…FAC" + [TABLE] + "ILITY TERMS…".
  Repair by deleting fragments (keep the trailing `\n`), re-read, rebuild.
- `deleteContentRange` CANNOT delete a range ending at a table boundary (paragraph break adjacent
  to table): "Invalid deletion range. Cannot delete the requested range." Delete text only, stop
  BEFORE the `\n` (endIndex = text_end).
- Remove a whole table row-by-row from the LAST row down: `deleteTableRow` with rowIndex rows-1..0.
- `insertText` with "" fails: "Insert text requests must specify text to insert." Model empty
  cells as None and skip.

## Bullets / numbering artifacts
- docx conversion brings auto-numbered lists ("1."/"2." glyphs). Remove with `deleteParagraphBullets`
  (range=paragraphs) — NOT `updateParagraphStyle` with a `bullet` field (doesn't exist → 400).

## Name/run-boundary trap
- Replace "NISHANTH"→"NISHANT" with delete+insert can leave a stray run ("H RANKA") because the
  original text is split across runs. After replace, re-read the paragraph FULL TEXT, delete
  leftover chars, re-insert missing spaces. Verify end-to-end text, not just the styled range.

## updateTextStyle / color pitfalls (verified Aug 2026)
- `updateTextStyle` CANNOT set `weightedFontFamily` — 400 "Unknown name \"weightedFontFamily\" ... Cannot find field." Font is not settable per-run via the API; inserted text inherits the run/paragraph style at the insertion point (e.g. Bookman Old Style in the BM MOU). Set `foregroundColor` only, with `fields: "foregroundColor"`.
- Reads OMIT zero RGB components: a blue run returns `{"foregroundColor": {"color": {"rgbColor": {"blue": 1}}}}` — red/green keys are absent, not 0. Blue-audit must (a) only count runs where `foregroundColor` is explicitly present, and (b) use `.get('red',0)==0 and .get('green',0)==0 and .get('blue',1)==1`. Using naive `red==0 and green==0` on missing keys, or defaulting missing blue to 1 on uncolored runs, produces garbage (0% or ~100%).
- Renumbering clauses in place: equal-length `deleteContentRange(start, start+3)` + `insertText(start, "7.3")` nets ZERO index shift, so subsequent indices in the same batch stay valid — no descending-order or running-offset bookkeeping needed. Insert the new clause at the target paragraph's startIndex, then style the inserted range.
- BOLD-INHERITANCE TRAP when inserting before a bold heading: inserting at a heading paragraph's startIndex (e.g. before "V - CONDITION PRECEDENT") makes the inserted text inherit the heading's BOLD run style. The style request must clear it: `updateTextStyle` with `{"foregroundColor": {...blue}, "bold": false}` and `fields: "foregroundColor,bold"`. Without `bold:false` the new clause shows up bold. (Verified 2026-08-07 Doddamarali MOU — both new clauses inserted before bold part headings.)
- Multi-insert + renumber batch recipe (verified 2026-08-07): to add clause N.10 after 4.9 and a new 7.4 before Force Majeure (renumbering it to 7.5), index sequentially in ONE batch: insert1 at orig_pos1 (len L1) → insert2 at orig_pos2 + L1 → renumber (delete+insert, equal length) at orig_pos2 + L1 + L2 → style insert1 [orig_pos1, +L1), insert2 [orig_pos2+L1, +L2), renumber [+3). Insert text must end with `\n` so it forms its own paragraph; the following paragraph stays intact.

## Verification checklist
1. Structured read of table: print each row's cells; every cell must have its own text.
2. Export plain text: `drive.files().export(fileId=..., mimeType='text/plain')` — ground truth. NOTE: export returns BYTES — `.decode('utf-8')` before `.find()`/string ops (TypeError: argument should be integer or bytes-like object otherwise).
3. Blue audit (correct accessor) — report % blue in summary.

## Worked example (Anvi Consultancy MOU, 06-Aug-2026)
- Source: Gmail thread "Proposal Progress and Mandate request" (msg 19fd205dd9db9dfd, revised MOU).
- Delivery terms came from Anil's EMAIL (10.50–12.50% rate, 30 working days, PG = Nishant only,
  fee on disbursement, 10-doc checklist); the MOU attachment itself lacked them → rewrite WHEREAS.
- Final doc: `1MYeheeeHH2H_do-RFsqe_G8vgMhsm1JRY4mySugsgtE` ("MOU DRA Ranka Holdings - Anvi
  Consultancy - REDLINED (06-Aug-2026)") in DRA Temp folder. Table 6x7 = Project | Location |
  Facility/Loan Type | Quantum (Rs Cr) | Interest Rate | Processing Fee | Timeline, TOTAL row 82.00,
  1.5%+GST, 30 working days.
