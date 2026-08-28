# Company Headcount Data — AI Job Loss Tracker

Headcount/employee counts for frequently-seen companies, used to estimate job numbers when articles only give percentages or "hundreds."

**Note:** These are approximate public figures — verify current numbers before using for exact calculations. Update when new data is found during runs.

## Tech / SaaS Companies

| Company | Approx Headcount | Source / Last Seen |
|---------|-----------------|-------------------|
| GitLab | ~2,000 employees | Public (GTLB NASDAQ) — 30% cut ≈ ~600 jobs, Q2 2026 |
| Oracle | ~180,000-200,000 employees | Public — 30,000 cuts ≈ 15-17% of workforce, Q2 2026 |
| SentinelOne | ~3,000 employees | Public reports, Wikipedia — used in Q2 2026 run |
| Wix | ~5,283 employees (2024) | Wikipedia — 20% cut ≈ ~1,057 jobs; corrected from erroneous ~1,600 estimate on May 31 2026 |
| Meta | ~70,000 employees | Public — Q2 2026 cut was 8,000 (~11%) |
| ClickUp | ~500 employees (est.) | Multiple sources — 22% cut ≈ ~110 jobs |
| Cloudflare | ~2,300 employees | Public — Q2 2026 cut was 1,100 (~48% — cited AI making "measurement" roles obsolete) |
| Intuit | ~17,000 employees | Public — 17% cut ≈ ~2,900 jobs |
| Groupon | ~1,000 employees | Public — 400 cut ≈ 40% |
| BitGo | ~566 employees (2026) | Wikipedia, NYSE:BTGO — 15% cut ≈ ~85 jobs, Q2 2026 |
| Rackspace Technology | ~7,000 employees | Public (RXT) — Q2 2026: 15% (~1,050) + 750-round two, both citing AI pivot |
| Cisco | ~84,000 employees | Public — <4,000 cut (<5%) |
| Microsoft | ~220,000 employees | Public — 8,750 buyout (~4%) |
| Visa | ~37,000 employees | Public — 7% cut ≈ ~2,600 jobs, Q3 2026 |
| Chime | ~1,300 employees | Reuters (Jul 31 2026) — 10% cut ≈ ~130 jobs, Q3 2026, explicitly AI-driven efficiencies |
| ServiceNow | ~25,000 employees | The Business Journals (Jul 30 2026) — 154 jobs in Santa Clara, Q3 2026 (exact number, AI link not explicit in headline) |
| VideoAmp | ~583-711 employees | Revelio Labs (583, Mar 2026); Tracxn (711, Jun 2026) — 20% cut ≈ 50-60 jobs confirmed by WSJ/Forbes/peoplemattersglobal, Q3 2026. CTO cut, role not refilled; CEO Fagan cites agentic AI. |
| Mews | ~1,350 employees | Skift (Jul 7 2026) — 15% cut ≈ ~200 jobs, Q3 2026. Also reported as ~170 jobs by nltimes.nl |

## Mobility / Gig Economy

| Company | Approx Headcount | Notes |
|---------|-----------------|-------|
| Uber | ~29,000-32,000 employees | Public (UBER) — 10% of customer service jobs, Q3 2026. Headline explicitly cites AI ("'Embrace' of AI"). |

## Non-Tech / Financial Services

| Company | Approx Headcount | Notes |
|---------|-----------------|-------|
| Standard Chartered | ~87,000 employees | Public — 7,000+ cuts by 2030 |
| Fidelity Investments | ~73,000 employees | Public reports — 1% cut ≈ ~730 jobs, Q3 2026 |

## Fintech / Banking

| Company | Approx Headcount | Notes |
|---------|-----------------|-------|
| Starling Bank | ~2,000 employees (est.) | UK digital bank. 130 jobs ≈ ~6.5% cut, Q3 2026 |

## Rules for Estimation

1. **"hundreds"** — when a company with ~3,000 employees cuts 8%, that's ~240 jobs. Describe as "~240-300 (hundreds, ~8%)" in the Jobs Lost column.
2. **"% of workforce"** — multiply percentage by known headcount. If headcount is unknown, write the percentage as given and note "exact headcount unconfirmed."
3. **Never guess headcount** — if no public data found and article only says "hundreds," use "hundreds (exact number unconfirmed)" and note the approximate in Notes.
4. **Update this file** — every time you discover a company's headcount during a run, add it here for future reference. Use `skill_manage(action='write_file', name='news-tracker', file_path='references/ai-job-loss-company-data.md', file_content=...)` to write.

## SentinelOne Case Study (May 30, 2026)

- **Articles:** CNBC (May 29), The Business Journals (May 28)
- **Headline:** "SentinelOne stock drops 8% as cyber firm trims headcount to boost AI investments"
- **Quote:** "trims headcount" — no exact number
- **Headcount found:** ~3,000 employees via Wikipedia/public reports
- **Calculation:** 8% × 3,000 ≈ 240
- **Entry written:** "~240-300 (hundreds, ~8%)"
- **Source quality:** CNBC (high credibility) + Business Journals (local but credible)

## Fidelity Investments Case Study (July 5, 2026)

- **Headline:** "Fidelity Investments lays off 1% of workforce but plans major hiring push to rebuild tech teams"
- **Source:** eciks.org (low credibility)
- **Headcount:** ~73,000 (public reports)
- **Calculation:** 1% × 73,000 ≈ 730 jobs
- **AI link:** Article explicitly cites AI in layoffs and hiring push context
- **Note:** If a higher-credibility source appears later (Reuters, Bloomberg, WSJ), update the entry

## Mews Case Study (July 7, 2026)

- **Headline:** "Mews Cuts 15% of Staff, Points to AI in Broad Restructuring — Exclusive"
- **Source:** Skift (travel industry publication, credible)
- **Headcount:** ~1,350 employees per Skift; ~1,133 if 170 employees = 15%
- **Calculation:** 15% × 1,350 ≈ 202 jobs; nltimes.nl stated ~170 jobs
- **Entry written:** "15%" (percentage — estimate ~170-200 jobs)
- **AI link:** Founder explicitly cited AI making roles obsolete
