# Batch Lead Processing & move_stage Limitations

## Batch Processing Workflow (DRA Sales Leads, Pipeline 10)

The standard pattern for processing sales leads in bulk:

1. **Search by phone** — `search_leads(pipeline_id=10, query="<phone>")` — works with or without "91" prefix
2. **Extract lead ID** — from `[#NNNNNNNN]` in the text output. Regex: `r'\[#(\d+)\]'`
3. **Get full details** — `get_lead(lead_id=N, pipeline_id=10)` — **pipeline_id is REQUIRED** (omitting it returns "Missing required arguments: pipeline_id")
4. **Add note** — `add_note(lead_id=N, pipeline_id=10, text="...")` — the parameter is `text`, NOT `note`
5. **Move stage** — `move_stage(lead_id=N, pipeline_id=10, stage_id="Warm")` — see limitations below

### Code template (terminal with Python + httpx)

```python
import sys, os, httpx, json, re, time
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
os.environ['HERMES_SESSION_USER_ID'] = '7449813913'
from tools.kelsa_auth import get_valid_access_token

token = get_valid_access_token()
MCP_URL = "https://kelsa.io/mcp"
HEADERS = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
PIPELINE_ID = 10

# Initialize MCP session (required once)
httpx.post(MCP_URL, json={
    "jsonrpc": "2.0", "method": "initialize",
    "params": {"protocolVersion": "2025-03-26", "capabilities": {},
               "clientInfo": {"name": "hermes-batch", "version": "1.0"}},
}, headers=HEADERS, timeout=10)

def mcp_call(name, args=None, id=2):
    payload = {"jsonrpc": "2.0", "method": "tools/call",
               "params": {"name": name, "arguments": args or {}}, "id": id}
    resp = httpx.post(MCP_URL, json=payload, headers=HEADERS, timeout=30)
    data = resp.json()
    for item in data.get("result", {}).get("content", []):
        if isinstance(item, dict) and item.get("text"):
            return item["text"]
    return str(data)

def extract_lead_id(text):
    m = re.search(r'\[#(\d+)\]', text)
    return int(m.group(1)) if m else None

# Process a single lead
def process_lead(phone, note, target_stage=None):
    result = mcp_call("search_leads", {"pipeline_id": PIPELINE_ID, "query": phone, "per_page": 5})
    lid = extract_lead_id(result)
    if not lid:
        return None, "not found"
    
    mcp_call("add_note", {"pipeline_id": PIPELINE_ID, "lead_id": lid, "text": note})
    
    if target_stage:
        mcp_call("move_stage", {"pipeline_id": PIPELINE_ID, "lead_id": lid, "stage_id": target_stage})
    
    return lid, "done"
```

## Limitations of move_stage

### 1. ❌ Cannot target retired stages

Retired stages (Junk, Dead, Lost, Others in Pipeline 10) are **completely unreachable** via `move_stage`. The API rejects them with:

```
Error: Stage "Junk" not found in this pipeline. Stages: Cold (cold), Warm (warm), PSC (psc), SSV (ssv), Hot (hot), Converted (converted).
```

Note that the error lists only **active** stages — retired ones are omitted entirely. Using the internal identifier (`st_junk`) also fails identically.

**Workaround:** Add a note documenting why the lead should be junked/lost. An admin must move the lead manually in the Kelsa UI, or a pipeline automation must handle it.

### 2. ❌ Sequential progression only — no stages skipped

`move_stage` only allows jumping to the **next sequential stage** or stages the pipeline explicitly configures as jumps from the current stage.

Pipeline 10 sequence: Cold → Warm → PSC → SSV → Hot → Converted

| Current Stage | Allowed Targets | Blocked |
|---------------|----------------|---------|
| Cold | Warm | PSC, SSV, Hot, Junk |
| Warm | PSC | SSV, Hot, Junk |
| PSC | SSV | Warm, Hot, Junk |
| SSV | Hot | PSC, Warm, Junk |

Attempting a forbidden jump returns:
```
Error: The record cannot jump to "Warm" from its current stage.
Allowed targets: SSV (ssv).
```

**Workaround:** Move leads through stages sequentially. If a lead needs to go to a non-adjacent stage, satisfy the current stage's prerequisites (via `complete_task`/`perform_manual_action`) and let it advance naturally, then move again.

### 3. ❌ "Cold" leads in Pipeline 10 have a blocking prerequisite

New leads auto-land in Cold stage with an `[data_entry] Collect required information` prerequisite. Until satisfied, some `move_stage` calls may be restricted. The prerequisite requires at minimum: `cf_contact1`, `cf_source`, `cf_sourcedetails`, `cf_campaign`, `cf_project`.

If you move a Cold lead to Warm without satisfying this, the `data_entry` prerequisite stays open (Warm stage has its own prerequisites) — the move succeeds but the prerequisite task remains pending.

### 4. ❌ Stage names vs internal identifiers

The `stage_id` parameter accepts **either** the human-readable name (case-insensitive: `"Warm"`, `"warm"`, `"WARM"`) or the internal identifier. Both work for active stages. The internal identifiers from Pipeline 10:

| Stage | Internal ID |
|-------|-------------|
| Cold | st_cold |
| Warm | st_warm |
| PSC | st_psc |
| SSV | st_ssv |
| Hot | st_hot |
| Converted | st_converted |
| Others (retired) | st_others |
| Dead (retired) | st_dead |
| Junk (retired) | st_junk |
| Lost (retired) | st_lost |

Use the human-readable name (`"Warm"`) — it's simpler and equally reliable for active stages.

## Deduplication: checking for existing notes

Before adding a note to a lead, check `get_lead()` output for `"Attempt by Chennai team"` or other note prefixes. The recent activity section at the bottom of `get_lead` output shows the last N notes. If the note already exists, skip `add_note` to avoid duplicate entries.

## Phone search quirks

- Kelsa searches by phone number (stored in `cf_contact_phone` via master contact link)
- Both `919513618837` (with 91 prefix) and `9513618837` (without) return the same lead
- The lead's `IDEN` field (e.g. `a-["919513618837"]-2026-08-22`) stores the phone with 91 prefix
- **Foreign numbers** (non-Indian, like `971549954664`) also get searched by exact match
- If phone search returns 0 results, the lead likely doesn't exist yet in Kelsa (no Kelsa record for that prospect)