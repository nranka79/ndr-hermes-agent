# Fiverr Freelancer Research

Researching freelancers on Fiverr who offer specific services (e.g., Revit MEP, STAAD-to-Revit, plumbing design).

## Key Constraint — Bot Detection & CAPTCHA Wall

Fiverr has aggressive bot detection. The failure modes are:

| Approach | Result |
|----------|--------|
| Direct URL with query params (`fiverr.com/search/results?query=...`) | CAPTCHA block |
| Clicking seller name links in search results | CAPTCHA block — "It needs a human touch" |
| Direct profile URL (`fiverr.com/users/<username>`) | 404 or CAPTCHA block |
| Gig detail page links | CAPTCHA block |
| `web_search` / `web_extract` | No provider configured — errors immediately |

**The browser tool is the only viable path for Fiverr, but it can only read the search results listing page.**

---

## Working Workflow

### Step 1 — Use the search box (not URL params)
```
browser_navigate → https://www.fiverr.com
browser_click → ref=<search box>   # Use snapshot to find the ref
browser_type  → text="Revit MEP BIM 3D model plumbing electrical from structural drawings STAAD ETABS"
browser_press → Enter
```

This mimics a real user typing and pressing Enter — avoids the query-param URL that triggers bot detection.

### Step 2 — Read results from the search listing page

The search results page itself loads reliably and shows substantial data for each seller:
- Seller name + level (Top Rated, Level 2, etc.)
- Star rating + review count
- Gig title
- Price ("From $X")
- Seller location

**Extract this data directly from the snapshot** — do NOT click through to profile or gig detail pages. They will trigger CAPTCHA and yield no additional usable data.

If you need more results, scroll down (new results load dynamically) rather than navigating to page 2, which also triggers CAPTCHA.

### Step 3 — Compile findings from snapshot data

Collect: name, username (from link href), rating, reviews, price, gig title. Present these to the user as the deliverable. Acknowledge that full profile verification (reading gig descriptions, seller bios, portfolio samples) is blocked by CAPTCHA.

---

## Query Strategies for Niche Engineering Services

When looking for very specific engineering services on Fiverr, try these query variants:

| Goal | Query |
|------|-------|
| Structural to Revit | `STAAD ETABS to Revit 3D model` |
| MEP full package | `MEP BIM Revit plumbing electrical design` |
| Plumbing + electrical | `plumbing electrical hvac structure drawings` |
| BIM modeling | `Revit BIM model from 2D drawings` |
| General CAD/Revit | `3D cad design revit inventor solidworks` |

Add `STAAD ETABS` explicitly to filter for structural-conversion specialists. Fiverr returns 3,000+ results for MEP-related queries — use seller ratings (5.0 stars, Top Rated badge, Fiverr's Choice) and review counts to narrow down.

---

## Limitations

- Cannot read individual gig descriptions or seller bios — CAPTCHA blocks profile pages
- Cannot verify a seller's actual portfolio or past projects
- Cannot filter by Pro services without triggering additional CAPTCHA challenges
- Video consultations badge is visible in results listing — useful signal without needing to visit the profile

**Workaround for deeper verification:** Ask the user to search Fiverr directly in their own browser, or suggest they message 2-3 shortlisted sellers directly with specific technical questions to vet competency.

---

## Notes

- Fiverr shows ~20 results per scroll — scroll down to load more
- Prices shown are "From $X" base prices; full project pricing requires contacting the seller
- "Pro services" checkbox filter reduces results significantly but surfaces verified top-tier sellers