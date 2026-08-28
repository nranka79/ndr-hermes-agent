# Spark Fee Investment Model — Gunjur 2026

## Model Summary

Investor pays a **Today's Contribution** to reserve a plot at registration. Plot is allocated at cost at exit, with investor receiving the plot at its **prevailing market value**. The gain is the difference between market value and total cost paid.

> **Option naming**: Use "Option A — Grade A Developer" and "Option B — Ranka Brand" in all documents. Do NOT name specific developers (e.g. Prestige) in investor-facing materials.

---

## The Two Options

| | Option A — Grade A Developer | Option B — Ranka Brand |
|---|---|---|
| **Today's contribution** (at registration, t=0) | ₹3,000 / sq.ft | ₹3,000 / sq.ft |
| **CLU charge** (~month 12, t=1) | ₹500 / sq.ft | ₹0 |
| **Total cost** | ₹3,500 / sq.ft | ₹3,000 / sq.ft |
| **Exit value** (at launch, t=2) | ₹6,500 / sq.ft | ₹5,000 / sq.ft |
| **Net gain per sq.ft** | ₹3,000 (85.7%) | ₹2,000 (66.7%) |
| **Multiple** | **1.86×** | **1.67×** |
| **IRR (annualised, 2 years)** | **~36%** | **~29%** |

> ⚠️ **IRR = Multiple^(1/years) − 1** (derived from the 2-year multiple):
> - 1.86× over 2 years → IRR = 1.86^0.5 − 1 ≈ **36.3%**
> - 1.67× over 2 years → IRR = 1.67^0.5 − 1 ≈ **29.1%**
>
> **Do NOT use 39% or 67%** — those were wrong. Option A has the higher multiple (1.86×) and therefore the higher IRR (~36%). Option B's lower exit value and no CLU charge give it a lower multiple (1.67×) and lower IRR (~29%). The confusion arises because Option B's simpler structure (one payment) makes it feel higher-return, but the math is unambiguous.

---

## IRR Computation

**Always derive IRR from the multiple** using `Multiple^(1/years) - 1`:

```python
def irr_from_multiple(multiple, years=2):
    return round((multiple ** (1/years) - 1) * 100, 1)

irr_from_multiple(1.86, 2)   # → 36.3
irr_from_multiple(1.67, 2)   # → 29.1
```

**Bisection method** (use only for non-standard cash flow timing):
```python
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

---

## Per-Acre Economics

Saleable area assumptions: Option A = 7,200 sq.ft/acre; Option B = 8,000 sq.ft/acre.

```
Option A — Grade A Developer (7,200 sq.ft/acre):
  At registration (₹3,000 × 7,200):           ₹2,16,00,000
  At CLU         (₹500  × 7,200):             ₹36,00,000
  Total investment:                            ₹2,52,00,000
  Exit revenue    (₹6,500 × 7,200):            ₹4,68,00,000
  Net gain per acre:                           ₹2,16,00,000
  Multiple: 4.68/2.52 = 1.857×  →  IRR: 36.3%

Option B — Ranka Brand (8,000 sq.ft/acre):
  At registration (₹3,000 × 8,000):           ₹2,40,00,000
  No additional charges
  Total investment:                            ₹2,40,00,000
  Exit revenue    (₹5,000 × 8,000):            ₹4,00,00,000
  Net gain per acre:                           ₹1,60,00,000
  Multiple: 4.00/2.40 = 1.667×  →  IRR: 29.1%
```

---

## Per 1,800 sq.ft Plot — DISPLAY WITH FULL INDIAN NUMBERING

⚠️ **Always use full lakhs notation — minimum 4 zeros shown:**

```
Option A — Grade A Developer:
  At registration: ₹3,000 × 1,800  = ₹54,00,000
  At CLU (month 12): ₹500 × 1,800  = ₹9,00,000
  Total investment:                   ₹63,00,000
  Exit value (₹6,500 × 1,800):       ₹1,17,00,000
  Net gain: ₹54,00,000 (85.7%) | Multiple: 1.86× | IRR: ~36%

Option B — Ranka Brand:
  At registration: ₹3,000 × 1,800  = ₹54,00,000
  No additional charges
  Total investment:                   ₹54,00,000
  Exit value (₹5,000 × 1,800):        ₹90,00,000
  Net gain: ₹36,00,000 (66.7%) | Multiple: 1.67× | IRR: ~29%
```

**Never display ₹54,000** — that is missing a zero. The display must always show full Indian format: ₹54,00,000.

---

## Exit Timeline

| Month | Event |
|---|---|
| **0** | Today's contribution paid at land registration. CLU process initiated. |
| **12** | CLU approved. Option A: ₹500/sq.ft CLU charge due. Project launch. |
| **24** | Plot allocated at prevailing market value. Investor exit complete. |

Note: BMRDA plot sanction expected within ~12 months from purchase. Sales cycle runs an additional ~12 months post-launch.

---

## Key Investor Messaging

- **₹3,000/sq.ft** is not a loss — it's the cost price of the plot
- Investors are not lending money; they are reserving a plot at cost
- Exit gain = market value minus cost paid — no other returns structure needed
- Option B has **no additional charges** after registration — one and done
- Option A has a higher exit value (₹6,500 vs ₹5,000) but requires ₹500/sq.ft more at month 12

---

## What Was the OLD Model (DEPRECATED)

The ₹4.6 Cr/acre co-investment model had:
- Per-acre investment with all charges included
- Monthly rental receipts during development
- ₹30L non-refundable token at month 12
- Grade A ~55% IRR, Ranka ~44% IRR

**This model is no longer active. Use the spark fee model above for all new documents.**