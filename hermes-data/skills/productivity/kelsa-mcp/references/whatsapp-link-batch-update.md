# WhatsApp Link Batch Update — Pipeline 10

Add `https://wa.me/<phone>` links to the `cf_whatsapp_link` field on leads in Pipeline 10. The user clicks the link from their phone → opens WhatsApp chat with the client. The client sees the user's WhatsApp number.

## Trigger

User says: "Add WhatsApp links to all Warm/SSV/Hot/Cold leads" or "Put wa.me links in the WhatsApp field."

## Workflow

### Step 1: Discover field identifier

```python
result = kelsa_mcp("get_pipeline", {"pipeline_id": 10})
# → Contains: "Whatsapp Link (text) — cf_whatsapp_link"
```

### Step 2: Find leads by stage

Search by stage name as query. Use `per_page` and `page` for pagination:

```python
# First page
result = kelsa_mcp("search_leads", {"pipeline_id": 10, "query": "Warm", "per_page": 100})
# Page 2, 3...
result = kelsa_mcp("search_leads", {"pipeline_id": 10, "query": "Cold", "per_page": 100, "page": 2})
```

**⚠️ `limit` parameter is NOT supported** — it returns "unknown keyword: :limit". Use `per_page` (max ~100) + `page` instead.

### Step 3: Parse response

Response format for each lead:
```
[#53742677] Vamsi-["918296690306"]-2026-07-15 · Warm · @unassigned · updated 23m ago · https://kelsa.io/10/leads?current_item_id=53742677
```

```python
import re

def parse_leads(text):
    leads = []
    lines = text.strip().split('\n')
    for line in lines:
        line = line.strip()
        if not line.startswith('['):
            continue
        m = re.search(r'\[#(\d+)\]', line)           # lead ID
        m2 = re.search(r'\["\+?(\d+)"\]', line)      # phone (with or without +)
        m3 = re.search(r'\] (.+?)-\["', line)        # name
        if m and m2:
            leads.append({
                "id": m.group(1),
                "name": m3.group(1).strip() if m3 else "Unknown",
                "phone": m2.group(1)
            })
    return leads
```

### Step 4: Update WhatsApp link

```python
phone_clean = re.sub(r'\D', '', lead["phone"])  # strip non-digits
wa_link = f"https://wa.me/{phone_clean}"

result = kelsa_mcp("update_lead", {
    "lead_id": int(lead["id"]),
    "field_values": {"cf_whatsapp_link": wa_link}
})
# → "Update queued for processing (draft ID: ...)."
# verify: get_lead shows "Whatsapp Link: https://wa.me/..."
```

### Step 5: Verify

```python
result = kelsa_mcp("get_lead", {"lead_id": 53742677})
# Fields output includes: "Whatsapp Link: https://wa.me/918296690306"
```

## ⚠️ Known Pitfalls

- **`update_lead` is async** — returns a draft ID. Call `get_draft_status(draft_id)` to confirm completion, or just re-read the lead.
- **Rate limit** — ~2 calls/second is fine. Use `time.sleep(0.4)` between updates for large batches.
- **854 Cold leads** take ~15-20 minutes to process at 0.4s per call. Run as a background terminal process.
- **Phone numbers may have `+` prefix** in some records (e.g. `+919311088628`). Strip non-digits before building wa.me link.
- **International numbers** will get wa.me links too (e.g. `+61406798576` → `https://wa.me/61406798576`). Works as long as WhatsApp supports the country code.

## Stage Counts (as of Jul 2026)

| Stage | Count |
|-------|-------|
| Cold | 854 |
| Warm | 59 |
| SSV | 27 |
| Hot | 99 |
| **Total** | **1,039** |

## Delivery Format — HTML Page (Mobile-Friendly)

When the user says they **"can't click the link"** from Excel on their phone, the wa.me links in cells aren't tappable. Create a **self-contained HTML page** instead:

1. Fetch leads from Kelsa by stage (same as Steps 2-3 above)
2. Build a single HTML file with inline data — no external dependencies
3. Each lead gets a green **"💬 Send"** button with `href="https://wa.me/{phone}?text={url_encoded_message}"`
4. Send the HTML file via Telegram — user opens it in Chrome/Safari and taps the buttons

**Key details:**
- URL-encode the full message text with `urllib.parse.quote()`
- The wa.me link format with pre-filled message: `https://wa.me/{phone}?text={encoded_message}`
- Include the message preview at the top of the page so the user sees what they're sending
- All data goes inline in a `<script>` tag as JSON — no separate data.json needed
- Use `meta viewport` and mobile-friendly styling (cards, rounded buttons, 100% width)
- Group leads by stage with colored section headers (Warm = yellow, SSV = green)

**WhatsApp link format:**
```python
import urllib.parse
msg = "Site Visit - Ranka Udaya\n\nThank you for taking the time..."
encoded = urllib.parse.quote(msg)
link = f"https://wa.me/{phone}?text={encoded}"
```

**Important:** The `wa.me` link opens WhatsApp on the user's phone and pre-fills the message in the text box. The user still needs to tap **Send** — the link does not auto-send.

## Example Script

```python
# Full batch update example for all Warm leads
import sys, os, json, re, time
sys.path.insert(0, '/opt/hermes')
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.kelsa_auth import get_valid_access_token
token = get_valid_access_token("[REDACTED-TID]")

import httpx

def kelsa_mcp(method, params):
    payload = {"jsonrpc": "2.0", "method": "tools/call",
        "params": {"name": method, "arguments": params}, "id": 1}
    resp = httpx.post("https://kelsa.io/mcp", json=payload,
        headers={"Authorization": f"Bearer {token}"}, timeout=60)
    return resp.json()

# Get leads by stage
result = kelsa_mcp("search_leads", {"pipeline_id": 10, "query": "Warm", "per_page": 200})
# Parse and update...
```
