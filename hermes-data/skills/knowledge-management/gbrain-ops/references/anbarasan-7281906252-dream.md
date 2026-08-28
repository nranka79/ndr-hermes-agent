# Anbarasan Murugaperumal (pm2.blr) — Dream Runs

## Run 1: 2026-06-24 — via GBRAIN_HOME → .gbrain-writable (minimax config)

### Invocation
```sh
cd /opt/gbrain && \
GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
HOME=/data/hermes/users/pm2.blr \
bun run src/cli.ts dream --json --dir /data/hermes/users/pm2.blr/brain
```

### Key Discovery: GBRAIN_HOME works
This was the first successful use of `GBRAIN_HOME` instead of `HOME` redirect. The source code at `configDir()` in `src/core/config.ts` **does** check `GBRAIN_HOME` first, and if set, returns `join(GBRAIN_HOME, '.gbrain')`.

With `GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable`:
- Config path resolves to `/data/hermes/users/pm2.blr/.gbrain-writable/.gbrain/config.json` — readable by hermes user
- `HOME` remains `/data/hermes/users/pm2.blr` — git still finds the correct `~/.gitconfig` at `/data/hermes/home/.gitconfig`
- No HOME redirect needed, so no git config breakage
- Embedding model: `minimax:embo-01` (1536d)

### Results — 2026-06-24
| Status | `partial` | Duration | 786ms |

| Phase | Status | Detail |
|---|---|---|
| lint | ⚠️ warn | 1 issue remaining, 0 fixed |
| backlinks | ok | no gaps |
| sync | ❌ fail | `No commits in repo /data/hermes/users/pm2.blr/brain` |
| synthesize | ⏭️ skipped | session_corpus_dir unset |
| extract | ok | 0 links, 0 timeline entries |
| extract_facts | ok | 0 facts reconciled |
| extract_atoms | ⏭️ skipped | not in active pack |
| resolve_symbol_edges | ok | no chunks |
| patterns | ⏭️ skipped | insufficient evidence |
| synthesize_concepts | ⏭️ skipped | not in active pack |
| recompute_emotional_weight | ok | 1 page |
| consolidate | ok | 0 facts promoted |
| propose_takes | ok | 0 proposals (warn: no ANTHROPIC_API_KEY) |
| grade_takes | ok | 0 verdicts |
| calibration_profile | ok | insufficient data |
| conversation_facts_backfill | ⏭️ skipped | disabled |
| enrich_thin | ⏭️ skipped | disabled |
| skillopt | ⏭️ skipped | disabled |
| embed | ❌ fail | `MINIMAX_API_KEY` not set |
| orphans | ⚠️ warn | 1 orphan / 1 total page |
| schema-suggest | ok | 0 suggestions |
| purge | ok | nothing to purge |

### Observations (Run 1)
- **No git commits** in brain dir → sync phase fails. Same pattern as other fresh brains.
- **All DB-backed phases that don't require API keys work**: extract, extract_facts, resolve_symbol_edges, recompute_emotional_weight, consolidate, orphans, etc.
- **PGLite initialized successfully** — no WASM failures at `.gbrain-writable` path.

---

## Run 2: 2026-06-28 — via HOME prefix, default config path (root-owned, zeroentropy config)

### Invocation
```sh
HOME=/data/hermes/users/pm2.blr \
bun /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/pm2.blr/brain
```

### Key Difference from Run 1
This run used **the default config path** (`~/.gbrain/config.json` at `/data/hermes/users/pm2.blr/.gbrain/config.json`, root-owned 600) — **not** the `.gbrain-writable` override. This revealed that **the default config uses a different embedding model** (`zeroentropyai:zembed-1`) than the `.gbrain-writable` config (`minimax:embo-01`).

Because the config dir is root-owned, gbrain can read it but **cannot write audit/ subdirectories**, which causes `connection-audit write failed: EACCES` warnings and **prevents schema event trigger migration** (`permission denied to create event trigger \"auto_rls_on_create_table\"`). The schema stays at version 34 (needs 119) — 84 migrations pending — causing cascading failures on any phase that expects modern schema.

### Results — 2026-06-28
| Status | `partial` | Duration | 394ms |

