---
name: bali-cash-tracking
description: Track Bali May 2026 cash balance in IDR — opening balance, expenses, IDR purchases, and running balance. Triggered whenever user mentions balance, expenses, or IDR purchases.
trigger: "balance, IDR, cash, suspense, spent, expense, rupiah"
---

# Bali Cash Tracking

## Master Spreadsheet (Source of Truth)

**Spreadsheet:** `Bali May 2026 - Expenses Ledger`
**Spreadsheet ID (hardcoded):** `1-Q-8NKVAesd7_HmA0qGMeNm6CZdL1ThKiI8v29gQBoQ`
**Columns:** DATE | TIME | TYPE | DESCRIPTION | CATEGORY | DEBIT (IDR) | CREDIT (IDR) | BALANCE (IDR) | NOTES | RECEIPT

**Key rules:**
- **DEBIT = positive numbers only** (expenses — no negative signs)
- **CREDIT = positive numbers only** (money in from currency exchange)
- **BALANCE formula:** `=H{prev_row}-F{new_row}+G{new_row}` — copy from previous row
- When appending a row: first `values.append`, then `values.update` on `H{new_row}` with `valueInputOption="FORMULA"`
- Receipt column: full Drive link `https://drive.google.com/file/d/{file_id}/view`

**When adding a new expense or credit:** Append a row to the sheet AND update this skill's tables below. Both must stay in sync.

---

## Balance Format

Always present balances as a clean table:

| | IDR |
|---|---|
| Available | X,XXX,XXX |
| Suspense | X,XXX,XXX |
| **Total** | **X,XXX,XXX** |

Include INR equivalent at 185 IDR/INR as a second line.

---

## Known Opening Balance (May 9, 2026)

- Available: **4,500,000 IDR**
- Suspense: **2,139,000 IDR**
- Total: **6,639,000 IDR**

---

## Known Exchange Rates

- **USD → IDR**: $100 = 1,720,000 IDR ($500 → 8,600,000 on May 9); $100 = 1,725,000 IDR ($200 → 3,450,000 on May 10); $100 = 1,730,500 IDR ($200 → 3,461,000 on May 12)
- **IDR → INR**: **185 IDR = Rs 1** (approx.)

---

## Known USD → IDR Credits

| Date | USD | Rate | IDR | Receipt |
|---|---|---|---|---|
| May 9 | $500 | 1,720,000 per $100 | +8,600,000 | receipt_20260510_USD_500_Exchange_IDR_8600000.pdf |
| May 11 | $200 | 1,730,500 per $100 | +3,461,000 | receipt_20260512_USD_200_Exchange_IDR_3461000.pdf |

---

## All Expenses (by date)

**Note:** All debits are **positive numbers** (no negative signs) to match the spreadsheet format. `=H{prev}-F{row}+G{row}`

**May 9:**
| Item | Category | Debit IDR | Receipt |
|---|---|---|---|
| Sukha Expresso - Lunch | Food & Beverage | 803,000 | receipt_20260510_Sukha_Expresso_Lunch_IDR_803000.pdf |
| Suka Coffee Ubud - Lunch | Food & Beverage | 803,000 | receipt_20260510_Suka_Coffee_Ubud_Lunch_IDR_803000.pdf |
| Fire Show Ubud | Entertainment | 400,000 | receipt_20260510_Fire_Show_Ubud_IDR_400000.pdf |
| Gelato for Kids | Food & Beverage | 105,000 | receipt_20260510_Gelato_Kids_IDR_105000.pdf |
| Suci Suci Suci Dinner | Food & Beverage | 900,000 | receipt_20260510_Suci_Suci_Suci_Dinner_IDR_900000.pdf |
| Cab - 2nd trip | Transport | 900,000 | receipt_20260510_Cab_2nd_IDR_900000.pdf |
| Cab - 3rd trip | Transport | 56,000 | receipt_20260510_Cab_3rd_IDR_56000.pdf |
| ATV Helpers & Photos | Activities | 500,000 | receipt_20260510_ATV_Helpers_Photos_IDR_500000.pdf |
| **May 9 total** | | **4,567,000** | |

**May 10:**
| Item | Category | Debit IDR | Receipt |
|---|---|---|---|
| Water bottle + 2 spirits | Food & Beverage | 60,000 | receipt_20260510_water_spirits_IDR_60000.pdf |
| ATV Helper tips (2 helpers × 50K) | Tips | 100,000 | receipt_20260510_ATV_tips_IDR_100000.pdf |
| ATV Photo Package (4 bikes × 250K) | Activities | 1,000,000 | receipt_20260510_ATV_photos_4bikes_IDR_1000000.pdf |
| Rafting snacks | Food & Beverage | 170,000 | receipt_20260510_rafting_snacks_IDR_170000.pdf |
| Jackie - Raft Guide tip | Tips | 100,000 | receipt_20260510_Jackie_raftguide_tip_IDR_100000.pdf |
| 2 helpers for kids | Tips | 200,000 | (no receipt) |
| Rafting photos | Activities | 300,000 | (no receipt) |
| Indomaret snacks | Food & Beverage | 110,000 | (no receipt) |
| **May 10 total** | | **2,040,000** | |

---

## Balance Calculation

**Running formula:**
```
Available = Opening (4,500,000) + USD_credits - all expenses
Suspense = 2,139,000 (unchanged — it's a hold, not spendable)
Total = Available + Suspense
```

**After May 9 expenses:** Available = 4,500,000 + 8,600,000 − 4,567,000 = **8,533,000**
**After May 10 $200 credit + all expenses:** Available = 8,533,000 + 3,450,000 − 2,040,000 = **9,943,000**

**May 11:**
| Item | Category | IDR | Receipt |
|---|---|---|---|
| (no expenses recorded) | | | |

**May 12:**
| Item | Category | Debit IDR | Receipt |
|---|---|---|---|
| Lunch / Snack | Food & Beverage | 513,000 | receipt_20260512_lunch_snack_IDR_513000.pdf |
| Ubud E-bike Tour - 4pax (Ubud Waterfall Tours) | Activities | 2,760,000 | receipt_20260512_Ubud_Ebike_Tour_4pax_IDR_2760000.pdf |
| Coffee estate shopping (cash portion) | Food & Beverage | 800,000 | receipt_20260512_Coffee_Estate_Shopping_IDR_800000.pdf |
| Tips - Cycling Tour restaurant | Tips | 30,000 | receipt_20260512_Cycling_Tour_Tip_IDR_30000.pdf |
| Natural Gelato - Ruhaan & Rivaan | Food & Beverage | 125,000 | receipt_20260512_Gelato_Ruhaan_Rivaan_IDR_125000.pdf |
| **May 12 total** | | **5,228,000** | |

**Running balance after May 12:** Available = 12,891,000 − 5,228,000 = **7,663,000 IDR**
**Current (May 12):**
- Available: **7,663,000 IDR**
- Suspense: **2,139,000 IDR**
- **Total: 9,802,000 IDR** (~Rs 53,012)
- *(Ledger balance at row 29: **5,922,810 IDR** — ledger tracks cash-IDR only, excludes suspense)*

---

## When User Gives a New Balance

1. Parse the new available/suspense/total figures
2. Reconcile against known expenses and purchases in this skill
3. Update the expense/purchase tables above
4. Append a row to the master spreadsheet
5. Present the updated table

## File Naming Convention for Receipts

`receipt_YYYYMMDD_ItemName_IDR_Amount.pdf`
- Underscores, no spaces
- Amount without commas: `IDR_1000000` not `IDR_1,000,000`

e.g. `receipt_20260510_ATV_photos_4bikes_IDR_1000000.pdf`