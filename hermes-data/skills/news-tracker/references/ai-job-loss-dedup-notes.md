# Deduplication Notes — AI Job Loss Tracker

Decision tree, source ranking, trap patterns, and captured entries for deduplication.

## Deduplication Decision Tree

```
1. Extract company name + quarter + year from article
   → Key = "Company Q2 2026"

2. Is key already in sheet?
   ├── YES → Same quarter, same company
   │         → Is confirmed job number HIGHER than existing?
   │            ├── YES → Update Jobs Lost + Notes + Last Updated
   │            └── NO  → Skip (keep existing, higher confidence source)
   └── NO  → Is article within 48 hours?
             ├── YES → Add as new row
             └── NO  → Skip (outside window)

3. Company appears in MULTIPLE articles same quarter?
   → Keep highest confirmed number + most credible source
   → Priority: Reuters > Bloomberg > national newspaper > tech blog > social media
```

## Source Credibility Ranking

1. **Reuters / Bloomberg** — structured, verified, reliable numbers
2. **National newspapers** — Economic Times, Financial Times, NYT, WSJ
3. **Tech blogs** — TechCrunch, Business Insider, VentureBeat
4. **Trade publications** — HR Executive, Fast Company
5. **Local news** — Business Journals (for US companies), regional outlets
6. **Social media / employee posts** — lowest credibility, use only if nothing else available

## Trap Patterns

### "Hundreds" / "Thousands" without exact number
- **Problem:** Articles say "cut hundreds of jobs" with no specifics
- **Fix:** Use company headcount from `references/company-data.md` to estimate. If unknown, write "hundreds (exact number unconfirmed)"

### Unnamed company articles (e.g. "Company dumps 1,000 workers")
- **Problem:** 24/7 Wall St. ran "AI Layoffs Strike Again, As Company Dumps 1,000 Workers" — no company name in headline
- **Fix:** Skip. Cannot deduplicate without company name.

### Pre-announcement articles
- **Problem:** Meta had articles published May 17 about May 20 layoffs
- **Fix:** These are the SAME event — do not treat as duplicates. If article describes a specific future layoff event, it's the same entry even if published before the event date.

### Multiple articles for same company+quarter — use the best number
- **Problem:** GitLab had May 13 article ("30% cut") and June 2 article ("hundreds"). Both describe Q2 2026 restructuring.
- **Fix:** Take the highest confirmed number (30% ≈ ~600 jobs) as the Jobs Lost value. Note the earlier article in Notes. Do NOT create two rows for the same company+quarter.

### Multiple quarters
- **Problem:** Standard Chartered announced 7,000+ cuts by 2030 — not all in Q2
- **Fix:** Record the announced total in Notes. If specific quarterly breakdown is given, record per-quarter. If only total known, record total and note timeline.

## Captured Entries (Q2 2026)

| Company | Jobs Lost | Source | Notes |
|---------|----------|--------|-------|
| Innovaccer | ~340 | Hindustan Times | 3rd layoff round in 4 years |
| AI21 Labs | ~60% workforce | CTech | Israeli NLP company, ~155M Series C |
| Meta | 8,000 | Business Insider | May 20 restructuring |
| Standard Chartered | 7,000+ | Reuters | By 2030; 7,800 corporate roles |
| Intuit | ~3,000 | TechCrunch | 17% workforce; CEO said "nothing to do with AI" |
| Acrisure | 2,250 | WWMT | Grand Rapids insurance broker |
| ClickUp | ~22% workforce | American Bazaar | ~110 jobs if ~500 employees |
| Cisco | <4,000 | HR Executive | <5% of 84,000 |
| Wix | ~1,000 | CTech / Reuters | 20% cut; CEO: Avishai Avraham |
| Synopsys | ~2,000 | tech-insider.org | Post-$35B Ansys acquisition |
| Groupon | 400 | PYMNTS | Deals marketplace, AI pivot |
| Microsoft | ~8,750 (buyouts) | tech-insider.org | April 2026; $80B AI pivot |
| GitLab | ~600 | The Business Journals | 30% of ~2,000 headcount (GTLB NASDAQ). May 13 article first reported 30% cut; June 2 article confirmed ongoing restructuring. |
| Oracle | 30,000 | The Economic Times | 30,000 cuts completing by June 15, 2026. AI restructuring cited. |
| Google Cloud | ~50-100 (dozens) | NDTV Profit, Mint | Fresh targeted cuts in Threat Intelligence + Mandiant teams citing AI shift. June 4-5, 2026. |
| Rackspace | ~1,050 (15%) + 750 (2nd round) | Business Journals, The American Bazaar | Two separate rounds in Q2 2026: 15% of ~7,000 (~1,050, June 16) + 750 (June 28). Both explicitly cited AI strategy pivot. Previous entry erroneously recorded "15" instead of properly estimating from 15% × ~7,000. Consolidated June 29 run. |

