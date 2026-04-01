#!/usr/bin/env python3
"""
Contextual Noun Resolver — 3-tier cache for voice message noun correction.

Architecture:
  Tier 1 — Thin name index (ALL contacts + all projects/entities/land in memory)
            Only stores: normalized_variant → {row, canonical, type, sheet}
            ~500KB total, rebuilt on startup + after learner writes.

  Tier 2 — Hot record cache (top 15 contacts by contact_score, full records)
            Refreshed every 5 minutes in background thread.

  Tier 3 — Live sheet fetch (name resolved via Tier 1 but not in Tier 2)
            Single targeted API call for that row only.

Resolution pipeline:
  1. Tokenize input text into candidate noun phrases (1–3 word windows)
  2. Look up each candidate in Tier 1 index (exact → fuzzy → phonetic)
  3. Score matches; auto-replace if confidence ≥ 0.92, flag if 0.75–0.91, skip if <0.75
  4. Use session context (last 5 messages) to disambiguate ties

Spreadsheet: https://docs.google.com/spreadsheets/d/1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g
"""

import json
import logging
import os
import re
import threading
import time
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)

# ── Sheet config ───────────────────────────────────────────────────────────────

SHEET_ID = "1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g"

# Contacts sheet column indices (0-based)
COL_FIRST_NAME        = 0   # A
COL_MIDDLE_NAME       = 1   # B
COL_LAST_NAME         = 2   # C
COL_NICKNAME          = 8   # I
COL_ORG_NAME          = 10  # K
COL_ALIAS             = 82  # CE
COL_PEOPLE_ASSOC      = 83  # CF
COL_CONV_HISTORY      = 84  # CG  (old index before new cols)
COL_VOICE_MISSPELL    = 91  # CN  (new)
COL_CONTACT_SCORE     = 92  # CO  (new)

# Non-contacts sheets: all have canonical_name(A), aliases(B), voice_misspellings(C)
COL_CANONICAL   = 0
COL_ALIASES     = 1
COL_MISSPELL    = 2

SHEET_CONFIGS = {
    "contacts": {
        "range":    "NDR DRAAS Google contacts.csv!A:CO",
        "name_col": None,       # special: built from first+last
        "alias_col": COL_ALIAS,
        "misspell_col": COL_VOICE_MISSPELL,
        "score_col": COL_CONTACT_SCORE,
    },
    "projects": {
        "range":    "projects!A:I",
        "name_col": COL_CANONICAL,
        "alias_col": COL_ALIASES,
        "misspell_col": COL_MISSPELL,
        "score_col": None,
    },
    "land_proposals": {
        "range":    "land_proposals!A:J",
        "name_col": COL_CANONICAL,
        "alias_col": COL_ALIASES,
        "misspell_col": COL_MISSPELL,
        "score_col": None,
    },
    "entities": {
        "range":    "entities!A:H",
        "name_col": COL_CANONICAL,
        "alias_col": COL_ALIASES,
        "misspell_col": COL_MISSPELL,
        "score_col": None,
    },
}

# Confidence thresholds
THRESH_AUTO    = 0.92   # auto-replace silently
THRESH_MENTION = 0.75   # replace but tell user

# Hot cache size
HOT_CACHE_SIZE = 15

# Refresh interval for hot cache (seconds)
HOT_REFRESH_INTERVAL = 300

# ── Module-level singleton ─────────────────────────────────────────────────────

_resolver: "NounResolver | None" = None
_resolver_lock = threading.Lock()


def get_resolver() -> "NounResolver":
    global _resolver
    with _resolver_lock:
        if _resolver is None:
            _resolver = NounResolver()
            _resolver.start()
        return _resolver


# ── Helpers ────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    """Lowercase, strip accents, collapse whitespace."""
    nfkd = unicodedata.normalize("NFKD", text or "")
    ascii_str = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_str).strip().lower()


def _get_credentials():
    """Load draas.com OAuth credentials from the Railway credential file."""
    cred_file = os.environ.get("DRAAS_CRED_FILE", "/data/hermes/oauth-draas.json")
    if not os.path.exists(cred_file):
        raise FileNotFoundError(f"Credential file not found: {cred_file}")
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request as GoogleRequest
    with open(cred_file) as f:
        data = json.load(f)
    creds = Credentials(
        token=None,
        refresh_token=data["refresh_token"],
        client_id=data["client_id"],
        client_secret=data["client_secret"],
        token_uri="https://oauth2.googleapis.com/token",
    )
    creds.refresh(GoogleRequest())
    return creds


