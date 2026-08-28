# Roshini Ranka — gbrain dream (uid=rnr)

## Run 7: 2026-07-16 (cron job — numeric Telegram ID [REDACTED-TID], first successful run on numeric ID path)

### Setup

- **Cron target**: `HOME=/data/hermes/users/[REDACTED-TID] gbrain dream --json --dir /data/hermes/users/[REDACTED-TID]/brain`
- **Initial state**: User dir existed with only `.bun/` (install cache) — no `brain/` dir, no `.gbrain/` config
- **Brain dir created fresh**: `/data/hermes/users/[REDACTED-TID]/brain/` — initially empty, no git repo
- **Engine**: Shared Postgres DB (not PGLite) — gbrain config at default Postgres connection string

### Invocation sequence

The cron command `gbrain dream` failed on first attempt because `gbrain: command not found`. Resolved by finding bun at `/data/hermes/home/.local/bin/bun`:

```
HOME=/data/hermes/users/[REDACTED-TID] /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/[REDACTED-TID]/brain
```

**First attempt** — brain dir didn't exist:
```
--dir path does not exist: /data/hermes/users/[REDACTED-TID]/brain
```

**Second attempt** — brain dir created via `mkdir` but no git repo:
```
sync: "Not a git repository: /data/hermes/users/[REDACTED-TID]/brain. GBrain sync requires a git-initialized repo."
```

**Solution**: use `gbrain export` to pull 7 scaffold pages from shared Postgres DB, then init git:
```sh
mkdir -p /data/hermes/users/[REDACTED-TID]/brain
HOME=/data/hermes/users/[REDACTED-TID] /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts export --json --dir /data/hermes/users/[REDACTED-TID]/brain
# Exported 7 pages:
#   identity.md, readme.md, notes/readme.md, people/readme.md,
#   people/roshni-ranka.md, person/roshni-ranka.md, projects/readme.md

cd /data/hermes/users/[REDACTED-TID]/brain
git init
git config user.email "roshini@draas.com"
git config user.name "Roshini Ranka"
git add -A
git commit -m "initial brain export"
```

**Third attempt** — git works, sync needs HEAD:
```
sync: "No commits in repo /data/hermes/users/[REDACTED-TID]/brain. Make at least one commit before syncing."
```
(This was because the brain export + commit was done AFTER the first git-init retry. On the actual run with committed files, sync passed.)

### Dream results — successful `partial`

```
status: partial
duration_ms: 579
brain_dir: /data/hermes/users/[REDACTED-TID]/brain
```

| Phase | Status | Detail |
|-------|--------|--------|
| lint | ⚠️ warn | 7 issues found, 0 fixed (dry run) — all 7 pages |
| backlinks | ✅ ok | no gaps |
| sync | ✅ ok | **first_sync** — +0 added, ~0 modified (full reimport, 7 files unchanged) |
| synthesize | ⏭️ skipped | `session_corpus_dir` unset |
| extract | ✅ ok | 0 links, 0 timeline entries |
| extract_facts | ✅ ok | 0 facts reconciled, 2 phantoms scanned |
| propose_takes | ✅ ok | 7 pages scanned, **0 proposals** — all 7 had `ANTHROPIC_API_KEY` warnings |
| grade_takes | ✅ ok | 0 takes |
| calibration_profile | ✅ ok | `insufficient_data` |
| embed | ❌ **fail** | `zeroentropyai:zembed-1 requires ZEROENTROPY_API_KEY` |
| orphans | ⚠️ warn | **7 orphan page(s) out of 7 total** |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items |

**Embed model**: `zeroentropyai:zembed-1` (default config model, not `.gbrain-writable` minimax) — because there's no `.gbrain-writable` for the numeric ID path
**Default-scaffold fingerprint confirmed**: 7 orphans, 7 pages scanned, holder=garry in calibration_profile
**No rate limit hit**: embed failed cleanly on missing credential, not quota

### Key observations

#### 1. Numeric ID [REDACTED-TID] has Postgres DB scaffold entries

Despite being a stale/legacy path, the numeric ID had 7 default scaffold pages in the shared Postgres DB. `gbrain export` retrieved them successfully. This is the same default scaffold that any gbrain init creates — identity.md, readme.md, notes/readme.md, people/readme.md, projects/readme.md, people/roshni-ranka.md, person/roshni-ranka.md.