## Known Duplicate Sources (do not add again)

- Meta Q2 2026 — already recorded (8,000 jobs, May 18 article)
- Wix Q2 2026 — already recorded (1,000 jobs, May 25; repeated May 28-31 with same 20% cut story from MSN/Yahoo Finance — same event, not a new one)
- Cloudflare Q2 2026 — already recorded (1,100 jobs, May 8 articles — outside 48h window)
- GitLab Q2 2026 — already recorded (June 3 run)

## Edge Cases

- **Descriptor-prefix company names ("Payment processor Visa")** — Aug 1 2026 run: headline "Payment processor Visa lays off 7% of staff, citing AI-driven efficiency gains" matched the generic catch-all and captured "Payment processor Visa" as the company, creating a NEW row even though `Visa|Q3 2026` (2,600 jobs, 7%, eciks.org) already existed. **Fix applied:** extended the descriptor pattern to `^(Payments?\s+(?:giant|processor|firm)|Payment\s+processor)\s+(Visa|...)` BEFORE the catch-all, and added aliases `"Payment processor Visa" → "Visa"`, `"Payments processor Visa" → "Visa"`, `"Payment firm Visa" → "Visa"`, `"Payments firm Visa" → "Visa"`. Duplicate row was deleted from the sheet. Any `X giant` / `X processor` / `X firm` descriptor prefix before a known company name is vulnerable to this — check new catch-all matches against existing sheet rows before writing.
- **CI Tech / Calcalist articles** — often 404 via direct URL. Use RSS headline/description as source. Do not spend time hunting working URLs.
- **Business Journals** — redirect chain (301 → advertise.bizjournals.com). Try the redirect target or use RSS link instead.
- **SentinelOne press release at sentinelone.com** — 404. Use secondary sources (CNBC, Business Journals) for both headline and job numbers.
- **Company name variant collision (Google / Google Cloud)** — the company extraction pattern `^(Google) (dumps|lays off|cuts...)` matches "Google" from headlines like "Google lays off Cloud, cybersecurity staff..." (Indian Express, June 7 2026). The dedup key becomes `Google|Q2 2026`, which does NOT match the existing sheet entry `Google Cloud|Q2 2026` (from NDTV/Mint June 4-5). These describe the same layoff event — Google Cloud division cuts. **Fix:** normalize company names before dedup checking: "Google Cloud" → "Google", "Meta Platforms" → "Meta", etc. Check parent-company vs division variants as equivalent before creating a new row.
- **GitLab 14% (June 8 Memeburn)** — "GitLab Cuts 14% of Staff in Major AI Pivot Despite Record Revenue" describes ~280 jobs (14% × ~2,000 headcount). Already captured in sheet at ~600 (30% headcount, May 13 + June 2 articles). Lower number → skip. Do not create a second GitLab row.
- **RSS description is often just the title repeated** — Indian Express and similar outlets publish headlines where the RSS `<description>` field contains only the outlet name, not article body text. Do not rely on description for job numbers; use title patterns and percentage-to-headcount estimation instead.
- **Existing row has percentage recorded as raw number (e.g. "15" for "15%")** — Some early rows contain un-estimated percentages because no headcount was available at the time. When a later article provides a specific number or the headcount is discovered, UPDATE the existing row with the properly estimated value rather than adding a duplicate row. Log the correction in Notes.