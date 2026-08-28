# Quick-reference: when to try vault bypass vs. generate new auth URL

## Symptom: `build_service()` raises `FileNotFoundError`

| Situation | Action |
|-----------|--------|
| User never authorized | Generate auth URL via `get_auth_url()` from terminal, send to user |
| User authorized but vault might have token | **Try vault bypass first!** Load vault client → `has_token(tid, 'google')` → if True, use bypass pattern |
| `has_token()` returns False | Generate new auth URL |
| Vault returns `Unauthorized` | Override `HERMES_SESSION_USER_ID` to correct Telegram ID before any vault call |

## Decision tree

```
build_service() raises FileNotFoundError
  → vault_is_available()?
    → No → system issue (daemon not running), contact admin
    → Yes → has_token(telegram_id, 'google')?
      → Yes → use vault bypass (references/gws-vault-bypass.md)
      → No → generate auth URL via terminal(), send to user
```