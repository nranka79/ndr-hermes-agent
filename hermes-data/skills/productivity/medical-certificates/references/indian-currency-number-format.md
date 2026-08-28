# Indian Currency & Number Formatting

Indian financial documents (insurance policies, bank statements, GST invoices, premium receipts, hospital bills) use the **Indian numbering system**: comma separators every **two** digits from the right (after the first three). Western formatting uses commas every three digits. Misreading one for the other is the single most common error when extracting ₹ values from Indian documents.

## The comma-position rule (memorize)

| Indian format | Western mistake | Actual value | Human-readable |
|---|---|---|---|
| `1,50,00,000` | "15,000,000" or "1,50,000" | **₹1,50,00,000** | ₹1.5 Crore |
| `15,00,00,000` | "150,000,000" or "15,000,000" | **₹15,00,00,000** | ₹15 Crore |
| `12,00,000` | "1,200,000" or "120,000" | **₹12,00,000** | ₹12 Lakh |
| `2,09,731` | "209,731" (same) or "20,97,310" | **₹2,09,731** | ₹2.09 Lakh (≈₹2.1 L) |
| `5,000` | "5,000" (same) | **₹5,000** | ₹5 Thousand |
| `50,000` | "50,000" (same) | **₹50,000** | ₹50 Thousand |
| `1,000` | "1,000" (same) | **₹1,000** | ₹1 Thousand |
| `100` | "100" (same) | **₹100** | ₹100 |

**Mental shortcut:** count the commas from the right. Indian always has commas at the 3rd-from-right position, then every 2nd position. Western only has commas every 3rd. So `1,50,00,000` has commas after positions 3, 5, 7 from the right (Indian) — Western would only put a comma after position 3 and 6.

## Unit ladder (₹)

| Unit | Value | Notes |
|---|---|---|
| 1 Hundred | 100 | Rare in formal docs |
| 1 Thousand | 1,000 | = 1K |
| 1 Lakh | 1,00,000 (100,000) | NOT "lac" / "lacs" in formal docs (use "lakh" / "lakh") |
| 10 Lakh | 10,00,000 (1,000,000) | = 1 Million |
| 1 Crore | 1,00,00,000 (10,000,000) | = 10 Million |
| 10 Crore | 10,00,00,000 (100,000,000) | = 100 Million |
| 100 Crore | 100,00,00,000 (1,000,000,000) | = 1 Billion |

## Common insurance/policy patterns (Royal Sundaram, ICICI Lombard, HDFC Ergo, etc.)

These three numbers appear in nearly every Indian health policy. Use them as sanity-check anchors:

| Field | Typical range (senior citizen, Lifeline / Elite / similar) |
|---|---|
| **Base Sum Insured** | ₹3,00,000 to ₹3,00,00,000 (₹3 Lakh to ₹3 Crore) |
| **Cumulative Bonus (NCB)** | 10%–50% of base SI, accumulated yearly |
| **Annual Premium (Lifeline Elite, 65-70 yr)** | ₹1,50,000 to ₹3,00,000 (₹1.5 L to ₹3 L) |
| **Co-payment** | 0% / 10% / 20% (look for "Co-Payment %" row in schedule) |
| **Hospital Cash Benefit** | ₹1,000 to ₹5,000 per day |

**Pre-flight check before quoting a sum insured:** if a single policy's base SI is below ₹3 Lakh, it's almost certainly a top-up or a very old policy. The "I quoted 15 lakhs when the actual is 1.5 crore" error happens when the figure ends in `,00,000` — the comma pattern `X,YZ,00,000` reads as "X lakh" if you mentally misalign. Always expand to full digits before quoting.

## Pre-send verification routine

Before quoting any ₹ figure to the user (in a WhatsApp message, email draft, pre-auth form, etc.):

