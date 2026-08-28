# Pricing Triangulation — Operational Recipe (Aug 2026, NorthStar R&D)

How the 66-project NorthStar triangulation was actually executed, so future
passes don't re-derive it. Companion to §5/§6b of SKILL.md.

## 1. Per-project listing collection

For each competitor, run `web_search` with a locality-qualified query:

```
"<Project Name>" <locality> Bangalore price per sqft
```

- Locality qualifier is CRITICAL — unqualified searches pollute with
  same-named projects elsewhere (Adarsh Tropica=Sarjapur, Birla Tisya=
  Rajajinagar, **Embassy Grove=Old Airport Rd/Kodihalli**, **SRNR
  Daffodil=JP Nagar**).
- First pass at limit=5 returns 5 hits/project but descriptions are
  truncated at 200 chars in the stored JSON — psf values often appear
  beyond that. **Run a second pass on no-psf projects with limit=8 and
  full 400-char descriptions.** (~22/26 stragglers resolved this way.)
- Third pass for the last few: alternate query shapes (`price`, `rate`,
  `2026`, `villas`, `plots`) and accept total-price text when psf absent
  (compute psf = total ÷ area, mark approx).

## 2. psf extraction regex

```python
pats = [
    r'[₹Rs\.]*\s*([\d,]{3,7}(?:\.\d+)?)\s*(?:/\s*sq\.?\s?ft\.?|per\s+sq\.?\s?ft\.?|psf|/sq)',
    r'([\d,]{3,7}(?:\.\d+)?)\s*K\s*(?:-|to|–)\s*([\d,]{3,7}(?:\.\d+)?)\s*/\s*sq',
    r'([\d,]{3,7}(?:\.\d+)?)\s*(?:-|to|–)\s*([\d,]{3,7}(?:\.\d+)?)\s*(?:/\s*sq\.?\s?ft|per\s+sq)',
]
# keep 1500 <= v <= 80000
```

## 3. Curation (the step that separates good data from garbage)

- Collect all (psf, domain, url) pairs; dedupe by (psf, domain).
- Filter to plausible band: **3000–45000** (Yelahanka has 3k plots to
  26k+ luxury — don't use one blanket ceiling).
- Pick the best per domain (median of that domain's values), rank domains
  by credibility (official builder > 99acres/MagicBricks/Housing/NoBroker
  > aggregators), take top 3 distinct domains.
- Triangulated psf = **median** of the chosen values (NOT mean — robust
  to one wrong-row listing).
- Single-source projects → `single-source (verify)` in Pricing Basis,
  never presented as triangulated.

## 4. Values to distrust (validated this run)

| Signal | What it was |
|---|---|
| ₹1,28,025/sqft for Century OneWorld Seraya | wrong-row MagicBricks "Project vs Locality" table (real: plots ₹7,000 official, ₹12,500 Reddit EOI) |
| Embassy Grove ₹26,666–32,727 | SAME-NAME — that's the Kodihalli/Old Airport Rd project, not Yelahanka; Google has NO pin for the Yelahanka one |
| SRNR Daffodil ₹27,500 / ₹9,584 | SAME-NAME — resolved to JP Nagar; mark LOW CONFIDENCE |
| Embassy Boulevard ₹40,000–44,135 | real — ultra-luxury villa community off Bellary Rd |
| L&T Raintree Boulevard search | returned L&T STOCK prices — title/snippet noise; re-query with quotes + locality |

Rule: if a snippet's project/locality doesn't match the sheet row, EXCLUDE
or mark `SAME-NAME WARNING` — never let it enter the median silently.

## 5. Google Sheets multi-column update gotcha (hit live)

Writing `Competitors!E2:M68` with a 2-column value list **silently did
NOT apply** (9-col range × 2-col values = mismatch). The M1 header wrote
fine, prices didn't. Fix: **write each column as its own range** —

```python
sv.spreadsheets().values().update(
    spreadsheetId=SHEET, range='Competitors!E2:E68',
    valueInputOption='USER_ENTERED', body={'values': [[str(psf)] for ...]})
sv.spreadsheets().values().update(
    spreadsheetId=SHEET, range='Competitors!M2:M68', ...)
```

Always re-read the range after writing to verify `updatedCells`/values.

## 6. Apify blanket city run — NOT useful for pricing

`magicbricks-99acres` with `cities:["Bangalore"], maxResults:200` returned
**1 listing** (an unrelated Whitefield project) — city-wide portal scraping
doesn't cover named per-project pricing. Use it only for discovery volume;
per-project pricing comes from the web_search snippet pipeline (Step 1).

## 7. Deliverable shape (what Nishant expects)

- New tab `Listings & Pricing Data`: `Sl No | Project Name | Source /
  Portal | Rate (Rs/sqft) | Date | Source URL` — one row per listing.
- Competitors tab: `Price (Rs/sqft)` = triangulated median; new
  `Pricing Basis` column (`3-source triangulated` / `2-source` /
  `single-source (verify)`).
- Spot-check ≥3 projects: Competitors psf == median of their listings rows.
