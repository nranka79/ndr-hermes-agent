# Development Feasibility Study (PPTX)

## When to Use

User asks for a **development proposal / feasibility study** for a raw land parcel — what to build, at what cost, at what price, how fast it will sell, and what returns to expect. Typical trigger: 5-20 acres in a growth corridor, first preference stated (villas/plots/apartments).

**How this differs from pure market research:**
| Task | `villa-development-market-research.md` | This workflow |
|------|----------------------------------------|---------------|
| Output | Competitor price comparison report | **Full development proposal** |
| Includes cost sheet? | ❌ | ✅ Land + construction + approvals + finance |
| Revenue projection? | ❌ Pricing rec only | ✅ 3-scenario (conservative/base/optimistic) |
| Sales velocity? | ❌ | ✅ 4-phase absorption model |
| Buyer personas? | ❌ | ✅ Segmented by catchment |
| Financial viability? | ❌ | ✅ Margin %, breakeven, ROI |

## Workflow

### Phase 0: Extract Source Data

The user typically shares a Google Doc or Sheet with competitor data. Access it via Drive export:

```python
# Export Google Doc as plain text
from googleapiclient.discovery import build
from tools.gws_vault_client import get_token, resolve

uid = resolve('email', 'user@email.com')
token_data = json.loads(get_token(uid, 'google-draas'))
creds = Credentials.from_authorized_user_info(token_data)
if creds.expired and creds.refresh_token: creds.refresh(Request())

drive = build('drive', 'v3', credentials=creds)
content = drive.files().export(fileId=DOC_ID, mimeType='text/plain').execute()
```

**Data categories to extract from the doc:**
- **Subject Land** — location, coordinates, area, access, zoning
- **Ongoing Competitors** — project name, type, size, launch date, launch price, current price, RERA, appreciation
- **Completed Projects** — resale pricing, appreciation timeline (shows actual exit velocity for investors)
- **Upcoming Projects** — national developer entries (validates corridor thesis)
- **Demand Drivers** — industrial, infrastructure, social, government mega-projects
- **Social Infrastructure** — schools, hospitals, retail, distances from site

### Phase 1: Supply Gap Analysis

Quantify the whitespace to justify the product thesis:

```python
composition = [
    ('Plotted Developments', '90%', GREEN, '11+ ongoing/completed'),
    ('Apartments', '7%', TEAL, 'Limited supply'),
    ('Villas', '0%', RED, 'NO dedicated villa community'),
    ('Mixed', '3%', PURPLE, 'Eagleton Golf legacy'),
]
```

Key insight to extract: if the user says "no supply in vicinity" for the preferred product type, verify this against the competitor list. Count villa-type projects vs plotted vs apartment. Zero villa count = first-mover thesis confirmed.

### Phase 2: Competitor Price Trend Analysis

Two tables needed:

**Ongoing projects table:** Project / Type / Size / Launch Date / Launch Price / Current Price / Appreciation %
- If appreciation >30%, the corridor is in growth phase
- If appreciation <10%, market may be stagnant or over-supplied

**Completed projects resale table:** Same columns but with completion date
- Completed projects show REAL exit prices (not developer asking prices)
- Use for appreciation evidence in investor materials
- Eagleton-style luxury projects (210% over 5yr) show brand premium potential

### Phase 3: Demand Drivers & Catchment Analysis

Structure as 6 driver cards for the presentation:
1. **Industrial Growth** — major employers, white-collar workforce count
2. **Government Mega-Projects** — smart city, SEZ, knowledge corridor
3. **Infrastructure** — expressway, ring road, metro, airport connectivity
4. **Social Infrastructure** — schools/hospitals within 15 km radius
5. **Employment Catchment** — total workforce, executive households, avg income
6. **Future Catalysts** — upcoming metro line, new industrial phase

### Phase 4: Buyer Persona Segmentation

Segment the catchment into 5 buyer types with % allocation:

| Segment | % | Trigger | Budget |
|---------|---|---------|--------|
| Industrial Executives | 35% | Locals wanting premium near work | ₹25-60 LPA salary |
| Smart City Professionals | 25% | Tech/IT from GBIT | ₹20-50 LPA |
| HNIs / Investors | 20% | Second home / weekend property | ₹3-7 Cr |
| Upgraders from Plotted | 15% | Existing plot owners (2018-22) | Equity ₹40-90 L |
| NRI / Expat | 5% | Returning NRIs, expat execs | ₹5-8 Cr |

**Why this matters for pricing:** The dominant segment (industrial execs) has a different price sensitivity than HNIs. Price for the segment that buys 35% of inventory, not the segment that buys 5%.

### Phase 5: Sales Velocity Estimation

Build a 4-phase absorption model:

```python
phases = [
    ('Pre-Launch (Months 1-3)', '25-35% of inventory', '₹7,000-7,500/sft (early-bird)', 'Builder network + brokers'),
    ('Launch (Months 4-8)', '35-45% of inventory', '₹7,500-8,500/sft', 'Digital + site visits'),
    ('Stabilization (Months 9-18)', '~25% of inventory', '₹8,500-9,500/sft', 'Referral + portal listings'),
    ('Trail (Months 19-36)', 'Remaining 3-5 units', '₹9,000-10,000/sft', 'Ready-to-move premium'),
]
```

**Typical velocity:** 1.5-2 units/month for 30-40 unit villa project in a growth corridor. Pre-sales target: 25-35% before completion.

### Phase 6: Project Cost Sheet

Build a 6-section cost breakdown. **This is the critical financial section.** Use the DRAAS dark theme presentation format.

| Section | Components | % of total |
|---------|-----------|------------|
| **A. Land Cost** | Acquisition + registration (8%) + stamp duty | ~54% |
| **B. Development Cost** | Site infrastructure, landscaping, boundary wall | ~4% |
| **C. Construction Cost** | Villa construction + architect fees | ~28% |
| **D. Approvals & Legal** | BMRDA/BBMP, RERA, legal docs | ~1% |
| **E. Marketing & Sales** | Advertising (3% of sales) + brokerage (2%) | ~5% |
| **F. Contingency & Overheads** | Contingency (5%), PM/admin (3%), finance cost (10% for 24m) | ~8% |

**Cost sheet structure:**
```
A. LAND COST
   Land Acquisition (~10 Ac @ ₹X Cr/Ac)     ₹XX.XX Cr
   Registration & Stamp Duty (8%)            ₹X.XX Cr
   Total Land Cost                            ₹XX.XX Cr

B. DEVELOPMENT COST
   Site Development & Infrastructure         ₹X.XX Cr
   Landscaping & Common Area                 ₹X.XX Cr
   Boundary Wall, Gate & Security            ₹X.XX Cr
   Total Development Cost                    ₹X.XX Cr

C. CONSTRUCTION COST
   Villa Construction (N units × X sft @ ₹X/sft)  ₹XX.XX Cr
   Architect & Design Fees (~5%)             ₹X.XX Cr
   Total Construction                        ₹XX.XX Cr

D. APPROVALS & LEGAL
   ...                                      ₹X.XX Cr

E. MARKETING & SALES
   ...                                      ₹X.XX Cr

F. CONTINGENCY & OVERHEADS
   Contingency (5% of dev+const)             ₹X.XX Cr
   Project Management & Admin (3%)           ₹X.XX Cr
   Finance Cost / Interest (@10% for 24m)    ₹X.XX Cr
   Total Contingency & Overheads             ₹X.XX Cr

══════════════════════════════════════════
TOTAL PROJECT COST                         ₹XX.XX Cr
Per sq.ft of built-up                       ₹X,XXX/sft
```

### Phase 7: Revenue Projection & 3-Scenario Analysis

Build 3 scenarios to show the viability range:

