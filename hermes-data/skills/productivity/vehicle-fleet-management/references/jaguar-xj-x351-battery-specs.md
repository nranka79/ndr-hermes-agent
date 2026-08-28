# Jaguar XJ X351 (2015-2016) — Battery Research Reference

## Vehicle Variants Covered

| Variant | Engine | Fuel | Notes |
|---------|--------|------|-------|
| **XJ 3.0L V6 Diesel** | 3.0L V6 D (2993cc) | Diesel | Has Stop/Start — **AGM mandatory** |
| **XJR 5.0L V8 Supercharged** | AJ133 5.0L V8 SC | Petrol | Has Stop/Start — **AGM mandatory** |

⚠️ **Important:** The owner may call their car "XJR" even when it's actually a 3.0L Diesel XJ. Always verify the exact model from the RC document (found in Gmail) — check the MODEL, FUEL, and CC fields. The 3.0L Diesel is not an XJR (which is exclusively 5.0L V8 Supercharged Petrol), but **both variants use the same battery**.

## Battery Specifications

| Parameter | Value |
|-----------|-------|
| **Type** | **AGM** (Absorbent Glass Mat) — mandatory for Stop/Start |
| **Capacity** | **95-96 Ah** |
| **CCA** | **850-900A** |
| **Size** | ~353×175×190 mm (European H9 / LN5 / L5 / DIN95 group) |
| **Layout** | Positive on right (Type 0) |
| **Terminal** | Type 1 |
| **Base hold-down** | B13 |

## OEM-Compatible Model Numbers

| Brand | Model | Specs |
|-------|-------|-------|
| **Bosch** | S5A 13 | 95Ah / 850A |
| **Varta** | G14 | 95Ah / 850A (factory-fit equivalent) |
| **Exide** | EK950 | 95Ah / 900A (widely available in India) |
| **Exide** | EK960 | 96Ah / 850A |
| **Amaron** | DIN95L AGM-LN5 | 95Ah / 900A (good for Indian heat) |
| **Lucas** | LF017 | AGM, 95Ah / 850A |

## Price Comparison (India, ~2025-2026)

| Option | Battery Only | Installed | Notes |
|--------|:-----------:|:---------:|-------|
| **Jaguar Dealer** | ₹30,283 | ~₹33,968 | Includes battery registration |
| **Exide EK950 AGM** | ₹16,000-18,000 | ~₹17,000-19,000 | Best value, 4yr warranty |
| **Amaron DIN95L AGM-LN5** | ₹17,000-22,000 | ~₹18,000-23,000 | 900CCA, heat-resistant |
| **Bosch S5A 13 AGM** | ₹18,000-22,000 | ~₹19,000-23,000 | OEM-equivalent |
| **Varta G14 AGM** | ₹20,000-23,000 | ~₹21,000-24,000 | Factory-fit, premium |

✅ **Verdict:** Dealer charges approximately ₹12,000–15,000 more than aftermarket for an equivalent AGM battery.

## Critical: Battery Registration

The Jaguar X351 XJ requires the new battery to be **registered** in the ECU via a diagnostic tool after replacement. Without registration:
- The BMS (Battery Management System) uses old charge parameters
- This leads to under/overcharging and shortened battery life
- Stop/Start system may malfunction

**Dealer** does this automatically. **Outside mechanic** — confirm they have a suitable diagnostic tool (e.g. Autel, Launch, or JLR SDD) that can perform battery registration.

## Key Research Sources Used

- **whatbattery.co.uk** — comprehensive battery specs per vehicle model + engine variant
- **DuckDuckGo** — for Indian market pricing (Amazon.in, Indiamart, dealer listings; note these sites may block automated browsers)
- **Gmail RC document** (PDF) — for exact vehicle identification (VIN, engine, fuel type, year)
- **Scribd** — Exide DP Price List 2026 / Amaron Retailer Price List (paywalled but useful for verifying price ranges)
