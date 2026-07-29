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


def get_user_config(telegram_user_id: str | int) -> dict:
    """Return the full user record owning *telegram_user_id*, or {} if unknown.

    Resolved via ``identities.telegram`` in the vault identity store.
    """
    _, rec = find_user_by_identity("telegram", telegram_user_id)
    return rec or {}
