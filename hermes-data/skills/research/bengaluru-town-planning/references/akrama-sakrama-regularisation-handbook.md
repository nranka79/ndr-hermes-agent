# Akrama-Sakrama / Sadaavakasha Regularisation Handbook (BBMP/UDD)

## What it is
- Official title (cover, Kannada): ಅನಧಿಕೃತ ಅಭಿವೃದ್ಧಿ ಅಥವಾ ನಿರ್ಮಾಣಗಳನ್ನು ಸಕ್ರಮಗೊಳಿಸುವಿಕೆ ಕುರಿತು ಕೈಪಿಡಿ = **"Handbook Regarding Regularization of Unauthorized Developments or Constructions"**
- Issued by: **Urban Development Department, Government of Karnataka** + **Bruhat Bengaluru Mahanagara Palike (BBMP)**
- Subtitle: Instructions / Guidelines and Application Forms for Applicants (ಅರ್ಜಿದಾರರಿಗೆ ಸೂಚನೆ / ಮಾರ್ಗದರ್ಶನಗಳು ಮತ್ತು ಅರ್ಜಿ ನಮೂನೆಗಳು)
- Scheme name on cover: **"Sadaavakasha"** (ಸದಾವಕಾಶ); edition **2015-16**
- Content: provisions of **Sec 76-FF KTCP Act 1961** (its sub-sections (2)-(14) apply mutatis mutandis to BBMP regularisation per s.249 of BBMP Act 53 of 2020), **Sec 321A KMC Act 1976**, **Sec 187A KM Act 1964**, plus application forms and fee tables.

## Official sources
- UDD Karnataka PDF (found via Google Kannada-title query): `https://udd.karnataka.gov.in/uploads/media_to_upload1741687877.pdf`
- Related statutes on BBMP site (`site.bbmp.gov.in`):
  - KTCP Act 1961 full text: `https://site.bbmp.gov.in/documents/Karnataka%20Town%20and%20Country%20Planning%20Act%201961.pdf`
  - BBMP Act 2020 (53 of 2020): `https://site.bbmp.gov.in/PDF/53of2020(E)29of2022.pdf` — s.249 regularisation, references 76-FF
- English mirror of the handbook: Scribd "Handbook-Akrama-Sakrama-eng-pdf" (doc 402347622) / "English-Akrama-Sakrama" (doc 335522537)
- Underlying statute: Karnataka Regularisation of Unauthorised Constructions in Urban Areas Act 1991 (Act 29 of 1991), PDF on `dpal.karnataka.gov.in`

## Egress notes (IMPORTANT)
- `bbmp.gov.in`, `site.bbmp.gov.in`, `karnataka.gov.in`, `udd.karnataka.gov.in`, `dpal.karnataka.gov.in` ALL block the Hermes VPS datacenter IP — curl returns HTTP 000, `web_extract` times out.
- Reachable via **Apify residential proxies** (`apify_run_actor` with `proxyConfiguration: {useApifyProxy: true, apifyProxyGroups: ["RESIDENTIAL"], apifyProxyCountry: "IN"}`).
- `browser_use_cloud` had $0 credits (Aug 2026) — check balance before relying on it; `smart_browser` sidecar timed out on this task.
- There is **NO separately configured residential proxy / client node** on the box (no SSH config, WireGuard, Tailscale, tunnels, proxy env vars). The Apify residential pool IS the residential route — when the user says "route via our residential node", that is what exists.

## Search recipe (how the official PDF was found)
- Regular `web_search` (Tavily) is weak on Kannada queries — returns noise.
- Use `apify/google-search-scraper`:
  - `queries` must be a **STRING** (array → HTTP 400 invalid-input)
  - `site:` queries (`site:bbmp.gov.in ಸದಾವಕಾಶ`) returned ZERO organic results
  - the bare Kannada title query `ಅನಧಿಕೃತ ಅಭಿವೃದ್ಧಿ ಅಥವಾ ನಿರ್ಮಾಣಗಳನ್ನು ಸಕ್ರಮಗೊಳಿಸುವಿಕೆ ಕುರಿತು ಕೈಪಿಡಿ` returned the official UDD PDF as result #1
- Apify rate-limits after ~5 quick runs ("All configured APIFY_API_KEY key(s) were rejected") — back off a few minutes rather than retry-looping.
- `apify/website-content-crawler` returned 0 items on a direct PDF URL — don't rely on it to read PDF bodies; use it only for HTML pages.

## Verification of the physical book (Aug 2026)
- User photographed the physical handbook cover. `vision_analyze` OCR garbled it; Gemini 2.5 Flash via OpenRouter transcribed + translated correctly in one call (see SKILL.md §4C for the code pattern).
