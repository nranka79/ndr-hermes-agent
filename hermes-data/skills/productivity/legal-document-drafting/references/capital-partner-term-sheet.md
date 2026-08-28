# Term Sheets for Capital-Partner / JD Deals (DRAAS → external Investor)

When NDR is negotiating a capital-partner / joint-development deal (e.g. Jiraaf Capital on
Ranka Oasis, and the prior 2023 precedent / 5A proposal), he often wants TWO documents:
a detailed **full draft** term sheet AND a clean **simple "key terms" term sheet** where
the commercial terms are presented in **tabular format, categorized by section**, with all
caveats pushed to a fine-print section.

## Why this matters / when to use
The "simple key-terms" tabular sheet is the shareable, counterparty-facing artifact. The
user explicitly asked: *"simple term sheet where just the key terms are captured, all the
caveats aside can be in fine print, but the key terms presented in a tabular format,
categorized by the different sections, whether it is sales price, whether it is sharing of
area or whatever."*

## Canonical structure (proven on Ranka Oasis × Jiraaf, 25-08-2026)
- **Title block**: `TERM SHEET` + subtitle `<Project> (<location>) · <DRA entity> × <Investor>`
- **Preamble**: 1 short paragraph — commercial/JD participation, NOT a land sale.
- **Section headings** (bold bars), each followed by a **two-column table**:
  `Term | Value / Provision`. Keep rows terse — one term per row.
- Section list that works for JD/capital-partner deals:
  1. Parties & Roles
  2. Land, Project & Scope (incl. exactly which parcels are IN / which are EXCLUDED)
  3. Economic Consideration (₹/acre × extent → gross; goodwill/net; payment structure)
  4. Investor's Share / Area Sharing (%, FSI basis, illustrative sqft)
  5. Sales & Marketing Schedule (the quarterly % liquidation model of the investor's inventory)
  6. Pass-Throughs, Clubhouse & Upgrades (what accrues to developer, not shared)
  7. Pricing & Realisation (price floor vs average-realisation aim; uplift/upside trigger)
  8. Tax Neutrality & Structuring (structuring consultant)
  9. Project / Construction Finance (security limited to developer's own share)
  10. Legal Diligence, Closing & Lapse
  11. Delivery, Possession & RERA Protections
  12. Profit Share (investor participates in project net profit, land-revenue excluded)
- **Caveats / Fine Print** section (prose, small, separate) — lists open items, "?" placeholders,
  and boilerplate deliberately deferred to definitive agreements.
- **Acceptance** block — two-column signature table (DRA side | Investor side).

## Drafting workflow (two-stage model routing)
NDR's preferred split for these:
1. **Content generation / thinking** → a HIGH-END model via **OpenRouter** (he asked for
   "GPT 5.5 and above"). Feed it the settled commercial terms + the exact structure above;
   ask for clean markdown pipe tables (Term | Value) per section. It produces the draft content.
2. **Google Doc construction** → the main (deepseek) model, via **HTML import**
   (google-doc-formatting-template skill) so tables + dark-blue header bars render cleanly
   in one shot. Markdown tables do NOT carry through to Docs; HTML `<table>` import does.

Keep the simple sheet **lean/commercial only** — mirror NDR's standing rule to exclude legal
boilerplate (default/termination, dispute resolution, indemnities, escrow/ring-fencing,
force majeure, conditions precedent, nomination right) from the term sheet itself; push them
to a single fine-print caveat line ("definitive agreements will carry these"). Open items are
marked explicitly with a **?** so they cannot be missed before definitive docs.

## Naming convention (NDR's folder convention — use for ALL new versions AND renames)
`<Project> × <Partner> — <DocType> <version> (<DD-MM-YYYY>)`
- Example: `Ranka Oasis × Jiraaf — Term Sheet (Key Terms) v1.0 (25-08-2026)`
- When creating a simple sheet alongside the full draft, distinguish them:
  `… — Term Sheet (Key Terms) v1.0` vs `… — Term Sheet (Full Draft) v0.4`.
- Apply the same convention to Q&A / notes docs: `… — Proposal Notes Q&A v3 (25-08-2026)`.
- When the user says "rename the file(s) per my naming convention", rename BOTH the new doc
  AND the pre-existing detailed doc so the folder stays consistent.

## Project where this was done
- Ranka Oasis (Sevaganapalli, Hosur) × Jiraaf Capital — Balaji Land Drive folder.
  Deals live in folder `Balaji Land` (id `1pKvhDHDFvMNJsEnveaRl-VGJ4tAuAKog`).
