# Area Statement Verification — Multi-Source Cross-Reference

Verify a project's customer-facing area statement against the architect-certified area statement, execution plan, and approved plan sanction. Used when Prakash/ndr sends a PDF area statement and asks "verify this is correct" or "cross-check against the approved plan."

## Workflow (5 steps)

### Step 1 — Extract the Customer Area Statement data

The customer statement is usually a 1-page PDF (Annexure-A format) with a unit-wise table. Use tesseract on a high-res render:

```bash
pdftoppm -png -r 300 "statement.pdf" /tmp/pages
tesseract /tmp/pages-1.png stdout --psm 6 -l eng
```

Table columns are typically: Sl No | Unit No | Share (LO/DEV) | Floor | Facing | RERA Carpet Area | Balcony/Exclusive Area | Built-up Area (walls incl.) | Common Area Loading | Super Built-up Area | UDS

Key summary fields at bottom:
- Total Carpet Area
- Total Balcony Area
- Total Built-up Area
- Total Common Area Loading
- Total Super Built-up Area
- Total UDS (= plot area)
- "Total Saleable Area (as per SSA / sanctioned plan)" note

### Step 2 — Find Reference Documents on Drive

Search for the project's:
1. **Architect Certified Area Statement** — Search `name contains '<Project>' and name contains 'Area Statement Certified'` or `'Architect Certificate'`. Usually a DOCX or PDF signed by the architect (Ar. Bhuvanesh Krishnan / Finding Form Design Studio for Ranka projects).
2. **Execution Plan Area Statement** — Search `name contains '<Project>' and name contains 'Execution Plan Area Statement'`. Usually a Google Sheet with per-unit breakdown including built-up area %, balcony, carpet, loading, SBUA, UDS.
3. **Plan Sanction / DTCP Approval** — Search `name contains '<Project>' and name contains 'Sanction'`. Look for PDFs with GBA (Built-up Area) approval reference numbers.
4. **Common Area & Amenity Statement** — Architect-certified doc listing staircase, lift, lobby, head room, etc. with per-component areas.
5. **Form-2 Architect Certificate (RERA)** — 2-page scanned PDF, page 1 = project summary + category table, page 2 = per-unit carpet area breakdown.

> **Identity pitfall:** Some project folders (e.g. "Oasis - print") are owned by psingh@draas.com, not ndr@draas.com. If Drive returns 404 or 0 results, re-run with `HERMES_SESSION_USER_ID=psingh` or use the vault token for `google-draas` service_name (which covers psingh's account when he's the session user).

### Step 3 — Extract Architect Certified Data

The architect-certified DOCX contains:
- **Table 1 (Project Summary):** Total Land Area (sqm + sft), Total Built-Up Area (sqm), Total FAR Area (sqm), Total Carpet Area (sft + sqm), Total Balcony Area, Total Common Area (sqft), Total Saleable Area (sft + sqm), No. of Units, FSI Achieved vs Permissible
- **Table 2 (Unit-wise):** Sl No | Unit No. | Floor | Type | RERA Carpet Area (sqft) | Balcony Area (sqft) | UDS (sqm / fraction)

The architect uses precise values (e.g. 1,247.82 sft) vs the customer statement which rounds (1,248 sft). Differences ≤ 1 sft are rounding — flag anything > 1 sft.

### Step 4 — Unit-by-Unit Comparison

Compare every unit across ALL three sources:

| Field | Tolerance | Action |
|---|---|---|
| **Carpet Area** | ≤ 1 sft | Rounding — pass |
| **Balcony Area** | ≤ 1 sft | Rounding — pass; > 1 sft = ⚠️ **FLAG** |
| **Built-up Area** | ≤ 1 sft | Rounding — pass |
| **Common Area Loading** | Match architect total | Customer statement's apportionment by unit may differ from aggregate |
| **Super BUA** | Derive: Carpet + Balcony + Walls + Loading | Cross-check arithmetic |
| **UDS** | Derive: (Unit Carpet / Total Carpet) × Plot Area | Cross-check proportion |

**Key discrepancy to watch for:** a unit where the architect certifies zero balcony area but the customer statement assigns one. This happened with **Ranka Amber Unit 104** (Architect: 0.00 sft, Customer Statement: 59 sft) — both the certified DOCX and the Execution Plan Sheet agreed on zero, so the customer statement was likely using a different plan revision.

### Step 5 — Overall Totals Reconciliation

Compare these roll-ups from the architect certificate vs customer statement:

| Total | Check |
|---|---|
| **Carpet** | Sum of all units = architect total ✓ |
| **Balcony** | Sum of all units = architect total ✓ |
| **Common Area Loading** | Per-unit sum vs architect's Common Area total. The customer statement's loading is **always** an apportionment — the architect's total common area (staircase + lift + lobby + head room, etc.) is the source of truth. A discrepancy here means the loading algorithm differs. |
| **Super BUA** | If Common Area Loading differs, SBUA will too. Report the variance and note which source looks authoritative. |

### Common Pitfalls

- **Saleable Area vs Super BUA**: Customer statements often have a note "Total Saleable Area (as per SSA/sanctioned plan): X sft" where X ≈ Total FAR Area, NOT Super BUA. The FAR/saleable area excludes balconies and the loading surcharge. Don't conflate the two.
- **FSI check**: FSI Achieved = Total FAR Area / Plot Area. For Ranka Amber: 2,559.82 sqm / 1,300.58 sqm = 1.97 (Permissible: 2.00) ✅
- **UDS calculation**: UDS per sqft of Super BUA = Plot Area / Total SBUA. For Ranka Amber: 14,000 / 31,853 = 0.4395 ✅
- **Floor naming variance**: The architect's DOCX may use "Ground/First/Second/Third" while the customer statement uses "First/Second/Third/Fourth". Always map the floor index, not the label.
- **SSA (Supplementary Sharing Agreement)**: The SSA figure for saleable area may not appear in any architect or plan document on Drive. Search for a document named "SSA", "Supplementary Sharing", or "Sharing Agreement" for the project. If not found, flag it as a data gap.

### Gardener's Notes (Ranka Amber worked example)

Grove/Vista/Reserve = villa design types (not Gross/Visible/Restricted). When a unit's FSI is "1.77/1.85" (2 values only), the middle tier (Vista) either matches Grove or is N/A — ask the user.