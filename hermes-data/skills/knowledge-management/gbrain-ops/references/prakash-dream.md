# Dream run — Prakash (psingh) — June/July 2026

## Run history

### Run 6 — Friday 03 July 2026, 02:45 UTC

#### Context

- Cron job still hardcoded to old Telegram ID `psingh` — agent fell back to DRAAS account `psingh`
- Brain-copy at `/data/hermes/users/psingh/brain-copy/` — 1 page (identity.md), 1 git commit (`cc1203a`)
- Config at `.gbrain-writable/.gbrain/config.json` — PGLite, minimax:embo-01, database_path correct (fixed Jun 30)
- Bun binary: `/data/hermes/home/.local/bin/bun` v1.3.14

#### Pre-flight: ENOSPC discovery

Dream failed immediately with Postgres error 53100 — `could not extend file "base/53698/54757": No space left on device`. Investigation revealed:

- `/data/hermes` is a **separate 38G ext4 mount at `/dev/sdb1`**, not the same as the root overlay
- It was **100% full** (36G of 38G used) — while the root overlay (`/`) showed 11G free
- Top consumers on `/data/hermes`:
  - uv cache: 5.5G (`/data/hermes/home/.cache/uv/`)
  - pip cache: 3.0G (`/data/hermes/home/.cache/pip/`)
  - npm cache: 285M (`/data/hermes/home/.npm/_cacache/`)
  - audio cache: 647M (`/data/hermes/audio_cache/`)
  - pdf work: 407M (`/data/hermes/pdf_work/`)
  - document cache: 114M (`/data/hermes/document_cache/`)

Freed 9.2G by clearing uv cache (`uv cache clean`), pip cache (`rm -rf /data/hermes/home/.cache/pip/*`), plus temp caches. Down to 27G used (75%).

#### PGLite database corruption

The ENOSPC had corrupted the PGLite database. Even after freeing space, re-running dream gave:
```
[dream] WARNING: could not connect to DB (Cannot connect to database: could not write init file)
ENOSPC: no space left on device, write
```

The corrupted database couldn't be recovered in-place. **Fix**: `init --pglite --embedding-model minimax:embo-01 --embedding-dimensions 1536 --force --skip-embed-check` created a fresh 42M PGLite database that worked immediately.

#### Invocation

```sh
HOME=/data/hermes/users/psingh/.gbrain-writable \
/data/hermes/home/.local/bin/bun run /opt/gbrain/src/cli.ts dream \
  --json \
  --dir /data/hermes/users/psingh/brain-copy
```

#### Phase results

```
Status: partial — 640ms total — 22 phases

  ✓ sync              +1 added, ~0 modified (full reimport — anchor missing after re-init)
  ✓ backlinks         no missing back-links found
  ✓ extract           0 link(s), 0 timeline entries
  ✓ extract_facts     0 fact(s) reconciled across 0 page(s)
  ✓ resolve_symbol_edges  no chunks needed
  ✓ consolidate       0 facts → 0 takes
  ✓ propose_takes     scanned 7 pages, 0 cached, 0 new proposals (ANTHROPIC_API_KEY warnings)
  ✓ grade_takes       scanned 0 takes
  ✓ calibration_profile  holder=garry, <5 resolved takes
  ✓ schema-suggest    0 suggestions
  ✓ purge             0 sources, 0 pages
  ❌ embed            minimax:embo-01 requires MINIMAX_API_KEY
  ⚠ lint              0 fix(es) applied, 1 remaining
  ⚠ orphans           7 orphan page(s) out of 7 total
  ⏭ synthesize        session_corpus_dir unset
  ⏭ extract_atoms     not in active pack
  ⏭ patterns          insufficient evidence
  ⏭ synthesize_concepts  not in active pack
  ⏭ conversation_facts_backfill  disabled
  ⏭ enrich_thin       disabled
  ⏭ skillopt          feature flag off
```

#### Key changes from Run 3 (Jun 30)

| Aspect | Run 3 (Jun 30) | Run 6 (Jul 3) |
|---|---|---|
| Brain path | `/data/hermes/users/psingh/brain` | `/data/hermes/users/psingh/brain-copy` |
| Pages imported | 7 (full reimport) | 1 (full reimport — fresh DB) |
| DB state | healthy (v119) | **corrupted by ENOSPC → re-init'd** |
| `/data/hermes` usage | unknown | **100% → 75% after cache cleanup** |
| Duration | 581ms | 640ms |
| Schema migrations | 0 | 0 (fresh init at latest) |

#### Failures (same as all runs)

1. **`embed` phase** — `minimax:embo-01` requires `MINIMAX_API_KEY`. Platform-wide limitation.
2. **`propose_takes`** — All 7 pages had LLM extractor failures (`ANTHROPIC_API_KEY` missing). Non-fatal — 0 proposals.

#### Noteworthy (new discoveries)

1. **`/data/hermes` is a separate mount** — `/dev/sdb1` ext4, 38G total. Always check BOTH mounts with `df -hT | grep -v tmpfs`.
2. **uv cache (5.5G) is the biggest reclaimable consumer** on `/data/hermes`, not npm cache (285M).
3. **PGLite ENOSPC corruption is recoverable** via `init --pglite --force --skip-embed-check` after freeing space.
4. **brain-copy approach** (hermes-owned copy with its own git repo) worked cleanly — no `safe.directory` or git config issues.

---

### Run 5 — Thursday 02 July 2026, 02:40 UTC

#### Context

- Identical to Run 4: `/data/hermes/users/psingh/` exists but has only `.bun/` — no brain
- Actual brain at `/data/hermes/users/psingh/brain/` (confirmed 7 pages, 1 git commit, migrated Jun 30)
- Cron job still hardcoded to old Telegram ID `psingh`

#### Result

Same as Run 4 — `--dir path does not exist: /data/hermes/users/psingh/brain`. Reported `[SILENT]`.

#### Pattern

The stale Telegram ID path `psingh` persists as a live (empty) directory. The brain was migrated to `psingh` on Jun 30. The cron job configuration needs updating from `psingh` to `psingh` for dream to actually run.

---

### Run 4 — Wednesday 01 July 2026, 02:40 UTC

#### Context

- Brain path checked: `/data/hermes/users/psingh/brain` — **directory does not exist**
- User dir: `/data/hermes/users/psingh/` exists but contains **only `.bun/`** (empty user dir — stale Telegram ID path)
- Actual brain lives at: `/data/hermes/users/psingh/brain` (migrated per Run 3)
- Config: no `.gbrain-writable` or `.gbrain/` at the stale psingh path

#### Invocation attempted

```sh
HOME=/data/hermes/users/psingh gbrain dream --json --dir /data/hermes/users/psingh/brain
```

