# Worked Example — DM 15-Acre Bengaluru Model + Project Finance Sheet

Session: 2026-07-31. Source workbook `DM_Financial_Model_15Acres.xlsx` (sheets: Assumptions, Revenue Model, Cost Summary, P&L Summary, Land Value & Break-Even, Project Timeline). Output: `DM_Financial_Model_15Acres_ProjectFinance.xlsx` with a new "Project Finance" sheet at index 3.

## Base model numbers (replicated in Python)

- Land 15 acres × 43,560 × 52% efficiency = **339,768 sqft saleable**
- Investor pre-sale tranche: 40,000 sqft @ ₹5,000 = ₹20.00 Cr (Month 1, working capital)
- Retail phases (of remaining 299,768 sqft), price escalates ₹7,500→₹10,000 linearly over 42 mo:
  - P1 20% @ ₹7,708 → 46.21 | P2 25% @ ₹8,065 → 60.44 | P3 30% @ ₹8,601 → 77.35 | P4 15% @ ₹9,315 → 41.89 | P5 10% @ ₹9,851 → 29.53 Cr
- **Gross revenue ₹275.43 Cr** (blended ₹8,106/sqft)
- Costs: land 105.00 (₹7 Cr/acre × 15) | infra 27.18 (800×339,768) | clubhouse 8.00 (20,000×4,000) | marketing 27.54 (10%) | RERA 5.51 (2%) | DM fee 33.05 (12%) = **₹206.28 Cr**
- All-equity: **NP ₹69.14 Cr (25.1% margin)**, ₹4.61 Cr/acre, ₹203/sqft

## Financed (60% debt @ 12% p.a., 42-mo tenure, 24-mo moratorium, 1% fee)

- Loan ₹123.77 Cr (= 60% × 206.28) | Sponsor equity ₹82.51 Cr (cash equity only ₹40.51 Cr)
- IDC ₹20.82 + post-construction interest ₹10.75 + fee ₹1.24 = **financing cost ₹32.81 Cr** (₹966/sqft)
- **NP after financing ₹36.34 Cr (13.2%)**, ROE 44.0%, Equity IRR ~13.5% p.a. (all-equity IRR ~13.1%), peak debt ₹113.49 Cr, DSCR 1.24×
- Financing drag vs all-equity: ₹32.81 Cr
- Sensitivity ROE (exact grid): 40%: 41.0/38.2/35.4/32.5 | 50%: 44.8/40.5/36.3/32.0 | 60%: 50.4/44.0/37.7/31.3 | 70%: 59.8/49.9/40.0/30.0 | 80%: 78.6/61.6/44.6/27.6 (cols = 10/12/14/16%)

## Exact sheet layout (row numbers matter — formulas reference them)

- R4 Section 1 header; R5 column headers (Parameter|Value|Unit|(blank)|Notes)
- R6 Total dev cost `='Cost Summary'!$C$12` | R7 Debt % 0.6 (yellow) | R8 Equity % 0.4 (yellow) | R9 Check `=B7+B8` | R10 Loan `='Cost Summary'!$C$12*B7` | R11 Equity `='Cost Summary'!$C$12*B8` | R12 Cash equity `=B8*('Cost Summary'!$C$12-'Cost Summary'!$C$6)` | R13 Rate 0.12 | R14 Tenure `=Assumptions!$B$52` | R15 Moratorium `=Assumptions!$B$49` | R16 Fee 0.01 | R17 Other 0 | R18 Start date 2026-08-01 (date, for XIRR)
- R20 Section 2 header; R21 column headers; **rows 22–69 = months 1–48**; R70 TOTAL
- Seed row 21: I21=J21=K21=L21=0
- Per-month formulas (row r, month = r−21):
  - Revenue: `=IF(A{r}=1,'Revenue Model'!$G$6,0)+IF(A{r}<=6,'Revenue Model'!$G$7/6,0)+IF(AND(A{r}>=7,A{r}<=12),'Revenue Model'!$G$8/6,0)+IF(AND(A{r}>=13,A{r}<=24),'Revenue Model'!$G$9/12,0)+IF(AND(A{r}>=25,A{r}<=36),'Revenue Model'!$G$10/12,0)+IF(AND(A{r}>=37,A{r}<=42),'Revenue Model'!$G$11/6,0)`
  - Dev cost: `=IF(A{r}=1,'Cost Summary'!$C$6,0)+IF(A{r}<=24,('Cost Summary'!$C$7+'Cost Summary'!$C$8)/24,0)+(Assumptions!$B$32+Assumptions!$B$33+Assumptions!$B$34)*B{r}` (24% = marketing+RERA+DM of monthly revenue)
  - Drawdown `=IF(A{r}<=$B$14,$B$7*C{r},0)` | Equity `=IF(A{r}<=$B$14,$B$8*C{r},0)` | Interest `=J{r-1}*$B$13/12` | Principal `=IF(OR(A{r}<=$B$15,A{r}>$B$14,$B$14<=$B$15),0,MIN($B$10/($B$14-$B$15),J{r-1}))` | Net `=B{r}-C{r}+D{r}-F{r}-G{r}` | Cum `=I{r-1}+H{r}` | Outstanding `=J{r-1}+D{r}-G{r}` | CumEq `=K{r-1}+E{r}` | CashBal `=I{r}+K{r}` | XIRR date `=$B$18+(A{r}-1)*(365.25/12)`
  - O (PF equity CF): `=IF(A{r}<=$B$14,-E{r},0)+IF(A{r}=$B$14,$B$11+$B$87,0)` — terminal = equity + NP at month 14 cell (=tenure)
  - P (all-equity CF): `=IF(A{r}<=24,-C{r},0)+IF(A{r}=42,'Cost Summary'!$C$12+'P&L Summary'!$B$14,0)`
- R72 Section 3; R74 IDC `=SUM(F22:F45)` | R75 post `=SUM(F46:F69)` | R76 total | R77 fee `=B10*B16` | R79 TOTAL FINANCING COST `=B76+B77+B78`
- R82 Section 4; R87 NP `=B84+B85+B86` | R92 ROE `=B87/B91` | R93 Equity IRR `=IFERROR(XIRR(O22:O69,N22:N69),"n/a")` | R95 Peak `=MAX(J22:J69)` | R96 DSCR `=('Revenue Model'!$G$12-B11)/(SUM(F22:F69)+SUM(G22:G69))` | R98 drag `='P&L Summary'!$B$14-B87`
- R100 Section 5 comparison; R110 Section 6 sensitivity (rows 113–117 = debt 40–80%, cols B–E = rates 10–16%, cell: `=IFERROR(('Revenue Model'!$G$12-'Cost Summary'!$C$12-($A{r}*$B$76*B$112/($B$7*$B$13))-($A{r}*'Cost Summary'!$C$12*$B$16))/((1-$A{r})*'Cost Summary'!$C$12),"")`)
- R120 notes block

## Verification pattern

```python
# no LibreOffice → replicate schedule + XIRR in Python and compare to reported numbers
def simulate(...):  # monthly loop exactly as the sheet formulas
def xirr(cfs):      # bisection on NPV, dates from project start + (m-1)*365.25/12
```
XIRR convention in the sheet = terminal cash flow at month 42 = `equity + NP` (capital recovered with profit). Using only NP as terminal gives a misleading NEGATIVE IRR — the capital return must be included.

## Data flags raised with the user (do not silently fix)

- Land B17 = ₹7 Cr/acre vs note "₹12 Cr/acre" → at 12 the project loses money; needs user confirmation before the model/proposal is used.
- DM fee 12% in model vs IM "10% + 1.5% performance bonus" → footnote, ask before aligning.
