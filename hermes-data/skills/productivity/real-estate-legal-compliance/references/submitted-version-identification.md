# Identifying WHICH version of a document was actually submitted to an authority

Verified 2026-09-18 on the Ranka Iris BBMP OC-submission as-built drawing question.

## The problem class

NDR asks: *"which one is the file we actually submitted to the department?"* — for an
as-built drawing, a revised plan, a compliance letter, a NOC. Drive holds several
near-identical copies (`x.dwg`, `x_final.dwg`, `x_OCSubmission.dwg`, plus copies
colleagues forwarded). Picking the wrong one and putting it on an outbound email is a
real error, because the authority's record is the thing that matters.

## HARD RULE — Drive timestamps are NOT document dates

`createdTime` / `modifiedTime` in the Drive API record when the *file landed in Drive*,
not when the drawing/document was authored or issued. DRA re-uploads and re-syncs
historical files constantly, so a 2013 sanction can show `createdTime` = 2026.

**Never reason about document chronology from `createdTime`/`modifiedTime`.**
Use instead, in priority order:
1. **The date printed/title-blocked on the document itself** (render page 1 and read it).
2. **The date in the covering email** that transmitted it (`internalDate`, or the date in the body).
3. **The document date encoded in the filename** (`20130902_...`, `20260414_...`).

A file's *name* usually encodes the true date and is the most reliable cheap signal.

## HARD RULE — apply the subject-matter date window BEFORE ranking candidates

This is the correction NDR made in this session, and it is the expensive one to get wrong.

A document tied to a *downstream process* cannot predate that process. So before you
compare candidate files at all, establish the process window and exclude everything
that falls outside it:

- **Rule applied here:** no AutoCAD file relating to the Iris as-built submission could
  predate Q2-2025 (Apr–Jun 2025), because that is when the OC application began. Any
  candidate dated earlier is definitionally disqualified.
- This immediately killed two candidates that *looked* right by filename and custody:
  a `.dwg` emailed Apr-2026 (after the window closed — wrong side), and a set of PDF
  sheets title-blocked **11 JAN 2023** (Studio62-authored, i.e. sanction-era drawings
  recycled, not as-builts).

**State the window out loud before ranking.** Do not skip to "which filename looks best".

## Ranking rule NDR confirmed

When candidates remain and you cannot verify the transmission directly:
**go with the LATER date** — later-dated email or later-dated drawing — where the file is
also explicitly named/held for that submission. NDR's decision here: take
`..._AsBuiltDrawing_OCSubmission.dwg` over the earlier `Iris As Built 11.03.2026.dwg`.

Combine three signals, and say which you used:
1. **Later date** (date on doc > date in transmitting email > date in filename).
2. **Naming** — a file explicitly named for the process (`_OCSubmission`) is the one
   the team treated as the submission copy.
3. **Custody** — held in the liaisoning/sanction folder, with a shortcut in the
   liaison officer's own space.

## Honesty requirement when it is inference

Custody + naming + date is *inference*, not proof. Say so plainly and name the missing
evidence. Here: no email in the mailbox showed the DWG attached to a BBMP submission,
and neither DWG could be opened to compare geometry (no DWG converter; ODA File
Converter's download is behind a browser form).

The definitive artifact to ask for is an **acknowledgement / portal attachment receipt**
from the liaisoning person (Anbu / Bhavik / Piyush). Recommend that as the ask.

## Do not over-claim from a byte-comparison

Two DWGs differing by ~56 KB with different checksums and ~14,366 of ~14,400 internal
string entries shared means "one is a lightly-edited save of the other" — it does NOT
establish which was submitted. Binary `strings` output on compressed DWG/AC1032 files
is noise; do not present it as evidence.

## Related

- `draas-drive-organization` — Drive search/move mechanics, cross-account handling.
