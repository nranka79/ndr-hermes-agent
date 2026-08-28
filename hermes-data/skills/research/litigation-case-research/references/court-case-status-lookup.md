# Indian Court Case-Status / Hearing-Outcome Lookup (fallback chain)

Use when the user asks "what happened at the hearing", "case status", "next date" for an Indian court matter and the court's own portal is unreachable.

## Structure of the portals (verified 2026-08)

- **eCourts v6 national portal** (`https://services.ecourts.gov.in/ecourtindia_v6/?p=casestatus`) covers **district courts only** in its state → district → court-complex flow. The **Karnataka High Court is NOT there** — its "High Courts" page links out to the HC's own instance (`judiciary.karnataka.gov.in` / `karnatakajudiciary.kar.nic.in` / `hck.kar.nic.in`), which is frequently down / unreachable / 502. Check `curl -o /dev/null -w "%{http_code}"` before spending time in the browser.
- **Karnataka HC eCourts** is a separate deployment; when down, fall back to news (below). Do not conclude "no data exists" — the case is alive, you just can't see the live docket.

## Fallback chain (in order of reliability, no API keys)

### 1. Google News RSS via curl — best general tool (no captcha, no key, no JS)
```bash
curl -sL -m 30 "https://news.google.com/rss/search?q=<URL-encoded+query>&hl=en-IN&gl=IN&ceid=IN:en" \
  | python3 -c "import sys,re,html; t=sys.stdin.read(); [print('-',html.unescape(re.search(r'<title>(.*?)</title>',it,re.S).group(1))[:100],'|',html.unescape(re.search(r'<pubDate>(.*?)</pubDate>',it,re.S).group(1))) for it in re.findall(r'<item>(.*?)</item>',t,re.S)[:10]]"
```
- Queries that work: case number in quotes (`"WP 38186/2025"`), party names + court + topic (`Ramaswamy cantonment railway PIL`), project + keyword.
- `<link>` entries are Google News redirect IDs — not directly resolvable (400 from urllib; r.jina.ai blocks news.google.com). Use title + pubDate + source; fetch the story from the publisher's own site search instead.

### 2. Publisher search APIs — full text when you need the order detail
**Deccan Herald** (works via plain curl, returns JSON):
- Search: `https://www.deccanherald.com/api/search?q=<query>&size=20` → `results.stories[]` with `headline`, `slug`, `published-at` (epoch ms), `story-content-id`.
- Full story: `https://www.deccanherald.com/api/stories/<story-content-id>` → body text lives in `story.cards[].story-elements[].text` (strip HTML).
- URL for sharing: `https://www.deccanherald.com/<slug>`.
- The Hindu / Indian Express / TOI have no such open API — use Google News RSS to find the headline, then fetch the publisher page via curl with a desktop UA (some bodies are JS-rendered; DH API above is the reliable one).

### 3. Browser search as last resort
- **Bing News** (`bing.com/news/search?q=...`) renders in the browser; results appear in `main#News` — some queries return "No results" for narrow phrasing; simplify the query.
- **Google search** (google.com) captcha-blocks datacenter IPs (`sorry/index` page). **DuckDuckGo lite** shows a "select all squares containing a duck" challenge. **Bing plain** curl returns a JS wall. **Indian Kanoon** sits behind Cloudflare ("Just a moment") — not curl-able. Don't burn cycles retrying these from the server; use Google News RSS instead.

## eCourts v6 form automation notes (when the district-court flow is needed)
- The `<option>` elements are not reliably clickable (`CDP error DOM.getBoxModel`). Instead drive the selects via `browser_console`:
```js
const s = document.getElementById('sess_state_code');
s.value = '3'; // Karnataka
s.dispatchEvent(new Event('change', {bubbles:true}));
// then sess_dist_code = '20' (BENGALURU), then court_complex_code from the populated list
```
- District values are numeric (Karnataka=3, Bengaluru=20) even though labels show text. After each change, take a snapshot to read the newly populated complex list.
- Captcha is required for the actual search — not automatable without vision/OCR; for HC matters the portal is separate anyway, so prefer the news fallback.

### Verified stable code chain (Karnataka → Bengaluru → City Civil) — re-fill in ~90s
- state `3` (Karnataka), district `20` (BENGALURU), complex `1030135` (City Civil Court Complex), establishment `3` (PRL. CITY CIVIL AND SESSIONS JUDGE), O.S. case type `52^3` (`66^3` = Com.O.S.).
- Wait ~1.5s between changes for the dependent dropdowns to populate via AJAX. Check with `Array.from(document.getElementById('X').options).map(o=>o.value+':'+o.text)`.

