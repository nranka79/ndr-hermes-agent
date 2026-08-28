# DSquare Global — OSINT Contact Discovery

## Background

DSquare Global (dsquare.global) is a UAE visa/immigration consultancy, referenced in a Raj Shamani YouTube interview featuring founder Deepesh Desai discussing Dubai Golden Visa for high earners.

## OSINT Methods Attempted

| Method | Result | Notes |
|---|---|---|
| `curl https://dsquare.global` | ❌ 0 bytes | ModSecurity 406 — server blocks automated requests |
| `curl` with User-Agent variants | ❌ 0 bytes | Same block |
| YouTube video page (curl) | ⚠️ Partial | Title extracted ("370") but channel/description failed |
| LinkedIn company page | ❌ Empty | Login-gated |
| WHOIS free API | ❌ Paid | Paid API only |
| Google search (curl) | ❌ Empty | Returns nothing |
| Facebook page search | ❌ Wrong co. | "dsquareglobal" is D2 tech, not visa consultancy |
| WHOIS via whoisxmlapi.com | ❌ Paid | Requires paid API key |

## Why It Blocked

- dsquare.global uses ModSecurity WAF — blocks non-browser User-Agents with 406
- JS-rendered contact forms mean static curl can't reach contact data
- LinkedIn requires login — can't scrape without session

## Fallback Approach

1. **If browser_navigate works**: Navigate to dsquare.global → snapshot → extract contact info from footer/contact page
2. **Raj Shamani YouTube video**: `https://www.youtube.com/watch?v=N_Lz5plv__M` — extract description/bio/links
3. **Google Maps business listing**: search "DSquare Global Dubai" → may have address/phone/WhatsApp
4. **Twitter/X search**: `@dsquareglobal` or `DSquare Global Dubai` → founder tweets with contact

## Verified Info

- Founder: **Deepesh Desai**
- Website: **https://dsquare.global**
- Raj Shamani video: `https://www.youtube.com/watch?v=N_Lz5plv__M`
- IP server reachable: **119.18.54.54**
- ⚠️ Facebook "dsquareglobal" = WRONG company (D2 tech)

## Contact Not Yet Found

- Email address
- WhatsApp number
- Direct phone
- Consultation booking link
- Personal LinkedIn

## If You Find Contacts

Update `uae-golden-visa-research` skill's `references/dsquare-findings.md` with:
- Founder email
- WhatsApp
- LinkedIn profile URL
- Consultation booking link
- Any phone number
