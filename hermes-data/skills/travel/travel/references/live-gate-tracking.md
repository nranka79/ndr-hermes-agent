# Live Flight Gate & Status Tracking

When the user asks for a flight's **gate number** or live departure status (e.g. "what gate is my IndiGo 6E 830?"), use this methodology.

## Key Fact: Gates Aren't Published Until 30–60 Minutes Before Departure

Gate numbers are assigned by airport operations close to departure time. Before that, all tracking sites show **N/A** or **—**. This is normal — don't assume something is wrong.

## Best Sources (in priority order)

| Source | URL Pattern | Gate Info | Notes |
|--------|-------------|-----------|-------|
| **FlightStats** | `https://www.flightstats.com/v2/flight-tracker/{airline}/{flight}` | ✅ Shows Gate when assigned, **N/A** until then | Most accessible, no login needed, also shows terminal & baggage carousel |
| **FlightAware** | `https://www.flightaware.com/live/flight/{ICAO_code}{flight}` | ⚠️ Free tier hides gate | Shows terminal, on-time status, estimated times. Gate visible with premium. |
| **FlightRadar24** | `https://www.flightradar24.com/data/flights/{flight}` | ❌ No gate info (history/schedule only) | Good for aircraft registration, actual times, route history |
| **Airport Website** | Airport-specific departure page | ✅ Gate when assigned | Often JS-heavy, may not render in browser tools |
| **IndiGo Flight Status** | `https://www.goindigo.in/flight-status.html` | ⚠️ PNR search may show gate | PNR-based search often returns "No flights found" — use flight number instead |

## Search Procedure

### 1. Confirm flight details first
```python
# Use FlightStats — simplest, most reliable
url = f"https://www.flightstats.com/v2/flight-tracker/{airline_code}/{flight_number}"
# e.g. 6E/830, AI/101, 6E/62849
```

### 2. For IndiGo flights — the ICAO code is IGO
FlightAware URL: `https://www.flightaware.com/live/flight/IGO{flight_number}`
FlightStats URL: `https://www.flightstats.com/v2/flight-tracker/6E/{flight_number}`

### 3. What to report
```
| Detail | Status |
|--------|--------|
| ✈️ **Flight** | 6E 830 (Airbus A321neo, VT-NHT) |
| 🛫 **Scheduled** | 09:30 IST |
| 🛬 **Estimated** | 12:15 IST (slightly ahead of schedule) |
| 🏢 **Terminal** | T1 (both BLR & DEL) |
| 🚪 **Gate** | ❌ Not yet assigned (check at airport ~08:00) |
| 🛄 **Baggage (DEL)** | Carousel 03 |
```

### 4. If gate is N/A, contextualize for the user
Say: **"Gates are typically assigned 30–60 minutes before boarding by the airport. Currently showing N/A — check back around [departure - 1.5h] and I can re-check, or you'll see it on the departure screens at the terminal."**

## Multi-Site Strategy When Gate Isn't Found

1. **FlightStats** first (terminal, gate, baggage, status in one view)
2. **FlightAware** for confirmation (aircraft, route, on-time estimate)
3. **Airport website** only if FlightStats shows N/A and you're within 1h of departure
4. **IndiGo PNR search** as last resort — unreliable, often returns "No flights found"

## Flight Number Disambiguation

Users often say the flight number slightly wrong (e.g., "62849" when the actual flight is "6E 830"). Search terms to use:
- PNR / booking reference from Gmail itinerary (e.g. ZCJD2D)
- Flight number from itinerary (e.g. 6E 830)
- Route + time (e.g. "BLR to DEL 9:30 AM")
- Airline + route (e.g. "IndiGo BLR to DEL")
