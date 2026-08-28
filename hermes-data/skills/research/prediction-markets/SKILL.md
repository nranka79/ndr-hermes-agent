---
name: prediction-markets
description: "Query prediction market data from Polymarket (decentralized, crypto) and Kalshi (CFTC-regulated, US) — search markets, read prices/orderbooks, and compare cross-platform odds. All read-only, no authentication needed for Polymarket; Kalshi public API provides structure but requires auth for live prices."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [prediction-markets, polymarket, kalshi, odds, trading, sports, politics]
    category: research
---

# Prediction Markets — Cross-Platform Data

Query prediction market odds, structure, and prices from the two major platforms: **Polymarket** (decentralized, crypto-native) and **Kalshi** (CFTC-regulated US exchange).

## When to Use

- User asks about prediction markets, betting odds, event probabilities
- User names a market platform — "Polymarket", "Kalshi", or a voice-mangled version ("Calci", "Kalshe", "Kashi")
- User wants cross-platform comparison of the same event's odds
- User asks "what are the odds of X happening?"

## Quick Decision: Which Platform?

| Need | Best Platform |
|------|--------------|
| Live prices (public) | Polymarket — fully public Gamma API |
| Regulated US market | Kalshi — CFTC-regulated DCM |
| US sports/politics odds | Kalshi (deeper in these categories) |
| Niche / longshot events | Polymarket (crypto liquidity on any topic) |
| Tournament brackets | Both — use Polymarket for prices, Kalshi for structure |

---

## Polymarket — Live Prices (Public, No Auth)

**API base:** `gamma-api.polymarket.com`, `clob.polymarket.com`, `data-api.polymarket.com`

### Quick Start

```bash
# Search for a market
curl -s "https://gamma-api.polymarket.com/events?limit=10&closed=false&tag=sports"

# Search by keyword
curl -s "https://gamma-api.polymarket.com/search?q=FIFA+World+Cup&limit=5"
```

### Key Concepts

- **Events** contain one or more **Markets** (binary Yes/No), price 0.00-1.00 = probability
- `outcomePrices` is a JSON-encoded string like `["0.65", "0.35"]` — parse with `json.loads()`
- Volume is in USDC (USD)
- All endpoints are **read-only, no auth required**

### Typical Workflow

1. Search via Gamma API with the user's query
2. Parse response — extract events and nested markets
3. Present prices as percentages (e.g. "Yes: 65.2%, No: 34.8%")
4. Deep dive with `clobTokenIds` for orderbook, `conditionId` for history

### Search (Gamma API)

```bash
GET /events?tag=sports&closed=false&limit=10
GET /events?closed=false&limit=10&title_contains=world+cup
GET /search?q=world+cup+winner
```

### Market Prices

```bash
# By token ID (from event)
GET https://clob.polymarket.com/book/<token_id>/book?side=SELL

# Price history by condition ID
GET https://clob.polymarket.com/prices/<condition_id>
```

### Rate Limits

| API | Limit |
|-----|-------|
| Gamma | 4,000 req / 10 seconds |
| CLOB | 9,000 req / 10 seconds |
| Data | 1,000 req / 10 seconds |

### Pitfalls

- `public-search` wraps results under `events` key — read `d.get("events", [])`
- `outcomePrices`, `outcomes`, `clobTokenIds` are JSON-encoded strings inside JSON — double-parse with `json.loads()`
- Tournament brackets: prefer "Exact Matchup" market over per-team reach markets
- "Calci", "Polymath" voice errors → the user means Polymarket or Kalshi — check context

### Reference

`references/polymarket-api-endpoints.md` — full endpoint reference with curl examples.

---

## Kalshi — US Regulated Exchange (Structure Public, Prices Need Auth)

**API base:** `https://api.elections.kalshi.com/trade-api/v2`

### Quick Start

```bash
# List series (categories) to find the right ticker
curl -s "https://api.elections.kalshi.com/trade-api/v2/series?limit=500"

# List markets in a series
curl -s "https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXNFLGAME&status=open&limit=200"
```

### Key Concepts

- **Series** = category/template (e.g. `KXMENWORLDCUP`, `KXNFLGAME`)
- **Market** = single binary contract within a series
- Prices are in cents ($0.00-$1.00); probability = price_cents / 100
- **Public endpoint does NOT return live prices** — `last_price`, `yes_bid`, `yes_ask` are all null

### Workflow

1. Identify series ticker — search `/series?limit=500` for keywords in `title`
2. Pull all markets in series — `/markets?series_ticker=...&status=open`
3. Present structure (titles, tickers, descriptions, rules)
4. For prices: use **Polymarket cross-reference** or Kalshi authenticated session

### Common Series Tickers

| Prefix | Category |
|--------|----------|
| `KXWCGAME`, `KXWCADVANCE`, `KXWCSPREAD`, `KXMENWORLDCUP` | FIFA World Cup |
| `KXNFLGAME`, `KXNFLSPREAD`, `KXNFLTOTAL`, `KXNFLMVP` | NFL |
| `KXNBAGAME`, `KXMLSGAME`, `KXEPLGAME` | Sports |
| `KXPRES`, `KXTRUMP`, `KXSENATE` | US Politics |

### Pitfalls

- Public endpoint has **no prices** — acknowledge this explicitly, don't report nulls
- Series catalog has ~11k entries — don't guess tickers, always query
- 429 rate limit fires quickly on batch pulls — add 1-2s sleep between series fetches
- No `Retry-After` header on 429 — implement simple backoff

### Cross-Platform Comparison

| Dimension | Polymarket | Kalshi |
|-----------|-----------|--------|
| Prices public? | Yes | No (structure only) |
| Best for | Live quotes, niche events | US sports/politics, regulated |
| Liquidity | Crypto-native | Cash, deeper on US markets |
| Tournament brackets | Per-team reach markets | Per-match advance markets |

**Recommended**: hit Polymarket for live prices; hit Kalshi for bracket structure + to confirm which matchups exist.

---

## Version

1.0.0 — merged from standalone polymarket (v1.0.0) and kalshi (v1.0.0) skills.
