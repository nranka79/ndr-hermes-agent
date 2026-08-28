# Cron Literal-Command Recipes (per user)

The literal `gbrain dream --json --dir <telegram_id>/brain` invocation that crons currently ship with fails for two reasons: (1) `gbrain` isn't on PATH, and (2) the Telegram-ID directory is a stale live dir with no `brain/` subdir. Use the per-user recipes below instead — they invoke the bun source path with `GBRAIN_HOME` pointing to the writable config and `--dir` at the real DRAAS-account brain path.

## Bun binary: known architecture mismatch

**⚠️ The symlink at `/data/hermes/home/.local/bin/bun` is a broken aarch64 binary on this x86_64 system.** It produces `Exec format error` when invoked directly. The working bun binary is at `/data/hermes/home/.bun/bin/bun` (v1.3.14, x86_64). 

All recipes below that reference `.local/bin/bun` should be read as `.bun/bin/bun` — the recipes are kept with `.local/bin/bun` for historical consistency but MUST be adjusted at runtime. The `gbrain` wrapper script at `/data/hermes/home/.local/bin/gbrain` was patched on 2026-08-10 to point to the correct path.

**Tiered resolution order when bun fails:**
1. `/data/hermes/home/.bun/bin/bun` — confirmed working, correct arch
2. `/data/hermes/home/.local/bin/bun` — may fail with Exec format error (aarch64)
3. `npx --yes bun run /opt/gbrain/src/cli.ts` — slow but reliable fallback

## Per-user working invocations

### Prakash Singh — Telegram psingh → DRAAS `psingh`

```sh
GBRAIN_HOME=/data/hermes/users/psingh/.gbrain-writable \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/psingh/brain
```

Last verified 2026-07-12: status `partial`, 412ms, 22 phases ran. Embed fails (no `MINIMAX_API_KEY`; configured model `minimax:embo-01` is also exhausted at provider). 7 pages synced, 0 net changes (brain content unchanged from prior run). 7 orphan pages — expected on a brain with only default scaffolding (identity.md + readme + 5 templates).

### Vinod Kumar Das — Telegram vkdas → DRAAS `vkdas`

```sh
# Default config is root-owned Postgres/Supabase (no --dir needed); but
# .gbrain-writable PGLite config exists for fallback. Pick one:

# Option A: Postgres engine, no --dir
HOME=/data/hermes/users/vkdas \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream --json

# Option B: PGLite via .gbrain-writable
GBRAIN_HOME=/data/hermes/users/vkdas/.gbrain-writable \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/vkdas/brain
```

Default config uses `zeroentropyai:zembed-1` (needs `ZEROENTROPY_API_KEY`); `.gbrain-writable` uses `minimax:embo-01` (needs `MINIMAX_API_KEY`). Embed fails under either — the config path you pick determines the error message.

### Roshini Ranka — Telegram rnr → DRAAS `rnr`

```sh
GBRAIN_HOME=/data/hermes/users/rnr/.gbrain-writable \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/rnr/brain
```

**Numeric-uid cron target: `uid=[REDACTED-TID]`.** Crons may target the numeric Telegram ID [REDACTED-TID] for "Roshini Ranka", but that path is NOT Roshini's brain:
- `/data/hermes/users/[REDACTED-TID]/brain` holds default scaffolding with `identity.md` = "Bharat Hawaldar" (not Roshini).
- `/data/hermes/users/[REDACTED-TID]/.gbrain/` has only `audit/`, `.locks/`, `last-update-check` residue — **no `config.json`**, so `dream` fails with `No brain configured. Run: gbrain init` (exit 1, no JSON) even with `--dir` pointing at the populated brain dir.
- Roshini's real brain is the `rnr` slug (above) with config at `rnr/.gbrain-writable/.gbrain/config.json` (`minimax:embo-01`, PGLite).
- Verified 2026-08-11: canonical `rnr` run → status `partial`, 249ms, sync ok (+0/~0/-0), embed fail (`minimax:embo-01 requires MINIMAX_API_KEY`), 1 orphan page, 6 schema migrations applied (119→125). Steady-state partial is expected.

**Wrapper sources `/data/hermes/.env`:** as of Aug 2026 the `gbrain` wrapper at `/data/hermes/home/.local/bin/gbrain` sources `/data/hermes/.env` (and unsets `GBRAIN_DATABASE_URL`/`DATABASE_URL` to avoid cross-user Postgres contamination) before exec'ing bun. So `OPENROUTER_API_KEY` IS now in gbrain's environment for wrapper invocations — the older "export from `.openrouter_key`" workaround is only needed for direct bun/npx invocations that bypass the wrapper.

### Anbarasan Murugaperumal — Telegram pm2.blr → DRAAS `pm2.blr`

```sh
# Use brain-copy because /pm2.blr/brain is root-owned and has no git history.
# If brain-copy is also missing, fall back to brain (with safe.directory set).
GBRAIN_HOME=/data/hermes/users/pm2.blr/.gbrain-writable \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/pm2.blr/brain-copy
```

### Bharat Hawaldar — Telegram sales1.blr → DRAAS `sales1.blr`

```sh
GBRAIN_HOME=/data/hermes/users/sales1.blr/.gbrain-writable \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/sales1.blr/brain
```

⚠️ The Telegram-ID path `sales1.blr` had a Postgres config (Jul 9 2026) but was cleaned up by Jul 10 — only `audit/` remains. Running dream there without `--dir` now resolves to `psingh`'s brain (wrong user). Always use `sales1.blr`.

### Nishant Ranka — Telegram ndr → DRAAS `ndr`

