# Nishant ndr — Dream Run 2026-07-06

## Invocation
```
HOME=/data/hermes/users/ndr bun /opt/gbrain/src/cli.ts dream --json --dir /data/hermes/users/ndr/brain
```
Note: used direct bun path (`/data/hermes/home/.local/bin/bun`), not `npx --yes bun`. No PATH issue since full path was used.

## Result
- **Duration**: 744ms
- **Status**: `partial`
- **Brain state**: 7 pages (default scaffolding from `init --pglite --no-embedding`)

## Phase-by-phase

| Phase | Status | Detail |
|---|---|---|
| lint | ok | 0 issues |
| backlinks | ok | 0 gaps |
| sync | **fail** | `Not a git repository: /data/hermes/users/ndr/brain`. Brain dir has 7 pages but no `.git/`. |
| synthesize | skipped | `dream.synthesize.session_corpus_dir` unset |
| extract | ok | 0 links, 0 timeline entries |
| extract_facts | ok | 0 facts, 2 phantoms scanned |
| resolve_symbol_edges | ok | no chunks |
| patterns | skipped | <3 reflections in last 30d |
| recompute_emotional_weight | ok | 7 pages |
| consolidate | ok | 0 takes |
| propose_takes | ok (warn) | 7 pages scanned, 0 proposals. 7 warnings: `extractor failed on [page]: Anthropic chat requires ANTHROPIC_API_KEY` |
| grade_takes | ok | 0 takes |
| calibration_profile | ok | insufficient data (0 resolved takes) |
| embed | **fail** | `This brain was initialized with \`--no-embedding\` (deferred setup). Configure an embedding provider before running embed / import`. Config has `embedding_disabled: true`. |
| orphans | warn | 7 orphans out of 7 pages (all pages) |
| schema-suggest | ok | 0 suggestions |
| purge | ok | 0 purged |

## Key observations
- **Default scaffolding pages present** after `init --pglite --no-embedding`: identity.md (username `garry` — not rewritten), readme.md, notes/readme.md, people/readme.md, projects/readme.md, people/roshni-ranka, person/roshni-ranka.
- **`--no-embedding` config confirmed**: `embedding_disabled: true`, no `embedding_model` key. Embed phase fails with the deferred-setup message (not a model-name message). This is the expected outcome for deferred embedding.
- **No git repo**: Brain has never had `git init` run. Sync phase is blocked. Once `git init` + initial commit are done, sync will import the 7 scaffolding pages.
- **Config ownership**: Default-path `.gbrain/` at `/data/hermes/users/ndr/.gbrain/` is hermes-owned, so direct `HOME=` works without `.gbrain-writable` redirect. No EACCES issues, no schema migration failures.
- **Bun binary**: Used `/data/hermes/home/.local/bin/bun` (v1.3.14) — found at the permanent install location. No npx/npm overhead.