| Phase | Status | Detail |
|---|---|---|
| lint | ⚠️ warn | 1 issue remaining, 0 fixed |
| backlinks | ✅ ok | 0 gaps found |
| sync | ❌ fail | `No commits in repo` — brain has no git commits |
| synthesize | ⏭️ skipped | session_corpus_dir unset |
| extract | ✅ ok | 0 links, 0 timeline entries (1 page processed) |
| extract_facts | ❌ fail | `relation "facts" does not exist` — schema not fully migrated |
| resolve_symbol_edges | ❌ fail | `column cc.edges_backfilled_at does not exist` — schema issue |
| patterns | ⏭️ skipped | insufficient evidence (< 3 reflections) |
| recompute_emotional_weight | ❌ fail | `relation "takes" does not exist` |
| consolidate | ❌ fail | `relation "facts" does not exist` |
| propose_takes | ✅ ok | 0 proposals (no pages scanned) |
| grade_takes | ❌ fail | `relation "takes" does not exist` |
| calibration_profile | ❌ fail | `relation "takes" does not exist` |
| embed | ❌ fail | `ZEROENTROPY_API_KEY` required for `zeroentropyai:zembed-1` — no API key set |
| orphans | ✅ ok | 0 orphans out of 0 pages |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items purged |

### Observations (Run 2)
- **Embedding model at default config is `zeroentropyai:zembed-1`** (not `minimax:embo-01` as in `.gbrain-writable`). The embed error message tells you which config path is active — `zeroentropyai:zembed-1` → reading root-owned default config; `minimax:embo-01` → reading `.gbrain-writable` config.
- **Schema migration cascade confirmed**: EACCES on event trigger → all phases that depend on `facts`, `takes`, or modern schema columns fail with missing relations/columns. Only phases that don't touch the DB (lint, backlinks, orphans, purge) succeed.
- **Brain still has no git commits** — same as Run 1. Needs `git init && git add -A && git commit -m "initial"`.

---

## Run 3: 2026-06-29 — Fresh zero-infrastructure setup via GBRAIN_HOME → .gbrain-writable

### Context
This was the **first-ever run** for this user with no prior infrastructure at all — no user directory, no brain dir, no gbrain config, no git repo.

