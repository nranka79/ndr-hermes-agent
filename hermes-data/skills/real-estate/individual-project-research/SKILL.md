---
name: individual-project-research
description: "Complete R&D for a specific real estate project: extract RERA info + plans, search listings for pricing, create project info doc + pricing spreadsheet. Covers pre-launch and RERA-registered projects. Also handles multi-competitor research runs. Codified 2026-08-26 by NDR. Updated 2026-08-28: real-browser over curl, tunnel/IP state corrected."
version: 1.3.0
author: NDR, Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [real-estate, research, rera, pricing, spreadsheet]
    category: real-estate
---

# Individual Project Research Skill

End-to-end R&D for a specific real estate project. Given a project name/URL/link,
produce three deliverables: (1) project info document with RERA details + GPS, 
(2) RERA plan downloads (layout, elevation, section, brochure), (3) pricing 
spreadsheet with 5+ listings from multiple portals.

## Prerequisites

- **Headless browser** (`browser_navigate` / `smart_browser`) — PREFERRED over curl. Real Chromium fingerprints pass Akamai/WAF on MagicBricks, 99acres, Housing.com from any exit IP; curl's fingerprint gets "Access Denied" from every IP, even residential.
- **Tavily API credits** (web_search) — may be exhausted; have fallback ready
- **browser_use_cloud credits** — may be exhausted; have fallback ready
- **Google Drive access** — via `tools.gws_auth.build_service('drive', 'v3', service_name='google-draas')`
- **Jina Reader proxy** (r.jina.ai) — requires API key (no key = 401)
- **Tavily out-of-credits fallback** → `browser_navigate` (headless browser, prefers residential route) then `smart_browser`. Prefer browser tools over curl.

### Current system state (Aug 2026, verified 2026-08-28):
- **Tunnel router is OPERATIONAL.** Residential-listed domains (MagicBricks, 99acres, rera.karnataka.gov.in, google/bing/duckduckgo, etc.) egress through a connected residential node; everything else defaults to `direct` (VPS IP). Verify with a **listed** echo endpoint, e.g. `curl -s --socks5-hostname hermes-utilities:1000 https://ifconfig.me` → residential node IP; NOT `api.ipify.org` (not in the residential list → correctly shows the VPS IP; that is expected, not a bug).
- **Blocking is client-fingerprint, not IP.** Akamai (MagicBricks/99acres) returns "Access Denied" for curl/minimal-header requests from *any* exit (VPS or residential), and 200 for a real browser header set from the *same* IP. The residential node's own browser works fine on these sites.
- **smart_browser** (browser-egress container, Chromium + browser-use): routes via the tunnel's SOCKS5; real browser fingerprint. Verify its LLM is not rate-limited (opencode-go key rotation + OpenRouter fallback configured).
- **browser_navigate** (agent-browser CLI, local Chromium headless-shell): real browser fingerprint; uses `AGENT_BROWSER_PROXY` tunnel SOCKS when set.
- **K-RERA** (rera.karnataka.gov.in): intermittently very slow (60–160 s connections observed) — retry and allow long timeouts; the site itself, not the route, is the bottleneck.
- **Housystan.com**: accessible, but project-specific RERA pages return 404 for many projects
- **Pricing discovery**: use the headless browser to load portal pages (full browser headers); extract listing prices from the page/`SERVER_PRELOADED_STATE_`. Avoid raw curl for portals that Akamai/WAF-protect.

### Verification practice before reporting "blocked"
Try each browser tool (browser_navigate, smart_browser, browser_use_cloud if credits available) at least ONCE before concluding a URL is inaccessible. Different tools route differently — browser_navigate goes through local Chromium + SOCKS5 proxy, smart_browser goes through a separate browser-egress Docker container. One may work where another fails. Document which tool was tried and what error/response was received. Always prefer the real-browser tools; a raw curl result is not evidence that the site is blocked for a browser.

## Step 1: Identify the project

Start with the URL or project name the user provides.

- If a URL is given, open it via a headless browser (browser_navigate or smart_browser) — not curl (curl fingerprints get blocked by Akamai/WAF)
- Search aggregator sites: housystan.com, propnewz.com, godrejsoukyaroad.com, etc.
- Extract: project name, developer, RERA number if available

## Step 2: Extract RERA Information

