# Government Research — Absorbed from research/government-research

## What This Reference Covers

Government research umbrella covering: Indian equity/financial research (yfinance), land record due diligence for DRAAS property transactions, and government web portal automation.

**Skill status:** Absorbed into `legal-document-drafting` umbrella (2026-05-29). Original at `research/government-research/`.

## Decision Tree

```
What research task?
├── Indian equity / financial data (NSE/BSE stocks)
│   └── → Equity Research (references/equity-research.md)
├── Land record due diligence for DRAAS property
│   ├── Karnataka → Karnataka Land Services (references/land-record-research.md)
│   └── Tamil Nadu → TN Land Records (references/tamil-nadu-land-records.md)
└── Government web portal automation
    └── → Government Portal Automation (references/government-portal-automation.md)
```

## Key Research Types

### Equity Research (yfinance)

```python
import yfinance as yf
ticker = yf.Ticker("RELIANCE.NS")
info = ticker.info
financials = ticker.financials
balance_sheet = ticker.balance_sheet
```

### Karnataka Land Records

- **IGR Karnataka** (guideline value/circle rate): `https://igr.karnataka.gov.in/page/Revised+Guidelines+Value/en`
- District → Taluk → Hobli → Village navigation
- **Known blocklist** (IPs block external connections): `igr.karnataka.gov.in`, `kaverionline.karnataka.gov.in`, `kgis.karnataka.gov.in`, `bbhoomi.karnataka.gov.in` — stop after 2 failed attempts; give user the URL + steps

### Tamil Nadu Land Records

- Hosur/Bagalur SRO jurisdiction
- Encumbrance Certificate, Gift Deed, Partition Deed, layout approval
- **Hosur = Karnataka jurisdiction** (not Tamil Nadu) despite proximity to state border

## Voice Transcription Notes

- "Dissousa" = D'Souza Layout (Whitefield, Bengaluru)
- Google Maps: `D' Souza Layout, Ashok Nagar, Bengaluru, PIN 560001`
