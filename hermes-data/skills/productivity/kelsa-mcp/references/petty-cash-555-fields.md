# DRA Petty Cash — Pipeline 555 Field Reference

**Confirmed Jul 2026** via direct MCP HTTP queries (`get_lead` on records created by Bharat H).

## Overview

- **Pipeline ID:** 555
- **Records:** 71 (all created by Bharat H, as of 30 Jul 2026)
- **Stages observed:** Requested → Approved → Expense Details Submitted → Expense Approved → Credited & Closed → Retired
- **Key users:** Bharat H (requester), Eshwari (approver), Nishant ahfl (first-level), Roshini Ranka, Accounts - DRA
- **⚠️ `create_lead` ghosts:** MCP-created records return success but never persist (async processor rejects because creator resolves to "N/A"). Records must be created via Kelsa web UI.

## Confirmed Fields (from get_lead output)

| Display Name | Type | Example Values |
|-------------|------|----------------|
| Date | date | 2026-07-23 |
| User | user | Bharat H |
| Petty Cash ID | text (auto) | 2026-07-23_Bharat H |
| Request Type | dropdown | `Advance`, `Reimbursement` |
| FromCompany | dropdown | `DRA Ranka Holdings`, `DRA Thindlu Land Partners`, `DRA` |
| Cash needed for | text | "Innova Fuel", "Fuel - Jaguar and Toyota Innova", "Cab Service" |
| Amount Requested | currency | ₹3,500.00, ₹6,500.00 |
| Account to be debited | dropdown | `DRA` |
| Amount Approved | currency | ₹3,500.00 |

## Stage Flow

```
Requested → Approved → Expense Details Submitted → Expense Approved → Credited & Closed
```

Appears to flow through with Eshwari as the main approver. Nishant ahfl handles first-level Requested stage. Roshini handles Expense Details Submitted.

## Query Pattern (direct HTTP, no MCP server needed)

```python
import sys, os, httpx
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.kelsa_auth import get_valid_access_token

token = get_valid_access_token()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# Search pipeline 555
search = httpx.post("https://kelsa.io/mcp", json={
    "jsonrpc": "2.0", "method": "tools/call",
    "params": {"name": "search_leads", "arguments": {"pipeline_id": 555, "per_page": 100, "page": 1}},
    "id": 1
}, headers=headers, timeout=30)

# Get detail on a record
detail = httpx.post("https://kelsa.io/mcp", json={
    "jsonrpc": "2.0", "method": "tools/call",
    "params": {"name": "get_lead", "arguments": {"lead_id": 54138660}},
    "id": 2
}, headers=headers, timeout=30)
```

## Notes

- All 71 records as of Jul 2026 are created by Bharat H — no Anbarasan records in this pipeline
- Records can sit in "Credited & Closed" or "Retired" state for extended periods (560+ days)
- The `create_lead` ghosting issue is specific to Pipeline 555 — the async processor rejects MCP-created records silently
