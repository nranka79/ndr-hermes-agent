# Indian Government Scheme Research

Workflow for researching Indian government schemes, subsidies, and programs when official websites return 403 errors or are inaccessible.

## Common Blocked Sites

Many GoI websites served through NIC/CSC infrastructure return **403 Forbidden** to headless browser agents or automated curl requests:
- `nbm.da.gov.in` (National Bamboo Mission)
- `pmksy.gov.in` (Pradhan Mantri Krishi Sinchayee Yojana)
- `nbm.nic.in` (NBM portal)
- Direct PDF links under `*.da.gov.in` or `*.nic.in`

## JS-Rendered Portals (Next.js / client-side hydration)

Several major GoI portals now use Next.js (React SSR + client hydration), making curl useless — they return empty shells:
- `india.gov.in` (National Portal of India — Next.js 14+)
- `myscheme.gov.in` (Next.js route-based rendering)
- `nbm.nic.in` (likely Next.js — curl returns empty)
- PIB site itself uses heavy client-side JS for its display layer

**Symptoms**: curl returns `<script>` bundles and JSON hydration data but zero visible content. Direct `browser_navigate` sometimes works, sometimes fails with engine errors.

## When Both Browser and Curl Fail

In this session (June 2026), `browser_navigate` failed with `"Unknown engine 'auto'"` — a browser-stack configuration issue. When **both** the browser tool and curl are blocked:

1. **Delegate to a subagent** using `delegate_task` with `toolsets=["web","terminal","file"]`. Subagents have their own browser infrastructure (separate engine config) and can often access sites the parent browser cannot.
2. The subagent's browser may use a different engine (e.g. lightpanda vs chrome) — the `Unknown engine 'auto'` error suggests engine auto-detection failed in the parent, but a subagent's isolated session may work.
3. Fallback sequence: parent browser → subagent browser → PIB/reference sites fetched via subagent curl.

**Example**: `delegate_task(goal="Research NBM subsidy...", toolsets=["web","terminal","file"])` successfully browsed government sites when the parent browser was down.

## Alternative Source Tiers

### Tier 1 — Primary Government (always try first)

| Source | URL | What it has |
|--------|-----|-------------|
| **PIB Press Releases** | `pib.gov.in/PressReleaseIframePage.aspx?PRID=<ID>` | Official scheme announcements, funding details, policy updates. PRID numbers found via Google search `site:pib.gov.in "scheme name"`. Works reliably with browser tool. |
| **myScheme.gov.in** | `myscheme.gov.in/schemes/<slug>` | Scheme eligibility, benefits overview, application process. Renders client-side (Next.js) — browser tool works, curl returns empty shell. |
| **NITI Aayog** | `niti.gov.in` | Technical notes, evaluation reports, outcome budgets. PDFs often downloadable despite 403s on other sites. |
| **India Budget / Outcome Budget** | `doe.gov.in` / `indiabudget.gov.in` | Scheme allocations, expenditure data |

### Tier 2 — Academic & Research Portals

| Source | URL | Reliability |
|--------|-----|-------------|
| **TNAU AgriTech** | `agritech.tnau.ac.in` | Excellent — Tamil Nadu Agricultural University. Cultivation guides, species data, economics. No bot blocking. |
| **IFGTB** | `ifgtb.icfre.gov.in` | Institute of Forest Genetics & Tree Breeding, Coimbatore. Bamboo research, high-yielding clones. Reliable. |
| **ICAR Institutes** | `iihr.res.in`, various | ICAR research portals. Generally accessible. |

### Tier 3 — Third-party Aggregators

| Source | URL | Caveat |
|--------|-----|--------|
| **AgriFarming.in** | `agrifarming.in` | Good for project reports, cost economics (sometimes 2018-era data). Verify current numbers against other sources. |
| **Krishijagran** | `krishijagran.com` | Ag news, scheme updates. Useful for current events. |
| **Google Search snippets** | `google.com/search` | Use with `site:.gov.in` or `site:pib.gov.in` filters to discover official PRIDs and PDF URLs. The snippet text often contains key data even when the target site is down. |

## Workflow

