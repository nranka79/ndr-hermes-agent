# Flight Schedule Data via ixigo JSON-LD Schema Extraction

A technique for getting current flight schedules (airline, flight number, departure/arrival times, duration) without a browser — by scraping JSON-LD schema data embedded in ixigo schedule pages.

## When to Use

- User wants actual flight timings (not just airline names)
- Browser tools are unavailable or blocked by Cloudflare
- You need schedule data for a specific route across all airlines
- Pricing is secondary (these pages have schedule data; actual fares need a separate search)

## The Technique

ixigo's flight schedule pages embed structured data as `<script type="application/ld+json">` blocks with `@type: "Flight"`. These contain `departureTime`, `arrivalTime`, `estimatedFlightDuration`, and `flightNumber`.

### Step 1: Get the schedule page for your route

The URL pattern is:
```
https://www.ixigo.com/flight-schedule/<origin>-<destination>-<airport-codes>/
```

Examples:
- BLR→DEL: `https://www.ixigo.com/flight-schedule/bangalore-new-delhi-blr-del`
- DEL→BLR: `https://www.ixigo.com/flight-schedule/new-delhi-bangalore-del-blr`

### Step 2: Extract JSON-LD blocks

```python
import re, json
from urllib.request import urlopen

url = "https://www.ixigo.com/flight-schedule/bangalore-new-delhi-blr-del"
req = urlopen(url)
html = req.read().decode('utf-8')

blocks = re.findall(
    r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>',
    html, re.DOTALL
)

for block in blocks:
    try:
        data = json.loads(block.strip())
        if isinstance(data, dict) and data.get('@type') == 'Flight':
            fn = data.get('flightNumber','')
            dept = data.get('departureTime','')
            arr = data.get('arrivalTime','')
            dur = data.get('estimatedFlightDuration','')
            airline = data.get('airline', {}).get('name', '')
            print(f'{fn} | {airline} | Dep: {dept} | Arr: {arr} | Dur: {dur}')
    except:
        pass
```

### Step 3: Filter by criteria

The page returns ALL flights — direct and connecting. Filtering logic:

- **Direct flights** have a single flight number (no comma), duration ~2-3 hours for domestic
- **Connecting flights** have comma-separated flight numbers (e.g., "6E528, 6E5321"), duration >3 hours
- Filter by arrival time by checking the `arrivalTime` field

### Known Airlines by Code (from schema data)

| Code | Airline |
|------|---------|
| 6E | IndiGo |
| AI | Air India |
| QP | Akasa Air |
| SG | SpiceJet |
| IX | Air India Express |

### Limitations

1. **No pricing data** — ixigo schedule pages don't embed fares in JSON-LD. For prices, you need a separate search on the ixigo cheap-flights page or IndiGo/Akasa/Air India sites directly.
2. **Times are static schedule, not real-time** — these are the standard scheduled times, not current-day status (delays/cancellations).
3. **Site may block curl** — ixigo currently serves schema data even to plain curl with a browser User-Agent header, but this may change.
4. **Route naming is specific** — the URL slug uses full city names (bangalore-new-delhi), not airport codes. Get the URL from a web search first if unsure.

### Alternative: Google Flights via Browser

If browser tools ARE available, use the existing `references/google-flights-browser-automation.md` reference for interactive search with live pricing.

### Example: BLR→DEL Schedule (direct flights only)

From the ixigo data, direct BLR→DEL flights and their typical timings:

| Flight | Airline | Dep BLR | Arr DEL | Duration |
|--------|---------|---------|---------|----------|
| 6E809 | IndiGo | 12:00 PM | 14:10 PM | 2h10m |
| AI2406 | Air India | 11:00 AM | 13:20 PM | 2h20m |
| 6E175 | IndiGo | 10:45 AM | 12:55 PM | 2h10m |
| 6E830 | IndiGo | 09:30 AM | 11:50 AM | 2h20m |
| 6E861 | IndiGo | 19:30 PM | 21:45 PM | 2h15m |
| AI2487 | Air India | 18:30 PM | 20:45 PM | 2h15m |
| 6E811 | IndiGo | 18:20 PM | 20:30 PM | 2h10m |
| QP1821 | Akasa Air | 13:05 PM | 15:20 PM | 2h15m |
| SG204 | SpiceJet | 19:10 PM | 21:35 PM | 2h25m |

### Typical Pricing (approximate, varies by date)

| Airline | Typical One-Way Range |
|---------|----------------------|
| IndiGo | ₹5,766 - ₹8,500 |
| SpiceJet | ₹6,500 - ₹8,000 |
| Akasa Air | ₹6,500 - ₹9,000 |
| Air India | ₹8,000 - ₹12,000 |
| Air India Express | ₹7,000 - ₹9,000 |

Fares are generally cheaper for early morning / late night departures and more expensive for daytime (10 AM - 4 PM) slots. Book at least 3-5 days ahead for best prices.
