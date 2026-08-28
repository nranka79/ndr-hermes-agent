# Customer Area Statement — Bank Project Pre-Approval

Structure for generating a Customer Area Statement (Annexure-A) submitted to a bank alongside the project pre-approval / project finance request letter for a DRAAS residential project.

## When to use

User says: "generate customer area statement", "area statement for bank", "RERA carpet breakdown per unit", "regenerate the statement with this format", or provides a structure spec for how to break down unit areas.

## Document structure

The document is a **landscape annexure** inside a bank letter docx, containing:

### Title block
```
ANNEXURE-A
CUSTOMER AREA STATEMENT – [PROJECT NAME]
Project: [Name] | Location: [address] | Configuration: [type] | Total Units: [N] | Plot Area: [sq.ft]
```

### Formula block (shown above the table — TWO lines)

**Line 1 — RERA Carpet definition:**
```
RERA Carpet Area = Sum of all usable internal room areas + Area of internal partition walls
```

**Line 2 — Super BUA derivation:**
```
Super Built-up Area = RERA Carpet Area + Exclusive Balcony/Utility Area + External Walls + Common Area Loading
```

### Table columns (11 cols, landscape)

| # | Unit # | Share | Floor | Entrance Facing (Boundary) | RERA Carpet Area (sft) | Balcony / Exclusive Area (sft) | Built-up Area (sft) [Walls incl.] | Common Area Loading (sft) | Super Built-up Area (sft) | UDS (sft) |

**Column-by-column data sources (from raw sheet):**
- RERA Carpet Area → col 10
- Balcony / Exclusive Area → col 9
- Built-up Area → col 7 (includes external walls per sanctioned plan)
- Common Area Loading → col 12
- Super Built-up Area → col 13
- UDS → col 14

### Notes section (below table)
1. **Summary line:** Total Saleable Area (as per SSA / sanctioned plan): [N] sq.ft | Total Super Built-Up Area: [N] sq.ft | Total sanctioned plot area: [N] sq.ft | UDS per sq.ft of Super BUA: [N] | Shares: LO = Landowner, DEV = Developer
2. **External Walls & Exclusions:** "External wall thickness and structural columns are included within the Built-up Area figures above as per the sanctioned plan. Utility / wash areas and exclusive open terrace are not applicable for the [unit type] configuration. Car parking charges, clubhouse membership fees, GST, registration costs and maintenance deposits are NOT included in the carpet area / apartment price."
3. **Disclaimer:** "This Customer Area Statement is furnished in connection with the project pre-approval request and is subject to verification against the sanctioned plan and the definitive project documents."

## Source data mapping

Source columns (from an Excel sheet exported as JSON):
- Col 7: Unit Built up Area / Plinth Area (sft) → used as "Built-up Area (sft) [Walls incl.]"
- Col 9: Execution Balcony Area → "Balcony / Exclusive Area"
- Col 10: RERA Carpet Area → "RERA Carpet Area"
- Col 12: Common Area Share → "Common Area Loading"
- Col 13: Super Built Up Area → "Super Built-up Area"
- Col 14: UDS → "UDS"

## Pitfalls
- **Data reconciliation** — In source sheets, Super BUA may not equal BUA + Common. The sheet's Super BUA column is the authoritative figure from the sanctioned plan. Show it as-is and do not force-reconcile.
- **Loading column removed** — The user explicitly does NOT want a Loading % column. Keep it out.
- **Saleable area** — The covering letter cites `27,543.25 sq.ft` as total saleable area (per SSA). This is the sum of (Carpet + Balcony) per the SSA, not the Super BUA total (31,853).
- **Unit boundaries** — The "Entrance Facing" column doubles as the boundary direction (N/S/E/W). Full four-direction boundaries require a separate boundary table from the plan.
- **No Loading %** — This column has been removed per user preference. Do not reintroduce it.