### If RERA-registered:
1. Go to rera.karnataka.gov.in via browser_navigate or smart_browser (headless browser, residential route)
2. Switch to English (click the "English" link on the top banner)
3. **Known behavior:** The /projectSearch and /services sub-URLs may intermittently return "Error Page" — K-RERA is slow/unreliable (60–160 s connections observed); retry with long timeouts rather than concluding blocked.
4. **Working alternative:** Use the RERA certificate URL directly:
   `https://rera.karnataka.gov.in/certificate?CER_NO=<RERA_NUMBER>`
   - May time out on the first try; retry. If it still fails after retries, ask the user to download from the portal manually.
5. **Aggregator sites** (may have some RERA info):
   - Housystan.com: try `/project/rera/<project-name-slug>` — may 404
   - PropNewz.com: try `/new-projects/<project-slug>` — may 404
6. Extract from any available source: project type/subtype, land area, status, completion date, promoter name

### If pre-launch (no RERA):
- Record that RERA is pending / not registered
- Collect info from aggregator websites, developer website, marketing partner sites
- Note: no RERA plans to download
- **Critical:** Pre-launch URLs often belong to channel partners (Assettrust, etc.), not the developer. Cross-reference developer name, project name, and contact info. Look for the RERA advertiser registration disclaimer at the page footer.
- **Marketing partner site detection:** Check the URL domain — does it match the developer's brand? (e.g., newlaunches-devanahalli.com ≠ prestigeconstructions.com). Footer disclaimers about channel partnerships are the giveaway.

## Step 3: GPS Coordinates

- **If RERA-registered:** K-RERA does NOT display GPS coordinates in project details. Do not expect to find them on the portal.
- **If pre-launch (or any project with a website):** Check the project website for embedded Google Maps iframes. The embed URL contains the coordinates directly.
  - Extract with browser_console:
    ```javascript
    document.querySelectorAll('iframe[src*="google.com/maps"]').forEach(el => console.log(el.getAttribute('src')))
    ```
  - Embed URL patterns:
    - `?q=<lat>,<lon>` (standard)
    - `@<lat>,<lon>,<zoom>z` (modern)
    - `!2d<lon>!3d<lat>!` (old pb format — longitude BEFORE latitude)
  - Fallback: `browser_vision` asking "find the Google Maps iframe and tell me its coordinates"
  - **Known working example:** newlaunches-devanahalli.com had Google Maps iframe showing 13.202971, 77.668530
- **Use Nominatim/OSM API (free, no key):**
  ```bash
  curl -s "https://nominatim.openstreetmap.org/search?q=<Project+Name+Bangalore>&format=json&limit=1"
  ```
  NOTE: Aggressive rate-limiting. Works for landmark-based searches, not project names.
- **Create Google Maps link:**
  - If coordinates known: `https://www.google.com/maps?q=<lat>,<lon>`
  - If only address known: `https://www.google.com/maps/search/<encoded-address>` — mark as approximate
- **Cross-reference tip:** Pre-launch marketing partner sites often embed a Google Maps pin that's approximate (may border competitor sites). Verify against the address/locality text in the page body, not just the pin location.

## Step 4: Pricing Discovery

### Method 1: Headless browser (PREFERRED)
Load the portal listing page with a real browser — `browser_navigate` or `smart_browser` (both go through the residential route for portal domains, and both present a real Chromium fingerprint that Akamai/WAF accepts):
- `browser_navigate("https://www.magicbricks.com/villa-for-sale-in-<locality>-bangalore-pppfs", ...)`
- Same for 99acres, Housing.com, NoBroker, etc.
Extract listing prices from the rendered page, or from the `SERVER_PRELOADED_STATE_` JSON blob in the page source if present.
If browser tools fail, curl with a FULL browser header set (User-Agent + Accept + Accept-Language + sec-ch-ua + Sec-Fetch-*) through the tunnel works from residential IPs:
```bash
curl -s --socks5-hostname hermes-utilities:1000 \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36" \
  -H "Accept: text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8" \
  -H "Accept-Language: en-US,en;q=0.9" \
  -H "sec-ch-ua: \"Chromium\";v=\"151\", \"Google Chrome\";v=\"151\", \"Not:A-Brand\";v=\"24\"" \
  -H "sec-ch-ua-mobile: ?0" -H "sec-ch-ua-platform: \"Windows\"" \
  -H "Sec-Fetch-Dest: document" -H "Sec-Fetch-Mode: navigate" -H "Sec-Fetch-Site: none" -H "Upgrade-Insecure-Requests: 1" \
  "https://www.magicbricks.com/villa-for-sale-in-<locality>-bangalore-pppfs"
```
A bare `-A "Mozilla/5.0 ..."` curl (no other headers) is NOT enough — it still gets "Access Denied" from every IP.

