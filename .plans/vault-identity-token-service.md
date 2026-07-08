# GWS Vault — Central Identity + Token Service

**Last updated:** 2026-07-08
**Status:** Phase 1 ✅, Phase 2 not started

---

## Current State (Phase 1 Complete ✅)

- **Vault server** (`/usr/local/bin/gws-vault-server` on VPS) extended with
  `resolve`, `add_identity`, `get_identity` ops. Identity store at
  `/opt/gws-vault/identities/{user_id}.json`.
- **All 6 users migrated** from `users.json` to vault identity store (0 errors).
- **`_user_registry.py`** — tries vault `resolve()` first, falls back to file-based
  `users.json` scan. `get_user_config` and `find_user_by_identity` auto-benefit.
- **`identity_resolver.py`** — automatically resolved via vault now (calls
  `find_user_by_identity`).
- **Key verification:** `resolve("telegram", "7449813913")` → `"ndr@draas.com"` ✅,
  unknown IDs return `None` gracefully ✅.
- **VPS deployment:** vault server restarted, Hermes container restarted.
- **Known difference:** VPS has a more modern `gws_vault_client.py` than local
  (uses `VAULT_SOCKET`/`_send_recv` instead of `VAULT_SOCKET_PATH`/`_call`). Local
  `bin_gws_vault_server_live.py` was updated to match the VPS client's field
  expectations (`not_found` field).

---

## Phase 1 — Pilot: Identity Resolution via Vault

**Scope:** Make the vault the source of truth for identity (`user_id` ↔ identifier
mapping). Hermes resolves identities from vault, not `users.json`.

### 1a — Extend vault server with identity ops

Add three new operations to `bin_gws_vault_server_live.py`:

| Operation | Input | Auth | Logic |
|---|---|---|---|
| `resolve` | `identity_type`, `identity_value` | None (public read) | Scan identity store, return canonical `user_id` |
| `add_identity` | `user_id`, `identity_type`, `identity_value`, `name?`, `role?`, `permissions?` | `vault_secret` required | Create/update identity record, detect duplicate identifier → error |
| `get_identity` | `user_id`, `session_uid` | `session_uid == user_id` (self-read only) | Return full identity record (all aliases, name, role, permissions) |

**Identity store layout:**
```
/opt/gws-vault/
├── tokens/                 # existing, owned by gws-vault
│   └── {user_id}/
│       ├── google.json
│       └── gws_draas.com.json
└── identities/             # NEW, same ownership/permissions
    └── {user_id}.json      # e.g. "ndr@draas.com.json"
```

**Identity record format (stored as `{user_id}.json`):**
```json
{
  "user_id": "ndr@draas.com",
  "name": "Nishant Ranka",
  "role": "admin",
  "permissions": {},
  "identities": {
    "telegram": ["7449813913"],
    "email": ["ndr@draas.com", "ndr@ahfl.in"],
    "draas_user_id": ["ndr"]
  }
}
```

**Reverse index:** `identities/by_type/{type}/{value}.json` → symlink to
`../../{user_id}.json` for O(1) resolve lookups without scanning.

### 1b — Write migration script

`scripts/migrate_users_json_to_vault.py`:

1. Reads `users.json` from `HERMES_HOME` (or VPS path)
2. For each user record, calls `add_identity` on the vault
3. Reports progress + errors
4. Safe to re-run (idempotent — vault rejects duplicate identifiers)

### 1c — Update `_user_registry.py` to use vault

Replace file-based reads with vault `resolve()` calls. Keep `find_user_by_identity`
as the public API but change implementation:

- `find_user_by_identity("telegram", "7449813913")` → `vault.resolve("telegram", "7449813913")` → canonical `user_id` → `vault.get_identity(user_id)` → full record
- Keep `load_user_registry()` as cached fallback (for backward compat during rollout)

### 1d — Update `identity_resolver.py`

Replace `_user_registry.find_user_by_identity()` with `gws_vault_client.resolve()`
+ `gws_vault_client.get_identity()`.

### 1e — Update `gws_auth.py`

Currently uses `telegram_id` directly as `vault_uid` for token storage. After
Phase 1, resolve `telegram_id` → canonical `user_id` (email) first, then use
that as the token key. This ensures:
- One user across Telegram + Open WebUI + WhatsApp shares the same token store
- No duplicate token sets per channel

