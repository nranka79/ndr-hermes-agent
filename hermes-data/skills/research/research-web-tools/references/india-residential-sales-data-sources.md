# India Residential Sales Data Sources — which firm covers which city

Knowledge bank from Vizag residential-sales research (2026-08-25). Use when a user asks for
"total units sold in <Indian city> 20XX" citing Anarock / Knight Frank / CBRE / JLL.

## Coverage matrix (verified recurring pattern)

| Firm | City-level unit sales coverage | Vizag? |
|------|-------------------------------|--------|
| Anarock | Top 7-8 metros (Mumbai, NCR, Bengaluru, Pune, Hyderabad, Chennai, Kolkata, +Ahmd) | NO |
| Knight Frank | Top 8 metros (annual "India Real Estate" H1/H2) | NO |
| CBRE | Top 9-10 metros (varies by year) | NO |
| JLL | Top metros; occasional old city pages (Vizag page exists ~2023, no 2024-25 series) | NO (standalone) |
| **PropEquity** (P E Analytics, NSE-listed) | **Top 15 tier-2 cities incl. Visakhapatnam, Coimbatore, Kochi, Bhubaneswar, Vadodara, Surat, Nagpur, Nashik, Bhopal, Jaipur, Lucknow, Mohali, Gandhinagar, Goa, Ahmedabad** | **YES — the de-facto city-level source** |

So: when the user says "from Anarock or Knight Frank or CBRE data" for a tier-2 city, the honest
answer is those firms don't publish it; the numbers that exist are PropEquity's (published via PTI
articles in ET/HT/Moneycontrol/Outlook Business/Business Standard). Say so, then deliver the
PropEquity figure with source attribution.

## PropEquity release cadence & revision gotcha

- Full-year release ~mid-Feb of following year (FY2025 released 12-Feb-2026; FY2024 released Feb-2025).
- **Numbers get restated between releases.** Vizag 2024: original Feb-2025 release said **4,258 units**
  (−21% vs 5,361 in 2023, value ₹4,798 Cr); the Feb-2026 release restated 2024 as **3,858 units**
  (−38% basis for 2025). Quote both / say "revised" when the datasets disagree.
- Quarterly reports also exist: Q1-2025 release (CNBC TV18/YoVizag) had Vizag −37% units, −35% value.

## Vizag numbers (PropEquity, as published)

- **2025: 2,406 units** (−38% YoY — steepest among 15 tier-2 cities)
- **2024: 3,858** (revised) / **4,258** (original Feb-2025 report)
- 2023: 5,361
- Top-15 tier-2 totals: 2024 = 1,78,771 units (+4%, ₹1,52,552 Cr +20%); 2025 = 1,56,181 units (−10%, ₹1.48 L Cr flat)
- 2025 city scale (units): Ahmedabad 51,148 · Surat 19,835 · Vadodara 13,798 · Gandhinagar 13,710 ·
  Nashik 11,188 · Jaipur 9,758 · Nagpur 6,260 · Mohali 6,118 · Bhubaneswar 4,885 · Lucknow 4,053 ·
  Coimbatore 3,702 · Bhopal 3,599 · Goa 3,507 · **Visakhapatnam 2,406** · Kochi 2,214

## NDR voice variants for research firms (add to memory list on recurrence)

- "Analog" → Anarock · "Nightfrag" → Knight Frank · "CVRE" → CBRE · "PropEquity" often spoken plainly

## Jina + DuckDuckGo parsing recipe that works (datacenter IP, no API keys)

1. Google News RSS hits give JS-redirect links — find the real publisher URL via Jina DDG search proxy:
   `curl -sS "https://r.jina.ai/https://html.duckduckgo.com/html/?q=<query>"` with UA Mozilla/5.0 (curl,
   not urllib direct, was the reliable path).
2. Jina output is **markdown**, not HTML — extract result links with:
   `re.finditer(r'\]\((https://duckduckgo\.com/l/\?uddg=[^)]+)\)', txt)` then URL-decode the `uddg=` param
   to get the real article URL.
3. Fetch article text via `https://r.jina.ai/<real-url>`; body text starts after the "URL Source" block;
   grep for `visakhapatnam|vizag|unit|sales|\d` lines.
4. For city-wise absolute numbers, the PTI article (Outlook Business / Business Standard) carries the full
   city table — the HT/Moneycontrol versions often only give percentages.