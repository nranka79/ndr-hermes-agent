---
name: kalshi
description: "Query Kalshi — the CFTC-regulated US prediction market — for market structure, prices, and orderbook data on sports, politics, economics, and current events. Use when the user asks about Kalshi, 'the regulated prediction market', or names a market that sounds like 'Calci'/'Kashi'/'Kalshe' (common voice-transcription misspellings of Kalshi). Pair with the polymarket skill for cross-platform odds comparison."
version: 1.0.0
author: Hermes Agent
tags: [kalshi, prediction-markets, market-data, sports-betting, odds, sports]
platforms: [linux, macos]
---

# Kalshi — Prediction Market Data

Kalshi is a CFTC-regulated Designated Contract Market (DCM) — the only major
US-regulated exchange where you can trade on the outcome of real-world events.
All event contracts are fully collateralized and binary (Yes/No), settling at
$1.00 if the event occurs, $0.00 if not.

## When to Use

- User asks about Kalshi specifically, or about "the regulated US prediction market"
- User names something that sounds like Kalshi via voice ("Calci", "Kalshe", "Kashi", "Calci odds")
- User wants prediction-market odds on **US political** events (Kalshi is the dominant venue; Polymarket can be geo-blocked)
- User wants prediction-market odds on **sports** (Kalshi has a deep sports book: NFL, World Cup, F1, tennis, golf)
- User wants a cross-platform read alongside Polymarket — see "Cross-platform comparison" below
- User asks "what's the line on X" / "what's Kalshi saying about Y"

## Key Concepts

- **Series** = a category/template (e.g. `KXMENWORLDCUP`, `KXWCGAME`, `KXNFLGAME`)
- **Market** = a single binary contract within a series (e.g. `KXMENWORLDCUP-26-FR` = "Will France win the 2026 Men's World Cup?")
- **Tickers** encode the question — e.g. `KXWCADVANCE-26JUL15ENGARG-ENG` = "England vs Argentina on Jul 15, England advances"
- Prices are in cents ($0.00–$1.00); probability = price in cents / 100
- **Public read endpoint** exposes market **structure** (titles, tickers, descriptions, rules) but NOT live bid/ask or last-trade prices. See "Price data" below for why.
- Trading is US-only (Kalshi is geo-restricted); public data is globally readable

## API Endpoints

Base URL: `https://api.elections.kalshi.com/trade-api/v2`

All endpoints below are **GET**, return JSON, and need **no auth** for public reads.
(Authenticated endpoints exist for trading and live orderbook — those need a
Kalshi account + API key.)

### List markets (by series)

```
GET /markets?series_ticker=KXSERIES&status=open&limit=200
```

Paginate with `&cursor=...` from the previous response's `cursor` field. Stop
when `cursor` is empty.

### List markets (broad scan)

```
GET /markets?status=open&limit=200
```

Iterate through all pages. With ~11k series this is slow — prefer
`series_ticker=...` when you know the series.

### List series (to discover series tickers)

```
GET /series?limit=500
```

Returns the full series catalog. Use this to find the right ticker for a topic.

## Price Data — The Critical Caveat

The public `/markets` endpoint **returns the market but with no price fields
populated** — `last_price`, `yes_bid`, `yes_ask` all come back `null`. To get
live prices you need to:

1. **Authenticate** with a Kalshi account (US only — uses email login + RSA key pair) and call the authenticated `/markets` or `/orderbook` endpoint, OR
2. **Scrape kalshi.com** for the specific market page (HTML, not API), OR
3. **Use the orderbook endpoint directly** — `/markets/{ticker}/orderbook` requires auth for live data

For the **probability read**, workarounds:
- Many markets have a public "implied probability" displayed on the event page
- For tournament brackets, cross-reference with Polymarket (which IS fully public) to get prices
- If the user only needs the bracket (not prices), Kalshi's public endpoint is sufficient — the ticker tells you the matchup

## Workflow

1. **Identify the series ticker** — search `/series?limit=500` for keywords in the `title` field. Common patterns:
   - `KXWCGAME`, `KXWCADVANCE`, `KXWCSPREAD`, `KXMENWORLDCUP`, `KXMWORLDCUP` — FIFA World Cup
   - `KXNFLGAME`, `KXNFLSPREAD`, `KXNFLTOTAL`, `KXNFLMVP` — NFL
   - `KXNBAGAME`, `KXMLSGAME`, `KXEPLGAME` — other sports
   - `KXPRES`, `KXTRUMP`, `KXSENATE` — US politics
