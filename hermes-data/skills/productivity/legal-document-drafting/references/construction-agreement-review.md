# Construction Agreement Review — Benchmark Gap Analysis

**When to use:** User asks to review, compare, or improve a construction agreement (villa/apartment) draft for a DRAAS project. Apply this checklist against an industry-standard developer agreement (Prestige, Sobha, Brigade, etc.) as a benchmark.

**For sale deed recitals from source chain documents:** See `references/sale-deed-recitals-from-source-chain.md` in the same skill directory.

## Comparison Methodology

1. **OCR the benchmark agreement** (scanned PDF) — use pdftoppm + vision_analyze per page:
   ```bash
   pdftoppm -png -r 200 /path/to/benchmark.pdf /tmp/pdf_ocr/page
   # Then vision_analyze(image_url="/tmp/pdf_ocr/page-N.png") for each page
   ```
2. **Extract the draft** — use gws_skill_bridge for Google Docs:
   ```python
   from tools.gws_skill_bridge import call as bridge_call
   doc = bridge_call("docs_get", doc_id="...", service_name="google-draas")
   ```
3. **Map clauses side-by-side** — list every clause in the benchmark, check presence/absence/quality in the draft.
4. **Prioritize gaps** — HIGH (commercial/completion risk), MEDIUM (legal ambiguity), LOW (boilerplate).

## 15-Point Gap Analysis Checklist

### HIGH Priority — Commercial & Completion Risk

| # | Clause | What to Check |
|---|--------|---------------|
| 1 | **Payment Default** | Interest rate (benchmark: 15% p.a.), cure notice period (15-21 days), liquidated damages % (benchmark: 15% of construction cost), termination mechanics |
| 2 | **Developer Delay Liability** | Interest rate on amounts paid for delayed possession (benchmark: 9% p.a.), grace period definition, trigger conditions |
| 3 | **Assignment / Transfer Restriction** | No assignment without developer's prior written consent; transfer fee provision |
| 4 | **Payment Schedule (Schedule D)** | Milestone-based: booking → foundation → slab → brickwork → finishing → possession. Must be filled, not blank. |
| 5 | **Specifications Annexure** | Structure, floor/wall/joinery finishes, bathroom fittings, electrical/plumbing specs. Must be substantive, not blank. |

### MEDIUM Priority — Legal Clarity

| # | Clause | What to Check |
|---|--------|---------------|
| 6 | **Force Majeure** | Enumerated events (civil commotion, strikes, Acts of God, govt notifications, court orders, material non-availability). Not just "subject to FM." |
| 7 | **Arbitration (fallback)** | RERA covers limited disputes. Add bilateral arbitration clause (sole arbitrator mutually appointed, or each party appoints one) for non-RERA matters (payment default, assignment disputes). |
| 8 | **Usage Restriction** | Residential use only + no structural alterations + no balcony/terrace enclosure without approval. |
| 9 | **Defects Liability — Trigger Date** | Benchmark: 12 months from completion (Prestige). RERA mandates 5 years for structural defects from **possession**, not from "intimation of readiness." Ensure correct trigger. |
| 10 | **Escalation Clause** | "Escalation-free except statutory charges / development charges by authorities" — not blanket "escalation-free." |
| 11 | **Co-terminus with Agreement for Sale** | Construction agreement + Sale agreement = one transaction. Termination of one = both terminated. |
| 12 | **Common Maintenance / Corpus Fund** | Corpus fund amount (benchmark: ₹42/sq.ft.), maintenance charge structure, common area maintenance scope annexure. |

### LOW Priority — Standard Boilerplate

| # | Clause | What to Check |
|---|--------|---------------|
| 13 | **Notices** | Address-based + certificate of posting/courier + email as valid intimation. |
| 14 | **No-Waiver / Indulgence** | Delay in enforcement ≠ waiver of rights (mutual). |
| 15 | **Entire Agreement + Severability** | Written amendment only; severability if clause voided. |

## Construction-Agreement-Specific Pitfalls

- **Payment milestone alignment**: Milestones must match actual construction progress, not calendar dates (risk: allottee delays payment claiming "work not at milestone").
- **Specifications as scope boundary**: Blank specs = unenforceable scope. The allottee can later claim higher-grade finishes were promised orally.
- **UDS % in Schedule B**: Must be calculated from the plot area ÷ total project land, not left blank.
- **Co-terminus linkage**: If the Agreement for Sale exists separately, the construction agreement must explicitly reference it. Missing linkage creates title-vs-construction dispute risk.
- **Club/amenities disclaimer**: Benchmark practice (Prestige) explicitly states club completion ≠ possession obligation. Include if the project has shared amenities.

## Common Drafting Patterns (DRAAS Specific)

| Element | Typical DRAAS Pattern |
|---------|----------------------|
| **Promoter entity** | Sevaganapalli Land Partners (firm) or DRA Realty Pvt Ltd |
| **Property type** | Villa on undivided share of land (plotted dev) |
| **RERA registration** | TNRERA (Tamil Nadu) — registration number to be inserted |
| **Project location** | Hosur Taluk, Krishnagiri District — Tamil Nadu jurisdiction |
| **Payment structure** | Construction cost + corpus fund at possession |
| **Defects** | 5 years structural (RERA minimum), not 12 months (Prestige standard) |

## Verification

Before finalizing a reviewed construction agreement:
- [ ] Payment Schedule filled with real milestones and amounts
- [ ] Specifications Annexure completed (not blank sections)
- [ ] Payment default: interest rate + cure period + LD % all present
- [ ] Developer delay: interest rate + grace period defined
- [ ] Force majeure enumerated
- [ ] Assignment restriction with consent requirement
- [ ] Usage restriction for residential only
- [ ] Co-terminus link to Agreement for Sale
- [ ] Arbitration clause (fallback beyond RERA)
- [ ] Notice clause with email acceptance
- [ ] No-waiver clause (mutual)
- [ ] Entire agreement + severability clauses
- [ ] Actual corpus fund amount specified
- [ ] UDS percentage calculated and filled
