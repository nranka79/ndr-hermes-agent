"""
Identity resolution: maps channel-specific identifiers to internal user IDs.

ARCHITECTURE
============

Every user has one stable **internal user ID** — the top-level key in users.json.
For users who were registered via Telegram this happens to equal their Telegram
numeric ID; for future users it can be any stable alphanumeric string.

Channel identities are stored in the ``identities`` block of each user entry:

    {
      "7449813913": {
        "name": "Nishant Ranka",
        "email": "ndr@draas.com",
        "role": "admin",
        "identities": {
          "telegram":  ["7449813913"],
          "email":     ["ndr@draas.com", "ndr@ahfl.in"],
          "whatsapp":  ["+919..."],
          "slack":     ["U04XYZ"]
        }
      }
    }

Any number of channel types can be added later without restructuring the vault.
The vault always stores tokens keyed by the internal user ID — it never sees
channel-specific identifiers.

ADDING A NEW CHANNEL
====================
1. Populate the relevant ``identities.<channel>`` list in users.json for each user.
2. At the ingress point of the new platform handler, call:
       user_id = resolve_user_id("<channel>", <channel_specific_id>)
       set_session_vars(user_id=user_id or "", ...)
3. No vault or token-storage changes are required.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def resolve_user_id(channel: str, identifier: str) -> Optional[str]:
    """
    Map a channel-specific identifier to the internal user ID.

    Args:
        channel:    The access channel — "telegram", "email", "whatsapp",
                    "slack", etc. Case-insensitive.
        identifier: The channel-specific value (Telegram numeric ID, email
                    address, phone number, Slack member ID, …).

    Returns:
        The internal user ID (top-level key in users.json), or None if the
        identifier is not registered for any user.

    Lookup order:
        1. Explicit ``identities.<channel>`` list in users.json  (authoritative)
        2. Legacy: top-level key == identifier for channel="telegram"
        3. Legacy: top-level ``email`` field for channel="email"
    """
    from tools._user_registry import load_user_registry

    if not identifier or not channel:
        return None

    registry = load_user_registry()
    identifier_norm = identifier.strip().lower()
    channel_norm = channel.strip().lower()

    for user_id, cfg in registry.items():
        # ── 1. Explicit identities map ──────────────────────────────────────
        identities = cfg.get("identities", {})
        channel_ids = identities.get(channel_norm, [])
        if isinstance(channel_ids, str):
            channel_ids = [channel_ids]
        if identifier_norm in [i.strip().lower() for i in channel_ids]:
            return str(user_id)

        # ── 2. Legacy: telegram_id IS the top-level key ──────────────────────
        #    Existing users were registered with their Telegram ID as the key.
        #    We honour this without requiring a full identities block.
        if channel_norm == "telegram" and str(user_id) == identifier.strip():
            return str(user_id)

        # ── 3. Legacy: top-level "email" field ───────────────────────────────
        #    Pre-identities registrations used a bare "email" key.
        if channel_norm == "email":
            top_email = (cfg.get("email") or "").strip().lower()
            if top_email and top_email == identifier_norm:
                return str(user_id)

    logger.debug("No user found for channel=%r identifier=%r", channel, identifier)
    return None


def resolve_or_fallback(channel: str, identifier: str) -> str:
    """
    Like resolve_user_id() but returns *identifier* unchanged when no mapping
    is found.  Useful at ingress points where the raw channel ID is still
    preferable to an empty string (e.g. Telegram DMs for unregistered bots).
    """
    return resolve_user_id(channel, identifier) or identifier.strip()
