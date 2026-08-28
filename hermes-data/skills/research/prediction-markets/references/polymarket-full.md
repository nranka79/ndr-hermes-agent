---
name: polymarket
description: "Query Polymarket: markets, prices, orderbooks, history."
version: 1.0.0
author: Hermes Agent + Teknium
tags: [polymarket, prediction-markets, market-data, trading]
platforms: [linux, macos, windows]
---

# Polymarket — Prediction Market Data

Query prediction market data from Polymarket using their public REST APIs.
All endpoints are read-only and require zero authentication.

See `references/api-endpoints.md` for the full endpoint reference with curl examples.

## When to Use

- User asks about prediction markets, betting odds, or event probabilities
- User wants to know "what are the odds of X happening?"
- User asks about Polymarket specifically
- User wants market prices, orderbook data, or price history
- User asks to monitor or track prediction market movements

## Key Concepts

- **Events** contain one or more **Markets** (1:many relationship)
- **Markets** are binary outcomes with Yes/No prices between 0.00 and 1.00
- Prices ARE probabilities: price 0.65 means the market thinks 65% likely
- `outcomePrices` field: JSON-encoded array like `["0.80", "0.20"]`
- `clobTokenIds` field: JSON-encoded array of two token IDs [Yes, No] for price/book queries
- `conditionId` field: hex string used for price history queries
- Volume is in USDC (US dollars)

## Three Public APIs

1. **Gamma API** at `gamma-api.polymarket.com` — Discovery, search, browsing
2. **CLOB API** at `clob.polymarket.com` — Real-time prices, orderbooks, history
3. **Data API** at `data-api.polymarket.com` — Trades, open interest

## Typical Workflow

When a user asks about prediction market odds:

1. **Search** using the Gamma API public-search endpoint with their query
2. **Parse** the response — extract events and their nested markets
3. **Present** market question, current prices as percentages, and volume
4. **Deep dive** if asked — use clobTokenIds for orderbook, conditionId for history

## Presenting Results

Format prices as percentages for readability:
- outcomePrices `["0.652", "0.348"]` becomes "Yes: 65.2%, No: 34.8%"
- Always show the market question and probability
- Include volume when available

Example: `"Will X happen?" — 65.2% Yes ($1.2M volume)`

## Parsing Double-Encoded Fields

The Gamma API returns `outcomePrices`, `outcomes`, and `clobTokenIds` as JSON strings
inside JSON responses (double-encoded). When processing with Python, parse them with
`json.loads(market['outcomePrices'])` to get the actual array.

## Rate Limits

Generous — unlikely to hit for normal usage:
- Gamma: 4,000 requests per 10 seconds (general)
- CLOB: 9,000 requests per 10 seconds (general)
- Data: 1,000 requests per 10 seconds (general)

## Limitations

- This skill is read-only — it does not support placing trades
- Trading requires wallet-based crypto authentication (EIP-712 signatures)
- Some new markets may have empty price history
- Geographic restrictions apply to trading but read-only data is globally accessible

## Pitfalls & Cross-Cutting Patterns

### `public-search` wraps results under `events`, not a bare list

`/public-search?q=...` returns `{"events": [...], "pagination": {...}}`. A common first attempt is `json.load(...)` treating the response as a list — that errors with `AttributeError: 'str' object has no attribute 'get'`. Always read `d.get("events", [])` first, then iterate.

### Tournament brackets: prefer the "Exact Matchup" market, not per-team reach markets

For events like World Cup / Champions League brackets, the cleanest source of truth is the *exact matchup* market (e.g. `World Cup: Semifinals Exact Matchup`). It locks the bracket to one Yes-100% outcome and is faster to read than N per-team "reach the round" markets. Cross-check with the per-team "reach the final" / "stage of elimination" markets to derive runner-up probabilities.

### When the user names a non-existent market ("Calci", "Polymath", etc.)

The two real prediction markets are **Polymarket** and **Kalshi**. If the user names something that doesn't exist (typo, mishearing, brand confusion), say so explicitly, name the likely intended platform, and proceed — do not silently fail or invent a fictional one. **When you hear anything that sounds like "Calci", "Kashi", "Kalshe", "Calshi" — that is Kalshi.** Load the `kalshi` skill immediately and add its numbers alongside the Polymarket read; the cross-platform comparison is the whole point of the question. See the `kalshi` skill for the regulated-US-exchange counterpart and the recommended cross-platform read pattern.
