# Kotak Bank Statement Email Patterns — DRAAS Accounts

When searching Gmail for Kotak bank statements and transaction alerts, there are multiple distinct email sources with different characteristics:

## Source 1: Monthly Auto-Generated Statements

**From:** `BankStatements@kotak.com`
**Subject format:** `Bank Account Statement {Month}-{Year}` (e.g., "Bank Account Statement Nov-25")
**To:** Company email addresses (e.g., `NDR@drahomes.in`, admin emails)
**Frequency:** ~5-6 emails per month (one per DRA group company account)
**PDF filenames:** `{number}-XXXXXXX-{pincode}.pdf` (account number masked as XXXXXXX)
**Password:** CRN (Customer Relationship Number) — stated in email body

**Key identifying information in email body:** The HTML email salutation reveals the account holder:
- `Dear DRA DEVELOPERS & PROJECTS PVT LTD` → Company account
- `Dear KANTA RANKA` → Kanta Ranka's personal account

**Limitation:** Cannot determine which account (account number) from filename alone — must parse the email body salutation.

## Source 2: On-Request Statements

**From:** `no-reply-kotak-customer.care@kotak.com`
**Subject format:** `Please find your requested Account Statement`
**Triggered by:** User requesting statement via Kotak Net Banking or Customer Care
**Format:** ZIP file containing password-protected PDF
**Password:** CRN (same as above)

## Source 3: Payment Received Alerts (Real-time Credits)

**From:** `bankalerts@kotak.bank.in` or `bankalerts@kotak.com`
**Subject:** `Payment Received`
**To:** Personal email (`NDR@drahomes.in`) for some accounts, company email (`NDR@draas.com`) for others
**Triggered by:** Every inward NEFT/RTGS credit to the account
**Format:** HTML-only (no PDF attachment) — full details inline in email body

**Key information in the alert body:**
- Amount credited
- Account number (last 4 digits, e.g., `XX0957`)
- Sender name
- Transaction type (NEFT/RTGS)
- UTR (Unique Transaction Reference Number)
- Date of credit

**Example snippet:**
```
Rs. 1000000 has been credited to your Kotak Bank a/c XX0957 on 15-DEC-25 via NEFT transaction from SALMAN KHALID.
Your Unique Transaction Reference Number (UTR) is: HDFCH00676280292.
```

## Source 4: Large Debit Alerts (Real-time Outward Payments)

**From:** `Kotak-BankAlerts <BankAlerts@kotak.com>`
**Subject:** `Large Debit Alert`
**To:** Company email (`NDR@draas.com`)
**Triggered by:** Large RTGS debits from the account
**Format:** HTML email with sender name, UTR, and updated balance

**Example snippet:**
```
INR 4900000.00 is debited from your account XXXX0957 on 12-02-2024 towards Sent RTGS KKBKH24043674807/SALMAN KHA/...
```

## Account Alert Delivery Pattern — Critical: Different Email Addresses for Different Alert Types

This is the single most important pitfall for Kotak account XX0957:

| Alert Type | Sender | Recipient |
|------------|--------|-----------|
| Payment Received (credit) | `bankalerts@kotak.bank.in` | `NDR@drahomes.in` |
| Monthly Statement | `BankStatements@kotak.bank.in` (or `.com`) | `NDR@draas.com` |
| Large Debit Alert | `Kotak-BankAlerts <BankAlerts@kotak.com>` | `NDR@draas.com` |
| InterBank Transfer Alert | `bankalerts@kotak.bank.in` (or `.com`) | `NDR@draas.com` |

**If you search one inbox and find nothing, the alert may be in the other inbox.** Always search both `NDR@draas.com` (google-draas) and switch to the drahomes.in context when the account involves XX0957.

## Gmail Search Strategy for Transaction Lookups

When looking for a specific credit/debit transaction across accounts:

### By sender/beneficiary name
```
query = 'from:bankalerts credited SALMAN'         # Incoming credits
query = 'from:bankalerts debited SALMAN'           # Outgoing debits  
query = 'SALMAN KHALID'                            # Any mention across all inboxes
```

### By account number
```
query = 'XX0957 Payment Received'        # Credits to account XX0957
query = 'A/c X0957'                      # Monthly statements for XX0957
query = 'XX0957'                         # Everything for XX0957
query = 'credited XXXX0957'              # Debit alerts mentioning the account
```

### By UTR number (cross-reference SMS alerts)
When the user has an SMS alert with a UTR, search the email inbox by UTR to find the full email alert:
```
query = 'HDFCH00676280292'               # Exact UTR match
```

### Full credit-list query (all incoming credits to an account)
```
query = 'from:bankalerts credited XX0957 after:2024/01/01 before:2026/07/24'
```

### Complete search flow for "find payments from [person]"
1. Search `from:bankalerts credited [NAME]` in google-draas inbox
2. Search `from:bankalerts credited [NAME]` in drahomes.in context
3. If nothing found, search `[NAME] credited` broadly across both inboxes
4. Search `XX[last4] Payment Received` for account-specific credit alerts
5. Search `XX[last4]` for debit/credit alerts mentioning the account number
6. If the user has an SMS with a UTR, search the exact UTR
7. Check the "Large Debit Alert" pattern for outgoing payments to the person

## Correlating SMS and Email Alerts

Kotak sends **both** an SMS and an email for every NEFT/RTGS credit. The UTR number is the common key:

1. User shares SMS: "Rs. 1000000 credited to XX0957 via NEFT from SALMAN KHALID, UTR: HDFCH00676280292"
2. Search Gmail by UTR: `query='HDFCH00676280292'`
3. Find matching email alert — full HTML body has sender details, sender IFSC, and timestamp

**The SMS-to-email UTR match is the only reliable way to confirm a specific transaction.** The email body is the authoritative source (sender name, amount, date, UTR, sender bank).

## Multi-Account Search Pattern

When the user says "check another account" after you've searched one account:
1. Note all known account suffixes from your search (X5634, X0957, X7071, X1904, X8047, X9082, X2482, X2475, X2499, X6034)
2. Search **each** suffix in both `NDR@draas.com` and `NDR@drahomes.in` context
3. The SMS alert the user received tells you the correct account (last 4 digits)
4. Cross-reference that account against your statement email list to confirm which inbox receives its alerts

## Known DRAAS Kotak Accounts

| Account Holder | Relation | Statement Via |
|----------------|----------|---------------|
| DRA Developers & Projects Pvt Ltd | Company | Monthly auto (Source 1) |
| Kanta Ranka | Mother | Monthly auto (Source 1) |
| Nishant Ranka (9880055634) | Personal | **Not received via email** — must request from Eshwari/Nilesh Prasar |

## Personal Salary Account (9880055634 ending 634)

Statements for Nishant's personal salary account **do not arrive via email automatically**. To obtain:
1. **Eshwari** (echamundeshwari@draas.com) — can share from internal records
2. **Nilesh Prasar** (Kotak DVP) — can provide on request
3. **Kotak Net Banking** — download directly from portal

## File identification tips

When processing a batch of Kotak statement PDFs from email:
1. Open each email and read the salutation line (`Dear XXXX,`)
2. The account holder name in the salutation is authoritative
3. Filter out company accounts when looking for personal account statements
4. The password `CRN` is universal across all statements
