# Multi-Source Voice Name Resolution — DRAAS Workflow

**When the user sends a voice message with garbled names, resolve them by searching ALL available data sources in parallel before asking for clarification.**

## Source Ladder (parallel, not sequential)

Search all of these simultaneously — they're independent:

1. **Kelsa CRM (`search_leads`)** — search with multiple name variants
   - Exact: `query="Prajna"`
   - Partial: `query="Jyothi"` (catches "Pragya Joythi" even when first name is garbled)
   - Email domain fragments: `query="pm2.blr"` to find Anbarasan
   - Use `list_users` to find people by email suffix (`@draas.com`, `@drahomes.in`)

2. **Google Contacts Sheet** (ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`)
   - Direct scan via `execute_code` + `build_service('sheets', 'v4', service_name='google-draas')`
   - Search ALL columns, not just name columns — phone/email/org fields may have the match
   - Sheet title: `'NDR DRAAS Google contacts.csv'`
   - Range: `"'{title}'"` (full sheet, ~2000+ rows)

3. **Gmail (sales1.blr@draas.com)** — search recent emails from/to the garbled name
   - `q='pragya OR prajna OR joythi OR "roy.pragyajyoti"'`
   - Works when the person has emailed the company recently
   - Get `snippet` for quick context, or pull full body to confirm identity

## Name Variant Patterns (from real sessions)

| Voice Input | Actual Name | Source That Resolved It |
|-------------|-------------|------------------------|
| "Prajna Jyothi" | Pragyajyoti Roy (roy.pragyajyoti@gmail.com) | Kelsa search "Jyothi" → lead Pragya Joythi → Gmail confirmed full name |
| "Anvarasan" | Anbarasan (pm2.blr@draas.com) | Kelsa list_users → found "Anbarasan <pm2.blr@draas.com>" |
| "Arvind Jyothi" | Unknown / unresolved | Searched Kelsa + Sheet + People API — no clear match found. Flag to user. |
| "Nordic Bhattavya" | Possibly "Naveed Khan" (eng1.blr@draas.com) or "Bhattacharya" | Kelsa list_users shows Naveed Khan (engineer). Sheet shows "Bhattacharya" with no first name. Unconfirmed. |

## Pitfalls

### Contact Resolver Falls Back to tool failure → execute_code

`contact_resolver` and `entity_resolver` may fail with:
- `no gws_service configured in their profile` — the Telegram user 8717455402 (Bharat) has no gws_service set
- `TypeError: _handle() got an unexpected keyword argument 'task_id'` — tool-level bug

**Fix:** Skip the gateway tools. Go direct:
```python
from tools.gws_auth import build_service

# Sheets
sheets = build_service('sheets', 'v4', service_name='google-draas')
meta = sheets.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
title = meta['sheets'][0]['properties']['title']
rows = sheets.spreadsheets().values().get(
    spreadsheetId=SHEET_ID,
    range=f"'{title}'!A1:Z2000"
).execute()['values']

# Gmail
gmail = build_service('gmail', 'v1', service_name='google-draas')
results = gmail.users().messages().list(
    userId='me',
    q='query terms',
    maxResults=10
).execute()
```

### Kelsa Search May Not Find by First Name Alone

Kelsa `search_leads` matches against the record **name** field. A lead named "Pragya Joythi" won't come up for `query="Prajna"` but WILL come up for `query="Jyothi"`. Strategy: search surname/email fragments, not the garbled first name.

### Gmail Only Has the User's Outbox

Searching Gmail from `sales1.blr@draas.com` only shows emails this account sent/received — it won't show emails from other DRAAS accounts. For full scope, loop `google-draas`, `google-ahfl`, `google-gmail`.

### When Resolution Fails — Ask the User with Context

After exhausting all sources, present the user with:
- What you searched (which sources, what queries)
- Any partial matches (even if uncertain)
- Ask for clarification with the specific question: "Is this person [name] at [company]?"

Example from this session:
> "I found Pragyajyoti Roy (the client), Anbarasan (pm2.blr@draas.com), and you in Kelsa. But 'Arvind Jyothi' and 'Nordic Bhattavya' — could you clarify who these are?"