2. **Pull all markets in the series** with `/markets?series_ticker=...&status=open`
3. **Present the structure** — titles + tickers + (if available) prices
4. **For prices**: if user is on a US IP and has a Kalshi account, suggest authenticated reads; otherwise cross-reference with Polymarket

## Ticker Patterns Worth Knowing

Match-level markets on Kalshi follow a consistent encoding that includes the date:
- `KXWCADVANCE-26JUL15ENGARG-ENG` → 2026-Jul-15, ENG vs ARG, England advances
- `KXWCSPREAD-26JUL14FRAESP-FRA2` → 2026-Jul-14, FRA vs ESP, France wins by 1.5+
- `KXWCROUND-26FINAL-FRA` → 2026 Final round, France qualifies
- `KXWCMATCHUP-26FIN-FRAENG` → Final will be France vs England
- `KXWCSTAGEOFELIM-26ESP-SF` → Spain eliminated in Semifinals

Date format: `YYMMMDD` (e.g. `26JUL15`). Useful for parsing fixtures from tickers.

## Cross-Platform Comparison (Polymarket ↔ Kalshi)

When a user wants odds from "both" platforms:

| Aspect | Polymarket | Kalshi |
|---|---|---|
| Geo-blocked? | No (read) / Yes (trade) | No (read) / US-only (trade) |
| Public prices? | **Yes** (via Gamma API) | **No** (structure only) |
| Liquidity | Crypto-native, deeper on longshots | Cash, deeper on US sports/politics |
| Tournament brackets | Yes (per-team "reach X" markets) | Yes (per-match "advance" markets) |
| Best for | Cross-market quotes, niche events | US sports, US politics, regulated contracts |

**Recommended pattern**: hit Polymarket for live prices; hit Kalshi for bracket
structure + cross-check that the right matches/markets exist. If Polymarket
prices are missing, Kalshi structure alone is still useful for confirming the
field and round structure.

## Rate Limits

- 429 (Too Many Requests) fires quickly when scanning many series in a loop. Add a 1–2 second sleep between series-ticker fetches when batch-pulling more than ~5 series.
- Cursor pagination is the only built-in throttle mechanism; the API does not return a `Retry-After` header in the 429 response, so simple backoff is the practical approach.

## Limitations

- Public read API does NOT return prices (`last_price`, `yes_bid`, `yes_ask` are all null)
- Trading is US-only with full KYC; international users can read but not trade
- Authenticated reads need a Kalshi account + API key generation (RSA key pair)
- The "/series?limit=500" endpoint can return very large responses — for broad topic discovery, prefer targeted searches via `/markets?series_ticker=...` once you have a candidate ticker

## Pitfalls

### Public endpoint has no prices — don't pretend it does

A common mistake is to fetch `/markets?series_ticker=KXMENWORLDCUP` and report
the "prices" — they're all `null`. Either:
- Acknowledge the price gap explicitly in the response, OR
- Cross-reference with Polymarket, OR
- Authenticate and re-query (only viable for US users)

### "Calci" / "Kalshe" / "Kashi" are voice-transcription misses of Kalshi

When a user says "Calci" or similar in a prediction-market context, they mean
Kalshi. Don't ask for clarification — name Kalshi, proceed, and flag the
assumption in the response so the user can correct if wrong.

### Series ticker guessing doesn't work — the catalog is huge

There is no obvious naming convention across all 11k+ series. Don't guess
tickers like `KXWORLDCUPWINNER`; query `/series?limit=500` and grep the
`title` field. Once you find one good series ticker, related ones cluster
(e.g. `KXWCGAME`, `KXWCADVANCE`, `KXWCSPREAD` all use the `KXWC*` prefix for World Cup).

### 429 on batch series pulls

Pulling 10+ series tickers in quick succession will get rate-limited. Add
`time.sleep(1.5)` between calls in a loop, or use a single `series_ticker=A,series_ticker=B,...`
query (note: Kalshi's API does NOT support comma-separated series_ticker —
you must loop).

## See Also

- `polymarket` skill — for live prices on the same events
- `primary-source-tracing` — for tracing news claims back to the underlying Kalshi market