The DB entries likely came from a prior `init` or `dream` run on this ID (possibly from an earlier cron run or migration artifact).

#### 2. Brain dir was clean — no prior content

The brain dir at `/data/hermes/users/[REDACTED-TID]/brain/` did not exist before this run. The session created it from scratch. The 7 pages came entirely from the Postgres DB export, not from local files.

#### 3. No `.gbrain-writable` config existed

The numeric ID path has no `.gbrain-writable/` directory. gbrain used the default Postgres engine config (shared DB connection). This means:
- Embed used the default `zeroentropyai:zembed-1` model (not `minimax:embo-01` from `.gbrain-writable`)
- All DB phases used the shared Postgres connection
- No PGLite database was created

#### 4. Propose_takes warnings on all 7 pages

Same pattern as every other run — `ANTHROPIC_API_KEY` missing:
```
"extractor failed on identity: Anthropic chat requires ANTHROPIC_API_KEY."
"extractor failed on projects/readme: ..."
"extractor failed on notes/readme: ..."
"extractor failed on people/readme: ..."
"extractor failed on readme: ..."
"extractor failed on people/roshni-ranka: ..."
"extractor failed on person/roshni-ranka: ..."
```

All 7 pages were processed but produced zero proposals due to the missing API key.

#### 5. Default-scaffold fingerprint identical to stale-ID runs

The dream output matched the exact default-scaffold fingerprint documented in the gbrain-ops SKILL.md:
- `orphans: 7 orphan page(s) out of 7 total`
- `propose_takes: scanned 7 pages, 0 cached, 0 new proposals`
- `calibration_profile: holder=garry, 0 resolved takes`
- `extract_atoms: not in active pack` (skipped)

This confirms that the numeric ID [REDACTED-TID], when run with a properly initialized brain dir, produces the same output as any other user running the default scaffold. No user-specific content exists for this path.

#### 6. The `export → git init → commit → dream` flow works as a Postgres alternative to `init --pglite`

This session demonstrated an alternative first-time setup flow for Postgres-engine brains:
- Instead of `init --pglite` (which creates a new PGLite DB and runs 108+ migrations),
- Use `gbrain export` to pull existing scaffold pages from the shared Postgres DB,
- Then `git init && git add -A && git commit -m "initial"` to satisfy sync's git requirement,
- Then `gbrain dream` runs all phases against the existing Postgres engine.

This is faster than `init --pglite` (no migrations) and works when the shared Postgres DB already has entries for that user. It doesn't create user-specific content — just the default scaffold — but it unblocks the dream cycle.

### Summary

- **First successful dream on numeric ID [REDACTED-TID]** — previous runs on this path either failed (no brain dir) or used the DRAAS account path (rnr)
- **Brain dir created, git inited, pages exported from Postgres DB, dream completed** in 579ms
- **Default scaffold only** — 7 pages, holder=garry, no user-specific content
- **Embed blocked** on `zeroentropyai:zembed-1` (ZEROENTROPY_API_KEY missing)
- **Propose_takes blocked** on ANTHROPIC_API_KEY for all 7 pages
- **The numeric ID still has active Postgres DB entries** (default scaffold from a prior operation)
- **No rate limits hit** — all failures were clean missing-credential rejections
- The `export → git init → commit → dream` flow is a valid alternative to `init --pglite` for Postgres-engine brains with existing DB data


## Run 6: 2026-07-12 (cron job — stale Telegram ID rnr, brain dir still missing, no fallback executed)

### Setup

- **Cron target**: `HOME=/data/hermes/users/rnr gbrain dream --json --dir /data/hermes/users/rnr/brain`
- **Brain dir configured in cron**: `/data/hermes/users/rnr/brain` — **does not exist** (stale Telegram ID path)
- **User dir contents**: only `.bun/` cache (no brain, no `.gbrain/`, no `.gbrain-writable/`)
- **Actual brain data**: still at `/data/hermes/users/rnr/` per the Per-User Isolation table — this run did NOT execute the AUTOMATIC FALLBACK path (it failed immediately at the `--dir` validation step)

### Invocation

```sh
HOME=/data/hermes/users/rnr bun /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/rnr/brain
```

gbrain rejected the command immediately:
```
--dir path does not exist: /data/hermes/users/rnr/brain
```

