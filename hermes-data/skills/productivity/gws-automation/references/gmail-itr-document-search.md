# Gmail Search Strategies for Indian ITR Documents

Finding Indian income tax return (ITR) documents, intimations, and acknowledgments in Gmail requires a multi-strategy approach because these emails come from different senders with different subject formats.

## Common Senders

| Sender | What they send |
|--------|----------------|
| `intimations@cpc.incometax.gov.in` | ITR Intimation (after return is processed) — "Your ITR Intimation" |
| `intimations@tdscpc.gov.in` | TDS default/demand notices |
| `itdreturn@incometax.gov.in` | e-Verification confirmation emails |
| `ITD_SUPPORT@insight.gov.in` | Advance Tax e-Campaigns |
| Company CA/accounts team | Actual ITR acknowledgment PDFs, computation sheets, financials |

## Search Query Strategy

Always try multiple query angles — different senders use different terminology:

### 1. By Assessment Year (AY) vs Financial Year (FY)

| You want | India terminology | Gmail query |
|----------|-------------------|-------------|
| Returns filed in current period | AY 2026-27 | `"AY 2026-27"` |
| Current financial year just ended | FY 2025-26 | `"2025-26"` OR `"2526"` |
| Short year format | 2526 | `2526` |

### 2. By PAN Number (most reliable)

```python
# PAN of DRA REALTY PRIVATE LIMITED
pan = 'AAPCS9730H'
results = service.users().messages().list(
    userId='me',
    q=f'{pan} AND (ITR OR intimation OR return)',
    maxResults=20
).execute()
```

### 3. By Company/Entity Name

```python
queries = [
    'subject:(ITR OR "Income Tax Return" OR intimation) AND "DRA REALTY PRIVATE LIMITED"',
    'subject:(ITR OR "Income Tax Return") AND "DRA Realty" AND (2026 OR "25-26")',
    '"DRA REALTY PRIVATE LIMITED" AND (acknowledgment OR Acknowledgement)',
]
```

### 4. By Status Type

| Email type | Search hint |
|------------|-------------|
| **e-Verification confirmation** | `"e-Verified" AND "Income Tax Return" AND PAN` |
| **ITR Intimation (refund/demand)** | `"Your ITR Intimation" AND PAN` |
| **ITR Acknowledgment** | `ACK AND PAN` — acknowledgment filenames often start with `ACK` |
| **Income Tax Dept (CPC)** | `from:intimations@cpc.incometax.gov.in` |
| **TDS defaults** | `from:intimations@tdscpc.gov.in` |
| **Advance Tax notices** | `"Advance Tax" AND "e-Campaign"` |

## Common Filename Patterns

ITR documents from the Income Tax Department follow predictable naming:

- `ACK{number}.pdf` — ITR Acknowledgment
- `{Name}_{Date}_{Number}.pdf` — Individual ITR (e.g., `Nishant Ranka_15-Sep-2025_503005850.pdf`)
- `{Company}_Financials_{FY}.pdf` or `.xls`
- `signedfinancialsfor{company}{FY}.zip`
- `{Company} Audited financials {FY}.pdf`

## Practical Workflow

```python
from tools.gws_auth import build_service
gmail = build_service('gmail', 'v1')

# Step 1: Try the most specific query
results = gmail.users().messages().list(
    userId='me',
    q='subject:(ITR OR "Income Tax Return") AND ("DRA Realty") AND ("2026" OR "25-26")',
    maxResults=20
).execute()

# Step 2: If specific fails, search by PAN
results = gmail.users().messages().list(
    userId='me',
    q='AAPCS9730H AND (ITR OR intimation OR return)',
    maxResults=20
).execute()

# Step 3: Check attachments
for m in results.get('messages', []):
    msg = gmail.users().messages().get(
        userId='me', id=m['id'], format='full'
    ).execute()
    # Walk parts looking for attachments
    parts = [msg['payload']]
    while parts:
        p = parts.pop(0)
        if 'parts' in p:
            parts.extend(p['parts'])
        if p.get('filename'):
            print(p['filename'])
```

## Understanding Assessment Year vs Financial Year

| Indian Tax Term | Meaning | Example |
|----------------|---------|---------|
| **AY 2026-27** | Assessment Year = FY 2025-26 | Filed Apr-Oct 2026 |
| **FY 2025-26** | Financial Year ended Mar 31, 2026 | Income earned in this period |
| **AY 2025-26** | Assessment Year = FY 2024-25 | Filed Apr-Oct 2025 |

File the query under the **Assessment Year** the IT department uses. An email about "AY 2026-27" won't match a search for "FY 2025-26".

## Latest Verified Searches

**Jun 2026 — DRA Realty Private Limited (PAN: AAPCS9730H):**
- AY 2025-26 ITR Intimation received Feb 2026 (refund)
- AY 2025-26 ITR Ack: `ACK454548901061125.pdf` (Nov 2025 email from Eshwari)
- FY 2025-26 (AY 2026-27): NOT YET FILED as of Jun 2026 (deadline Oct 31, 2026)
- Advance Tax e-Campaign received Mar 2026 for AY 2026-27
