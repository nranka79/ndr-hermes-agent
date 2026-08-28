# PGLite WASM Runtime Failure

## Status

**⚠️ This failure mode has been resolved.** As of gbrain 0.42.x with the `.gbrain-writable` workaround (hermes-owned config initialized via `init --pglite`), PGLite initializes successfully on this Linux host. All DB-backed phases run normally — only `embed` remains blocked by missing API keys.

The transcript below is retained for reference in case the failure reappears under different conditions (root-owned config, older gbrain, different bun version).

## Observed error (2026-06-17, Linux 6.8.0-124-generic)

When running `gbrain dream` with PGLite engine from a root-owned `.gbrain/` config directory:

```
[dream] WARNING: could not connect to DB (PGLite failed to initialize its WASM runtime.
  Most common cause: the macOS 26.3 WASM bug
  (https://github.com/garrytan/gbrain/issues/223).
  Run `gbrain doctor` for a full diagnosis.
  Original error: Aborted(). Build with -sASSERTIONS for more info.). Running filesystem-only phases (lint, backlinks, extract). DB-dependent phases (sync, embed, synthesize, etc.) will report as skipped.
```

## Impact

- All DB-backed phases: `skipped` (reason: `no_database`)
- Only `lint` and `backlinks` filesystem phases execute
- `status` in dream JSON is always `"partial"`

## Full dream JSON output (representative)

```json
{
  "schema_version": "1",
  "status": "partial",
  "phases": [
    {"phase": "lint", "status": "warn"},
    {"phase": "backlinks", "status": "ok"},
    {"phase": "sync", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "synthesize", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "extract", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "extract_facts", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "extract_atoms", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "resolve_symbol_edges", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "patterns", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "synthesize_concepts", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "recompute_emotional_weight", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "consolidate", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "propose_takes", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "grade_takes", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "calibration_profile", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "conversation_facts_backfill", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "enrich_thin", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "skillopt", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "embed", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "orphans", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "schema-suggest", "status": "skipped", "details": {"reason": "no_database"}},
    {"phase": "purge", "status": "skipped", "details": {"reason": "no_database"}}
  ],
  "totals": {
    "pages_synced": 0,
    "pages_embedded": 0,
    "pages_extracted": 0,
    "lint_fixes": 0,
    "backlinks_added": 0
  }
}
```

## Configuration used

- Engine: `pglite`
- Config path: `/data/hermes/users/<uid>/.gbrain/config.json`
- Config contents: `{"engine": "pglite", "database_path": ".../brain.pglite", "embedding_model": "minimax:embo-01", "embedding_dimensions": 1536, "provider_base_urls": {"minimax": "http://localhost:8765/v1"}}`
- gbrain source: `/opt/gbrain` (TypeScript CLI)
- Runtime: `npx --yes bun run /opt/gbrain/src/cli.ts`
- OS: Linux 6.8.0-124-generic

## WAL-repair false-positive on Bharat (sales1.blr), Aug 17 2026

New failure signature: PGLite corrupt beyond WAL repair, where `pglite-repair --yes`
**reports success but the DB still aborts** on the next open.

- Symptom: dream logs `PGLite failed to initialize its WASM runtime … Original error: Aborted(). Build with -sASSERTIONS for more info.`; auto-repair fails repeatedly (4+ attempts on record over 3 days, cooldown 3600s between auto attempts); `pglite-repair --dry-run` says `wal-corruption-likely` + `Repairable: yes`.
- `gbrain pglite-repair --yes` prints `WAL reset complete.` with a fresh backup — but the NEXT `gbrain dream` still fails with the identical WASM abort. **The repair resets WAL, not the underlying DB state that makes the WASM runtime abort.** Always verify a repair with a re-run of dream (or `gbrain doctor`) before trusting it.
- Real fix (verified Aug 17 2026 on Bharat/sales1.blr): `HOME=<user>/.gbrain-writable gbrain reinit-pglite --yes --no-sync` — wipes the corrupt DB, applies 120 migrations cleanly, embedding live-check passes (openrouter:openai/text-embedding-3-small, 1536d), old DB preserved as `brain.pglite.bak`. Then `gbrain dream --json --dir <user>/brain-copy` reimports from the git repo (sync ok, 1 page) and embeds (1 chunk). Reinit defaults read the config file, so the OpenRouter embed target is picked up automatically; no flags needed.
- No rate-limit issue: OpenRouter embed works; the only skipped phase is propose_takes (no ANTHROPIC_API_KEY — non-blocking, status stays `partial`).
- Pitfall for background/cron shells: `gbrain` is NOT on PATH in background processes — use the full wrapper `/data/hermes/home/.local/bin/gbrain`.

### Auto-repair cooldown trap (Aug 18 2026, Vinod vkdas)

After a manual `pglite-repair --yes` succeeds, the next `gbrain dream` still fails with:
```
[dream] WARNING: could not connect to DB … Auto-repair skipped: last auto-repair attempt failed <N>s ago (cooldown 3600s)
```

The auto-repair cooldown is **per-process** and counts from the last *auto-repair attempt* (not the manual `pglite-repair`). If dream's auto-repair was triggered on a prior run within 3600 seconds, it defers even though the manual repair already fixed the WAL.

**Workaround:** Bypass the cooldown with the env var:
```sh
GBRAIN_PGLITE_WAL_REPAIR_COOLDOWN_SECONDS=0 gbrain dream --dir /path/to/brain-copy
```

If even that fails (auto-repair runs, restores pre-repair state, but PGLite still aborts), the corruption is beyond WAL — proceed directly to `reinit-pglite` (next section).

### `reinit-pglite` as side-effect embed fix

When `reinit-pglite` rebuilds the PGLite database, it reads the **config file's** embedding model and dimensions. If the config uses an embedder whose API key is available in the environment (e.g. `openrouter:openai/text-embedding-3-small` with `OPENROUTER_API_KEY` set), subsequent `gbrain dream` invocations will pass the embed phase — even if the pre-reinit brain was failing on a different embedder's missing key (e.g. `minimax:embo-01` needing `MINIMAX_API_KEY`). This is a side-effect, not the primary purpose of reinit, but it can resolve long-standing embed failures.

## Cross-reference

- Upstream issue: https://github.com/garrytan/gbrain/issues/223 (the referenced "macOS 26.3 WASM bug" — occurs on Linux too)
- The "macOS 26.3" reference in the error message appears to be a misclassified error path in gbrain's WASM detection; the actual failure occurs on this Linux kernel as well.
