# Flight Price Research — JavaScript-Rendered Booking Sites

## Problem

Flight booking sites (Air India Express, MakeMyTrip, Yatra, Cleartrip, Google Flights) are JavaScript-rendered. Simple `curl`/`requests` calls return:
- Anti-bot blocks
- Wrong URL errors
- Generic page shells
- API 401/404 (subscription key required)

Getting live fares requires browser automation.

---

## Decision Tree

```
Need flight fare for a route/date?
├── Site has a public API (Skyscanner, Google Flights JSON endpoints)
│   └── → Try direct HTTP API first (fastest)
├── JS-rendered site with bot protection
│   └── → Playwright headless Chromium
└── Need to present link to user
    └── → Generate wa.me HTML card for delivery
```

---

## Confirmed Working: Playwright Headless

Install:
```bash
pip install playwright
python3 -m playwright install chromium
```

Basic pattern:
```python
from playwright.sync_api import sync_playwright
import time

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True, args=['--no-sandbox'])
    context = browser.new_context(
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        viewport={'width': 1440, 'height': 900}
    )
    page = context.new_page()
    page.set_default_timeout(60000)
    
    page.goto(url, timeout=60000)
    time.sleep(10)
    
    page.screenshot(path='/tmp/flight_search.png')
    
    text = page.inner_text('body')
    prices = __import__('re').findall(r'₹\s*[0-9,]+', text)
    
    browser.close()
```

---

## Site-by-Site Findings (June 2026)

### Air India Express (airindiaexpress.com)
- **Status**: JS-rendered, requires form interaction
- **API**: `api.airindiaexpress.com/b2c-flightsearch/v3/` requires subscription key (401 returned)
- **Working approach**: `browser_navigate` to `/flights-from-bengaluru-to-phuket` — page shows origin/destination fields, date picker. Search results render after form submission.
- **What renders**: Prices for Mobikwik offer (₹1000, ₹500), SME discount cap (₹6000) — not actual fares. Actual fare requires selecting BLR→HKT + date + clicking Search.
- **Schedule confirmed**: Direct BLR→HKT flights launched June 1, 2026. Weekend-only (Friday–Sunday). Flight IX 1924/1925.

### MakeMyTrip (makemytrip.com)
- Blocks region in HTTP responses (HTTP 451 Unavailable)
- Playwright also blocked at JS level

### Cleartrip (cleartrip.com)
- Direct booking URL returns "Wrong URL" page
- Working URL format: `https://www.cleartrip.com/flights/results?from=BLR&to=HKT&depart=2025-06-05&adults=1&children=0&infants=0&channel=mobile` — returns generic landing page
- Not usable via automation

### Yatra (yatra.com)
- API endpoint: `https://www.yatra.com/air-search/dom2/trigger?type=O&view=detail&from=BLR&to=HKT&date=06/05/2026&passengerGroup=Adult|1|0|0`
- Times out on HTTP level

### Google Flights
- JSON/graphql endpoints return generic results or require auth cookies
- `browser_navigate` works for page-level access but results aren't parseable via `inner_text`

---

## HTML Card for Flight Fare Delivery

When giving user a WhatsApp link for airfare research, use HTML card delivery — not plain wa.me link.

```html
<!DOCTYPE html>
<html><head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Air India Express — BLR → Phuket</title>
<style>
  body { font-family: -apple-system, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }
  .card { background: white; border-radius: 12px; padding: 24px; max-width: 500px; margin: 0 auto; box-shadow: 0 1px 3px rgba(0,0,0,.12); }
  .route { font-size: 20px; font-weight: 700; color: #1a1a1a; margin-bottom: 16px; }
  .info { color: #666; font-size: 14px; line-height: 1.5; margin-bottom: 20px; }
  .btn { display: block; background: #25D366; color: white; text-align: center; padding: 14px 24px; border-radius: 8px; 
         text-decoration: none; font-weight: 600; font-size: 16px; }
  .btn:hover { background: #1ebe5c; }
</style>
</head><body>
<div class="card">
  <div class="route">Air India Express — BLR → Phuket (HKT)</div>
  <div class="info">
    Direct flight launched June 1, 2026<br>
    Weekend service (Fri/Sat/Sun)<br>
    Book at airindiaexpress.com<br>
    Select BLR → HKT, date June 5, 2026
  </div>
  <a class="btn" href="https://api.whatsapp.com/send/?phone=919900029200&text=Hi%20Bharat%2C%20please%20check%20the%20fare%20for%20Air%20India%20Express%20BLR%20to%20HKT%20on%20June%205.%20">Send to Bharat</a>
</div>
</body></html>
```

Save to `/data/hermes/cron/output/flight-aix-blr-hkt.html` and deliver as `MEDIA:/data/hermes/cron/output/flight-aix-blr-hkt.html`.

---

## Key Trap: Date Assumptions

The user says "this weekend" or "this Friday" — today is June 1, 2026 (Monday). The upcoming Friday is **June 5, 2026** (not June 6). Always confirm the specific date before searching, as "this Friday" depends on the current day of week.

Error: Using `2025-06-06` when today is `2026-06-01` returns historical/past data.

---

## Fallback: browser_use_cloud Tool

If `browser_navigate` and Playwright both fail to get live fares, use the `browser_use_cloud` tool — it launches a real remote browser controlled by an AI agent. The user should be given the `live_url` to take over manually if the agent gets stuck.

**Important**: `browser_use_cloud` is not always connected in all environments — check tool availability before promising this to the user.