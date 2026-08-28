# Lawyer Requisition Checklist → Supplied vs Pending Tracking

Class of task: lawyer (e.g. BRK Law / Pattanshetti) sends a "requisition list" of
title-due-diligence documents for a land parcel; later claims "most documents
still not furnished" citing a list sent months earlier. User asks: find that
checklist, figure out what's already supplied, and produce **just the pending
list**.

## Workflow

1. **Find the checklist email.** Search Gmail (google-draas; also ndr@drahomes.in
   legacy address — old threads live there):
   - `from:krishna@brklaw.in` / `from:pattanshetti.com` (or the firm's associate,
     e.g. `ananya.s@pattanshetti.in`)
   - Subject terms: `requisition list`, `checklist`, `Gunjur`, `title`, `due diligence`
   - The firm typically sends TWO lists: original (e.g. 28-10-2025) and an
     *Additional Requisition List* (e.g. 06-11-2025) with color-coded status.
   - The checklist is an **attachment** (.doc/.docx), not inline text. Pull it via
     `users().messages().attachments().get()` (base64 urlsafe decode).

2. **Handle the .doc-that-is-actually-.docx gotcha.** Law-firm .doc files are
   frequently ZIP/docx in disguise. Check magic bytes: `PK\x03\x04` = docx.
   Extract with `zipfile` + regex on `word/document.xml`:
   `<w:p...>.*?</w:p>` split, then `<w:t[^>]*>(.*?)</w:t>` per paragraph,
   `html.unescape` and strip tags. (catdoc/antiword/libreoffice may be absent —
   pure-stdlib route always works.)

3. **Read the color legend.** Additional lists use font colors as status:
   - **Black** = asked earlier (still pending)
   - **Blue** = received (`w:color w:val="0070C0"` in rPr, often text "Received",
     sometimes inline like "(b) & (c) Received", "Received MR Nos. ...")
   - **Red** = additional documents sought (new asks, e.g. auction records)
   Capture received annotations line-by-line while extracting.

4. **Cross-check what's supplied beyond the lawyer's ticks.** Look at:
   - Recent emails to the lawyer (PTCL/48A/77A endorsement emails, RTC correction
     order, etc.)
   - The Drive folder of legal docs for the parcel (may contain documents never
     formally marked "Received" by the lawyer — flag these as
     "in folder, not yet ticked", don't silently count them as supplied).

5. **Deliverable = pending list only** (user asked "give me just a list of the
   pending documents"). Structure:
   - One short "Already supplied ✓" section (endorsements, received-marked items)
   - Pending grouped by the lawyer's own section headings (Title / Revenue &
     Mutations / Survey / Endorsements / Conversion / ECs / Clarifications /
     Mortgages / Tax / Cases / Originals)
   - **Clarifications** are statements, not documents — call them out separately
   - Heads-up at the end: which pending items actually exist in the Drive folder
     un-ticked (cheap to resolve by asking the lawyer to confirm), vs genuinely
     new work (grant files, auction files, authority endorsements, ECs).

## Pitfalls

- The *older* list (28-10-2025) is superseded by the Additional list (06-11-2025);
  use the additional list as the source of truth for pending status.
- "Received" annotations may be partial (e.g. "Received MR Nos. 08/1993-94 and
  06/2002-03" — the 10/2019-20 extract is still pending).
- Family trees / caste certificates / tax receipts often exist in the Drive
  folder but were never marked received — do not claim them pending without
  noting they're already filed.
- If a checklist ref (e.g. JMP/AS/158/25) appears, keep it — the lawyer will
  quote it back.
