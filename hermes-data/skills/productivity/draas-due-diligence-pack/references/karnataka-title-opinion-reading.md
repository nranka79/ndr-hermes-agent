# Reading a Scanned Karnataka Title Opinion (Preliminary Title Report)

Worked example: 03-Sep-2026 email from B. R. Krishna (BRK Law / Jayanth Pattanshetti
Associates LLP) to ndr@draas.com re: **Gunjur Sy. No. 40 (18A 21G), Tubagere Hobli,
Doddaballapur** — two PDF attachments: `Scanned_Preliminary_Title_Report_3_9_26.pdf`
(24 pp) + `Scanned_Bill_99_dt_3_9_26.pdf` (professional fee bill). The user asks:
"what does the opinion say, what are the caveats, is it a clear title opinion?"

## Pipeline (proven)

1. **Find the email + attachments** — Gmail `messages().list` with
   `"title opinion" survey 40` / `from:(firm) "sy. 40"` style queries, then
   `attachments().get()` each PDF. Handle large scans: the report was 7.3 MB / 24 pp.
2. **Render every page** — `pdftoppm -r 150 -png report.pdf pg` → 24 PNGs.
   `pdfinfo` first for page count.
3. **Vision-read page-by-page with targeted questions** — one
   `vision_analyze` per page, question = "Read ALL text exactly, what section is
   this?" This is a SCANNED document; do not rely on pdftotext (empty for scans).
4. **Log the narrative per page** as you go: property description → title
   discussion per parcel → revenue/mutation records → endorsements → EC/CC →
   the formal Opinion section → Annexures. Stop when the Annexures begin (they are
   the evidence list, not new opinion).

## Structural map of a Pattanshetti/BRK title report

- **Continuation Sheets** numbered 1..N (not PDF pages — sheet no = page - 1).
- **Property description** — sy no, extent, village/hobli/taluk, boundaries,
  kharab note (e.g. "no kharab land" is a positive finding).
- **Discussion on Title** (numbered 2.x) — per-parcel chains. Often TWO or more
  chains feeding one owner (e.g. 9A 21G grant line + 9A sale line). Read each on
  its own merits — they may carry different caveats.
- **Document chain evidence** — every deed cited with registration details
  (Doc No., Book I, Volume, Pages, Sub-Registrar office) and "evidenced from
  Document No. XX". These XX numbers map to the annexure list at the end.
- **Revenue Records / Mutations / Inheritance** (4.x) — MR serials, IHC/order
  numbers, khata mutation trail.
- **Endorsements** (7.x) — REVENUE-CRITICAL for grant lands: 48A/77A tenancy
  nil certificate + PTCL (Prohibition of Transfer of Certain Lands) nil
  endorsement. Quote the endorsement numbers verbatim.
- **EC/CC** (8.x) — normally "documents to furnish" flags the GAPS in EC
  coverage (e.g. "furnish EC 1940→2004 and 2023→date" when only 2004→2023 given).
- **Opinion** (9.x) — the operative sentence. Read it VERBATIM and distinguish
  its strength:
  - "X is the absolute owner of …" = ownership finding
  - "valid and marketable title" = strongest available (usually qualified)
  - "may be considered valid and marketable, subject to verification and the
    other qualifications set out in this report" = conditional, NOT clean
- **Annexure A** — "Standard Exceptions to the Title Search" boilerplate
  (encroachments, unregistered claims, post-report matters). Not parcel-specific.
- **Annexure B / document list** — the 20+ "Documents shall be furnished"
  checklist: grant order/grant certificate/caste certificate/upset-price
  receipt, sale certificates, court-case records (plaint/WS/decree/withdrawal
  memo/order sheet), death certs, family trees, gap RTCs, maps (karda, village
  map, hudbast, survey sketch), acquisition/road-widening endorsements, tax
  receipts, public notice, originals.

## Answering "is it a clear title opinion?"

- Collect ALL opinion sentences (there may be one per parcel) + every
  "subject to / qualification / note / shall furnish" phrase.
- The single most common blocker: **original grant order / grant certificate /
  saguvali chit** for grant lands — almost always missing from the client's set.
- Secondary common blockers: EC period gaps, old court-case records
  (e.g. O.S. No. 196/1991), death certificates of pre-2000 khatedars.
- Report honestly: "opinion holds title vested + marketable, but it is
  CONDITIONAL not final — close items X, Y, Z and the firm can upgrade."

## Filing the scanned opinion

- Rename per NDR convention: `YYYYMMDD_SyNo_Description_Firm.pdf`
  (e.g. `20260903_GunjurSy40_PreliminaryTitleReport_JayanthPattanshettiLLP.pdf`).
- Pick the Drive folder by CONTENT: the folder that already holds the source
  documents the opinion cites (RTCs, MRs, sale deeds, ECs, Will) is the right
  home (e.g. "Copy Gunjur-Doddaballapur"), not the generic legal/case folder.
  List folder before upload and verify the source deeds live there.
- Upload both attachments (report AND bill) — bills are part of the matter file;
  extract amount/advance/balance/GST/bank details from the bill page.
- Flag unpaid balances to the user (here: fee ₹9,26,250 − ₹2,03,000 received =
  ₹7,23,250 due) and offer a tracker task.