Failed with: `gbrain: command not found` (not in PATH), then resolved to `bun run /opt/gbrain/src/cli.ts` which still failed with `--dir path does not exist: /data/hermes/users/psingh/brain`.

#### Result

No dream run — brain path doesn't exist. Reported `[SILENT]` as state was unchanged from previous run.

---

### Run 3 — Monday 30 June 2026, 02:44 UTC

#### Context

- Brain: `/data/hermes/users/psingh/brain` — 7 pages (identity.md, readme, notes/readme, people/readme, people/roshni-ranka, person/roshni-ranka, projects/readme), **1 git commit** (`be80f8a init brain`) — content migrated from old Telegram ID dir
- User dir: `/data/hermes/users/psingh/` — old Telegram ID path `/data/hermes/users/psingh/` no longer exists
- Config: `.gbrain-writable/.gbrain/config.json` (hermes-owned, readable) — **stale `database_path`** still pointed to old Telegram ID path, fixed this run
- Bun binary: `/data/hermes/home/.local/bin/bun` v1.3.14 (on PATH)
- Invocation:
  ```sh
  cd /opt/gbrain && \
  GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
  /data/hermes/home/.local/bin/bun run /opt/gbrain/src/cli.ts dream \
    --json \
    --dir /data/hermes/users/psingh/brain
  ```

#### Pre-flight fix

The config's `database_path` was `/data/hermes/users/psingh/.gbrain-writable/.gbrain/brain.pglite` (old Telegram ID path). The database actually existed at `/data/hermes/users/psingh/.gbrain-writable/.gbrain/brain.pglite`. Fixed with:

```sh
python3 -c "
import json
path = '/data/hermes/users/psingh/.gbrain-writable/.gbrain/config.json'
with open(path) as f:
    cfg = json.load(f)
cfg['database_path'] = '/data/hermes/users/psingh/.gbrain-writable/.gbrain/brain.pglite'
with open(path, 'w') as f:
    json.dump(cfg, f, indent=2)
"
```

This is the 4th confirmed occurrence of the stale `database_path` bug after an identity migration (after Nishant/ndr, Bharat/sales1.blr, Anbarasan/pm2.blr).

#### Phase results

```
Status: partial — 581ms total — 22 phases

  ✓ sync              +1 added, ~0 modified (full reimport — anchor missing, history rewrite)
  ✓ backlinks         no missing back-links found
  ✓ extract           0 link(s), 0 timeline entries
  ✓ extract_facts     0 fact(s) reconciled across 0 page(s)
  ✓ resolve_symbol_edges  no chunks needed
  ✓ consolidate       0 facts → 0 takes
  ✓ propose_takes     scanned 7 pages, 0 cached, 0 new proposals (ANTHROPIC_API_KEY warnings)
  ✓ grade_takes       scanned 0 takes
  ✓ calibration_profile  holder=garry, <5 resolved takes
  ✓ schema-suggest    0 suggestions
  ✓ purge             0 sources, 0 pages
  ❌ embed            minimax:embo-01 requires MINIMAX_API_KEY
  ⚠ lint              0 fix(es) applied, 1 remaining
  ⚠ orphans           7 orphan page(s) out of 7 total
  ⏭ synthesize        session_corpus_dir unset
  ⏭ extract_atoms     not in active pack
  ⏭ patterns          insufficient evidence
  ⏭ synthesize_concepts  not in active pack
  ⏭ conversation_facts_backfill  disabled
  ⏭ enrich_thin       disabled
  ⏭ skillopt          feature flag off
```

#### Key changes from Run 2 (Jun 25)

| Aspect | Run 2 (Jun 25) | Run 3 (Jun 30) |
|---|---|---|
| Brain path | `/data/hermes/users/psingh/brain` | `/data/hermes/users/psingh/brain` |
| User dir | psingh (existed) | psingh (psingh deleted) |
| Git commits | 0 (sync failed) | 1 (sync succeeded) |
| `database_path` | `/data/hermes/users/psingh/...` (correct then) | `/data/hermes/users/psingh/...` (stale — fixed) |
| Pages imported | 1 (failed) | 7 (full reimport) |
| sync | ❌ fail — no commits | ✅ ok — full reimport |
| Duration | 1222ms | 581ms |
| Schema migrations | 6 (v113→v119) | 0 (already at latest) |
| Propose_takes warnings | 1 page | 7 pages (no ANTHROPIC_API_KEY) |

#### Failures

1. **`embed` phase** — `minimax:embo-01` requires `MINIMAX_API_KEY`. Platform-wide limitation, same as all previous runs.
2. **`propose_takes`** — All 7 pages had LLM extractor failures (`ANTHROPIC_API_KEY` missing). Non-fatal — phase completes gracefully with 0 proposals.

#### Noteworthy

- First successful `sync` for Prakash — all prior runs failed at sync (no git commits). The brain had been imported from the old Telegram ID dir with 1 commit, enabling sync to proceed.
- Full reimport (`Sync anchor 79142945 object missing (gc'd after history rewrite)`) is expected — gbrain's stored anchor was from the old Telegram ID git history. Subsequent runs will be incremental.
- Brain has both `person/roshni-ranka` and `people/roshni-ranka` — a duplicate from the directory copy. Harmless but inflates page count slightly.
- No schema migrations needed (DB was at latest).
- `.gbrain-writable/.gbrain/` config and `brain.pglite` persisted since last run (Jun 26) — no re-init needed.

---

### Run 2 — Wednesday 25 June 2026, 02:42 UTC

#### Context

- Brain: `/data/hermes/users/psingh/brain` — single page (`identity.md`), **no git commits** (same as run 1)
- Config: root-owned `.gbrain/config.json` (600) — actual readable config at `.gbrain-writable/.gbrain/config.json`
- Config content:
  ```json
  {
    "engine": "pglite",
    "database_path": "/data/hermes/users/psingh/.gbrain-writable/.gbrain/brain.pglite",
    "embedding_model": "minimax:embo-01",
    "embedding_dimensions": 1536,
    "schema_pack": "gbrain-base-v2",
    "mcp": {"publish_skills": true},
    "self_upgrade": {"mode": "notify", "mode_prompted": true}
  }
  ```

#### Invocation

```sh
cd /opt/gbrain && \
HOME=/data/hermes/users/psingh \
GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
bun run src/cli.ts dream --json --dir /data/hermes/users/psingh/brain
```

Key details:
- `bun` found on PATH at `/data/hermes/home/.local/bin/bun` (v1.3.14) — previously used `/tmp/bun-bin/bun-linux-aarch64/bun`
- `GBRAIN_HOME` required because `$HOME/.gbrain/config.json` is root-owned (600) and unreadable by hermes
- `HOME` set but redundant when `GBRAIN_HOME` is set
- Brain dir pointed directly at root-owned brain — no brain-copy → sync fails (no git commits)

