# Hermes Project — Claude Code Context

Project: Hermes AI Agent (Telegram bot, Hetzner VPS deployment)
Repo: github.com/nranka79/ndr-hermes-agent (private fork)
Python: /c/Python314/python.exe (NOT `python3` — Windows Store alias intercepts it)

---

## N8N (DEPRECATED for GWS routing — 2026-07-11)

`tools/n8n_tool.py` has been REMOVED. Hermes no longer routes Gmail/Sheets/
Calendar/Docs/Tasks/Contacts through N8N webhooks. Replaced by direct
`google-api-python-client` calls written inline via the `execute_code` tool,
authenticated through `tools/gws_auth.py`'s `build_service(api, version,
service_name=...)` (per-user, multi-account, vault-backed — service names:
`google-draas`, `google-ahfl`, `google-gmail`). This is the SOLE sanctioned
path per `hermes-data/SOUL.md`: "NEVER build Google credentials inline —
always go through tools.gws_auth.build_service(...)". Confirmed working in
production logs (Gmail draft creation, real Draft IDs returned) — see Key
File Paths below. The separate `google-workspace` skill
(`skills/productivity/google-workspace/`) is a DIFFERENT, single-account,
legacy mechanism — likely superseded/redundant now, not confirmed in active
use, needs a follow-up decision on whether to remove it too.

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
postgres, redis, n8n, n8n-worker, hermes, hermes-bot2, hermes-bot3,
smart-browser, voice, free-whisper, loki, promtail, grafana, oauth2-proxy,
open-webui, oauth2-proxy-chat.

Bot: @NDRHermes_bot (Telegram, primary). Chat UI: https://chat.ahfl.in (Open
WebUI, behind Google-SSO oauth2-proxy-chat).

### Hermes container
- Startup: `python3 setup_oauth_credentials.py && exec hermes gateway run -v`
- `HERMES_HOME=/data/hermes`, mounted from host `/opt/hermes/hermes-data`
- GWS token vault: separate `gws-vault` daemon, Unix socket at
  `/run/gws-vault/vault.sock` (bind-mounted into the hermes container),
  gated by `GWS_VAULT_SECRET`. Hermes never reads token files directly.

### Deployment — MANDATORY: use `deploy_bots.sh`, never a bare `--build hermes`

`hermes`, `hermes-bot2`, and `hermes-bot3` each build and tag their **own
separate Docker image** (`hermes-hermes`, `hermes-hermes-bot2`,
`hermes-hermes-bot3`) from the identical `./hermes-agent` build context —
there's no shared `image:` key in `docker-compose.yml`. **Rebuilding one
does NOT rebuild the others, silently, with no warning.**

Always deploy any `hermes-agent` code change with:
```bash
/opt/hermes/deploy_bots.sh
# == docker compose up -d --build hermes hermes-bot2 hermes-bot3 (run from /opt/hermes)
```
**NEVER** run `docker compose up -d --build hermes` alone for a real code
change — it looks like it worked (bot1 gets the fix) but leaves bot2/bot3
frozen on old code with zero error.

**Real incident this caused (found + fixed 2026-07-30):** bot2/bot3 drifted
~12 days behind bot1's code (first diagnosed 2026-07-29, which is why
`Infrastructure_Scripts/hetzner/deploy_bots.sh` exists at all). The drift
window silently swallowed two Kelsa CRM fixes — the `kelsa_login` toolset
registration fix (2026-07-19) and the OAuth HTTPS-callback fix (2026-07-20)
— so bot3 reported "Kelsa MCP/OAuth not found" (tools never registered on
its stale image) while a user's Kelsa OAuth flow, run from a similarly
stale bot1 process that hadn't itself been rebuilt since before those
fixes, produced a broken `http://127.0.0.1:<port>/callback` URL (the agent,
finding no `kelsa_login` tool, fell back to the legacy `hermes mcp add
--auth oauth` CLI flow, which is designed for a human running it locally,
not a headless container). Fixed by running `deploy_bots.sh` (rebuild +
restart all 3 together) and verifying `kelsa_login`/`kelsa_list_tools`/
`kelsa_call_tool` are actually registered and `tools/kelsa_auth.py`'s
`REDIRECT_URI` resolves to `https://transcribe.ahfl.in/kelsa/auth/callback`
on all three running containers, not just source on disk.

### Useful commands (run on the server)
```bash
cd /opt/hermes
docker compose logs -f hermes            # or hermes-bot2 / hermes-bot3
docker compose restart hermes            # or hermes-bot2 / hermes-bot3
./deploy_bots.sh                          # rebuild + restart ALL 3 bots together — use this, not --build hermes
docker compose exec hermes bash          # or hermes-bot2 / hermes-bot3
```

### Multi-bot Telegram setup (2026-07)
3 separate telegram bot services in docker-compose, same "brain" (shared
`users.json`, `hermes-data/users/` GBrain dirs, `honcho.json`, `SOUL.md`),
but each with its OWN `HERMES_HOME` (own `config.yaml`, own session/state
DB) — no chat-history bleed between bots for the same user:

