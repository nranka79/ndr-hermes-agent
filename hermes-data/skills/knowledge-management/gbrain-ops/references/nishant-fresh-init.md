# Nishant ndr — Fresh gbrain Init & First Dream (Jul 2 2026)

## Context

This user (Telegram ID `ndr`, Nishant Ranka) had **no existing gbrain setup** — no `.gbrain/` config dir, no `brain/` content dir, only a `the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)` in their user directory. This was a true first-time setup, not a migration or re-init.

## Init Command

```
HOME=/data/hermes/users/ndr npx --yes bun run /opt/gbrain/src/cli.ts init --pglite --non-interactive --json --no-embedding
```

- Created `/data/hermes/users/ndr/.gbrain/` (hermes-owned, writable)
- Applied 114 schema migrations (v1 → v119) successfully
- Database at `/data/hermes/users/ndr/.gbrain/brain.pglite`
- Schema pack: `gbrain-base-v2`
- Search mode: `conservative` (no LLM expansion — no OpenAI key)

## Result: 7 Default Scaffolding Pages

The init command auto-created these pages under the brain dir at `/data/hermes/users/ndr/brain/`:

- `identity.md`
- `projects/readme.md`
- `notes/readme.md`
- `people/readme.md`
- `readme.md`
- `people/roshni-ranka`
- `person/roshni-ranka`

These are generic starter templates — no real content.

## First Dream Run

```
HOME=/data/hermes/users/ndr npx --yes bun run /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/ndr/brain
```

**Status:** `partial` — 839ms duration

| Phase | Result | Reason |
|---|---|---|
| lint | ✅ ok | 0 issues |
| backlinks | ✅ ok | 0 gaps |
| sync | ❌ fail | Not a git repo |
| synthesize | ⏭️ skipped | Not configured |
| extract | ✅ ok | 0 links, 0 timeline entries from 7 pages |
| extract_facts | ✅ ok | 0 facts |
| propose_takes | ✅ ok | 7 pages scanned, 0 proposals (Anthropic key missing) |
| recompute_emotional_weight | ✅ ok | 7 pages recomputed |
| **embed** | ❌ fail | `--no-embedding` deferred setup — no model configured |
| orphans | ⚠️ warn | 7 orphan pages (100%) |
| purge | ✅ ok | Nothing to purge |

All LLM-dependent phases (propose_takes, grade_takes, extract_facts) warn about missing API keys but skip gracefully — no crash.

## Key Takeaways

1. **`init --pglite --no-embedding` produces a fully working brain** — PGLite, schema migration, default scaffolding all succeed. The only blocked phase is `embed` (expected — it requires a model).

2. **The brain dir starts with 7 default pages** — not zero. The dream reports 100% orphans because there are no internal links.

3. **Sync needs git** — `gbrain sync` fails with `Not a git repository`. Fix: `cd brain && git init && git add -A && git commit -m "initial"`.

4. **No API keys needed for filesystem phases** — lint, backlinks, extract, orphans, purge all work without any LLM or embedding keys.

5. **Hidden credentials risk** — The init created default `identity.md` with username `garry` (gbrain default). If the user doesn't overwrite `identity.md`, the dream exposes a wrong identity in logs. Check and rewrite `identity.md` for new users.

## Follow-up: Jul 4 2026 Dream

Cron job invoked dream on the existing brain at the Telegram ID path `ndr` using direct HOME (no `.gbrain-writable`):

```sh
HOME=/data/hermes/users/ndr /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/ndr/brain
```

**Key findings:**
- **Direct HOME works** — the default-path `.gbrain/` config is hermes-owned and readable, so no `.gbrain-writable` redirect was needed. The bun binary at `/data/hermes/home/.local/bin/bun` (Tier 0.5) worked directly — no npx or npm needed.
- **`--no-embedding` confirmed** — embed phase failed with: `"This brain was initialized with --no-embedding (deferred setup)."` matching the init config.
- **Sync still fails** — brain dir has no git repo (`"Not a git repository"`). Still needs `git init` if sync is desired.
- **`garry` identity still present** — propose_takes showed `"holder=garry"` in calibration_profile output, confirming identity.md was never rewritten.
- **All non-DB phases ok** — lint, backlinks, extract, extract_facts, resolve_symbol_edges, recompute_emotional_weight (7 pages), consolidate, purge all reported ok/warn.
- **Propose_takes had 7 extractor failures** — all due to missing `ANTHROPIC_API_KEY` (expected — no LLM key configured).
- **Duration**: 794ms — very fast since no embedding and no git sync.
- **Bun path used**: `/data/hermes/home/.local/bin/bun` — not `npx --yes bun`. This is the permanent install at the user's home directory and persists across cron runs.