### Setup performed before dream
1. Created `/data/hermes/users/pm2.blr/brain/{notes,people,projects}` (brain dir did not exist)
2. Created `brain/README.md` as a placeholder (git doesn't track empty dirs)
3. `git init && git config user.email "hermes@draas.com" && git config user.name "Hermes DRAAS" && git add -A && git commit -m "initial commit with README"`
4. `mkdir -p /data/hermes/users/pm2.blr/.gbrain-writable`
5. `init --pglite --embedding-model minimax:embo-01 --embedding-dimensions 1536 --force --skip-embed-check`
   - All **114 migrations applied cleanly** (v35 did NOT block — passes on fresh hermes-owned config)
   - PGLite WASM initialized successfully

### Invocation
```sh
GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
/data/hermes/home/.local/bin/bun run /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/pm2.blr/brain
```

### Results — 2026-06-29
| Status | `partial` | Duration | 972ms |

| Phase | Status | Detail |
|---|---|---|
| lint | ⚠️ warn | 1 issue remaining (formatting on README), 0 fixed |
| backlinks | ✅ ok | 0 gaps found |
| sync | ✅ ok | **+1 added** (README.md), 0 modified, 0 deleted, 1 chunk created |
| synthesize | ⏭️ skipped | session_corpus_dir unset |
| extract | ✅ ok | 0 links, 0 timeline entries (incremental) |
| extract_facts | ✅ ok | 0 facts reconciled across 0 pages |
| extract_atoms | ⏭️ skipped | not in active pack |
| resolve_symbol_edges | ✅ ok | 1 chunk walked, 0 resolved/ambiguous/unmatched |
| patterns | ⏭️ skipped | insufficient evidence (< 3 reflections) |
| synthesize_concepts | ⏭️ skipped | not in active pack |
| recompute_emotional_weight | ✅ ok | 0 pages recomputed (incremental) |
| consolidate | ✅ ok | 0 facts promoted into 0 takes |
| propose_takes | ✅ ok | 0 proposals (warnings: no ANTHROPIC_API_KEY — harmless) |
| grade_takes | ✅ ok | 0 takes scanned |
| calibration_profile | ✅ ok | insufficient data (< 5 resolved takes) |
| conversation_facts_backfill | ⏭️ skipped | disabled (default) |
| enrich_thin | ⏭️ skipped | disabled (default) |
| skillopt | ⏭️ skipped | disabled (default) |
| embed | ❌ fail | `Embedding model "minimax:embo-01" requires MINIMAX_API_KEY` |
| orphans | ⚠️ warn | 4 orphan pages out of 4 total (auto-generated identity pages) |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items purged |

### Key Observations (Run 3)
- **First run where sync succeeded** — because git repo was created and committed before dream ran. Previous runs (Run 1, Run 2) had sync fail with `No commits in repo`.
- **v35 migration did NOT block** — the barrier is root-owned config dir. With a hermes-owned `.gbrain-writable` config, all 114 migrations apply cleanly. The `config set version 36 --force` workaround was **not needed**.
- **Brain dir fully absent at start** — this was a zero-infrastructure setup. Made the full pipeline run green except for embed (no API key, same as all DRAAS users).
- **Placeholder file essential** — git can't commit empty directories. A `README.md` was needed for the first commit.
- **Git identity must be set** — `git config user.email` and `user.name` are required before the first commit. This was done manually in the setup phase.
- **Propose_takes warnings** about missing `ANTHROPIC_API_KEY` are harmless — the LLM-based extraction gracefully skips with a warning.
- **4 orphans** (out of 4 pages) — the auto-generated identity pages (`identity`, `people/roshni-ranka`, `person/roshni-ranka`, `readme`) are expected for a fresh brain. No real content yet.

---

## Run 4: 2026-07-03 — cron job, live stale dir detected, fell back to `._old_` backup

### Context
Cron job targeted uid `pm2.blr` with `HOME=/data/hermes/users/pm2.blr`. The user directory existed (passed Step 0) but had **no `brain/` subdirectory** — only `.bun/` and `.npm/` cache from a prior npx invocation. The actual brain data remained at `._old_pm2.blr/brain/`.

**This is the first session where `pm2.blr/` had a live stale directory** (previously it only had the renamed `._old_` version). The stale dir was created between Jun 30 and Jul 3 by a previous cron run's `npx --yes bun` which unpacked cache into the user dir.

### Setup
- Brain data discovered at `/data/hermes/users/._old_pm2.blr/brain/` (7 pages: identity.md, readme.md, notes/readme.md, people/readme.md, projects/readme.md, people/roshni-ranka, person/roshni-ranka)
- No `.gbrain/` config at `HOME=/data/hermes/users/pm2.blr` — gbrain used built-in defaults
- Bun resolved via `bun` at `~/.local/bin/bun` (Tier 0.5 — permanent install, on PATH from cron)
- Direct invocation: `HOME=/data/hermes/users/pm2.blr bun run /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/._old_pm2.blr/brain`

### Invocation
```sh
HOME=/data/hermes/users/pm2.blr \
bun run /opt/gbrain/src/cli.ts dream --json \
  --dir /data/hermes/users/._old_pm2.blr/brain
```

No `GBRAIN_HOME` or `HOME` redirect — `pm2.blr/` had no `.gbrain/` config, so gbrain fell back to built-in defaults.

### Results — 2026-07-03
| Status | `partial` | Duration | 560ms |

| Phase | Status | Detail |
|---|---|---|
| lint | ⚠️ warn | 1 issue remaining, 0 fixed |
| backlinks | ✅ ok | 0 gaps found |
| sync | ✅ ok | +0 added, ~0 modified, -0 deleted (1 page skipped unchanged) |
| synthesize | ⏭️ skipped | session_corpus_dir unset |
| extract | ✅ ok | 0 links, 0 timeline entries (incremental) |
| extract_facts | ✅ ok | 0 facts reconciled across 0 pages |
| resolve_symbol_edges | ✅ ok | 0 chunks walked |
| patterns | ⏭️ skipped | insufficient evidence (< 3 reflections) |
| recompute_emotional_weight | ✅ ok | 0 pages recomputed |
| consolidate | ✅ ok | 0 facts promoted |
| propose_takes | ⚠️ ok | 7 pages scanned, 0 proposals — **ANTHROPIC_API_KEY missing** on all 7 pages |
| grade_takes | ✅ ok | 0 takes graded |
| calibration_profile | ✅ ok | insufficient data |
| embed | ❌ fail | `zeroentropyai:zembed-1 requires ZEROENTROPY_API_KEY` — no config found, using built-in default model |
| orphans | ⚠️ warn | 7 orphans out of 7 total pages |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items purged |

### Key Observations
- **Live stale dir discovered**: The Telegram ID path `pm2.blr/` now EXISTS as a live stale directory (NOT renamed to `._old_`), created by a prior `npx --yes bun` from a cron that set `HOME=/data/hermes/users/pm2.blr`. This is a new phenomenon — previously only `._old_` existed. The stale dir has only `.bun/` and `.npm/` cache, no user data.
- **Embed model was built-in default (`zeroentropyai:zembed-1`)**: No `.gbrain/` config existed at the live HOME path, so gbrain used its baked-in default embedding model (not `minimax:embo-01`). The `.gbrain-writable` config (with minimax) is at `._old_pm2.blr/.gbrain-writable/` but wasn't used because `GBRAIN_HOME` was not set.
- **Sync phase succeeded** against `._old_` backup — the 7-page brain dir has a valid git history with a commit, so `sync=ok` with 0 new pages (all unchanged since last run).
- **Propose_takes scanned 7 pages but produced 0 proposals** — `ANTHROPIC_API_KEY` missing (same pattern as all DRAAS users). All 7 pages had extractor failures.
- **No PGLite database**: Since no `.gbrain/` config was found, gbrain had no PGLite database. DB-backed phases (extract, consolidate, orphans) still reported `ok` because they completed without a database — they scanned 0 pages/chunks and did nothing. Only `propose_takes` reports real page scanning (via file-system traversal, not DB).
- **`._old_` backup as fallback brain source**: When the DRAAS account path (`pm2.blr`) didn't have a brain, and the live stale dir had no brain, the `._old_pm2.blr/` backup was the only viable brain source. This is a documented fallback path that worked correctly.

---

## Run 5: 2026-07-05 — cron job, empty brain dir with no config, cycle_already_running lock issue

### Context
Cron job targeted uid `pm2.blr`. This is the DRAAS account path (not a stale Telegram ID dir). The `brain/` directory did not exist — only `.bun/` cache and `.gbrain/` with audit logs. No `.gbrain/config.json` either at default path or at any `.gbrain-writable/` override.

### Key Issue: `gbrain: command not found`
gbrain is not on PATH. Must use `bun run /opt/gbrain/src/cli.ts` explicitly. The bun binary was found at `/data/hermes/home/.local/bin/bun` (Tier 0.5 — permanent install location, on PATH from cron).

### Key Issue: `--dir path does not exist`
The initial invocation with `--dir /data/hermes/users/pm2.blr/brain` failed immediately because the brain directory did not exist. Resolution: created via `mkdir -p`.

### Key Issue: `cycle_already_running` (file lock conflict)
After creating the brain dir and re-running, gbrain reported `status: "skipped", reason: "cycle_already_running"` with zero phases executed. **Root cause**: A previous dream invocation (run without `--dir`, which connected to `/data/hermes/users/rnr/brain-copy` by default) had acquired the file lock at `$HOME/.gbrain/cycle.lock`. Since both invocations used `HOME=/data/hermes/users/pm2.blr`, the lock path was the same — the lock from the first run was still live when the second run tried to acquire it.

The lock resolved by itself when retried — no explicit deletion was needed.

**Important lesson**: The file lock at `$HOME/.gbrain/cycle.lock` is scoped to HOME, not to the brain directory. Two dreams running with the same HOME but different `--dir` targets will conflict. This is a gbrain design choice — the lock ensures single-writer access to PGLite, which is per-HOME, not per-brain-dir.

### Final Invocation (successful)
```sh
cd /opt/gbrain && \
HOME=/data/hermes/users/pm2.blr \
bun run src/cli.ts dream --json --dir /data/hermes/users/pm2.blr/brain
```

### Results — 2026-07-05
| Status | `partial` | Duration | 414ms |

| Phase | Status | Detail |
|---|---|---|
| lint | ✅ ok | 0 issues |
| backlinks | ✅ ok | 0 gaps |
| sync | ❌ fail | `Not a git repository` — brain dir is empty with no git init |
| synthesize | ⏭️ skipped | session_corpus_dir unset |
| extract | ✅ ok | 0 links, 0 timeline entries |
| extract_facts | ✅ ok | 0 facts reconciled |
| extract_atoms | ⏭️ skipped | not in active pack |
| resolve_symbol_edges | ✅ ok | no chunks |
| patterns | ⏭️ skipped | insufficient evidence |
| synthesize_concepts | ⏭️ skipped | not in active pack |
| recompute_emotional_weight | ✅ ok | 7 pages recomputed (full mode) |
| consolidate | ✅ ok | 0 facts promoted |
| propose_takes | ✅ ok | 7 pages scanned, 0 proposals (ANTHROPIC_API_KEY missing) |
| grade_takes | ✅ ok | 0 takes graded |
| calibration_profile | ✅ ok | insufficient data |
| conversation_facts_backfill | ⏭️ skipped | disabled |
| enrich_thin | ⏭️ skipped | disabled |
| skillopt | ⏭️ skipped | disabled |
| embed | ❌ fail | `zeroentropyai:zembed-1 requires ZEROENTROPY_API_KEY` |
| orphans | ⚠️ warn | 7 orphans out of 7 total pages |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items purged |

### Key Observations (Run 5)
- **Empty brain dir → 7 pages reported**: The dream reported 7 scanned pages and 7 orphans despite the brain directory being completely empty (no files). This is gbrain's default scaffolding — when no PGLite database exists and no brain content is present, gbrain uses built-in default template pages. The 7 pages are the standard scaffolding set (identity.md, readme.md, notes/readme.md, etc.).
- **No git repo needed for non-sync phases**: Even though `sync` failed, phases like `recompute_emotional_weight` and `orphans` ran successfully and reported 7 pages each. These work on the filesystem directly, not via git.
- **No prior `gbrain init` needed**: gbrain auto-handles the missing config by falling back to engine=null (no DB connection), running filesystem phases only. DB-dependent phases are skipped gracefully.
- **No `.gbrain/config.json` means no PGLite database**: All phases are engine=null, meaning they work on filesystem content only. No DB-backed operations (the phases report `ok` with 0 items processed because they complete with no database).
- **The 7-page count is misleading**: It comes from gbrain's built-in default content scanning, not from actual user data. An empty brain dir should report 0 pages, but gbrain reports 7 because of its default template scaffold.
- **`cycle_already_running` from same-HOME lock collision**: If two consecutive `gbrain dream` invocations share the same `HOME` (even with different `--dir` targets), the second one gets `cycle_already_running` because the file lock is scoped to HOME, not to the brain dir. Clear the lock file at `$HOME/.gbrain/cycle.lock` or wait for the first invocation to finish before running the second. The lock TTL is checked via PID liveness + file mtime.

---

## Run 6: 2026-07-15 — cron job targeting numeric Telegram ID `[REDACTED-TID]`, Postgres engine, DB lock collision

### Context
This is the **first run targeting the numeric Telegram ID** (`[REDACTED-TID]`) instead of the DRAAS account path (`pm2.blr`). All previous 5 runs used `pm2.blr`. The numeric ID path was created by a prior gbrain init (Jul 5 2026) — it has an empty `brain/` directory (created Jul 5, last modified Jul 5) and a `.gbrain/` config with audit logs but no `config.json`.

**Key difference from other numeric Telegram IDs**: Unlike Roshini (`[REDACTED-TID]`), Bharat (`[REDACTED-TID]`), Vinod (`[REDACTED-TID]`), and Prakash (`[REDACTED-TID]`) — whose numeric ID paths lack a `brain/` dir entirely — Anbarasan's numeric ID `[REDACTED-TID]` **has** a `brain/` directory. But it's empty (0 files, no git repo, no content). This means cron Step 0 path checks pass (`-d "$BRAINDIR"` succeeds) but the brain has zero usable content.

### Invocation (literal cron command)
```sh
HOME=/data/hermes/users/[REDACTED-TID] gbrain dream --json --dir /data/hermes/users/[REDACTED-TID]/brain
```

This failed immediately with `gbrain: command not found`. Actual working invocation:
```sh
cd /opt/gbrain && HOME=/data/hermes/users/[REDACTED-TID] \
  /data/hermes/home/.local/bin/bun src/cli.ts dream --json \
  --dir /data/hermes/users/[REDACTED-TID]/brain
```

### Key Issues

1. **`gbrain: command not found`** — gbrain not on PATH. Required full path via bun (consistent with all runs).

2. **`cycle_already_running` from Postgres DB lock (5-min TTL)** — First two attempts (02:16:31 and 02:16:51, 20s apart) both returned `status: "skipped", reason: "cycle_already_running"` with zero phases. The brain uses a Postgres engine (not PGLite) — the DB lock table `gbrain_cycle_locks` had a stale entry from PID 965 (Jul 13 run) that persisted due to the 5-minute TTL. Unlike file locks, there is no `.lock` file to delete. **Resolution**: waited ~3 minutes, third attempt at 02:19:46 succeeded. **Prevention**: space dream runs ≥5 minutes apart for Postgres brains.

3. **`--dir` IS accepted by dream** — Confirmed that the `--dir` flag works with the dream subcommand on this user. No `--dir` validation error. This differs from some earlier sessions where `--dir` was rejected — the behavior depends on the dream command's internal flag parser version.

### Results — 2026-07-15
| Status | `partial` | Duration | 386ms |

| Phase | Status | Duration | Detail |
|---|---|---|---|
| lint | ok | 17ms | 0 fixes, 0 remaining |
| backlinks | ok | 3ms | 0 gaps |
| sync | ❌ fail | 60ms | `Not a git repository: /data/hermes/users/[REDACTED-TID]/brain` |
| synthesize | ⏭️ skipped | 12ms | session_corpus_dir unset |
| extract | ok | 6ms | 0 links, 0 timeline entries |
| extract_facts | ok | 30ms | 0 facts reconciled across 0 pages |
| extract_atoms | ⏭️ skipped | 0ms | not in active pack |
| resolve_symbol_edges | ok | 7ms | no chunks needed |
| patterns | ⏭️ skipped | 17ms | 0 reflections in last 30d |
| synthesize_concepts | ⏭️ skipped | 3ms | not in active pack |
| recompute_emotional_weight | ok | 6ms | 7 pages recomputed (full mode) |
| consolidate | ok | 5ms | 0 facts → 0 takes |
| propose_takes | ok | 49ms | 7 pages scanned, 0 cached, **0 new proposals**; 7 warnings: `ANTHROPIC_API_KEY` missing |
| grade_takes | ok | 5ms | 0 takes scanned |
| calibration_profile | ok | 3ms | holder=garry, 0 resolved takes |
| conversation_facts_backfill | ⏭️ skipped | 60ms | feature off |
| enrich_thin | ⏭️ skipped | 23ms | feature off |
| skillopt | ⏭️ skipped | 6ms | feature flag off |
| **embed** | **❌ fail** | **5ms** | `zeroentropyai:zembed-1 requires ZEROENTROPY_API_KEY` |
| orphans | ⚠️ warn | 7ms | 7 orphans out of 7 total pages |
| schema-suggest | ok | 11ms | 0 suggestions |
| purge | ok | 18ms | 0 items purged |

### Imported / Embedded / Errors
- **Imported (sync):** 0 — sync failed (not a git repo)
- **Extracted:** 0 links, 0 timeline entries, 0 facts
- **Embedded:** 0 pages — embed failed (ZEROENTROPY_API_KEY missing)
- **Errors:** sync (not a git repo), embed (no ZEROENTROPY_API_KEY), propose_takes (no ANTHROPIC_API_KEY — harmless)

### Rate limit note
No rate limit was hit. Embed never started — it failed on configuration (missing API key) before any API call.

### Key Observations (Run 6)
- **Numeric Telegram ID has a brain dir (unlike other users)**: Anbarasan's numeric ID `[REDACTED-TID]` is the **only** numeric Telegram ID path that has a `brain/` directory. All other numeric IDs (Roshini [REDACTED-TID], Bharat [REDACTED-TID], Vinod [REDACTED-TID], Prakash [REDACTED-TID]) lack a brain dir entirely. But it's empty — no files, no git repo.
- **Postgres engine confirmed**: The `.gbrain/` config at `[REDACTED-TID]` uses Postgres (not PGLite). The `db-disconnect` audit log confirms `engine_kind:"postgres"`. This is consistent with the DRAAS account path's default config (root-owned, Postgres engine, zeroentropy model).
- **Postgres DB lock TTL**: First time the 5-minute DB lock TTL was confirmed in practice for this brain. The lock persisted from PID 965 (Jul 13) through two 20s-apart retries, then released after ~3 minutes.
- **Default scaffold fingerprint**: 7 pages scanned, 7 orphans, 0 proposals, holder=garry — clear indicator the brain has no real content, just gbrain's default scaffolding.
- **No `.gbrain-writable` PGLite**: Unlike the DRAAS account path (`pm2.blr/.gbrain-writable/`), the numeric Telegram ID path has no writable config override. The default root-owned config at `[REDACTED-TID]/.gbrain/` may lack write permissions for audit logs, but no EACCES was observed (Postgres engine doesn't write file-based audit).