| Service | Bot token env var | HERMES_HOME (host path) |
|---|---|---|
| `hermes` (primary) | `TELEGRAM_BOT_TOKEN` | `/opt/hermes/hermes-data` |
| `hermes-bot2` | `TELEGRAM_BOT_TOKEN_2` | `/opt/hermes/hermes-data-bot2` |
| `hermes-bot3` | `TELEGRAM_BOT_TOKEN_3` | `/opt/hermes/hermes-data-bot3` |

Each `config.yaml` is a **runtime file only — NOT git-tracked, not in this
repo** (the `hermes-data/` folder tracked in the repo is a seed copy with
just `SOUL.md` + `users.json`, distinct from the live runtime dirs above).

All 3 bots share the SAME `hermes-agent` source (bind-mounted `tools/`,
`skills/`, `toolsets.py`, etc.) but run it inside 3 SEPARATE, independently
built images — see "Deployment" above. Code being right in git/on disk does
NOT mean a given bot's running process has it; only a rebuild of that
specific bot's image does.

### Default Model — Telegram Bots (2026-07-14)
All 3 bots' `config.yaml` top-level `model:` block set to:
```yaml
model:
  provider: opencode-go
  default: deepseek-v4-flash
  base_url: https://opencode.ai/zen/go/v1
  api_mode: anthropic_messages
```
Changed `default` from previous `minimax-m3` → `deepseek-v4-flash`.
`provider: opencode-go` was already correct on all 3, untouched. Per-tool/
subagent model overrides further down each `config.yaml` were already on
`opencode-go` + `deepseek-v4-flash` — untouched, no change needed there.
Edited directly on the VPS via SSH (files aren't git-tracked, so no repo
diff for the value itself — this note is the record of the change).
Requires a gateway restart per bot to take effect (`config.yaml` read at
process startup, not hot-reloaded) — restart via `docker compose restart
hermes` / `hermes-bot2` / `hermes-bot3`, or via the bot's own
telegram-triggered gateway restart.

---

## Key File Paths

| File | Purpose |
|---|---|
| `tools/gws_auth.py` | THE Gmail/Calendar/Drive/Sheets/Docs/Tasks/Contacts mechanism — replaced `tools/n8n_tool.py` (removed 2026-07-11). `build_service(api, version, service_name=...)` returns an authenticated `googleapiclient` service object (vault-backed, multi-account, auto-refreshing). Agent writes plain `google-api-python-client` calls inline via `execute_code` — e.g. `service.users().drafts().create(...)`. NOT a discrete named tool — no fixed operation menu, so it covers everything the Google APIs support (drafts included) as long as the model writes the right call. `gws_resolve_account` (separate tool) only picks WHICH service_name to use. |
| `tools/noun_resolver.py` | In-memory index + fuzzy/phonetic search across all registry sheets |
| `tools/entity_resolver_tool.py` | Agent tool: search contacts/projects/entities/land by name |
| `tools/contact_resolver_tool.py` | Agent tool: ranked contact lookup (3-signal: name+context+compound) |
| `tools/noun_learner_tool.py` | Writes corrections/associations back to sheets |
| `tools/gws_auth.py` | Per-user OAuth2 token management (vault-backed, multi-account): `build_service()`, `get_auth_url()` — used by `gws_resolve_account` tool for account resolution only, NOT Gmail/Calendar/Sheets operations. |
| `tools/kelsa_auth.py` | Per-user OAuth2.1 (PKCE, DCR) token manager for Kelsa CRM MCP (mirrors `gws_auth.py`'s shape). `REDIRECT_URI` defaults to `https://transcribe.ahfl.in/kelsa/auth/callback`; only overridden by `KELSA_REDIRECT_URI` env (not set on any of the 3 bots as of 2026-07-30). Guarded by `_reject_if_not_called_from_kelsa_tool` / `_reject_if_sandboxed` — never call this module directly from `execute_code` or a shelled-out script; always go through the `kelsa_login` tool (`tools/kelsa_tool.py`). |
| `tools/kelsa_tool.py` | Registers the `kelsa_login` / `kelsa_complete_login` (deprecated) / `kelsa_list_tools` / `kelsa_call_tool` tools (toolset `oauth`, resolved into every messaging platform's core toolset via `toolsets.py`). If these don't show up in the agent's tool list on a given bot, that bot's image is stale — see "Deployment" above, do NOT fall back to `hermes mcp add ... --auth oauth` (legacy local-interactive OAuth flow, produces an unreachable `127.0.0.1` callback for anyone but a human running the CLI locally). |
| `model_tools.py` | Tool discovery/registration list |
| `toolsets.py` | Tool groupings by capability |

Note: `tools/gws/_shared.py` does NOT exist — do not reference it. It was a
dead import in `contact_resolver_tool.py` (fixed 2026-07-07) that caused
draas contact lookups to fail and the agent to wrongly generate an OAuth
re-auth link.

Note: `skills/productivity/google-workspace/scripts/google_api.py` +
`gws_bridge.py` are a SEPARATE, single-account skill (reads one
`~/.hermes/google_token.json`, NOT the multi-account vault). This is NOT
the mechanism actually used in production (confirmed via logs — see above).
Status unclear: may be legacy/dead. Do not assume it is the active GWS path.

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