| Scenario | Price/sft | Revenue | Cost | Profit | Margin | Verdict |
|----------|-----------|---------|------|--------|--------|---------|
| Conservative | ₹7,500 | ₹67.50 Cr | ₹69.49 Cr | -₹1.99 Cr | -2.9% | ❌ NOT VIABLE |
| Base Case ⭐ | ₹8,500 | ₹76.50 Cr | ₹69.49 Cr | ₹7.01 Cr | 9.2% | ✅ VIABLE |
| Optimistic | ₹9,500 | ₹85.50 Cr | ₹69.49 Cr | ₹16.01 Cr | 18.7% | ✅ STRONG |

**Critical viability test:** If the base case margin is <10%, the project is too risky. Recommend optimisation:
- Reduce construction cost (shell+basic finish at ₹2,500/sft vs premium ₹4,000/sft)
- Reduce average villa size (2,500 sft instead of 3,000+)
- Negotiate lower land cost
- Increase target ASP through better positioning

**BREAKEVEN calculation:**
```
Break-even price = Total Cost / Saleable Area
                 = ₹69,49,00,000 / 90,000 sft
                 = ₹7,721/sft
```
If break-even > minimum viable price, the project needs restructuring.

### Phase 8: Build the Presentation

Use the DRAAS dark theme (navy background, gold accents) from the `powerpoint` skill. Structure:

| # | Slide | Content |
|---|-------|---------|
| 1 | **Title** | Project name, acreage, Development Proposal, DRA Group, Confidential |
| 2 | **Executive Summary** | Thesis statement, 6 key metrics, land summary, recommendation |
| 3 | **Subject Land Overview** | Land particulars table (11+ rows), key advantages panel |
| 4 | **Location Advantage** | Expressway hero card, 3×2 connectivity grid, catchment demographics |
| 5 | **Supply Gap Analysis** | Market composition bar chart, WHY NOW rationale (8 points) |
| 6 | **Ongoing Competitors** | Full table with launch → current pricing + appreciation |
| 7 | **Completed Resale** | Appreciation evidence table, pattern summary |
| 8 | **Upcoming Validation** | National developer entries, strategic window impact |
| 9 | **Demand Drivers** | 6 driver cards (3×2 grid) with icons |
| 10 | **Buyer Profile & Velocity** | 5 segments + 4-phase absorption model |
| 11 | **Project Cost Sheet** | Full 6-section cost breakdown, summary with assumptions |
| 12 | **Revenue & Viability** | 3-scenario analysis, pricing strategy, breakeven |
| 13 | **Recommendations** | 4-card layout (Product, Land, Marketing, Financial) |
| 14 | **Disclaimer** | Data sources, limitations |

**python-pptx helper pattern for the cost table:**

```python
def add_cost_row(s, x, y, w, label, amount, is_header=False, is_total=False):
    """Add a cost breakdown row with label + amount"""
    bg = CARD2 if is_header else RGBColor(0x2A,0x2A,0x15) if is_total else CARD
    R(s, x, y, w, 240000, fill=bg)
    Tx(s, x+50000, y+10000, w-1300000, 220000, label, 
       fs=9 if not is_header and not is_total else 10,
       bold=is_header or is_total, c=GOLD if is_total else WHITE, va=MSO_ANCHOR.MIDDLE)
    if amount:
        Tx(s, x+w-1200000, y+10000, 1150000, 220000, f'₹{amount} Cr', 
           fs=10, bold=is_total, c=GOLD if is_total else WHITE, a=PP_ALIGN.RIGHT, va=MSO_ANCHOR.MIDDLE)
```

### Phase 9: Viability Optimisation (Important)

When the user's preferred product (e.g. premium finish villas at ₹4,000/sft) makes the project unviable at target prices, present the trade-off clearly:

```
At premium finish (₹4,000/sft):
  Construction: 30 × 3,000 sft × ₹4,000 = ₹36.00 Cr
  Total Cost: ₹90.10 Cr
  Revenue at ₹8,500/sft: ₹76.50 Cr  ← COST EXCEEDS REVENUE
  Verdict: NOT VIABLE

Optimised (₹2,500/sft shell+basic):
  Construction: 30 × 2,500 sft × ₹2,500 = ₹18.75 Cr
  Total Cost: ₹69.49 Cr
  Revenue at ₹8,500/sft: ₹76.50 Cr
  Profit: ₹7.01 Cr (9.2% margin) ✅
```

