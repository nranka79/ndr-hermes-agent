# OpenRouter Embedding + Shared-Postgres Contamination Fix (Aug 10 2026)

## What was fixed

### 1. Embedding now works via OpenRouter

Nishant's brain (uid=[REDACTED-TID]) previously used `minimax:embo-01` (key exhausted, 429) and was
initialized with `--no-embedding` (`embedding_disabled: true` in config).

Fix applied:

1. Edited `/data/hermes/users/[REDACTED-TID]/.gbrain/config.json`:
   - removed `embedding_disabled`
   - added `"embedding_model": "openrouter:openai/text-embedding-3-small"`
   - added `"embedding_dimensions": 1536`
2. Old PGLite DB was vector(1280) (minimax dims) — `reinit-pglite` needed since PGLite cannot
   ALTER vector column types. Reinit preserves old DB as `brain.pglite.bak`.
3. Wrapper `/data/hermes/home/.local/bin/gbrain` now sources `/data/hermes/.env` so
   `OPENROUTER_API_KEY` (single source of truth, shared with Hermes) flows into every gbrain run.

Verified:
- `gbrain doctor`: `[OK] embedding_provider: openrouter:openai/text-embedding-3-small ✓ 292ms, 1536 dims, DB aligned`
- `gbrain embed --stale`: `Embedded 7 chunks across 7 pages`
- `gbrain doctor`: `[OK] embeddings: 100% coverage, 0 missing`
- Brain score 10 → 45 (embed component 35/35)
- Semantic search works: `gbrain query "Roshni Ranka contact phone"` returns 0.91 relevance

### 2. CRITICAL: Cross-user data contamination from shared Postgres

**Root cause**: The Hetzner infra compose (`/opt/hermes/Infrastructure_Scripts/hetzner/docker-compose.yml`)
injects `GBRAIN_DATABASE_URL=postgresql://gbrain:***@postgres:5432/gbrain` into the container env
(landing at `/run/s6/container_environment/GBRAIN_DATABASE_URL`). gbrain treats this env var as
authoritative and connects to ONE shared Postgres for ALL users — completely bypassing the
per-user PGLite configs that the gbrain-ops skill documents.

**Symptom**: `gbrain list` under ANY user's HOME returned the same 7 pages, a mix of all users'
data:
- identity = "Bharat Hawaldar" (wrong for Nishant)
- notes/readme = "Vinod Kumar Das - Brain"
- readme = "Anbarasan Murugaperumal — Brain"
- people/roshni-ranka = Roshni's real phone +919845026390, email rnr@draas.com (visible to everyone)

This is a data-isolation violation: every user could see every other user's brain content.

**Fix applied**: `/data/hermes/home/.local/bin/gbrain` now contains:
```sh
unset GBRAIN_DATABASE_URL DATABASE_URL 2>/dev/null
```
at the top, so gbrain resolves each user's own PGLite via `$HOME/.gbrain/config.json`.

**Verification**: With the unset in place, `HOME=/data/hermes/users/[REDACTED-TID] gbrain list` shows
only Nishant's 4 pages (identity, notes/readme, people/readme, projects/readme) and `gbrain doctor`
reports `connection: Connected, 4 pages` (per-user PGLite), not 7 (shared Postgres).

## Per-user setup after the fix

**2026-08-11: Bharat (sales1.blr) migrated to OpenRouter embedding.** Edited
`/data/hermes/users/sales1.blr/.gbrain-writable/.gbrain/config.json`:
`embedding_model` minimax:embo-01 → `openrouter:openai/text-embedding-3-small`
(dims stayed 1536). Backup at `config.json.bak-20260811`. Dream now: embed ok
(1 chunk embedded), status partial only due to missing ANTHROPIC_API_KEY
(propose_takes, non-blocking). Also note: the numeric Telegram-ID path
`/data/hermes/users/[REDACTED-TID]/` has NO config.json since the wrapper unsets
`GBRAIN_DATABASE_URL` — cron must target `HOME=/data/hermes/users/sales1.blr`
with `GBRAIN_HOME=/data/hermes/users/sales1.blr/.gbrain-writable` instead.

**2026-08-11 (same day): Vinod (vkdas) migrated to OpenRouter embedding.** Same
edit at `/data/hermes/users/vkdas/.gbrain-writable/.gbrain/config.json`:
`embedding_model` minimax:embo-01 → `openrouter:openai/text-embedding-3-small`
(dims stayed 1536). Backup at `config.json.bak-20260811`. Verified invocation
(works, embed ok):
```sh
GBRAIN_HOME=/data/hermes/users/vkdas/.gbrain-writable \
  /data/hermes/home/.local/bin/gbrain dream --json --dir /data/hermes/users/vkdas/brain-copy
```
Result: status partial (917ms, 23 phases), sync ok (0 added — 1 page total),
embed ok (1 page embedded, 679ms), propose_takes skipped (no ANTHROPIC_API_KEY,
non-blocking), lint warn (1 issue), orphans warn (1/1). Brain content: 1 page
(`identity` — Vinod Kumar Das).

**Failure-signature note for Vinod's cron (uid=[REDACTED-TID])**: the literal command
`HOME=/data/hermes/users/[REDACTED-TID] gbrain dream --json --dir .../[REDACTED-TID]/brain`
fails with exit 1 `No brain configured. Run: gbrain init` — the numeric dir HAS an
empty `brain/` subdir (since ~Jul 18) but no `.gbrain/` config. This is a NEW
failure signature vs the Jul 14 run (`--dir path does not exist`). Both mean the
same: stale numeric-uid target. Do NOT `gbrain init` there; run the vkdas
invocation above. See the SKILL.md pitfall on numeric Telegram-ID uids.

For each DRAAS user, the brain dir needs to be a git repo for `sync` to work:

```sh
cd /data/hermes/users/<uid>/brain
git init
git config user.email "<email>@draas.com"
git config user.name "<Name>"
git add -A
git commit -m "Seed brain"
```

Then dream runs cleanly:
```sh
export PATH="/data/hermes/home/.local/bin:$PATH"
HOME=/data/hermes/users/<uid> gbrain dream --json --dir /data/hermes/users/<uid>/brain
```

Nishant's dream now: sync ok (4 pages), embed ok (4 pages), status partial only because
`propose_takes` is skipped (no ANTHROPIC_API_KEY — LLM insight extraction, non-blocking).

## Residual notes

- `propose_takes` / LLM extraction needs ANTHROPIC_API_KEY. Currently not in /data/hermes/.env
  nor s6 env. Non-blocking — everything else runs.
- The old contaminated shared Postgres still exists at postgres:5432/gbrain. It is now unused by
  the wrapper. If it should be dropped, do it on the host (outside the Hermes container).
- Do NOT re-add GBRAIN_DATABASE_URL to the container env without per-user Postgres schemas.
