# Bharat Hawaldar (sales1.blr → sales1.blr) — gbrain Dream Jul 3 2026

## Context

- **Telegram ID**: sales1.blr → stale (dir exists, only `.bun/` cache, no brain)
- **DRAAS account**: sales1.blr@draas.com
- **Brain path**: `/data/hermes/users/sales1.blr/brain` (7 scaffolding pages, 1 real page)
- **Config path**: `/data/hermes/users/sales1.blr/.gbrain-writable/.gbrain/` (hermes-owned, PGLite working)
- **Embedding model**: `minimax:embo-01` (fails — MINIMAX_API_KEY not set)

## Key Findings

### 1. Old Telegram ID dir still exists
The skill previously stated the old dir was cleaned up. **It was not.** `/data/hermes/users/sales1.blr/` still exists with only `.bun/` cache (from a prior npx/bun install). No brain, no `.gbrain/` config. The Step 0 dir-exists check passes but the brain-dir check fails. The cron job targeting uid=sales1.blr was redirected to `sales1.blr` via the AUTOMATIC FALLBACK pattern.

### 2. System gitconfig lacked safe.directory for sales1.blr
When running with GBRAIN_HOME (preferred approach), HOME is NOT redirected, so git reads `/data/hermes/home/.gitconfig`. That file had `safe.directory` entries for the old Telegram ID path (`/data/hermes/users/sales1.blr/brain`) but NOT for the DRAAS account path (`/data/hermes/users/sales1.blr/brain`). Git failed with `fatal: detected dubious ownership`. Fixed by running:
```sh
git config --global --add safe.directory /data/hermes/users/sales1.blr/brain
```

### 3. GBRAIN_HOME + ~/.local/bin/bun works cleanly
The preferred approach works:
```sh
GBRAIN_HOME=/data/hermes/users/sales1.blr/.gbrain-writable \
/data/hermes/home/.local/bin/bun run /opt/gbrain/src/cli.ts dream \
  --json \
  --dir /data/hermes/users/sales1.blr/brain
```
No npx overhead, no HOME redirect, no git config breakage. Bun 1.3.14 at `~/.local/bin/bun`.

### 4. Dream result: partial (expected)
Duration: 949ms. Status: `partial`.

| Phase | Status | Note |
|---|---|---|
| lint | warn | 1 issue, 0 fixed (expected for small brain) |
| backlinks | ok | No missing back-links |
| sync | ok | Full reimport (anchor gc'd), 1 page imported |
| extract | ok | 0 links (incremental) |
| extract_facts | ok | 0 facts |
| propose_takes | ok | 7 pages scanned, 0 proposals (all LLM calls failed — ANTHROPIC_API_KEY missing) |
| **embed** | **fail** | `minimax:embo-01 requires MINIMAX_API_KEY` |
| orphans | warn | 7 orphan pages out of 7 |

The "Sync anchor object missing" triggered full reimport instead of incremental — this is expected for the first run against this brain dir's git history. Subsequent runs will be incremental.

### 5. Brain content
- `identity.md` correctly set to **Bharat Hawaldar** (bharat@draas.com)
- 6 other scaffolding pages (readmes, roshni-ranka templates)
- Only 1 chunk created (identity.md content)
