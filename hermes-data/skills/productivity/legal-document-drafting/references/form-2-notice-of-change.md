# Form No. 2 — Notice of Change in Constitution of a Firm (Karnataka)

> **⚠️ Don't confuse with Form II (Rule 3).** This reference covers **Form 2** (Sec 63(1), Rule 10). For a simple name change or place-of-business change under **Sec 60(1), Rule 3**, see `form-ii-statement-of-alteration.md` — that is a different form for a different purpose.

## When to Use

When the user asks you to prepare **Form 2** under **Section 63(1)** of the Indian Partnership Act, 1932 and **Rule 10** of the Karnataka Partnership (Registration of Firms) Rules, 1995 — for recording changes in a registered firm (reconstitution, name change, profit ratio change, new property contribution).

## Form Structure

Form 2 has these sections:

### 1. Firm Particulars
| Field | Source |
|-------|--------|
| Name of Firm | Reconstitution deed / Registration certificate |
| Registered Address | As per registration — use the firm's registered address |
| Firm Registration No. | From the acknowledgement / registration certificate (e.g. SJN-F823-2023-24) |
| Date of Original Registration | From the acknowledgement (e.g. 14 November 2023) |
| Date of Reconstitution | Date of the Deed of Reconstitution (e.g. 24 June 2026) |

### 2. Nature of Change(s)
Checkboxes — tick all that apply. Common reconstitution changes:
- ✅ Change in firm name
- ✅ Change in profit-sharing ratio
- ✅ Change in capital contribution / introduction of new property
- ☐ Admission / Retirement / Expulsion / Death of partner (as applicable)

### 3. New Name of the Firm (if applicable)
Former Name → New Name + Effective Date.

### 4. Profit-Sharing Ratio
Table: Partner Name, Share Before (%), Share After (%). Must total 100%.

### 5. Particulars of Partners After Reconstitution
Table with: Sl.No., Name, Father's/Mother's Name, Residential/Registered Address, Age, Occupation, Share (%), Partner Type (Managing Partner / Partner).

**For corporate partners (e.g. DRA Realty Pvt Ltd):**
- Father's/Mother's Name → "— (Corporate Entity)"
- Address → Registered office address
- Age → "—"
- Occupation → Nature of business (e.g. "Real Estate Development")
- Partner Type → "Managing Partner" if applicable

**For individual partners (e.g. Mr. Ashok Kumar):**
- Leave father's name, address, age as blanks for the user to fill
- Occupation → "Business"

### 6. Property/Assets Contributed Table
When new properties are brought into the reconstituted firm, include a table:

| Sl.No. | Schedule | Description | Location/Survey | Extent | Value (₹) | Contributed By |
|--------|----------|-------------|-----------------|--------|-----------|----------------|

### 7. Declaration
Standard declaration: "I/We give notice that the above changes have taken place..." Signed by all continuing partners.

### 8. Witnesses
Two witness lines — name & address, signature.

### 9. Document Checklist
- [ ] Certified copy of Deed of Reconstitution
- [ ] Original Registration Certificate (for verification/update)
- [ ] Board Resolution of corporate partner(s)
- [ ] Proof of payment of prescribed fee

## Creating the Document

Use **HTML → Drive import** (same as `google-doc-formatting-template` approach) — tables formatted with inline CSS. The form is structured-data heavy (tables), which HTML handles better than the Docs API.

## Fee (Karnataka)
Typically ₹500–₹1,000 depending on nature of change. Verify current fee with the Registrar of Firms office.

## 🚨 Form 3 — Required Alongside Form 2 When Name Changes

**Critical distinction under Karnataka Rules:**

| Change | Form | Section | Rule |
|--------|------|---------|------|
| PSR change, property introduction, partner admission/retirement | **Form 2** | S.63(1) | Rule 10 |
| Change of firm name | **Form 3** | S.63(2) | **Rule 11** |

