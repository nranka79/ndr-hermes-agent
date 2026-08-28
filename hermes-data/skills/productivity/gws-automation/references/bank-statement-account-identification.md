# Bank Statement Account Identification from Gmail

**Use when:** Multiple bank statements arrive in the same inbox and you need to identify which account each PDF belongs to.

## Problem

Banks like Kotak Mahindra send monthly statements for all accounts linked to a customer ID/email to the same inbox. With multiple accounts (personal savings, company current accounts, family accounts), you get 5-6 PDFs per month — filenames are masked (e.g., `24825782-XXXXXXX-560001.pdf`) so you can't tell which account from the filename alone.

## How to Identify the Account

### Method 1: Check the email body salutation

The HTML body of Kotak statement emails contains `Dear [ACCOUNT HOLDER NAME]`. Extract it:

```python
import base64

def extract_salutation(payload):
    """Find 'Dear NAME' in HTML body to identify account holder."""
    html = ""
    if payload.get("body", {}).get("data"):
        html = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
    for part in payload.get("parts", []):
        if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
            html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8", errors="replace")
            break
        if part.get("parts"):
            for sub in part.get("parts", []):
                if sub.get("mimeType") == "text/html" and sub.get("body", {}).get("data"):
                    html = base64.urlsafe_b64decode(sub["body"]["data"]).decode("utf-8", errors="replace")
                    break

    import re
    match = re.search(r'Dear\s+([^,<]+)', html)
    return match.group(1).strip() if match else "Unknown"
```

### Method 2: Check PDF file naming patterns

Different Kotak accounts produce different filename prefixes:
- Group emails by filename prefix to identify unique accounts per month

### Method 3: Check the To field

The `To` header often reveals which email alias received it (e.g., `NDR@drahomes.in` vs `ndr@draas.com` vs a specific project email).

## Common Kotak statement scenarios for DRAAS

| Email Salutation | Likely Account | Purpose |
|---|---|---|
| `DRA DEVELOPERS & PROJECTS PVT LTD` | Company current a/c | Business operations |
| `KANTA RANKA` | Kanta Ranka's a/c | Family member |
| Individual name | Personal savings/salary a/c | Salary credits |

## Pitfalls

- The email body is HTML with inline CSS — use `text/html` parts, not `text/plain` (which may be empty)
- Salutation extraction from HTML is fragile — use regex `Dear\s+([^,<]+)` to capture the name before comma or HTML tag
- Kotak sends e-statements as password-protected PDFs with CRN as the password
- Most recent statement may be 1-2 months behind (bank sends statements around the 5th-10th of the following month)
- If statements for the user's personal account are not found, they may need to request them from accounts team (Eshwari) or the bank relationship manager (Nilesh Prasar for Kotak)
