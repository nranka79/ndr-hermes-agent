# RERA Means of Finance / Source of Funds Letter

Domain-specific structure for the RERA Means of Finance letter, required for project registration under RERA Act 2016.

## Standard Structure

### A. Total Cost of Project

| # | Particulars | Data Source |
|---|---|---|
| 1 | Land Cost of the Project (JDA) | Per guidance value, CA Form 1 |
| 2 | Goodwill Cost (to Land Owner) | JDA terms, director loan |
| 3 | Construction Cost (as certified by Engineer) | Engineer Form-3 / Cost Abstract |
| 4 | Approvals, NOCs & Other Charges | CA Form 1 (Plan Approvals + Water + Electricity) |
| 5 | Stamp Duty & Registration | Actual incurred |
| | **Total Cost** | = Sum of above |

### B. Source of Funds

| # | Particulars | Source Label |
|---|---|---|
| 1 | Loan from Director — Goodwill paid | Loan from Director |
| 2 | Loan from Director — Refundable Deposit | Loan from Director |
| 3 | From Company Internal Accruals — Approvals & NOCs | Company surplus |
| 4 | From Company Internal Accruals — Stamp Duty & Registration | Company surplus |
| 5 | From Company Internal Accruals — Construction cost incurred | Company surplus |
| | **Subtotal — Already Incurred by Promoter** | |
| | **Balance from Customer Receipts / Allottees** | = Total Cost - Already Incurred |
| | **Total Funds** | = **Total Cost** |

## Key Rules from CA Form 1 (Form Reg 1)

The CA-certified Form 1 contains the official cost breakdown:
- **Item 1**: Land of the Project (JDA) — As per Guidance Value
- **Item 2**: Approvals & NOCs — Plan Approvals (₹14,06,075), Water/BWSSB (₹30,00,000), Electricity/BESCOM (₹30,00,000)
- **Item 3**: Construction Cost — Engineer-certified + Architects/Consultants Fees + Administrative Costs
- **Item 4**: Total Estimated Cost

## Supporting Documents Required

| Document | Source |
|---|---|
| Cost Abstract (Engineer Form-3) | Engineer (MAN Constructions — S.Vinay Prasad) |
| Land Cost Letter | Promoter letterhead, per development agreement/JDA |
| CA Form 1 (Form Reg 1) | Chartered Accountant (Yogesh T. Gandhi) |
| SOF Supporting Document | CA-certified loans statement (like Kumar Properties reference) |
| Bank Statements | RERA Collection/Designated/Operative accounts |
| Cash Flow Statement | 3 preceding financial years |
| Director's Report | 3 preceding financial years |

## Kumar Properties Reference Format

The reference "SOF with Supportive document.pdf" shows:
- **Document type**: CA-certified "Loans from Relatives" statement
- **Content**: Director/relative name, opening balance (Cr), debit, credit, closing balance
- **Use**: Proves promoter's own investment as source of funds
- **Format**: Company letterhead/PAN, period, account-wise breakdown, total, director signature

## RED Text Workflow for Drafting

When preparing a draft for user review:
1. **Items requiring user confirmation** → mark in **RED** (foregroundColor red + bold)
2. **Placeholders for missing data** → RED with `[To be provided]` / `[Amount needed]`
3. **Calculated/estimated figures** → RED until user confirms
4. **Black text** → data already verified from CA/Engineer-certified sources
5. **Get user confirmation** before removing RED formatting

## Docs API Implementation Notes

- Use `insertTable` with proper rows/cols, then fill cells one-at-a-time to avoid index shifting
- Process cells in **reverse order** (bottom-right to top-left) when batching
- Apply RED formatting with: `{'foregroundColor': {'color': {'rgbColor': {'red': 1.0, 'green': 0.0, 'blue': 0.0}}}, 'bold': True}`
- Rate limit: 60 write operations/minute — batch aggressively or insert `time.sleep(1)` between single-cell calls
