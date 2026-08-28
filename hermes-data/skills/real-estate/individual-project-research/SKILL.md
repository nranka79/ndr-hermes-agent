---
name: individual-project-research
description: "Complete R&D for a specific real estate project: extract RERA info + plans, search listings for pricing, create project info doc + pricing spreadsheet. Covers pre-launch and RERA-registered projects. Also handles multi-competitor research runs. Codified 2026-08-26 by NDR."
version: 1.2.0
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

- **Tavily API credits** (web_search) — may be exhausted; have fallback ready
- **browser_use_cloud credits** — may be exhausted; have fallback ready
- **browser_navigate** — works from VPS IP but NO residential proxies by default (stealth=local only); many sites return Access Denied
- **Google Drive access** — via `tools.gws_auth.build_service('drive', 'v3', service_name='google-draas')`
- **Jina Reader proxy** (r.jina.ai) — requires API key (no key = 401)
- **Curl from terminal** — VPS IP (91.99.219.247 range), no tunnel SOCKS on 1080 by default
- **Tavily out-of-credits fallback** → direct browser_navigate + tunnel curl (if tunnel available) + smart_browser (if credits available)

### Current system state (Aug 2026, under maintenance):
- **SOCKS5 proxy** (`AGENT_BROWSER_PROXY=socks5://hermes-utilities:1000`) exists but as of last test (Aug 28) egressed from the **same VPS IP** (91.99.219.247). Verified: both direct curl and `curl -x socks5h://hermes-utilities:1000 https://api.ipify.org` return the same IP. NDR confirmed the routing algorithm was being updated as of Aug 28 — re-test after the fix is applied.
- **Domain-policy router design:** The intended architecture routes residential-listed domains (MagicBricks, NoBroker, rera.tn.gov.in) through a Bengaluru residential node while non-listed domains exit from the VPS IP. This means IP echo tests do NOT confirm or deny tunnel health — always test against the actual portal domain. If this router becomes operational, the blocked-portal situation below may resolve for some sites.\n- **No tunnel-router service** exists on this system (found in AGENTS.md documentation but not deployed). Camofox container also not deployed.
- **smart_browser** (browser-egress container, Chromium + browser-use): runs from VPS IP. K-RERA, MagicBricks, all block. Failed silently on K-RERA search (7 steps, no result).
- **browser_navigate** (agent-browser CLI, local Chromium headless-shell): runs WITHOUT residential proxies (accessibility tree warning confirms). K-RERA homepage loads fine (Kannada/English), but projectSearch and services sub-URLs return "Error Page". Google returns CAPTCHA page (`/sorry/index?continue...`).
- **browser_use_cloud**: requires separate API credits — may be exhausted
- **Major portals** (MagicBricks, 99acres, Housing.com): return "Access Denied" from VPS IP via browser_navigate
- **Housystan.com**: accessible, but project-specific RERA pages return 404 for many projects
- **K-RERA certificate PDF** endpoint: `https://rera.karnataka.gov.in/certificate?CER_NO=<RERA>` — times out (HTTP 000) from both VPS curl and browser_navigate. smart_browser also fails.
- **Pricing discovery constraint**: MagicBricks API blobs (SERVER_PRELOADED_STATE_) only accessible from the tunnel SOCKS (which exits at the same VPS IP and is also blocked). No reliable automated pricing extraction from any Indian property portal.

### Verification practice before reporting "blocked"
Try each browser tool (browser_navigate, smart_browser, browser_use_cloud if credits available) at least ONCE before concluding a URL is inaccessible. Different tools route differently — browser_navigate goes through local Chromium + SOCKS5 proxy, smart_browser goes through a separate browser-egress Docker container. One may work where another fails. Document which tool was tried and what error/response was received.

## Step 1: Identify the project

Start with the URL or project name the user provides.

- If a URL is given, open it via browser (browser_navigate) or curl through tunnel
- Search aggregator sites: housystan.com, propnewz.com, godrejsoukyaroad.com, etc.
- Extract: project name, developer, RERA number if available

