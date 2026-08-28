# Indian Real-Estate Research-Firm Source Roster

Quick-reference map of *which* Indian real-estate research firm publishes *what*, and where to find the underlying report. This is the answer to "the news article cited *a report* — which one?" for the most common firms covering the Indian residential / commercial market.

Last updated: 12 July 2026 (verified live during the Knight Frank H1 2026 housing-sales trace).

## The big seven

### Knight Frank India
- **Reports**: H1 (Jan–Jun), H2 (Jul–Dec), Y-end (Dec). Plus India Real Estate Office+Residential combined report each half.
- **City basket**: **8 cities default** — Mumbai, Delhi-NCR, Bengaluru, Pune, Hyderabad, Kolkata, Chennai, **Ahmedabad**.
- **Coverage of H1 2026 (verified July 2026)**:
  - Total: 1,71,471 units, +1% YoY
  - Mumbai 47,355 (+1%), 28% of national
  - Delhi-NCR 24,862 (-7%)
  - Bengaluru 27,968 (+5%)
  - Chennai 9,198
  - Pune, Hyderabad, Kolkata, Ahmedabad — in PDF only
- **Research portal**: https://www.knightfrank.co.in/research
- **Gating**: PDF download requires First Name / Last Name / Email / Company / Job Title / Country / Phone form. POSTing programmatically returns 200 but no direct PDF URL — server-side session-validated. The page has a thumbnail cover image and a "Download" modal triggered by `data-kf-ajax-form="intelligencelabdownloadform"`.
- **NOT mirrored on** `knightfrank.com` (404s confirmed July 2026).
- **Chairman & MD**: Shishir Baijal (often quoted in coverage).
- **Free data points**: covered in detail by Outlook Money, Moneycontrol, The Hindu, The Times of India, HT, Fortune India within 1–2 days of release.

### Anarock
- **Reports**: Quarterly (Q1/Q2/Q3/Q4). Plus annual "Real Estate Industry in India" report.
- **City basket**: **7 cities default** — Mumbai, Delhi-NCR, Bengaluru, Pune, Hyderabad, Chennai, Kolkata (no Ahmedabad).
- **Coverage of Q2 2026 (29 Jun 2026 release, verified)**: "Housing sales fall 6% in Q2; launches rise 7%" — Fortune India.
- **Gating**: similar to Knight Frank — registration wall.
- **Causality angle**: Anarock reports often attribute demand softness to specific events (e.g. "West Asia war weighs on demand" — 29 Jun 2026).
- **Often conflated with Knight Frank** in coverage because the windows overlap. Always check the city count and time window before comparing.

### JLL India (Jones Lang LaSalle)
- **Reports**: Residential, Office, Retail, Industrial + Capital Markets. Each released semi-annually and ad-hoc.
- **City basket**: 7–8 cities depending on report.
- **Format**: "India Real Estate Outlook" series.
- **Useful for**: office-market data, institutional investment, data centres (JLL has a strong data-centre India report).

### Colliers India
- **Reports**: H1, H2, full-year, plus "India Real Estate Investment Report" (covered in H1 2026 coverage as "India Real Estate Investment Report H1 2026" — released 2 Jul 2026).
- **Useful for**: institutional investment volume, grade-A office, data centres, life-sciences.
- **City basket**: varies, usually 8–10.

### CREDAI
- **Industry body**, not a research firm. Releases sentiment indices and lobby positions.
- **CREDAI-NAREDCO joint sentiment index** is the most-cited — Knight Frank and NAREDCO partner on the India Real Estate Sentiment Index.

### NAREDCO (National Real Estate Development Council)
- Industry body under MoHUA. Releases affordability reports, regulatory positions, and the quarterly Sentiment Index (often with Knight Frank).
- **NAREDCO Real Estate Conclave 2026** — annual event, 20 Jun 2026 (KPMG partnered).

