"""
Per-user STT vocabulary for faster-whisper prompt injection.

Vocabulary lists are stored as JSON at:
  <HERMES_HOME>/vocab/<user_id>.json

Each file is a list of strings (proper nouns, names, domain terms).
At transcription time, the list is injected via faster-whisper's
``initial_prompt`` and ``hotwords`` parameters to improve recognition
of rare names and domain-specific words.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List

logger = logging.getLogger(__name__)


def _vocab_path(user_id: str) -> Path:
    from hermes_constants import get_hermes_home
    return get_hermes_home() / "vocab" / f"{user_id}.json"


def load_vocab(user_id: str) -> List[str]:
    """Return the vocabulary list for *user_id*, or [] if none stored."""
    if not user_id:
        return []
    try:
        p = _vocab_path(user_id)
        if p.exists():
            data = json.loads(p.read_text())
            if isinstance(data, list):
                return [str(t) for t in data if str(t).strip()]
    except Exception as exc:
        logger.warning("Failed to load vocab for user %s: %s", user_id, exc)
    return []


def save_vocab(user_id: str, terms: List[str]) -> None:
    """Persist *terms* as the vocabulary list for *user_id*."""
    if not user_id:
        raise ValueError("user_id required")
    p = _vocab_path(user_id)
    p.parent.mkdir(parents=True, exist_ok=True)
    cleaned = sorted({t.strip() for t in terms if t.strip()})
    p.write_text(json.dumps(cleaned, ensure_ascii=False, indent=2))


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
    p = _vocab_path(user_id)
    if p.exists():
        p.unlink()


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
