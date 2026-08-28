# Petty Cash (555) — Company Master Field Resolution Blocker

## Symptoms

Calling `create_lead` on pipeline 555 with any value for `cf_fromcompany` fails with:

```
Error creating record: Invalid master value for FromCompany - <VALUE> could not be resolved,
Required fields not present: FromCompany, Acknowledgement Voucher
```

This applies to ALL formats tested:
- **Plain text** company names: `"DRA Realty Pvt Ltd."`, `"DRA Ranka Holdings"`, `"Dra realty pvt ltd."`
- **Plain integer** IDs: `1`, `10`, `100`, `1000`
- **Object format**: `{"id": 1}`
- **String IDs**: `"1"`, `"10"`

## Root Cause

The `cf_fromcompany` field is defined as `master → dra_companies_master` in the pipeline schema. This references a **companies master pipeline** that:

1. **Does NOT appear** in the 22 active pipelines listed under DRA account (ID: 5) via `list_pipelines`
2. **Cannot be accessed** via `get_pipeline` or `search_leads` — pipeline IDs 1–10000 return "not found"
3. **Cannot be discovered** through `list_pipelines` with queries like "company", "Company", "master" (only "DRA Employee Master" shows up)

The `edit_pipeline` tool returned: "Pipeline design via MCP is restricted to super admins" — so we can't inspect the field config to find the target pipeline ID.

## Existing Records DO Have Company Data

Existing Petty Cash records show company names as resolved labels:
```
FromCompany: DRA Realty Pvt Ltd.
FromCompany: DRA Ranka Holdings
FromCompany: DRA Thindlu Land Partners
```

Searching by `cf_fromcompany:NAME` works (e.g. `cf_fromcompany:DRA Realty Pvt Ltd.` returns 41 results), confirming the data is stored. But `create_lead` requires a live resolution through the companies master, which is inaccessible.

## Why This Happened

Likely causes (in order of probability):
1. **The `dra_companies_master` pipeline was deactivated/archived** but the field reference remains in the Petty Cash schema. Old records retain their resolved text labels; new records cannot resolve against it.
2. **The `dra_companies_master` pipeline exists in a hidden/system account** not exposed via `list_accounts` (only "DRA (ID: 5)" is listed).
3. **The current OAuth token lacks `read` scope on the companies master** even though it has write scope on Petty Cash.

## Workarounds

| # | Approach | Feasibility |
|---|----------|-------------|
| 1 | Use Kelsa web UI to create Petty Cash records (company dropdown resolves correctly there) | ✅ Works if user has UI access |
| 2 | Ask super admin (likely Kelsa support or someone with `mcp:design` scope) to re-link or expose `dra_companies_master` | ✅ Permanent fix |
| 3 | Create the record via MCP without the company field, then have user update it via UI | ❌ `cf_fromcompany` is required |
| 4 | Use the Kelsa API with cookie-based auth (browser session) to POST the record | Possible but complex |
| 5 | File a support request with Kelsa to restore `dra_companies_master` as a visible pipeline | Medium effort |

## Cross-Pipeline Impact

The same `dra_companies_master` reference appears in:
- **DRA PO-WO Issuing (537)**: `Company Name Master → cf_company_name1` — likely same blocker
- **DRA Invoice Processing (516)**: `Invoiced to the Company → cf_invoiced_to_the_company1` — likely same blocker

## Reproduction (for future debugging)

```python
import asyncio, json
from tools.mcp_tool import _ensure_mcp_loop, _run_on_mcp_loop
from tools.kelsa_tool import _connect_and_run
from tools.kelsa_auth import get_valid_access_token
from gateway.session_context import get_gws_identity_env

_ensure_mcp_loop()
tid = get_gws_identity_env().strip()
token = get_valid_access_token(tid)

async def test(session):
    # All of these fail:
    for val in ["DRA Realty Pvt Ltd.", "DRA Ranka Holdings", 1, "1", {"id": 1}]:
        r = await session.call_tool("create_lead", {
            "pipeline_id": 555,
            "field_values": {
                "cf_date": "2026-07-25",
                "cf_request_type": "Reimbursement",
                "cf_fromcompany": val,
                "cf_amount_requested": 100,
                "cf_cash_needed_for": "Test"
            },
            "name": "test_blocker"
        })
        print(f"{val}: {r.content[0].text[:100] if r.content else 'empty'}")

_run_on_mcp_loop(_connect_and_run(token, test), timeout=60)
```
