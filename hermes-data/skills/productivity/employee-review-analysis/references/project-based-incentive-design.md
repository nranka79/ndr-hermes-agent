# Project-Based Incentive Design — Engineering Head (DRAAS)

## When to Use This Model

Use Model B instead of the default monthly KPI model when:
- The role has end-to-end project ownership (Engineering Head, Project Director)
- The user explicitly asks for "no monthly variable" or "incentive only on project outcomes"
- Multiple concurrent projects exist with distinct budgets and timelines
- Quality/snag tracking infrastructure is in place or planned

## Core Framework

### A) Fixed Pay
- Base + attendance + commute allowance as fixed monthly
- No variable component — clean separation of fixed and performance pay
- For Bangalore-Hosur corridor senior roles: ₹30K/month commute allowance is market minimum

### B) Timeline Incentive

**Formula:** Timeline Bonus = % × Total Project Contract Value

| Condition | Payout |
|---|---|
| On time | 1.0% of contract value |
| 1 month early | 1.5% of contract value |
| 2 months early | 2.0% of contract value |
| 3+ months early | 2.5% of contract value (cap) |

**Market benchmark:** 1-3% of contract value is standard in Indian real estate for senior engineering roles.

### C) Cost Savings Incentive

**Formula:** Savings Incentive = 15% × (Approved Baseline Budget − Actual Cost) + Fixed Top-Up Kicker

**Budget Verification Process:**
1. Internal team prepares budget A
2. Independent external QS/PMC prepares budget B
3. Approved Baseline Budget = min(Budget A, Budget B)
4. Change orders for scope additions excluded from savings calculation
5. Final cost verified by external auditor at project close

**Top-Up Kicker:** ₹25,000 per ₹10L of savings (fixed amount on top of %)

**Market benchmark:** 10-20% of net savings is standard. 15% is mid-range.

### D) Red Snags Clause

**Zero-Tolerance (1 snag = full forfeiture):**
- Column / pillar deviation from plumb beyond structural tolerance
- Foundation / footing settlement or cracking
- Structural element not as per approved structural drawings
- Waterproofing failure in basement or terrace
- Major deviation in set-back / building line from approved plan

**Graded Penalties:**

| Red Snags Found | Timeline Incentive | Savings Incentive |
|---|---|---|
| 0-2 | 100% retained | 100% retained |
| 3-5 | 50% retained | 75% retained |
| >5 | 0% (FULL FORFEITURE) | 0% (FULL FORFEITURE) |
| Zero-tolerance item (any) | Full forfeiture | Full forfeiture |

**Snag inspection stages:** structural completion → finishing → pre-handover
**Holdback:** 10% of total incentive retained for 6 months post-handover, released after zero-pending-snags certificate

### E) Head vs Team Split

- **Head (Engineering Head):** 50% of total incentive pool
- **Team Pool:** 50% (Head has full discretion on internal distribution, documented to HR/Management)

**Market benchmark:** 50:50 to 60:40 in favour of head. 50:50 recommended for team retention.

## Total Compensation Target

**Variable as % of Fixed CTC:** 30-50% at target performance, uncapped upside for exceptional
**Scenario modelling:**
- Baseline (1 project/year, on-time, no savings) → timeline bonus only
- Target (2 projects/year, on-time, modest savings) → 30-40% of fixed
- Exceptional (2-3 projects/year, early completion, significant savings) → 80-115% of fixed

## Kelsa Tracking Fields

Suggested workspace fields per project:

**Project-level:**
- Project Name
- Contract Value (₹)
- Approved Baseline Budget (₹) — internal
- External Benchmark Budget (₹)
- Actual Cost to Date (₹)
- Scheduled Completion Date
- Current Forecast Completion Date
- Red Snag Count (Zero-Tolerance / Category A / Category B split)
- Red Snags Rectified / Open
- Savings to Date (₹)
- Estimated Final Savings (₹)
- Estimated Incentive Payout (₹)

**Automation triggers:**
- Scheduled milestone tasks → auto-populate completion dates
- Snag register entries → auto-count categories, apply forfeiture rules
- Monthly cost update → recalculate savings estimate
- Final completion → trigger incentive calculation

## Domain Research Sources

Benchmarks sourced from (2024-2025 data):
- Indian real estate engineering head compensation: 1-3% of project value for on-time completion
- Cost savings sharing: 10-20% of net savings (industry standard)
- Variable pay as % of fixed: 30-50% for senior engineering roles
- Red snag thresholds: >5 category defects = full forfeiture is standard practice
- Retention holdback: 10-20% for 3-6 months post-handover
- Head:Team split: 50:50 is standard for department heads

## Optional Additional KPAs (DRAAS, June 2026)

The core framework above covers timeline + cost + quality. For senior Engineering Heads with multi-role scope, these additional KPAs can be layered in as separate bonus pools:

### F) Site Housekeeping & Presentation

Monthly unannounced inspections score across 4 dimensions (25% each):
- Material storage (organised, labelled, covered)
- Site cleanliness (debris management, designated pathways)
- Safety signage & PPE compliance
- Worker amenities (toilets, drinking water, rest area)

**Incentive:** If quarterly average across ALL active sites exceeds 85%, Engineering Head earns a quarterly housekeeping bonus of ₹50,000.

