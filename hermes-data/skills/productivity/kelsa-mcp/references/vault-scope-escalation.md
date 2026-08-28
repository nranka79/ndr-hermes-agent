# ✅ RESOLVED — Kelsa Vault OAuth Scope (2026-07-20)

**This issue is no longer reproducible.** The scope in `tools/kelsa_auth.py` was widened from `mcp:read` to `mcp:read mcp:write mcp:design` on **2026-07-20** (line 141). All new authorizations grant full read + write + design access in a single grant.

## What changed

| Before (2026-07-19) | After (2026-07-20) |
|---|---|
| `SCOPE = "mcp:read"` | `SCOPE = "mcp:read mcp:write mcp:design"` |
| Write ops failed with scope error | Write ops succeed after authorization |
| Required workaround: generate custom auth URL with expanded scope | No workaround needed — use normal `kelsa_login` flow |

## If legacy `mcp:read`-only tokens exist

Have the user re-authorize via the normal `kelsa_login` flow. The new auth overwrites the old token with the full scope.

## Historical context (kept for reference)

The old workaround (generating a custom auth URL with `mcp:read mcp:write` scope via `_get_or_register_client()` + manual PKCE generation) is preserved in the git history of this file but no longer needed. Do not use `references/vault-scope-escalation.md` as a reference for current auth flows — the standard flow in `references/kelsa-oauth-setup.md` or `SKILL.md#OAuth-Authentication` is sufficient.
