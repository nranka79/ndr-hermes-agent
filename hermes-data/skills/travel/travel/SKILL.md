---
name: travel
description: "Travel umbrella — flight document retrieval, hotel check-in, and nearby place discovery. Covers itinerary retrieval from Google Drive, flight booking reference lookups, and finding nearby restaurants/cafes/bars."
umbrella: travel
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Travel, Flights, Hotels, Itinerary, Google Drive, Check-in, Nearby Places]
---

# Travel — Umbrella

Covers travel document retrieval, flight check-in, and nearby place discovery.

## Decision Tree

```
What travel task do you need?
├── Retrieve flight/hotel documents from Google Drive
│   └── → Travel Document Retrieval (references/travel-docs.md)
│         Itinerary PDFs, PNR lookups, boarding passes.
├── Find flight details by searching Gmail
│   └── → Gmail Flight Itinerary Search (references/gmail-flight-itinerary-search.md)
│         Airline email queries, body extraction, PNR/times.
├── Find nearby restaurants, cafes, bars, etc.
│   └── → Find Nearby (references/find-nearby.md)
│         OSM-based, no API key needed.
├── Book flights via Bharat (DRAAS booker)
│   └── → DRAAS Flight Booking Coordination (references/draas-flight-booking-coordination.md)
│         Research → narrow → compile passenger details → email Bharat + CC Roshini.
├── Find businesses / places / contact info via Google Maps
│   └── → Apify Google Maps (references/apify-google-maps.md)
│         Apify actor, returns name/address/phone/rating/website/URL.
└── Web check-in for a flight
    └── → Use travel-document-retrieval, then navigate to airline check-in URL
└── Find live flight status / gate number
    └── → Live Gate Tracking (references/live-gate-tracking.md)
          Multi-site search: FlightStats → FlightAware → FlightRadar24 → airport.
          Gates publish 30-60min before departure; "N/A" is normal.
```

## Absorbed Skills (2026-05-29)

- `apify-google-maps` → `references/apify-google-maps.md`

## Sub-Skill Reference

| Skill | When to Use | Key Method |
|-------|-------------|-----------|
| `references/travel-docs.md` | Flight/hotel document retrieval | Google Drive API |
| `references/gmail-flight-itinerary-search.md` | Flight details from Gmail itinerary emails | Gmail API search + body extraction |
| `references/find-nearby.md` | Nearby place discovery | OSM/Nominatim |
| `references/blr-bom-flights-may2026.md` | BLR↔BOM flight research (May 18) | Google Flights + aggregator testing |
| `references/google-flights-browser-automation.md` | Google Flights browser automation | Form interaction, result counting, live URL sharing |
| `references/draas-flight-booking-coordination.md` | DRAAS internal flight booking | Research → email Bharat + CC Roshini with booking instructions |
| `references/flight-schedule-via-schema-jsonld.md` | ixigo JSON-LD flight schedule extraction | curl + regex on schema data (no browser needed) |
| `references/live-gate-tracking.md` | Live flight gate/status tracking | Multi-site search, FlightStats |

## Absorbed Skills

- `travel-document-retrieval` → `references/travel-docs.md`
- `find-nearby` → `references/find-nearby.md` (was in `leisure`)

## Bali Airport Lounges — Ngurah Rai DPS (International Terminal)

**All via Priority Pass** — both Indulge (Visa Infinite) and Kotak Signature include Priority Pass.

| Lounge | Terminal | Hours | Guest Policy |
|--------|----------|-------|-------------|
| Blue Sky Premier Lounge | Domestic | 05:30–21:30 | Unlimited guests per cardholder |
| Concordia Lounge | Domestic | 05:00–22:00 | Unlimited guests per cardholder |
| Concordia Lounge | International | 06:00–02:00 | Unlimited guests per cardholder |
| **Flight Club DPS** | International | **05:00–01:00** (overnight) | Unlimited guests per cardholder |

**Important:** Priority Pass **must be activated via DreamFolks** (physical cards stopped October 2024). Go to `https://webaccess.dreamfolks.in` — register with your card details, link your PP membership number (found in netbanking → Cards → Priority Pass section). Show DreamFolks digital pass at lounge. Old activation URL (`prioritypass.com/en-GB/activate-your-account`) leads to 404 — dead, do not use.

**Children:** Under 6 years admitted free at all Priority Pass lounges.

### Bali DPS Return (May 16) — Lounge Strategy
- Concordia International full → try **Flight Club DPS** (open 05:00–01:00, same terminal)
- Both you and Roshini can enter using your cards — unlimited guests means 2 cards cover all 4 (2 adults + 2 kids)

---

## Quick Reference

### Retrieve Itinerary from Google Drive
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

creds = Credentials.from_authorized_user_file(token_path, SCOPES)
drive = build('drive', 'v3', credentials=creds)
# List files in trip folder, download by file ID
```

### Find Nearby Places
```bash
# See references/find-nearby.md for OSM-based place discovery
```

## Vision / Image Analysis — Use Gemini API Directly

**The `vision_analyze` tool is unreliable** — it uses `google/gemini-2.0-flash` which returns 400 errors ("not a valid model ID").

**Fallback procedure when vision_analyze fails:**
```python
import urllib.request, json, base64

api_key = "<GOOGLE_MAPS_API_KEY - removed 2026-07-17, read from env, do not hardcode>"  # Google AI Studio key (env: GOOGLE_AI_STUDIO_API_KEY)
image_path = "/data/hermes/image_cache/img_XXXX.jpg"   # or browser screenshot

with open(image_path, "rb") as f:
    image_data = base64.b64encode(f.read()).decode()

payload = {
    "contents": [{"parts": [
        {"text": "Your question here"},
        {"inline_data": {"mime_type": "image/jpeg", "data": image_data}}
    ]}]
}

url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
req = urllib.request.Request(url, data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=30) as resp:
    result = json.loads(resp.read())
    print(result["candidates"][0]["content"]["parts"][0]["text"])
```

**Known failure modes:**
- `gemini-2.0-flash` → 404 Not Found (model name deprecated)
- `gemini-2.5-flash` → 403 Forbidden on some keys
- `models/gemini-2.5-flash` → 403 Forbidden
- Rate limit (429) — wait 5+ seconds and retry
- Browser screenshots saved to `/data/hermes/cache/screenshots/browser_screenshot_*.png`

**Also check:** `AUXILIARY_VISION_PROVIDER=openrouter` env var is set but the OpenRouter API key may not be available in `OPENROUTER_API_KEY`. If direct Gemini fails, try OpenRouter via `infsh` CLI or check if the key exists first with `env | grep OPENROUTER`.

## BLR ↔ BOM — Open Issues

✅ **RESOLVED: Air India BLR→BOM afternoon flights discrepancy** — Air India DOES have multiple BLR→BOM flights between 9 AM and 2 PM on May 18 (confirmed via user screenshot + OpenRouter/Gemini 2.5 Flash analysis). Browser truncation was the only issue. See `references/blr-bom-flights-may2026.md` for corrected data.

**Remaining actions:**
- IndiGo/Akasa morning flight prices not yet captured (need separate search for complete Option B pricing)
- Air India website still returns 404 on /flight-search endpoint — direct booking not verifiable via browser automation
- BOM→BLR return search with 5–9 PM filter also showed truncation in browser snapshot; user screenshot may be needed to confirm full return flight list if user disputes

## Resources

- **Google Drive API**: https://developers.google.com/drive
- **OSM Nominatim**: https://nominatim.org