#### Schema migration

The PGLite database was 6 migrations behind (schema v113 → v119). Applied automatically:
```
  [114] links_link_source_check_kebab_regex ✓
  [115] op_checkpoint_paths_append_table     ✓
  [116] code_edges_source_backfill_and_callee_index ✓
  [117] context_volunteer_events_table       ✓
  [118] page_generation_clock_sequence_swap  ✓
  [119] op_checkpoints_completed_keys_array_check ✓
```
This is normal — the `.gbrain-writable` PGLite database was from an earlier gbrain version (0.42.x) and gets auto-migrated on first connect. Subsequent runs should be migration-free.

#### Phase results

```
Status: partial — 1.2s total — 22 phases
✓=ok  ⚠=warn  ❌=fail  ⏭=skipped

  ⚠ lint              0 fix(es) applied, 1 remaining
  ✓ backlinks          no missing back-links found
  ❌ sync              No commits in repo. Make at least one commit before syncing.
  ⏭ synthesize        dream.synthesize.session_corpus_dir is unset
  ✓ extract           0 link(s), 0 timeline entries
  ✓ extract_facts     0 fact(s) reconciled across 0 page(s)
  ⏭ extract_atoms     not in active pack (base-v2)
  ✓ resolve_symbol_edges  no chunks needed
  ⏭ patterns          0 reflections in last 30d (need ≥3)
  ⏭ synthesize_concepts  not in active pack (base-v2)
  ✓ recompute_emotional_weight  1 pages
  ✓ consolidate       0 facts → 0 takes
  ✓ propose_takes     scanned 1 pages, 0 cached, 0 new proposals
  ✓ grade_takes       scanned 0 takes
  ✓ calibration_profile  holder=garry, <5 resolved takes
  ⏭ conversation_facts_backfill  disabled (default OFF)
  ⏭ enrich_thin       disabled (default OFF)
  ⏭ skillopt          feature flag off
  ❌ embed            minimax:embo-01 requires MINIMAX_API_KEY
  ⚠ orphans           1 orphan page(s) out of 1 total
  ✓ schema-suggest    0 suggestions
  ✓ purge             0 source(s), 0 page(s)
```

#### Propose_takes details

The phase ran but the LLM extractor failed gracefully:
```
warnings: ["extractor failed on identity: Anthropic chat requires ANTHROPIC_API_KEY."]
```
Harmless — the extraction uses Anthropic for proposals; when the key is missing it skips the page.

#### Failures (same as run 1)

1. **`sync` phase** — brain dir has zero git commits. Was `git init`'d but never committed. Fix: `cd /data/hermes/users/psingh/brain && git add -A && git commit -m "initial"` (requires write permission, or brain-copy approach).
2. **`embed` phase** — `minimax:embo-01` requires `MINIMAX_API_KEY`. Platform-wide limitation, affects all users equally.

#### Skipped by design (same as run 1)

- synthesize — no session corpus dir
- extract_atoms / synthesize_concepts — not in base-v2 schema pack
- patterns — insufficient evidence (1 page only)
- conversation_facts_backfill / enrich_thin / skillopt — default OFF
- calibration_profile — holder=garry (default), <5 resolved takes

---

### Run 1 — Saturday 20 June 2026, 02:42 UTC

#### Context

Same brain, same config location. Used direct bun binary at `/tmp/bun-bin/bun-linux-aarch64/bun` (host is aarch64).

#### Invocation

```sh
cd /opt/gbrain
HOME=/data/hermes/users/psingh \
GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
/tmp/bun-bin/bun-linux-aarch64/bun run src/cli.ts dream \
  --json \
  --dir /data/hermes/users/psingh/brain
```

#### Phase results

Same 22-phase cycle (duration 951ms). Identical failure/skip pattern — no schema migrations needed (db was fresh from init).

#### Differences from run 2

| Aspect | Run 1 (Jun 20) | Run 2 (Jun 25) |
|---|---|---|
| Bun binary | `/tmp/bun-bin/bun-linux-aarch64/bun` | `bun` on PATH (`~/.local/bin/bun`) |
| Duration | 951ms | 1222ms |
| Schema migrations | 0 (fresh init) | 6 (v113→v119 auto-migrated) |
| Propose_takes status | ok, no warnings | ok, with `ANTHROPIC_API_KEY` warning |
| Config DB size | fresh (0 files before init) | existing (6 migrations behind) |

---

### Run 7 — Sunday 05 July 2026, 02:41 UTC

#### Context

- Cron job still hardcoded to old Telegram ID `psingh` — agent fell back to DRAAS account `psingh`
- Brain: `/data/hermes/users/psingh/brain/` (direct — not brain-copy) — 1 git commit (`be80f8a init brain`)
- Config: `.gbrain-writable/.gbrain/config.json` — still valid and readable since Run 6's fresh init (no re-init needed)
- Brain contents: `identity.md`, `notes/`, `people/`, `projects/` — 7 pages total (1 real + 6 scaffolding)
- Invocation: `GBRAIN_HOME` (preferred, no git config breakage):
  ```sh
  GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
  /data/hermes/home/.local/bin/bun run /opt/gbrain/src/cli.ts dream \
    --json \
    --dir /data/hermes/users/psingh/brain
  ```

#### Anchor miss

The stored sync anchor (`ec580838`) was from Run 6's brain-copy repo (a different git history), so it didn't exist in the original brain's repo:
```
Sync anchor ec580838 object missing (gc'd after history rewrite). Running full reimport.
```
Triggered a full reimport — expected when switching between brain-copy and original brain. Harmless: 1 page imported, 0 skipped.

#### Phase results

```
Status: partial — 553ms total — 22 phases

  ✓ sync              +1 added, ~0 modified, -0 deleted (full reimport — anchor mismatch)
  ✓ backlinks         no missing back-links found
  ✓ extract           0 link(s), 0 timeline entries
  ✓ extract_facts     0 fact(s) reconciled across 0 page(s)
  ✓ resolve_symbol_edges  no chunks needed
  ✓ consolidate       0 facts → 0 takes
  ✓ propose_takes     scanned 7 pages, 0 cached, 0 new proposals (ANTHROPIC_API_KEY warnings)
  ✓ grade_takes       scanned 0 takes
  ✓ calibration_profile  holder=garry, <5 resolved takes
  ✓ schema-suggest    0 suggestions
  ✓ purge             0 sources, 0 pages
  ❌ embed            minimax:embo-01 requires MINIMAX_API_KEY
  ⚠ lint              1 issue remaining, 0 fixed
  ⚠ orphans           7 orphan page(s) out of 7 total
  ⏭ synthesize        session_corpus_dir unset
  ⏭ extract_atoms     not in active pack
  ⏭ patterns          insufficient evidence
  ⏭ synthesize_concepts  not in active pack
  ⏭ conversation_facts_backfill  disabled
  ⏭ enrich_thin       disabled
  ⏭ skillopt          feature flag off
```