### Pitfalls driving the form via JS
- **`court_complex_code` value is COMPOUND**: option values look like `1030135@3@Y` (complex@est_codes@flag). Setting the bare `1030135` breaks every downstream call — `fillCaseType` throws `Cannot read properties of null (reading 'split')` because it does `courtArr.split('@')`. ALWAYS set the full compound string: `el.value = '1030135@3@Y'`.
- **Case Type dropdown won't populate until you call `fillCaseType('c_no')`** — and it requires a valid `court_est_code` set first (est `3`), else it silently returns nothing or alerts "Select Establishment". Sequence: set state → dist → complex (full value) → set est code (dropdown auto-populates after complex change; if it's empty, inject `<option value="3">PRL. CITY CIVIL AND SESSIONS JUDGE</option>` manually) → `fillCaseType('c_no')` → then set `case_type` (e.g. `52^3`), `search_case_no`, `rgyear`.
- **Hidden `#active_tab` drives tab logic**: after switching to the Case Number tab via click, set `document.getElementById('active_tab').value = 'casenumber'` before calling fillCaseType.
- Submit via `submitCaseNo()` (not a form POST); on success it renders results into `#case_no_res`.

### Captcha: session-bound — extraction MUST happen inside the page context
- **The captcha image is tied to the PHP session cookie.** `curl`-downloading `securimage_show.php` with a fresh/no cookie jar produces an image whose answer does NOT match the form — always fail. Extract via `fetch()` from `browser_console` so it rides the page's own session. `document.cookie` is usually **empty (HttpOnly)** — do not rely on reading it to build a curl request; the in-page fetch is the only reliable path.
- **Long base64 strings get corrupted in tool transport.** Do NOT paste a full data-URL back to the agent. Fetch the base64, split it into ~500-char chunks stored on `window.__captchaChunks`, read each chunk back separately, write each to `/tmp/cap_chunkN.txt`, then `cat` + `base64 -d`. Verify with PIL (`Image.open` prints size) before sending.
- **Alternative: browser_vision screenshot path** — `browser_vision` returns a `screenshot_path` even when no vision provider is configured (it just fails the analysis part). Crop the captcha region from that PNG with PIL. **The screenshot is at devicePixelRatio scale** (e.g. 1.25): multiply `getBoundingClientRect()` coords by dpr before cropping.
- **Any page reload issues a NEW captcha** — a solved value from a previous page load is invalid. After a session restart, re-extract and re-ask.
- **User-solves-captcha flow** (vision unavailable): send the exact captcha image via `MEDIA:/tmp/captcha_final.png` (upscale 3-4× LANCZOS for readability), ask for the characters, then `document.getElementById('case_captcha_code').value = '<answer>'` and call `submitCaseNo()`. User answers are case-sensitive.
- **DO NOT spend long OCR loops on eCourts captchas.** Multiple tesseract preprocessing passes (threshold, invert, autocontrast, connected-component runs, per-char crops) still give inconsistent reads (e.g. `6Ildpbt` vs `6ldpbt`, `7z8a6ly` vs `28a6ly`). NDR's explicit preference (stated 2026-08-12): *"just give me the image and let me solve the OCR"* — when vision is unavailable, hand the captcha to the user immediately instead of burning turns on OCR. The read can be used as a hint, never as the submit value without user confirmation.

### Browser session drops — the captcha-invalidation loop (biggest time sink)
- The eCourts browser session **drops to `(empty page)` between turns** (observed 3× in one session). Each drop means: re-navigate → refill the whole cascade → **new captcha** → user re-solves. This is the single biggest time sink in the flow — plan around it.
- **Order the work to minimize solve→submit latency**: fill state → district → complex → est → tab → case fields FIRST, extract the captcha image LAST, send it immediately, and on the user's answer go straight to `case_captcha_code.value = ...` + `submitCaseNo()` with zero intermediate browser calls (any navigation/refresh invalidates the solved value).
- **Before submitting a user-solved value, verify the on-screen captcha still matches what they solved**: `fetch()` the current `securimage_show.php` in-page, compare md5 against the image you sent (`md5sum` both sides). If different, re-extract, re-send, re-ask — do not burn a submit on a stale answer.
- **Recognize the drop signal fast**: `browser_snapshot` returning `(empty page)` / `element_count: 0` means the session is gone — don't retry console JS on it, re-navigate to `?p=casestatus/index` and refill.
- The verified re-fill chain (~90s) is above in "Verified stable code chain".

## Pitfalls
- Do NOT report "case disposed / no case found" from a portal outage. State: portal unreachable, verified via news/alternate source.
- News coverage lags: a same-day hearing may have no article yet (observed for 30-Jul-2026 hearing, nothing published by 01-Aug). Say so explicitly and offer to retry the HC portal later.
- Keep the case number in the ask — it is the anchor for every fallback query.
