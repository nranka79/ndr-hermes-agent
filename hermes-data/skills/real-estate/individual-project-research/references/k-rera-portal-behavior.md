# K-RERA Portal Access Behavior

Observed August 2026. VPS IP range 91.99.219.x, no residential tunnel.

## Portal URLs

| URL | browser_navigate | smart_browser | Notes |
|-----|-----------------|---------------|-------|
| `https://rera.karnataka.gov.in/` | ✓ Works | n/a | Homepage in Kannada. Click "English" link to switch. Full navigation tree accessible. |
| `https://rera.karnataka.gov.in/projectSearch` | ✗ "Error Page" — only "Home Page" link | ✗ Silent failure (7 steps, null result) | No search form renders. Browser-use agent sees empty page and can't fill forms. |
| `https://rera.karnataka.gov.in/projectSearchDetails` | ✗ "Error Page" | n/a | |
| `https://rera.karnataka.gov.in/services` | ✗ "Error Page" | n/a | |
| `https://rera.karnataka.gov.in/projectViewDetails` | ✗ "Error Page" | n/a | |
| `https://rera.karnataka.gov.in/certificate?CER_NO=<RERA>` | ✗ HTTP timeout (curl: HTTP 000, browser: "Error Page") | ✗ Silent failure | PDF download endpoint. Times out from both VPS curl and all browser tools. |

## Route-tested results (2026-08-28)

All routes tested during a single session:
- **Direct curl:** 91.99.219.247 — K-RERA cert endpoint: HTTP 000 timeout
- **SOCKS5 curl** (`-x socks5h://hermes-utilities:1000`): Same IP 91.99.219.247 — same timeout
- **browser_navigate** (agent-browser + Chromium via SOCKS5): K-RERA homepage ✓, subpages ✗
- **smart_browser** (browser-egress Docker container): K-RERA search ✗ (silent failure)

## What works
- Homepage navigation (Kannada and English)
- Clicking "KNOW PROJECT STATUS" on homepage → leads to empty page (no search form rendered)
- Clicking "DEFAULT PROJECT LIST" on homepage → leads to empty page (no table rendered)
- The "English" / "ಕನ್ನಡ" toggle link on the top banner

## What doesn't work
- Project search by RERA number (all tools)
- Project detail pages by detail_id
- Certificate PDF download (all tools, all routes — likely geo-blocked at India-only IP range)
- Plan downloads (layout, site, elevation, section, brochure)

## Root cause
The K-RERA portal (and most Indian government portals) serves different content based on the requesting IP. Datacenter IP ranges (Hetzner, AWS, GCP, Azure) are either blocked entirely or receive a stripped-down "Error Page" for all internal routes. Only the static homepage loads. This is classic geo-blocking / IP reputation filtering, not a JavaScript rendering issue.

## What to tell the user
"K-RERA portal is geo-blocked from this VPS. The homepage loads but all project search, details, and certificate/PDF download endpoints return 'Error Page' or time out. These routes require an Indian residential/business ISP IP. You can access them directly from your phone or office internet at https://rera.karnataka.gov.in — search by RERA number and click 'View Details' for the project, where you'll find the plans under the 'Documents' tab."

## Alternative sources for RERA data (tested this session)

### Housystan.com
- URL pattern: `https://housystan.com/project/rera/<project-slug>`
- Results: 404 for many villa projects. Footer shows generic RERA disclaimer, not project-specific.
- Known 404s: goyal-riviera-uno, goyal-royale-ville
- Status: Unreliable for villa/row-house projects

### PropNewz.com
- URL pattern: `https://www.propnewz.com/new-projects/<project-slug>-<id>`
- Results: "Page Not Found" for villa projects tested
- Status: Unreliable for villa/row-house projects

### Google Search
- URL: `https://www.google.com/search?q=<RERA+NUMBER>`
- Status: BLOCKED — VPS IP redirects to CAPTCHA page at `/sorry/index?continue=`
- The CAPTCHA page shows: IP address, Time, URL — no way to bypass without residential proxies

### Google News RSS
- URL: `https://news.google.com/rss/search?q=<RERA+NUMBER>`
- Status: WORKS from VPS IP
- May have news articles about the project if it's in the news

### Developer website
- Some developers (e.g., Daiwik Housing at daiwikhousing.com) have their own project pages with pricing and configs
- No RERA plans available on developer websites — only marketing information
- Daiwik website worked from VPS IP (simple non-blocking hosting)

## RERA Numbers Found This Session

| Project | RERA No | Status |
|---------|---------|--------|
| Daiwik Salvina Sapphire | PRM/KA/RERA/1250/304/PR/180808/001975 | Approved (completion expired 04/03/2020) |
| Goyal Riviera Uno (Sol & Luna) | PRM/KA/RERA/1250/304/PR/060225/007489 | Under Construction (possession Jan 2030) |
| Godrej Soukya Road | None | Pre-launch |
| Prestige Row Houses Devanahalli | None | Pre-launch |
| Goyal Royale Ville | Not found | Early stage |

## RERA search endpoint (from K-RERA homepage behavior)

The homepage has links:
- "DEFAULT PROJECT LIST" (ref=e13) — leads to empty page
- "KNOW PROJECT STATUS" (ref=e14) — leads to empty page
- Neither renders any interactive search form

The K-RERA project search probably uses a POST-based search endpoint that is behind the same geo-block as the rest. Without the actual search form JavaScript loading, the search cannot be triggered programmatically.

## Recommendations for future sessions

1. **Automated access is blocked for K-RERA deep pages.** Do not burn retries. One try per tool per URL is sufficient.
2. **smart_browser fails differently from browser_navigate** — failure mode is silent (null result) rather than an error page. Always try smart_browser once if browser_navigate fails — it's a separate container with a different rendering engine and might succeed where the other doesn't.
3. **Nominate manual download** as the primary path: the user (or a colleague on Indian residential ISP) accesses rera.karnataka.gov.in → navigates to project search → enters RERA number → opens project details → downloads plans from the "Documents" tab.
4. **GPS coordinates are NOT available on K-RERA.** RERA registration doesn't include GPS for most Karnataka projects. Get GPS from:
   - Embedded Google Maps iframes on marketing partner websites (works for pre-launch projects)
   - Google Maps search by address
   - Nominatim/OSM API if address is available