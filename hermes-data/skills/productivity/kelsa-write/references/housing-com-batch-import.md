# Housing.com Batch Lead Import — Pipeline 10 (verified 2026-08-22)

For importing leads from a **Housing.com portal export sheet** into
**DRA Sales Leads (Pipeline 10)**. Covers bulk import (50+ leads) and the
direct MCP JSON-RPC pattern.

## Source Sheet Format

Housing.com export sheets typically have 18 columns. Key columns (0-indexed):
- **Col D (3)**: Lead Name — may contain bracket annotations like `(Owner)`, `(Broker)`
- **Col E (4)**: Lead Phone Number — format `(+91)-XXXXXXXXXX`
- **Col F (5)**: Lead Email — various domains
- All rows share the same Project (DRA Ranka Udaya), price band, locality

**Pre-processing needed before import:**
1. **Phone format**: `(+91)-9488813596` → `919488813596`. Strip all non-digits,
   ensure `91` prefix + last 10 digits.
2. **Name cleaning**: Remove bracket annotations from names:
   `re.sub(r'\s*\(.*?\)\s*', '', name).strip()`
   e.g. `"Harsh (Owner)"` → `"Harsh"`, `"C (Broker)"` → `"C"`
3. **Do NOT modify the source sheet** during import — read-only.

## Direct MCP JSON-RPC Pattern (for batch operations)

When `kelsa_call_tool`/`kelsa_list_tools` are available they're preferred,
but for batch operations the direct JSON-RPC approach is faster and avoids
the per-call connection overhead:

```python
import httpx, re

token = get_valid_access_token()

def mcp_call(method, args):
    resp = httpx.post('https://kelsa.io/mcp', headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }, json={
        'jsonrpc': '2.0',
        'method': 'tools/call',
        'params': {'name': method, 'arguments': args},
        'id': int(time.time() * 1000)
    }, timeout=60)
    data = resp.json()
    return data['result']['content'][0]['text']
```

## Batch Import Flow (2-step per lead)

### Step 1: Create contact in Pipeline 3429 (DRA Sales Contacts)

⚠️ **CRITICAL: cf_contact must contain ALL fields as a nested dict:**
```python
field_values = {
    'cf_contact': {
        'name': lead_name,
        'phone': '919XXXXXXXXX',
        'email': lead_email
    }
}
```
Passing `name` as a top-level param + separate `cf_contact_email`/`cf_contact_phone`
creates the contact with a **blank name**. All three must go inside `cf_contact`.

Extract contact ID: `re.search(r'ID: (\d+)', response_text)` → `int(m.group(1))`

### Step 2: Create lead in Pipeline 10 (DRA Sales Leads)

```python
field_values = {
    'cf_contact1': {'id': CONTACT_ID},
    'cf_source': 'Housing.com',
    'cf_sourcedetails': 'Housing.com',
    'cf_campaign': 'Portals',
    'cf_project': 'Ranka udaya'
}
```

**Housing.com source config** (differs from Meta/I Am Here):
| Field | Value |
|-------|-------|
| `cf_campaign` (Channel) | `Portals` |
| `cf_source` (Source) | `Housing.com` |
| `cf_sourcedetails` (SourceDetails) | `Housing.com` |
| `cf_project` (Project) | `Ranka udaya` |

The lead enters at **Cold** stage (the pipeline start stage). Leads are
automatically placed at Cold — no `stage_id` parameter needed.

### Rate limiting and sequencing

- **0.5s delay** between leads is sufficient to avoid MCP rate issues
- Each lead requires 2 calls: contact creation → lead creation
- 139 leads take ~2.5 minutes at 0.5s delay
- Leads created via this method show "created by Nishant Ranka" when using
  the shared vault token — this is expected (cosmetic, attributed to token
  owner, not the requesting user)

### Dedup

Contact search in Pipeline 3429 by phone is the only reliable dedup method.
Direct phone search in Pipeline 10 returns 0 results even when the lead
exists (phone is master-linked, not on the lead itself — see
`references/pipeline10-phone-search-limitation.md`).

Search contacts: `search_leads(pipeline_id=3429, query="cf_contact_phone:919XXXXXXXXX")`

## Pitfalls

1. **Blank contact name**: The #1 gotcha. If you don't put ALL fields inside
   `cf_contact`, the contact name field stays empty. This propagates to the
   lead display: `-["+919488813596"]` instead of `Ramamurthy-["+919488813596"]`.
   Fix requires deleting the contact+lead and re-creating — `update_lead`
   with the name field won't fix a blank name on an existing contact.
2. **Retired stages**: `move_stage` cannot move leads to retired stages
   (Junk, Dead, Lost, Others) via the tool — these stages are excluded from
   the allowed jump targets. Leads stuck at Cold with blank names must be
   cleaned up via the Kelsa web UI.
3. **Sheet still shared**: The user may need to explicitly share the sheet
   with `sales1.blr@draas.com` (editor access) — "anyone with the link" may
   not work for API access depending on the sheet's domain sharing settings.
4. **Batch processing speed**: 0.5s delay is a safe minimum. Faster than that
   risks MCP rate errors on sequential create calls.

## Cleanup (when leads are created incorrectly)

If leads were created with blank names (Step 1 skipped or misconfigured):
- They're at Cold stage, unassigned
- Can't be moved to Junk via MCP tool (retired stage restriction)
- Best option: `update_lead` to set the name (may or may not work depending
  on the contact linkage), or clean up via Kelsa web UI