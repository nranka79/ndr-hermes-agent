import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def find_user_by_identity(identity_type: str, identity_value: str) -> Tuple[Optional[str], Optional[dict]]:
    """Resolve a raw identifier to the canonical user record.

    Vault is the single source of truth — reads exclusively from the
    gws-vault daemon. No file fallback.

    Args:
        identity_type: ``"telegram"``, ``"email"``, ``"slug"``, ``"draas_user_id"``, or ``"phone"``.
        identity_value: the raw identifier to resolve.

    Returns:
        ``(canonical_user_id, record)`` or ``(None, None)``.
    """
    value = str(identity_value).strip() if identity_value is not None else ""
    if not value:
        return None, None

    try:
        from tools import gws_vault_client as vault

        user_id = vault.resolve(identity_type, value)
        if not user_id:
            return None, None

        vault_rec = vault.get_identity(user_id, session_uid=user_id)
        if not vault_rec:
            return None, None

        return user_id, vault_rec
    except Exception:
        logger.debug("Vault resolve failed for %s=%s", identity_type, value)
        return None, None


def get_user_config(session_user_id: str | int) -> dict:
    """Return the full user record for *session_user_id*, or {} if unknown.

    Fixed 2026-09-15: previously hardcoded ``identities.telegram`` as the
    only lookup bucket, regardless of what *session_user_id* actually was.
    That silently broke on any non-Telegram-shaped session id -- e.g.
    OpenWebUI/SSO sessions, where the id is often already the canonical
    vault user_id (a slug like ``ndr-7449813913``), not a raw Telegram
    digit string. Symptom: contact_resolver / noun_resolver / noun_learner
    erroring "no gws_service configured in their profile" for every
    OpenWebUI session, while working fine on Telegram.

    Two-step lookup, vault as sole source of truth for the match (no
    client-side type-guessing):
      1. Try *session_user_id* as an already-canonical user_id directly
         (covers OpenWebUI/SSO sessions -- identity_resolver.py hands us
         the canonical id straight from the vault record).
      2. If that misses, treat it as a raw alias of unknown type (Telegram
         digits, email, slug, draas_user_id, phone -- doesn't matter which)
         and ask the vault to resolve it across every bucket via
         ``resolve_any`` (covers Telegram sessions, and slug-only cron
         invocations like ``HERMES_SESSION_USER_ID=psingh``).
    """
    value = str(session_user_id).strip() if session_user_id is not None else ""
    if not value:
        return {}

    try:
        from tools import gws_vault_client as vault

        # Step 1: already-canonical?
        try:
            rec = vault.get_identity(value, session_uid=value)
            if rec:
                return rec
        except Exception:
            pass  # not canonical, or vault hiccup -- fall through to step 2

        # Step 2: raw alias of unknown type -- let the vault find it.
        canonical = vault.resolve_any(value)
        if not canonical:
            return {}
        rec = vault.get_identity(canonical, session_uid=canonical)
        return rec or {}
    except Exception:
        logger.debug("get_user_config vault lookup failed for %s", value)
        return {}
