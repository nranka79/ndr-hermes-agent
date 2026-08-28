# JDA Financial Modeling — Worked Example

## Bidadi ~10 Acres Premium Villa Development (July 2026)

### Context

Prakash shared a Google Doc ("Bidadi 10 Acre - Villas JD") with competitor data and asked for a comprehensive development proposal. The land is under **JDA** at 33% landowner share. He provided specific cost rates during the conversation that superseded the initial assumptions.

### Critical JDA Rule (Learned via Prakash's Correction)

**In a JDA where the developer bears ALL construction costs, the developer pays for 100% of costs on ALL units — including the landowner's share.** The landowner contributes land; the developer builds everything (infrastructure + construction + approvals for all units). The landowner receives their share of built-up area at no additional cost to them. This means:

- **Total Project Cost** = cost to build ALL 150 villas (not just the developer's 100)
- **Landowner's 50 villas cost the developer ₹43.75 Cr** in construction (included in the ₹131.25 Cr total)
- **Effective cost per sq.ft for developer** = Total Cost ÷ Developer's Saleable Area = ~₹7,712/sft (NOT just ₹3,500/sft)
- **Landowner gets ₹106.25 Cr in value** (at market price) for contributing land worth ~₹50 Cr

The developer must sell at ₹8,137/sft just to break even — even though raw construction cost is only ₹3,500/sft. The 33% JDA creates a ~2.3x multiplier on effective cost per sq.ft.

### Parameters (as corrected by Prakash)

| Parameter | Value | Source |
|-----------|-------|--------|
| Gross Land | 10 Acres | Google Doc |
| Land Yield | 53% (developable plot area) | Prakash correction |
| Plot Size | 1,500 sq.ft per villa | Prakash |
| Built-up | 2,500 sq.ft per villa | Prakash |
| Density | ~15 villas/acre → ~150 total | Prakash |
| JDA Landowner Share | 33% of saleable area | Prakash |
| Land Value (ref.) | ₹5 Cr/acre | Prakash |
| Initial Deposit | 10% of land value = ₹5 Cr | Prakash |
| Infrastructure | ₹600/sq.ft | Prakash |
| Construction | ₹3,500/sq.ft | Prakash |
| Approvals | ₹200/sq.ft | Prakash |
| Marketing | 5% of developer's revenue | Prakash |
| **Developer Bears 100% of ALL costs** | **Confirmed** | Prakash correction |

### Calculation Sequence

#### Step 1: Developable Area & Units
```
Gross: 10 × 43,560 = 4,35,600 sq.ft
Yield: 53% → 2,30,868 sq.ft developable
Villas: 2,30,868 ÷ 1,500 = ~150 villas
Total Built-up: 150 × 2,500 = 3,75,000 sq.ft
```

#### Step 2: JDA Split
```
Landowner (33%):  50 villas = 1,25,000 sq.ft built-up  (→ earns ₹106.25 Cr value at market price)
Developer (67%): 100 villas = 2,50,000 sq.ft built-up  (→ sells for revenue)
Total:            150 villas = 3,75,000 sq.ft
```

#### Step 3: Cost Breakdown (Developer Bears 100% of ALL Costs)

| Component | Calculation | Amount (₹ Cr) |
|-----------|-------------|------:|
| **A. LAND COST** | | |
| Initial Deposit (10% of ₹5 Cr/Ac × 10 Ac) | Fixed cash outflow | 5.00 |
| Land Consideration (33% built-up at const. cost) | 50 villas × 2,500 sft × ₹3,500 | 43.75* |
| **Total Land Cost** | | **48.75** |
| **B. INFRASTRUCTURE** (all 150 villas) | 3,75,000 × ₹600 | 22.50 |
| **C. CONSTRUCTION** (all 150 villas, incl. landowner's) | 3,75,000 × ₹3,500 | 131.25 |
| **D. APPROVALS** (all 150 villas) | 3,75,000 × ₹200 | 8.00 |
| **E. MARKETING** | 5% × Dev. Gross Revenue | 10.63 |
| **F. CONTINGENCY & OVERHEADS** | 5% contingency + 3% admin + finance | 26.54 |
| **GRAND TOTAL (Developer's Outflow)** | A+B+C+D+E+F | **₹247.67 Cr** |

*\*Note: The land consideration of ₹43.75 Cr (building landowner's 50 villas) IS included in the ₹131.25 Cr total construction. It is listed separately under Land Cost for JDA accounting but is NOT an additional cost on top of construction.*

#### Step 4: Developer's Effective Cost per Sq.Ft (Key Metric)

```
Developer's Cash Outflow  = ₹247.67 Cr (includes marketing)
Developer's Saleable Area = 2,50,000 sq.ft (100 villas)

Effective Cost per Sq.Ft = ₹247.67 Cr ÷ 2,50,000 sft = ₹9,907/sq.ft
```

**Why this is so high:** The developer builds 3,75,000 sft but only sells 2,50,000 sft. The cost of the landowner's 1,25,000 sft (33%) is borne by the developer but generates zero revenue for them.

#### Step 5: Three-Scenario P&L (Corrected — Developer Bears 100%)

| Scenario | ₹/sft | Gross Rev | Marketing | Net Revenue | Total Cost | **Profit** | **Margin** |
|:--------:|:-----:|:---------:|:---------:|:-----------:|:----------:|:---------:|:---------:|
| Conservative | ₹7,500 | ₹187.50 Cr | ₹9.38 Cr | ₹178.13 Cr | ₹193.29 Cr | **(₹15.16 Cr)** | **-8.5%** |
| **Base Case** | **₹8,500** | **₹212.50 Cr** | **₹10.63 Cr** | **₹201.88 Cr** | **₹193.29 Cr** | **₹8.59 Cr** | **4.3%** |
| Optimistic | ₹9,500 | ₹237.50 Cr | ₹11.88 Cr | ₹225.63 Cr | ₹193.29 Cr | **₹32.34 Cr** | **14.3%** |

*Total Cost (excl. marketing) = ₹5.00 (deposit) + ₹22.50 (infra) + ₹131.25 (const) + ₹8.00 (approvals) + ₹12.54 (contingency/admin) + ₹14.00 (finance) = ₹193.29 Cr. Marketing is deducted from revenue.*

#### Step 6: Breakeven Analysis

| Metric | Value |
|--------|-------|
| Total Cost (excl. marketing) | ₹193.29 Cr |
| Developer's Saleable Area | 2,50,000 sq.ft |
| **Breakeven Price** | **₹8,137/sq.ft** |
| Breakeven Gross Revenue (incl. marketing) | ₹203.42 Cr |
| Villas to Breakeven (at ₹8,500/sft) | ~96 of 100 |
| Breakeven Construction Cost (at ₹8,500 price) | ₹3,950/sft (current ₹3,500 = buffer) |
| Breakeven Infra Cost (at ₹8,500 price) | ₹685/sft (current ₹600 = buffer) |

#### Step 7: Key Takeaways

- **JDA at 33% makes margins thin** — Base case is only 4.3% at ₹8,500/sft
- **Price sensitivity**: The project loses money below ₹8,000/sft; becomes attractive only above ₹9,000/sft
- **Effective cost multiplier**: Because developer builds 3,75,000 sft but sells 2,50,000 sft, the effective cost is ~2.3x the construction cost per sft
- **Landowner gets significant value**: 50 villas worth ₹106.25 Cr at market price for land valued at ~₹50 Cr
- **Negotiation lever**: Reducing landowner share from 33% to 25% improves developer margin by ~6-8% at base case
- **Cost reduction lever**: Reducing construction to ₹3,000/sft + infra to ₹400/sft makes the project viable even at ₹8,500/sft (13-15% margin)

### Format Preference

Prakash requested a **Google Doc** rather than slides because "the slides will not be able to accommodate all the data." The final deliverable was a 14-section Google Doc with proper native tables (22 tables) for: executive summary, JDA structure, land overview, location advantage, supply gap analysis, competitor landscape (3 tables), demand drivers, target buyer profiles + sales velocity, cost sheet (6-section with subtotals/references), revenue scenarios, 3-scenario P&L, breakeven analysis, recommendations, and disclaimer.

**Key document structure lesson:** For JDA feasibility studies with full cost sheets, use Google Docs with native HTML tables imported as Google Doc tables (not slides, not pipe-tables in markdown). The HTML → Google Doc conversion via Drive API (`MediaFileUpload` with `mimeType='text/html'` → `mimeType='application/vnd.google-apps.document'`) automatically converts `<table>` elements to proper Google Docs tables with alternating row colors and styled headers.

### KML Map Update

A companion KML file was created with 50+ placemarks organized into 7 layers (Proposed Land, Ongoing Projects, Completed Projects, Upcoming Projects, Industrial/Drivers, Social Infrastructure, Infrastructure) and uploaded to Drive for Prakash to import into his My Maps. See `references/comprehensive-market-map-kml.md` in this skill for the KML creation workflow.

### JDA vs Outright Purchase: Key Differences

| Dimension | Outright Purchase | JDA at 33% |
|-----------|-----------------|------------|
| Upfront cash | ₹37.80 Cr (land + reg) | ₹5.00 Cr (deposit only) |
| Total development cost | ₹69.49 Cr (30 villas) | ₹193.29 Cr (150 villas) |
| Revenue | ₹76.50 Cr (30 villas) | ₹201.88 Cr (100 villas) |
| Profit (base) | ₹7.01 Cr (9.2%) | ₹8.59 Cr (4.3%) |
| Breakeven | ₹7,721/sft | ₹8,137/sft |
| Risk | Higher upfront, lower per-unit cost | Lower upfront, thinner margins |
| Best for | Certain markets, developer can wait for exit | Growth corridors where land is scarce/expensive
