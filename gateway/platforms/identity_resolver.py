"""
Resolves the authenticated caller's identity from an inbound API server request.

Open WebUI forwards the SSO-authenticated user's identity to backends when
ENABLE_FORWARD_USER_INFO_HEADERS=true is set in its environment.  It adds:
    X-OpenWebUI-User-Email  -- the Google SSO email (e.g. user@example.com)
    X-OpenWebUI-User-Name   -- display name
    X-OpenWebUI-User-Role   -- Open WebUI role (admin / user)

This module reads that email header, looks it up in the vault (via
_user_registry), and returns the full user record so the API server can wire
up the correct user_id (canonical vault id — an email for SSO-only users, a
numeric Telegram ID for Telegram users), OAuth vault scope, Honcho memory
bucket, and system-prompt profile — identically to how a Telegram session
is handled.

Nothing here is exposed to the LLM.  The resolver runs in Python before the
AIAgent is constructed, and the results flow into set_session_vars / AIAgent
constructor kwargs only.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Header injected by Open WebUI when ENABLE_FORWARD_USER_INFO_HEADERS=true.
HEADER_USER_EMAIL = "X-OpenWebUI-User-Email"


def _first_alias(record: dict, kind: str) -> str:
    """Return the first alias of *kind* from a vault identity record, or ''.

    The vault stores aliases nested under ``identities`` (e.g.
    ``identities.email``), not as top-level fields.  Reads both the nested
    list and a legacy top-level scalar so both record shapes resolve.
    """
    try:
        values = (record or {}).get("identities", {}).get(kind, []) or []
        if values:
            return str(values[0])
    except Exception:
        pass
    return str((record or {}).get(kind, "") or "")


def resolve_from_request(request) -> Optional[dict]:
    """Return the full vault identity record for the SSO-authenticated caller.

    Reads ``X-Hermes-User-Email`` from the request headers, looks it up in
    the vault via ``find_user_by_identity("email", ...)``, and returns the
    record.  Returns ``None`` if the header is absent or the email is not
    found in the registry.

    Args:
        request: aiohttp ``web.Request`` object.
    """
    email = request.headers.get(HEADER_USER_EMAIL, "").strip().lower()
    if not email:
        # No identity header -- anonymous API caller. Worth an INFO line:
        # an anonymous run cannot resolve any user's tokens, so downstream
        # tool failures are expected and must never be papered over by
        # guessing an identity.
        logger.info(
            "API server identity: no %s header -- request runs ANONYMOUS",
            HEADER_USER_EMAIL,
        )
        return None
    try:
        from tools._user_registry import find_user_by_identity
        _, record = find_user_by_identity("email", email)
        if record:
            logger.info(
                "API server identity resolved: email=%s user_id=%s draas_user_id=%s",
                email, record.get("user_id", ""), _first_alias(record, "draas_user_id"),
            )
        else:
            logger.warning(
                "API server: %s=%s not found in registry — session runs anonymous",
                HEADER_USER_EMAIL, email,
            )
        return record
    except Exception as exc:
        logger.warning("API server identity resolution failed: %s", exc)
        return None


def telegram_id_from_record(record: dict) -> str:
    """Return the first Telegram ID from a vault identity record, or ''."""
    try:
        ids = (record or {}).get("identities", {}).get("telegram", [])
        return str(ids[0]) if ids else ""
    except Exception:
        return ""


def user_identity(request) -> Tuple[str, str, str]:
    """Convenience wrapper: resolve request → (user_id, user_email, draas_user_id).

    ``user_id`` is the canonical vault user_id (``record["user_id"]``, e.g.
    ``pebblyshark69@gmail.com`` for an SSO-only user or ``ndr-7449813913``
    for NDR) — the stable cross-platform identifier used by gws_auth, Honcho,
    and the session system-prompt injector.  Records without a top-level
    ``user_id`` fall back to the first Telegram ID.  ``user_email`` /
    ``draas_user_id`` are read from the record's ``identities`` aliases (the
    vault stores them nested, not as top-level fields).  All three values are
    empty strings when the caller is anonymous (no header or unknown email).
    """
    record = resolve_from_request(request)
    if not record:
        return "", "", ""
    user_id = str(record.get("user_id", "") or "") or telegram_id_from_record(record)
    user_email = _first_alias(record, "email")
    draas_user_id = _first_alias(record, "draas_user_id")
    return user_id, user_email, draas_user_id