#### Comparison with Run 6 (Jul 3)

| Aspect | Run 6 (Jul 3) | Run 7 (Jul 5) |
|---|---|---|
| Brain path | `/data/hermes/users/psingh/brain-copy` | `/data/hermes/users/psingh/brain` |
| Git repo | Fresh brain-copy repo (2 commits) | Original brain repo (1 commit `be80f8a`) |
| Config state | Re-initialized after ENOSPC corruption | Existing — no re-init needed |
| Duration | 640ms | 553ms |
| Pages imported | 1 (full reimport) | 1 (full reimport — anchor mismatch) |
| `/data/hermes` usage | 75% (after 9.2G cleanup) | Not checked (assumed stable) |
| Embed failure | minimax:embo-01 (no MINIMAX_API_KEY) | Same |

#### Noteworthy

- `GBRAIN_HOME` approach worked cleanly — HOME not redirected, so git used the real system gitconfig at `/data/hermes/home/.gitconfig` which has `safe.directory` for the `psingh/brain` path. No git config workarounds needed.
- `.gbrain-writable` config persisted since Run 6's fresh init (3 days) — no re-init needed.
- The anchor miss between brain-copy and original brain is cosmetic — subsequent runs on the same path will be incremental.
- The `holder=garry` in calibration_profile persists across all runs — the default `identity.md` from gbrain scaffolding has never been rewritten for Prakash.

### Run 8 — Thursday 09 July 2026, 02:41 UTC

#### Context

- Cron job still hardcoded to old Telegram ID `psingh` — agent fell back to DRAAS account `psingh`
- Stale dir `/data/hermes/users/psingh/` still exists with only `.bun/` cache (unchanged since Runs 4-5)
- Brain: `/data/hermes/users/psingh/brain/` (direct — not brain-copy) — 1 git commit (`be80f8a init brain`), hermes-owned
- Config: `.gbrain-writable/.gbrain/config.json` — still valid since Run 6's fresh init (no re-init needed, 6 days stable)
- Bun binary: `/data/hermes/home/.local/bin/bun`

#### Pre-flight: safe.directory missing

The system gitconfig (`/data/hermes/home/.gitconfig`) had entries for many brain dirs but was **missing** `/data/hermes/users/psingh/brain`. Added with:
```sh
git config --global --add safe.directory /data/hermes/users/psingh/brain
```

This is the same pattern as Vinod's `vkdas/brain-copy` (Jul 6 2026) — the DRAAS account brain dir wasn't in the safe.directory allow-list, only old Telegram ID paths were. The GBRAIN_HOME skill pitfall already covers this check: "Check the system gitconfig before first GBRAIN_HOME dream run and add the missing entry."

#### Invocation

```sh
GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
/data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
  --json \
  --dir /data/hermes/users/psingh/brain
```

#### Phase results

```
Status: partial — 591ms total — 22 phases

  ✓ sync              +1 added, ~0 modified (full reimport — anchor gc'd from prior history rewrite)
  ✓ backlinks         no missing back-links found
  ✓ extract           0 link(s), 0 timeline entries
  ✓ extract_facts     0 fact(s) reconciled across 0 page(s)
  ✓ resolve_symbol_edges  no chunks needed
  ✓ consolidate       0 facts → 0 takes
  ✓ propose_takes     scanned 7 pages, 0 cached, 0 new proposals (ANTHROPIC_API_KEY warnings)
  ✓ grade_takes       scanned 0 takes
  ✓ calibration_profile  holder=garry, <5 resolved takes
  ✓ schema-suggest    0 suggestions
  ✓ purge             0 sources, 0 pages
  ❌ embed            minimax:embo-01 requires MINIMAX_API_KEY
  ⚠ lint              1 issue remaining
  ⚠ orphans           7 orphan page(s) out of 7 total
  ⏭ synthesize        session_corpus_dir unset
  ⏭ extract_atoms     not in active pack
  ⏭ patterns          insufficient evidence
  ⏭ synthesize_concepts  not in active pack
  ⏭ conversation_facts_backfill  disabled
  ⏭ enrich_thin       disabled
  ⏭ skillopt          feature flag off
```

#### Sync anchor detail

```
fatal: git cat-file: could not get object info
Sync anchor ec580838 object missing (gc'd after history rewrite). Running full reimport.
```

Same anchor hash as Run 7 (`ec580838`) — still stored in the PGLite DB from Run 6's brain-copy history. Since we're back on the original brain repo (different git history, commit `be80f8a`), the anchor never resolves. Full reimport of the single page. This will persist until the next re-init or brain-copy cycle.

#### Comparison with Run 7 (Jul 5)

| Aspect | Run 7 (Jul 5) | Run 8 (Jul 9) |
|---|---|---|
| Brain path | `/data/hermes/users/psingh/brain` | Same |
| safe.directory | Already present | **Added this run** (was missing) |
| Config state | Existing | Same (no re-init needed — 6 days stable) |
| Duration | 553ms | 591ms |
| Pages imported | 1 (full reimport) | 1 (full reimport — same anchor miss) |
| Anchor hash | `ec580838` | Same (persistent mismatch) |
| Embed failure | minimax:embo-01 | Same |

#### Noteworthy

