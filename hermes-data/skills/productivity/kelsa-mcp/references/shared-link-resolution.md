# Kelsa Shared Short Link Resolution

When a user shares a Kelsa link in the format `https://kelsa.io/s/<hash>`, you can resolve it to a Pipeline ID + Lead ID programmatically.

## Technique

```python
import httpx
import os

os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
from tools.kelsa_auth import get_valid_access_token

token = get_valid_access_token(telegram_id)
headers = {"Authorization": f"Bearer {token}"}

# Follow the redirect — do NOT follow redirects automatically
resp = httpx.get(
    "https://kelsa.io/s/<hash>",
    headers=headers,
    timeout=15,
    follow_redirects=False
)

if resp.status_code in (301, 302, 307, 308):
    redirect_url = resp.headers['location']
    # Redirect URL format:
    # https://kelsa.io/{pipeline_id}/leads?current_item_id={lead_id}&subdomain=
    print(f"Pipeline/Lead URL: {redirect_url}")
```

## What you get

The redirect URL reveals:
- **Pipeline ID** — from the URL path (e.g. `/519/`)
- **Lead ID** — from the `current_item_id` query param (e.g. `53691609`)

Example: `https://kelsa.io/519/leads?current_item_id=53691609&subdomain=`
→ Pipeline 519, Lead 53691609

## When to use this

- User shares a `kelsa.io/s/` link and you need to look up the record
- `get_lead()` returns "not found or no access" — this confirms whether the record actually exists (the redirect works) but your token lacks permission to read it (Super Admin limitation)
- You need to construct a direct Kelsa web UI URL for the user: `https://app.kelsa.io/5/leads/{lead_id}`

## Limitations

- The redirect does NOT authenticate — it just expands the short link. Any visitor gets redirected regardless of permissions.
- The subsequent `get_lead` MCP call still requires permissions — the redirect tells you the IDs, not the data.
- If the shared link was deleted or the record was removed, the redirect may go to the pipeline list page instead of a specific record.
