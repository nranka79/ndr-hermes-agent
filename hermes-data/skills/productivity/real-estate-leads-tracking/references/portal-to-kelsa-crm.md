# Portal Leads → Kelsa CRM (Pipeline 10)

After extracting portal leads from Gmail (MagicBricks, Housing.com, etc.), Bharat's workflow adds them to **Kelsa DRA Sales Leads (Pipeline 10)**. This reference bridges extraction → CRM.

## Two-Step Kelsa Creation Workflow

Each portal lead needs:
1. A **contact record** in Pipeline 3429 (DRA Sales Contacts)
2. A **lead record** in Pipeline 10 (DRA Sales Leads) linked to that contact

### ⚠️ CRITICAL: Check Pipeline 10 for existing leads FIRST

Before creating anything, **ALWAYS search Pipeline 10 by phone** to check if this person already has a lead:

```python
dupe_check = search_leads(pipeline_id=10, query="919XXXXXXXXX")  # 10-digit phone
```

**IF a lead already exists (count > 0):**
- **SKIP** creation entirely — do NOT create a new lead
- Optionally add a note on the existing lead: `add_note(lead_id, "Re-enquired via MagicBricks on 22 Jul 2026")`
- Report back to the user: "[Name] already has a lead from [date], skipped duplicate"

**IF no existing lead (count = 0):** Proceed with the two-step creation below.

⚠️ **Do NOT rely on checking Pipeline 3429 alone.** A person can have an existing lead in Pipeline 10 without having a contact in 3429, or vice versa. Always check the target pipeline (Pipeline 10) directly by phone.

**Failure example (confirmed Jul 2026):** Vijay (9901097135) had an existing lead created on 5 Jul 2026 in Pipeline 10. The agent checked Pipeline 3429 only, found an existing contact, and created a **duplicate lead** in Pipeline 10. The user explicitly corrected this — checking Pipeline 10 by phone would have caught it.

### Step 1 — Create contact in Pipeline 3429

```python
create_lead(pipeline_id=3429, field_values={
    "cf_contact": {"name": "Full Name", "phone": "919XXXXXXXXX", "email": "email@example.com"}
})
```

**⚠️ Phone prefix matters:** Use `91` prefix WITHOUT `+`. Contacts created with `+91` prefix are prone to ghosting (disappear after creation, fields become unreadable). The no-prefix format `919XXXXXXXXX` works reliably.

**⚠️ Contact already exists:** If `create_lead` returns `"already exists in pipeline 3429"`, search for the existing contact by phone:
```python
search_result = search_leads(pipeline_id=3429, query="919XXXXXXXXX")
# Extract the [#ID] from the result text
contact_id = <extracted_id>
```

### Step 2 — Create lead in Pipeline 10

```python
create_lead(pipeline_id=10, field_values={
    "cf_contact1": {"id": <contact_id>},
    "cf_source": "Magicbricks",
    "cf_sourcedetails": "MB",
    "cf_campaign": "Portals",
    "cf_project": "Ranka udaya"
})
```

**Known field values for MagicBricks leads at DRAAS:**
| Field | Identifier | Value |
|-------|-----------|-------|
| Contact | `cf_contact1` | `{"id": <contact_id>}` |
| Source | `cf_source` | `"Magicbricks"` |
| SourceDetails | `cf_sourcedetails` | `"MB"` |
| Channel | `cf_campaign` | `"Portals"` |
| Project | `cf_project` | `"Ranka udaya"` |

### Step 3 — Verify with `get_draft_status`

`create_lead` returns a draft ID (async processing). Verify it completed:
```python
get_draft_status(draft_id=<draft_id>)
# Returns: "Draft <id> completed." + lead record details with actual Lead ID
```

Then search for the created lead by phone to get its actual Kelsa link:
```python
search_leads(pipeline_id=10, query="919XXXXXXXXX")
# → [#53946205] Name-["919XXXXXXXXX"]-2026-07-22
```

### Complete Working Pattern (execute_code with MCP SDK)

When MCP gateway tools aren't available mid-conversation, use the MCP SDK directly from execute_code:

```python
import os, sys, re, asyncio
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'  # MUST set manually

import httpx
from mcp.client.streamable_http import streamable_http_client
from mcp import ClientSession
from tools.kelsa_auth import get_valid_access_token

async def run():
    token = get_valid_access_token("[REDACTED-TID]")  # Bharat's Telegram ID
    http_client = httpx.AsyncClient(headers={"Authorization": f"Bearer {token}"})

    async with streamable_http_client("https://kelsa.io/mcp", http_client=http_client) as streams:
        read_stream, write_stream, get_session_id = streams
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            
            # Step 1: Create contact
            contact_result = await session.call_tool("create_lead", arguments={
                "pipeline_id": 3429,
                "field_values": {
                    "cf_contact": {"name": name, "phone": phone, "email": email}
                }
            })
            # Extract ID from: "(ID: 53946172)"
            contact_id = int(re.search(r'ID: (\d+)', contact_result.content[0].text).group(1))
            
            await asyncio.sleep(2)  # Let async processing settle
            
            # Step 2: Create lead
            lead_result = await session.call_tool("create_lead", arguments={
                "pipeline_id": 10,
                "field_values": {
                    "cf_contact1": {"id": contact_id},
                    "cf_source": "Magicbricks",
                    "cf_sourcedetails": "MB",
                    "cf_campaign": "Portals",
                    "cf_project": "Ranka udaya"
                }
            })
            # Extract draft ID
            draft_id = int(re.search(r'draft ID: (\d+)', lead_result.content[0].text).group(1))
            
            await asyncio.sleep(2)
            
            # Step 3: Verify
            verify_result = await session.call_tool("get_draft_status", arguments={"draft_id": draft_id})
            print(f"Status: {verify_result.content[0].text[:100]}")

asyncio.run(run())
```

## Kelsa Account Details

- **Account ID:** 5 (DRAAS primary)
- **Pipeline 10 (Sales Leads):** DRA Sales Leads — Lead tracking: Cold → Warm → PSC → SSV → Hot → Converted
- **Pipeline 3429 (Sales Contacts):** DRA Sales Contacts — contact records linked to leads
- **User token:** Bharat's Telegram ID `[REDACTED-TID]` has a valid Kelsa OAuth token (auto-refreshed)
- **Kelsa MCP endpoint:** `https://kelsa.io/mcp`
- **Record URLs:** `https://kelsa.io/10/leads?current_item_id=<lead_id>`

## Pitfalls

- **create_lead returns a DRAFT ID, not a LEAD ID.** Always call `get_draft_status` and then search by phone to get the actual lead ID and link.
- **Existing contacts** (same phone) cause `"already exists"` error. Search pipeline 3429 by phone to get the existing contact ID rather than creating a duplicate.
- **Phone without `+` prefix** (`919XXXXXXXXX`) for contacts. The `+` prefix causes ghost contacts — the record disappears seconds after creation.
- **Token access:** `GWS_VAULT_SOCKET` is NOT inherited in execute_code sandboxes. Always set it manually: `os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'`. Verify the socket exists at that path in terminal first.
- **`streamable_http_client` returns 3 values:** unpack as `(read_stream, write_stream, get_session_id)` — NOT 2. The third is a callable that returns session ID.
- **Async delay:** After `create_lead`, wait 1-2 seconds before calling `get_draft_status` or searching. The async processor needs time to materialize the record.
