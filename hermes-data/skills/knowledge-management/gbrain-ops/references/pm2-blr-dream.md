# Anbarasan Murugaperumal (pm2.blr) — Dream Runs

## Run 1: 2026-06-30 — via GBRAIN_HOME → .gbrain-writable (minimax config), brain-copy

### Context
First dream run under the new DRAAS identity (pm2.blr@draas.com). The user directory was migrated from the old Telegram ID `pm2.blr` to `/data/hermes/users/pm2.blr`. The `.gbrain-writable` config and PGLite database survived the migration at the new path, but the **`database_path` in config.json was still pointing to the old pm2.blr path**.

### Pre-flight fixes
1. **Stale `database_path`**: Config at `/data/hermes/users/pm2.blr/.gbrain-writable/.gbrain/config.json` had `database_path: "/data/hermes/users/pm2.blr/.gbrain-writable/.gbrain/brain.pglite"` — old Telegram ID path. Fixed to `/data/hermes/users/pm2.blr/.gbrain-writable/.gbrain/brain.pglite` using python3:
   ```python
   import json
   path = '/data/hermes/users/pm2.blr/.gbrain-writable/.gbrain/config.json'
   with open(path) as f: cfg = json.load(f)
   cfg['database_path'] = '/data/hermes/users/pm2.blr/.gbrain-writable/.gbrain/brain.pglite'
   with open(path, 'w') as f: json.dump(cfg, f, indent=2)
   ```
2. **Brain-copy out of sync**: Root brain's `identity.md` had 2 extra lines (Telegram ID metadata `Telegram ID: pm2.blr (linked: draas_user_id=pm2.blr)`) that the brain-copy lacked — synced via `cp + git commit`.

### Invocation
```sh
GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
/data/hermes/home/.local/bin/bun run /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/pm2.blr/brain-copy
```

Bun v1.3.14 at `~/.local/bin/bun` (Tier 0 — permanent install, no npx overhead).

### Results — 2026-06-30
| Status | `partial` | Duration | 621ms |

| Phase | Status | Detail |
|---|---|---|
| lint | ⚠️ warn | 1 issue remaining, 0 fixed |
| backlinks | ✅ ok | 0 gaps found |
| sync | ✅ ok | **+1 added (identity.md)**, 1 chunk created, full reimport (anchor stale after brain-copy replacement) |
| synthesize | ⏭️ skipped | session_corpus_dir unset |
| extract | ✅ ok | 0 links, 0 timeline entries |
| extract_facts | ✅ ok | 0 facts reconciled across 0 pages |
| extract_atoms | ⏭️ skipped | not in active pack |
| resolve_symbol_edges | ✅ ok | 0 chunks walked |
| patterns | ⏭️ skipped | insufficient evidence (< 3 reflections) |
| synthesize_concepts | ⏭️ skipped | not in active pack |
| recompute_emotional_weight | ✅ ok | 0 pages recomputed (incremental) |
| consolidate | ✅ ok | 0 facts promoted into 0 takes |
| propose_takes | ⚠️ ok | 7 pages scanned, 0 proposals (warnings: no ANTHROPIC_API_KEY — harmless) |
| grade_takes | ✅ ok | 0 takes scanned |
| calibration_profile | ✅ ok | insufficient data (< 5 resolved takes) |
| conversation_facts_backfill | ⏭️ skipped | disabled (default) |
| enrich_thin | ⏭️ skipped | disabled (default) |
| skillopt | ⏭️ skipped | disabled (default) |
| embed | ❌ fail | `Embedding model "minimax:embo-01" requires MINIMAX_API_KEY` |
| orphans | ⚠️ warn | 7 orphans out of 7 total pages (auto-generated identity pages) |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items purged |

### Key Observations (Run 1)
- **All DB-backed phases work**: PGLite initialized successfully at `.gbrain-writable` path. No schema issues. All 114+ migrations were already applied from the previous init.
- **`database_path` stale after identity migration**: The `.gbrain-writable/config.json` had a hardcoded absolute path from the old Telegram ID era. The database physically existed at the new pm2.blr path, but the config pointer was wrong. Had I not fixed this, PGLite would have failed to find the database and all DB phases would report `no_database`. **Diagnosis**: Always check `database_path` when a user's home directory was renamed.
- **Config persists across runs**: The `.gbrain-writable` config and PGLite database have been stable since June 16 (creation) through June 30 — no re-init needed for routine cron runs.
- **Brain-copy diff-based sync**: Only `identity.md` had changed (2 lines added). Used direct `cp` + `git commit` instead of full `rm -rf && cp -r`. This avoids the full-reimport penalty from anchor hash loss.
- **Embed remains blocked**: Same as all DRAAS users — `MINIMAX_API_KEY` not set. The embed model is `minimax:embo-01` (from the `.gbrain-writable` config), not `zeroentropyai:zembed-1` (from the root-owned default config).
- **Sync anchor stale**: Brain-copy had a different git history (from a prior `rm -rf && cp -r` cycle), so gbrain triggered a full reimport on identity.md. Harmless (1 page, 190ms) but worth noting for monitoring.

