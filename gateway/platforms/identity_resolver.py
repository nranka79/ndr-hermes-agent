"""
Resolves the authenticated caller's identity from an inbound API server request.

The Open WebUI Pipe function (scripts/openwebui/hermes_pipe.py) injects
X-Hermes-User-Email into every request using the SSO-authenticated user's
email from Open WebUI's session context.  This module reads that header,
looks the email up in users.json via _user_registry, and returns the full
user record so the API server can wire up the correct user_id, OAuth vault
scope, Honcho memory bucket, and system-prompt profile — identically to how
a Telegram session is handled.

Nothing here is exposed to the LLM.  The resolver runs in Python before the
AIAgent is constructed, and the results flow into set_session_vars / AIAgent
constructor kwargs only.
"""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Header name injected by the Open WebUI Pipe function.
HEADER_USER_EMAIL = "X-Hermes-User-Email"


def resolve_from_request(request) -> Optional[dict]:
    """Return the full users.json record for the SSO-authenticated caller.

    Reads ``X-Hermes-User-Email`` from the request headers, looks it up in
    users.json via ``find_user_by_identity("email", ...)``, and returns the
    record.  Returns ``None`` if the header is absent or the email is not
    found in the registry.

    Args:
        request: aiohttp ``web.Request`` object.
    """
    email = request.headers.get(HEADER_USER_EMAIL, "").strip().lower()
    if not email:
        return None
    try:
        from tools._user_registry import find_user_by_identity
        _, record = find_user_by_identity("email", email)
        if record:
            logger.debug(
                "API server identity resolved: email=%s draas_user_id=%s",
                email, record.get("draas_user_id", ""),
            )
        else:
            logger.warning(
                "API server: %s=%s not found in users.json — session runs anonymous",
                HEADER_USER_EMAIL, email,
            )
        return record
    except Exception as exc:
        logger.warning("API server identity resolution failed: %s", exc)
        return None


def telegram_id_from_record(record: dict) -> str:
    """Return the first Telegram ID from a users.json record, or ''."""
    try:
        ids = (record or {}).get("identities", {}).get("telegram", [])
        return str(ids[0]) if ids else ""
    except Exception:
        return ""


def user_identity(request) -> Tuple[str, str, str]:
    """Convenience wrapper: resolve request → (user_id, user_email, draas_user_id).

    ``user_id`` is the Telegram numeric ID string — the stable cross-platform
    identifier used by gws_auth, Honcho, and the session system-prompt injector.
    All three values are empty strings when the caller is anonymous (no header
    or unknown email).
    """
    record = resolve_from_request(request)
    if not record:
        return "", "", ""
    user_id = telegram_id_from_record(record)
    user_email = record.get("email", "")
    draas_user_id = record.get("draas_user_id", "")
    return user_id, user_email, draas_user_id