### 1f — Deploy and verify

1. Push vault server changes to VPS, restart vault daemon
2. Run migration script
3. Restart Hermes container
4. Test: Telegram session resolves identity correctly
5. Test: Open WebUI session resolves SSO email correctly
6. Test: GWS OAuth callback stores + retrieves tokens

---

## Phase 2 — Full Build: Deprecate `users.json` across services

**Scope:** All Hermes-internal identity reads go through vault. `users.json`
becomes a **legacy artifact** — Hermes no longer reads it at runtime.

### 2a — Update `bin/add-user` to write via vault

Replace direct SSH+JSON edits with `vault.add_identity()` calls. The script
already creates the gbrain home directory — keep that, but let vault own the
identity record.

### 2b — Audit all `_user_registry` / `users.json` references

Full grep for `users.json`, `_user_registry`, `user_registry`, `load_user_registry`,
`find_user_by_identity`, `get_user_config`, `USER_FILE`, `users_json`. Replace
each with vault-backed equivalents.

Key files to touch (verified via grep):
- `tools/_user_registry.py` — already addressed in 1c
- `gateway/platforms/identity_resolver.py` — already addressed in 1d
- `gateway/run.py` — session init reads `users.json` for system-prompt injection
- `tools/noun_resolver.py` — line 162 imports and uses vault (already done)
- `tools/noun_learner_tool.py` — line 118 imports and uses vault (already done)
- `tools/gws_auth.py` — already vault-backed for reads/writes, but verify `draas_user_id` resolution path

### 2c — Remove `users.json` from the Hermes Docker volume mount

Once Hermes no longer reads `users.json` at runtime, it can be removed from
`docker-compose.yml`. The admin app (Phase 3) can still mount it for audits.

### 2d — Update `identity_resolver.py` for Open WebUI

Currently `resolve_from_request` reads `X-OpenWebUI-User-Email` header and
looks up via `_user_registry`. After Phase 2, it should:
1. Extract email from header
2. `vault.resolve("email", email)` → canonical `user_id`
3. `vault.get_identity(user_id, session_uid=...)` → full identity record
4. Return `{telegram_id, email, draas_user_id, name, role, ...}`

---

## Phase 3 — Admin App (Separate from Hermes agent)

**Scope:** A standalone web app (Flask/FastAPI) for admin operations. Admin
writes (user provisioning, token management, auditing) go through this app
only — never through the Hermes agent.

### 3a — Admin app architecture

```
Admin App (container or standalone)
  ├── /auth — Google SSO or similar (delegates identity check to vault)
  ├── /users — CRUD for user identities (writes via vault.add_identity)
  ├── /tokens — View/manage stored tokens (reads via vault with admin secret)
  ├── /vault-health — Vault daemon health check
  └── /audit — Token access log (if vault ever supports it)
```

### 3b — Admin identity gate

The admin app uses vault for its own identity too:
- Admin user's identity record has `permissions: {"vault_admin": true}`
- Before any write operation, the app checks `vault.get_identity(admin_user_id).permissions`
- Hermes agent NEVER sees `GWS_VAULT_SECRET` for write ops

### 3c — Deprecation timeline

| Phase | Component | Status |
|---|---|---|
| P1 | Vault server identity ops | ✅ Deployed |
| P1 | Migration script | ✅ Run (6 users) |
| P1 | `_user_registry.py` vault-backed | ✅ Deployed |
| P2 | `remove_identity` vault server op | ✅ Deployed |
| P2 | `remove_identity` vault client func | ✅ Deployed |
| P2 | `user_mgmt_tool.py` vault dual-write | ✅ Deployed |
| P2 | `bin/add-user` vault dual-write | ✅ Deployed |
| P2 | String messages updated (users.json → registry/profile) | ✅ Deployed |
| P2 | `users.json` removed from runtime | Pending (requires P3) |
| P3 | Admin app built | Pending |
| P3 | `bin/add-user` replaced by admin app | Pending |

---

## Deploy checklist (per phase)

1. Commit changes to `hermes-agent/` repo
2. Push to VPS: `cd /opt/hermes && git pull`
3. For vault server changes: restart systemd service
4. For Hermes changes: `docker compose up -d --build hermes`
5. Run smoke test
