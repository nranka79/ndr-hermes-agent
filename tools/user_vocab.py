"""
Per-user STT vocabulary for faster-whisper prompt injection.

Backed by the GWS Token Vault (``tools/gws_vault_client.py``, service
name ``"vocab"``) instead of flat JSON files — vocabulary now lives
alongside OAuth tokens under the same per-user, per-service protection
(isolated ``gws-vault`` OS user, Unix socket, session-checked reads).

This keeps the exact same function signatures the rest of the codebase
already expects (``gateway/slash_commands.py``'s ``/vocab`` command,
``tools/transcription_tools.py``'s local faster-whisper provider) — only
the storage backend changed, so no other file needs to change to pick
this up.

At transcription time, the list is injected via faster-whisper's
``initial_prompt`` and ``hotwords`` parameters to improve recognition
of rare names and domain-specific words.

Every public function here resolves ``user_id`` through
``tools.gws_auth.canonical_uid()`` before touching the vault -- same as
``gws_auth.py``'s own token read/write path. Callers (e.g. the ``/vocab``
slash command, ``transcription_tools.py``) still pass whatever raw channel
id they have (Telegram numeric id, email, etc.); this module is the single
choke point that maps it to the canonical vault key, so vocabulary data
can't end up split across two vault keys for the same physical user the way
it previously did (raw telegram id vs. canonical ``name-telegramid``
surrogate) -- see `.plans/` for the root-cause writeup and
`scripts/migrate_orphaned_vault_keys.py` for the one-time cleanup of data
written under the old, uncanonicalized key.
"""

from __future__ import annotations

import json
import logging
from typing import List

from tools.gws_vault_client import (
    VaultError,
    VaultNoTokenError,
    delete_token,
    get_token,
    set_token,
)

logger = logging.getLogger(__name__)

SERVICE = "vocab"


def _canonical(user_id: str) -> str:
    """Resolve a raw channel id to the canonical vault user_id.

    Thin wrapper around ``tools.gws_auth.canonical_uid()`` (imported lazily
    to avoid a module-level import cycle -- gws_auth imports
    googleapiclient/google-auth at import time, which vocab callers like the
    CLI's fast-path slash-command dispatch shouldn't be forced to pay for).
    Falls back to the raw id on any resolution failure, matching
    canonical_uid()'s own fallback -- unmigrated / unknown users keep
    working unchanged.
    """
    if not user_id:
        return user_id
    try:
        from tools.gws_auth import canonical_uid
        return canonical_uid(user_id)
    except Exception:
        logger.debug("vocab: canonical_uid resolution failed for %r", user_id, exc_info=True)
        return user_id


def load_vocab(user_id: str) -> List[str]:
    """Return the vocabulary list for *user_id*, or [] if none stored."""
    if not user_id:
        return []
    user_id = _canonical(user_id)
    try:
        raw = get_token(user_id, SERVICE, session_uid=user_id)
        data = json.loads(raw)
        if isinstance(data, list):
            return [str(t) for t in data if str(t).strip()]
    except VaultNoTokenError:
        pass
    except Exception as exc:
        logger.warning("Failed to load vocab for user %s: %s", user_id, exc)
    return []


def save_vocab(user_id: str, terms: List[str]) -> None:
    """Persist *terms* as the vocabulary list for *user_id*."""
    if not user_id:
        raise ValueError("user_id required")
    user_id = _canonical(user_id)
    cleaned = sorted({t.strip() for t in terms if t.strip()})
    set_token(user_id, SERVICE, json.dumps(cleaned, ensure_ascii=False))


def add_terms(user_id: str, new_terms: List[str]) -> List[str]:
    """Add *new_terms* to the user's vocabulary, return the full updated list."""
    existing = set(load_vocab(user_id))
    existing.update(t.strip() for t in new_terms if t.strip())
    merged = sorted(existing)
    save_vocab(user_id, merged)
    return merged


def remove_terms(user_id: str, remove: List[str]) -> List[str]:
    """Remove *remove* from the user's vocabulary, return the updated list."""
    remove_set = {t.strip().lower() for t in remove}
    existing = [t for t in load_vocab(user_id) if t.lower() not in remove_set]
    save_vocab(user_id, existing)
    return existing


def clear_vocab(user_id: str) -> None:
    """Delete all vocabulary for *user_id*."""
    user_id = _canonical(user_id)
    try:
        delete_token(user_id, SERVICE)
    except VaultError as exc:
        logger.warning("Failed to clear vocab for user %s: %s", user_id, exc)


def build_initial_prompt(terms: List[str]) -> str:
    """Build a natural-sentence initial_prompt from *terms*.

    OpenAI's prompting cookbook shows that a natural sentence
    outperforms a bare comma-separated word list for spelling biasing.
    """
    if not terms:
        return ""
    terms_str = ", ".join(terms)
    return f"The following names and terms may appear: {terms_str}."


def build_hotwords(terms: List[str]) -> str:
    """Build the comma-separated hotwords string for faster-whisper."""
    return ", ".join(terms) if terms else ""
