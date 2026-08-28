# MOU / Consultant-Fee Clause Revision — NDR's Workflow & Preferences

Session-proven workflow for revising DRA Realty / DRA Ranka Holdings MOUs with finance consultants (e.g. Anvi Consultancy, Anil Kumar P) — captured Aug 2026.

## NDR's hard preferences (do not re-derive)

1. **Edit the Google Doc directly — no PDF unless asked.** NDR reviews the Doc himself and makes the PDF for signing. Do NOT produce a PDF as part of clause revision ("don't even worry about creating a PDF... I'll review it and I'll make the PDF myself").
2. **All text must remain black.** No blue/redline/colored markup in the working Google Doc. The redlined working copy (blue text) is a separate file, never the live one.
3. **No open-ended contracts.** Fee/back-out provisions need a FIXED NUMBER, even as a placeholder the counterparty can negotiate later. "The contract should not be open ended... I want a number there, that's all." E.g. back-out fee = one-time flat Rs. 30,00,000 + GST (placeholder), not "fee calculated on the sanctioned amount".
4. **MOU is non-binding; only the fee-protection clause binds** (Clause 5). Preserve that structure.

## Clause-revision workflow (what worked)

1. Read the full Google Doc via Docs API (`build_service('docs','v1', service_name='google-draas')`), print every paragraph with its `startIndex`/`endIndex` — indices are needed for structural edits.
2. Walk the user clause-by-clause in plain language: what each ambiguous clause means, why it's weak, proposed rewording. NDR decides; you execute.
3. Apply edits with ONE `documents().batchUpdate()`:
   - Structural changes (remove old clause block, insert replacement/new clause) via `deleteContentRange` + `insertText` using byte indices, ordered HIGHEST index → LOWEST (so earlier ops don't invalidate later indices).
   - Text-only rewrites via `replaceAllText` — match WITHOUT leading indentation spaces (indented list items store spaces in the text run; a match string with wrong leading whitespace silently returns `{}` = zero matches).
4. Verify: re-read the doc; assert each intended change (old text gone, new text present) with a boolean checklist; assert zero non-black text runs.

## Domain notes for this MOU class (finance-consultant fee MOUs)

- **Construction finance vs term loan exit:** CF is short-term (~2-3 yr, higher rate, tranched vs progress); a "term loan exit" = refinancing the CF with a long-term amortising term loan (takeout funding) when the asset completes / CF matures. Worth making a standalone clause (e.g. 2.5) rather than burying it in the project list; explicitly state it's covered by the existing fee (no separate charge).
- **Commitment vs indicative target:** "Minimum aggregate sanction Rs. 90 Cr" was made an explicit consultant COMMITMENT; Rs. 30 Cr of it available for immediate drawdown by DRA Realty (any project — Uday/Amber/North Star), not personally by NDR.
- **Back-out fee:** flat one-time amount (Rs. 30L placeholder) payable if client withdraws post-sanction for ANY reason, in lieu of percentage fee.
- **Arbitration deadlock fallback:** sole arbitrator mutually appointed; failing agreement, partner/senior lawyer nominated by Indus Law or Fox Mandal; neither party may dispute the appointment.
- **MOTD:** spell out as "MOTD (Memorandum of Title Deeds)" at least once (appears in fee/charges clauses).
