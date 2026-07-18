import json
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

_registry_cache: Optional[dict] = None
_registry_mtime: float = 0.0


def _registry_path() -> Path:
    return Path(os.environ.get("HERMES_HOME", "")) / "users.json"


def load_user_registry() -> dict:
    """Load the raw users.json registry, keyed by each user's primary email.

    Mtime-cached: re-reads from disk only when the file's mtime changes, so
    admin edits (via the manage_user tool) take effect on the next call
    without a gateway restart.
    """
    global _registry_cache, _registry_mtime
    path = _registry_path()
    try:
        mtime = path.stat().st_mtime
        if _registry_cache is not None and mtime == _registry_mtime:
            return _registry_cache
        _registry_cache = json.loads(path.read_text(encoding="utf-8"))
        _registry_mtime = mtime
        return _registry_cache
    except Exception as e:
        logger.debug("Could not load user registry: %s", e)
        return {}


def _find_in_file_registry(value: str, identity_type: str) -> Tuple[Optional[str], Optional[dict]]:
    """Scan users.json to resolve an identifier. Returns (email_key, record)."""
    registry = load_user_registry()

    direct = registry.get(value)
    if isinstance(direct, dict):
        return value, direct

    for email_key, rec in registry.items():
        if not isinstance(rec, dict):
            continue
        ids = rec.get("identities")
        if not isinstance(ids, dict):
            continue
        values = ids.get(identity_type) or []
        if value in [str(v) for v in values]:
            return email_key, rec

    return None, None


def find_user_by_identity(identity_type: str, identity_value: str) -> Tuple[Optional[str], Optional[dict]]:
    """Resolve a raw identifier to the canonical user record.

    Resolution order:
      1. Vault (``gws_vault_client.resolve``) — canonical identity source.
      2. File registry (``users.json``) — fallback, also provides app-specific
         fields (gbrain_home, phone, etc.) that aren't in the vault yet.

    Args:
        identity_type: ``"telegram"``, ``"email"``, or ``"draas_user_id"``.
        identity_value: the raw identifier to resolve.

    Returns:
        ``(canonical_email, record)`` or ``(None, None)``.
    """
    value = str(identity_value).strip()
    if not value:
        return None, None

    try:
        from tools import gws_vault_client as vault

        user_id = vault.resolve(identity_type, value)
        if user_id:
            vault_rec = vault.get_identity(user_id, session_uid=user_id)
            file_rec = load_user_registry().get(user_id) if vault_rec else None
            if vault_rec and file_rec:
                merged = {**file_rec}
                merged.setdefault("identities", vault_rec.get("identities", {}))
                merged.setdefault("permissions", vault_rec.get("permissions", {}))
                # App-specific fields (2026-07-18 users.json consolidation):
                # prefer vault's value once present (post-migration source
                # of truth, protected by the vault's admin-secret-gated
                # write path), falling back to the file's value for users
                # not yet migrated. Scoped to just these 3 fields so
                # identities/permissions merge behavior above is untouched.
                for _field in ("gbrain_home", "phone", "contacts_sheet_id"):
                    if _field in vault_rec:
                        merged[_field] = vault_rec[_field]
                return user_id, merged
            if file_rec:
                return user_id, file_rec
            if vault_rec:
                return user_id, vault_rec
    except Exception:
        logger.debug("Vault resolve failed for %s=%s, falling back to file", identity_type, value)

    return _find_in_file_registry(value, identity_type)


def get_user_config(telegram_user_id: str | int) -> dict:
    """Return the full user record owning *telegram_user_id*, or {} if unknown.

    Resolved via ``identities.telegram`` (see :func:`find_user_by_identity`) --
    users.json is keyed by primary email, not by Telegram ID.
    """
    _, rec = find_user_by_identity("telegram", telegram_user_id)
    return rec or {}
