# BLR ↔ BOM Flight Search — May 2026 Findings

## Google Flights URL Pattern

```
https://www.google.com/travel/flights?hl=en-IN&gl=in&curr=INR&q=BLR+to+BOM+May+18+2026
```

- `hl=en-IN&gl=in&curr=INR` → India, INR currency (shows Indian prices including taxes)
- Date format: plain text "May 18 2026" works
- Round trip: set same outbound + return date for same-day return trips

## Reading Results

- Snapshot shows 13 results max per page load
- "Cheapest" tab shows price-ranked results (default selected)
- "Best" tab shows time/convenience ranked
- Each flight: departure time, arrival time, airline, ₹price "round trip total"
- Return flights shown separately below outbound selection (click a flight to see return options)

---

## Aggregator Bot Detection — What Works for Browser Automation

| Source | Status | Notes |
|--------|--------|-------|
| Google Flights | ✅ Reliable | Best for browser automation |
| MakeMyTrip | ❌ Blocked | Returns empty/1-element page |
| Cleartrip | ❌ Blocked | Returns "Access Denied" |
| AirIndia.com | ⚠️ Unreliable | 404s on /flight-search; form-based booking works but slow |

**Recommendation:** Use Google Flights as primary. AirIndia.com as secondary for direct booking. Skip MakeMyTrip/Cleartrip for programmatic searches.

---

## Google Flights URL Time Filter — Known Failure Mode

**Problem:** `departureTime=09%3A00%2C14%3A00` URL param does NOT filter results — page still loads all flights.

**Workaround:** 
1. Always apply airline filter first (click "Airlines" → select airline → close dialog)
2. Then use the "Times" filter dialog with sliders — sliders for departure/arrival time ranges
3. Alternatively: use the "Best" tab vs "Cheapest" tab to expose different results
4. Confirm filter is active by checking the filter pills shown below the search bar

**For Air India specific searches:** Use `q=Air+India+BLR+to+BOM+May+18+2026` and apply both "Air India" airline filter AND Times filter.

**Sliders:** 0–24 scale (hours); set earliest to ~9 for 9 AM cutoff.

**Results truncation:** Google Flights shows "16 results" but list truncates at ~4 visible items — scroll down to see more.

---

## BLR ↔ BOM — May 18, 2026 Complete Results

### Outbound (BLR → BOM, Monday morning)

| Airline | Departs | Arrives | ₹ One-way |
|---------|---------|---------|-----------|
| SpiceJet | 4:15 AM | 6:15 AM | ₹5,680 |
| SpiceJet | 4:55 AM | 7:10 AM | ₹5,680 |
| Akasa Air | 6:00 AM | 7:55 AM | ~₹11,268 |
| Air India | 2:20 AM | 4:10 AM | ₹6,376 |

### Return (BOM → BLR, Monday evening)

| Airline | Departs | Arrives | ₹ One-way |
|---------|---------|---------|-----------|
| Akasa Air | 6:45 PM | 8:40 PM | ₹6,587 |
| Akasa Air | 9:45 PM | 11:35 PM | ₹5,875 |
| SpiceJet | 10:30 PM | 12:30 AM (Tue 19) | ₹5,916 |
| Air India | 7:45 PM | 9:50 PM | ₹7,856 (one-way) |
| Air India | 8:50 PM | 10:50 PM | ₹7,221 |

### Best Combination for Prayer Window (No SpiceJet preference)

- Outbound: Akasa Air 6:00 AM → 7:55 AM (arrive BOM 7:55 AM)
- Return: Air India 7:45 PM → 9:50 PM (arrive BLR 9:50 PM)
- Total for 4 pax (2 adults + 2 children): ~₹(11,268×2) + (7,856×2) = ~₹38,248
- Mumbai window: ~11 hrs 50 min

---

## Air India — BLR ↔ BOM Same-Day Round Trip (May 18) — CORRECTED

**CORRECTED from user screenshot + OpenRouter vision analysis (May 16, 2026):**

Air India DOES have BLR→BOM flights throughout the day on May 18, including in the 9 AM – 2 PM window. Browser snapshots were truncating results — only showing 3 of 9 Air India flights. User screenshot confirmed the full list.

