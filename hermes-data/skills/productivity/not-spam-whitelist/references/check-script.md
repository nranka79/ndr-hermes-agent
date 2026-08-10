# Not-Spam Check Script Reference

> **⚠️ STALE AUTH PATTERNS BELOW** — The `GwsClients` class and `get_token(user_id, "google")` patterns shown in this file use the Jul 11 wrong-key bug (raw email as `user_id`, generic `"google"` service key). Do NOT copy these patterns. The current working approach is in the SKILL.md ("Vault-Based Auth — Working Approach (as of Jul 12, 2026)") section: it resolves the email to the canonical vault uid, uses service key `"google-draas"`, and builds `Credentials` from the token's own scope list (not `HERMES_GWS_SCOPES`). This reference is kept for historical context only.

Session: 2026-06-06 — Initial debugging session

## Key Findings

### Sheet Column Mapping (Verified)
When reading via Sheets API `values().get()`, the `Whitelist` tab returns rows as arrays with the following 0-based indices:

| Index | Column | Header              | Used For                         |
|-------|--------|---------------------|----------------------------------|
| 0     | A      | #                   | Row sequence number              |
| 1     | B      | Category            | Classification (Banking, Legal…) |
| 2     | C      | From Email / Domain | **Matching value**               |
| 3     | D      | To Email            | Recipient filter                 |
| 4     | E      | Subject Keywords    | Keyword matching                  |
| 5     | F      | Content Description | Description                      |
| 6     | G      | Rule Type           | Matching strategy                |
| 7     | H      | Date Added          | Date                             |
| 8     | I      | Notes               | Notes                            |

**Bug encountered:** Initial code used index 1 for `from_email_domain` — this read the Category column instead, causing all rules to show wrong values. Always verify by dumping raw rows with headers before implementing matching logic.

### `domain_from` Matching Logic
The sheet has some `domain_from` rules where the value is a full email (contains `@`):
- Rule: `drive-shares-dm-noreply@google.com` (type `domain_from`) — extract domain = `google.com`
- Rule: `creditcardalerts@kotak.bank.in` (type `domain_from`) — extract domain = `kotak.bank.in`
- Rule: `alwaysyoufirst@emailer.idfcfirst.bank.in` (type `domain_from`) — extract domain = `idfcfirst.bank.in` (note: the subdomain matters here)

Correct algorithm:
```python
def get_domain_part(email):
    parts = email.split('@')
    return parts[1].lower() if len(parts) > 1 else email

def check_domain_from(sender_email, rule_value):
    if rule_value.startswith('@'):
        return sender_email.endswith(rule_value.lower())
    elif '@' in rule_value:
        domain = get_domain_part(rule_value)
        return sender_email.endswith('@' + domain)
    else:
        return sender_email.endswith('@' + rule_value.lower())
```

### Runtime Paths
- Hermes venv Python: `/opt/hermes/.venv/bin/python3`
- Python packages needed: `google-api-python-client`, `google-auth`, `google-auth-oauthlib`
- Token storage: Vault daemon at `/run/gws-vault/vault.sock` (NOT a file on disk — see vault-based OAuth section in SKILL.md)
- Access method: `tools.gws_auth.build_service(api, version)` — reads token from vault automatically
- Token scopes required: `gmail.modify`, `spreadsheets` (both confirmed present)

### Token Refresh Pattern (Automatic via Vault)
No manual token management needed. The vault daemon handles refresh inside `load_credentials()`:
```python
# This is what gws_auth.build_service does internally:
from tools.gws_vault_client import get_token
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

token_json = get_token(user_id, "google")
creds = Credentials.from_authorized_user_info(json.loads(token_json), scopes)
if creds.expired and creds.refresh_token:
    creds.refresh(Request())
    # save_credentials() writes refreshed token back to vault
```

### Gmail API Pattern
- List spam: `q='in:spam'` with `maxResults=200`, pagination via `nextPageToken`
- Read details: `format='metadata'` with `metadataHeaders=['From','To','Subject','Date']`
- Extract sender: regex `r'<([^>]+)>'` on From header value
- Move to inbox: `modify()` with `{'removeLabelIds': ['SPAM'], 'addLabelIds': ['INBOX']}`

### Current Rules (as of 2026-07-01) — 20 Rules