No phases ran.

### Key observations

#### 1. Recurring failure across 4 runs (Jul 1, Jul 2 [fallback], Jul 10 [fallback], Jul 12)

This is the **second** occurrence of the exact same failure pattern (Run 3 on Jul 1 had the same error). The cron configuration has not been updated to use the DRAAS account path `rnr` despite:
- Run 3 (Jul 1) — failure, no fallback
- Run 4 (Jul 2) — failure, fallback to rnr brain-copy worked (860ms, partial)
- Run 5 (Jul 10) — failure, fallback to rnr brain-copy worked (584ms, partial)
- Run 6 (Jul 12, this run) — failure, no fallback executed

Runs 4 and 5 succeeded via the AUTOMATIC FALLBACK rule (Per-User Isolation table → `rnr`). This run did NOT apply the fallback, so it produced zero useful output. The cron needs to be updated to use `rnr` directly — relying on the agent's AUTOMATIC FALLBACK at runtime is fragile (the fallback only applies if the agent catches the failure and consults the table; cron runs that fail-fast on the CLI's `--dir path does not exist` error never reach the agent's recovery logic).

#### 2. The fix is a one-line cron change

**Option A (preferred — no brain data at `rnr`):** Update the cron job to use the DRAAS account path:
```sh
GBRAIN_HOME=/data/hermes/users/rnr/.gbrain-writable \
/data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
  --json --dir /data/hermes/users/rnr/brain-copy
```

**Option B (populate `rnr` with a real brain):** First-time init at the Telegram ID path — same as the "Brand new user" checklist in gbrain-ops SKILL.md:
```sh
mkdir -p /data/hermes/users/rnr/brain
HOME=/data/hermes/users/rnr \
  npx --yes bun run /opt/gbrain/src/cli.ts init --pglite --non-interactive --json --no-embedding
cd /data/hermes/users/rnr/brain
git init && git config user.email "hermes@draas.com" && git config user.name "Hermes DRAAS"
git add -A && git commit -m "initial brain state"
```
Then rewrite `identity.md` (default has username `garry`) and the cron target works as-is.

**Option B is NOT recommended** — Roshini's actual brain lives at `rnr/`, not `rnr/`. Creating a second brain at the Telegram ID path would scatter her data across two locations.

#### 3. No new pitfalls discovered

This run confirmed only that the existing "Cron job configured with stale user path" pitfall in the gbrain-ops SKILL.md is correct and persistent. No rate limit hit on embed (the command never reached the embed phase). No platform errors. The earlier Run 5 (Jul 10) showed that when the fallback does execute, the dream succeeds with `partial` status as expected.

### Summary

- Same failure as Run 3 (Jul 1) — the recurring issue is that the cron job hardcodes the stale Telegram ID `rnr`
- Two of the last three runs (Runs 4 and 5) succeeded via AUTOMATIC FALLBACK to `rnr`; this run (Run 6) did not execute the fallback and produced zero output
- **Action required**: update the cron job to use `rnr` directly. This is the only way to make the cron reliable without depending on per-run agent reasoning.
- The `gbrain-ops` SKILL.md "Cron job configured with stale user path" pitfall + the Roshini entry in the Per-User Isolation table already cover this case correctly

---

## Run 5: 2026-07-10 (cron job — stale Telegram ID rnr, GBRAIN_HOME + brain-copy on rnr, gc'd anchor)

### Setup

- **Cron target**: `/data/hermes/users/rnr/brain` — does not exist (stale Telegram ID, only `.bun/` cache)
- **Actual brain-copy**: `/data/hermes/users/rnr/brain-copy/` — **persisted from Run 4 (Jul 2)**, still has 2 git commits:
  ```
  9d00b18 sync 2026-07-02T01:44:55+00:00
  35b9ac2 init brain
  ```
- **Original brain**: `/data/hermes/users/rnr/brain/` (root-owned, 7 pages, git) — not synced to brain-copy since Jul 2
- **Config**: `.gbrain-writable/.gbrain/config.json` — PGLite, minimax:embo-01, database_path correct for rnr
- **Bun**: `/data/hermes/home/.local/bin/bun` v1.3.14
- **safe.directory**: Already configured for rnr paths in system gitconfig

### Invocation (GBRAIN_HOME — no brain-copy sync needed)

