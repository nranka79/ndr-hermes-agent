# TNRERA Annexure 'A' — Agreement for Sale (Rule 9 model), Ranka Udaya variant

Verified 2026-10-12: **Plot 31 → Rajani Jaisimha Rao** Agreement for Sale, built from the
TNRERA model PDF the user sent (Annexure 'A', "[See Rule 9]" of the TN RERA Rules 2017) +
the Plot 36 Absolute Sale Deed as the party/title-chain source.

## Trigger
- "change this to an agreement of sale" / "we need an agreement for sale" for a plotted
  project, where the buyer **has already paid the full amount** and sale-deed registration is
  deferred.
- The user may drop a TNRERA Annexure 'A' PDF into chat ("consider this as reference too") —
  that PDF **IS the structural model**, not the sale deed.

## Which document and why
- This is a **promoter↔allottee contract BEFORE sale-deed registration** (RERA model form),
  NOT an absolute sale deed. Do NOT copy the sale deed's clause order (transfer/possession/
  conveyance). Follow the model: Parties (Promoter / Allottee with OR-branches), Recitals
  A–I, ~20 numbered clauses, Schedule A (total land), B (plot agreed to be conveyed),
  C (payment schedule), execution block.
- Vendor block stays the same as the latest sale deed in the same project (e.g. DRA Thindlu
  Land Partners via its partners), but the labels are "PROMOTER" / "ALLOTTEE".

## Key clause engineering
- **Full-payment clause is the user's explicit ask**: "he has made the payment of ₹X already —
  we have to mention full money has been received by the promoter or developer here."
  Insert a dedicated clause right after the encumbrance clause (e.g. Clause 3
  "FULL AND FINAL PAYMENT"): entire consideration already paid; promoter acknowledges full
  and final receipt; nothing outstanding; promoter will execute and register the Sale Deed
  within ~90 days of the allottee's request.
- Clause "registration on receipt of all monies" must reflect that monies are **already
  received** → registration happens on request, not on payment completion.
- Amount = what the user states, NOT the master-sheet rate. If it differs from the standard
  ₹/sft (e.g. ₹33L vs ₹3,500/sft ⇒ ~₹2,713/sft), **flag the implied rate** in the confirm
  list — do not "fix" it silently.
- TDS clause: check the agreement consideration against the ₹50,00,000 Sec 194-IA threshold
  (₹33L ⇒ no TDS).
- Cancellation/default clause: since full payment received, carve out payment default; keep
  refund "in accordance with the Act and Rules".
- Disputes: adjudicating officer under the Act + courts at the project district
  (Krishnagiri for Ranka Udaya).

## Data sources (same as sale-deed update — see plotted-layout-sale-deed-update.md)
- Master sheet `1mtqU51isImvtEmqEIuuqNmeeycV5zMxhjT7tXNiaao8` → plot row (dims, sqm, sft,
  facing). Plot 31: 9.27 × 12.19 m, 112.996 sqm / 1,216.28 sqft, East-facing.
- Title chain + RERA no. (TNRERA/30/LO/0642/2026, 18.02.2026), HNTDA approvals
  (SWP 90/2025 & 38/2025), gift deeds (1634/2025 TANGEDCO, 1632/2025 Panchayat) — carry from
  the latest Absolute Sale Deed draft in the project Title folder.
- Boundaries for an East-facing plot (20–38 row): East = 9M internal road, West = layout
  boundary (Sy 240/2A2), N = next number up, S = next number down (serpentine numbering).

## Extracting buyer KYC from scanned PAN/Aadhaar PDFs
- **pdftotext returns EMPTY on these scans** → render pages with pymupdf (dpi 200–350),
  then `vision_analyze` the PNG.
- **Aadhaar letter may render rotated/mirrored**: try 90° rotations (CW/CCW) and a left-right
  flip; crop the front face (name / father|husband / address / enrollment) and the back face
  ("Government of India" — name / YOB / gender / **full 12-digit Aadhaar number**); for
  tesseract fallback, autocontrast + 3–4× upscale.
- **Reconcile, don't guess.** PAN and Aadhaar frequently disagree: name "RAJANI" vs "Rajan";
  PAN father's name (Tumukuru Seetharamaiah Raghavendra Rao) vs Aadhaar relation
  (W/o Jaisimha Rao). Use PAN for name/DOB/PAN; print the Aadhaar relation the user intends —
  and ALWAYS list the mismatch in the confirm list.
- Age: compute from DOB vs today, birthday may not have passed (24/10/1970 on 12-Oct ⇒
  "aged about 55", turns 56 on the 24th).
- Address on the Aadhaar is low-contrast; cross-read with zoomed crops and flag housenumber
  ambiguities (A2-500 vs A2-603) rather than asserting one.

## Deliverable & reply shape (same cadence as sale-deed update)
- Build .docx with python-docx (Times New Roman 12, justified, numbered clauses with hanging
  indent). Upload BOTH a converted native Google Doc AND raw .docx into the project Title
  folder. Verify the converted gdoc via Docs API contains the key figures
  (name, consideration in figures+words, plot no., PAN, Aadhaar) before handing over.
- Reply: Drive link first → what was built → ⚠️ confirm-before-registration list
  (rate mismatch vs master sheet, parentage/father-vs-husband, boundaries, payment
  particulars, execution date).