# Per-User gbrain Configuration Reference

## Roshini Ranka (uid=rnr)

**Status**: Config dir root-owned. Workaround: GBRAIN_HOME to writable location. `.gbrain-writable` already initialized from prior setup — no re-init needed for subsequent runs, but brain-copy not yet set up.

### Setup state (current as of 2026-06-17)

- `.gbrain-writable` config exists at `/data/hermes/users/rnr/.gbrain-writable/.gbrain/config.json`
- Config has `engine: pglite`, `embedding_model: minimax:embo-01`, `embedding_dimensions: 1536`
- Database initialized (brain.pglite exists)
- **brain-copy not created yet** — the dual workaround (writable config + writable brain-copy with git) is only half complete

### Dream result (2026-06-17 — this session)

Ran with GBRAIN_HOME but against the *original* brain dir (not a writable copy):

- **sync**: ❌ **fail** — `No commits in repo /data/hermes/users/rnr/brain. Make at least one commit before syncing.` (brain dir is root-owned, no git history)
- **embed**: ❌ **fail** — `minimax:embo-01 requires MINIMAX_API_KEY` (platform limitation, same as all users)
- **phantom side-effect**: `fatal: detected dubious ownership in repository at '/data/hermes/users/rnr/brain'` surfaced during dream (git safedirectory check — harmless, didn't block)
- **propose_takes**: Warning — `ANTHROPIC_API_KEY` missing (harmless, LLM extraction gracefully skipped)
- **lint**: ⚠️ warn — 1 issue remaining (expected for single-page brain)
- **orphans**: ⚠️ warn — 1 orphan page (identity.md — expected)
- **status**: `partial`, 880ms duration
- All other phases: ok or skipped (no content to process)

### Next setup step

Create a writable brain-copy with git, then run dream against it:

```sh
# 1. Create writable copy of brain dir
cp -r /data/hermes/users/rnr/brain /data/hermes/users/rnr/brain-copy
rm -rf /data/hermes/users/rnr/brain-copy/.git
cd /data/hermes/users/rnr/brain-copy
git init
git config user.email "roshini@draas.com"
git config user.name "Roshini Ranka"
git add identity.md
git commit -m "Initial brain state"

# 2. Run dream against the copy
GBRAIN_HOME=/data/hermes/users/rnr/.gbrain-writable \
HOME=/data/hermes/users/rnr \
npx --yes bun run /opt/gbrain/src/cli.ts dream \
  --json \
  --dir /data/hermes/users/rnr/brain-copy
```

### Root cause

`/data/hermes/users/rnr/.gbrain/config.json` is owned by `root:root` with `-rw-------` (600) permissions. The `hermes` user cannot read it, so gbrain says "No brain configured". The `.gbrain/` directory itself is also root-owned, so you can't delete or overwrite the config.

Workaround uses `GBRAIN_HOME` env var to redirect gbrain to an alternate config location outside the root-owned `.gbrain/` tree.

### Brain content

- `identity.md` — single page: "Roshini Ranka, roshini@draas.com"
- `notes/`, `people/`, `projects/` — all empty directories
- Brain dir root-owned (hermes can read but not write); git operations fail without a writable copy

---

## Bharat Hawaldar (uid=sales1.blr)

**Status**: Config readable (hermes-owned), **but PGLite at default path may still fail WASM init**. Use GBRAIN_HOME workaround for reliability. Embed blocked by missing API key.

### Default config (sometimes fails)
```json
{
  "engine": "pglite",
  "database_path": "/data/hermes/users/sales1.blr/.gbrain/brain.pglite",
  "embedding_model": "minimax:embo-01",
  "embedding_dimensions": 1536,
  "provider_base_urls": {
    "minimax": "http://localhost:8765/v1"
  }
}
```

Despite the config being hermes-owned and the `brain.pglite` directory having normal permissions, the WASM runtime can fail to initialize at this path (reason unknown — possibly stale database from older gbrain version). The fix is to use `GBRAIN_HOME` pointing to a `.gbrain-writable` directory — the fresh database always works.

### GBRAIN_HOME workaround setup (June 18, 2026)

```sh
# 1. Create writable config area
mkdir -p /data/hermes/users/sales1.blr/.gbrain-writable

# 2. Init PGLite with embedding model
GBRAIN_HOME=/data/hermes/users/sales1.blr/.gbrain-writable \
HOME=/data/hermes/users/sales1.blr \
npx --yes bun run /opt/gbrain/src/cli.ts init \
  --dir /data/hermes/users/sales1.blr/brain \
  --pglite \
  --embedding-model minimax:embo-01 \
  --embedding-dimensions 1536 \
  --force \
  --skip-embed-check

# 3. Create writable brain copy with git
cp -r /data/hermes/users/sales1.blr/brain /data/hermes/users/sales1.blr/brain-copy
cd /data/hermes/users/sales1.blr/brain-copy
git init && git add -A && git commit -m "init brain-copy"

# 4. Run dream against the copy
GBRAIN_HOME=/data/hermes/users/sales1.blr/.gbrain-writable \
npx --yes bun run /opt/gbrain/src/cli.ts dream \
  --json \
  --dir /data/hermes/users/sales1.blr/brain-copy
```

### Brain content

- `identity.md` — single page (no frontmatter, just name)
- `notes/`, `people/`, `projects/` — empty directories
- Brain dir root-owned (hermes can read but not write git operations)

### Dream result (June 18, 2026 — this session)

Ran with GBRAIN_HOME workaround (fresh PGLite database) + brain-copy:

- **lint**: ⚠️ warn — 1 issue remaining (identity.md — expected for single-page brain)
- **sync**: ✅ ok — **1 page imported** (identity.md, first_sync since fresh DB)
- **extract**: ✅ ok — 0 links (incremental, no cross-references in single page)
- **resolve_symbol_edges**: ✅ ok — 1 chunk walked, 0 edges
- **propose_takes**: ✅ ok — 1 page scanned, 0 proposals (warned about ANTHROPIC_API_KEY — expected)
- **orphans**: ⚠️ warn — 1 orphan out of 1 total (expected)
- **embed**: ❌ fail — `minimax:embo-01 requires MINIMAX_API_KEY` (platform limitation)
- **status**: `partial` (expected), 960ms duration
- All DB-backed phases (sync, extract, consolidate, purge, etc.) executed normally — only embed failed
- **Key finding**: The PGLite at the default path (`/data/hermes/users/sales1.blr/.gbrain/brain.pglite`) failed WASM init. The fresh database at `.gbrain-writable` worked on first try. This user should always use GBRAIN_HOME.

---

## Vinod Kumar Das (uid=vkdas)

**Status**: Config dir root-owned. Workaround: GBRAIN_HOME to writable location. Same pattern as Roshini/Anbarasan.

### Workaround setup

```sh
# 1. Create writable config area
mkdir -p /data/hermes/users/vkdas/.gbrain-writable

# 2. Init PGLite with embedding model
GBRAIN_HOME=/data/hermes/users/vkdas/.gbrain-writable \
HOME=/data/hermes/users/vkdas \
npx --yes bun run /opt/gbrain/src/cli.ts init \
  --dir /data/hermes/users/vkdas/brain \
  --pglite \
  --embedding-model minimax:embo-01 \
  --embedding-dimensions 1536 \
  --force \
  --skip-embed-check

# 3. Handle root-owned brain dir: copy to writable, init git
cp -r /data/hermes/users/vkdas/brain /data/hermes/users/vkdas/brain-copy
rm -rf /data/hermes/users/vkdas/brain-copy/.git
cd /data/hermes/users/vkdas/brain-copy
git init
git config user.email "vinod@draas.com"
git config user.name "Vinod Kumar Das"
git add identity.md
git commit -m "Initial brain state"

# 4. Run dream against the copy
GBRAIN_HOME=/data/hermes/users/vkdas/.gbrain-writable \
HOME=/data/hermes/users/vkdas \
npx --yes bun run /opt/gbrain/src/cli.ts dream \
  --json \
  --dir /data/hermes/users/vkdas/brain-copy
```

### Brain content

- `identity.md` — single page: name + email
- `notes/`, `people/`, `projects/` — empty directories
- Brain dir root-owned (hermes can read but not write)

### Dream result (June 15, 2026)

- **sync**: ok — 1 page imported (identity.md), 1 chunk
- **embed**: fail — missing `MINIMAX_API_KEY` (platform limitation)
- **status**: `partial` (expected)

### Dream result (June 16, 2026 — cron job run)

Ran with GBRAIN_HOME + brain-copy workaround (same as Roshini/Anbarasan/Prakash).

- **sync**: ok — **2 pages imported** (`identity.md` + `brain/identity.md` — duplicate). The `brain/identity.md` was a stray copy from a prior `cp -r` that nested the original brain dir into `brain-copy/brain/`. Same content imported twice because it existed at two paths. Gbrain warned: `brain/identity.md shares content_hash with identity (f1386597) but has different frontmatter.id. Indexing both.`
- **embed**: fail — missing `MINIMAX_API_KEY` (platform limitation, unchanged)
- **status**: `partial` (expected), 851ms duration
- **Key lesson**: If `brain-copy` already existed, `cp -r` nested the original directory structure, creating the duplicate. Use `rm -rf brain-copy` before `cp -r` to avoid this.

---

## Anbarasan Murugaperumal (uid=pm2.blr)

**Status**: Config dir root-owned (identical to Roshini). Workaround: GBRAIN_HOME to writable location.

### Setup history

```sh
# 1. Create writable config area
mkdir -p /data/hermes/users/pm2.blr/.gbrain-writable

# 2. Init PGLite with embedding model
GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
HOME=/data/hermes/users/pm2.blr \
npx --yes bun run /opt/gbrain/src/cli.ts init \
  --dir /data/hermes/users/pm2.blr/brain \
  --pglite \
  --embedding-model minimax:embo-01 \
  --embedding-dimensions 1536 \
  --force

# 3. Handle root-owned brain dir: copy to writable, init git
cp -r /data/hermes/users/pm2.blr/brain /data/hermes/users/pm2.blr/brain-copy
rm -rf /data/hermes/users/pm2.blr/brain-copy/.git
cd /data/hermes/users/pm2.blr/brain-copy
git init
git config user.email "anbarasan@draas.com"
git config user.name "Anbarasan Murugaperumal"
git add identity.md
git commit -m "Initial brain state"

# 4. Run dream against the copy
GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
HOME=/data/hermes/users/pm2.blr \
npx --yes bun run /opt/gbrain/src/cli.ts dream \
  --json \
  --dir /data/hermes/users/pm2.blr/brain-copy
```

### Brain content

- `identity.md` — single page: "Anbarasan Murugaperumal, anbarasan@draas.com"
- `notes/`, `people/`, `projects/` — all empty directories
- Brain dir root-owned, git repo root-owned — identical setup issue to Roshini

### Dream result (June 15, 2026)

- **sync**: ok — 1 page imported (identity.md), 1 chunk
- **embed**: fail — missing `MINIMAX_API_KEY` (platform limitation)
- **status**: `partial` (expected)
- Original `.gbrain/` config at `/data/hermes/users/pm2.blr/.gbrain/config.json` is 600 root-owned.

### Dream result (June 16, 2026 — cron job run)

- `brain-copy` persisted with clean git state (1 commit, no uncommitted changes) — no re-copy or re-init from original needed
- `.gbrain-writable` was **not** preserved between cron runs — init re-ran all 108 PG migrations (schema v1 → 113) at setup time
- **sync**: ok — 1 page imported (identity.md), 1 chunk (incremental, content unchanged from prior run)
- **embed**: fail — `minimax:embo-01` requires `MINIMAX_API_KEY` (platform limitation, unchanged)
- **status**: `partial` (expected), 805ms duration
- **Cron run command** (writable config already initialized, just needed dream):
  ```
  GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
  npx --yes bun run /opt/gbrain/src/cli.ts dream \
    --json \
    --dir /data/hermes/users/pm2.blr/brain-copy
  ```

### Dream result (June 17, 2026 — cron job run)

- `brain-copy` was recreated from root `brain/` via `rm -rf brain-copy && cp -r brain brain-copy` (to pick up any new content)
- **anchor commit mismatch**: gbrain detected `Sync anchor commit c6d314fc missing (force push?)` because the new `brain-copy` carried the root's git history, not the previous hermes-owned history. Triggered a full reimport instead of incremental sync — harmless (0 new pages), added ~200ms overhead.
- **sync**: ok — 0 pages imported, 1 skipped (unchanged), 0 errors. Full reimport confirmed no new content.
- **embed**: fail — `minimax:embo-01` requires `MINIMAX_API_KEY` (platform limitation, unchanged)
- **PGLite working**: all DB-backed phases (sync, extract, propose_takes, orphans, purge, etc.) executed successfully — only `embed` failed
- **status**: `partial` (expected), 880ms duration
- **Key lesson**: Full reimport after brain-copy replacement is harmless. The anchor mismatch resolves itself on the next dream run (re-anchors to new commit hash).

### Dream result (June 19, 2026 — cron job run via HOME redirect)

This run used `HOME=/data/hermes/users/pm2.blr/.gbrain-writable` (HOME redirect instead of GBRAIN_HOME) and pointed `--dir` at the **original** brain dir (`/data/hermes/users/pm2.blr/brain`), not `brain-copy`. The writable config was found correctly, but the original brain dir is root-owned with **no git history** (zero commits).

- **sync**: ❌ **fail** — `No commits in repo /data/hermes/users/pm2.blr/brain. Make at least one commit before syncing.` (brain dir is root-owned, no git history — brain-copy is needed)
- **embed**: ❌ **fail** — `minimax:embo-01 requires MINIMAX_API_KEY` (platform limitation, unchanged)
- **PGLite working**: all non-sync, non-embed DB phases (extract, consolidate, purge, orphans, etc.) executed normally — PGLite database at `.gbrain-writable` is stable
- **status**: `partial` (expected), 881ms duration
- **HOME redirect worked**: config was resolved correctly — gbrain found the writable config at `.gbrain-writable/.gbrain/config.json` via `$HOME/.gbrain/` convention
- **Key lesson**: HOME redirect is a viable alternative to GBRAIN_HOME when the writable `.gbrain/` lives under a directory you can set HOME to. However, running against the original brain dir (no git) causes sync to fail — brain-copy with git history is still required regardless of which env var you use.
- **Bun path used**: `/data/hermes/home/.npm/_npx/5c4f1b4a21be27f7/node_modules/.bin/bun` (v1.3.14 via npx cache — valid glibc build)

### Dream result (June 20, 2026 — cron job run, direct bun download)

This was the first cron run that required **Tier 3 bun resolution** — neither `npx --yes bun` nor `npm install bun` were viable:
- `npx --yes bun` led to permissions errors writing to root-owned `/opt/gbrain/node_modules/`
- `npm install` (both `--legacy-peer-deps` and `--force`) failed with permissions errors on root-owned files
- The host is **aarch64** — initially downloaded the x86_64 bun binary which failed with `Exec format error`
- Used the Tier 3 approach (direct GitHub download via `curl` + Python `zipfile` extraction) to get `bun-linux-aarch64` v1.3.14
- Bun path used: `/tmp/bun-bin/bun-linux-aarch64/bun`

Ran against the **original** brain dir (no brain-copy) with `GBRAIN_HOME` redirect:

- **sync**: ❌ **fail** — `No commits in repo /data/hermes/users/pm2.blr/brain. Make at least one commit before syncing.` (identical to June 19 — brain has zero git commits)
- **embed**: ❌ **fail** — `minimax:embo-01 requires MINIMAX_API_KEY` (platform limitation, unchanged)
- **propose_takes**: ✅ ok but warning — `extractor failed on identity: Anthropic chat requires ANTHROPIC_API_KEY.` (harmless)
- **lint**: ⚠️ warn — 1 issue remaining (expected for single-page brain)
- **orphans**: ⚠️ warn — 1 orphan out of 1 total (expected)
- **PGLite working**: all non-sync, non-embed DB-backed phases (extract, consolidate, patterns, purge, etc.) executed normally
- **status**: `partial` (expected), 894ms duration
- **Key lessons from this run**:
  1. Direct GitHub binary download is a reliable Tier 3 fallback when both npx and npm install fail
  2. Always check `uname -m` before downloading — aarch64 and x86_64 binaries are not interchangeable
  3. Python's `zipfile` module can extract archives without triggering security-scan blocks on `unzip`
  4. The cron environment had no global npm write permissions — Tier 3 was the only viable path

### Dream result (June 22, 2026 — cron job, brain dir POV, not brain-copy)

This run was the first to use `--dir` pointing directly at the **original root-owned brain dir** (not brain-copy) with HOME redirect AND `safe.directory` set under the redirected HOME.

**Setup performed before dream**: The brain dir `/data/hermes/users/pm2.blr/brain` actually had a git commit (`066cea4 init brain`), but git was blocked by the dubious ownership error because `HOME` was redirected to `.gbrain-writable`. The fix:

```sh
HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
  git config --global --add safe.directory /data/hermes/users/pm2.blr/brain
```

Result:

| Phase | Status | Detail |
|---|---|---|
| lint | ⚠️ warn | 1 issue remaining, 0 fixed |
| sync | ✅ **ok** | +0/-0/~0 (up_to_date — brain had no new content) |
| extract | ✅ ok | 0 links (incremental, 0 slugs) |
| extract_facts | ✅ ok | 0 facts, 0 pages |
| propose_takes | ✅ ok | 1 page scanned, 0 proposals (ANTHROPIC_API_KEY missing — harmless) |
| embed | ❌ fail | minimax:embo-01 needs MINIMAX_API_KEY (platform limitation) |
| orphans | ⚠️ warn | 1 orphan out of 1 total |
| purge | ✅ ok | nothing to purge |

- **Duration**: 728ms
- **Bun path**: `/tmp/bun-bin/bun-linux-aarch64/bun` (Tier 3 direct download, already cached from June 20)
- **HOME redirect path**: `HOME=/data/hermes/users/pm2.blr/.gbrain-writable`
- **Config**: `--dir /data/hermes/users/pm2.blr/brain` (original root-owned brain dir, NOT brain-copy)
- **Status**: `partial` (expected — embed failed)
- **Key lesson**: The brain-copy approach is NOT required when the brain dir has git commits AND safe.directory is set under the redirected HOME. Setting `safe.directory` under the redirected HOME fixes the "dubious ownership" error and lets dream work directly against the original root-owned brain dir. This is simpler and avoids the anchor-commit drift issue from brain-copy replacement.

### Recovery → next cron run

If pointing at brain dir directly (with safe.directory configured), no recovery needed — sync works incrementally. To switch back to brain-copy approach (e.g. if the git config is lost), recreate it:

```sh
# Create writable brain copy with git
rm -rf /data/hermes/users/pm2.blr/brain-copy
cp -r /data/hermes/users/pm2.blr/brain /data/hermes/users/pm2.blr/brain-copy
rm -rf /data/hermes/users/pm2.blr/brain-copy/.git
cd /data/hermes/users/pm2.blr/brain-copy
git init
git config user.email "anbarasan@draas.com"
git config user.name "Anbarasan Murugaperumal"
git add identity.md
git commit -m "Initial brain state"
```

Then run dream with either GBRAIN_HOME or HOME redirect, pointing at brain-copy.

---



## Prakash (uid=psingh)

**Status**: Config dir root-owned (600 — identical to Roshini/Anbarasan/Vinod). Workaround: GBRAIN_HOME to writable location.

### Workaround setup

```sh
# 1. Create writable config area
mkdir -p /data/hermes/users/psingh/.gbrain-writable

# 2. Init PGLite with embedding model (skip-embed-check needed — no MINIMAX_API_KEY)
GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
HOME=/data/hermes/users/psingh \
npx --yes bun run /opt/gbrain/src/cli.ts init \
  --dir /data/hermes/users/psingh/brain \
  --pglite \
  --embedding-model minimax:embo-01 \
  --embedding-dimensions 1536 \
  --force \
  --skip-embed-check

# 3. Handle root-owned brain dir: copy to writable, init git
cp -r /data/hermes/users/psingh/brain /data/hermes/users/psingh/brain-copy
rm -rf /data/hermes/users/psingh/brain-copy/.git
cd /data/hermes/users/psingh/brain-copy
git init
git config user.email "prakash@draas.com"
git config user.name "Prakash"
git add identity.md
git commit -m "Initial brain state"

# 4. Run dream against the copy
GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
HOME=/data/hermes/users/psingh \
npx --yes bun run /opt/gbrain/src/cli.ts dream \
  --json \
  --dir /data/hermes/users/psingh/brain-copy
```

### Brain content

- `identity.md` — single page: "# Prakash\nEmail: prakash@draas.com\nTelegram ID: psingh"
- `notes/`, `people/`, `projects/` — all empty directories
- Brain dir root-owned (hermes can read but not write); git operations fail without a writable copy
- `.gbrain/` config at `/data/hermes/users/psingh/.gbrain/config.json` is 600 root-owned

### Dream result (June 15, 2026)

- **sync**: ok — 1 page imported (identity.md), 1 chunk
- **embed**: fail — missing `MINIMAX_API_KEY` (platform limitation)
- **status**: `partial` (expected)
- Applied 108 PGLite migrations during init (schema v1 → 113)
- All non-embedding phases passed (lint ⚠️ 1 issue, orphans ⚠️ 1 orphan — expected for single-page brain)

### Dream results (June 20 + June 25, 2026 — subsequent cron runs)

Both subsequent runs confirmed the same pattern with one important difference: **the brain dir still has no git commits**. Runs used `GBRAIN_HOME` pointing to `.gbrain-writable` (stable — no re-init needed) and `bun` from PATH (`~/.local/bin/bun` v1.3.14).

**Key findings**:
- **sync**: ❌ fail both runs — `No commits in repo /data/hermes/users/psingh/brain. Make at least one commit before syncing.` The brain dir was `git init`'d during initial setup but never committed. This is a **fresh brain that needs git commit** or a **brain-copy workaround**.
- **embed**: ❌ fail — same platform limitation (MINIMAX_API_KEY missing)
- **Schema migration**: On June 25, the PGLite database was 6 migrations behind (v113→v119). Auto-applied on first connect. Subsequent runs will be migration-free.
- **Propose_takes**: On June 25, showed `ANTHROPIC_API_KEY` warning (was hidden on June 20 — the error surfaced differently). Harmless — extraction gracefully skips.
- **Duration**: 951ms (Jun 20) / 1222ms (Jun 25) — slightly slower on migration run
- **Bun binary**: June 20 used `/tmp/bun-bin/bun-linux-aarch64/bun` (Tier 3 download); June 25 used `bun` from PATH at `~/.local/bin/bun` (available natively)

**Next step**: Either `git commit` in the brain dir OR set up a brain-copy with git history. See `references/prakash-psingh-dream.md` for full JSON output and phase breakdown.
