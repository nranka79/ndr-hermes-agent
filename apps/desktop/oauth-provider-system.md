# OAuth Provider System — Remaining Work

This documents the remaining steps after the admin panel UI and vault
permissions model are in place (Steps 1–2).

---

## Step 3 — Dynamic `EMAIL_TO_SERVICE` from vault

**File:** `tools/gws_auth.py`

Replace the hardcoded `EMAIL_TO_SERVICE` dict with a function that reads the
current user's `permissions.oauth_providers.google` list from their vault
identity record.

```python
# OLD: static dict
EMAIL_TO_SERVICE = {
    "ndr@draas.com": "google-draas",
    "nishantranka@gmail.com": "google-gmail",
    ...
}

# NEW: dynamic per-user lookup
def _resolve_google_service(email: str) -> str | None:
    """Return vault service key for *email* if user is authorized."""
    uid = canonical_uid(_current_telegram_id())
    identity = vault.get_identity(uid, session_uid=uid)  # or use vault_secret
    providers = ((identity or {}).get("permissions", {})
                 .get("oauth_providers", {}).get("google", []))
    if email in providers:
        return f"google-{email.split('@')[0]}"
    return None
```

### What needs to change

| Location | Change |
|---|---|
| `EMAIL_TO_SERVICE` dict (top of file) | Remove static dict. Keep `_DEFAULT_SERVICE = "google"` as fallback. |
| New function `_resolve_google_service(email)` | Query vault identity -> `permissions.oauth_providers.google` -> return service key |
| `exchange_and_store()` (callback handler) | Currently looks up `EMAIL_TO_SERVICE.get(email)`. Replace with `_resolve_google_service(email)`. If None -> raise `UnknownGoogleAccountError`. |
| `canonical_uid()` / `_current_telegram_id()` | Already resolves session user. The callback handler sets session vars from `state` (telegram_id) before calling `exchange_and_store()`, so `_current_telegram_id()` works. |

### Authorization gate in `exchange_and_store()`

After resolving the email from `id_token`:

1. Look up the session user's `permissions.oauth_providers.google`
2. If email is in the list -> store token under `google-{localpart}`
3. If not -> return error: "This Google account is not authorized for you. Ask your admin to add it."

### Edge cases

- User has no `oauth_providers` key yet (legacy users) -> allow any email
  (backward compat for existing users, they'll get the new behavior after
  the admin next saves their OAuth providers)
- User has `oauth_providers.google = []` -> deny all
- User has `oauth_providers.google = ["a@gmail.com"]` -> only that one

---

## Step 4 — `/oauth` Telegram slash command

**Files:** `hermes_cli/commands.py`, `gateway/run.py`, `gateway/slash_commands.py`,
`gateway/platforms/telegram.py`, new `tools/oauth_providers.py`

### 4a — Provider registry (`tools/oauth_providers.py`)

New module that discovers available OAuth providers and their status per user.

```python
PROVIDER_REGISTRY: dict[str, ProviderDef] = {}

ProviderDef = {
    "key": str,              # "google", "kelsa", etc.
    "label": str,            # "Google Workspace"
    "icon": str,             # "🔵"
    "check_token": callable, # (user_id) -> bool
    "get_auth_url": callable,# (user_id, force) -> str | None
}
```

Providers auto-discovered:
- **Google**: from `permissions.oauth_providers.google` (list of emails).
  Each email is a separate entry: `google-{localpart}`.
- **Kelsa**: from `permissions.oauth_providers.kelsa` (boolean).
- **Future**: Microsoft, Twitter, Facebook — check their respective flags.

### 4b — Command registration (`hermes_cli/commands.py`)

```python
CommandDef("oauth", "Manage SSO connections — list, connect, or re-authorize",
           "Tools & Skills", aliases=("sso", "auth"), args_hint="[provider] [--force]"),
```

### 4c — Gateway handler (`gateway/slash_commands.py`)

`_handle_oauth_command()`:
- No args: enumerate user's permitted providers with status badges
- With provider: show detail page (connected? -> re-auth button; not connected? -> connect button)
- With `--force`: always generate fresh auth URL

### 4d — Telegram inline keyboard (`telegram.py`)

Callback prefix: `oau:` (e.g. `oau:google-draas`, `oau:kelsa`).

Pattern follows existing model-picker pattern:
- `_handle_oauth_callback()` dispatches on `oau:` prefix
- Provider list rendered as buttons with status emoji
- Single-provider view shows Connect/Re-auth/Back buttons

### 4e — Dispatch in `gateway/run.py`

Wire `canonical == "oauth"` into the if/elif chain around existing commands.

### Security

- Identity comes from session context only (same pattern as `send_oauth_url`)
- The LLM never generates OAuth URLs — the command handler does it
- Only providers the user is authorized for (by admin) are shown

---

## Step 5 — Future provider onboarding

When adding a new provider (e.g. Microsoft 365):

| File | Change |
|---|---|
| `admin-app/app/users.py` | Add `microsoft` to oauth_providers in the update handler |
| `admin-app/app/templates/user_detail.html` | Enable the Microsoft toggle (remove `disabled`, add live status) |
| `tools/oauth_providers.py` | Register the new provider (auth URL builder, token checker) |
| `gateway/platforms/api_server.py` | Add callback route: `/microsoft/auth/callback` |
| Provider library | New file `tools/microsoft_auth.py` (or similar) |

The admin panel and `/oauth` command auto-discover providers registered in
`tools/oauth_providers.py` — no additional wiring needed.

---

## Timeline

| Step | Effort | Depends on |
|---|---|---|
| 3 — Dynamic EMAIL_TO_SERVICE | ~2h | Steps 1-2 deployed |
| 4 — `/oauth` command | ~4h | Step 3 |
| 5 — New providers | varies per provider | Step 4 (pattern established) |