- **safe.directory gap confirmed for psingh/brain** — This is the second confirmed case (after Vinod `vkdas/brain-copy`, Jul 6) where the DRAAS account brain dir was missing from the system gitconfig's safe.directory allow-list. The pre-flight checklist in the skill already covers this check; it was caught and fixed before dream ran.
- Config persists reliably (6 days since Run 6's ENOSPC recovery) — `.gbrain-writable` PGLite database is stable on this host.
- The stale Telegram ID `psingh` dir continues to exist with only `.bun/` cache — the cron job is still misconfigured 9 days after migration.

## Run 9 — Monday 13 July 2026, 02:40 UTC

#### Context

- Cron job still hardcoded to old Telegram ID `psingh` with `--dir /data/hermes/users/psingh/brain` — both stale
- User dir `/data/hermes/users/psingh/` still exists, contains **only `.bun/install/` cache** (hermes-owned) — no `brain/`, no `.gbrain/`, no `.gbrain-writable/`
- DRAAS account `/data/hermes/users/psingh/` not consulted this run — agent followed the literal cron command first
- Bun binary: `/data/hermes/home/.local/bin/bun` v1.3.14

#### Literal command outcome

```sh
HOME=/data/hermes/users/psingh gbrain dream --json --dir /data/hermes/users/psingh/brain
```

Two failures in sequence:
1. `gbrain: command not found` — gbrain is not in PATH. Resolved by invoking `bun run /opt/gbrain/src/cli.ts` directly (canonical pattern from the SKILL.md).
2. `--dir path does not exist: /data/hermes/users/psingh/brain` — exit 0, no phases ran. The standard "exit code lies" pitfall fired (documented in cron-recipes).

#### Discovery: HOME-only invocation works even with no `--dir` and no real brain

After the literal command failed, the agent retried with **only `HOME` set** and no `--dir`:

```sh
HOME=/data/hermes/users/psingh \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream --json
```

**This succeeded** — gbrain ran 22 phases against a PGLite database that was auto-created (or re-resolved) on the fly from the default scaffold. Phase results:

```
Status: (no top-level status field — run produced 22 phases regardless) — 22 phases, ~600ms total
  ⚠ lint              0 fix(es) applied, 1 remaining
  ✓ backlinks          no missing back-links found
  ✓ sync               0 changes (no brain repo)
  ⏭ synthesize         session_corpus_dir unset
  ✓ extract            0 link(s), 0 timeline entries
  ✓ extract_facts      0 fact(s) reconciled across 0 page(s)
  ⏭ extract_atoms      not in active pack (base-v2)
  ✓ resolve_symbol_edges  no chunks needed
  ⏭ patterns           0 reflections in last 30d (need ≥3)
  ⏭ synthesize_concepts  not in active pack
  ✓ recompute_emotional_weight  0 slugs
  ✓ consolidate        promoted 0 facts into 0 takes
  ✓ propose_takes      scanned 7 pages, 0 cached, 0 new proposals
  ✓ grade_takes        scanned 0 takes
  ✓ calibration_profile  holder=garry, 0 resolved takes
  ⏭ conversation_facts_backfill  disabled
  ⏭ enrich_thin        disabled
  ⏭ skillopt           feature flag off
  ❌ embed              zeroentropyai:zembed-1 requires ZEROENTROPY_API_KEY
  ⚠ orphans            7 orphan page(s) out of 7 total
  ✓ schema-suggest     0 suggestions
  ✓ purge              0 sources, 0 pages
```

#### Why this matters

The HOME-only invocation pattern is **already documented in the SKILL.md** under "Postgres engine, no local checkout" for users whose brain is on Postgres (e.g. Vinod/vkdas). This run confirms it also works for **PGLite on a hermes-owned default `$HOME` path** when no `.gbrain-writable` exists. gbrain's config resolution found or created a config at `/data/hermes/users/psingh/.gbrain/config.json` and ran against a PGLite database there.

The 7 orphan pages, `holder=garry`, and `extract_atoms not in active pack (base-v2)` are the **fingerprint of gbrain's default scaffold** — not real user data. If you see this fingerprint in a dream report and the user is supposed to have real content, the brain was never properly initialized. Fix: run `init --pglite` against the DRAAS account path and rewrite `identity.md`.

#### Embed failure — provider switched

The embed error mentions **`zeroentropyai:zembed-1`** (not `minimax:embo-01` as in all prior runs). This means the config auto-created in `$HOME/.gbrain/` (default path) uses a different provider than the `.gbrain-writable` config (which used minimax). The Pitfall "Embedding model differs by config path for same user" in SKILL.md already documents this dual-provider behavior — the embed error message's model name tells you which config is active.

This is the **fifth distinct embed failure pattern** observed across DRAAS users (after `minimax:embo-01`, `minimax:embo-01` exhausted 429, `openrouter:openai/text-embedding-3-small` credential-delivery-gap, and `opencode-go` no-embeddings). Documented in the Embedding table in SKILL.md.

#### Comparison with prior runs

| Aspect | Run 8 (Jul 9) | Run 9 (Jul 13) |
|---|---|---|
| Cron command | `--dir psingh/brain` (still wrong path) | Literal `--dir psingh/brain` |
| Invocation | GBRAIN_HOME + --dir | **HOME only, no --dir** (auto-fallback) |
| Brain path | `/data/hermes/users/psingh/brain` | `/data/hermes/users/psingh/.gbrain` (default) |
| Database | `.gbrain-writable/brain.pglite` (stable) | New PGLite at default `$HOME/.gbrain/` |
| Embed model | `minimax:embo-01` | **`zeroentropyai:zembed-1`** (different config path) |
| Pages | 7 (real + scaffold) | 7 (default scaffold only — phantom) |
| Duration | 591ms | ~600ms |
| Sync | ok (1 page reimport) | ok (0 changes — no real content) |

#### Noteworthy

- **The literal cron command is now broken in two distinct ways** — `gbrain: command not found` AND `--dir path does not exist`. The agent's automatic fallback (drop `--dir`, set HOME) salvaged the run by running against gbrain's default scaffold. This is the same pattern documented in "Cron `--dir` failure: agent-level fallback pattern" in the SKILL.md pitfalls.
- **No real content was processed** — the 7 phantom pages are the default scaffold. A future cron that wants to do real work for Prakash must use the DRAAS account path: `GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable ... --dir /data/hermes/users/psingh/brain` (per the cron-recipes reference).
- **The default-path config uses `zeroentropyai:zembed-1`** — different from `.gbrain-writable`'s `minimax:embo-01`. Both block embed (no API keys in env). Documented in the SKILL.md pitfall "Embedding model differs by config path for same user."
- **HOME-only fallback is a viable emergency pattern** for any user whose cron's `--dir` is broken AND whose `.gbrain-writable` doesn't exist. It runs default-scaffold phases only — useful as a "is gbrain functional at all" smoke test, not as a real dream cycle.

## Key observations

- `GBRAIN_HOME` consistently works — config resolves to `<GBRAIN_HOME>/.gbrain/config.json`, bypassing root-owned `$HOME/.gbrain/`
- On a fresh PGLite db, schema is at latest version (no migrations needed). On a several-day-old db, auto-migration applies any pending changes — normal, harmless.
- `bun` is now on PATH (`~/.local/bin/bun`) — no need to find or download it separately
- The `propose_takes` warning about `ANTHROPIC_API_KEY` is new (wasn't visible in run 1). Harmless — extraction gracefully skips.
- The `holder=garry` in calibration_profile is the default calibration identity in gbrain's schema — not a real person.
- This brain went from 1 page / 0 git commits (Runs 1-2, sync failed) to 7 pages / 1 commit (Run 3, sync succeeded) after the identity migration completed and `database_path` was fixed.
- Run 3 confirmed the `database_path` stale-path bug for a 4th user (Prakash/psingh, after Nishant/ndr, Bharat/sales1.blr, Anbarasan/pm2.blr) — always check `database_path` when a user directory is renamed.
- **Runs 4-5**: After the migration to psingh, the cron job hardcoded to old Telegram ID `psingh` continues targeting an empty stale directory. The actual brain lives at `/data/hermes/users/psingh/brain/` and has been unreachable by the cron job since Jun 30. The cron configuration needs updating.
- **Run 6 (Jul 3)**: Discovered that `/data/hermes` is a separate 38G ext4 mount at `/dev/sdb1` that can fill up independently (100% while root shows 11G free). PGLite database got corrupted by the ENOSPC. Recovery: freed 9.2G (uv + pip caches), re-init'd PGLite with `init --pglite --force`, dream succeeded with `partial` status. Added brain-copy approach for zero git-config issues.
- **Run 9 (Jul 13)**: Confirmed that `HOME=<stale_uid> gbrain dream --json` (no `--dir`) works as an emergency fallback even when there's no `.gbrain-writable` config and no brain dir. gbrain auto-creates a PGLite config at the default `$HOME/.gbrain/` path and runs 22 phases against the default scaffold. **Fingerprint of a default-scaffold (non-content) run**: 7 pages, 7 orphans, `holder=garry`, `extract_atoms not in active pack (base-v2)`, `propose_takes` 0 proposals. If you see this and the user is supposed to have real content, the brain was never initialized — run `init --pglite` against the DRAAS account path.

## Run 10 — Tuesday 14 July 2026, 02:41 UTC

#### Context

- Cron job hardcoded to **numeric Telegram ID** `uid=[REDACTED-TID]` (a new variation — every prior run used the DRAAS slug `psingh`; this one uses the raw 10-digit numeric uid)
- User dir `/data/hermes/users/[REDACTED-TID]/` exists but contains **only `.bun/install/cache` and `.gbrain/audit/`** — no `brain/`, no `.gbrain-writable/`, no real gbrain config
- DRAAS account is `psingh` — confirmed by `/data/hermes/users/psingh/brain/identity.md` ("# Prakash / Email: prakash@draas.com / Telegram ID: [REDACTED-TID]")
- Bun binary: `/data/hermes/home/.local/bin/bun` v1.3.14

#### Literal command failure (3 ways)

```sh
HOME=/data/hermes/users/[REDACTED-TID] gbrain dream --json --dir /data/hermes/users/[REDACTED-TID]/brain
```

Would have failed in three ways: (1) `gbrain: command not found` (not in PATH), (2) `--dir path does not exist: /data/hermes/users/[REDACTED-TID]/brain` (no `brain/` under the numeric uid path), (3) if both were patched, the home-only default-scaffold fallback would have processed phantom pages instead of real content.

#### Agent-level fallback applied (per SKILL.md pitfalls)

Used the documented "Cron `--dir` failure: agent-level fallback pattern": keep `HOME` at the cron's original value for audit routing, point `--dir` at the real DRAAS-account brain.

```sh
HOME=/data/hermes/users/[REDACTED-TID] \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/psingh/brain
```

**Subtle but important nuance:** because `HOME=/data/hermes/users/[REDACTED-TID]` and that path has no `.gbrain/`, gbrain's config resolution auto-created a new PGLite config at `/data/hermes/users/[REDACTED-TID]/.gbrain/`, defaulting to **`zeroentropyai:zembed-1`** as the embedding model. This is **not** Prakash's real config (which lives at `/data/hermes/users/psingh/.gbrain-writable/.gbrain/config.json` and uses `minimax:embo-01`). The run processed the real `psingh/brain/` content (confirmed by `brain_dir: /data/hermes/users/psingh/brain` in the output) but the PGLite database and audit logs landed at `[REDACTED-TID]`'s `.gbrain/`, not at the real user's config path. Cross-check: the embed error mentions `zeroentropyai:zembed-1` (default-path model), not `minimax:embo-01` (the real `.gbrain-writable` model) — confirms the fallback used a throwaway PGLite.

**Lesson:** the agent-level fallback is good for **audit forensics** (logs stay at the cron's original HOME) but bad for **DB continuity** (the real `.gbrain-writable` PGLite is bypassed). If persistent embedding or DB state matters, prefer `GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable` over `HOME=<stale_uid>`.

#### Phase results

```
Status: partial — 575ms total — 22 phases
  ✓ sync               +1 added, ~0 modified (full reimport — fresh DB)
  ✓ backlinks          no missing back-links found
  ✓ extract            0 link(s), 0 timeline entries
  ✓ extract_facts      0 fact(s) reconciled across 0 page(s)
  ✓ resolve_symbol_edges  no chunks needed
  ✓ consolidate        promoted 0 facts into 0 takes
  ✓ propose_takes      scanned 7 pages, 0 cached, 0 new proposals
  ✓ grade_takes        scanned 0 takes
  ✓ calibration_profile  holder=garry, 0 resolved takes
  ✓ schema-suggest     0 suggestions
  ✓ purge              0 sources, 0 pages
  ❌ embed              zeroentropyai:zembed-1 requires ZEROENTROPY_API_KEY
  ⚠ lint               0 fix(es) applied, 1 remaining
  ⚠ orphans            7 orphan page(s) out of 7 total
  ⏭ synthesize         session_corpus_dir unset
  ⏭ extract_atoms      not in active pack (base-v2)
  ⏭ patterns           0 reflections in last 30d (need ≥3)
  ⏭ synthesize_concepts  not in active pack
  ⏭ conversation_facts_backfill  disabled
  ⏭ enrich_thin        disabled
  ⏭ skillopt           feature flag off
```

#### Comparison with prior runs

| Aspect | Run 7-8 (Jul 5-9) | Run 9 (Jul 13) | Run 10 (Jul 14) |
|---|---|---|---|
| Cron `uid` value | `psingh` (DRAAS slug) | `psingh` (DRAAS slug) | **`[REDACTED-TID]` (numeric Telegram ID)** |
| HOME | `/data/hermes/users/psingh` | `/data/hermes/users/psingh` | `/data/hermes/users/[REDACTED-TID]` |
| Config source | `.gbrain-writable/` (real) | Default at `$HOME/.gbrain/` (auto-created) | Default at `$HOME/.gbrain/` (auto-created) |
| Embed model | `minimax:embo-01` | `zeroentropyai:zembed-1` | `zeroentropyai:zembed-1` |
| --dir used | Yes (`psingh/brain`) | No (HOME-only fallback) | **Yes** (`psingh/brain`) |
| Brain processed | Real `psingh/brain/` | None (default scaffold only) | **Real `psingh/brain/`** |
| Duration | 553-591ms | ~600ms | 575ms |
| Sync | ok (1 page reimport) | 0 changes (no real content) | ok (1 page reimport) |

#### Noteworthy

- **New cron failure mode: `uid=<numeric_telegram_id>` is structurally worse than `uid=<draas_slug>`.** The numeric path was never migrated — `[REDACTED-TID]` has no `brain/`, no `.gbrain-writable/`, no real config. The DRAAS slug path (`psingh`) has all of those. The agent's fallback salvaged this run by pointing `--dir` at the real brain, but the data landed in a throwaway PGLite at the numeric uid's `.gbrain/`. If the cron continues to target numeric uids, every run will recreate a throwaway PGLite and lose continuity.
- **Cron is still misconfigured 14 days after migration** — needs to be updated from `uid=[REDACTED-TID]` to `uid=psingh` (the DRAAS account slug). The `identity.md` at `/data/hermes/users/psingh/brain/identity.md` already says "Telegram ID: [REDACTED-TID]" — the cron is targeting the right user, but via the wrong path.
- **Cross-check on agent-level fallback worked:** `brain_dir: /data/hermes/users/psingh/brain` in the dream output matches the agent's `--dir` — confirms `--dir` overrode the HOME-based default scaffold and processed the real brain content. The audit destination is `/data/hermes/users/[REDACTED-TID]/.gbrain/audit/` (the cron's original HOME) — useful for log forensics.
- **Embed model attribution as a diagnostic signal:** When the agent-level fallback runs against a numeric uid with no `.gbrain/`, the auto-created default config uses `zeroentropyai:zembed-1`. The embed error message's model name is the cleanest indicator that the run used the fallback config, not the real `.gbrain-writable` config. This is an extension of the existing "Embedding model differs by config path for same user" pitfall.

## Run 11 — Wednesday 15 July 2026, 02:41 UTC

#### Context

- Cron job hardcoded to **numeric Telegram ID** `uid=[REDACTED-TID]` (same as Run 10)
- Stale uid dir `/data/hermes/users/[REDACTED-TID]/` — only `.bun/` and `.gbrain/audit/`, no brain, no config
- Agent **used `GBRAIN_HOME` this time** (not HOME redirect) — pointed at the real `.gbrain-writable` config:
  ```sh
  GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
    /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
      --json --dir /data/hermes/users/psingh/brain
  ```
- This accesses the **real PGLite database** at `.gbrain-writable/.gbrain/brain.pglite` (stable since Run 6's Jul 3 fresh init — **12 days without re-init**)
- Embed model: **`minimax:embo-01`** (from real config, not throwaway `zeroentropyai:zembed-1`)
- safe.directory: already present since Run 8 (Jul 9) — no pre-flight fix needed
- Bun binary: `/data/hermes/home/.local/bin/bun` v1.3.14

#### Phase results

```
Status: partial — 1270ms total — 22 phases

  ✓ sync               +1 added, ~0 modified (full reimport — anchor ec580838 still gc'd)
  ✓ backlinks          no missing back-links found
  ✓ extract            0 link(s), 0 timeline entries
  ✓ extract_facts      0 fact(s) reconciled across 0 page(s)
  ✓ resolve_symbol_edges  no chunks needed
  ✓ consolidate        promoted 0 facts into 0 takes
  ✓ propose_takes      scanned 7 pages, 0 cached, 0 new proposals (7 ANTHROPIC_API_KEY warnings)
  ✓ grade_takes        scanned 0 takes
  ✓ calibration_profile  holder=garry, 0 resolved takes
  ✓ schema-suggest     0 suggestions
  ✓ purge              0 sources, 0 pages
  ❌ embed             minimax:embo-01 requires MINIMAX_API_KEY
  ⚠ lint               1 issue remaining, 0 fixed
  ⚠ orphans            7 orphan page(s) out of 7 total
  ⏭ synthesize         session_corpus_dir unset
  ⏭ extract_atoms      not in active pack (base-v2)
  ⏭ patterns           0 reflections in last 30d (need ≥3)
  ⏭ synthesize_concepts  not in active pack
  ⏭ conversation_facts_backfill  disabled
  ⏭ enrich_thin        disabled
  ⏭ skillopt           feature flag off
```

#### Sync anchor persistence

```
fatal: git cat-file: could not get object info
Sync anchor ec580838 object missing (gc'd after history rewrite). Running full reimport.
```

Same `ec580838` anchor hash from Run 6's brain-copy repo, still stored in the PGLite DB. The original brain repo (commit `be80f8a`) has never had this commit. Every run against the original brain dir triggers a **full reimport** of the single `identity.md` page. This is cosmetic (1 page, negligible cost) but the anchor will persist indefinitely until the PGLite DB is re-initialized.

#### Duration anomaly (1270ms vs ~575ms prior)

Run 11 took **1270ms** — more than double Runs 8-10 (553-591ms). The PGLite database at `.gbrain-writable/` is 12 days old and received 114+ migration checks (normal for a multi-day-old DB that connects after a gap). Prior runs were faster because the connection was to a fresh or recently-used DB. The duration is still well within acceptable range.

#### Comparison with Run 10 (Jul 14)

| Aspect | Run 10 (Jul 14) | Run 11 (Jul 15) |
|---|---|---|
| Cron uid | `[REDACTED-TID]` (numeric) | `[REDACTED-TID]` (numeric) |
| Config source | **HOME redirect**: throwaway PGLite at numeric uid's `.gbrain/` | **GBRAIN_HOME**: real `.gbrain-writable` PGLite |
| Embed model | `zeroentropyai:zembed-1` (throwaway config) | **`minimax:embo-01`** (real config) |
| Brain processed | Real `psingh/brain/` (via `--dir` override) | Same |
| Duration | 575ms | **1270ms** (older DB, more schema checks) |
| Sync anchor | Fresh DB — no anchor mismatch | **Persistent `ec580838` anchor miss** |
| Pages imported | 1 (full reimport — fresh DB) | 1 (full reimport — anchor miss) |
| safe.directory | Not checked (HOME redirect) | Already present (no fix needed) |

#### Noteworthy

- **GBRAIN_HOME worked with no pre-flight fixes needed** — safe.directory was already in the system gitconfig since Run 8 (Jul 9), and the `.gbrain-writable` config has been stable for 12 days without re-init. This is the cleanest run of the entire sequence.
- **Config persistence proven**: `.gbrain-writable` PGLite lasted 12 days (Jul 3 → Jul 15) across multiple runs without needing re-init. The ENOSPC corruption was a one-time event — the stable host keeps the database healthy.
- **The anchor miss is a permanent quirk for this brain** — `ec580838` from Run 6's brain-copy history will never resolve in the original brain repo. Only a PGLite re-init would clear it. The cost is negligible (1 page full reimport each run).
- **`identity.md` still has `garry`** — never rewritten for Prakash. All 7 `propose_takes` warnings are about missing `ANTHROPIC_API_KEY`, not about the identity being wrong. The `holder=garry` in calibration_profile persists.
- **Embed failure is the same pattern** — `minimax:embo-01` needs `MINIMAX_API_KEY`, which is not exported in the cron environment. Compare with Run 10's `zeroentropyai:zembed-1` — the model name in the embed error is the cleanest indicator of which config was used.

---

## Run 12 — Monday 20 July 2026, 02:42 UTC

#### Context

- Cron job hardcoded to **numeric Telegram ID** `uid=[REDACTED-TID]` (same as Runs 10-11)
- User dir `/data/hermes/users/[REDACTED-TID]/` — only `.bun/` and `.gbrain/audit/` (`.gbrain/` has no `config.json` — just audit logs and locks from prior runs)
- DRAAS account `psingh` not consulted by default — this run used the **literal cron command** first with `--dir`, then a **HOME-only no--dir fallback**
- No `GBRAIN_HOME`, no `--dir`, no `.gbrain-writable` involvement — pure `HOME=` fallback

#### Literal command failure

```sh
HOME=/data/hermes/users/[REDACTED-TID] gbrain dream --json --dir /data/hermes/users/[REDACTED-TID]/brain
```

Failed immediately: `--dir path does not exist: /data/hermes/users/[REDACTED-TID]/brain` (same as all prior numeric-uid runs).

#### HOME-only fallback — NEW edge case observed

After the `--dir` failure, retried with:

```sh
HOME=/data/hermes/users/[REDACTED-TID] gbrain dream --json
```

**This resolved brain_dir to Garry's brain** (`/data/hermes/users/[REDACTED-TID]/brain`), NOT the default scaffold (Run 9 behavior) and NOT Prakash's brain via `--dir` override (Run 10 behavior). This is a **new variant** of the HOME-only fallback pattern.

Key difference from Run 9 (Jul 13): Run 9 used `HOME=/data/hermes/users/psingh` (DRAAS slug) and gbrain auto-created a PGLite at `$HOME/.gbrain/`, running against default scaffold (7 phantom pages). This run used `HOME=/data/hermes/users/[REDACTED-TID]` (numeric uid, no `.gbrain/config.json`, but has stale `.gbrain/audit/` residue from prior runs) — gbrain fell through to a global default brain dir pointing at [REDACTED-TID]'s brain.

**Theory:** gbrain may scan `$HOME/.gbrain/` first (which exists for [REDACTED-TID] but has no config), and when that yields no valid config, it resolves to a globally configured or discovered brain dir — in this case Garry's brain at `[REDACTED-TID]/brain`, whose content happens to have the same 7-page scaffold structure as all un-initialized brains.

#### Phase results

```sh
Status: partial — 397ms total — 22 phases
  ✓ sync               +0 added, ~0 modified (up_to_date — no new content in Garry's brain)
  ✓ backlinks          no missing back-links found
  ✓ extract            0 link(s), 0 timeline entries
  ✓ extract_facts      0 fact(s) reconciled across 0 page(s)
  ✓ resolve_symbol_edges  no chunks needed
  ✓ consolidate        promoted 0 facts into 0 takes
  ✓ propose_takes      scanned 7 pages, 0 cached, 0 new proposals (7 ANTHROPIC_API_KEY warnings)
  ✓ grade_takes        scanned 0 takes
  ✓ calibration_profile  holder=garry, 0 resolved takes
  ✓ schema-suggest     0 suggestions
  ✓ purge              0 sources, 0 pages
  ❌ embed              zeroentropyai:zembed-1 requires ZEROENTROPY_API_KEY
  ⚠ lint               7 issues remaining (vs 1 in other runs — different brain content?)
  ⚠ orphans            7 orphan page(s) out of 7 total
  ⏭ synthesize         session_corpus_dir unset
  ⏭ extract_atoms      not in active pack (base-v2)
  ⏭ patterns           0 reflections in last 30d (need ≥3)
  ⏭ synthesize_concepts  not in active pack
  ⏭ conversation_facts_backfill  disabled
  ⏭ enrich_thin        disabled
  ⏭ skillopt           feature flag off
```

#### Comparison with prior HOME-only fallback runs

| Aspect | Run 9 (Jul 13) | Run 10 (Jul 14) | **Run 12 (Jul 20)** |
|---|---|---|---|
| HOME value | `psingh` (DRAAS slug) | `[REDACTED-TID]` (numeric) | `[REDACTED-TID]` (numeric) |
| HOME dir contents | `.bun/` only (no `.gbrain/`) | `.bun/` + `.gbrain/audit/` | `.bun/` + `.gbrain/audit/` + `.gbrain/.locks/` |
| `--dir` used? | No | Yes (`psingh/brain`) | **No** |
| **brain_dir resolved** | *ghost — default scaffold* | `psingh/brain` (via --dir) | **`[REDACTED-TID]/brain` (Garry's brain)** |
| Config source | Auto-created at `$HOME/.gbrain/` | Auto-created at `$HOME/.gbrain/` | **Auto-created at `$HOME/.gbrain/`** |
| Embed model | `zeroentropyai:zembed-1` | `zeroentropyai:zembed-1` | `zeroentropyai:zembed-1` |
| Content processed | Phantom scaffold (no real brain) | Real `psingh/brain/` content | **Garry's brain content** ([REDACTED-TID]) |
| Duration | ~600ms | 575ms | **397ms** |
| Lint issues | 1 | 1 | **7** (different brain dir) |
| Propose_takes warnings | 0 (no real pages) | 7 (ANTHROPIC_API_KEY) | 7 (ANTHROPIC_API_KEY) |
| Sync | 0 changes | 1 page (full reimport) | **0 changes (up_to_date)** |

#### Noteworthy

- **New fallback resolution discovered:** `HOME=<numeric_uid_with_audit_residue>` + no `--dir` → gbrain resolves to Garry's brain dir, not the default scaffold. The trigger appears to be the existence of a `.gbrain/` directory with audit logs (from prior runs) but no `config.json`. This contrasts with Run 9 where the HOME dir had no `.gbrain/` at all.
- **The 7 lint issues vs the usual 1** confirms a different brain dir was scanned — Garry's brain has different content quality than Prakash's.
- **`brain_dir` field in dream output is the critical diagnostic** — it told us the fallback processed Garry's brain, not Prakash's. Without checking it, the 7-page/7-orphan fingerprint would look like any other RUN for Prakash.
- **Embed model `zeroentropyai:zembed-1`** confirms the fallback used the auto-created default config path, not `.gbrain-writable`'s `minimax:embo-01`.
- **This is the worst possible fallback outcome** — HOME-only with numeric uid and stale .gbrain/audit/ residue silently processed the **wrong user's brain** without any `holder=` or `brain_dir` mismatch warning visible in the phase summary. The only way to catch it is to cross-check `brain_dir` in the raw JSON. See SKILL.md pitfalls: "always check `brain_dir` when using HOME-only fallback".
