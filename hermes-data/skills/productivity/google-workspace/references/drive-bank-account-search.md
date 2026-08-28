# Drive & Email — Bank Account / IFSC Search Patterns

**Use case:** User asks to "find bank account details" for a person (director, partner, employee) or entity — account number, IFSC, bank name, branch.

## The Problem

Personal bank account details are **rarely in the shared Drive**. Unlike project financial models or compliance documents, individual bank details are stored:
- In personal email threads (shared privately between the person and accounts)
- On payroll/salary sheets (accessible only to accounts team)
- In vendor registration forms (for third parties)
- In Kelsa CRM vendor/partner records

The Drive is useful for **company** accounts (RERA collection accounts, project loan accounts) but not personal ones.

## What to Search First (in order)

### 1. Email — search for IFSC + name combination

Gmail search in the shared mailbox (typically `google-draas` = ndr@draas.com):

```
from:sales1.blr@draas.com "bank account" OR "IFSC" OR "account number" OR "NEFT"
```

Or filter by person's name + bank name:

```
"Nishant" "HDFC" "account"
"Roshni" "Kotak" "bank"
```

**Common finding:** These mostly return project/business bank docs, NOT personal accounts. If the user says "find bank details for Nishant", check sales1.blr's **sent** items — Bharat may have forwarded or shared them.

### 2. Drive — search for IFSC code patterns

Use `raw_query=True` with Drive-native syntax through `gws_skill_bridge.call('drive_search', ...)`:

```python
call('drive_search', service_name='google-draas',
    query="fullText contains 'HDFC000' and fullText contains 'account number'",
    raw_query=True, max=30)
```

IFSC prefix patterns for common Indian banks:

| Bank | IFSC Prefix | Notes |
|------|-------------|-------|
| HDFC Bank | `HDFC000` | |
| Canara Bank | `CNRB000` or `CANB000` | Formerly `CNRB`, some older docs use `CANB` |
| Kotak Mahindra | `KKBK000` | |
| Karnataka Bank | `KARB000` | |
| SBI | `SBIN00` | |
| ICICI | `ICIC000` | |
| Axis | `UTIB000` | OR `AXIS` in older docs |

Combined query for broad coverage:
```
fullText contains 'HDFC000' or fullText contains 'KKBK000' or fullText contains 'CNRB000' or fullText contains 'KARB000'
```

**⚠️ Pitfall:** This returns mostly legal/property documents (sale deeds, mortgages, sale agreements) that mention account numbers incidentally — not the personal bank detail record you're looking for.

### 3. Drive — search for "beneficiary name" or "A/C No"

Search query:
```
fullText contains 'beneficiary name' or fullText contains 'A/C No' or fullText contains 'account no'
```

**Result:** Mostly EFT letter templates (blank formats, not populated), vendor payment ledgers, and legal documents.

### 4. Drive — search by personal name + "bank"

```
(fullText contains 'Nishant' or fullText contains 'NDR') and (fullText contains 'HDFC' or fullText contains 'account' or fullText contains 'IFSC')
```

**Result:** Returns loan ledgers, investment documents, property deeds — NOT personal savings/current account records.

### 5. Email — broader search across accounts

Try in both the shared business mailbox (`google-draas`) and the user's personal mailbox if authorized:

```
"bank details" OR "account details" OR "IFSC code"
```

Filter by sender from accounts department (`echamundeshwari@draas.com`) — they handle payroll and vendor payments.

### 6. Compliance Tracker Sheet

The "Entity Statutory And Legal Compliance_Tracker" sheet (`1QJC8Ep-TznhWOtJG91cgoU2NXqb_lPp0d7wKgO174JI`) has GST numbers, PAN, and compliance status for entities — but **no bank account details**.

## Dead Ends (What NOT to Waste Time On)

| Document Type | Why It Doesn't Help |
|---------------|---------------------|
| **EFT letter formats** | Blank templates, not populated with actual bank details |
| **APF / Project clearance forms** | Company-level bank details for project financing, not personal |
| **RERA bank affidavits** | Company RERA collection accounts, not personal |
| **Loan ledgers** | Show cheque numbers and loan balances, NOT account numbers |
| **Bank statements** | Belong to the company, not individuals |
| **Contacts sheet** (NDR DRAAS Google contacts) | Only contact info (email/phone), no bank fields |

## What Actually Works (When Data Is Accessible)

1. **Payroll/salary spreadsheet** — The accounts team maintains employee bank details for salary disbursement. If accessible, this has account num, bank name, IFSC for all employees and directors.
2. **Vendor master sheet** — For external parties receiving payments. Often includes bank details.
3. **Email attachments from accounts** — PDFs of cancelled cheques or bank detail forms shared when setting up vendor/employee records. Search `from:echamundeshwari@draas.com` with "cancelled cheque" or "bank details" or "KYC" and `has:attachment`.
4. **Kelsa CRM vendor/partner records** — If the person is set up as a vendor or partner in Kelsa, their bank details may be in the record fields.
5. **Specific email where the person shared their own details** — E.g. "Please find my bank account details for salary" — these are personal emails, not in shared business folders.

## Practical Approach When User Asks "Find Bank Details for X"

1. **First pass (fast):** Drive IFSC prefix search + email bank-detail search (takes ~30 seconds)
2. **If nothing found:** Tell the user honestly what was checked and where the data likely lives (payroll sheet, Kelsa, or shared privately via email)
3. **Suggest action:** "Could you check if [accounts person] has it in the payroll sheet, or ask [person] to share it directly?"
4. **Offer to save:** If the user provides the details, save them to memory for quick reference next time — the data isn't in Drive so saving it avoids re-searching.

## Example: Full Search Sequence for a Person

```python
# Step 1: Drive — IFSC pattern search
call('drive_search', service_name='google-draas',
    query="fullText contains 'HDFC000' and fullText contains 'Nishant'",
    raw_query=True, max=30)

# Step 2: Drive — account number search
call('drive_search', service_name='google-draas',
    query="fullText contains 'Nishant Ranka' and (fullText contains 'account' or fullText contains 'savings')",
    raw_query=True, max=30)

# Step 3: Email — general bank detail search  
call('gmail_search', service_name='google-draas',
    query='"bank account" OR "IFSC" OR "account number" OR "NEFT" "Nishant"', max=20)

# Step 4: Email — from accounts person
call('gmail_search', service_name='google-draas',
    query='from:echamundeshwari@draas.com "bank" OR "account" OR "salary"', max=20)
```
