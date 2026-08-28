# Worked Example: HP Fuel Invoice — Reimbursement from DRA Realty

Session date: 15 July 2026

## Trigger

User sent a fuel receipt image from HP — Bharathi Service, Rajbavan Road, Bangalore.
Voice: *"This is a fuel invoice for the fuel I just filled in the Innova paying on my Kotak credit card. Post it to invoice processing pipeline — already paid on NDR credit card, reimbursement from DRA Realty Private Limited."*

## Receipt details extracted

| Field | Value |
|-------|-------|
| Station | HP — Bharathi Service |
| Address | Rajbavan Road, Bangalore |
| Phone | 9886708224 |
| Receipt No. | G4145 |
| Date | 15/07/2026 |
| Time | 15:40 |
| Product | Petrol |
| Rate | ₹110.89/L |
| Volume | 36.07 L |
| **Total** | **₹3,999.80** |
| Vehicle | Innova |
| Payment | Kotak Credit Card (NDR personal) |

## Files created

| File | Location | Link |
|------|----------|------|
| Receipt image | TMP/20260715_HP_Fuel_Invoice_Petrol_3999.80_Innova.jpg | `1AxvMifQPtGpdEosxVrmerJBEXOtulwfA` |
| Processing note | TMP/20260715_Invoice_Processing_NOTE - HP Fuel - DRA Realty | `1ui76Q0PPy3Fv-Vi6GsnTsZli7_Suhwr4W4_Hy-w9J5c` |

## Processing note content

The note documented:
- **Invoice Details**: HP Petrol × 36.07 L @ ₹110.89/L = ₹3,999.80, Innova
- **Payment**: Paid by NDR on Kotak Credit Card — PAID
- **Reimbursement**: DRA Realty Private Limited → Nishant Ranka (NDR)
- **Reason**: Fuel for Innova — Company vehicle expense
- **Attachment**: Receipt image in same folder

## Key observations

- The user did not request a Gmail draft or email — just "post to invoice processing pipeline." The pipeline in this context means: upload receipt + create structured processing note + flag for reimbursement.
- No permanent expense folder was created under DRA Realty's Drive — TMP staging is the right boundary for the agent. The accounts team handles the final filing.
