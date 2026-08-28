# Reverse Phone Number OSINT — Indian mobile numbers (free sources, NDR no-API directive)

Trigger: "find social media about this number", "who owns +91…", "where is
this number", "check this number on X/Facebook/Instagram". Common in DRAAS
work: verifying unknown callers, cold leads, WhatsApp numbers.

## Ladder (free sources only — no Apify/Tavily, per NDR standing directive)

1. **Exact-match DDG via Jina** (the reliable first move):
   ```
   curl https://r.jina.ai/https://html.duckduckgo.com/html/?q=7065703131
   ```
   Try ALL formats before concluding:
   - bare 10-digit: `7065703131`
   - +91 prefixed: `%2B917065703131` (URL-encode the `+` — DDG treats bare `+91…` as a query token)
   - spaced: `70657%2003131`
   For a number with no web footprint, DDG returns only generic US
   reverse-lookup directories (411, Spokeo, TruePeopleSearch…) — that IS
   the answer: the number has no indexed presence.

2. **Google News RSS** (zero-captcha news check):
   ```
   https://news.google.com/rss/search?q=7065703131&hl=en-IN&gl=IN&ceid=IN:en
   ```
   Use for numbers that might appear in business listings / news / press.

3. **Truecaller web**:
   ```
   https://www.truecaller.com/search/in/7065703131
   ```
   Returns placeholder "First Last +1 234 4567" + login wall; caller stats
   and comments are blurred. Owner name requires the app login — state this
   limit plainly, don't pretend to have the answer.

4. **Business directories** (only when the number is a listed business):
   site: queries via DDG-via-Jina, e.g. `site:indiamart.com 7065703131`,
   `site:justdial.com 7065703131`. Usually empty for personal mobiles.

## Blocked / do not burn retries (verified 2026-08-25)
- Google SERP: captcha-walled even via Jina reader (unusual-traffic page).
- Bing / Brave / Yandex via Jina: anti-bot junk or 429.
- Instagram `web/search/topsearch/?query=…`: 403 AbuseAlleviationError via
  Jina; anonymous access to www.instagram.com blocked. X/Facebook/IG search
  needs login.
- Truecaller HTML has no name without OAuth sign-in.

## Reporting
- A number with zero hits across all formats = **no public social/web
  footprint**. Say that explicitly; only Truecaller app login or paid data
  (Spokeo, etc.) could surface the owner name.
- Always report which sources were tried and which were walled — the wall
  itself is a finding ("name is behind Truecaller login").