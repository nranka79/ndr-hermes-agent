# Indian Pre-IPO & Unlisted Stock Research

Research workflow for verifying unlisted/pre-IPO share purchases and estimating IPO returns. Useful when a user has bought unlisted shares (NSE, etc.) and wants to understand potential IPO value.

## Workflow

### 1. Extract Purchase Details from Gmail

Search the user's Gmail for the transaction thread:

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')

# Find the thread — use subject line fragments and sender emails
results = gmail.users().messages().list(
    userId='me',
    q='subject:"Confirmation" NSE OR "Valiant Fintech" OR "Infinyte" kishan@flamebackcapital.com'
).execute()
```

Pull key transaction fields from the thread:
- Number of shares, price per share, total consideration
- Statutory charges, grand total
- Facilitator/seller names
- Fund transfer timeline
- Any bonus/split clauses in the terms

### 2. Check Corporate Actions (Bonus/Splits)

Bonus issues and stock splits dramatically change share count and per-share cost basis. Search for them:

```python
from ddgs import DDGS
with DDGS() as ddgs:
    for r in ddgs.text("NSE 4:1 bonus November 2024 record date", max_results=5):
        print(r['title'], r['href'], r.get('body','')[:200])
```

Key things to confirm:
- Bonus ratio (e.g. 4:1 = 4 bonus shares per 1 held)
- Record date — relative to when the transaction completed
- If shares were in transfer during the record date, whether the buyer got the bonus

### 3. Research Current Unlisted/Grey Market Price

Multiple sources for unlisted prices:

```python
# Current price
for r in ddgs.text("NSE unlisted share price 2026", max_results=5):
    print(r['title'], r.get('body','')[:200])

# Price history (helps establish cost basis post-bonus)
for r in ddgs.text("NSE unlisted share price history 2024 2025", max_results=5):
    print(r['title'], r.get('body','')[:200])
```

Always check 2-3 sources — unlisted prices vary across platforms.

### 4. Research IPO Status

Use `ddgs.news()` for the latest IPO developments:

```python
for r in ddgs.news("NSE DRHP IPO SEBI filing", max_results=5):
    print(r['date'], r['title'], r['url'])
```

Also text search analyst estimates:

```python
for r in ddgs.text("NSE IPO estimated price band 2026", max_results=5):
    print(r['title'], r.get('body','')[:300])
```

### 5. Calculate Return Scenarios

Present scenarios based on whether bonus was received:

| Scenario | Shares | Cost/Share | Value at ₹X | Return |
|----------|--------|------------|-------------|--------|
| Without bonus | 450 | ₹5,650 | ₹9,00,000 | — |
| With 4:1 bonus | 2,250 | ~₹1,131 | ₹45,00,000 | ~77% |

## NSE IPO Key Data Points (June 2026)

| Field | Value |
|-------|-------|
| DRHP filed | 18 June 2026 |
| IPO size | ~₹30,000 crore |
| Structure | 100% OFS |
| Shares on offer | 14.89 crore (~6% equity) |
| Face value | ₹1 |
| Estimated IPO price | ₹1,900–2,000 (from IPO math) |
| Current unlisted | ₹2,000–2,160 |
| Implied valuation | ~₹5 lakh crore ($55B) |
| Bonus issue | 4:1, record date 2 Nov 2024 |
| FY26 revenue | ₹16,601 Cr |
| FY26 net profit | ₹10,302 Cr |

## Sources

- **Unlisted prices**: InCred Money, UnlistedZone, SharesCart, UnlistedArena, stockify
- **Corporate actions**: NSE India announcements, news articles
- **IPO news**: Economic Times, Moneycontrol, Business Standard, Business Today, Mint, Financial Express
- **Valuation analysis**: Analyst reports on Moneycontrol, PL Capital, Dhan, m.Stock

## Pitfalls

- **Bonus vs. no-bonus is the key uncertainty** in pre-IPO purchases made near a record date. The email thread may have cancellation clauses if bonus falls during transfer. Always flag this for the user to clarify with the intermediary.
- **IPO price is often below grey market** — analysts expect issuers to leave "money on the table" for IPO subscribers. Don't assume grey market = listing price.
- **Unlisted prices vary across platforms** — cross-reference 3+ sites before reporting a range.
- **Timeline uncertainty** — DRHP → SEBI approval → RHP → IPO can take 3-12 months. The IPO may not happen at all (regulatory hurdles, market conditions).
- **Face value changes** — check if face value changed (₹10→₹1 often means a split). Adjust historical prices accordingly.
