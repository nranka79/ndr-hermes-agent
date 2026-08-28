"""GWS multi-account resolver.

Root-cause fix for the recurring "vault has no token" false alarm: the
model has no reliable way to know the exact vault ``service_name`` slug for
a given Google account (``google-draas`` / ``google-ahfl`` / ``google-gmail``
-- see ``tools/gws_auth.py`` EMAIL_TO_SERVICE), so it has been hand-typing
guesses (e.g. the raw email address) via execute_code/terminal. A wrong
service_name looks *exactly* like "not authorized" even when the real token
exists under the correct key, and the model then wrongly tells the user the
vault daemon is down and/or generates unnecessary re-auth links.

This tool makes that lookup deterministic and callable directly -- no more
hand-typed slugs. Call it with no arguments to list every known service and
whether each currently has a stored token, showing your own email for each
service you have a token for. Call it with an ``account`` (email address or
short label like "draas"/"ahfl"/"gmail"/"personal") to resolve a single one.

Once you have the ``service_name`` back, use it directly in execute_code:
    from tools.gws_auth import build_service
    svc = build_service("gmail", "v1", service_name="google-draas")
"""

import json
import re

from tools.registry import registry, tool_error, tool_result

# Short, human-typeable aliases -> vault service names.
# Unlike _ALIAS_TO_EMAIL which pinned a specific email, these resolve directly
# to the service_name so the ownership check can use ANY of the session user's
# own emails that map to that service.
_ALIAS_TO_SERVICE = {
    "draas": "google-draas",
    "ahfl": "google-ahfl",
    "gmail": "google-gmail",
    "personal": "google-gmail",
}

_SERVICE_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,49}$")

GWS_RESOLVE_ACCOUNT_SCHEMA = {
    "name": "gws_resolve_account",
    "description": (
        "Resolve a Google account (email address or short label like "
        "'draas'/'ahfl'/'gmail'/'personal') to the exact vault service_name "
        "key needed by build_service()/has_token(), and report whether a "
        "token is currently stored for it. Call with no arguments to list "
        "ALL known services and their auth status at once -- use this "
        "before any 'search across my accounts' task instead of guessing.\n\n"
        "MANDATORY: this is the ONLY sanctioned way to determine a GWS "
        "vault service_name. Never guess it, never pass a raw email address "
        "as service_name, and never assume the vault is down just because "
        "a lookup with a guessed key came back empty -- call this tool "
        "first to get the real key."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "account": {
                "type": "string",
                "description": (
                    "Email address (e.g. 'ndr@draas.com') or short label "
                    "('draas', 'ahfl', 'gmail', 'personal'). Omit to list "
                    "every known service and its auth status."
                ),
            },
        },
        "required": [],
    },
}


def _current_telegram_id() -> str | None:
    from gateway.session_context import get_gws_identity_env
    tid = get_gws_identity_env().strip()
    return tid or None


def _user_service_emails(tid: str) -> dict[str, str]:
    """Return {service_name: user_email} for every service the session user
    has an email for in their vault identity.

    This lets the listing show the user's own email per service instead of
    a global default (e.g. ``ndr@draas.com`` for ``google-draas``) that was
    causing the model to tell a non-Nishant user "the token is for ndr@draas.com".
    """
    from tools.gws_auth import EMAIL_TO_SERVICE, canonical_uid
    from tools import gws_vault_client as vault
    uid = canonical_uid(tid)
    if not uid:
        return {}
    try:
        identity = vault.get_identity(uid, session_uid=uid)
    except Exception:
        return {}
    if not identity:
        return {}
    user_emails = identity.get("identities", {}).get("email", [])
    result = {}
    for email in user_emails:
        svc = EMAIL_TO_SERVICE.get(email.lower())
        if svc:
            result[svc] = email
    return result


def _resolve_one(account: str) -> dict:
    """Resolve a single account string to {email, service_name} or an error dict.

    Returns ``{"email": ..., "service_name": ...}`` when the input was a
    known email address (directly from ``EMAIL_TO_SERVICE``). Returns
    ``{"service_name": ...}`` (no fixed email) when the input was a short
    alias or a raw service name -- in those cases ownership is checked
    against any of the session user's own emails that map to that service.
    """
    from tools.gws_auth import EMAIL_TO_SERVICE

    raw = account.strip()
    key = raw.lower()

    # Already a known email.
    if key in EMAIL_TO_SERVICE:
        return {"email": key, "service_name": EMAIL_TO_SERVICE[key]}

    # Short alias -> service_name (no fixed email -- per-user resolution).
    if key in _ALIAS_TO_SERVICE:
        return {"service_name": _ALIAS_TO_SERVICE[key]}

    # Raw vault service_name -- pass through if recognised.
    if _SERVICE_NAME_RE.match(key) and key in set(EMAIL_TO_SERVICE.values()):
        return {"service_name": key}

    return {
        "error": (
            f"'{account}' is not a known GWS account. Known emails: "
            f"{sorted(EMAIL_TO_SERVICE.keys())}. Known short labels: "
            f"{sorted(_ALIAS_TO_SERVICE.keys())}."
        )
    }


def gws_resolve_account_tool(args, **kw):
    from tools.gws_auth import EMAIL_TO_SERVICE
    from tools import gws_auth

    tid = _current_telegram_id()
    if not tid:
        return tool_error(
            "No session user context (HERMES_SESSION_USER_ID not set) -- "
            "cannot check token status."
        )

    account = (args.get("account") or "").strip()

    # No account given -> list every known service + auth status.
    # Each service shows the session user's OWN email (not a global default).
    if not account:
        user_svc_emails = _user_service_emails(tid)
        seen_services = sorted(set(EMAIL_TO_SERVICE.values()))
        results = []
        for svc in seen_services:
            user_email = user_svc_emails.get(svc)
            try:
                has_tok = gws_auth.has_token(svc)
            except Exception as e:
                results.append({
                    "email": user_email,
                    "service_name": svc,
                    "has_token": None,
                    "error": str(e),
                })
                continue
            results.append({
                "email": user_email,
                "service_name": svc,
                "has_token": has_tok,
            })
        return tool_result(accounts=results)

    resolved = _resolve_one(account)
    if "error" in resolved:
        return tool_error(resolved["error"])

    svc = resolved["service_name"]

    # Resolve the session user's own email for ownership check when the
    # input didn't specify a fixed email (alias / raw service name).
    if "email" in resolved:
        resolved_email = resolved["email"]
    else:
        user_svc_emails = _user_service_emails(tid)
        resolved_email = user_svc_emails.get(svc)

    if resolved_email:
        if not gws_auth.verify_email_ownership(resolved_email, tid):
            return tool_error(
                f"Account '{resolved_email}' is not associated with your "
                f"session user. You can only query accounts linked to your "
                f"own user profile."
            )

    try:
        has_tok = gws_auth.has_token(svc)
    except Exception as e:
        return tool_error(f"Vault lookup failed for service_name={svc}: {e}")

    return tool_result(
        email=resolved_email or svc,
        service_name=svc,
        has_token=has_tok,
        usage_hint=(
            f"from tools.gws_auth import build_service; "
            f"build_service(api, version, service_name='{svc}')"
        ),
    )


registry.register(
    name="gws_resolve_account",
    toolset="oauth",
    schema=GWS_RESOLVE_ACCOUNT_SCHEMA,
    handler=gws_resolve_account_tool,
    emoji="🔑",
)