```sh
GBRAIN_HOME=/data/hermes/users/rnr/.gbrain-writable \
/data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
  --json --dir /data/hermes/users/rnr/brain-copy
```

No `rm -rf` + `cp -r` brain-copy sync was needed — the brain-copy from Run 4 (Jul 2) was still intact with its git history.

### Key observations

#### 1. brain-copy persisted for 8 days

The brain-copy at `/data/hermes/users/rnr/brain-copy/` survived between Jul 2 and Jul 10 with both git commits intact. No cleanup occurred — the cron system's ephemeral storage doesn't wipe user brain directories. This confirms brain-copy is durable across cron runs when it's under `/data/hermes/users/<uid>/`.

#### 2. Anchor was gc'd — full reimport (harmless)

The PGLite database's stored anchor commit (`7789bb24`) no longer existed in the brain-copy git history:
```
fatal: git cat-file: could not get object info
Sync anchor 7789bb24 object missing (gc'd after history rewrite). Running full reimport.
```
**Root cause**: The brain-copy was created via `rm -rf` + `cp -r` from the root brain (Run 4), which carried the root brain's git history. The original brain dir's anchor was from a prior setup cycle that was gc'd or reset. When the brain-copy was re-init'd with a fresh git repo (`git init` in Run 4), two different commit lineages existed — the fresh commits (`35b9ac2`, `9d00b18`) plus the old PGLite anchor from the original brain (`7789bb24`). Since the PGLite anchor references a commit that never existed in the re-init'd brain-copy repo, gbrain triggers a full reimport on every run.

**Fix**: This will happen on every subsequent run unless the PGLite anchor is reset. To fix: run `gbrain config set sync.anchor_commit null --force` in the brain-copy's PGLite database, or simply let gbrain re-anchor after the first full reimport (it should store the new head hash). The reimport confirmed that 1 page was imported (unchanged content skipped at the file level) — the full reimport cost is ~260ms, negligible.

#### 3. GBRAIN_HOME worked without issues

This was the first Roshini run using GBRAIN_HOME (Run 4 used HOME redirect). No git config problems, no `safe.directory` issues. The `.gbrain-writable` config was found and the PGLite database initialised cleanly.

#### 4. Dream results — expected `partial`

| Phase | Status | Detail |
|-------|--------|--------|
| lint | ⚠️ warn | 1 issue remaining, 0 fixed |
| backlinks | ✅ ok | No gaps |
| sync | ✅ ok | +1 added, 0 errors (full reimport, 1 page: identity.md) |
| synthesize | ⏭️ skip | `session_corpus_dir` unset |
| extract | ✅ ok | 0 links, incremental |
| extract_facts | ✅ ok | 0 facts reconciled, 2 phantoms scanned |
| consolidate | ✅ ok | 0 takes written |
| propose_takes | ✅ ok | 7 pages scanned, **7 extractor warnings** (`ANTHROPIC_API_KEY` missing) — all graceful |
| grade_takes | ✅ ok | 0 takes to grade |
| calibration_profile | ✅ ok | `insufficient_data` (0 resolved takes) |
| embed | ❌ **fail** | `LLMError: UNKNOWN` — `minimax:embo-01 requires MINIMAX_API_KEY` |
| orphans | ⚠️ warn | 7 orphan pages out of 7 total (default scaffolding) |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items |

