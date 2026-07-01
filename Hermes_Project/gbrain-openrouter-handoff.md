# Hermes gbrain + User-Identity Refactor — Session Handoff

**Date:** 2026-06-28
**Status:** Today's refactor DONE. Tomorrow's LLM/embedding switch pending OpenRouter top-up.
**Working dir:** `C:\Users\ruhaan\Hermes_Project`
**Server:** `root@178.105.35.94` | SSH key: `C:\Users\ruhaan\.ssh\id_ed25519`
**Container:** `hermes-hermes-1` (image `hermes-hermes`, last recreated 2026-06-28 18:02:47 UTC)

---

## What was done today (2026-06-28)

### 1. User-identity refactor — `users.json` rekeyed + directory layout migrated
**Before:** top-level keys were Telegram numeric IDs (`"7449813913": {...}`).
**After:** top-level keys are draas.com user IDs (email local-part); Telegram ID is in `identities.telegram`.

| Top-level key (draas_user_id) | Name | telegram_id (in identities) | role | dir | gbrain pglite |
|---|---|---|---|---|---|
| `ndr` | Nishant Ranka | 7449813913 | admin | `/data/hermes/users/ndr/` | 42M ✓ |
| `rnr` | Roshini Ranka | 7245204091 | admin | `/data/hermes/users/rnr/` | 42M ✓ |
| `sales1.blr` | Bharat Hawaldar | 8717455402 | employee | `/data/hermes/users/sales1.blr/` | 42M ✓ |
| `pm2.blr` | Anbarasan Murugaperumal | 7281906252 | employee | `/data/hermes/users/pm2.blr/` | 42M ✓ |
| `vkdas` | Vinod Kumar Das | 8654428154 | employee | `/data/hermes/users/vkdas/` | 42M ✓ |
| _not in JSON_ | Prakash Singh | 8502281203 | n/a | `/data/hermes/users/8502281203/` (telegram-keyed) | n/a |

**Prakash intentionally out of `users.json`** per your earlier instruction. He's in `TELEGRAM_ALLOWED_USERS`, so the env-allowlist path still admits him. `resolve_user_id("telegram", "8502281203")` returns `None` — that's correct. If you ever want him back in JSON, use the new `manage_user` tool (see below).

### 2. Code changes
- `gateway/authz_mixin.py:316-322` — replaced `if str(user_id) in load_user_registry()` with `if resolve_user_id("telegram", str(user_id))`. Uses the explicit `identities.telegram` lookup.
- `gateway/run.py:7364-7370` — same change (mirror).
- Both files are now bind-mounted into the container (added `gateway/run.py` and `gateway/platforms/api_server.py` to the `docker-compose.yml` bind-mount list). Changes persist across container restarts.
- `tools/user_mgmt_tool.py` — full refactor:
  - `draas_user_id` is the new required field in the input schema; `telegram_id` is now stored in `identities.telegram` (not the top-level key).
  - `add`/`update` actions accept `draas_user_id`; legacy callers passing only `telegram_id` get a transparent migration (existing telegram_id-keyed entry is renamed to draas_user_id).
  - `list` action now reports `draas_user_id` + `telegram_ids[]` per user.
- `init-user-brain.sh` — new signature: `init-user-brain.sh <draas_user_id> <telegram_user_id> <user_email> <user_name>`. All 4 args required (refuses to fall back to legacy).

### 3. Backups (timestamped)
- `/opt/hermes/.refactor-backup-20260628-175443/` contains:
  - `users.json` (pre-refactor)
  - `user-7245204091/`, `user-7281906252/`, `user-7449813913/`, `user-8502281203/`, `user-8654428154/`, `user-8717455402/` (full per-user dirs)
  - `authz_mixin.py`, `run.py`, `user_mgmt_tool.py`, `init-user-brain.sh`, `docker-compose.yml` (old versions)

### 4. Useful bash detail (the bug from today)
The host has TWO separate paths that look like user-data dirs:
- `/opt/hermes/hermes-data/users/` — the **real** data (bind-mount source; container sees as `/data/hermes/users/`)
- `/data/hermes/users/` — **stale test data from May 5** (NOT the bind mount; container cannot see it)

The pilot worked because `cd /opt/hermes/hermes-data/users && mv 7449813913 ndr` uses the correct path. The bulk rename initially failed because I used `Path("/data/hermes/users/...")` in Python instead of `/opt/hermes/hermes-data/users/...`. Lesson: always operate on the host's `/opt/hermes/hermes-data/` path, never `/data/hermes/`.

### 5. Stale test data to clean up later (out of scope today)
`/data/hermes/users/{7449813913, rnr, sales1.blr}` from May 5 are leftovers from a previous refactor attempt. Not in the container, not affecting anything. Safe to delete at your leisure, or leave.

---

## What to do tomorrow — Embedding + LLM standardization

### A. OpenRouter top-up (you, on openrouter.ai)
Add credits at https://openrouter.ai/settings/credits. $5 covers months of gbrain embedding use at `$0.02/1M tokens` for `openai/text-embedding-3-small`.

### B. Verify top-up + readiness
```bash
ssh -i 'C:\Users\ruhaan\.ssh\id_ed25519' root@178.105.35.94 \
  'curl -sS https://openrouter.ai/api/v1/credits -H "Authorization: Bearer $(docker exec hermes-hermes-1 sh -c "echo \$OPENROUTER_API_KEY")"'
```
Need: `total_usage < total_credits`. Also verify a real embed call returns 200:
```bash
ssh -i 'C:\Users\ruhaan\.ssh\id_ed25519' root@178.105.35.94 \
  'curl -sS -X POST https://openrouter.ai/api/v1/embeddings -H "Authorization: Bearer $(docker exec hermes-hermes-1 sh -c "echo \$OPENROUTER_API_KEY")" -H "Content-Type: application/json" -d "{\"model\":\"openai/text-embedding-3-small\",\"input\":\"smoke\"}" | python3 -c "import json,sys; d=json.load(sys.stdin); print(\"OK dims=\"+str(len(d[\"data\"][0][\"embedding\"])))"'
```

