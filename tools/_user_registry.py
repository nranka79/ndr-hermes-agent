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


def find_user_by_identity(identity_type: str, identity_value: str) -> Tuple[Optional[str], Optional[dict]]:
    """Resolve a raw identifier (a Telegram ID, an email, ...) to its owning
    user record in users.json.

    users.json is keyed by each user's *primary email*; the actual identifiers
    (Telegram IDs, any linked email addresses) live under each record's
    ``identities`` dict, e.g. ``identities["telegram"] == ["7449813913"]``.
    A flat ``identity_value in load_user_registry()`` membership check only
    ever matches a primary-email key -- it can never match a Telegram ID.
    This scans ``identities`` properly instead.

    Args:
        identity_type: "telegram" or "email" (matches an ``identities`` key).
        identity_value: the raw identifier to resolve.

    Returns:
        (primary_email_key, record) for the owning user, or (None, None)
        if no user has this identifier.
    """
    value = str(identity_value).strip()
    if not value:
        return None, None
    registry = load_user_registry()

    # Fast path: value IS itself a primary-email key.
    direct = registry.get(value)
    if isinstance(direct, dict):
        return value, direct

    for email_key, rec in registry.items():
        if not isinstance(rec, dict):
            continue
        identities = rec.get("identities")
        if not isinstance(identities, dict):
            continue
        values = identities.get(identity_type) or []
        if value in [str(v) for v in values]:
            return email_key, rec

    return None, None


def get_user_config(telegram_user_id: str | int) -> dict:
    """Return the full user record owning *telegram_user_id*, or {} if unknown.

    Resolved via ``identities.telegram`` (see :func:`find_user_by_identity`) --
    users.json is keyed by primary email, not by Telegram ID.
    """
    _, rec = find_user_by_identity("telegram", telegram_user_id)
    return rec or {}
