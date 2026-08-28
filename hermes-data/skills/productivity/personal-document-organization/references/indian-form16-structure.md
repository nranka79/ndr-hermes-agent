# Form 16 Structure (Indian Income Tax)

Form 16 is the TDS certificate issued under Section 203 of the Income-tax Act, 1961, certifying tax deducted at source on salary. It has two parts:

## Part A — TDS Deduction Certificate

**Issued by**: Employer (or Specified Bank for senior citizens under 194P)

**Key fields to extract**:
| Field | Example |
|-------|---------|
| Employer Name | SOUTHCITY PROPERTIES INDIA PRIVATE LIMITED |
| Employer PAN | AALCS0354H |
| Employer TAN | BLRS26790B |
| Employee Name | NISHANT RANKA |
| Employee PAN | AHVPR5168E |
| Assessment Year | 2026-27 |
| Period | 01-Apr-2025 to 31-Mar-2026 |
| Total Salary Paid | ₹75,00,000 |
| Total TDS Deducted | ₹21,12,000 |
| Certificate No. | AONGJMA |
| Certifying Authority | DHARMESH RANKA (Director) |

**Certifying authority conventions for DRA Group companies:**
- DRA Projects Pvt Ltd → Dharmesh Ranka as "PRINCIPAL OFFICER"
- Southcity Properties India Pvt Ltd → Dharmesh Ranka as "DIRECTOR"

**Source**: Page 1 of Part A PDF — the top section.

## Part B — Salary Breakup & Tax Computation (Annexure)

**Key sections**:
- **Section 1**: Gross Salary (Salary u/s 17(1) + Perquisites u/s 17(2) + Profits in lieu u/s 17(3))
- **Section 2**: Exemptions under Section 10 (HRA, LTA, gratuity, etc.)
- **Section 4**: Deductions u/s 16 (Standard deduction ₹75,000 for AY 2026-27, Professional tax)
- **Section 10**: Chapter VI-A deductions (80C, 80D, 80CCD, etc.)
- **Section 12-21**: Tax computation (tax on total income, cess, relief, net tax payable)

**Opting out of 115BAC(1A)?**: Listed as "Yes/No" near the top of Part B.

## Pairing Part A and Part B

Both parts share the same **Certificate Number**:
- Part A → Shows Certificate Number at top right "Certificate No."
- Part B → Shows Certificate Number at top right "Certificate No."

Always verify the Certificate Number matches before filing as a pair.

## Multiple Employers in a Financial Year

If the user worked for multiple employers in the same FY, each employer issues a separate Form 16 set (Part A + Part B). Example from AY 2026-27:

| Employer | PAN | TAN | Salary | TDS | Cert No. |
|----------|-----|-----|--------|-----|----------|
| DRA PROJECTS PRIVATE LIMITED | AACCD4378F | BLRD04516B | ₹18,00,000 | ₹6,30,000 | AOLLXIA |
| SOUTHCITY PROPERTIES INDIA PRIVATE LIMITED | AALCS0354H | BLRS26790B | ₹75,00,000 | ₹21,12,000 | AONGJMA |

Total Gross Salary for AY 2026-27: ₹93,00,000
Total TDS for AY 2026-27: ₹27,42,000