### Method 2: Browser navigate (real browser, residential route)
- Use browser_navigate/smart_browser first; these present a real browser fingerprint and work on MagicBricks, 99acres, Housing.com.
- Google Search may still CAPTCHA from some IPs; prefer Bing/DuckDuckGo (residential-listed) or browser-based Google.
- **Try anyway** — real browsers sometimes work where curl-based attempts failed.

### Method 3: Developer's own website
- Daiwikhousing.com, Godrej properties site, etc.
- May have indicative pricing, unit configuration, and contact info

### Method 4: Previous research data
- If this is a project from a prior session, search session history for pricing
- Use session_search("project name pricing") to find earlier data

### Method 5: Market estimates
- State clearly that these are estimates, not verified portal listings
- Use known comparable rates from the same corridor

### For each listing, track:
- BHK configuration
- Total super built-up area
- Total asking price
- Rate per sqft = total_price / area
- Listed by (broker/agent/developer)
- Individual listing URL (or note if unavailable)
- Source of the data
- Any notes about reliability

### Minimum: 5 listings across project(s)
- But accept available data when portals are blocked
- Document the data source and limitations clearly
- Use "N/A - Portal blocked" for unavailable URLs

## Step 5: Create Deliverables

### A. Project Info Document (Markdown)

For a single project, include:
- Project name, developer, RERA no (or "Not Registered / Pre-Launch"), land area, unit configs
- GPS coordinates + Google Maps link
- Website URL, source of data
- RERA plan availability status

For multi-competitor research, create ONE consolidated document with:
- A section per competitor project
- Summary comparison table at the end (developer, size, units, price range, rate/sqft, RERA, status)
- Notes on data gaps for each project

### B. Pricing Spreadsheet (XLSX)

Two sheets:
1. **Pricing Data** — complete listing table with columns:
   # | Project | Listing URL | Seller Type | Type | Super Built-up (sqft) | Ask Price (Rs) | Rate/sqft | Source | Notes
2. **Summary** — per-project summary:
   Project | RERA No. | Min Rate | Max Rate | Avg Rate | Price Range | Status | RERA Status

For multi-competitor research: place ALL projects' listings in one Pricing Data sheet with project name in column B, separated by colored section headers. Summary sheet has one row per project.

## Step 6: WhatsApp Message Delivery (if requested)

When NDR asks you to send or share competitor research details via WhatsApp:

1. **Identify the recipient** — use `contact_resolver` with the person's name and project context. The recipient may NOT be in NDR's contacts (e.g., Dishan Prakash, Assudani, etc.). If not found, ask NDR for the phone number. Do NOT guess or skip.

2. **Compose the message** — include these key details:
   - Project name and developer
   - Pricing range and rate per sqft (e.g., "Rs 25,000-26,000/sqft")
   - Location context (e.g., "opposite where we intend to launch Ashok G's Palya land as row villa")
   - Google Maps link for the project (from GPS coordinates found in Step 3)
   - RERA status, unit config, land area

3. **Generate the WhatsApp link** — use the `whatsapp_link` tool with the recipient's full phone number (country code included) and the message text. NEVER construct a WhatsApp URL manually.

4. **Deliver the link to NDR** — paste it in the response so he can tap to open WhatsApp with the message pre-filled.

5. **If contact not found in resolver**: tell NDR explicitly that the person isn't in his contacts sheet, share the draft message text for review, and ask for the phone number.

## Step 7: Upload to Drive

- Use `tools.gws_auth.build_service('drive', 'v3', service_name='google-draas')`
- Create folder under TMP root
- Upload project info doc (markdown or text)
- Upload pricing spreadsheet (xlsx)
- Return Drive URLs to user

## Pitfalls

