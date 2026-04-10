# Hermes Project — Claude Code Context

Project: Hermes AI Agent (Telegram bot, Railway deployment)
Repo: github.com/nranka79/ndr-hermes-agent (private fork)
Python: /c/Python314/python.exe (NOT `python3` — Windows Store alias intercepts it)

---

## N8N

Instance: https://transcribe.ahfl.in
API key: stored in env as HERMES_N8N_TOKEN (Railway) — do not hardcode

### Workflows

| Name | ID | Purpose |
|---|---|---|
| hermes-sheets | y0UpKyLVHV1jJo6T | Google Sheets CRUD |
| hermes-gmail | CZlngZ6QbxDxyKoL | Gmail read/send |
| hermes-drive | bXgo4sFfiEv00Xd3 | Drive list/get/create |
| hermes-calendar | 5gnGQsIgUZXQptk8 | Calendar CRUD |

Webhook base: `https://transcribe.ahfl.in/webhook/{workflow-name}`
All webhooks are POST, body at `$input.first().json.body`

### N8N Gotchas (learned the hard way)
- Code nodes: `process` global is removed. Use `$env` but that is also blocked by default (`N8N_BLOCK_ENV_ACCESS_IN_NODE=true`). Pass data in the request body instead.
- HTTP Request node: setting `sendBody: true` sends a body even on GET requests — Google APIs return HTTP 400. Use an IF node to split GET/DELETE (no body) vs POST/PUT/PATCH (with body).
- Webhook wraps POST body under `.body` key: read as `$input.first().json.body || $input.first().json`.
- `predefinedCredentialType` on HTTP Request node injects Bearer token from stored N8N credential — use this instead of generating tokens in Python.
- Multiple credentials of same type: `creds_by_type` dict picks LAST one. For Calendar, hardcode `arJhLzccI5BcX0Lj` (NDR DRAAS) not `RZ7VJKypYCyqEL47` (Rivaan Ranka).

### N8N Credentials (ID → type → account)
| ID | Type | Account |
|---|---|---|
| SosGP34vjdXM7OHj | googleSheetsOAuth2Api | ndr@draas.com |
| wk4DTjnZdvNVSubc | gmailOAuth2 | ndr@draas.com |
| kgrCRhyiWKYj341l | googleDriveOAuth2Api | ndr@draas.com |
| arJhLzccI5BcX0Lj | googleCalendarOAuth2Api | ndr@draas.com (NDR DRAAS) |
| VM2ovHwHAEOT227q | googleDocsOAuth2Api | ndr@draas.com |
| 7ObJA6A3ofXI4ovH | googleTasksOAuth2Api | ndr@draas.com |
| yh1ob3b5JqBUNq0Y | googleContactsOAuth2Api | ndr@draas.com |

---

## Google Sheets Registry

Spreadsheet ID: `1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g`

### Tab Names (exact — use these in range strings)
| Logical name | Actual tab name |
|---|---|
| contacts | `'NDR DRAAS Google contacts.csv'` (quote it — has spaces and dots) |
| projects | `projects` |
| entities | `entities` |
| land_proposals | `land_proposals` |
| topics | `topics` |

Range example: `'NDR DRAAS Google contacts.csv'!A:CN`

### Key Column Indices (0-based)
**Contacts:**
- A(0) first_name, C(2) last_name, I(8) nickname, K(10) org
- CA(78) project_assoc, CB(79) land_assoc, CE(82) addressed_as (how user addresses this contact in message salutations), CN(91) voice_misspellings, CO(92) contact_score

**Non-contacts (projects/entities/land_proposals/topics):**
- A(0) canonical_name, B(1) aliases, C(2) voice_misspellings
- D(3) associated_contacts (projects), E(4) associated_contacts (entities), F(5) associated_contacts (land/topics)

---

## Railway

### Hermes Bot Service
- Project ID: 112e98ba-305d-45ea-87ae-1e3915176567
- Service ID: 42cde9f1-5f74-4f01-b236-f78f3479abcd
- Env ID: 91a2dcb8-6ed4-4009-9bed-19a979ced590
- Bot: @NDRHermes_bot (Telegram)

### N8N Service
- In project: 07fba0a5-f776-4280-ad74-dbfd53b13136 ("inspiring-creation")
- Primary service: 627de5d3-53b9-4c09-aca3-9c15f6375d7f

### Railway API access
- The ndr@ahfl.in token has READ access to all projects but WRITE only to hermes-telegram project.
- For Railway write operations on other projects, use CLI: `railway link` with temp config in `/tmp/`.

---

## Key File Paths

| File | Purpose |
|---|---|
| `tools/n8n_tool.py` | Routes GWS operations through N8N webhooks |
| `tools/noun_resolver.py` | In-memory index + fuzzy/phonetic search across all registry sheets |
| `tools/entity_resolver_tool.py` | Agent tool: search contacts/projects/entities/land by name |
| `tools/contact_resolver_tool.py` | Agent tool: ranked contact lookup (3-signal: name+context+compound) |
| `tools/noun_learner_tool.py` | Writes corrections/associations back to sheets |
| `tools/gws/_shared.py` | OAuth2 credential loading for direct Google API calls |
| `model_tools.py` | Tool discovery/registration list |
| `toolsets.py` | Tool groupings by capability |

---

## Credential Files (Railway runtime)
- `/data/hermes/oauth-draas.json` — ndr@draas.com OAuth2 refresh token (for direct API calls)
- `DRAAS_CRED_FILE` env var points to this file

---

## Pending Work
- Add ahfl.in and nishantranka@gmail.com credentials to N8N → add credential routing by `_user` param in n8n_tool.py
- Build `hermes-docs` and `hermes-tasks` N8N workflows (credentials already in N8N: VM2ovHwHAEOT227q, 7ObJA6A3ofXI4ovH)
