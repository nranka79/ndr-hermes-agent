# Bagmane Texworth / RLDA Commercial CCD Investment Note (June 2026)

**DO NOT use the green/dark Spark Fee model for this.** This is a completely different asset class (Grade-A commercial equity via CCDs → REIT) vs land plot reservation.

## When to Use

The user shares a real estate investment opportunity involving:
- A commercial development (office/retail) on RLDA railway land
- Investment via CCDs (Compulsorily Convertible Debentures) in an SPV
- Exit via REIT (Real Estate Investment Trust) listing
- The opportunity is structured through a partnership vehicle (e.g. Roma Ventures) holding CCDs
- Target investor: ultra-HNI / commercial investor (e.g. Sindhi Marwadi)

## Design System — Navy/Gold Theme

```css
:root {
  --navy: #1a365d;
  --navy-light: #2d4a6b;
  --gold: #c9a961;
  --gold-light: #fef5e7;
  --dark: #1a202c;
  --muted: #4a5568;
  --text: #1a1a1a;
  --bg: #f8f9fa;
  --card-bg: #ffffff;
  --success: #38a169;
  --pending: #ecc94b;
  --hc-pending: #fed7d7;
}
```

**Typography:** Georgia / Times New Roman (serif) for body text. Helvetica Neue / Arial (sans-serif) for labels, tables, and metrics. The serif body + sans-serif labels gives a premium financial-document feel.

**Cover page:** Full navy gradient background (`linear-gradient(135deg, #1a365d 0%, #2d4a6b 100%)`) with gold badge and white text.

## User Correction History

In the June 2026 session, the user gave **specific structural corrections** after a first draft that was too elaborate (10 pages):

| What was wrong | What was right |
|----------------|----------------|
| Over-emphasized Roma Ventures (intermediate vehicle) | Lead with the **Bagmane brand** and the **asset itself** (14,000 sq ft, Grade-A, Cantonment) |
| Too long (10 pages, 60KB) | Keep to **2 pages max** — investor wants key terms only |
| Too many sections | Only need: Deal Economics, How Value Flows, Status/Timeline |
| Roma's internal structure (Maya Nair history, partnership breakdown) | Irrelevant to the buyer — skip entirely |
| Technical legal terms (ISHA, SHA, SSA) | Translate to plain English — "investor/shareholder agreement" |
| Partnership deed details | Only say "partner in Roma" — no partner history |
| Tax structure buried in text | Lead with **"tax-free during construction + 12.5% LTCG on REIT sale"** |

## Page Structure (2-Page Max)

### Page 1:

**Header:**
- "CONFIDENTIAL INVESTMENT MEMORANDUM" badge in gold
- H1: Focus on **the asset** (e.g. "Core Bangalore Grade-A Commercial Asset")
- Subtitle: "Secure Allocation: 14,000 SQ FT Leasable Space"

**Hero Metrics Row (3 cards, gold top border):**
1. Attributable area (e.g. 14,000 SQ FT)
2. Entry vs Target Value (e.g. 1:4 — ₹15K vs ₹50K)
3. Total Outlay (e.g. ₹21 Cr)

**Two-Column Pitch:**
- Left column (60%): The Opportunity (developer name, land details, security) + Regulatory Status
- Right column (40%): Deal Economics (highlighted box with term rows: Allocated Area, Entry Rate, Total Outlay, Expected Rent, Yield, Cap Rate, Target Multiplier)

### Page 2:

**How Value Flows (blue-tinted flow box):**
- 4-step flow diagram: Partner in Roma → 8% of CCDs → SPV Equity Shares → REIT Units
- Below it: Tax Advantage callout (zero tax during construction, 12.5% LTCG on REIT sale)

**Development Checklist (green-tinted status box):**
- Completed items with green dots + "Done" labels
- Pending items with yellow dots + "Scheduled" labels
- HC pending item with red dot + "Final Hearing July 2026"

**Footer:** Navy gradient bar with Contact (Nishant Ranka), Email, Phone, Address

## Key Messaging Points (from user corrections)

1. **Who is Bagmane:** "One of India's most prominent Grade-A commercial office developers with the most solid balance sheet"
2. **What you get:** Not direct square footage. You get equity in a company. Your equity represents a stake equivalent to 14,000 sq ft of leasable space.
3. **Why REIT critical:** "This entire company will go into a REIT" — until that happens, no taxes. When REIT units come, they trade like stocks. You can sell ₹1 worth or ₹1,000 Cr worth. Only 12.5% LTCG.
4. **Why entry at 1/4 price:** Entering pre-launch at ₹15,000/sq ft vs projected ₹48-50,000/sq ft stabilized value
5. **No capital calls:** All CCDs paid up — investment is fully paid from day 1
6. **No governance complexity:** Roma holds ~1.75 lakh sq ft economic interest. Roma is well-protected. Shareholder structure is fixed — no new shareholders can be added.
7. **Current status language:** "Activist claimed 200-year-old tree... frivolous case, no chance of standing... central govt land. BBMP Forest NOC already deposited in court. Alternate railway quarters completed and handed over. Property barricaded, possession with Bagmane."

## Template Flow

```html
<!-- Page 1 -->
<div class="container">
  <header>
    <span class="badge">Strictly Private &amp; Confidential</span>
    <h1>Core Bangalore Grade-A Commercial Asset</h1>
    <div class="subtitle">Secure Allocation Opportunity: 14,000 SQ FT Leasable Space</div>
  </header>

  <!-- 3 Hero Metrics -->
  <div class="grid-3">
    <div class="metric-card">14,000 SQ FT / Attributable Area / Office + F&B Retail</div>
    <div class="metric-card">1 : 4 Entry / Entry vs Target Value / ₹15,000 vs ₹50,000/sq ft</div>
    <div class="metric-card">₹21 Crore / Total Outlay / Fully Paid Up — No Capital Calls</div>
  </div>

  <!-- Two-Col Pitch -->
  <div class="two-col">
    <div class="left">
      <h2>The Opportunity</h2>
      <p>Bagmane Group, land details, security, timeline...</p>
    </div>
    <div class="right">
      <h2>Deal Economics</h2>
      <div class="deal-terms">
        <!-- term rows -->
      </div>
    </div>
  </div>
</div>

<!-- Page 2 -->
<div class="container">
  <!-- How Value Flows -->
  <div class="flow-box">4-step flow + Tax Advantage</div>

  <!-- Development Checklist -->
  <div class="status-box">5 status rows with colored dots</div>

  <!-- Footer -->
  <footer>Contact information</footer>
</div>
```

## PDF/Print

Set `@page { size: A4; margin: 0; }` in CSS. Use `@media print` for clean output. The design targets browser-print-to-PDF — no Playwright needed.

## Key Number Computations

| Metric | Formula |
|--------|---------|
| Annual rent | 14,000 sq ft × ₹300/sq ft/month × 12 = ₹5,04,00,000 |
| Capital value | ₹5,04,00,000 / 7.5% = ₹67,20,00,000 |
| Entry valuation | ₹15,000 × 14,000 = ₹21,00,00,000 |
| Target valuation | ₹48,000–50,000 × 14,000 = ₹67–70 Cr |
| Multiple | ~3.2–3.3× on capital value |
| Tax (LTCG on REIT) | 12.5% on gains only |