def _build_service():
    from googleapiclient.discovery import build
    return build("sheets", "v4", credentials=_get_credentials())


def _fuzzy_score(query: str, candidate: str) -> float:
    """Return similarity 0–1 using rapidfuzz if available, else simple ratio."""
    try:
        from rapidfuzz import fuzz
        return fuzz.token_sort_ratio(query, candidate) / 100.0
    except ImportError:
        # Fallback: character overlap ratio
        q, c = set(query), set(candidate)
        if not q and not c:
            return 1.0
        return len(q & c) / max(len(q | c), 1)


# ── NounResolver class ─────────────────────────────────────────────────────────

class NounResolver:
    """
    Thread-safe noun resolver with 3-tier cache.

    Usage:
        resolver = get_resolver()
        result = resolver.resolve("meeting with drast about ranka amba project")
        # result.corrected_text, result.substitutions, result.needs_confirmation
    """

    def __init__(self):
        # Tier 1: normalized_variant → {canonical, type, sheet, row}
        self._index: dict[str, dict] = {}
        self._index_lock = threading.RLock()
        self._index_built = False

        # Tier 2: canonical_name → full row dict (top HOT_CACHE_SIZE by score)
        self._hot_cache: dict[str, dict] = {}
        self._hot_lock = threading.RLock()

        # Background refresh thread
        self._stop_event = threading.Event()
        self._refresh_thread: threading.Thread | None = None

    # ── Lifecycle ──────────────────────────────────────────────────────────────

    def start(self):
        """Build initial index and start background refresh."""
        try:
            self._rebuild_index()
            self._refresh_hot_cache()
        except Exception as e:
            logger.warning(f"NounResolver: initial load failed ({e}) — will retry in background")

        self._refresh_thread = threading.Thread(
            target=self._background_refresh, daemon=True, name="noun-resolver-refresh"
        )
        self._refresh_thread.start()
        logger.info(f"NounResolver started: {len(self._index)} index entries, {len(self._hot_cache)} hot records")

    def stop(self):
        self._stop_event.set()

    def force_refresh(self):
        """Call this after the learner writes new data to the sheet."""
        threading.Thread(target=self._rebuild_index, daemon=True).start()

    # ── Index building ─────────────────────────────────────────────────────────

    def _rebuild_index(self):
        """Rebuild the full thin name index from all 4 sheets."""
        try:
            svc = _build_service()
            new_index: dict[str, dict] = {}

            for sheet_name, cfg in SHEET_CONFIGS.items():
                try:
                    resp = svc.spreadsheets().values().get(
                        spreadsheetId=SHEET_ID,
                        range=cfg["range"],
                    ).execute()
                    rows = resp.get("values", [])
                    if len(rows) < 2:
                        continue

                    for row_idx, row in enumerate(rows[1:], start=2):  # skip header
                        canonical = self._extract_canonical(sheet_name, cfg, row)
                        if not canonical:
                            continue

                        entries = self._extract_variants(sheet_name, cfg, row, canonical)
                        for variant, confidence in entries:
                            key = _normalize(variant)
                            if not key:
                                continue
                            # Keep highest-confidence entry per key
                            existing = new_index.get(key)
                            if existing is None or existing["confidence"] < confidence:
                                new_index[key] = {
                                    "canonical": canonical,
                                    "type": sheet_name,
                                    "sheet": sheet_name,
                                    "row": row_idx,
                                    "confidence": confidence,
                                }

                except Exception as e:
                    logger.warning(f"NounResolver: failed loading sheet '{sheet_name}': {e}")

            with self._index_lock:
                self._index = new_index
                self._index_built = True

            logger.info(f"NounResolver: index rebuilt with {len(new_index)} entries")

        except Exception as e:
            logger.error(f"NounResolver: _rebuild_index failed: {e}")

    def _extract_canonical(self, sheet_name: str, cfg: dict, row: list) -> str:
        """Extract the canonical name for a row."""
        def _get(idx):
            return row[idx].strip() if idx < len(row) else ""

        if sheet_name == "contacts":
            first = _get(COL_FIRST_NAME)
            last  = _get(COL_LAST_NAME)
            nick  = _get(COL_NICKNAME)
            org   = _get(COL_ORG_NAME)
            name  = f"{first} {last}".strip()
            return name or nick or org
        else:
            return _get(cfg["name_col"])

    def _extract_variants(self, sheet_name: str, cfg: dict, row: list, canonical: str) -> list[tuple[str, float]]:
        """Return list of (variant_text, confidence) tuples for this row."""
        def _get(idx):
            return row[idx].strip() if idx < len(row) else ""

        variants = [(canonical, 1.0)]

        # Nickname / first name alone for contacts
        if sheet_name == "contacts":
            first = _get(COL_FIRST_NAME)
            nick  = _get(COL_NICKNAME)
            if first:
                variants.append((first, 0.85))
            if nick:
                variants.append((nick, 0.95))

        # Aliases (pipe or comma separated)
        alias_raw = _get(cfg["alias_col"])
        if alias_raw:
            for a in re.split(r"[|,;]", alias_raw):
                a = a.strip()
                if a:
                    variants.append((a, 1.0))

        # Voice misspellings (pipe or comma separated)
        misspell_raw = _get(cfg["misspell_col"])
        if misspell_raw:
            for m in re.split(r"[|,;]", misspell_raw):
                m = m.strip()
                if m:
                    variants.append((m, 0.95))

        return variants

    # ── Hot cache ──────────────────────────────────────────────────────────────

    def _refresh_hot_cache(self):
        """Fetch top HOT_CACHE_SIZE contacts by contact_score."""
        try:
            svc = _build_service()
            resp = svc.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range="NDR DRAAS Google contacts.csv!A:CO",
            ).execute()
            rows = resp.get("values", [])
            if len(rows) < 2:
                return

            # Score each row
            scored = []
            for row_idx, row in enumerate(rows[1:], start=2):
                score_raw = row[COL_CONTACT_SCORE] if COL_CONTACT_SCORE < len(row) else ""
                try:
                    score = float(score_raw) if score_raw else 0.0
                except ValueError:
                    score = 0.0
                if score > 0:
                    first = row[COL_FIRST_NAME].strip() if COL_FIRST_NAME < len(row) else ""
                    last  = row[COL_LAST_NAME].strip() if COL_LAST_NAME < len(row) else ""
                    name  = f"{first} {last}".strip()
                    if name:
                        scored.append((score, name, row_idx, row))

            scored.sort(reverse=True)
            hot = {}
            for _, name, row_idx, row in scored[:HOT_CACHE_SIZE]:
                hot[name] = {"row": row_idx, "data": row, "type": "contacts"}

            with self._hot_lock:
                self._hot_cache = hot

        except Exception as e:
            logger.warning(f"NounResolver: hot cache refresh failed: {e}")

    # ── Background thread ──────────────────────────────────────────────────────

    def _background_refresh(self):
        while not self._stop_event.wait(HOT_REFRESH_INTERVAL):
            self._refresh_hot_cache()

    # ── Resolution ─────────────────────────────────────────────────────────────

    def resolve(self, text: str, session_context: list[str] | None = None) -> "ResolveResult":
        """
        Resolve nouns in text.

        Returns ResolveResult with:
          .corrected_text   — text with high-confidence substitutions applied
          .substitutions    — list of {original, canonical, type, confidence}
          .needs_confirmation — list of {original, candidates} for ambiguous matches
        """
        if not self._index_built or not text:
            return ResolveResult(text, [], [])

        substitutions = []
        needs_confirmation = []
        corrected = text

        # Generate candidate phrases (1, 2, 3 word windows)
        candidates = self._candidate_phrases(text)

        # Track which character spans have been resolved (avoid double-substitution)
        resolved_spans: list[tuple[int, int]] = []

        for phrase, start, end in candidates:
            # Skip if overlaps an already-resolved span
            if any(s <= start < e or s < end <= e for s, e in resolved_spans):
                continue

            match = self._lookup(phrase, session_context)
            if not match:
                continue

            conf = match["confidence"]
            canonical = match["canonical"]
            norm_phrase = _normalize(phrase)
            norm_canonical = _normalize(canonical)

            # Skip if phrase already matches canonical (no correction needed)
            if norm_phrase == norm_canonical:
                continue

            if conf >= THRESH_AUTO:
                corrected = corrected[:start] + canonical + corrected[end:]
                # Adjust subsequent positions
                delta = len(canonical) - len(phrase)
                resolved_spans = [(s + delta if s > start else s, e + delta if e > start else e)
                                  for s, e in resolved_spans]
                resolved_spans.append((start, start + len(canonical)))
                substitutions.append({
                    "original": phrase, "canonical": canonical,
                    "type": match["type"], "confidence": round(conf, 3),
                })
            elif conf >= THRESH_MENTION:
                needs_confirmation.append({
                    "original": phrase,
                    "candidates": [{"canonical": canonical, "type": match["type"], "confidence": round(conf, 3)}],
                })

        return ResolveResult(corrected, substitutions, needs_confirmation)

    def _candidate_phrases(self, text: str) -> list[tuple[str, int, int]]:
        """Return (phrase, start, end) for all 1–3 word windows."""
        words = list(re.finditer(r"\S+", text))
        result = []
        for n in (3, 2, 1):
            for i in range(len(words) - n + 1):
                group = words[i:i + n]
                start = group[0].start()
                end   = group[-1].end()
                phrase = text[start:end]
                result.append((phrase, start, end))
        return result

    def _lookup(self, phrase: str, context: list[str] | None = None) -> dict | None:
        """Look up a phrase in the index. Returns best match dict or None."""
        key = _normalize(phrase)
        if not key or len(key) < 3:
            return None

        with self._index_lock:
            # Exact match
            if key in self._index:
                return self._index[key]

            # Fuzzy match — scan index keys with sufficient prefix overlap
            best_score = 0.0
            best_entry = None
            for idx_key, entry in self._index.items():
                # Quick pre-filter: first char must match to avoid full scan cost
                if not idx_key or idx_key[0] != key[0]:
                    continue
                score = _fuzzy_score(key, idx_key) * entry["confidence"]
                if score > best_score:
                    best_score = score
                    best_entry = entry

            if best_entry and best_score >= THRESH_MENTION:
                result = dict(best_entry)
                result["confidence"] = best_score
                return result

        return None

    def get_full_record(self, canonical: str, sheet: str, row: int) -> dict | None:
        """
        Get full record. Checks hot cache first, falls back to live API call.
        """
        # Tier 2: hot cache
        with self._hot_lock:
            if canonical in self._hot_cache:
                return self._hot_cache[canonical]

        # Tier 3: live fetch
        try:
            cfg = SHEET_CONFIGS.get(sheet)
            if not cfg:
                return None
            svc = _build_service()
            col_end = cfg["range"].split("!")[-1].split(":")[1]
            resp = svc.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range=f"'{sheet}'!A{row}:{col_end}{row}",
            ).execute()
            rows = resp.get("values", [])
            if rows:
                return {"row": row, "data": rows[0], "type": sheet}
        except Exception as e:
            logger.warning(f"NounResolver: live fetch failed for row {row} in {sheet}: {e}")
        return None

    def increment_contact_score(self, row: int, amount: int = 1):
        """Increment contact_score for a contacts row. Batched externally."""
        try:
            svc = _build_service()
            col = "CO"  # contact_score column
            resp = svc.spreadsheets().values().get(
                spreadsheetId=SHEET_ID,
                range=f"'NDR DRAAS Google contacts.csv'!{col}{row}",
            ).execute()
            current = 0
            vals = resp.get("values", [])
            if vals and vals[0]:
                try:
                    current = int(vals[0][0])
                except ValueError:
                    pass
            svc.spreadsheets().values().update(
                spreadsheetId=SHEET_ID,
                range=f"'NDR DRAAS Google contacts.csv'!{col}{row}",
                valueInputOption="RAW",
                body={"values": [[str(current + amount)]]},
            ).execute()
        except Exception as e:
            logger.warning(f"NounResolver: increment_contact_score failed: {e}")


# ── Result type ────────────────────────────────────────────────────────────────

class ResolveResult:
    def __init__(self, corrected_text: str, substitutions: list, needs_confirmation: list):
        self.corrected_text    = corrected_text
        self.substitutions     = substitutions       # auto-replaced
        self.needs_confirmation = needs_confirmation  # ambiguous, needs user input

    def has_changes(self) -> bool:
        return bool(self.substitutions or self.needs_confirmation)

    def summary(self) -> str:
        """Human-readable summary of changes made."""
        lines = []
        for s in self.substitutions:
            lines.append(f"'{s['original']}' → '{s['canonical']}' ({s['type']}, {s['confidence']:.0%} confident)")
        return "\n".join(lines) if lines else ""

    def to_dict(self) -> dict:
        return {
            "corrected_text":     self.corrected_text,
            "substitutions":      self.substitutions,
            "needs_confirmation": self.needs_confirmation,
        }