1. **Find the source number as printed** in the document (e.g. "Sum Insured: 1,50,00,000").
2. **Strip commas** → `15000000`.
3. **Count digits** → 8 digits → falls in the crore range.
4. **Convert** → `1,50,00,000` = 1 crore 50 lakh = **₹1.5 Crore**.
5. **Cross-check** against the policy's premium: an annual premium of ₹2,09,731 on a ₹1.5 Cr SI is plausible; on a ₹15,000 SI it would be absurd (premium would be ~140% of SI). This inverse check catches unit errors.

```python
def parse_indian_rupee(s: str) -> tuple[int, str]:
    """Returns (numeric_value, human_readable). Raises if unit detection fails."""
    s = s.replace('₹', '').replace(',', '').strip()
    n = int(s)
    if n >= 1_00_00_000:
        return n, f"₹{n/1_00_00_000:.2f} Crore"
    if n >= 1_00_000:
        return n, f"₹{n/1_00_000:.2f} Lakh"
    if n >= 1_000:
        return n, f"₹{n/1_000:.2f} Thousand"
    return n, f"₹{n}"

# Examples:
# parse_indian_rupee("1,50,00,000") → (15000000, "₹1.50 Crore")
# parse_indian_rupee("12,00,000")    → (1200000, "₹12.00 Lakh")
# parse_indian_rupee("2,09,731")     → (209731, "₹2.10 Lakh")
```

## Anti-pattern — do NOT do this

- ❌ **Don't** parse `1,50,00,000` as a string and split on comma to "15000000" + then forget to count digits. The string is correct; the conversion is what's risky.
- ❌ **Don't** use `int("1,50,00,000")` — Python raises `ValueError: invalid literal for int()`. The Indian grouping isn't a standard locale separator.
- ❌ **Don't** assume "lakhs" or "crores" without first seeing the document. The unit of measurement is in the source — your job is to read it correctly, not to infer it.
- ❌ **Don't** send the user a message with a ₹ figure until you have written it both in expanded form (`₹1,50,00,000`) AND in human form (`₹1.5 Crore`) — the dual display makes the unit visible and forces you to confront any mental misread.

## Real failure case (KDR pre-op insurance, 11 Jul 2026)

I had to draft a WhatsApp message to Charan (Trustwell Hospital insurance coordinator) about Kanta Ranka's Royal Sundaram renewal. The actual figures from the 30 Mar 2026 renewal notice:

```
Base Sum Insured: 1,50,00,000
Cumulative Bonus: 12,00,000
Annual Premium: 2,09,731
```

I read `1,50,00,000` as "15,00,000" (mentally dropped one comma) and wrote **"₹15,00,000 (₹1.5 Cr)"** in the message — which is internally contradictory (15 L ≠ 1.5 Cr). I also wrote "₹15,00,000" as the SI in the meta block. The user caught it on review: "you said 15 lakhs there's something wrong... it's a 3 crore policy or 1 crore or something." I then read the actual schedule (full PDF, not just the email summary) and corrected to **₹1,50,00,000 (₹1.5 Cr) base + ₹1,20,00,000 (₹1.2 Cr) CB = ₹2,70,00,000 (₹2.7 Cr) total**.

**Lesson:** the email summary showed `1,50,00,000` correctly. My draft quoted it as `15,00,000`. The error happened in my own note-taking, not in OCR. The verification routine above would have caught it: count digits → 8 → crore range → ₹1.5 Cr. The inverse check (premium ₹2.09 L on ₹15,000 SI is nonsensical) would also have caught it.

## When this convention applies

Everywhere in DRAAS work where money or large numbers appear in Indian documents:
- Insurance policy schedules, renewal notices, premium receipts
- Hospital bills and GST invoices (₹1,234.00 is just a normal small number; ₹12,34,567 is ₹12.34 Lakh)
- Sale deeds, khata documents, property valuations
- Bank statements, NEFT/RTGS references
- Tax documents (Form 16, AIS, capital gains)
- Personal finance / wealth statements
