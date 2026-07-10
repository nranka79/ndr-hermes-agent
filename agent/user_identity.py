"""Canonical cross-platform user identity resolution.

Single source of truth for "which stored-memory bucket does this platform
user belong to" — shared by the built-in MemoryStore (MEMORY.md/USER.md)
and the Honcho memory provider's one-time file migration, so the same
human gets the same memory bucket regardless of which platform (Telegram,
Slack, Discord, etc.) they message through.

Deliberately reuses Honcho's existing ``honcho.json`` ``userPeerAliases``
table as the canonical identity source rather than introducing a second,
parallel identity-mapping file — one place to manage "which platform IDs
belong to the same human", already proven working for Honcho's own
per-peer memory scoping.

Resolution order (mirrors ``HonchoSessionManager._resolve_user_peer_id``
in plugins/memory/honcho/session.py, kept in sync deliberately so both
memory systems agree on the same canonical name for the same user):
  1. honcho.json's ``pinUserPeer`` + ``peerName``, if configured (pins ALL
     runtime identities to one name — single-user deployments)
  2. honcho.json's ``userPeerAliases``: platform_user_id -> canonical name
  3. honcho.json's ``runtimePeerPrefix`` + first known user_id (no alias
     found for this user_id)
  4. Sanitized raw platform_user_id, prefixed with the platform name (no
     honcho.json / no Honcho config at all — keeps per-user isolation
     working even when Honcho isn't configured)
  5. Empty string if no user_id was ever passed (CLI/local sessions have
     no platform user — callers should fall back to the flat, historical
     shared path, not treat this as an error)

honcho.json is read purely as config here (HonchoClientConfig.from_global_config()
does no network/SDK calls), so this resolves correctly whether or not the
Honcho provider is actually enabled for this session.
"""

from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)


def _sanitize(value: str) -> str:
    """Sanitize a candidate identity string to a filesystem-safe directory name."""
    return re.sub(r"[^a-zA-Z0-9_-]", "-", value.strip())


def resolve_canonical_user_id(
    user_id: str | None,
    user_id_alt: str | None = None,
    *,
    platform: str = "",
) -> str:
    """Resolve a platform user_id to the canonical identity bucket name.

    Args:
        user_id: Primary platform user identifier (e.g. Telegram numeric ID).
        user_id_alt: Optional stable alternate identifier for the same
            platform session, checked if ``user_id`` has no alias match.
        platform: Platform name (e.g. "telegram"), used only for the
            no-config fallback bucket name so different platforms'
            unmapped raw IDs can't collide with each other.

    Returns:
        A filesystem-safe canonical bucket name, or "" when there's no
        user_id at all (CLI/local/cron sessions) — callers should treat
        that as "use the flat/shared path", not as an error.
    """
    candidates = [
        str(c).strip() for c in (user_id, user_id_alt) if c and str(c).strip()
    ]

    cfg = None
    try:
        from plugins.memory.honcho.client import HonchoClientConfig

        cfg = HonchoClientConfig.from_global_config()
    except Exception as e:
        logger.debug(
            "user_identity: honcho.json not readable, falling back to raw id: %s", e
        )

    if cfg is not None:
        if cfg.peer_name and cfg.pin_peer_name:
            return _sanitize(cfg.peer_name)

        aliases = cfg.user_peer_aliases or {}
        for candidate in candidates:
            alias = aliases.get(candidate)
            if isinstance(alias, str) and alias.strip():
                return _sanitize(alias.strip())

        if candidates:
            prefix = (cfg.runtime_peer_prefix or "").strip()
            primary = candidates[0]
            return _sanitize(f"{prefix}{primary}" if prefix else primary)

        if cfg.peer_name:
            return _sanitize(cfg.peer_name)

    if candidates:
        plat = (platform or "user").strip() or "user"
        return _sanitize(f"{plat}_{candidates[0]}")

    return ""
