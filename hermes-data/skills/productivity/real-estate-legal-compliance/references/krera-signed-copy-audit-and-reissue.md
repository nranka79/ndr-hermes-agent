# K-RERA QU Signed-Copy Audit & Re-Issue Loop

Verified 2026-10-10 on Ranka Amber Q2 FY 2026-27. Companion to
`krera-qu-forms-html-replica.md` (build) and `krera-quarterly-update-filing.md`
(Google-Doc template route). Use when the professionals (CA / architect / engineer)
have SIGNED the QU forms and returned PDFs — NDR then wants (a) a form-wise audit of
what data is still missing in the signed copies, and (b) the re-issue workflow ("you
signed this earlier but X was missing — here are new PDFs, print on your letterhead,
sign, send back").

## Where the signed copies live

NDR files them back into the same folder as the source templates:
`RANKA Amber - Scanned Documents for RERA Approval` (`1CdySY2wMfAYrQ2LrT3l6zF1tXE2-iVdM`),
named `YYYYMMDD_<Project>_K-RERA_Form<n>_..._Signed_Q2_2026-27.pdf`. Actual set (Oct 2026):
Form-6 Engineer signed 08-10, Form-4 CA signed 09-10, Form-5 Architect signed 10-10.
Search `name contains 'Signed'` + `name contains 'Ranka'` in one gws_drive_list call.

## The audit — read each signed copy and report form-wise gaps

1. **Probe the text layer first** — `pymupdf` per page. In the Oct-2026 set, Form-5 came back
   WITH text (the architect's office printed from our derive), while Form-4 and Form-6 were
   scans (empty text). Render those at 300 dpi → tesseract `--psm 6` per page; the signed
   copy's letterhead is the professional's own (Yogesh T Gandhi & Associates / Finding Form
   Design Studio / SLVS) — that OCR block doubles as the source for their real contact data.
2. **Form-wise gap list, in the exact shape NDR will forward.** Lead each form with the
   blanks, then the date defect, then any professional-added note. The Oct-2026 result:
   - **Form-4 (CA, signed):** missing item 4 (% completion per architect cert — fill **12.29%**,
     NOT the originally-instructed 20%; see the reconciliation rule below),
     the whole ASR chain (rate line, Annexure A Unit Consideration column, page-6 rows
     3(ii)/4/5), dates mis-dated 05-10-2026 (must read 30-09-2026). CA *had* filled UDIN,
     email, website=NA, and his own note "cost incurred Rs 70,00,000 and WIP as per ledger
     Rs 1,39,03,550" — flag that WIP note as a difference vs NDR's 70L yardstick.
   - **Form-5 (Architect, signed):** site supervisor blank, site-inspection date blank,
     date 05-10-2026 vs quarter-end 30-09-2026. Everything else present.
   - **Form-6 (Engineer, signed):** QS blank, engineer email blank (fill info@slvs.in),
     table A/B "Work done in percentage" rows not legible from the scan (verify the printed
     copy), date 05-10-2026 vs 30-09-2026.
3. **Never trust OCR on dense table rows from a single pass.** The signed Form-6 Table-A/B
   rows came back as garbage (`Lis a i A`, `Pa`) at one crop scale and cleanly (`Rs.
   4,99,75,601`, `Rs. 70,00,000`) at full-page 300 dpi. Whole-page tesseract beat cropped
   sub-regions repeatedly this session — crop only after the whole page is read, and use the
   full-page numbers as truth. `vision_analyze` on the full rendered page is the tiebreaker
   for number presence vs absence.

## The re-issue round

- NDR's message template: "you signed this earlier but this data was missing — these are the
  new PDFs, print on your letterhead, sign and send back."
- **Strip the K-RERA Kannada letterhead bands from the re-issue PDFs.** The professionals
  print on THEIR letterhead, so pages 1/8 of Form-4 and the header rows of 5/6 must not carry
  the authority's band. Rebuild without the band crops (keep `@page A4`, exact pagination),
  regenerate PDFs via weasyprint, and confirm page counts unchanged (4/4/8).
- Ship the **already-corrected** build, not a copy of what they signed: dates=quarter-end,
  site supervisor=Anbarasan M, QS=Kantesh B G, engineer email/website=info@slvs.in /
  www.slvs.in, CA website=NA, architect %=**12.29** — NOT the instructed 20% (see the
  reconciliation rule below; NDR correction 2026-10-12).
- **UDIN cannot be pre-filled.** It is an 18-digit ICAI number the CA generates online at the
  moment of signing (date + serial; verifiable on ICAI's UDIN portal). Form-4 makes it
  mandatory (form note 1). Tell NDR it only exists at signing — the new Form-4 leaves it for
  the CA, who will issue a fresh UDIN.

## Cross-form percentage reconciliation — MANDATORY (NDR correction 2026-10-12)

**NDR's rule after the 20%-vs-12.29% incident: "we were supposed to check and eliminate
all discrepancies between the forms."** Before any QPR pack goes to a signer, reconcile the
completion percentages across all three certificates — they are compared side-by-side by
KRERA reviewers and buyers alike:

| Figure | Where | Value (Ranka Amber Q2) |
|---|---|---|
| Work done % (cost-based) | Form-6 Engineer, Tables A+B | **12.29%** = ₹70,00,000 ÷ ₹5,69,75,601 |
| Stage-wise % (physical) | Form-5 Architect, Table A | Excavation 100%, Basements Nil, Stilt 100%, Superstructure 4 slabs **0%**, all downstream 0% |
| "% as per Project Architect's Certificate" | Form-4 CA, item 4 | was **20%** (an instructed estimate — WRONG; architect's own cert never states 20%) |
| CA's own % (cost-based) | Form-4 CA, item 7 | 4.95% = ₹70,00,000 ÷ ₹14,13,81,676 (project incl. land) |

**Why 20% was wrong:** Form-4 item 4 must quote the ARCHITECT's figure. The architect's
signed Form-5 carries no overall %; its stage table (superstructure at 0%) implies ~12%,
which matches the engineer's cost-based 12.29% — not 20%. An instructed estimate that
contradicts both other certificates is a reviewer-visible discrepancy.

**The fix (agreed 2026-10-12): align Form-4 item 4 to the engineer's cost-based 12.29%**
(or get the architect to explicitly certify an overall % on Form-5). Note the mechanic:
Form-4 item 8 = Total Estimated Cost × **lower of item 4 & item 7**, so item 4 = 12.29%
still leaves item 7 = 4.95% governing the withdrawal (₹70,00,000) — the withdrawal figure
does not change; only the middle rows align. Also note Form-4's 20% line originated as an
NDR dictation ("we can just put it at 20 percent") — treat ALL dictated percentages as
suspect until reconciled, even when NDR supplied them.

**Final form of the reconciliation (2026-10-12/13, NDR dictated 12.36% and was WRONG):**
when NDR says "put 12.36% as per the Engineer's Certificate", verify the figure against the
engineer's actual certificate before writing it — the engineer cert (and the signed copy)
carries **12.29%** (₹70,00,000 ÷ ₹5,69,75,601 = 12.285%). 12.36% does not reconcile to any
base on file; writing it would have re-created the exact discrepancy being eliminated.
Use the source-verified 12.29%, and tell NDR plainly "you dictated 12.36 but the engineer
cert says 12.29; if you have a 12.36 from another base, tell me where and I'll change all
three". Relabel Form-4 item 4's parenthetical from "(as per Project Architect's
Certificate)" to "(as per Engineer's Certificate)" so the reference matches what is quoted.

## Resolved identities (2026-10-12) — engineer gap CLOSED

- **Engineer is Loganathan M** (SLVS, BCCL/BL-3.6/E-0293/24-25). NDR confirmed: S. Vinay
  Prasad was the original pre-registration Form-3 engineer, but they had to CHANGE because
  KRERA needed a Karnataka-registered engineer; Loganathan signed subsequently. Form-6 (and
  the current QU builds) name Loganathan — correct.
- **info@slvs.in = the ENGINEER's firm email (SLVS Design Consultants LLP), NOT the
  quantity surveyor's.** NDR corrected this explicitly. The QS line on Form-6 carries
  **Kantesh B G** by name only (no email field); his email is kanteshbg@draas.com.
- **Site Supervisor on Form-5: Anbarasan M (Anbu)** — taken from the org structure filed
  with KRERA (Level 3 Project Team: "Project Manager / Site Supervisor Anbarasan M").
- **Site Inspection date on Form-5: 30-09-2026** (quarter end; NDR: "inspection date like i
  said 30th september").
- Both are now filled in the v2 builds; do not leave blank in re-issue PDFs.

## ASR / Ready Reckoner rate — resolved (2026-10-12)

Form-4 Annexure A needs the locality Ready Reckoner rate (Rs/sq.m) as on the certificate
date; it drives item 3(ii), items 4-5, and the Unit Consideration column. Source of truth:
**the Sub-Registrar's certified guidance-value letter already in the project RERA folder**
(`20260622_RankaAmber_Guidance_Value_Sub_registrar.pdf`) — it is a certified copy of the very
ASR table. Official portal: kaveri.karnataka.gov.in; the operative ASR for Bengaluru Urban is
Gazette No. 461 dated 30-09-2023 (effective 01-10-2023; the 2025-26 hike was announced but
not gazetted as of Oct-2026). For Ranka Amber (D'Silva Layout, Pattandur Agrahara):
**Sl. 633 De Silva Layout = Rs 58,000/sq.m** (neighbours: Patandur Agrahara BDA 65,000;
State Highway to White Field road 75,000; Upkar/Prithvi 58,000; Prestige Palms 72,380).
Chain: 2,165.00 sq.m unsold × 58,000 = **Rs 12,55,70,000** for items 3(ii)/4; item 5 =
100% deposit rule (12.55 Cr < 13.43 Cr). Individual unit consideration = unit carpet area
(sq.m) × 58,000 with Indian-format amounts (68,86,340 etc). A per-unit cross-check: sum of
A×B must equal 12,55,70,000.

## Replacing a corrected signed copy on Drive (2026-10-12)

When NDR uploads a corrected/signed PDF (e.g. architect's re-signed Form-5) and says
"replace what we have on drive": verify the upload first (pdfinfo page count, text layer vs
scan, OCR the data block — date = quarter-end, RERA no, no blanks, signature/seal present
via vision on the signature page), then upload to the SAME folder with the SAME naming
convention, verify byte-identical read-back (sha256), then DELETE the old version and
confirm the folder holds exactly one copy. None of "replace" = upload alongside the old.

## Plinth-status propagation — one story across ALL three forms (2026-10-13)

The physical-progress story must be identical in Form-5 (architect), Form-6 (engineer) AND
consistent with Form-4 (CA is financial, so it is silent on plinth — no conflict). When the
plinth is NOT completed, every form that states progress must say so in the same words:

- **Form-6 (engineer):** explicit certification clause — "The plinth of the building has
  NOT been completed as on the date of this certificate" — plus Table C row 2 reading
  `0 (Nil) – Plinth not completed`.
- **Form-5 (architect):** mirror it with its own clause — "I further certify that as on the
  date of this certificate … the plinth of the building has NOT been completed and the
  plinth work is still pending. All the footings and the RCC columns of the building have
  been raised as per the sanctioned drawings." Table A row 2 = `0 (Nil) – Plinth not
  completed` (same wording as Form-6's Table C).
- It reads oddly alongside "Stilt Floor 1 (One) – 100%"; NDR accepts this (stilt/structure
  work can read 100% while plinth is pending) but flag it so the signers aren't surprised.
- **Do NOT invent the percentage story.** NDR's own recollection of the architect cert was
  briefly "architect says plinth complete" — it actually says 0 (Nil). Verify each form's
  current text by reading the builds, never by memory, before editing.

## Sartak review-gate — the email flow BEFORE sign-off emails (2026-10-12/13)

NDR's gate: after forms are updated, a review email goes to **Sartak (admin3.blr@draas.com,
cc Prakash psingh@draas.com)** with all three DRA Content links (Form 4/5/6), asking him to
review, confirm the data is now clear/consistent, and raise any remaining questions. Only
after his confirmation do the per-professional sign-off emails go out. Draft it as a plain
text email with the three artifact URLs and the key-points summary (the % reconciliation +
plinth status + date consistency). Never send — DRAFTS ONLY, NDR presses send.

## Signer routing (who signs what, and via whom) — Oct 2026

| Form | Signer | Email routing (Oct-2026) | Notes |
|---|---|---|---|
| Form-4 | CA Yogesh T. Gandhi, M.No. 215599, Y T Gandhi & Associates | To gandhiyogesh@yahoo.com; cc Eshwari Chamundeshwari (echamundeshwari@draas.com) + Sartak + Prakash | UDIN generated at signing |
| Form-5 | Ar. Anjali Mandhyan, CA/2018/100260, Finding Form Design Studio | To Bhuvanesh (bk@fnw.homes) + Anjali (anjali.mandhyan07@gmail.com); cc Sartak + Prakash | |
| Form-6 | Engineer Loganathan M, BCCL/BL-3.6/E-0293/24-25, SLVS | To info@slvs.in (the ENGINEER's firm — see identity notes); cc Anbu (pm2.blr@draas.com) + Sartak | engineer-change question: filed Form-3 carried S. Vinay Prasad |

Drafts always CC Prakash + Bharat (why: Prakash runs the quarterly upload; Bharat must learn
it). NDR shares the artifact links with Roshni — grant her viewer access too (rnr@draas.com).
Bharat's address for grants/CC: sales1.blr@draas.com. And per house
rule: **DRAFTS ONLY — never send; NDR presses send.**

## Pitfalls

- Search `name contains 'RANKA Amber'` returns the whole project tree; the signed set is the
  `..._Signed_...` files in the Approvals/Scanned folder — don't confuse the `_Letterhead_`
  Google Docs Prakash prepared (those are templates, not signed copies).
- The first "form 4" hit on Drive can be a stale/other-purpose folder; confirm by content
  (8 pages, Kannada band, CA block) before treating it as the current build.
- Bytes: after re-uploading standalone HTML to Drive, read back `size` and compare to the
  local file — an in-place `drive_update` can silently produce a different file; the published
  DRA Content payload must equal the sum of its source files (verify via content-api:8650
  version endpoint, see the replica reference).