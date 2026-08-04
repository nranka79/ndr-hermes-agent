# Karnataka Land Price Benchmarks — Government Sources (Kaveri / IGR / KIADB)

When the user asks for "current land prices from Kaveri portal or government sources" for a Devanahalli / Nandi Hills / North Bangalore parcel. Complements `devanahalli-per-sqft-curated-aug2026.md` (per-sqft project rates) — this covers **per-acre land/transaction benchmarks** and the **registry/guidance-value angle**.

## Source inventory (tested Aug 2026 from Hermes VPS)

| Source | Accessibility | What it gives |
|---|---|---|
| `kaveri.karnataka.gov.in` (Kaveri 2.0) | NOT reachable from VPS (login/portal) | The authoritative survey-number-level guidance value lookup — cite it as the verification step, don't try to scrape it |
| `igr.karnataka.gov.in` (Revised Guidelines Value page) | **times out** from VPS (connection timeout) | Same data; get it via Google snippets instead |
| `findcirclerate.com/india/karnataka/bengaluru/devanahalli` | **web_extract works** | Current guidance/circle rates per property type (₹/sq.m), updated 2026-27 |
| The Hindu / newspaper articles | web_search works | KIADB acquisition compensation figures — the strongest "government source" anchor |
| Portal listings (99acres, realestateindia, Instagram/Facebook broker posts) | web_search snippets | Recent market transactions/listings per acre |
| `brai.in/wp-content/uploads/2018/01/Devanahalli.pdf` | curl works | Old (2017-18) guidance value PDF — shows the per-village structure (Khushki/Thari/Bhagaytu ₹lakh/acre) but stale; don't quote as current |

## Key figures (verified mid-2026, Devanahalli corridor)

- **KIADB compensation (Jun 2026): ₹2.70 Cr/acre** offered to Devanahalli farmers who voluntarily came forward — described as the **highest land-acquisition compensation in Karnataka** (The Hindu, 24 Jun 2026, KIADB Act notification gazetted 16 Jun 2026). This is the single best public-government benchmark for "what is this land worth" on the corridor.
- **Guidance value — Devanahalli (Airport Area) 2026-27** (findcirclerate.com, "official guidance value"):
  - Residential plot: ₹45,208/sq.m (~₹4,200/sq.ft)
  - Flat/apartment: ₹40,903/sq.m
  - Commercial: ₹59,202/sq.m
- **Guidance vs market gap**: in Devanahalli/Hoskote-type newer corridors guidance is typically **15–25% below market**; Feb 2026 revision raised guidance **6–15%** in Bengaluru urban limits. OneCityProperty table: Devanahalli plot guidance ₹5,000–7,500/sqft vs market ₹6,000–10,000/sqft (15–40% above guidance).
- **Registration fee changed**: 1% → 2% effective **Aug 31, 2025** (Karnataka). Stamp duty still 5% (plus cess/surcharge ≈7.6% total). Quote the current fee if the deck discusses acquisition costs.

## Market per-acre bands (Nandi Hills / Devanahalli corridor, 2026)

Cross-checked from portal snippets + broker listings. Wide spread — always present as a band with the value driver noted:

- **₹8.5 Cr/acre** — 10-acre premium farmland near Nandi Hills (Jul 2026 listing)
- **₹5.5–7 Cr/acre** — Nandi Hills road parcels (2.3 ac @ ₹5.5 Cr/ac; 3.5 ac @ ₹7 Cr/ac, 2026)
- **₹6.5 Cr/acre** — Hegadehalli, Nandi foothills, 2-acre parcel (2026)
- **~₹1.7 Cr/acre** — raw 1.5-acre foothills parcel, no approach tar road (2025–26) — the "raw, no conversion, no road" floor
- **₹7,000–9,600/sq.ft** — Devanahalli–Shettigere belt land (Mar 2026), up from ~₹4,500 in 2024 (+60–110% in 24 months)
- **₹60L–2 Cr/acre** — general Nandi Hills farmland band (scenic/water/frontage dependent)

**Implied-value formula for a subject parcel**: state raw (no DC conversion, no road frontage) at the floor (₹2–4 Cr/acre) and with conversion/frontage at the premium (₹5–8 Cr/acre); a 10-acre parcel → ₹20–80 Cr range. Always add the caveat: "verify survey-level guidance value on Kaveri 2.0 before any offer."

## Workflow

1. Resolve the maps short link first (`curl -s -o /dev/null -w "%{url_effective}"` → `!3d<lat>!4d<lng>`) to confirm the parcel's corridor.
2. `web_search` for KIADB compensation + guidance value articles (The Hindu, OneCityProperty, homesok.in) — snippet descriptions carry the numbers.
3. `web_extract` findcirclerate.com for the per-type guidance values.
4. `web_search` for "Nandi Hills OR Devanahalli land sale 'per acre' 2026" for market transactions; treat broker/Instagram posts as listings, not registered deals.
5. Build the benchmark slide: government column (KIADB comp, guidance values, gap, portal) + market column (per-acre deals) + footer note with implied range + Kaveri verification caveat.

## Pitfalls

- **Do NOT claim you pulled a value from the Kaveri portal directly** — it's not reachable from the VPS. Present the guidance values as "Kaveri circle-rate / IGR revised guidelines" and direct the user to verify survey-level values on Kaveri 2.0 themselves.
- **KIADB ₹2.70 Cr/acre is a compensation offer, not a market price** — label it as acquisition compensation; market deals on the same corridor range much higher (₹5.5–8.5 Cr/acre with frontage).
- **Distinguish listings from transactions**: broker/Instagram "for sale" prices are asking prices; only registered-sale figures (rare in public snippets) are true transactions. Say "listings" unless the source says registered.
- **Per-sqft land rates (₹7,000–9,600/sq.ft) are for small developed plots, not farmland per acre** — don't mix the two units on the same slide without labeling.