### PropTiger / Magicbricks / Housing.com / 99acres / NoBroker
- **Portal-level data**, often only cited for asking-price / listed-inventory metrics. They don't issue formal H1/H2 reports.
- **PropTiger annual price-growth report** — "Housing Price Growth Moderates Across Top 8 Cities to 6% in 2025" (6 Feb 2026, Realty Today) is the main one.
- **Magicbricks** — "Avg housing prices in New Gurugram at nearly Rs 14K/sq ft" type articles; useful for sub-market price points.

## Government / regulator sources

- **RBI** — quarterly macroprudential / housing-finance data; residential price index; bank-credit to housing.
- **SEBI** — REIT / InvIT filings, listed-developer disclosures.
- **MCA (Ministry of Corporate Affairs)** — listed-developer annual reports.
- **MoHUA (Ministry of Housing and Urban Affairs)** — PMAY data, CLSS uptake, RERA rules.
- **State RERAs** — MahaRERA, UP-RERA, HRERA, K-RERA, TN-RERA, RERA Odisha, etc. Each has its own project-registration database.
- **State IGR (Inspector General of Registrations)** — actual stamp-duty / property-registration data. The "Mumbai 80,000+ registrations in H1 2026" figure is from IGR, not Knight Frank.

## The "data of the data" — what the firms themselves rely on

| Firm | Underlying data source |
|---|---|
| Knight Frank | Developer sales (builder reports), RERA project-level data, broker data |
| Anarock | Developer sales + portal listings + RERA |
| JLL | Direct occupier surveys + office-lease data + capital-markets transactions |
| Colliers | Capital-markets deal database + occupier surveys |
| PropTiger | Portal listings + sold-price when disclosed |
| IGR (state) | Stamp-duty registrations — the only true "closed deal" count |
| RERA (state) | Project registrations, not transaction data |

**Caveat**: All the developer-data firms count *sales* which can include pre-launch / soft-launch reservations that may not convert to registrations. The IGR registration count is the only count of actually-completed transactions. When "Mumbai did 80,000+" comes up, it's IGR. When "Mumbai did 47,355" comes up, it's Knight Frank.

## Common headline patterns and what they mean

| Headline | What it usually is | Window | City count |
|---|---|---|---|
| "Housing sales fall X%" | Anarock Q2 | Apr–Jun | 7 |
| "1.71 lakh homes sold" | Knight Frank H1 | Jan–Jun | 8 |
| "80,000 property registrations" | IGR Mumbai H1 | Jan–Jun | 1 (Mumbai) |
| "Premium housing demand doubles" | Knight Frank | Jan–Jun | 8 |
| "Sentiment index turns cautious" | Knight Frank–NAREDCO quarterly | Q1/Q2/Q3/Q4 | pan-India |
| "Housing Price Growth Moderates to X%" | PropTiger annual | Jan–Dec | 8 |
| "₹X lakh crore real estate investment" | Colliers investment report | H1/H2/FY | pan-India |
| "China property crisis parallels" | Editorial comparison, not Indian data | n/a | n/a |

## Reusable troubleshooting tips

- When you see "according to a report" in an Indian real-estate article, the firm is almost always one of: Knight Frank, Anarock, JLL, Colliers, CREDAI, NAREDCO, PropTiger.
- When the city count isn't specified, check whether "Ahmedabad" appears in the breakdown — if it does, the source is 8-city (Knight Frank / Colliers). If it doesn't, it's 7-city (Anarock).
- When the headline says "Q1" or "Q2", it's almost always Anarock or NAREDCO. When it says "H1" or "H2", it's Knight Frank / Colliers / JLL.
- "Mumbai + Pune" sub-basket without NCR = Colliers India Real Estate Outlook (data centres, luxury).
- Direct H1/H2 Knight Frank India press releases don't exist on the firm's newsroom — the newsroom is JS-rendered. The data appears via Outlook Money / Moneycontrol / The Hindu / Fortune India / HT / TOI / BW Businessworld within 24–48 hours of release.