---

## Run 2: 2026-07-07 — cron job, stale Telegram ID → DRAAS account fallback

### Context
Cron job was hardcoded with uid `pm2.blr` (stale Telegram ID). The path `/data/hermes/users/pm2.blr/` existed as a live stale dir (no brain, only `.bun/`/`.npm/` cache) — passed the Step 0 dir-exists check but had no brain. Automatic fallback to DRAAS account path `/data/hermes/users/pm2.blr` with brain-copy (hermes-owned, 2 commits: `init brain` + `sync 2026-06-30`).

### Pre-flight checks
- **Stale Telegram ID path** `pm2.blr/brain` — existed as empty dir (created Jul 5), no brain content. Fell back to `pm2.blr`.
- **Brain-copy**: `/data/hermes/users/pm2.blr/brain-copy` — hermes-owned, 2 git commits, 1 markdown file.
- **Config**: `/data/hermes/users/pm2.blr/.gbrain-writable/.gbrain/config.json` — readable, no stale `database_path` (was fixed in Run 1).
- **Bun**: `/data/hermes/home/.local/bin/bun v1.3.14` — Tier 0 permanent install.
- **Diff check**: Root brain vs brain-copy had identical file lists — no new content to sync.

### Invocation
```sh
GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
/data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/pm2.blr/brain-copy
```

### Results — 2026-07-07
| Status | `partial` | Duration | 1137ms |

| Phase | Status | Detail |
|---|---|---|
| lint | ⚠️ warn | 1 issue remaining, 0 fixed |
| backlinks | ✅ ok | 0 gaps found |
| sync | ✅ ok | **+1 added, ~0 modified, -0 deleted** (full reimport — anchor gc'd after history rewrite) |
| synthesize | ⏭️ skipped | session_corpus_dir unset |
| extract | ✅ ok | 0 links, 0 timeline entries |
| extract_facts | ✅ ok | 0 facts reconciled (2 phantoms scanned) |
| extract_atoms | ⏭️ skipped | not in active pack |
| resolve_symbol_edges | ✅ ok | 0 chunks walked |
| patterns | ⏭️ skipped | insufficient evidence |
| synthesize_concepts | ⏭️ skipped | not in active pack |
| recompute_emotional_weight | ✅ ok | 0 pages recomputed |
| consolidate | ✅ ok | 0 facts promoted into 0 takes |
| propose_takes | ⚠️ ok | 7 pages scanned, 0 proposals (all 7 failed: no ANTHROPIC_API_KEY) |
| grade_takes | ✅ ok | 0 takes scanned |
| calibration_profile | ✅ ok | holder=garry, 0 resolved takes (< 5 needed) |
| conversation_facts_backfill | ⏭️ skipped | disabled |
| enrich_thin | ⏭️ skipped | disabled |
| skillopt | ⏭️ skipped | disabled |
| embed | ❌ fail | `Embedding model "minimax:embo-01" requires MINIMAX_API_KEY` |
| orphans | ⚠️ warn | 7 orphans out of 7 total |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items purged |

### Key Observations (Run 2)
- **Anchor gc'd after history rewrite**: `Sync anchor 9d00b18a object missing (gc'd after history rewrite). Running full reimport.` — brain-copy was NOT replaced in this run, but the anchor commit had been gc'd (likely from a prior `rm -rf .git && git init` cycle during initial brain-copy setup). The `gc'd` phrasing is distinct from the `force push?` message seen in Run 1 — both trigger a full reimport but the root cause differs.
- **Post-full-reimport-import**: 1 page imported, 0 errors. Harmless.
- **PGLite healthy**: All DB-backed phases (extract_facts, consolidate, resolve_symbol_edges, orphans, purge) ran cleanly. No schema issues, no migration needed.
- **Embed still blocked**: Same `minimax:embo-01` model, same missing `MINIMAX_API_KEY`. No change.
- **Extraction blocked**: All 7 extraction calls failed with `Anthropic chat requires ANTHROPIC_API_KEY`. The `ANTHROPIC_API_KEY` from `/opt/hermes/.env` is NOT exported to the gbrain subprocess — it exists in Hermes's own env but `bun run` doesn't inherit it unless it's explicitly exported.
- **Cron job still targets stale Telegram ID**: The cron configuration needs updating from `pm2.blr` to `pm2.blr`. The automatic fallback works, but it's an extra hop.
- **brain-copy anchor gc'd observation**: The anchor gc'd even though brain-copy wasn't replaced. This means the git history rewrite happened during the initial setup of brain-copy (prior to Jun 30 Run 1), and gbrain's persisted anchor hash (stored in PGLite) outlived the git objects. The full reimport on subsequent runs is expected until the anchor is reset by a successful dream.

---

## Run 3: 2026-07-16 — cron job, numeric Telegram ID [REDACTED-TID] → DRAAS account fallback