### G) Innovation & R&D Bonus

Encourage proposals for new methodologies, materials, products, or construction techniques that measurably improve cost, time, quality, sustainability, or maintenance.

**Process:**
1. Head submits proposal with expected benefit analysis (cost, time, quality)
2. Management reviews (with external consultant if needed)
3. If approved and implemented → Head earns:

   a) One-time innovation bonus: ₹25,000 per approved innovation
   b) If measurable cost savings result: 20% of net savings (in addition to regular cost savings incentive under C)

### H) Engineering Manpower Overhead Efficiency

Controls the ratio of engineering team salary cost to total engineering spend across all active projects:

```
Overhead % = (Total Engineering Team Salary + Benefits) / (Total Engineering Spend) × 100
```

**Incentive:**
- If actual ≤ Target: ₹50,000 per quarter
- If actual ≤ Stretch Target: ₹1,00,000 per quarter

Target % established from first 6 months baseline data.

### I) Company Profitability Link

Aligns Head's interests with overall company financial health:

| Metric | Condition | Payout |
|--------|-----------|--------|
| Topline | Annual sales bookings ≥ ₹100Cr | 0.05% of total engineering spend across completed projects (cap ₹5L) |
| Bottomline | Net profit margin > 20% | ₹2,50,000 lump sum |
| **Combined max** | | **₹7,50,000 per financial year** |

## Discussion-Document Pattern

When the deliverable is a performance incentive framework that the employee should **review and provide input on** (not a final policy), frame it as a **Discussion Document**:

1. **Title clearly states:** "Discussion Document"
2. **Opening paragraph:** States this is a starting point, not final — employee encouraged to question, suggest enhancements, propose modifications
3. **Specific asks at the end:** Invite input on ambiguous metrics (overhead target %, scoring methodology, alternative payout mechanisms)
4. **Meeting commitment:** State that a discussion meeting will follow the employee's review
5. **Include worked examples** with company-specific project names and realistic budget figures to make the upside tangible

This pattern was used for Anbarasan (Anbu) in June 2026 with three project scenarios (Amber ₹8Cr, Oasis ₹80Cr, North Star ₹40Cr).

## Worked Examples

### Example 1 — Small Project (Ranka Amber: ₹8Cr, 12-month schedule)
- Baseline budget: ₹7.50Cr | Actual: ₹6.80Cr | 1 month early | 2 red snags (Cat B) | Housekeeping 88% | 1 innovation | Overhead met
- Timeline: 1.0% × ₹8Cr = ₹80,000
- Savings: ₹70L → 15% = ₹10,50,000 + ₹1,75,000 kicker = ₹12,25,000
- Innovation: ₹25,000 | Housekeeping: ₹50,000 | Overhead: ₹50,000
- **Total:** ₹14,30,000 (68% of annual fixed ₹21L)

### Example 2 — Large Project (Ranka Oasis: ₹80Cr, 36-month schedule)
- Baseline budget: ₹76.00Cr | Actual: ₹69.50Cr | 2 months early | 1 red snag (Cat B) | Housekeeping 92% | 2 innovations | Overhead met
- Timeline: 2.0% × ₹80Cr = ₹16,00,000
- Savings: ₹6.50Cr → 15% = ₹97,50,000 + ₹16,25,000 kicker = ₹1,13,75,000
- Innovation: ₹50,000 | Housekeeping: ₹50,000 | Overhead: ₹50,000
- **Total:** ₹1,31,25,000 (625% of annual fixed — exceptional for an exceptional project)

### Example 3 — Mid Project (Ranka North Star: ₹40Cr, 24-month schedule)
- Baseline budget: ₹38.50Cr | Actual: ₹36.20Cr | On time | 3 red snags (Cat B) | Housekeeping 82% | 0 innovations | Overhead not met
- Timeline: 0.75% × ₹40Cr = ₹3,00,000 (on-time rate, reduced from 1.0%)
- Savings: ₹2.30Cr → 15% = ₹34,50,000 + ₹5,75,000 kicker = ₹40,25,000
- Red snags (3): timeline at 50% = ₹1,50,000, savings at 75% = ₹30,18,750
- Innovation: ₹0 | Housekeeping: ₹0 (<85%) | Overhead: ₹0
- **Total:** ₹31,68,750 (151% of annual fixed)

### Classic Example — ₹20Cr contract value, 18-month schedule
**Baseline Budget:** ₹18.50Cr (internal), ₹18.75Cr (external) → baseline = ₹18.50Cr
**Actual Cost:** ₹16.80Cr
**Timeline:** 1 month ahead of schedule
**Red Snags:** 2 Category B (rectified pre-handover)

**Timeline:** 1.5% × ₹20Cr = ₹3,00,000
**Savings:** ₹18.50Cr − ₹16.80Cr = ₹1.70Cr → 15% = ₹25,50,000 + top-up ₹4,25,000 = ₹29,75,000
**Total Pool:** ₹32,75,000
**Head:** ₹16,37,500 | **Team:** ₹16,37,500
**Holdback:** ₹3,27,500 released after 6 months
**Net to Head at close:** ₹13,10,000 (~115% of annual fixed pay)
