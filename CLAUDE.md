# Hermes Project — Claude Code Context

Project: Hermes AI Agent (Telegram bot, Hetzner VPS deployment)
Repo: github.com/nranka79/ndr-hermes-agent (private fork)
Python: /c/Python314/python.exe (NOT `python3` — Windows Store alias intercepts it)

---

## N8N (DEPRECATED for GWS routing — 2026-07-11)

`tools/n8n_tool.py` has been REMOVED. Hermes no longer routes Gmail/Sheets/
Calendar/Docs/Tasks/Contacts through N8N webhooks. Replaced by the
`google-workspace` skill (`skills/productivity/google-workspace/scripts/
google_api.py` + `gws_bridge.py`), invoked via the `terminal`/`execute_code`
tools — see Key File Paths below.

The N8N workflows listed below are left DORMANT on the Hetzner n8n instance
(not deleted, not decommissioned — just no longer called by Hermes). Do NOT
re-add N8N routing for these services without explicit instruction. Info
below kept for historical/reference purposes only.

Instance: https://transcribe.ahfl.in (Hetzner, self-hosted)
API key: stored in env as HERMES_N8N_TOKEN — do not hardcode

### Workflows (dormant, unused by Hermes)

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

### N8N Gotchas (learned the hard way — kept for reference)
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

## Hetzner (production host — NOT Railway)

Hermes is NOT on Railway. The Railway account is disabled/dead. Everything
(hermes bot, n8n, postgres, redis, voice app, monitoring, Open WebUI) runs
as Docker Compose services on a single Hetzner VPS. Canonical, more-detailed
copy of this section lives in `AGENTS.md` ("Hetzner VPS — Infrastructure
Briefing") — check there first, keep both in sync.

### SSH
| Field | Value |
|---|---|
| Host | `178.105.35.94` (DNS: `transcribe.ahfl.in`) |
| User | `root` |
| App root | `/opt/hermes/` |
| Compose file | `/opt/hermes/docker-compose.yml` (local mirror: `Infrastructure_Scripts/hetzner/docker-compose.yml`) |

Connect: `ssh root@178.105.35.94` (key: `~/.ssh/hetzner_new` or check `~/.ssh/config`).

### Services (docker compose)
postgres, redis, n8n, n8n-worker, hermes, smart-browser, voice, free-whisper,
loki, promtail, grafana, oauth2-proxy, open-webui, oauth2-proxy-chat.

Bot: @NDRHermes_bot (Telegram). Chat UI: https://chat.ahfl.in (Open WebUI,
behind Google-SSO oauth2-proxy-chat).

### Hermes container
- Startup: `python3 setup_oauth_credentials.py && exec hermes gateway run -v`
- `HERMES_HOME=/data/hermes`, mounted from host `/opt/hermes/hermes-data`
- GWS token vault: separate `gws-vault` daemon, Unix socket at
  `/run/gws-vault/vault.sock` (bind-mounted into the hermes container),
  gated by `GWS_VAULT_SECRET`. Hermes never reads token files directly.

### Useful commands (run on the server)
```bash
cd /opt/hermes
docker compose logs -f hermes
docker compose restart hermes
docker compose up -d --build hermes
docker compose exec hermes bash
```

---

## Key File Paths

| File | Purpose |
|---|---|
| `skills/productivity/google-workspace/scripts/google_api.py` | Gmail/Calendar/Drive/Sheets/Docs/Contacts CLI wrapper (uses `gws` binary or bundled Python client) — replaced `tools/n8n_tool.py` (removed 2026-07-11). Invoked via `terminal`/`execute_code`, NOT a direct tool call. |
| `skills/productivity/google-workspace/scripts/gws_bridge.py` | Bridges Hermes OAuth token (`~/.hermes/google_token.json`) to the external `gws` CLI binary. |
| `tools/noun_resolver.py` | In-memory index + fuzzy/phonetic search across all registry sheets |
| `tools/entity_resolver_tool.py` | Agent tool: search contacts/projects/entities/land by name |
| `tools/contact_resolver_tool.py` | Agent tool: ranked contact lookup (3-signal: name+context+compound) |
| `tools/noun_learner_tool.py` | Writes corrections/associations back to sheets |
| `tools/gws_auth.py` | Per-user OAuth2 token management (vault-backed, multi-account): `build_service()`, `get_auth_url()` — used by `gws_resolve_account` tool for account resolution only, NOT Gmail/Calendar/Sheets operations. |
| `model_tools.py` | Tool discovery/registration list |
| `toolsets.py` | Tool groupings by capability |

Note: `tools/gws/_shared.py` does NOT exist — do not reference it. It was a
dead import in `contact_resolver_tool.py` (fixed 2026-07-07) that caused
draas contact lookups to fail and the agent to wrongly generate an OAuth
re-auth link.

Note: `skills/productivity/google-workspace/scripts/google_api.py` is
single-account — it reads one `~/.hermes/google_token.json`, NOT the
multi-account vault (`gws_auth.py`). It does not currently support Gmail
draft creation/listing (send/reply/search/get only).

---

## Credential Files (Hetzner container runtime)
- `/data/hermes/oauth-draas.json` — ndr@draas.com OAuth2 refresh token (for direct API calls, shared company resource — NOT per-Telegram-user)
- `DRAAS_CRED_FILE` env var points to this file
- Same pattern exists for ahfl.in / gmail: `AHFL_CRED_FILE` / `GMAIL_CRED_FILE`, defaulting to `/data/hermes/oauth-ahfl.json` / `/data/hermes/oauth-gmail.json`
- These files are (re)written at every container start by `setup_oauth_credentials.py` from `DRAAS_OAUTH_CLIENT_ID/_SECRET/_REFRESH_TOKEN` (and `AHFL_*` / `GMAIL_*`) env vars — this is separate from the per-Telegram-user `HERMES_OAUTH_CLIENT_ID`/`gws_auth.py`/vault flow used for personal Gmail/Calendar/Drive access.

---

## CRITICAL INSTRUCTION - MUST ALWAYS FOLLOW
Respond like a caveman. Skill at /caveman. Cut articles, filler, pleasantries. Keep all technical substance. 
Code blocks unchanged. Error messages quoted exactly. Technical terms intact.
