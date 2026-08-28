# Nishant ndr — gbrain dream 2026-07-07

## Invocation

gbrain was NOT in PATH. Found via npm npx cache:

```sh
export PATH="/data/hermes/home/.npm/_npx/c26e5d3461431f82/node_modules/.bin:$PATH"
HOME=/data/hermes/users/ndr gbrain dream --json --dir /data/hermes/users/ndr/brain
```

The npx cache hash (`c26e5d3461431f82`) is NOT stable — do not hardcode. Use `find /data/hermes/home/.npm/_npx -name "gbrain" -type f | head -1` instead.

## Result summary

- Status: `partial` (846ms)
- **sync**: fail — not a git repo (expected, standalone PGLite brain)
- **embed**: fail — brain initialized with `--no-embedding` (deferred setup)
- **propose_takes**: ok but 0 proposals — all 7 extractors failed: "Anthropic chat requires ANTHROPIC_API_KEY"
- **recompute_emotional_weight**: ok — 7 pages recomputed
- **orphans**: warn — 7 of 7 pages are orphans

## Key observation: Anthropic dependency in propose_takes

The `propose_takes` phase uses **Anthropic Claude** (not OpenRouter) for LLM extraction. The error messages say "Anthropic chat requires ANTHROPIC_API_KEY" for every page. This is the same ANTHROPIC_API_KEY that lives at `/opt/hermes/.env` — gbrain doesn't inherit it because `bun run` creates a subprocess that doesn't read that file.

If ANTHROPIC_API_KEY were exported, propose_takes would produce take proposals (standalone facts extracted from brain pages). This is the mechanism by which gbrain turns raw markdown pages into actionable knowledge.

## Config status

- Config at default path: hermes-owned, `--no-embedding` (deferred setup)
- Embedding model: none configured (`embedding_disabled: true`)
- No git repo in brain dir (sync phase correctly skips)
- Default scaffolding: 7 pages (identity.md, readme.md, notes/readme.md, people/readme.md, projects/readme.md, people/roshni-ranka, person/roshni-ranka)