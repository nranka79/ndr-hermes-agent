# Hermes Project — Claude Code Context

Project: Hermes AI Agent (Telegram bot, Railway deployment)
Repo: github.com/nranka79/ndr-hermes-agent (private fork)
Python: /c/Python314/python.exe (NOT `python3` — Windows Store alias intercepts it)

---

## N8N

Instance: https://transcribe.ahfl.in (Hetzner, self-hosted)
API key: stored in env as HERMES_N8N_TOKEN — do not hardcode

### Workflows

| Name | ID | Purpose |
|---|---|---|
| hermes-sheets | ldcUjFvyJsrVVDRz | Google Sheets CRUD |
| hermes-gmail | 07skMESRJ1rvFwI3 | Gmail read/send |
| hermes-calendar | vQJMyrOLwnxgu2A0 | Calendar CRUD |
| hermes-docs | 2BOMt8fhwpXPlrw5 | Google Docs |
| hermes-tasks | Qr53kyRRekxaFINN | Google Tasks |
| hermes-contacts | Q77vS5DKTRlW1lSd | Google Contacts |

Webhook base: `https://transcribe.ahfl.in/webhook/{workflow-name}`
All webhooks are POST, body at `$input.first().json.body`

### N8N Gotchas (learned the hard way)
- Webhook wraps POST body under `.body` key: read as `$input.first().json.body || $input.first().json`.
- Task runner VM (N8N 2.x) does NOT have `fetch`, `URL`, `URLSearchParams` as globals. All workflows use an https-module fetch polyfill + manual encodeURIComponent for query strings.
- `N8N_BLOCK_ENV_ACCESS_IN_NODE=false` must be set on BOTH `n8n` AND `n8n-worker` — worker runs all Code node executions in queue mode.
- SA auth pattern: all 6 workflows use `$env.GOOGLE_SA_KEY` (JSON) to mint a JWT → exchange for access token → call Google APIs directly. No stored N8N OAuth credentials needed for these workflows.
- `NODE_FUNCTION_ALLOW_BUILTIN: "*"` on both n8n and n8n-worker (crypto + https needed; `*` avoids enumerating).

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

## CRITICAL INSTRUCTION - MUST ALWAYS FOLLOW
Respond like a caveman. Skill at /caveman. Cut articles, filler, pleasantries. Keep all technical substance. 
Code blocks unchanged. Error messages quoted exactly. Technical terms intact.
