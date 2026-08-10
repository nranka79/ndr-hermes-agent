# Indian E-Commerce Availability & Delivery Research

Session-proven workflow (Baseus Inspire XC1 hunt, Aug 2026). Use when user asks "where can I buy X in India/Bangalore" or "can I get X in 24-48h".

## Core doctrine
- Tavily (web_search/web_extract) and Firecrawl frequently out of credits on this VPS → do NOT retry same path, switch rungs.
- Datacenter IPs are bot-blocked by Google, Flipkart, Croma, DuckDuckGo. Escalate: web_search → apify → browser_use_cloud → smart_browser → browser_navigate → **curl + plain-HTML/RSS endpoints**.
- **Bing RSS via curl is the reliable last rung** (works from datacenter IP when Google/DDG/Bing HTML are gated):
  `curl -sL "https://www.bing.com/search?q=<query>&format=rss"` → parse XML titles/links/descriptions.

## Amazon.in flow (critical path)
1. Find ALL ASINs (search + Bing RSS) — multiple listings, different prices/sellers.
2. Open product page → price, MRP, seller name.
3. **Verify delivery with pincode** (e.g. 560001 Bangalore) via delivery-location change flow — read actual "delivery by <date>" line. Never quote ETA without pincode check.
4. Check buying options / all sellers per ASIN.
5. **No Prime listing ⇒ import/pre-order ⇒ 2-3 weeks.** Fresh global launches (2026 era) in India are import-seller-only (e.g. "Doveberry", "Apna America").

## Multi-store sweep (India)
- Flipkart search is FUZZY for niche products — verify exact match on card.
- Croma, Reliance Digital, Vijay Sales, Tata CLiQ, Meesho — check each; chains rarely stock niche imports.
- Official brand .in site — VERIFY it's a real store first (baseus.in was a dead parking page).
- Specialist retailers (Headphone Zone, HiFiMart) — niche audio sometimes only here.
- Global site (baseus.com $149.99 vs Amazon.in ₹22,846 import) — quote as cheaper-but-slower alternative.

## Bangalore offline path
- SP Road / Commercial Street import-electronics shops can beat e-commerce for fresh imports — offer store-level stock check or dealer WhatsApp.

## Conclusion pattern
When no 24-48h option: say so plainly → best online option (link+price+verified date+seller) → cheaper global alternative → offline path → offer concrete next actions. Never fabricate delivery dates.

## Pitfalls
- Flipkart/Croma/Google pages that "load" may be bot walls showing stale content.
- Don't burn 10+ calls retrying a blocked site; escalate rungs and tell the user.
- Niche fresh launches in India: assume import-seller-only until proven otherwise.
