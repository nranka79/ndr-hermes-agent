---
name: india-local-services-search
description: Search for local businesses, services, and recreational facilities in Indian cities — coaches, academies, clinics, gyms, etc. When search engines return JS-garbled or captcha-blocked results, fall back to Indian directory sites and direct scraping.
version: 1.0.0
---

# India Local Services Search

When asked to find a local business, service, coach, facility, or recreational option in an Indian city, search engines like Google and Bing often return obfuscated JS or trigger captchas when scraped via curl. DuckDuckGo's HTML endpoint works for a few queries before rate-limiting kicks in.

Use this layered approach instead:

## Layer 1 — DuckDuckGo HTML (initial sweep)

```
https://html.duckduckgo.com/html/?q=squash+coaching+Vasanth+Nagar+Bangalore
```

Works for 1–3 queries before captcha. Use a desktop UA. Extract results with `sed 's/<[^>]*>//g'`. Good for discovering which directory sites have listings for your query.

## Layer 2 — Indian Directory Sites (primary sources)

These sites render cleanly via curl and cover Indian cities thoroughly:

| Directory | Coverage | URL Pattern |
|-----------|----------|-------------|
| **JustDial** | All businesses, services | `justdial.com/<City>/<Category-in-Vicinity>/nct-<id>` |
| **Sulekha** | Services, coaching, classes | `sulekha.com/<category>/<city>` |
| **BookMyPlayer** | Sports academies, coaches, venues | `bookmyplayer.com/<sport>-classes-in-<locality>-<city>` |

### Extraction Pattern

```bash
curl -sL "https://www.justdial.com/Bangalore/Squash-Classes-in-Vasanth-Nagar/nct-10449859" \
  -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36" \
  | sed 's/<[^>]*>//g' | tr -s ' \n' '\n' | grep -iE 'phone|contact|call|address|rating|name'
```

Note: JustDial and Sulekha pages are large; pipe through `tr -s` and grep for contact fields. Extract phone numbers with `grep -oP '[\+\d]{10,15}'` (watch for false positives from timestamps).

## Layer 3 — Category-Specific Directories

For sports/recreation:
- **BookMyPlayer**: Lists academies, coaches, venues per locality
- **Playo** (`playo.co`): Venue booking + coaching, JS-heavy but has structured initial state
- **MyTribe** (`mytribe.in`): Coaches with structured JSON-LD data — best source for pricing

### MyTribe — Structured JSON-LD Extraction

MyTribe embeds full pricing, coach details, and location data in JSON-LD script tags. Extract with:

```bash
curl -sL "https://mytribe.in/<provider>/<service>" | \
  grep -oP '"description":"[^"]*"|"name":"[^"]*"|₹[0-9,-]+'
```

Or extract the entire JSON-LD block:
```bash
curl -sL "https://mytribe.in/indian_school_of_sports/squash-coaching" | \
  grep -oP '<script type="application/ld\+json">.*?</script>' | \
  sed 's/<[^>]*>//g' | python3 -m json.tool 2>/dev/null | \
  grep -E '"name"|"description"|"price"|"telephone"|"address"'
```

## Layer 4 — Direct Business Website Scraping

Once you have business names from directory results, scrape their own websites:

```bash
curl -sL "https://www.indianschoolofsports.co.in/contact" \
  -H "User-Agent: Mozilla/5.0" | \
  sed 's/<[^>]*>//g' | tr -s ' \n' '\n' | grep -v '^\s*$'
```

Look for: phone numbers, email addresses, physical address, price ranges.

## Common Search Patterns by Category

### Sports Coaching
```
<sport> + coaching/training/classes + <locality> + <city>
```
Directories: BookMyPlayer, Sulekha, JustDial, MyTribe

### Fitness / Gym
```
gym/fitness + <locality> + <city>
```
Directories: JustDial, Sulekha, Fitternity

### Medical / Clinic
```
clinic/doctor/<speciality> + <locality> + <city>
```
Directories: Practo, JustDial, 1mg

### Education / Tuition
```
<subject> + classes/tuition + <locality> + <city>
```
Directories: JustDial, Sulekha, UrbanPro

## Pitfalls

- **JustDial phone number obfuscation**: JustDial sometimes hides phone numbers behind JavaScript. The curl-extracted page may not contain them. Try mobile UA or use a different directory as fallback.
- **DuckDuckGo rate limiting**: After 2–3 queries from the same IP, DDG returns a captcha page. Rotate UAs or switch to direct directory scraping.
- **Google/Bing JS obfuscation**: Both return heavily minified JS that is not worth parsing via curl. Skip them for local service searches — use directories instead.
- **Sulekha page bloat**: Sulekha pages embed large amounts of tracking JS. Use `tr -s ' \n' '\n' | grep -v '^\s*$'` to normalize before extraction.
- **Multiple locations**: A single business may have multiple branches listed across different directory pages. Cross-reference by phone number.
- **Pricing recency**: MyTribe pricing data may be months old. Always verify with the business directly.