| # | Rule Type | Value | Subject Keywords |
|---|-----------|-------|-----------------|
| 1 | exact_from | apsaraa.sridhar@cms-induslaw.com | CMA 742/2026, Savaganapalli |
| 2 | exact_from | statement@idfcfirst.bank.in | Account statement, month of |
| 3 | exact_from | alerts@hdfcbank.bank.in | UPI txn, transaction |
| 4 | exact_from | information@hdfcbank.bank.in | KYC, Preferred Banking |
| 5 | domain_from | drive-shares-dm-noreply@google.com | DRA Payroll, Paramvah |
| 6 | exact_from | bk@findingform.design | Ranka Amber, Architectural GFC |
| 7 | domain_from | creditcardalerts@kotak.bank.in | x0531, Kotak Credit Card |
| 8 | domain_from | alwaysyoufirst@emailer.idfcfirst.bank.in | Reactivate, Dormant Account |
| 9 | exact_from | RoyalSundaramVconnect@royalsundaram.in | Customer Information Sheet |
| 10 | exact_from | nach.alerts@kotak.bank.in | NACH/ECS advice |
| 11 | domain_from | @draas.com | (catch-all) |
| 12 | exact_from | ebill.mobility@jio.com | E-Bill for Jio Number |
| 13 | domain_from | manipalhospitals.com | — |
| 14 | exact_from | billing_accounts@nsdl.com | Invoice |
| 15 | domain_from | jio.com | autopay, debit, failed |
| 16 | domain_from | google.com | — |
| 17 | exact_from | arch_arvind2000@yahoo.co.in | — |
| 18 | exact_from | samdoc_mamc@yahoo.com | — |
| 19 | domain_from | @drahomes.in | — |
| 20 | domain_from | @kotak.com | — |

---

Session: 2026-06-07 — First cron run

### GOOGLE_SA_KEY Unavailable + Wrong UID Auth Fix (Jul 2026)

The `GOOGLE_SA_KEY` env var does NOT exist in this environment (confirmed: not in `.env`, not in any process environ, no service account JSON file on disk). `tools.gws_sa.build_service()` raises `KeyError`.

**Worse: `gws_auth.build_service()` also fails** when used with `HERMES_SESSION_USER_ID=<session-user-id>` because that UID maps to `ndr@ahfl.in`, which has valid Gmail/Sheets scopes but the whitelist sheet is a shared DRAAS asset only accessible by `@draas.com` accounts.

### Fix: GwsClients — Vault Direct Access with Correct UID

Replace all `gws_auth.build_service()` calls with a `GwsClients` class that pins the UID to `ndr@draas.com`:

```python
import json, os, sys, tempfile
sys.path.insert(0, "/opt/hermes")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

class GwsClients:
    def __init__(self):
        from tools.gws_vault_client import get_token
        self._get_token = get_token
        self._uid = "ndr@draas.com"  # ← ONLY this account has sheet access

    def _get_creds(self, scopes: list):
        token_json = self._get_token(self._uid, "google")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write(token_json)
            tmp = f.name
        try:
            creds = Credentials.from_authorized_user_file(tmp, scopes)
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
            return creds
        finally:
            os.unlink(tmp)

    def sheets(self): return build("sheets","v4",credentials=self._get_creds(["https://www.googleapis.com/auth/spreadsheets"]))
    def gmail(self): return build("gmail","v1",credentials=self._get_creds(["https://www.googleapis.com/auth/gmail.modify"]))
```

This works because:
1. `ndr@draas.com`'s vault token has both `spreadsheets` AND `gmail.modify` scopes
2. `ndr@draas.com` is the sheet's owner / has access to the shared whitelist sheet
3. The vault daemon handles token refresh automatically (no manual refresh needed)

**Do NOT set `HERMES_SESSION_USER_ID` when running the script** — it would override to `ndr@ahfl.in` and cause 403s on sheet access.

### Cron Run Results (2026-07-01 06:38 UTC) — Auth Fix Applied
- 20 whitelist rules loaded ✓ (previous attempts got 403 until auth was fixed)
- 62 spam messages found
- **1 moved to inbox**: `nach.alerts@kotak.bank.in` — "NACH/ECS advice" → matched rule 7 (domain_from: `creditcardalerts@kotak.bank.in`, domain extracted: `kotak.bank.in`)
- 8 @draas.com via-pattern emails correctly skipped (Internshala ×3, Justdial ×2, PMO ×2, Sonel India, ERBIL Build Expo, TCS iON — all identified as forwarded newsletters and kept in spam)
- 0 errors
- Gmail account checked: ndr@draas.com
