# Roshini Ranka (rnr) — Dream Run, 2026-07-14

## Summary

Cron target `uid=[REDACTED-TID]` is the **stale Telegram-ID path**. The literal command
`HOME=/data/hermes/users/[REDACTED-TID] gbrain dream --json --dir /data/hermes/users/[REDACTED-TID]/brain`
fails with `gbrain: command not found` (exit 127). The directory exists but has only
`.bun/` cache — no `brain/`, no `.gbrain/config.json`.

**Working invocation** (fallback to DRAAS account path):

```sh
GBRAIN_HOME=/data/hermes/users/rnr/.gbrain-writable \
  HOME=/data/hermes/users/rnr \
  /data/hermes/home/.local/bin/bun /opt/gbrain/src/cli.ts dream \
    --json --dir /data/hermes/users/rnr/brain-copy
```

`brain-copy` is preferred over `brain` here: `brain/` is root-owned and has no git
commits, so `sync` fails with `No commits in repo`. `brain-copy/` is hermes-owned
with 2 commits — sync runs cleanly. `safe.directory` for both paths is set in
`/data/hermes/home/.gitconfig` already.

## Dream results (Jul 14 2026, 01:41 UTC)

- **status:** `partial`
- **duration_ms:** 450
- **brain_dir:** `/data/hermes/users/rnr/brain-copy`
- **embedding_model:** `minimax:embo-01` (configured, in `.gbrain-writable/.gbrain/config.json`)

Phase breakdown:

| Phase | Status | Detail |
|---|---|---|
| lint | warn | 0 fix(es) applied, 1 remaining |
| backlinks | ok | no missing back-links |
| **sync** | **ok** | +0 added, ~0 modified, -0 deleted |
| synthesize | skipped | `dream.synthesize.session_corpus_dir` is unset |
| extract | ok | 0 links, 0 timeline entries (incremental: 0 slugs) |
| extract_facts | ok | 0 facts reconciled across 0 pages |
| extract_atoms | skipped | active pack does not declare this phase |
| resolve_symbol_edges | ok | no chunks needed symbol resolution |
| patterns | skipped | 0 reflections in last 30d (need ≥3) |
| synthesize_concepts | skipped | active pack does not declare this phase |
| recompute_emotional_weight | ok | incremental, 0 slugs |
| consolidate | ok | 0 facts → 0 takes across 0 buckets |
| propose_takes | ok | scanned 7 pages, 0 cached, 0 new proposals |
| grade_takes | ok | 0 takes scanned |
| calibration_profile | ok | holder=garry, 0 resolved takes |
| conversation_facts_backfill | skipped | feature flag off |
| enrich_thin | skipped | feature flag off |
| skillopt | skipped | feature flag off |
| **embed** | **fail** | `Embedding model "minimax:embo-01" requires MINIMAX_API_KEY` |
| orphans | warn | 7 orphan page(s) out of 7 total |
| schema-suggest | ok | 0 suggestions emitted |
| purge | ok | purged 0 sources, 0 pages |

## Embed failure: not a 429 — missing env var

The user message asked to "note [a rate limit on embed] and skip gracefully." The
actual failure is **not a 429 rate limit** — it's `Embedding model "minimax:embo-01"
requires MINIMAX_API_KEY. Set it in your shell...` Per the SKILL.md Platform
Limitations table, the MiniMax key is ALSO exhausted at the provider (Token Plan
limit), so embedding is blocked regardless. Practical outcome identical: no embedding
happens, no retry attempted. Report the env-var error to the cron log so the user
sees the actual cause (not a misleading "rate limit" framing).

## Default-scaffold fingerprint confirmed

`propose_takes: scanned 7 pages, 0 cached, 0 new proposals` +
`calibration_profile: holder=garry` + `7 orphans out of 7 total` = the 7-page
default scaffold from `init --pglite` (`identity.md` + 6 readmes in
`notes/`, `people/`, `projects/`, and two `person/`/`people/` roshni-ranka
templates). The real `identity.md` is on disk but the brain has zero extracted
content, zero takes, zero facts. Knowledge extraction pipeline gap still applies.

## New technique: stripping log prefix from `--json` output

Even with `--json` and `2>/dev/null`, gbrain emits 1–2 log lines BEFORE the JSON
on stdout:

```
Links: created 0 from 1 pages
Timeline: created 0 entries from 1 pages
{
  "schema_version": "1",
  ...
}
```

Naïve pipe `... 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin)"`
fails with `JSONDecodeError: Expecting value: line 1 column 1 (char 0)`.

**Fix:** strip everything before the first `{` before parsing:

```sh
... 2>/dev/null | awk '/^\{/{found=1} found{print}' | python3 -c "import json,sys; d=json.load(sys.stdin); ..."
```

The `awk` anchor `^\{` finds the line starting with `{` (the JSON object) and prints
that line plus everything after. Drops all preceding log lines. Apply this to every
`dream --json` cron pipeline.

## Cross-references

- `references/cron-literal-command-recipes.md` — Roshini working invocation block
- Main SKILL.md → Pitfalls: `--json output is prefixed with log lines, breaks naïve json.loads pipe` (added Jul 14 2026)
