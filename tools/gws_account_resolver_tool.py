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
hand-typed slugs. Call it with no arguments to list every known account and
whether each currently has a stored token (ideal for "search across all my
accounts" requests). Call it with an ``account`` (email address or short
label like "draas"/"ahfl"/"gmail"/"personal") to resolve a single one.

Once you have the ``service_name`` back, use it directly in execute_code:
    from tools.gws_auth import build_service
    svc = build_service("gmail", "v1", service_name="google-draas")
"""

import json
import re

from tools.registry import registry, tool_error, tool_result

# Short, human-typeable aliases -> canonical email used to resolve service_name.
# Keep in sync with tools/gws_auth.py EMAIL_TO_SERVICE.
_ALIAS_TO_EMAIL = {
    "draas": "ndr@draas.com",
    "ahfl": "ndr@ahfl.in",
    "gmail": "nishantranka@gmail.com",
    "personal": "nishantranka@gmail.com",
}

_SERVICE_NAME_RE = re.compile(r"^[a-z][a-z0-9-]{0,49}$")

GWS_RESOLVE_ACCOUNT_SCHEMA = {
    "name": "gws_resolve_account",
    "description": (
        "Resolve a Google account (email address or short label like "
        "'draas'/'ahfl'/'gmail'/'personal') to the exact vault service_name "
        "key needed by build_service()/has_token(), and report whether a "
        "token is currently stored for it. Call with no arguments to list "
        "ALL known accounts and their auth status at once -- use this "
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
                    "every known account and its auth status."
                ),
            },
        },
        "required": [],
    },
}


def _current_telegram_id() -> str | None:
    # NOTE: must use get_gws_identity_env(), not os.environ directly. This
    # tool runs in-process (not via a subprocess), so the session user id
    # only ever lives in the per-task ContextVar set by
    # gateway.session_context.set_session_vars() -- it is never mirrored
    # into process-global os.environ. Reading os.environ here returns ""
    # in every session (interactive and cron alike); see the root-cause
    # writeup in .plans/ for the bug this fixes. get_gws_identity_env() also
    # falls back to the cron job's owner id when this is a cron run.
    from gateway.session_context import get_gws_identity_env
    tid = get_gws_identity_env().strip()
    return tid or None


def _resolve_one(account: str) -> dict:
    """Resolve a single account string to {email, service_name} or an error dict."""
    from tools.gws_auth import EMAIL_TO_SERVICE

    raw = account.strip()
    key = raw.lower()

    # Already a known email.
    if key in EMAIL_TO_SERVICE:
        return {"email": key, "service_name": EMAIL_TO_SERVICE[key]}

    # Short alias -> email -> service_name.
    if key in _ALIAS_TO_EMAIL:
        email = _ALIAS_TO_EMAIL[key]
        svc = EMAIL_TO_SERVICE.get(email)
        if svc:
            return {"email": email, "service_name": svc}

    # Already looks like a raw vault service_name (e.g. "google-draas") --
    # pass through only if it's a real, known service.
    if _SERVICE_NAME_RE.match(key) and key in set(EMAIL_TO_SERVICE.values()):
        matched_email = next(
            (e for e, s in EMAIL_TO_SERVICE.items() if s == key), None
        )
        return {"email": matched_email, "service_name": key}

    return {
        "error": (
            f"'{account}' is not a known GWS account. Known emails: "
            f"{sorted(EMAIL_TO_SERVICE.keys())}. Known short labels: "
            f"{sorted(_ALIAS_TO_EMAIL.keys())}."
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

    # No account given -> list every known account + auth status.
    if not account:
        seen_services = {}
        for email, svc in EMAIL_TO_SERVICE.items():
            seen_services.setdefault(svc, email)  # first/primary email per service
        results = []
        for svc, email in seen_services.items():
            try:
                has_tok = gws_auth.has_token(svc)
            except Exception as e:
                results.append({
                    "email": email, "service_name": svc,
                    "has_token": None, "error": str(e),
                })
                continue
            results.append({"email": email, "service_name": svc, "has_token": has_tok})
        return tool_result(accounts=results)

    resolved = _resolve_one(account)
    if "error" in resolved:
        return tool_error(resolved["error"])

    svc = resolved["service_name"]
    try:
        has_tok = gws_auth.has_token(svc)
    except Exception as e:
        return tool_error(f"Vault lookup failed for service_name={svc}: {e}")

    return tool_result(
        email=resolved["email"],
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