### Complete Air India BLR → BOM (May 18) — From User Screenshot
| Flight | Departs | Arrives | ₹ One-way |
|--------|---------|---------|-----------|
| AI-XXX | 2:20 AM | 4:10 AM | ₹6,376 |
| AI-XXX | 6:35 AM | 8:35 AM | ₹19,879 |
| AI-XXX | 9:15 AM | 11:15 AM | ₹17,475 |
| AI-XXX | 10:30 AM | 12:35 PM | ₹11,526 |
| AI-XXX | 12:05 PM | 2:05 PM | ₹13,122 |
| AI-XXX | 6:05 PM | 8:05 PM | ₹11,621 |
| AI-XXX | 7:00 PM | 9:05 PM | ₹6,502 |
| AI-XXX | 8:30 PM | 10:40 PM | ₹6,502 |
| AI-XXX | 9:30 PM | 11:35 PM | ₹6,502 |

### Viable Outbound Options (arrive BOM by ~2 PM for 10:30 AM event)
- **AI 6:35 AM → 8:35 AM** — ₹19,879/pax — arrives 8:35 AM ✓ (BEST for early arrival)
- **AI 10:30 AM → 12:35 PM** — ₹11,526/pax — arrives 12:35 PM ✓
- **AI 12:05 PM → 2:05 PM** — ₹13,122/pax — arrives 2:05 PM ✓

### Best Return (5–9 PM prayer window)
- **AI 7:45 PM → 9:50 PM** — ₹15,711 round trip (or ~₹7,856 one-way)

### Recommended Round Trip (Family of 4, 2 Adults + 2 Children)
- Outbound: AI 10:30 AM → 12:35 PM (₹11,526 × 4 = ₹46,104)
- Return: AI 7:45 PM → 9:50 PM (₹15,711 × 4 = ₹62,844)
- **Total: ₹1,08,948** — full Maharaja Club miles on both legs

### Booking Reality
- Air India has excellent coverage on BLR→BOM May 18 including afternoon options
- Browser truncation was the only reason earlier analysis said "no afternoon flights"
- Always use OpenRouter vision analysis when user provides a screenshot of flight results

---

## Depart After 9 AM + No-SpiceJet Constraint

**Hard user constraint:** NO SpiceJet, departures after 9 AM only OR arrive BOM by 9 AM with 5–8 hour window.

### BLR → BOM (May 18) — Departures after 9 AM
| Airline | Departs | Arrives | ₹ One-way |
|---------|---------|---------|-----------|
| SpiceJet | 10:35 PM | 12:35 AM (Tue 19 May) | ₹5,228 |
| Air India | 2:20 AM | 4:10 AM | ₹6,376 |

**No non-SpiceJet flights depart BLR between 9 AM and 10 PM on May 18.** Air India is the only viable non-SpiceJet carrier and it departs at 2:20 AM (arrives BOM 4:10 AM = within the 9 AM window).

### BOM → BLR (May 18) — Evening departures
| Airline | Departs | Arrives | ₹ One-way |
|---------|---------|---------|-----------|
| Akasa Air | 9:45 PM | 11:35 PM | ₹5,875 |
| SpiceJet | 10:30 PM | 12:30 AM (Tue 19 May) | ₹5,916 |
| Air India | 8:50 PM | 10:50 PM | ₹7,221 |

### Cheapest non-SpiceJet combo (BLR → BOM → BLR, May 18)
- Outbound: Air India 2:20 AM → 4:10 AM (₹6,376)
- Return: Akasa Air 9:45 PM → 11:35 PM (₹5,875)
- **Total: ₹12,251** | Mumbai window: ~17 hours

---

## Key Findings

- SpiceJet cheapest for this route/date but user excludes it
- Same-day return = both dates set to same day in Google Flights
- "Round trip total" = combined price shown per flight option
- For 5–6 hour Mumbai window: arrive by 6–7 AM, depart 6–7 PM works
- Air India tends to be more expensive on this route for economy
- The "Cheapest" tab is price-sorted but shows SpiceJet first; "Best" tab may show non-SpiceJet higher — always check both tabs when user has airline exclusions
- For BOM→BLR return leg, search **separately** with same time/airline filters — Google Flights doesn't show return prices until you select outbound