While Form 2 has an integrated "Change of firm name" checkbox (Section 2) and a "New Name of the Firm" section (Section 3), **Rule 11 of the Karnataka Partnership Rules prescribes a separate Form 3** for name changes under S.63(2). Some Registrar of Firms offices accept Form 2 alone for a combined reconstitution+name change, but others may insist on Form 3 as well.

**Best practice:** **Prepare both forms.** Have Form 3 ready even if not asked. The extra form costs nothing to prepare but saves a return visit.

### What Form 3 Covers

Form 3 is simpler than Form 2 — it only needs:
- Current firm name
- New firm name
- Effective date of name change
- Declaration signed by all partners
- Witnesses

Format: Same HTML→Drive import pattern as Form 2.

---

## 🚨 Additional Affidavit for Name Change

**Many Registrar of Firms offices require a sworn affidavit** alongside Form 3 (or alongside Form 2 if used for name change):

Affidavit should state:
1. No other firm with the proposed name (DRA KAAJ DEVELOPMENT PARTNERS) is already registered
2. The name change is bona fide and not intended to defraud any creditor
3. The firm continues to be liable for all existing obligations (creditors' rights are preserved)
4. The firm has not changed its name more than once in the last 12 months

The affidavit must be sworn before a Notary Public or Oath Commissioner (format: first-person declaration, notarised signature block).

---

## 🚨 Registrar of Firms vs District Registrar — Two Different Processes

**This is the most common confusion in partnership reconstitution filings.** There are TWO separate processes with TWO different authorities:

| Process | Authority | What You Submit | Purpose |
|---------|-----------|----------------|---------|
| **Notice of Reconstitution** | **Registrar of Firms**, Karnataka | Form 2 (+ Form 3 + Affidavit) | Update the Register of Firms — recording the change, NOT registering the deed |
| **Stamp Duty + Registration** | **District Registrar / Sub-Registrar** (e.g., Shivajinagar) | Covering letter + physical deed on stamp paper | Pay stamp duty on the Reconstitution Deed; optionally register under the Registration Act if property is conveyed |

**Both are needed**, but they are separate:
- The **Covering Letter** (see `references/covering-letter-deed-registration.md`) goes to the **District Registrar** — for stamp duty assessment on the deed
- **Form 2** goes to the **Registrar of Firms** — for recording the reconstitution in the state register

**Do not confuse the addressee.** The covering letter says "The District Registrar," while Form 2 says "The Registrar of Firms, Karnataka, Bengaluru."

---

## Required Supporting Documents

| Document | For Which Process | Status |
|----------|------------------|--------|
| Deed of Reconstitution (certified copy) | Both | Required |
| Original Registration Certificate | Registrar of Firms | For verification/update |
| Board Resolution (corporate partner) | Registrar of Firms | Often required when a company is a partner |
| Name Change Affidavit (notarised) | Registrar of Firms | Variable — some offices require it |
| Covering Letter | District Registrar | For stamp duty assessment |
| Proof of fee payment | Registrar of Firms | ₹500–₹1,000, varies |
| PAN Card/GST Update | Post-filing | After reconstitution is recorded, update PAN and GST |

---

## Post-Filing Steps

After the Registrar records the reconstitution, update the following:

1. **PAN** — Apply to IT Department for name change on the firm's PAN card. This is a prerequisite for bank updates.
2. **GST Registration** — Amend the firm's GST registration with the new name (Form GST REG-14).
3. **Bank Accounts** — Update the firm's bank accounts with the new name and changed PSR.
4. **Existing Contracts** — Notify counterparties of the reconstitution to avoid questions on enforceability.

---

## Filing Notes
- Section 63(1) requires notice within **90 days** of the change
- File in duplicate before the Registrar of Firms, Karnataka, Bengaluru
- Multiple changes (PSR, property, capital) can be recorded in a **single Form 2**, but a **name change** may require a separate **Form 3** (Rule 11) — prepare both
