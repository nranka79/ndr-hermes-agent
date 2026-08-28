# DSquare Global — Research Findings (Updated May 2026)

> This file lives under `references/` — it is a support file for the `uae-golden-visa-research` umbrella skill.
> The main skill SKILL.md at the root of this skill carries the current outreach templates.

## Verified/Confirmed Contacts

- **WhatsApp (May 2026):** +91 8291924600 — Deepesh Desai ✅ CONFIRMED
- **Email:** info@dsquare.global (website contact form)
- **Founder:** Deepesh Desai
- **Website:** https://dsquare.global — JS-rendered, blocked by ModSecurity on curl
- **Reference:** Raj Shamani YouTube interview — `https://www.youtube.com/watch?v=N_Lz5plv__M`

## Key Data Points (Updated May 2026)

| Item | Old (Jun 2025) | Updated (May 2026) |
|---|---|---|
| O3 Infotech ARR | ~INR 1 Cr | **~INR 3 Crore** |
| DRA Group turnover | ~INR 250 Cr | **~INR 2,000 Crore** |

## WhatsApp Encoding — Full-Width Ampersand Fix

**⚠️ Critical: Android/mobile WebView ampersand truncation bug**
Standard `%26` (URL-encoded `&`) is misinterpreted by WhatsApp mobile WebView as a URL parameter separator, truncating the message at the first `&` inside the text body.

**Fix:** Use full-width ampersand `＆` (U+FF06) encoded as `%EF%BD%86` inside the message body.

**Correct wa.me URL structure:**
```
https://wa.me/918291924600?text=Hi%20Deepesh%2C%20co-founder%20%EF%BD%86%20I%20qualify.
```
- `918291924600` = phone (raw digits, no +, no spaces, no dashes)
- `%20` = space
- `%2C` = comma
- `%EF%BD%86` = full-width ampersand `＆` (U+FF06) inside message body
- `%27` = apostrophe
- `%2B` = plus sign
- `%3A` = colon
- `?` and `&` between URL params = NOT encoded (standard characters)

**NEVER use `%2526`** — that is double-encoding and makes the `text` parameter completely invisible (link opens WhatsApp but with no message pre-filled).

## Web Research Limitation

Google search is blocked by consent/captcha pages in this environment. Bing returns no structured results. For alternative advisory firms, search Google Maps and LinkedIn directly. Known alternatives to DSquare:
- Golden Gate Visas (goldengatevisas.com) — Bangalore
- Stellar Immigration (stellarimmigration.com) — Mumbai/Delhi
- UAE BizVisa (uaebizvisa.com) — Bangalore
- Immigroup (immigroup.in) — Mumbai
- XIPHIAS Immigration (xiphiias.com) — Bangalore/Chennai