**Three levers to pull (in priority order):**
1. **Construction cost** — shell+basic finish is viable; premium finish is not at target prices
2. **Villa size** — smaller units (2,000-2,500 sft) reduce cost exposure while maintaining per-sft revenue
3. **Land cost** — every ₹0.5 Cr/acre reduction improves margin by ~1.5%

### Phase 10: Upload & Share

Upload to Drive and share with the requesting user:

```python
from googleapiclient.http import MediaFileUpload
from googleapiclient.discovery import build

media = MediaFileUpload('/tmp/deck.pptx',
    mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
    resumable=True)
body = {
    'name': 'Project Name — Development Proposal.pptx',
    'mimeType': 'application/vnd.google-apps.presentation',
    'description': 'Development Feasibility Study | DRA Group | Date'
}
f = drive.files().create(body=body, media_body=media, fields='id,name,mimeType,webViewLink').execute()
file_id = f['id']

# Set public access
drive.permissions().create(fileId=file_id, body={'type': 'anyone', 'role': 'reader'}).execute()

# Share with requester if different from auth'd account
drive.permissions().create(fileId=file_id, body={
    'type': 'user', 'role': 'writer', 'emailAddress': 'requester@email.com'
}).execute()
```

**Telegram delivery:** Place the link inside a code block (backticks). Google Slides links often fail when rendered inline on Telegram.

## Pitfalls

- **Cost > Revenue trap:** Always sanity-check total cost vs. total revenue early. Premium finishes (₹4,000/sft) can inflate construction to 40% of cost, making the project unviable at realistic selling prices.
- **Land cost dominates:** In Bangalore periphery markets, land can be 50-55% of total project cost. Small changes in land cost have outsized impact on viability.
- **Finance cost is real:** At 10% p.a. for 24 months, finance cost adds 3-5% to total project cost. Many first-pass estimates forget this.
- **Brokerage is non-negotiable:** Villa projects in unproven corridors need 2-3% brokerage to move inventory.
- **Don't mix construction tiers:** Shell+basic (₹2,500/sft) and premium (₹4,000/sft) produce wildly different outcomes. Be explicit about which tier you're using.
- **Sellout timeline impacts price:** Longer sellout (36+ months) means higher finance cost AND market risk. Target 24-30 months for 30-40 units.
- **Pre-sales are critical:** Without 25-35% pre-sales, the project may not get construction finance. Price the pre-launch phase to move volume, not maximise margin.
- **Appreciation data must be project-specific:** Don't use Bangalore-wide averages. Use only projects within the same micro-market.
- **Income segmentation drives pricing:** If the dominant buyer segment earns ₹25-60 LPA, the EMI-affordable villa price is ₹2.5-3.5 Cr. Pricing above this needs HNI/Investor demand to absorb inventory.

## Worked Example: Bidadi ~10 Acres (Jul 2026)

See the completed presentation at the Drive link delivered in the Bidadi session. Key numbers:
- **Target:** 30 premium villas at ₹8,500/sft avg
- **Land:** ₹3.5 Cr/Ac × 10 Ac = ₹35 Cr (₹37.80 incl reg)
- **Construction:** 30 × 2,500 sft × ₹2,500/sft = ₹18.75 Cr (optimised)
- **Total Cost:** ₹69.49 Cr
- **Revenue:** ₹76.50 Cr (base case)
- **Profit:** ₹7.01 Cr (9.2% margin)
- **Breakeven:** ₹7,721/sft
- **Buyers:** 35% industrial execs, 25% smart city professionals
- **Velocity:** 1.5-2 units/month, 24-30 month sellout
- **Key constraint:** Premium finish (₹4,000/sft) makes project unviable at target prices
