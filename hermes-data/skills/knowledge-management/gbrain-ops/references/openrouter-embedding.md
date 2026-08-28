# OpenRouter as gbrain Embedding Provider

## Summary

gbrain's OpenRouter recipe (`src/core/ai/recipes/openrouter.ts`) supports embedding via `/v1/embeddings`, proxying OpenAI's `text-embedding-3-small` (1536 dims). This is the recommended alternative to MiniMax `embo-01` whose key is exhausted (429).

## Prerequisite

`OPENROUTER_API_KEY` must be exported in the environment that runs gbrain. In the DRAAS Hermes deployment, this env var is NOT set in the shell or in `/data/hermes/.env`. The key IS available at `/data/hermes/users/<uid>/.openrouter_key` — Hermes uses it internally for OpenRouter model calls (Claude, Gemini) and it authenticates successfully. But gbrain can't see it because gbrain reads from `process.env` not from the filesystem.

## The Credential Delivery Gap

This is the critical finding from Jun 2026:

- **Hermes** reads the key directly from `/data/hermes/users/<uid>/.openrouter_key` when making OpenRouter API calls (e.g. vision via `google/gemini-2.5-flash`, deep thinking via `anthropic/claude-sonnet-4-20250514`). The user sees usage on their OpenRouter dashboard.
- **gbrain** is a standalone `bun run` subprocess. It reads credentials from `process.env`, specifically `OPENROUTER_API_KEY`. It does NOT check the `.openrouter_key` file. gbrain's OpenRouter recipe declares `required: ['OPENROUTER_API_KEY']`.
- **auth.json** registers the OpenRouter credential as `source: 'env:OPENROUTER_API_KEY'` with `last_status: 'ok'`, but this credential pool entry is NOT automatically exported as an actual shell env var.

**The gap**: the key exists, the key works, but it's not delivered to gbrain's subprocess environment.

## Fix: Export the Key

```sh
# Option A: One-time export (session-scoped)
export OPENROUTER_API_KEY=$(cat /data/hermes/users/<uid>/.openrouter_key)

# Option B: Persist in .env (permanent)
echo "OPENROUTER_API_KEY=$(cat /data/hermes/users/<uid>/.openrouter_key)" >> /data/hermes/.env

# Verify it's now available
echo "OPENROUTER_API_KEY in env: $([ -n \"$OPENROUTER_API_KEY\" ] && echo YES || echo NO)"
```

## Switching to OpenRouter Embedding

After exporting the key:

```sh
# 1. Verify OPENROUTER_API_KEY is set
echo "Key set: $([ -n \"$OPENROUTER_API_KEY\" ] && echo YES || echo NO)"

# 2. Switch embedding model
GBRAIN_HOME=/data/hermes/users/<uid>/.gbrain-writable \
bun run /opt/gbrain/src/cli.ts config set embedding_model openrouter:openai/text-embedding-3-small

# 3. Run embed to populate vectors
GBRAIN_HOME=/data/hermes/users/<uid>/.gbrain-writable \
bun run /opt/gbrain/src/cli.ts embed --stale
```

## Cost Comparison

| Provider | Model | Cost/1M tokens | Status |
|---|---|---|---|
| MiniMax | embo-01 | $0.07 | Exhausted (429) |
| OpenRouter | text-embedding-3-small | $0.02 | Key exists, not exported as env var |
| OpenCodeGo | N/A | N/A | No embedding models available |

## Key Validation

To verify the stored OpenRouter key is valid (it should be — Hermes uses it successfully):

```sh
OR_KEY=$(cat /data/hermes/users/<uid>/.openrouter_key)
curl -s https://openrouter.ai/api/v1/auth/key \
  -H "Authorization: Bearer $OR_KEY" \
  -H "HTTP-Referer: https://gbrain.ai" | python3 -c "
import sys, json
d = json.load(sys.stdin)
if 'data' in d:
    print('OK - label:', d['data'].get('label','unknown'), '| limit:', d['data'].get('limit',0), '| usage:', d['data'].get('usage',0))
else:
    print('FAIL:', d.get('error',{}).get('message','unknown'))
"
# Expected on success: OK - label: <name> | limit: <number> | usage: <number>
# Expected on failure: FAIL: User not found.
```

## Verification After Setup

After switching, `gbrain doctor` should show:
```
[OK] embedding_provider: openrouter:openai/text-embedding-3-small
```

And `gbrain embed --stale` should produce vectors (no more "no provider credentials" warning).

## Relevant gbrain Source

- OpenRouter recipe: `src/core/ai/recipes/openrouter.ts`
- Gateway embedding dispatch: `src/core/ai/gateway.ts` (via AI SDK `embed()`)
- Model resolver: `src/core/ai/model-resolver.ts` (parses `provider:model` strings)
- Build gateway config: `src/core/ai/build-gateway-config.ts` (folds env vars into gateway config)
- Credential pools: `auth.json` (Hermes credential store, not gbrain-specific)