- **Pre-launch projects have no RERA**: Don't expect to find plans; clearly flag this in deliverables
- **Marketing partner websites**: Pre-launch projects often have URLs that don't match the developer's official domain (e.g., newlaunches-devanahalli.com for Prestige). Always cross-reference developer name, project name, and contact info. Look for the RERA advertiser registration and channel partner disclaimer at the bottom of the page.
- **Meta keywords can be misleading**: Some marketing partner sites reuse templates from other developers (e.g., "Godrej" keywords appearing on a Prestige page). Don't trust meta data blindly - verify project identity from body content and branding.
- **Embedded Google Maps iframes**: For pre-launch projects, these often contain the actual GPS coordinates. Extract lat/lon from the embed URL (format: `?q=<lat>,<lon>`).
- **Competitor pricing from different areas**: When doing multi-project R&D, clearly note which projects are in the same locality vs. "nearby" but actually in different suburbs (e.g., Soukya Road projects vs. Devanahalli projects are 15-20 km apart). Tag them clearly in deliverables.
- **Tavily credits may be exhausted**: Fall back to browser_navigate or search sites directly
- **browser_use_cloud credits may be exhausted**: Fall back to browser_navigate or smart_browser
- **Curl fingerprint ≠ blocked site**: Akamai/WAF "Access Denied" for curl is a client-fingerprint rejection, NOT an IP block. A bare-`-A` curl 403s from residential IPs too; a real browser (or curl with full browser headers) returns 200 from the SAME IP. Never conclude "site blocked" from a curl result alone.**
- **Real-browser tools route residential**: browser_navigate (AGENT_BROWSER_PROXY) and smart_browser (browser-egress SOCKS5) both go through the tunnel SOCKS for residential-listed portal domains — the same residential node you use at home.
- **K-RERA is slow, not blocked**: rera.karnataka.gov.in intermittently takes 60–160 s per connection. Retry with long timeouts before concluding failure; this is the site's own slowness, not the tunnel.**
- **Tool-by-tool blocking differences**: Different browser tools fail differently on the same URL — browser_navigate may show "Access Denied"/"Error Page", smart_browser may fail silently (returns null with no error). Always try at least 2 tools before reporting a URL as blocked.**
- **"Try before concluding" rule**: When NDR asks why something was blocked, do NOT answer from memory/knowledge alone. Actually try the tools (browser_navigate, smart_browser) and verify the result. Show the actual error/output received. NDR expects demonstrated results, not remembered constraints.**
- **Cloudflare on project websites**: Try aggregator sites (Housystan, PropNewz) or Google Maps listing
- **99acres**: works with real-browser fingerprint; curl-style requests 403. Use browser tools.  
- **Housing.com**: WAF-protected against curl; use browser tools.
- **Google Search CAPTCHA**: may appear from some IPs; prefer Bing/DuckDuckGo (residential-listed) or retry via browser.
- **K-RERA certificate PDF**: The `/certificate?CER_NO=` endpoint may be slow/timeout on first try; retry with long timeout. Ask the user to download manually only after retries fail.
- **K-RERA project search sub-URLs**: `/projectSearch`, `/projectSearchDetails`, `/services` may intermittently return "Error Page" — retry.
- **Housystan RERA pages**: `/project/rera/<slug>` returns 404 for many projects — don't rely on this
- **MagicBricks pricing**: works via real-browser tools or curl-with-full-browser-headers through the residential route. Mark data as estimated only if unverifiable.
- **Voice transcription errors**: NDR uses voice input. Common corrections in this domain:
  - "Rovala" → "Row Villa"
  - "Goodridge" → "Godrej"  
  - "Saukaya" → "Soukya"
  - "Roor" → "Soukya Road"
  - "Tars" → "Towers"
  - "Riyaga" → "Riya Gawri"
  - Always apply these corrections silently — never repeat the original voice error back to the user
- **BHK and area fields**: Extract from URL path using regex, not from preloaded state
- **MagicBricks URL format**: `propertyDetails/<slug>&id=<hex>` where id = hex of "MB"+decimal
- **MagicBricks locality slugs**: Use lowercase with hyphens (e.g. `whitefield-bangalore`)
- **Contact not in NDR's address book**: If the user asks for a WhatsApp message to someone (e.g., "Dishan Prakash"), first check contact_resolver. If not found, ask the user for the phone number rather than guessing or skipping
- **WhatsApp message link**: After completing pricing research, if the user asks for a WhatsApp message about a competitor, use the `whatsapp_link` tool (never construct wa.me links manually)
- **GPS from heard/mentioned source**: Don't trust "lat/lon from RERA website" if you haven't actually extracted it. If RERA portal doesn't display GPS, use embedded Google Maps iframes from the project's website or Google Maps search