### Context
Cron job was hardcoded with `uid=[REDACTED-TID]` (numeric Telegram ID for Anbarasan). The path `/data/hermes/users/[REDACTED-TID]/brain/` **exists** but is **completely empty** (0 files, no git repo). This is the unique case among numeric Telegram IDs — the `brain/` dir object was created by a prior gbrain operation (Jul 5 2026). Unlike other numeric IDs where the path doesn't exist at all, `[REDACTED-TID]` passes both "dir exists" and "brain dir exists" checks but has zero user content.

**Automatic fallback**: Agent consulted the Per-User Isolation table and resolved to DRAAS account `pm2.blr` with brain-copy at `/data/hermes/users/pm2.blr/brain-copy`.

### Pre-flight checks
- **Numeric ID path** `[REDACTED-TID]/brain/` — 2 entries (`.` and `..`), 0 files. Verified by `ls -la` showing only `.` and `..`.
- **Real brain-copy**: `/data/hermes/users/pm2.blr/brain-copy` — hermes-owned, git commit `7914294 sync 2026-06-30T02:01:57+00:00`, 1 file (identity.md).
- **Config**: `/data/hermes/users/pm2.blr/.gbrain-writable/.gbrain/config.json` — readable, PGLite database intact.
- **Safe.directory**: System gitconfig already has `/data/hermes/users/pm2.blr/brain-copy` and `/data/hermes/users/pm2.blr/brain` — no git config issues with GBRAIN_HOME approach.
- **Bun**: `/data/hermes/home/.local/bin/bun v1.3.14`.

### Invocation
```sh
GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
/data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/pm2.blr/brain-copy
```

### Results — 2026-07-16
| Status | `partial` | Duration | 706ms |

| Phase | Status | Detail |
|---|---|---|
| lint | ⚠️ warn | 1 issue remaining, 0 fixed |
| backlinks | ✅ ok | 0 gaps found |
| sync | ✅ ok | **+1 added, ~0 modified, -0 deleted** (full reimport — anchor gc'd: `Sync anchor 8027e855 object missing`) |
| synthesize | ⏭️ skipped | session_corpus_dir unset |
| extract | ✅ ok | 0 links, 0 timeline entries (incremental) |
| extract_facts | ✅ ok | 0 facts reconciled (2 phantoms scanned) |
| extract_atoms | ⏭️ skipped | not in active pack (pack_gated) |
| resolve_symbol_edges | ✅ ok | 0 chunks walked, 1 source walked |
| patterns | ⏭️ skipped | < 3 reflections in 30d |
| synthesize_concepts | ⏭️ skipped | not in active pack |
| recompute_emotional_weight | ✅ ok | 0 pages recomputed (incremental) |
| consolidate | ✅ ok | 0 facts → 0 takes across 0 buckets |
| propose_takes | ✅ ok | 7 pages scanned, 0 new proposals (all 7 failed: `Anthropic chat requires ANTHROPIC_API_KEY`) |
| grade_takes | ✅ ok | 0 takes scanned |
| calibration_profile | ✅ ok | holder=garry, 0 resolved takes (< 5 needed) |
| conversation_facts_backfill | ⏭️ skipped | disabled (default OFF) |
| enrich_thin | ⏭️ skipped | disabled (default OFF) |
| skillopt | ⏭️ skipped | feature flag off |
| embed | ❌ fail | `Embedding model "minimax:embo-01" requires MINIMAX_API_KEY` |
| orphans | ⚠️ warn | 7 orphan pages out of 7 total |
| schema-suggest | ✅ ok | 0 suggestions emitted |
| purge | ✅ ok | 0 items purged |

### Key Observations (Run 3)
- **Empty `--dir` produces phases, not empty JSON**: Unlike the `--dir path does not exist` failure mode (which produces no phases array), the empty-brain-dir case runs a full 22-phase cycle. The phases array is present and populated — only the `phantom` count and `orphans`/`calibration_profile` fingerprint reveal the lack of real content.
- **Anchor 8027e855 gc'd**: Different anchor hash than Run 2 (`9d00b18a`), confirming the PGLite database was re-anchored during Run 2's dream (which did write a new anchor to the DB) but git's history had the rewritten anchor gc'd again. The `gc'd after history rewrite` message confirms the root cause: brain-copy's git was rewritten during initial setup, and every subsequent dream triggers a full reimport because the DB anchor never matches git's object store.
- **PGLite healthy**: 706ms complete cycle (faster than Run 2's 1137ms). All DB phases clean.
- **Brain-copy content steady**: Still only identity.md (1 file). The 7 phantom pages in PGLite from the initial init persist — gbrain doesn't clean them up when the corresponding `.md` files are no longer on disk.
- **`--json` output clean**: Unlike some users (Roshini rnr), no log-line prefix before the JSON object. Direct `json.loads` pipe worked without `awk` preprocessing. Future runs may not be this clean — always use the `awk` safeguard.
- **Cron target needs updating**: The cron's `uid=[REDACTED-TID]` should be updated to `pm2.blr` to skip the agent-level fallback. The numeric ID path passes the directory-exists check (unique to Anbarasan) and looks valid to a naive observer, producing a plausible-looking dream report with zero actual content processing.
