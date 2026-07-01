"""
Per-user Google Workspace OAuth token manager — multi-account edition.

Tokens are stored in the Token Vault daemon (gws-vault-server), keyed by:
  {user_id}/{service_key}.json

where service_key is:
  "google"            — primary Google account (default, backward-compatible)
  "google-{label}"    — secondary Google account, label is a short user-defined
                        name such as "gmail", "ahfl", "work"

All token access goes through:
  tools/gws_vault_client.py → Unix socket → daemon → /opt/gws-vault/tokens/

## Design principles

1. The user identity is ALWAYS read from the session context
   (HERMES_SESSION_USER_ID, injected by the gateway for every request).
   It is NEVER accepted as a parameter from LLM tool calls.

2. The LLM-facing tool (gws_vault_tool.py / schema name "token_auth") provides:
     - check    → is the current session user authorized?
     - authorize → give me a URL the user should open
     - list     → what services/accounts are connected?
     - revoke   → delete a specific token
   The LLM never sees raw tokens; it never specifies which user to act on.

3. The OAuth callback (exchange_and_store) is called by the HTTP callback route
   at /gws/auth/callback after Google redirects back. The state parameter
   encodes "{user_id}|{service_key}" — both set server-side when the URL
   was generated for the current authenticated session user.

4. Multi-account permission gate:
   Authorizing a secondary Google account (service_key != DEFAULT_SERVICE)
   requires permissions.multi_google=true in the user's registry entry.
   This check is enforced in gws_vault_tool.py, not here.

Usage from skill code (terminal subprocesses or execute_code):
    from tools.gws_auth import build_service
    svc = build_service("gmail", "v1")                    # primary account
    svc = build_service("gmail", "v1", "google-gmail")    # secondary account
    svc = build_service("calendar", "v3")
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

# Default / primary Google service key (backward-compatible)
DEFAULT_SERVICE = "google"

# Valid secondary service key label: lowercase alphanumeric + hyphens, 1–40 chars
_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,39}$")

# Scopes granted to every authorized Google account
HERMES_GWS_SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/spreadsheets",
]

_REDIRECT_URI = "https://transcribe.ahfl.in/gws/auth/callback"

# Separator used in the OAuth state parameter to encode both user_id and
# service_key.  Must not appear in email addresses or service key names.
_STATE_SEP = "|"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _validate_service_key(service_key: str) -> str:
    """Normalise and validate a vault service key.

    - "google" is always valid (primary).
    - "google-{label}" is valid when label matches _LABEL_RE.
    - Bare labels (no "google-" prefix) are accepted and prefixed automatically.
    Raises ValueError on invalid input.
    """
    sk = service_key.strip().lower()
    if sk == DEFAULT_SERVICE:
        return sk
    if sk.startswith("google-"):
        label = sk[len("google-"):]
        if not _LABEL_RE.match(label):
            raise ValueError(
                f"Invalid Google account label {label!r}. "
                "Use lowercase letters, digits and hyphens only (1–40 chars)."
            )
        return sk
    # Bare label provided — prefix it
    if _LABEL_RE.match(sk):
        return f"google-{sk}"
    raise ValueError(
        f"Invalid service key {service_key!r}. "
        "Use 'google' for primary or 'google-<label>' for secondary accounts."
    )


def _encode_state(user_id: str, service_key: str) -> str:
    """Encode user_id + service_key into the OAuth state parameter."""
    return f"{user_id}{_STATE_SEP}{service_key}"


def decode_state(state: str) -> tuple[str, str]:
    """Parse the OAuth state parameter back into (user_id, service_key).

    Backward-compatible: states without a separator are treated as
    legacy user_id-only states with service_key="google".
    """
    if _STATE_SEP in state:
        user_id, service_key = state.split(_STATE_SEP, 1)
        return user_id.strip(), service_key.strip() or DEFAULT_SERVICE
    return state.strip(), DEFAULT_SERVICE


# ---------------------------------------------------------------------------
# Session identity — ALWAYS from context, NEVER from LLM arguments
# ---------------------------------------------------------------------------

def _current_user_id() -> str:
    """Return the canonical user ID (primary email) for the current request.

    Reads HERMES_SESSION_USER_ID, injected by the gateway. Never accepts
    user identity as a parameter — this is architecturally enforced.
    """
    try:
        from gateway.session_context import get_session_env
        uid = get_session_env("HERMES_SESSION_USER_ID", "").strip()
    except Exception:
        uid = ""
    if not uid:
        uid = os.environ.get("HERMES_SESSION_USER_ID", "").strip()
    if not uid:
        raise ValueError(
            "HERMES_SESSION_USER_ID is not set for this request. "
            "Cannot determine which user's Google token to use. "
            "Via OpenUI/API: ensure X-Hermes-User-Email or X-Hermes-User-Id "
            "is sent in the request header. Via Telegram: this is injected automatically."
        )
    return uid


# ---------------------------------------------------------------------------
# OAuth client config
# ---------------------------------------------------------------------------

def _client_config() -> dict:
    client_id = os.environ.get("HERMES_OAUTH_CLIENT_ID", "")
    client_secret = os.environ.get("HERMES_OAUTH_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise EnvironmentError(
            "HERMES_OAUTH_CLIENT_ID and HERMES_OAUTH_CLIENT_SECRET must be set"
        )
    return {
        "web": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": [_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


# ---------------------------------------------------------------------------
# Credential management — vault-backed, session-identity only
# ---------------------------------------------------------------------------

def load_credentials(service_key: str = DEFAULT_SERVICE):
    """Load Google OAuth credentials for the current session user from the vault.

    Args:
        service_key: Vault service key — "google" (primary) or "google-{label}"
                     for a secondary Google account. Defaults to primary.

    Raises:
        ValueError        — HERMES_SESSION_USER_ID not set
        FileNotFoundError — no token; user must authorize
        PermissionError   — vault refused (cross-user block)
        RuntimeError      — vault unreachable
    """
    import json as _json
    from google.oauth2.credentials import Credentials
    from tools.gws_vault_client import (
        get_token, VaultNoTokenError, VaultUnauthorizedError,
    )

    sk = _validate_service_key(service_key)
    user_id = _current_user_id()

    try:
        token_json = get_token(user_id, sk)
    except VaultNoTokenError:
        raise FileNotFoundError(
            f"No Google token for user {user_id} (account: {sk}). "
            "Ask the agent to run `token_auth check` to get the authorization URL."
        )
    except VaultUnauthorizedError as exc:
        raise PermissionError(str(exc)) from exc
    except (ConnectionRefusedError, FileNotFoundError) as exc:
        raise RuntimeError(
            f"Token Vault daemon is not running ({exc}). "
            "Start it: systemctl start gws-vault"
        ) from exc

    creds = Credentials.from_authorized_user_info(_json.loads(token_json), HERMES_GWS_SCOPES)

    if creds.expired and creds.refresh_token:
        try:
            from google.auth.transport.requests import Request
            creds.refresh(Request())
            save_credentials(creds, sk)
        except Exception as exc:
            logger.warning(
                "Google token refresh failed for %s (account: %s): %s",
                user_id, sk, exc,
            )

    return creds


def save_credentials(creds, service_key: str = DEFAULT_SERVICE) -> None:
    """Store Google OAuth credentials for the current session user in the vault.

    Args:
        creds:       google.oauth2.credentials.Credentials object.
        service_key: Vault service key (see load_credentials).

    Called by load_credentials() after a successful token refresh. Never
    called directly with user-supplied arguments.
    """
    from tools.gws_vault_client import set_token
    sk = _validate_service_key(service_key)
    user_id = _current_user_id()
    try:
        set_token(user_id, sk, creds.to_json())
    except Exception as exc:
        raise RuntimeError(
            f"Failed to store Google credentials in vault "
            f"(user={user_id}, service={sk}): {exc}"
        ) from exc


def build_service(api: str, version: str, service_key: str = DEFAULT_SERVICE):
    """Build a Google API client for the current session user.

    Args:
        api:         e.g. "gmail", "calendar", "drive", "sheets", "people"
        version:     e.g. "v1", "v3", "v4"
        service_key: Which stored Google credential to use (default: primary).
                     Use "google-gmail", "google-ahfl" etc. for secondary accounts.

    The user identity is read from HERMES_SESSION_USER_ID — never passed as arg.
    """
    from googleapiclient.discovery import build
    creds = load_credentials(service_key)
    return build(api, version, credentials=creds)


def has_token(service_key: str = DEFAULT_SERVICE) -> bool:
    """Return True if the current session user has a stored token for service_key."""
    try:
        uid = _current_user_id()
    except ValueError:
        return False
    try:
        sk = _validate_service_key(service_key)
        from tools.gws_vault_client import has_token as vault_has_token
        return vault_has_token(uid, sk)
    except Exception:
        return False


def list_google_accounts() -> list[str]:
    """Return vault service keys for all Google accounts the current user has
    authorized, e.g. ["google", "google-gmail", "google-ahfl"].
    """
    try:
        uid = _current_user_id()
        from tools.gws_vault_client import list_services
        all_svcs = list_services(uid, session_uid=uid)
        return [s for s in all_svcs if s == DEFAULT_SERVICE or s.startswith("google-")]
    except Exception:
        return []


# ---------------------------------------------------------------------------
# OAuth flow — auth URL generation and token exchange
# ---------------------------------------------------------------------------

def get_auth_url(user_id: str, service_key: str = DEFAULT_SERVICE) -> str:
    """Generate an OAuth authorization URL for *user_id* / *service_key*.

    The URL encodes both the user_id and service_key in the OAuth state
    parameter so the callback knows where to store the token.

    For the primary account ("google"), sets login_hint to the user's primary
    email to pre-select the right Google account. For secondary accounts, no
    login_hint is set so the user can freely choose any Google account.

    Args:
        user_id:     Canonical user ID (primary email), from HERMES_SESSION_USER_ID.
        service_key: "google" or "google-{label}" for the target account slot.
    """
    from google_auth_oauthlib.flow import Flow

    sk = _validate_service_key(service_key)

    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        autogenerate_code_verifier=False,
    )

    auth_kwargs: dict = {
        "access_type": "offline",
        "prompt": "consent",
        "state": _encode_state(user_id, sk),
    }

    # For the primary account, hint at the user's registered email so Google
    # pre-selects the right account in the consent screen.
    if sk == DEFAULT_SERVICE:
        try:
            from tools._user_registry import get_user_config
            user = get_user_config(str(user_id))
            if user and user.get("email"):
                auth_kwargs["login_hint"] = user["email"]
        except Exception:
            pass

    url, _ = flow.authorization_url(**auth_kwargs)
    return url


def exchange_and_store(user_id: str, code: str, service_key: str = DEFAULT_SERVICE) -> None:
    """Exchange an OAuth authorization code for tokens and store them in the vault.

    Called EXCLUSIVELY by the HTTP callback route (_handle_gws_auth_callback in
    api_server.py) when Google redirects back after user consent.

    Args:
        user_id:     Internal user ID embedded in the OAuth state parameter.
        code:        Authorization code from Google's redirect.
        service_key: Vault service key extracted from the OAuth state parameter.
    """
    from google_auth_oauthlib.flow import Flow
    from tools.gws_vault_client import set_token

    sk = _validate_service_key(service_key)

    flow = Flow.from_client_config(
        _client_config(),
        scopes=HERMES_GWS_SCOPES,
        redirect_uri=_REDIRECT_URI,
        state=_encode_state(user_id, sk),
    )
    flow.fetch_token(code=code)
    set_token(user_id, sk, flow.credentials.to_json())
    logger.info("Google token stored in vault: user=%s service=%s", user_id, sk)