1. **Google reconnaissance first** — search `site:.gov.in "Scheme Name" subsidy beneficiaries` to discover:
   - PIB PRID numbers (note down for direct access)
   - PDF filenames on the official site
   - Alternative government pages referencing the scheme

2. **Try official sites with browser tool** — some work even when curl gets 403. The `browser_navigate` tool has stealth features.

3. **Fall back to PIB** — construct URL: `https://pib.gov.in/PressReleaseIframePage.aspx?PRID=<PRID_NUMBER>`. Press releases usually contain exact subsidy percentages, beneficiary counts, allocation amounts, and scheme durations.

4. **Cross-reference with academic portals** — for technical data (species, cultivation practices, soil requirements), academic portals are often better than government sites anyway.

5. **Check NITI Aayog / Outcome Budget** — for allocation data and scheme performance metrics.

## Example: NBM Research Path

When researching National Bamboo Mission (June 2026):

1. `nbm.da.gov.in` → 403 Forbidden (curl and browser)
2. Google search `site:pib.gov.in "National Bamboo Mission"` → found PRID references
3. PIB Backgrounder ID 155112 (Aug 2025) — Comprehensive NBM scheme document (downloaded as PDF)
4. PIB PRID 2113716 → AIF scheme details (3% interest subvention, 1L Cr fund)
5. PIB PRID 2106913 → FPO scheme details (Rs. 6865 Cr outlay)
6. TNAU AgriTech → bamboo species, spacing, yield data
7. AgriFarming.in → per-acre cost breakdown, economics
8. myscheme.gov.in/schemes/nbm → scheme listing (eligibility checker)
9. NITI Aayog Technical Note on Restructured NBM → scheme design document

### NBM Specific Findings (June 2026 Research)

**Status:** Restructured NBM (since April 2018) is a **standalone Centrally Sponsored Scheme** under Ministry of Agriculture & Farmers Welfare — it was previously under MIDH (2014-2018). Implemented in 24 States/UTs.

**Funding pattern confirmed:** 50:10:40 (Govt Subsidy : Beneficiary : Bank Loan) — credit-linked back-ended subsidy. Direct subsidy of Rs. 1,00,000 per hectare at 50% rate. 60:40 Centre:State for general states; 90:10 for NE/Hilly; 100% for UTs.

**What's covered:** Land preparation, planting material, drip irrigation, fencing, 3-year maintenance, intercropping costs, nursery development, processing units (50% capital subsidy), market infrastructure, skill development, R&D.

**Subsidy stacking strategy (worked example — 10 acres bamboo farm):**

|--- Scheme ---|---- Component ----|--- Subsidy ---|---- Savings on 10 Ac ----|
| **NBM** | Cultivation (3yr, excl. drip) | 50% | Rs. 6,41,250 |
| **PMKSY** | Drip irrigation | 55% | Rs. 2,47,500 |
| **AIF** | Processing unit loan | 3% subvention (7yr) | ~Rs. 6,00,000 |
| **Total stacked** | Cultivation + Irrigation | ~51% effective | Rs. 8,88,750 |

**Key insight:** After stacking NBM (50%) + PMKSY (55%), the net cultivation cost for 10 acres over 3 years is Rs. 8.4L. Intercropping generates Rs. 9L over the same period. Zero net out-of-pocket during establishment phase.

**Convergence schemes:** AIF (Rs. 1L Cr loan pool, 3% interest subvention for 7yr), PMKSY (55-75% drip subsidy), FPO Support (Rs. 6865 Cr outlay, Rs. 18L per FPO), RKVY (25-40% value-add infra).

## Key Data Points to Extract

For any subsidy scheme, extract into a consistent structure:

- **Funding pattern** (e.g., 50:40:10 = govt:loan:self)
- **Per-beneficiary cap** (Rs./ha or Rs./unit)
- **Eligibility** (land ownership, farmer status, land type)
- **Application process** (online/offline, documents needed)
- **Disbursement mechanism** (front-ended vs. back-ended subsidy)
- **Convergence possibilities** (which other schemes can stack)
- **Validity** (scheme end date, budget cycle)