```sh
# Option A (preferred): GBRAIN_HOME, no HOME redirect
GBRAIN_HOME=/data/hermes/users/ndr/.gbrain-writable \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/ndr/brain

# Option B: direct HOME (when .gbrain/ is hermes-owned at default path)
HOME=/data/hermes/users/ndr \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/ndr/brain
```

The Telegram-ID path `ndr` had a fresh `init` on Jul 2 2026 (--no-embedding, hermes-owned) and may still produce results. But the canonical path is `ndr`. The MiniMax key is exhausted (429) — switch to OpenRouter embedding by exporting `OPENROUTER_API_KEY` from `.openrouter_key`.

### Nishant Ranka — numeric Telegram uid `[REDACTED-TID]`

Same person as `ndr` above, but via Telegram numeric ID. This path has a working brain dir with 7 pages (same `--no-embedding` + no-git skeleton).

```sh
# Direct HOME invocation (preferred for cron audit routing)
HOME=/data/hermes/users/[REDACTED-TID] \
  /data/hermes/home/.bun/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/[REDACTED-TID]/brain
```

**Failure pattern (confirmed 2026-08-10, 666ms):**
- sync: fail — "Not inside a git repository" (no `.git/` in brain dir)
- embed: fail — "brain initialized with --no-embedding (deferred setup)"
- 7 pages recomputed for emotional weight, 3 orphan pages
- Same pattern as `ndr` slug brain — identical init state

## Cron-output parsing

After running any of the above, pipe through the JSON summary one-liner (in the main SKILL.md) to get a 22-line report:

```sh
... 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); ..."
```

Expected patterns by user:

| User | Status | Sync | Embed | Notes |
|---|---|---|---|---|---|
| psingh | partial | ok (0 net change) | fail (minimax:embo-01) | 7 orphan pages (default scaffolding) |
| vkdas | partial | ok | fail (zeroentropy OR minimax) | Postgres engine is cleanest path |
| rnr | partial | ok | fail | Same as psingh pattern |
| pm2.blr | partial | ok | fail | Use brain-copy, not brain |
| sales1.blr | partial | ok | fail | Avoid sales1.blr path |
| ndr | partial | ok | fail (429) | OpenRouter key export needed |
| [REDACTED-TID] | partial | fail (no git) | fail (--no-embedding) | Numeric uid, same person as ndr; 7 pages, 3 orphans |

## Pitfalls specific to cron literal commands

- **`/data/hermes/home/.local/bin/bun` is aarch64 on this x86_64 host.** It produces `Exec format error` with exit code 126. The working binary is at `/data/hermes/home/.bun/bin/bun`. If bun fails, check with `file <path>` or just try `~/.bun/bin/bun` directly.
- **`gbrain` wrapper script was patched 2026-08-10** to point to the correct bun path, but if the script was re-installed or the symlink was replaced, it breaks again. The script is at `/data/hermes/home/.local/bin/gbrain` — verify the exec line points to `.bun/bin/bun`, not `.local/bin/bun`.
- **Exit code lies when `--dir` doesn't exist.**** Observed exit 0 AND exit 1 on different runs. Always grep for `--dir path does not exist` AND check `phases` is non-empty.
- **Stale Telegram-ID paths accumulate `.bun/` cache** as hermes-owned files. They look like valid user dirs in `ls` but have no `brain/` and no `.gbrain/config.json`. The only signal is the absence of `brain/`.
- **Numeric Telegram IDs (`uid=[REDACTED-TID]`) are structurally worse than DRAAS slugs (`uid=psingh`).** The numeric path was never migrated — no `brain/`, no `.gbrain-writable/`, no real config. The DRAAS slug has all of those. Agent-level fallback with `HOME=<numeric>` + `--dir <draas_brain>` works (processes real content) but uses a throwaway PGLite at the numeric path — see the "agent-level fallback uses a throwaway PGLite" caveat in SKILL.md pitfalls and `references/prakash-dream.md` Run 10.
- **`HOME=<stale_uid>` + `--dir <real_brain>` works for audit routing** — keeps audit logs in the stale uid's `.gbrain/audit/` dir while running dream against the real brain. Use when the cron must keep its audit identity. **Trade-off:** throwaway PGLite, no DB continuity. For real DB continuity, use `GBRAIN_HOME=<draas_user>/.gbrain-writable` instead.
- **`brain_dir` field in dream output tells you which brain was processed.** A mismatch with the expected user means the pipeline processed wrong data (saw this on Bharat sales1.blr → psingh misroute).
- **`MINIMAX_API_KEY` is exhausted at the provider** for all DRAAS users as of mid-2026. The `openrouter:openai/text-embedding-3-small` path HAS a valid key at `.openrouter_key` but it's not exported as `OPENROUTER_API_KEY` env var. Export it before running dream to enable embedding.
- **Embed model attribution as a diagnostic signal.** When the dream output's embed error mentions a model that doesn't match the user's known config (e.g. `zeroentropyai:zembed-1` when the user's `.gbrain-writable` is `minimax:embo-01`), it means the run used a fallback config — either the agent-level fallback (above) or the home-only default scaffold. Cross-check with `brain_dir` in the output to confirm which brain was actually processed.
- **HOME-only with numeric-uid + stale `.gbrain/audit/` + no `--dir` → processes wrong user's brain.** This is the worst fallback. When `HOME` points to a numeric-uid path that has `.gbrain/audit/` residue (from prior cron runs) but no `config.json`, gbrain falls through to a globally discovered brain dir — in this case Garry's brain (`[REDACTED-TID]/brain`), not Prakash's (`psingh/brain`). The 7-page/7-orphan fingerprint looks identical to Prakash's normal run, making it hard to detect without checking `brain_dir`. The `.gbrain/audit/` residue triggers a different resolution path than a completely empty dir (which produces default scaffold, Run 9). **Always check `brain_dir` when using HOME-only fallback.**