## Step 2: Extract RERA Information

### If RERA-registered:
1. Go to rera.karnataka.gov.in via browser_navigate
2. Switch to English (click the "English" link on the top banner)
3. **Known limitation:** The /projectSearch and /services sub-URLs return "Error Page" from VPS IP. The homepage "KNOW PROJECT STATUS" link also leads to an empty page.
4. **Working alternative:** Use the RERA certificate URL directly:
   `https://rera.karnataka.gov.in/certificate?CER_NO=<RERA_NUMBER>`
   - NOTE: This PDF download times out from VPS IP (HTTP 000). The page loads as "Error Page" in browser_navigate.
   - **Manual step required:** Ask user to download from the portal manually
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

### Method 1: MagicBricks (if tunnel SOCKS available - may not be)
```bash
curl -s --socks5-hostname hermes-utilities:1000 -A "Mozilla/5.0 ..." \
  "https://www.magicbricks.com/villa-for-sale-in-<locality>-bangalore-pppfs"
```
Extract listing prices from `SERVER_PRELOADED_STATE_` JSON blob.

### Method 2: Browser navigate (VPS IP - likely Access Denied)
- MagicBricks, 99acres, Housing.com all return "Access Denied" from VPS IP
- Google Search blocks VPS IP with CAPTCHA
- **Try anyway** — sometimes works for less popular portals or specific sub-pages

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
- **browser_use_cloud credits may be exhausted**: Fall back to browser_navigate from VPS IP (limited success) or smart_browser
- **browser_navigate blocking**: Browser_navigate runs local Chromium + SOCKS5 proxy (hermes-utilities:1000). The SOCKS5 proxy exits from the same VPS IP (91.99.219.247) — no residential exit. Sites that block the VPS IP will also block the SOCKS5 path.**
- **smart_browser blocking**: Smart_browser runs in a separate browser-egress Docker container. It ALSO exits from the VPS IP. Sites that block via IP will also fail here. The failure mode is different from browser_navigate (silent agent failure vs "Access Denied" page) — so always try it once before concluding a URL is inaccessible.**
- **Tool-by-tool blocking differences**: Different browser tools fail differently on the same URL — browser_navigate shows "Access Denied" or "Error Page", smart_browser fails silently (returns null with no error), browser_use_cloud would succeed if credits available. Always try at least 2 tools before reporting a URL as blocked.**
- **"Try before concluding" rule**: When NDR asks why something was blocked, do NOT answer from memory/knowledge alone. Actually try the tools (browser_navigate, smart_browser, curl with SOCKS5) and verify the IP egress. Show the actual error/output received and the IP check result (`curl -x socks5h://hermes-utilities:1000 https://api.ipify.org` vs direct `curl https://api.ipify.org`). NDR expects demonstrated results, not remembered constraints.**
- **Cloudflare on project websites**: Try aggregator sites (Housystan, PropNewz) or Google Maps listing
- **99acres blocked**: Akamai even through tunnel; skip or use Google snippets  
- **Housing.com blocked**: WAF even through tunnel; skip or use Google snippets
- **Google Search blocks VPS IP**: Returns CAPTCHA page on `/sorry/index?continue...` — cannot use google.com from terminal curl or browser_navigate
- **K-RERA certificate PDF**: The `/certificate?CER_NO=` endpoint times out (HTTP 000) from both VPS curl and browser_navigate — user must download manually
- **K-RERA project search sub-URLs**: `/projectSearch`, `/projectSearchDetails`, `/services` all return "Error Page" — only the homepage works
- **Housystan RERA pages**: `/project/rera/<slug>` returns 404 for many projects — don't rely on this
- **MagicBricks from VPS IP**: "Access Denied" — no way to scrape pricing. Use alternative sources (developer website, previous data, market estimates) and mark data as estimated
- **sellerName/API data from MagicBricks**: Only accessible via tunnel curl with matching User-Agent. From VPS IP, even the page is blocked
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