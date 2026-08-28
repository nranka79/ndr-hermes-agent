---
name: portfolio-research-report
description: Generate comprehensive HTML research reports for a stock portfolio — yfinance-driven 6-month performance, monthly bar charts, earnings analysis, and buy/hold/sell verdicts per holding.
category: productivity
triggers:
  - "research my portfolio"
  - "analyze my stocks"
  - "stock research report"
  - "detailed analysis of these stocks"
  - "how are my stocks performing"
  - "portfolio deep-dive"
  - "check my holdings"
  - "stock performance analysis"
---

# Portfolio Research Report

Generate a comprehensive, professional HTML research report for an investment portfolio. The report covers monthly performance bar charts, earnings beats/misses, analyst metrics, and a per-stock verdict.

## Pipeline

### 1. Install yfinance

```bash
cd /opt/data && source .venv/bin/activate && uv pip install yfinance -q
```

If the venv doesn't exist:
```bash
cd /opt/data && uv venv .venv && source .venv/bin/activate && uv pip install yfinance
```

### 2. Fetch Stock Data

Use `/opt/data/.venv/bin/python3` as the interpreter. For each stock:

```python
import yfinance as yf
import pandas as pd

ticker = yf.Ticker(symbol)
df = yf.download(symbol, start="2026-01-01", end="2026-08-24", progress=False, auto_adjust=False)
close = df['Close'].squeeze()  # CRITICAL: yfinance returns multi-index DataFrame; squeeze() extracts Series
```

#### Monthly Performance
```python
monthly = close.resample('ME').last()
monthly_pct = monthly.pct_change() * 100
```

#### Earnings
```python
earnings = ticker.earnings_dates.sort_index(ascending=False)
# Last 2 quarters
for idx in earnings.head(2).index:
    row = earnings.loc[idx]
    eps_est = float(row.get('EPS Estimate', 0)) if pd.notna(row.get('EPS Estimate', None)) else None
    eps_rep = float(row.get('Reported EPS', 0)) if pd.notna(row.get('Reported EPS', None)) else None
```

#### Key Stats
```python
info = ticker.info
pe = info.get('forwardPE', info.get('trailingPE', 'N/A'))
mc = info.get('marketCap', 'N/A')
```

#### News Headlines (for sentiment context)
```python
news = ticker.news
for item in news[:25]:
    title = item.get('title', '')
    # Classify positive/negative based on keywords
```

### 3. Generate HTML Report

Key structural elements:

- **Dark theme** (`--bg: #0f0f1a`, `--card: #1a1a2e`, `--accent: #00d4ff`)
- **Header** with portfolio value and date
- **Summary cards** (best/worst performer, earnings beats, market caps)
- **Per-stock cards** with:
  - Ticker + sector tags (color-coded: AI=cyan, Cloud=purple, ETF=pink, etc.)
  - Current price + cost basis (if known) + 6M change
  - CSS-only monthly bar chart (7 bars, Feb–Aug)
  - Earnings table (last 2 quarters with beat/miss badges)
  - Analysis paragraph + verdict badge
- **Portfolio summary table** ranked by 6M performance
- **Verdict dashboard** (Strong Buy/Buy / Hold / Sell cards)
- **Key takeaways** (concentration risk, valuation dispersion, earnings momentum)
- Disclaimer footer

#### Bar Chart Calculation

Map each monthly % change to a bar height using proportional scaling:
- The chart container is 120px tall
- The max bar represents 100% (scale based on largest absolute value in the set)
- Positive bars: gradient green; Negative bars: gradient red

```html
<div class="bar-group">
  <div class="bar negative" style="height:44%"></div>
  <div class="bar-value red">-7.3</div>
  <div class="bar-label">Feb</div>
</div>
```

#### Verdict Badges
```html
<div class="verdict strong-buy">🟢 STRONG BUY — ...</div>
<div class="verdict buy">🟢 BUY — ...</div>
<div class="verdict hold">🟡 HOLD — ...</div>
<div class="verdict sell">🔴 SELL — ...</div>
```

### 4. Deliver

Send the HTML file path as a MEDIA attachment via Telegram.

## Pitfalls

- **yfinance multi-column index:** `df['Close']` returns a DataFrame, not a Series. Always call `.squeeze()` to get a proper Series before `.resample()`.
- **yfinance datetime iteration:** The index items from `.items()` may be Timestamp or str depending on yfinance version. Check `hasattr(dt, 'month')` before accessing `.month`.
- **Earnings data:** ETFs (ARKK, ARKW) return `None` for earnings_dates. Handle gracefully with try/except.
- **Analyst recommendations:** `ticker.recommendations_summary` may be None. Fall back to web search or omit.
- **News keyword classification:** Simple positive/negative keyword matching is approximate. Don't present as definitive sentiment.
- **HTML file size:** ~45-50KB for 10 stocks. Keep self-contained (no external CSS/JS).
- **Cost basis:** Always ask or use the user's stated average price. Never guess.
- **Always include disclaimer:** "Not financial advice. Past performance ≠ future results."

## User Preferences (NDR-style)

- Dark theme (consultant/investor-grade presentation)
- Lead with summary numbers, then per-stock deep-dive
- Verdict must be actionable (Strong Buy / Buy / Hold / Sell) — never ambiguous
- Always flag concentration risk if a single position > 20% of portfolio