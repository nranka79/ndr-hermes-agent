# Lead Analysis Pattern — Direct HTTP MCP Calls

When Kelsa gateway tools (`mcp_kelsa_read_*` / `kelsa_call_tool`) are unavailable mid-conversation, query Kelsa via direct HTTP POST to the MCP endpoint using `tools.kelsa_auth.get_valid_access_token()`.

## Setup Template

```python
import sys, os, json, time, re
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'

from tools.kelsa_auth import get_valid_access_token
import httpx

token = get_valid_access_token("[REDACTED-TID]")
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

def call_mcp(method, args=None):
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {"name": method, "arguments": args or {}},
        "id": int(time.time() * 1000) % 100000
    }
    resp = httpx.post("https://kelsa.io/mcp", json=payload, headers=headers, timeout=30)
    return resp.json()
```

## Common Queries

### Stage distribution (get_stats with group_by)
```python
stats = call_mcp("get_stats", {
    "pipeline_id": 10,
    "query": "cf_project:Ranka udaya;created>20 days ago",
    "group_by": "stage"
})
```

### Parse lead IDs from search results
```python
def parse_leads(text):
    leads = []
    for line in text.split("\n"):
        if "[#" in line:
            try:
                lead_id = int(line.split("[#")[1].split("]")[0])
                name = line.split("[#")[1].split("]")[1].split("-")[0].strip() if "-" in line else ""
                phone = ""
                if '["' in line:
                    phone = line.split('["')[1].split('"]')[0]
                parts = line.split("·")
                stage = parts[1].strip() if len(parts) >= 2 else ""
                leads.append({"id": lead_id, "name": name, "phone": phone, "stage": stage})
            except:
                pass
    return leads
```

### Get notes for analysis
```python
notes = call_mcp("list_lead_notes", {"lead_id": lead_id, "limit": 10})
text = notes.get("result", {}).get("content", [{}])[0].get("text", "")
```

### Get events / stage history
```python
events = call_mcp("list_lead_events", {"lead_id": lead_id, "limit": 10})
```

### Get full lead details
```python
details = call_mcp("get_lead", {"lead_id": lead_id})
```

## Rate Limiting

Always add `time.sleep(0.3)` between sequential calls to avoid being throttled. For large batches (50+ leads), sleep 0.5s between calls.

## Pagination

`search_leads` defaults to 20 results per page. Set `per_page: 100` for max. Iterate with `page` parameter:
```python
for page in range(1, max_pages + 1):
    result = call_mcp("search_leads", {
        "pipeline_id": 10,
        "query": "cf_project:Ranka udaya;created>20 days ago",
        "page": page,
        "per_page": 100
    })
    # Extract leads...
    if "0 result" in text:
        break
```

## Draft Verification

After `create_lead` returns a draft ID, always verify:
```python
status = call_mcp("get_draft_status", {"draft_id": draft_id})
# Returns "completed" with lead info, "pending", or "failed: Validation failed: ..."
```
