# MOU Drafting — Aggregator / Landowner-Proposal Deals (Doddamarali-LG pattern, Aug 2026)

Companion to `mou-drafting-workflow.md`. Covers the **land-aggregator MOU** variant, where
the First Party is a local aggregator (who may himself OWN lands inside the deal) procuring
multiple landowners' parcels in phases for DRA's outright purchase.

## Structural template
Base = Bestamanahalli MOU v3 Google Doc (ID `13n53Ouoq2miq1FGwfFHROwj_GqcJLcUdYxluMAE_eLs`).
Parts I–VIII + Annexures A–D. Build with python-docx → upload as Google Doc → share to
psingh@draas.com (owner) → verify by Drive export to text/plain.

## Deal anatomy that worked (user-approved shape)
- **Recitals**: lands per RTC summary Annexure; FP is aggregator AND owner/co-owner of
  certain survey numbers; total ~70A incl. ~7A JDA for plotted development; FP organizes
  direct meetings with landowners for consent incl. ALL family members/legal heirs.
- **Part IV Consideration**: flat ₹/acre for TOTAL land, pre-condition Phase 1 done in 60
  days; Phase 1 = ~10A contiguous block abutting the access road; Phase 2+ in ~20A lots at
  same ₹/acre; **4.4 JDA Lands**: SECOND PARTY directly executes/signs JDA Definitive
  Documents with landowners on terms FAVORABLE to Second Party; FP procures landowners to
  those terms; **4.5 overall timeline ~12 months + 3 months grace**.
- **Part V Condition Precedent — TRIMMED per user**: legal clearance (EC + no-encumbrance),
  up-to-date revenue records/RTC/khata/conversion/tax receipts, registered title deeds +
  title-flow/chain-of-title + survey docs, landowner consent meetings (incl. heirs), third-party
  consents. **User explicitly removed ED / Income Tax / CBI / DRI clauses** from CP.
- **NO default clause**: user: "default clause is not required" — delete old 7.3
  (mutual-termination + 18% default interest). Keep CP-failure exit: terminate + refund
  advances, NO interest penalty. Renumber Force Majeure → 7.3; Part VII = "TIMELINE".
- **6.1 reps** mirror the structure: FP authority (own lands + procuring balance),
  direct-meeting consent duty, JDA-direct-signing duty, indemnity.

## User preferences (encode in every MOU)
- CP scope = legal + revenue + survey + title/title-flow docs ONLY. No enforcement-agency
  (ED/IT/CBI/DRI) conditions unless explicitly requested.
- No default/penalty clause by default.
- When aggregator owns parcels, say so in party block + recitals + reps (his own rows:
  e.g. G.N. Venugopal 18-3; G.V. Vivek 10-3, 11-3, 13-3) and aggregate his lands + others
  in the same phases.

## Tech gotchas (re-verified this session)
- **Google Doc content can live in a TABLE** (BM MOU v3 body is a full-width table) — the
  Docs API `paragraph` extraction returns empty; use `drive.files().export(fileId,
  mimeType='text/plain')` to read full text.
- **Update-in-place keeps the link**: `drive.files().update(fileId, media_body=docx,
  fields='id,name,mimeType,webViewLink')` re-imports the DOCX into the SAME Google Doc ID.
  Verify afterwards by re-exporting text/plain and asserting clause presence AND absence
  (e.g. "Enforcement Directorate" not in text).
- **uv venvs have no pip module**: `uv venv` then `uv pip install --python <venv>/bin/python python-docx`.
- **/tmp is wiped between turns**: keep the build script + sheet JSON in the SAME session
  turn as the build; re-fetch sheet data (execute_code → JSON) rather than trusting old dumps.
- Sheets → annexure tables: dump `values().get` to JSON, build script reads JSON, adds rows
  with 8.5pt font, skips non-digit Sl No rows, appends SUBTOTAL/GRAND TOTAL bold rows.
- Deliverable naming: `YYYYMMDD MOU_<Project>_<Area>`; deliver link in a plain code block
  (Telegram breaks URLs) + "search Drive by filename" fallback.
