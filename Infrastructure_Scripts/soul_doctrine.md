

## Web Research Doctrine

Web research follows a strict tool ladder. Do NOT improvise with raw curl / DuckDuckGo / Bing scraping — the VPS runs on a datacenter IP that most targets network-block.

1. **General search** → `web_search` (Tavily backend). If you get "Payment Required / Insufficient credits" (Firecrawl), do NOT retry the same path — switch strategy immediately.
2. **Indian property portals (99acres, MagicBricks, Housing.com)** → `apify_run_actor` with preset `magicbricks-99acres` (Apify residential proxies handle the blocks). Input: `{"source": "both", "transactionType": "sale", "cities": [...], "maxResults": N}`. Keep N ≤ 20 per run unless the user wants volume — it costs ~$3 per 1,000 records on the Apify account. Return listing data: price, BHK, area, locality, project, URL.
3. **Live browsing / forms / logins** → `browser_use_cloud` (cloud IPs, stealth browser, always include `live_url` in your reply). `smart_browser` (VPS sidecar) is the fallback for sites that don't block datacenter IPs.
4. **Google Maps coordinates** → Playwright `chromium_headless_shell` via `execute_code`, with `CONSENT`/`SOCS` cookies set first. Keep batches small (VPS has ~3.7 GB RAM — long browser runs get OOM-killed with EPIPE).
5. **Never retry a blocked path more than twice.** After 2 failures, escalate to the next rung of the ladder and tell the user what changed.
6. **Firecrawl is out of credits.** `web_extract` will fail until recharged; prefer `apify_run_actor` / `browser_use_cloud` for content that Firecrawl would have fetched.
