# Portal Listing Capture — Real URLs + Posted-By/Date (R&D pricing source rows)

The R&D sheet's `Listings & Pricing Data` tab must contain **individual listing rows**
that a human can click. Each row: Project | Source/Portal | Posted By | Posted Date |
Price (Rs) | Area (sqft) | Rate (Rs/sqft) | Source URL | Data Source.

## Hard rule: full URLs, never truncated
The #1 user complaint was "all the links seem to fail". Root cause: during curation the
URLs were cut mid-ID (e.g. `pdpid-4d4235…`, `…-npxid` with no ID, `…-np`). 109/156 rows
were truncated. **Never shorten or reformat a source URL when writing rows.** If a URL
is longer than your display, the display truncates — the CELL must keep the full string.

## Date column = the listing's POSTED date, not the research date
The user was explicit: 99acres/MagicBricks listing pages show "Posted by <builder/broker>"
and a posted date. Capture THAT. Storing "today" (the day you researched) in the Date
column is wrong and was called out. Use columns `Posted By` + `Posted Date` and fill them
from the listing page / snippet, not from `datetime.now()`.

## Tool ladder for live portal data (in priority order)
1. **Tavily `web_search`** — still the funded workhorse. Site-targeted queries return real
   listing URLs + snippet dates:
   - `site:99acres.com "<project>" spid` → individual listing URLs ending `spid-<id>`
   - `site:magicbricks.com "<project>" propertyDetails` → `/propertyDetails/...&id=...`
   - Snippets carry posted dates: `Jul 9, 2026 —`, `Posted: Jul 28, '26`, `19 hours ago —`,
     `3 days ago —`. Resolve relative dates against today.
   - **Rate limit**: HTTP 432 after ~90 searches in ~3 min. Pace: chunk ~15 projects per
     execute_code run (3 queries each), sleep 0.4–1.5 s between, retry with backoff on
     empty results. Don't hammer.
2. **browser_use_cloud** — best when credits available; real browser reads the actual
   listing page (posted-by name + posted date verified). Batch ~6 projects per task, ask
   for URL/price/area/psf/posted-by/posted-date, max_steps 80–90, both portals. It hits
   captchas on 99acres sometimes; MagicBricks works better. Costs credits fast — budget
   ~10 listings per project if it runs out mid-batch, fall back to Tavily.
3. **Apify presets** — `magicbricks-99acres` city scrape returns ~1 irrelevant item;
   don't rely on it for per-project work. Custom codingfrontend actors
   (`magicbricks-property-search-scraper`, `99acres-projects-search-scraper`) need
   `maxItems` at run level; the `apify_run_actor` wrapper fails for PAY_PER_EVENT actors
   with `max-items-must-be-greater-than-zero`. Direct API calls need the payment header.
   Only worth it with credits and the SDK.
4. **NOT usable from the VPS**: direct curl / Playwright / smart_browser / web_extract —
   both portals serve `Access Denied` from Akamai edge for datacenter IPs (HTTP 403 /
   `errors.edgesuite.net`). Don't waste attempts; the blocking is IP-based, not header-based.

## Parser pitfalls (learned the hard way)
- `parse_area` grabbing the FIRST `NNNN sqft` in a description often grabs the **project
  total area** (3256, 4450, 5888…) instead of the unit area → garbage psf (e.g. ₹1,150,
  ₹1,560, ₹3,256). Fix: only trust an **explicit ₹X/sqft** pattern
  (`₹ 11,959 / sqft`, `₹16,588 per sq.ft`, `10.8 k /sq ft`) OR price/area where
  area ≤ 6000 sqft, and sanity-band psf 3000–60000.
- Parse posted-by from `Posted by: NAME (role)`, `Agent: NAME`. Rare in snippets; browser
  capture is the reliable source. Where blank, leave blank — do NOT fabricate.
- Same-name pollution: Embassy Grove → Rustam Bagh (Old Airport Rd) project exists; verify
  the locality qualifier in the URL before trusting the value.
