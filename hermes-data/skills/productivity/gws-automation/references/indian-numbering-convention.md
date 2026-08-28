# Indian Numbering Convention — Lakh / Crore Reference

Indian financial documents (insurance policies, bank statements, invoices) use the lakh-crore numbering system, which is non-obvious for non-Indian readers and easily misread by LLMs.

## The System

| Indian notation | International | Value |
|---|---|---|
| 1,000 | 1 thousand | ₹1,000 |
| 1,00,000 | 100 thousand | ₹1 Lakh |
| 10,00,000 | 1 million | ₹10 Lakh |
| 1,00,00,000 | 100 million | ₹1 Crore |
| 1,50,00,000 | 150 million | ₹1.5 Crore (1 Crore 50 Lakh) |
| 2,10,00,000 | 210 million | ₹2.1 Crore (2 Crore 10 Lakh) |
| 99,99,99,999 | ~1 billion | ₹99.99 Crore (just under 100 Crore) |

**The grouping is asymmetric:** rightmost 3 digits = thousands, then groups of 2 = lakhs, then groups of 2 = crores.

## The Misread Trap

A `1,50,00,000` looks like "1.5 crore" but to an LLM reading it as Western-style "150 million" or worse as "15,000,000" (15 million, which is 1.5 Crore — actually correct in this case, but luck), the units get confused. The real risk: a number like `1,20,000` could be read as "1.2 lakh" (correct) or "120,000" (also correct) but `1,20,00,000` could be read as "1.2 crore" (correct) or "12,000,000" (which is also 1.2 crore but in different units) — the issue is when the original was `12,00,000` (12 lakh, ₹1.2 million) and a careless parse reads it as `1,20,00,00` (1.2 crore) by missing the lakh grouping.

**KDR case (Jul 2026):** Insurance schedule listed `1,50,00,000` as the base sum insured. Initial parse read it as "₹15 lakh" (treating the `1,50` as 150 and dropping the trailing zeroes). Correct value: **₹1.5 Crore**. User caught the error.

## Conversion Algorithm (re-derive, don't parse)

```python
def parse_indian_amount(s: str) -> tuple[int, str]:
    """Returns (amount_in_rupees, human_readable_indian).
    
    Example: parse_indian_amount("1,50,00,000") -> (15000000, "₹1.5 Crore")
    """
    s = s.replace(',', '').replace('₹', '').replace('Rs.', '').strip()
    n = int(s)
    
    if n >= 1_00_00_000:
        crores = n / 1_00_00_000
        if crores == int(crores):
            return n, f"₹{int(crores)} Crore"
        return n, f"₹{crores:.1f} Crore"
    elif n >= 1_00_000:
        lakhs = n / 1_00_000
        if lakhs == int(lakhs):
            return n, f"₹{int(lakhs)} Lakh"
        return n, f"₹{lakhs:.1f} Lakh"
    elif n >= 1000:
        return n, f"₹{n//1000} Thousand"
    else:
        return n, f"₹{n}"
```

**Always re-derive.** When you see `1,50,00,000`, do the math: 1 × crore + 50 × lakh + 0 × thousand + 0 = 1.5 Crore. Never rely on string parsing alone.

## Common Numbers in Indian Health Insurance

- Base sum insured for a senior individual plan: typically **₹3-15 Lakh** or **₹1-3 Crore**
- Cumulative Bonus (no-claim bonus): typically **₹30 Lakh - ₹1.5 Crore** after years of renewal
- Total available SI: base + CB, often **₹50 Lakh - ₹5 Crore**
- Premium for senior Elite plan: **₹50,000 - ₹2,50,000** per year (with GST ~18% on top)
- Hospital bill for major surgery: **₹1.5-5 Lakh**
- Pre-op tests bundle: **₹15,000-30,000** at private hospitals

## Quick Sanity Checks

If a sum insured you extract comes out as < ₹10 Lakh for a "comprehensive" health insurance plan, **double-check** — most plans worth having are ₹10 Lakh+ base. If it comes out as > ₹10 Crore for an individual retail plan, also double-check — that's commercial-scale.

For KDR's Royal Sundaram Lifeline Elite 2026-27: base ₹1.5 Cr, CB ₹1.2 Cr, total ₹2.7 Cr, premium ₹2.09 Lakh. This is a **high-end** individual plan. A typical retail plan is 1/10th of these numbers.

## When In Doubt, Ask the User

Insurance amounts, premium calculations, and policy numbers are easy to misread and the consequences (wrong pre-auth value, wrong policy number in the email) are visible. When the number feels off, ask the user to confirm rather than risk a wrong interpretation.
