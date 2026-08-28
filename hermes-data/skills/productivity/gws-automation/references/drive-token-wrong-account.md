# Drive Token — Wrong Account Detection

**Scenario:** Vault shows `has_token: true` for the expected email (e.g., `google-draas` → `ndr@draas.com`). `build_service()` returns a usable service object. API calls succeed. **But** the token was issued to a **different Google account** (e.g., `psingh@draas.com` not `ndr@draas.com`).

This is **more dangerous** than a dead/expired token because:
- Dead token: API calls fail with `RefreshError` → immediately obvious
- **Wrong account:** API calls succeed but read/write the **wrong user's Drive** → silent data corruption

## Real-world example (Jul 2026)

For DRAAS, the `google-draas` service_name:
- Vault maps it to: `ndr@draas.com` ✅ (looks correct)
- Vault reports: `has_token: true` ✅ (looks healthy)
- **Actual token owner:** `psingh@draas.com` ❌ (Prakash Singh's account)

All `drive_search`, `drive_create_folder`, `drive_upload` operations silently operate on Prakash's Drive root instead of Nishant's.

## Root Cause

During OAuth authorization, the user may have:
- Logged in with a different Google account than intended
- Had the browser auto-fill/auto-login with credentials from a different session
- Selected the wrong profile from the Google account picker

The vault only stores what the OAuth flow returns — it has no way to verify the email matches what was expected until you actually check the Drive root.

## The One-Line Verification

**Always verify token ownership before any Drive operations by checking the Drive root owner:**

```python
from gws_skill_bridge import call
import json

# Check who the token actually belongs to — NOT who the vault says
r = call('drive_get', service_name='google-draas', file_id='root')
data = json.loads(r) if isinstance(r, str) else r
actual_owner = data.get('owners', [{}])[0].get('emailAddress', 'unknown')
print(f"Token belongs to: {actual_owner}")
# Expected: ndr@draas.com
# Actual (if wrong): psingh@draas.com
```

**The Drive root's owner IS the account the token was issued to.** This never lies.

## Full Verification Routine

```python
from gws_skill_bridge import call
import json

def verify_gws_token(service_name, expected_email):
    """Verify the token for service_name actually belongs to expected_email.
    Returns (is_valid, actual_owner, details)"""
    try:
        r = call('drive_get', service_name=service_name, file_id='root')
        data = json.loads(r) if isinstance(r, str) else r
        actual = data.get('owners', [{}])[0].get('emailAddress', 'unknown')
        is_valid = (actual == expected_email)
        return is_valid, actual, data
    except Exception as e:
        return False, str(e), None

# Usage
valid, owner, _ = verify_gws_token('google-draas', 'ndr@draas.com')
if not valid:
    print(f"⚠️ Token mismatch! Expected ndr@draas.com, got {owner}")
    print(" → User needs to re-authorize with the correct account")
```

## Fix: Re-authorize with the Correct Account

Send a fresh OAuth URL with `login_hint` set to the correct email:

```python
# Use the send_oauth_url tool (in a script, not via execute_code nesting)
# send_oauth_url(login_hint='ndr@draas.com', service_name='google-draas')
# This generates a button/link for the user to tap
```

The `login_hint` pre-fills the email field on Google's login page, making it more likely the user picks the right account.

## Relationship to Other Checks

| Problem | Symptom | Detection |
|---|---|---|
| **Dead token** (expired/revoked) | API calls throw `RefreshError` | `gws-dead-token-verification-flow.md` |
| **Wrong account** (different owner) | API calls succeed, wrong Drive | This file — check Drive root owner |
| **No token** | `build_service` raises `FileNotFoundError` | `gws_resolve_account` → `has_token: false` |
