"""User registry — loads users.json and resolves identities.

users.json schema
-----------------
Top-level keys are **canonical user IDs** — the primary email address for each
user (e.g. "ndr@draas.com").  This is globally unique, SSO-compatible, and
distinguishes users across domains (ndr@draas.com vs ndr@ahfl.in).

Each entry may contain:

    {
      "ndr@draas.com": {
        "name":  "Full Name",
        "email": "ndr@draas.com",          # same as key — canonical ID
        "role":  "admin" | "employee",
        "identities": {
          "telegram":  ["<telegram_numeric_id>"],
          "email":     ["ndr@draas.com", "alias@example.com"],
          "whatsapp":  ["+1..."],
          "slack":     ["U..."]
        },
        "cross_message_allowed": true     # optional, Telegram cross-user DMs
      }
    }

Use _identity_resolver.resolve_user_id(channel, identifier) to map any
channel-specific identifier back to the canonical user ID (primary email).

get_user_config() accepts both canonical IDs and raw channel identifiers
(Telegram numeric IDs, email aliases, etc.) — it resolves them automatically.
"""

import json
import logging
import os
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

_registry_cache: Optional[dict] = None
_registry_mtime: float = 0.0


def _registry_path() -> Path:
    return Path(os.environ.get("HERMES_HOME", "")) / "users.json"


def load_user_registry() -> dict:
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


def get_user_config(user_id: str | int) -> dict:
    """Return the config dict for a user given their canonical user ID or any
    registered channel identifier (Telegram numeric ID, email alias, etc.).

    Lookup order:
      1. Direct key match — canonical email-based user ID (e.g. "ndr@draas.com")
      2. Identity resolution — resolve channel identifier → canonical user ID:
         - All-digit string → try "telegram" channel
         - Otherwise        → try "email" channel

    To look up by a specific channel-and-identifier pair, use
    resolve_user_id() or _identity_resolver.resolve_user_id() directly.
    """
    registry = load_user_registry()
    uid = str(user_id)

    # 1. Direct key lookup (canonical email-based user ID)
    if uid in registry:
        return registry[uid]

    # 2. Resolve channel identifier → canonical user ID then look up
    try:
        from tools._identity_resolver import resolve_user_id
        channel = "telegram" if uid.isdigit() else "email"
        canonical = resolve_user_id(channel, uid)
        if canonical and canonical in registry:
            return registry[canonical]
    except Exception:
        pass

    return {}


def resolve_user_id(channel: str, identifier: str) -> Optional[str]:
    """Map a channel-specific identifier to the canonical user ID (primary email).

    Convenience wrapper around _identity_resolver.resolve_user_id().
    See that module's docstring for full details.
    """
    from tools._identity_resolver import resolve_user_id as _resolve
    return _resolve(channel, identifier)


def is_cross_message_allowed(user_id: str | int) -> bool:
    """Return True if the user has opted into cross-user Telegram messaging."""
    return bool(get_user_config(user_id).get("cross_message_allowed"))