### C. Pilot on Nishant (ndr) only — DO NOT roll to others until smoke test passes
The new config (REPLACES the current 4 fields, keeps everything else):
```json
{
  "engine": "pglite",
  "database_path": "/data/hermes/users/ndr/.gbrain/brain.pglite",
  "embedding_model": "openrouter:openai/text-embedding-3-small",
  "embedding_dimensions": 1536,
  "chat_model": "deepseek:deepseek-v4-flash",
  "provider_base_urls": {
    "minimax": "http://localhost:8765/v1",
    "openrouter": "https://openrouter.ai/api/v1",
    "deepseek": "https://opencode.ai/zen/go/v1"
  }
}
```

Path: `/opt/hermes/hermes-data/users/ndr/.gbrain/config.json` (on host) or `/data/hermes/users/ndr/.gbrain/config.json` (in container).

Notes on the chat model:
- Provider name `deepseek` + `provider_base_urls.deepseek = https://opencode.ai/zen/go/v1` routes the call through the **OpenCode Go API** (not direct DeepSeek). The bearer token in the container is `DEEPSEEK_API_KEY`, which is bridged to `OPENCODE_API_KEY` via the env var — see bridge below.
- **BRIDGE ALREADY DONE TODAY:** `DEEPSEEK_API_KEY=$OPENCODE_API_KEY` added to `/opt/hermes/.env` (line 77) AND `DEEPSEEK_API_KEY: ${OPENCODE_API_KEY}` added to `docker-compose.yml` line 110 (hermes service environment). Container recreated, `DEEPSEEK_API_KEY` is now set in the running container (length 67, matches `OPENCODE_API_KEY`).
- **Model name CONFIRMED:** `deepseek-v4-flash` exists in the OpenCode Go catalog (verified today via `GET /v1/models` with the bridged key). 20 models total; the DeepSeek entries are `deepseek-v4-pro` and `deepseek-v4-flash`. Use `deepseek-v4-flash` per your earlier instruction.
- gbrain's deepseek recipe has a hardcoded `models: ['deepseek-chat', 'deepseek-reasoner']` list, but its `tier: 'openai-compat'` implementation means any model name works at the gateway — the recipe list is advisory, not enforcing. The smoke test will confirm.

### D. Smoke test (run after config update)
```bash
docker exec hermes-hermes-1 bash -c '
  export HOME=/data/hermes/users/ndr
  cd /opt/gbrain
  echo "pilot test $(date -u +%FT%TZ)" | bun src/cli.ts put test-pilot-20260629
  bun src/cli.ts search "pilot test"
  bun src/cli.ts get test-pilot-20260629
  bun src/cli.ts doctor --fast
'
```
If 200/clean, ask for go-ahead before applying to the other 5.

### E. If pilot works, apply to the other 5
The same JSON block (above) for each of: `rnr`, `sales1.blr`, `pm2.blr`, `vkdas`. Prakash (`8502281203`) is OUT — his brain isn't in users.json and uses the telegram-id-keyed layout, so he's not in scope for this standardization.

---

## Things I learned today that future-me will need

1. **`docker compose restart hermes` does NOT reload `.env`** — it just restarts the existing container with the existing env. To apply `.env` edits, use `docker compose up -d hermes` (recreates if config changed) or `docker compose up --force-recreate -d hermes`. Confirmed: `restart` left the old 5-user list in the container; `up -d` re-resolved `${TELEGRAM_ALLOWED_USERS}` and recreated with 6.

2. **The host has two `/data/hermes`-style paths** — see "Useful bash detail" above. Always use `/opt/hermes/hermes-data/...` for actual data operations.

3. **The gateway's authz logic is in TWO files** (authz_mixin.py + run.py mirror). Both are now bind-mounted for live editing.

4. **`_user_registry.py` mtime-caches users.json** — any edits to users.json are picked up on the next read (no restart needed for users.json changes; only for code changes).

5. **gbrain's `resolve_user_id` function in `_identity_resolver.py` already supports the new schema** with a legacy fallback. No code changes needed for OAuth retrieval (`gws_vault_client.py:24` already uses it).

6. **The OAuth-retrieval tool (`gws_vault_client.py`) uses `resolve_user_id` already** — no change needed there. OAuth files live outside hermes; the separate Python tool retrieves them using the resolved user_id.

---

## Other parked flags (NOT to fix unless asked)
- 2 users (Nishant + Bharat) have no `chat_model` set in their old config — will be overwritten tomorrow anyway by the standardized chat_model.
- `GOOGLE_AI_STUDIO_API_KEY` in container env ≠ gbrain's expected `GOOGLE_GENERATIVE_AI_API_KEY` (only matters if you revisit Google — and the project is denied access on embedding models anyway).
- `Kelsa-Read` MCP server OAuth warning on every gateway start (pre-existing; not from this refactor).
- Stale `/data/hermes/users/{7449813913, rnr, sales1.blr}` test data from May 5 (host only; container can't see; safe to delete).
- `secret redaction: DISABLED` warning on every gateway start (pre-existing; recommend `security.redact_secrets: true` in config.yaml).
- `api_server` network-accessible warning (pre-existing; recommend sandboxed terminal backend + firewalling).
