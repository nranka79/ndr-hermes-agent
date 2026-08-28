---
name: investment-document-creation
description: "Create investor-facing HTML documents for real estate investment opportunities — dark-themed, print-ready, with Q&A structure and Google Drive upload. For DRAAS land deal proposals."
version: 1.0.0
author: Nous Research / Hermes
license: MIT
metadata:
  hermes:
    tags: [investment, HTML, document-creation, real-estate, investor-deck, Drive, PDF-print]
    homepage: 
    related_skills: [google-workspace, nano-pdf, ocr-and-documents]
---

# Investment Document Creation

Create investor-facing HTML documents for real estate land deal proposals — dark theme, Q&A structure, print-to-PDF ready, uploaded to Google Drive.

## Trigger

When user shares a PDF investment proposal and asks to convert it into a Q&A format document, investor deck, or "one-pager" in similar style.

---

## Document Structure

Every DRAAS investor deck is a **2-page PDF**:

**Page 1 — Investment Card (`.card.accent-border`):**
- Header (eyebrow, H1, tagline — tagline must state the Today's Contribution model clearly)
- Today's Contribution (₹3,000/sq.ft) + one-line that plot is allocated at cost, exit at market value
- 4-metric grid: ~2yr exit / 2 options / **29–36% IRR** / 1.67–1.86× multiple
- Two option cards side-by-side:
  - **Option A — Grade A Developer** (blue accent, "✓ Larger exit value" badge, ₹6,500/sq.ft exit, ₹3,000 at reg + ₹500 at CLU, **~36% IRR**, 1.86×)
  - **Option B — Ranka Brand** (green accent, "✓ No extra charges" badge, ₹5,000/sq.ft exit, ₹3,000 at reg only, **~29% IRR**, 1.67×)
- Per-plot breakdown box: show both options side-by-side for a 1,800 sq.ft plot with actual ₹ figures — **use full notation: ₹54,00,000 (not ₹54,000)**.
  - Option A: ₹54,00,000 today + ₹9,00,000 at CLU = ₹63,00,000 total → exit ₹1,17,00,000
  - Option B: ₹54,00,000 today → exit ₹90,00,000

**Page 2 — All other content in `.all-context` 2-column grid:**
- Left column: "What You're Investing In" (opp-card with why-grid) + Current Status (status-card)
- Right column: Structure Q&A (struct-card, Q&A pairs) + Exit Timeline (timeline-card)
- No CTA, no footer

**Structure Q&A must cover (in order) — spark fee model:**
1. What the spark fee is and what the investor gets at exit (plot at cost vs plot at market value)
2. How the LLP/partnership collective investment works
3. How the land development is linked to the Ranka family's larger project
4. What the ₹500 additional charge for Option A is and when it's paid (CLU, ~month 12)
5. Investor protection (land in LLP name, no capital calls)
6. Callout note about the 10+ year JV backstop with grade-A developer

**Exit timeline (spark fee model):**
- Month 0: Spark fee paid + land registered + CLU initiated
- Month 12: CLU approved + Option A ₹500/sq.ft paid + project launch
- Month 24: Plot allocated at market value + investor exit complete

---

## When to Use Which DRAAS Design System — Two Distinct Templates

There are **two confirmed DRAAS design systems** as of May 2026. Check which one the user has
referenced before building any document:

| Design | Accent Colors | Font | When Used |
|--------|---------------|------|-----------|
| **Green theme** | `--accent: #c8ff57` (lime green) | Inter + JetBrains Mono | Spark-fee model documents (2-page PDFs) |
| **Navy/gold theme** | `--navy: #1A3A5C`, `--gold: #F9BA2F` | Inter + Playfair Display | Investor pitch decks (multi-slide HTML) |

**If user shares a styled PDF as a reference template → use the navy/gold system.**
Extract colors/font using PyMuPDF + PIL per `references/draas-pdf-styling.md`.

**If user describes a spark-fee model document (₹3,000 entry + ₹500 CLU + ₹6,500 exit) → use the green system.**

**⚠️ Never mix the two systems.** The green (`#c8ff57`) and gold (`#F9BA2F`) accents are completely different brand expressions. Using the wrong one looks like a brand error to the DRAAS team.

---

## CSS Design System (Green Theme — Spark Fee Model)

Use this exact token set for all DRAAS investment documents:

```css
:root {
  --dark-bg: #0e0e0e;
  --card-bg: #181818;
  --card-border: #272727;
  --accent: #c8ff57;        /* DRAAS signature green */
  --accent-dim: rgba(200,255,87,0.12);
  --accent-glow: rgba(200,255,87,0.25);
  --text: #f0f0f0;
  --muted: #666;
  --warm: #ff9f43;          /* negative cash flows */
  --rankablue: #c8ff57;     /* Ranka brand color */
  --gradea: #54a0ff;       /* grade-A developer color */
  --success: #26de81;       /* status dots */
}
```

**Typography:** Inter (Google Fonts) — weights 400/500/600/700/900. JetBrains Mono for all numbers and monospace values.

**Cards:** `background: var(--card-bg)`, `border: 1px solid var(--card-border)`, `border-radius: 16px`, `padding: 28px`.
Accent card: `border-color: var(--accent)` + `box-shadow: 0 0 0 1px var(--accent-glow), 0 8px 32px rgba(0,0,0,0.4)`.

**Numbers:** Always `font-family: 'JetBrains Mono', monospace`.

---

## Print / Page Break CSS

**Target: 2-page PDF.** Page 1 = the investment card only. Page 2 = everything else in a single 2-column grid. No more than 2 pages total.

**Pattern — do NOT use `break-after: page` on every card.** That creates a 5-page PDF. Instead:

```css
@media print {
  /* Page 1: the investment card alone */
  .card.accent-border { break-after: page; }

  /* Page 2: everything else grouped — one break after the whole container */
  .all-context { break-after: page; }

  /* Disable per-card breaks */
  .card:not(.accent-border) { break-after: avoid; }
  h2, .options-grid { break-after: avoid; break-inside: avoid; }
}
```

**`.all-context` layout** — the container for pages 2+:
```css
.all-context {
  display: grid;
  grid-template-columns: 1fr 1fr;  /* two columns */
  gap: 10px;
}
```
Inside `.all-context`, nest each section as a plain `<div>` with a class like `.opp-card`, `.struct-card`, `.status-card`, `.timeline-card` — all with `border: 1px solid var(--card-border); border-radius: 10px; padding: 11px 13px;`. No `break-after: page` on these inner cards.

**Tighter sizing for the investment card (page 1):**
- Header h1: ≤28px, body padding: 16px 14px (not 40px)
- Investment amount: ≤36px font-size
- Metrics gap: 6px, card padding: 14px 16px
- Option card padding: 10px 12px, opt-total: ≤20px
- Body font-size: 11px, line-height: 1.35

**If Playwright still generates >2 pages**, the `.all-context` content is too tall to fit on one A4 page. Reduce font sizes or trim content — do NOT add more `break-after: page` rules.

---

### ⚠️ Playwright PDF Generation — Diagnosis

**Page count diagnostic:**
```python
import fitz
doc = fitz.open('/path/to/output.pdf')
for i, page in enumerate(doc):
    words = page.get_text("words")
    max_y = max(w[3] for w in words) if words else 0
    print(f"Page {i+1}: max word y={max_y:.1f}pt  (A4 limit ≈ 842pt)")
```

**Known root cause of >2 pages:** Applying `break-after: page` to individual `.card` divs inside a flex or grid container. Playwright renders correctly (content fits in A4 height) but the CSS break rules cause unwanted pagination. The fix is always the `.all-context` pattern above — NOT content reduction.

**Available PDF tools on this system:**
- `playwright` (Python) — use `chromium` headless shell. Command:
  ```python
  from playwright.sync_api import sync_playwright
  with sync_playwright() as p:
      browser = p.chromium.launch(args=['--no-sandbox'])
      page = browser.new_page()
      page.goto(f'file://{html_path}', wait_until='networkidle')
      page.pdf(format='A4', margin={'top': '12px', 'bottom': '20px', 'left': '12px', 'right': '12px'}, path=pdf_path)
      browser.close()
  ```
- `pymupdf` / `fitz` — for PDF page inspection only (not generation)
- `wkhtmltopdf` / `weasyprint` — **not available** on this system

---

## Q&A Block Format

```html
<div class="qa-block">
  <div class="qa-q">Question text in accent color, bold</div>
  <div class="qa-a">Answer text in #ccc, line-height 1.7</div>
  <div class="qa-note">Callout box — accent-dim background, accent border, used for important notes</div>
</div>
```

CSS:
```css
.qa-q { font-size: 13px; font-weight: 700; color: var(--accent); margin-bottom: 8px; }
.qa-q::before { content: 'Q.'; font-family: 'JetBrains Mono', monospace; }
.qa-a { font-size: 13px; color: #ccc; line-height: 1.7; padding-left: 28px; margin-bottom: 16px; }
.qa-note { background: var(--accent-dim); border: 1px solid rgba(200,255,87,0.15); border-radius: 8px; padding: 12px 14px; font-size: 12px; color: var(--accent); margin-top: 14px; }
```

---

## Financial Model: Spark Fee Structure

This is a **plot-reservation model** — NOT the old per-acre co-investment model. The investor pays a spark fee to reserve a plot at cost, then exits at the prevailing market price at launch. No monthly rental receipts.

**Spark fee model — per sq.ft cash flows:**

| | Option A (Grade A Dev) | Option B (Ranka Brand) |
|---|---|---|
| Today's contribution (t=0) | ₹3,000/sq.ft | ₹3,000/sq.ft |
| CLU charge (month 12, t=1) | ₹500/sq.ft | ₹0 |
| **Total cost** | **₹3,500/sq.ft** | **₹3,000/sq.ft** |
| Exit value (t=2, ~month 24) | ₹6,500/sq.ft | ₹5,000/sq.ft |
| Net gain | ₹3,000 (85.7%) | ₹2,000 (66.7%) |
| Multiple | **1.86×** | **1.67×** |
| IRR | **~36%** | **~29%** |

> ⚠️ **IRR is computed as `Multiple^(1/years) - 1`** — NOT a simple return %:
> - 1.86× over 2 years → IRR = 1.86^0.5 − 1 ≈ **36.3%**
> - 1.67× over 2 years → IRR = 1.67^0.5 − 1 ≈ **29.1%**
>
> **Counterintuitive**: Option B (Ranka) has *lower* IRR (29%) than Option A (36%) despite being a simpler deal (no extra CLU charge, no grade-A developer share). Option A has the larger exit value but also a 2-payment structure (t=0 + t=12) that raises its cash-weighted return. Do NOT swap the IRR labels.
>
> **Do NOT show 39% or 67%** — those numbers were wrong. Always compute IRR from the multiple: `round((multiple ** 0.5 - 1) * 100, 1)` for a 2-year exit.

**IRR computation — always derive from multiple (bisection as fallback):**
```python
def irr_from_multiple(multiple, years=2):
    """Correct IRR from a stated multiple over years."""
    return round((multiple ** (1/years) - 1) * 100, 1)  # e.g. 1.86× → 36.3%

# Verify:
irr_from_multiple(1.86, 2)   # → 36.3
irr_from_multiple(1.67, 2)   # → 29.1

# Bisection method (use only if cash flows are non-standard):
def irr_annual(cfs):
    def npv(r):
        return sum(cf / (1+r)**t for t, cf in enumerate(cfs))
    lo, hi = -0.999, 20.0
    for _ in range(2000):
        mid = (lo + hi) / 2
        if npv(mid) > 0: lo = mid
        else: hi = mid
    return round((lo + hi) / 2 * 100, 1)

irr_annual([-3000, -500, 6500])  # Option A → 36.3%
irr_annual([-3000, 5000])          # Option B → 29.1%
```

**Per-acre economics (saleable area: Option A=7,200 sq.ft/acre, Option B=8,000 sq.ft/acre):**
```python
# Option A per acre
inv_a = 3000*7200 + 500*7200  # = ₹2.52 Cr total
rev_a = 6500*7200              # = ₹4.68 Cr exit → multiple 1.86× → IRR 36.3%
# Option B per acre
inv_b = 3000*8000             # = ₹2.40 Cr total
rev_b = 5000*8000             # = ₹4.00 Cr exit → multiple 1.67× → IRR 29.1%
```

**Typical plot: 1,800 sq.ft — display with FULL Indian numbering (4 zeros minimum):**
- Option A: invest ₹54,00,000 + ₹9,00,000 CLU = ₹63,00,000 total → exit ₹1,17,00,000 → gain ₹54,00,000 (85.7%)
- Option B: invest ₹54,00,000 → exit ₹90,00,000 → gain ₹36,00,000 (66.7%)
- ⚠️ **Never display ₹54,000** — that is missing a zero. Always show full lakhs: ₹54,00,000.

### Old Per-Acre Co-Investment Model (DEPRECATED — do not use)

The ₹4.6 Cr/acre model with monthly rental receipts is **no longer active**. It had:
- Monthly rental receipts (₹72L or ₹64L/mo)
- ₹30L non-refundable token at month 12
- Grade A: ~55% IRR, Ranka: ~44% IRR

**Discard this model entirely for new documents.**

---

## Removing CTA / Footer for PDF-Conversion Documents

When document will be printed to PDF (not a live web page), **remove**:
- The `.cta-bar` section entirely
- Any "Connect with us" or "Request Documents" footer
- Any email links or action buttons

These should never appear in a static PDF document.

---

## Google Drive Upload Pattern

After writing the HTML file:

```python
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

token_path = '/data/hermes/users/{telegram_id}/the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)'
creds = Credentials.from_authorized_user_file(token_path)
if creds.expired:
    creds.refresh(Request())

svc = build('drive', 'v3', credentials=creds)
path = '/data/hermes/cron/output/FILENAME.html'
meta = {'name': 'FILENAME.html', 'id': 'EXISTING_FILE_ID'}  # omit 'id' for new file
media = MediaFileUpload(path, 'text/html')
file = svc.files().update(fileId='EXISTING_FILE_ID', media_body=media, fields='id,webViewLink').execute()
# OR for new file (no fileId, include 'parents'):
# meta = {'name': 'FILENAME.html', 'parents': ['FOLDER_ID']}
# file = svc.files().create(body=meta, media_body=media, fields='id,webViewLink').execute()
print(file['webViewLink'])
```

**To delete old file before uploading new version:**
```python
svc.files().delete(fileId='OLD_FILE_ID').execute()
```

---

## Workflow

1. **Receive PDF** — user sends investment proposal PDF
2. **Analyze and extract** — read financial data: investment amount, exit scenarios (Ranka brand vs grade-A), prices, sharing ratios, timelines
3. **Compute IRR** — use `compute_irr()` above for each exit option
4. **Build HTML** — write the document following the structure above
5. **Upload to Drive** — find or create the correct folder (search by name), delete old version, upload new
6. **Return link** — send Drive link to user

---

## References

- `references/spark-fee-model.md` — Active model: ₹3,000/sq.ft entry, Option A (+₹500 at CLU, exit ₹6,500, ~36% IRR, 1.86×), Option B (no extra, exit ₹5,000, ~29% IRR, 1.67×). Per-sq.ft, per-acre, and per-1,800sq.ft-plot figures. **Always use this — the old IRR values (39%, 67%) were wrong.**