# Investor Portfolio Spreadsheet Creation (xlsx)

Create a multi-project investor portfolio spreadsheet for DRA Group real estate projects. Each project gets an enterprise-format data sheet; a summary sheet provides cross-project comparison + company/director profiles + sharing ratios.

## When to Use

User says: "create investor portfolio spreadsheet", "make project summary for investor", "add [Project Name] to the portfolio", "regenerate with all projects".

## Workflow

### 1. Gather Data Per Project

Each project needs:

- **A. Group & Project Details**: Group name, entity name, incorporation date, CIN, registered office, project name, location
- **B. Land Details**: Total land area (Acres + sq.ft), freehold/leasehold, JV structure, FSI/FAR, TDR
- **C. Structure Specification**: Total built-up area, saleable area (FAR), number of buildings/floors
- **D. Sharing Ratio (JV)**: Developer vs landowner split in sq.ft and units
- **E. Unit Breakup & Timeline**: Start date, completion date, floors, units, avg area per unit
- **F. Approvals Status**: Table of approvals (plan sanction, RERA, CC, electricity, water, fire NOC, etc.)
- **G. Profitability (Developer's Share)**: Sales value, development cost, invested amount, refundable, projected profit, margin %
- **H. Sales Details**: Sold vs unsold units, area, agreement value, amount received, balance, achieved price

### 2. Handle Land Mortgage / Encumbrance

When a project has mortgaged land (e.g., Oasis Phase 1: 2.5 Ac mortgaged to investors):

- Show the **split** clearly: total → mortgaged → available
- Calculate **only on available land**:
  - Plot saleable area = available sq.ft × plottal % (typically 63%)
  - Constructed saleable = plot saleable × FSI (typically 1.80)
- Use the **user's stated plottal %** — do not assume. If user says "assume 63%", use that.

```python
mortgaged_ac = 2.5
available_ac = 4.0
plot_saleable = round((available_ac * 43560) * 0.63)
constructed_area = round(plot_saleable * 1.80)
sales_value = constructed_area * launch_price
profit = sales_value - total_cost
```

### 3. Add Survey Numbers

Extract from project documents. For Phase 1 vs Phase 2:

| Type | Content |
|------|---------|
| Survey Numbers (Phase 1) | Comma-separated list of specific survey sub-divisions |
| Survey Numbers (Phase 2 — Future) | Additional survey numbers for future development |
| Total Land Bank | Summary of all acres across all surveys |

### 4. Add Project Description Section

Append a `PROJECT DESCRIPTION` block below the data table for each sheet:

| Field | Content |
|-------|---------|
| Project Overview | 2-3 sentences: location, type, scale, USP |
| JV Structure | Entity, ratio, parties |
| Current Status | Approvals, pre-sales, timeline |
| Land Status | (for Oasis) Total, mortgaged, available, Phase 2 |
| Key USP | 1-2 sentences highlighting the investment case |

### 5. Add Company Profile & Director Profile (Summary Sheet)

Clear the section after the parameter table, then write:

```
DRA GROUP — COMPANY PROFILE
  Company, Founded, Registered Office, CIN, Core Business,
  Completed Projects, Land Bank, Group Entities

DIRECTOR / PROMOTER PROFILE
  Name, Role, Experience, Email, Core Strengths, Other Family
```

### 6. Add Sharing Ratio & Profit Sharing Table

Project-wise table with columns: Parameter | Amber | NorthStar | Oasis | Combined

Include:
- Executing Entity, JV Type, JV Ratio, DRA Share %
- DRA Saleable Area per project
- Projected Profit per project (Rs. Cr)
- DRA Group Share of Profit (Rs. Cr + %)
- Investor Share (if any, with note)

### 7. Update Combined Portfolio Numbers

Recalculate all combined totals:

```python
total_sa = sum(project_saleable_areas)
total_sv = sum(project_sales_values_in_cr)
total_dc = sum(project_costs_in_cr)
total_pp = sum(project_profits_in_cr)
overall_margin = round(total_pp / total_dc * 100, 1)
```

### 8. Combined Portfolio Highlights Section

Write a bullet list with: number of projects, combined saleable area, combined sales value, combined cost, combined profit, overall margin %, pre-sales achieved, developer equity invested, completion timeline, track record, land bank.

## Key Calculations

| Metric | Formula |
|--------|---------|
| Total Land sq.ft | Acres × 43,560 |
| Plot Saleable | Available sq.ft × Plottal % |
| Constructed Saleable | Plot Saleable × FSI |
| Sales Value | Constructed × Launch Price/sq.ft |
| Total Cost | Constructed × Cost/sq.ft |
| Profit | Sales Value − Total Cost |
| Margin % | Profit / Total Cost × 100 |

## Code Pattern for openpyxl

```python
import openpyxl
from openpyxl.styles import Font

wb = openpyxl.load_workbook('template.xlsx')

# Update cells by scanning content
for row in ws.iter_rows(min_row=1, max_row=ws.max_row):
    for cell in row:
        v = str(cell.value) if cell.value else ''
        if 'Total Saleable Area' in v:
            ws.cell(row=cell.row, column=2).value = f'{num:,} sq.ft'
```

**Pitfall:** Merged cells cause `AttributeError: 'MergedCell' object attribute 'value' is read-only`. Unmerge first:

```python
for m in list(ws.merged_cells.ranges):
    ws.unmerge_cells(str(m))
```

## Pitfalls

- **Merged cells block writes** — always unmerge before bulk cell updates
- **User stated plottal % takes priority** over any calculated estimate
- **2.5 Ac mortgaged changes saleable area** — recalculate on available land only, not total
- **Survey numbers** should come from the project's legal documents, not assumptions
- **Director/shareholder ratios** — if not known precisely, state "TBC from RoC/partnership records"
- **Combined Oasis Profit Margin at bottom** (the key financial ratios section) may show a stale number — ensure it gets recalculated when Oasis numbers change