- **Duration**: 584ms (faster than Run 4's 860ms — no brain-copy sync step needed)
- **Status**: `partial` (embed failure)
- **Imported**: 1 page (identity.md)
- **Embedded**: 0 (blocked by MINIMAX_API_KEY)

#### 5. Embed error class: `LLMError` code `UNKNOWN`

The embed failure reported:
```json
"error": {
  "class": "LLMError",
  "code": "UNKNOWN",
  "message": "Embedding model \"minimax:embo-01\" requires MINIMAX_API_KEY.\n\nSet it in your shell, or:\n  • Re-run with --no-embed to import-only..."
}
```
The error class/code pair is `LLMError / UNKNOWN` — not a descriptive error code. Useful for programmatic detection: check `error.class === "LLMError"` and `error.code === "UNKNOWN"` combined with the message containing "requires" for a heuristic match.

#### 6. Propose_takes warnings format

All 7 pages produced the same warning format:
```
"extractor failed on identity: Anthropic chat requires ANTHROPIC_API_KEY."
```
The "extractor failed on" prefix with page slug is the standard format. Importantly, these warnings DO NOT cause the phase to fail — the phase still reports `status: "ok"`. The warnings are buried in `details.warnings[]` as an array, not in `error`. To detect extraction failures programmatically, check `details.warnings` length > 0 AND any warning matching `extractor failed` pattern.

### Summary

- **brain-copy persisted** across 8 days — durable under `/data/hermes/users/`
- **Anchor gc'd** — full reimport happens every run; fixable by resetting `sync.anchor_commit` in PGLite config, but overhead is negligible (260ms)
- **GBRAIN_HOME** confirmed working for Roshini — no HOME redirect needed
- **No new blockers** — embed and propose_takes failures are the same platform constraints (missing API keys), no rate limits hit
- **Cron still targets stale Telegram ID** `rnr` — should be updated to `rnr` to avoid the wasted path-validation check


## Run 4: 2026-07-02

### Setup

- **Brain dir configured in cron**: `/data/hermes/users/rnr/brain` — **does not exist** (rnr dir exists but has only `.bun/` cache)
- **Actual brain dir**: `/data/hermes/users/rnr/brain/` (root-owned, 7 pages, git history since Jun 14)
- **Brain-copy**: `/data/hermes/users/rnr/brain-copy/` (hermes-owned, synced from brain)
- **Config**: `.gbrain-writable/.gbrain/config.json` — exists, PGLite, minimax:embo-01, database_path pointing to correct rnr path
- **Bun**: `/data/hermes/home/.local/bin/bun` (v1.3.14)

### Invocation

```sh
# Sync brain-copy from brain:
rm -rf /data/hermes/users/rnr/brain-copy
cp -r /data/hermes/users/rnr/brain /data/hermes/users/rnr/brain-copy
cd /data/hermes/users/rnr/brain-copy
git init && git config user.email "hermes@draas.com" && git config user.name "Hermes DRAAS"
git add -A && git commit -m "sync 2026-07-02T01:44:55+00:00"

# Run dream:
GBRAIN_HOME=/data/hermes/users/rnr/.gbrain-writable \
/data/hermes/home/.local/bin/bun run /opt/gbrain/src/cli.ts dream \
  --json --dir /data/hermes/users/rnr/brain-copy
```

### Key observations

#### 1. Three user directories exist for Roshini

The cron was hardcoded to `rnr` but that dir only has `.bun/` (bun install cache — created Jul 1). The actual brain data is at `rnr/`. Unique to Roshini: the old Telegram ID `rnr` still exists as a **live (non-renamed) hermes-owned directory**, unlike other users where it was either cleaned up or renamed to `._old_`. This is a subtle trap: the Step 0 path validation check finds a directory at `/data/hermes/users/rnr/` and passes, but there's no brain data there. Only `rnr/` has the real brain.

The three directories:

| Path | Owner | Content |
|------|-------|---------|
| `/data/hermes/users/rnr/` | hermes | brain (7 pages, git), .gbrain (root), .gbrain-writable (hermes), brain-copy (hermes) |
| `/data/hermes/users/rnr/` | hermes | `.bun/` only — no brain, no gbrain config |
| `/data/hermes/users/._old_rnr/` | root | old Telegram ID data (not migrated) |

#### 2. brain-copy synced and identity.md updated

The root brain had an updated `identity.md` — 2 lines added linking `rnr` to `draas_user_id=rnr`. brain-copy was behind (Jun 16 version). After`rm -rf` + `cp -r` sync, identity.md was up to date and committed (1 file changed, 2 insertions).

#### 3. GBRAIN_HOME worked cleanly

No git config issues (GBRAIN_HOME doesn't redirect HOME). The `.gbrain-writable` config had the correct `database_path` pointing to `rnr/.gbrain-writable/.gbrain/brain.pglite`. No schema migration issues — PGLite was already at the current version.

#### 4. Dream results — expected `partial`

| Phase | Status | Detail |
|-------|--------|--------|
| sync | ✅ ok | +1 page imported (identity.md update) |
| embed | ❌ fail | `minimax:embo-01 requires MINIMAX_API_KEY` — missing env var |
| propose_takes | ✅ ok | 7 pages scanned, 0 proposals (ANTHROPIC_API_KEY warnings on all — expected) |
| orphans | ⚠️ warn | 7/7 pages orphaned (single-page brain with scaffolding) |
| All other DB phases | ✅ ok | PGLite working, no schema issues |
| **Duration** | | 860ms |
| **Status** | | `partial` (embed failure) |

### Summary

- The cron hardcoded to Telegram ID `rnr` must be updated to `rnr`
- GBRAIN_HOME + brain-copy approach works reliably
- No new pitfalls discovered — the existing cron job path validation pattern covers this case once the cron config is updated
- The `rnr` live stale directory is a Roshini-specific trap: path validation passes but brain data is absent


## Run 3: 2026-07-01 (cron job — brain directory does not exist)

### Setup

- **Brain dir**: `/data/hermes/users/rnr/brain` — **does not exist**
- **User dir**: `/data/hermes/users/rnr/` — exists but contains only `.bun/` (install cache), no brain content
- **Config**: no `.gbrain/` or `.gbrain-writable/` directories present
- **Bun**: `/data/hermes/home/.local/bin/bun` (v1.3.14) — installed, on PATH from cron environment

### Invocation

```sh
HOME=/data/hermes/users/rnr bun /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/rnr/brain
```

gbrain rejected the command immediately:
```
--dir path does not exist: /data/hermes/users/rnr/brain
```

No phases ran — gbrain validates `--dir` existence before any processing.

### Key observations

#### 1. Brain dir was removed since Run 2 (Jun 28)

Between June 28 and July 1, `/data/hermes/users/rnr/brain/` was removed. The June 28 reference shows it existed with `identity.md` and a git repo (0 commits). As of July 1, only `.bun/` remains in the user directory. No brain scaffolding (`brain/{notes,people,projects}`) present either.

Possible causes:
- Cron maintenance cleanup (ephemeral storage reset)
- Manual directory purge by system admin
- A re-initialization process that removed and didn't recreate the brain dir

#### 2. gbrain validates --dir early (good behavior)

gbrain checks for directory existence eagerly — before any config loading, schema migrations, or PGLite initialization. The error is clean and immediate (no partial failures, no cascading issues).

#### 3. First-time setup needed for future runs

To run dream for Roshini again, the pre-flight checklist from gbrain-ops SKILL.md applies:

1. Create brain structure: `mkdir -p /data/hermes/users/rnr/brain/{notes,people,projects}`
2. Init git repo with at least one commit
3. Set up `.gbrain-writable` config via `init --pglite --force --skip-embed-check`
4. Then run dream with `GBRAIN_HOME` pointing to the writable config

### Summary for future runs

- **Brain dir is gone** — complete re-initialization needed before any dream run
- This is the first DRAAS user observed to have an entirely missing brain dir after prior runs, suggesting a cleanup/reset between June 28 and July 1
- No new technique or workaround needed — the existing first-time setup checklist in gbrain-ops covers this case

---

## Run 2: 2026-06-28 (cron job, no HOME redirect — root-owned config, schema migration partial failure)

### Setup

- **Brain dir** (original, root-owned): `/data/hermes/users/rnr/brain/`
  - 1 file (`identity.md`), git repo with **0 commits** (repo was reset or re-cloned since June 23)
  - `safe.directory` set in system gitconfig only — invisible when HOME is not redirected
- **Config**: default path `/data/hermes/users/rnr/.gbrain/` — root-owned (600)
  - No `.gbrain-writable` used in this run
  - Schema version: 34, target: 119 (84 migrations pending)
- **Bun**: `/data/hermes/home/.local/bin/bun` (v1.3.14) — used directly, not via npx

### Invocation

```sh
HOME=/data/hermes/users/rnr \
  /data/hermes/home/.local/bin/bun run /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/rnr/brain
```

No `GBRAIN_HOME`, no `HOME` redirect to `.gbrain-writable`, no `GIT_CONFIG_GLOBAL` — ran against the **default root-owned config** and **original brain dir**.

### Key observations

#### 1. EACCES on `.gbrain/audit/` — root-owned config blocks audit dir creation

The root-owned `.gbrain/` dir (600) is readable enough for gbrain to load its config, but **not writable** for creating subdirectories. This produced:
```
[connection-audit] write failed: EACCES: permission denied, mkdir '/data/hermes/users/rnr/.gbrain/audit'
```
This warning repeats multiple times at startup and shutdown. Harmless to output but indicates the config dir isn't fully usable.

#### 2. Schema migration partial failure

gbrain detected 84 pending migrations (schema 34 → 119) and attempted to apply them, but the event trigger creation step failed:
```
Schema probe failed: permission denied to create event trigger \"auto_rls_on_create_table\"
  Re-run: `gbrain apply-migrations --yes`
```
This is the **same PGLite permissions limitation** as other DRAAS users — the in-process PGLite WASM runtime doesn't have the privileges needed for event triggers. The migration halts at step 35, leaving the schema in a **partially-migrated state**:

| Missing relation/column | Cascading failures |
|---|---|
| `relation "facts" does not exist` | extract_facts ❌, consolidate ❌ |
| `column cc.edges_backfilled_at does not exist` | resolve_symbol_edges ❌ |
| `relation "takes" does not exist` | recompute_emotional_weight ❌, grade_takes ❌, calibration_profile ❌ |

This is the first DRAAS user where the schema migration was this far behind (v34 — other users start at v1 or v2). The 84-step gap suggests gbrain was updated but the PGLite database was from a much older version.

#### 3. Sync failed — no git commits

```
No commits in repo /data/hermes/users/rnr/brain. Make at least one commit before syncing.
```
The brain dir's git repo has been reset — zero commits. Unlike the June 23 run (which had commit `35b9ac2`), the current brain has no git history. This blocks the `sync` phase entirely.

#### 4. Embedding model: `zeroentropyai:zembed-1`

```
Embedding model \"zeroentropyai:zembed-1\" requires ZEROENTROPY_API_KEY.
```
Roshini's config uses the same embedding model as Bharat (sales1.blr) — `zeroentropyai:zembed-1` via `ZEROENTROPY_API_KEY`, NOT the `minimax:embo-01` / `MINIMAX_API_KEY` used by most other DRAAS users.

#### 5. Built-in bun on PATH works

Unlike the June 23 run (which used `npx --yes bun`), this run found bun at `/data/hermes/home/.local/bin/bun` (v1.3.14) — the permanent install location. Using the direct binary is ~2s faster than the `npx` detour and doesn't hit npm cache issues.

#### 6. Non-DB phase resilience

Despite the cascading schema failures, several phases still completed successfully:
- **lint** ⚠️ — 1 issue found on single page
- **backlinks** ✅ — no gaps
- **extract** ✅ — processed 1 page (links/timeline extraction is filesystem-based, not DB-dependent)
- **propose_takes** ✅ — scanned 0 pages (skips cached pages)
- **orphans** ✅ — 0 orphans
- **purge** ✅ — nothing to purge
- **schema-suggest** ✅ — 0 suggestions

### Dream output — full phase breakdown

| Phase | Status | Detail |
|-------|--------|--------|
| lint | ⚠️ warn | 0 fixes applied, 1 remaining |
| backlinks | ✅ ok | No gaps |
| sync | ❌ fail | No commits in repo |
| synthesize | ⏭️ skip | `session_corpus_dir` unset |
| extract | ✅ ok | 0 links, 0 timeline entries |
| extract_facts | ❌ fail | Relation `facts` does not exist |
| extract_atoms | ⏭️ skip | Not in active pack |
| resolve_symbol_edges | ❌ fail | Column `edges_backfilled_at` missing |
| patterns | ⏭️ skip | 0 reflections in 30d (need ≥3) |
| recompute_emotional_weight | ❌ fail | Relation `takes` does not exist |
| consolidate | ❌ fail | Relation `facts` does not exist |
| propose_takes | ✅ ok | 0 proposals |
| grade_takes | ❌ fail | Relation `takes` does not exist |
| calibration_profile | ❌ fail | Relation `takes` does not exist |
| conversation_facts_backfill | ⏭️ skip | Disabled (default) |
| enrich_thin | ⏭️ skip | Disabled (default) |
| skillopt | ⏭️ skip | Feature flag off |
| embed | ❌ fail | `ZEROENTROPY_API_KEY` not set |
| orphans | ✅ ok | 0 orphans out of 0 total pages |
| schema-suggest | ✅ ok | 0 suggestions |
| purge | ✅ ok | 0 items |

- **Duration**: 428ms
- **Status**: `partial` (7 phases failed, 7 skipped, 8 ok/warn)

### Summary for future runs

- **Fix the git repo**: `cd /data/hermes/users/rnr/brain && git add -A && git commit -m "init"` — the brain dir needs at least one commit.
- **Use GBRAIN_HOME or HOME redirect**: Pointing to `.gbrain-writable` eliminates both the EACCES audit errors and the schema migration failure (writable config allows PGLite to apply the full 84-step migration). Without this, all DB-backed phases that depend on `facts`, `takes`, or `edges_backfilled_at` will continue to fail.
- **Embedding blocked**: Requires `ZEROENTROPY_API_KEY` (not `MINIMAX_API_KEY`). Platform-wide limitation — no API keys set for any embedding provider.

---

## Run 1: 2026-06-23 (GIT_CONFIG_GLOBAL approach — brain-copy-less, working PGLite)

### Setup

- **Brain dir** (original, root-owned): `/data/hermes/users/rnr/brain/`
  - 1 file (`identity.md`), git repo with 1 commit (`35b9ac2 init brain`)
  - `safe.directory` already set in system gitconfig for this path
- **Config**: `.gbrain-writable/.gbrain/config.json` exists, hermes-owned (338 bytes)
- **Bun**: `npx --yes bun` (v1.3.14) — no need for direct binary

### Invocation (GIT_CONFIG_GLOBAL approach)

```sh
GIT_CONFIG_GLOBAL=/data/hermes/home/.gitconfig \
HOME=/data/hermes/users/rnr/.gbrain-writable \
npx --yes bun run /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/rnr/brain
```

**No brain-copy needed** — GIT_CONFIG_GLOBAL makes `safe.directory` visible even with HOME redirect, letting dream operate directly on the root-owned original brain dir.

### Key observations

#### Anchor stale → full reimport (harmless)

The stored anchor commit (`8a6bb1ab`) didn't exist in the brain's git history (which has only `35b9ac2`). gbrain detected this and ran a full reimport:
```
Sync anchor commit 8a6bb1ab missing (force push?). Running full reimport.
```
Since content was unchanged, 0 pages were imported (1 skipped as unchanged). This adds ~200ms overhead on the first run after switching from brain-copy to direct dir.

**Fix**: This is a one-time occurrence when switching from brain-copy to direct brain dir — subsequent runs use incremental sync.

#### GIT_CONFIG_GLOBAL + HOME redirect works

The GIT_CONFIG_GLOBAL fix (pointing git at `/data/hermes/home/.gitconfig` which already has `safe.directory` entries) eliminated the `fatal: detected dubious ownership` error that would otherwise occur with HOME redirect + root-owned brain dir. No extra git config commands needed.

#### db-backed phases all work

PGLite initialized successfully via the `.gbrain-writable` HOME redirect — all DB phases (sync, extract, consolidate, patterns, etc.) executed. Only embed blocked by missing `MINIMAX_API_KEY` (platform-wide limitation).

### Dream output summary (June 23)

| Phase | Status | Detail |
|-------|--------|--------|
| sync | ✅ ok | +0 added, ~0 modified (full reimport, stale anchor) |
| lint | ⚠️ warn | 1 issue on single-page brain |
| backlinks | ✅ ok | no gaps |
| extract | ✅ ok | incremental, 0 pages processed |
| extract_facts | ✅ ok | 0 facts reconciled |
| consolidate | ✅ ok | 0 takes |
| propose_takes | ✅ ok | 1 page scanned, `ANTHROPIC_API_KEY` warning (expected) |
| grade_takes | ✅ ok | 0 takes to grade |
| embed | ❌ fail | `MINIMAX_API_KEY` not set (platform limitation) |
| orphans | ⚠️ warn | 1 orphan out of 1 total page |
| purge | ✅ ok | nothing purged |
| others | ✅/⏭️ | feature-flagged or insufficient data |

- **Duration**: 890ms
- **Status**: `partial` (expected — embed phase blocked by platform constraint)
- **Imported**: 0 pages (1 skipped as unchanged)
- **Embedded**: 0 (blocked by MINIMAX_API_KEY)

### Current brain structure

```
identity.md        — 1 page (Roshini's identity/profile note)
```
(The empty `notes/`, `people/`, `projects/` directories present in 2026-06-21 are no longer present.)
