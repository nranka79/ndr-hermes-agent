"""API-key rotation helpers for multi-account vendor services.

Hermes may hold several accounts/keys for the same vendor (Tavily, Apify,
Firecrawl, ...). Each key brings its own free credits, so we keep a "key
series" per vendor and try keys in order until one works.

Convention: the base env var is key #1 (``TAVILY_API_KEY``,
``APIFY_API_KEY``, ``FIRECRAWL_API_KEY``, ...) and extra keys are ``_2``,
``_3``, ... until the first unset var::

    TAVILY_API_KEY=abc       # key 1
    TAVILY_API_KEY_2=def     # key 2
    TAVILY_API_KEY_3=ghi     # key 3

A key is considered *dead* when the vendor rejects it with an auth /
credit / rate-limit error (status in :data:`KEY_DEAD_STATUSES`). Dead
keys are skipped for a cooldown window (in case the account is recharged),
then retried. The last key that worked is remembered and tried first on
the next call, so requests don't waste time on dead keys.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Callable, Iterator, List, Optional

logger = logging.getLogger(__name__)

# Seconds a rejected key stays blacklisted before being retried.
DEAD_COOLDOWN_SECONDS = 300.0

# HTTP statuses that mean "this key is useless right now": 401/403 bad
# credentials, 402 out of credits, 429 rate-limited.
KEY_DEAD_STATUSES = frozenset({401, 402, 403, 429})


def key_series(base_env: str) -> List[str]:
    """Return the configured key series for ``base_env`` in order.

    ``base_env`` is key #1; ``<base_env>_2``, ``<base_env>_3``, ...
    follow until the first unset or blank var.
    """
    keys: List[str] = []
    first = (os.environ.get(base_env) or "").strip()
    if first:
        keys.append(first)
    index = 2
    while True:
        extra = (os.environ.get(f"{base_env}_{index}") or "").strip()
        if not extra:
            break
        keys.append(extra)
        index += 1
    return keys


def has_key_series(base_env: str) -> bool:
    """Return True when at least one key in the series is configured."""
    return bool(key_series(base_env))


def mask_key(key: str) -> str:
    """Short non-secret fingerprint for logs (never log full keys)."""
    if len(key) <= 8:
        return "***"
    return f"...{key[-4:]}"


class AllKeysRejectedError(RuntimeError):
    """Raised when every configured key in a series was rejected by the vendor."""


class KeyRotator:
    """Try a vendor key series in order; remember which keys work.

    Usage::

        rotator = KeyRotator("TAVILY_API_KEY")
        try:
            result = rotator.run(call_vendor, is_key_dead)
        except AllKeysRejectedError as exc:
            ...  # all keys rejected by the vendor
    """

    def __init__(self, base_env: str):
        self.base_env = base_env
        self._preferred: Optional[str] = None
        self._dead_at: dict = {}

    def iter_keys(self) -> Iterator[str]:
        """Yield keys: last-working (preferred) first, then series order."""
        now = time.monotonic()

        def alive(key: str) -> bool:
            dead_at = self._dead_at.get(key)
            if dead_at is None:
                return True
            if now - dead_at < DEAD_COOLDOWN_SECONDS:
                return False
            del self._dead_at[key]
            return True

        ordered = list(key_series(self.base_env))
        if self._preferred in ordered:
            ordered.remove(self._preferred)
            ordered.insert(0, self._preferred)
        for key in ordered:
            if alive(key):
                yield key

    def mark_worked(self, key: str) -> None:
        """Remember ``key`` as the last key that succeeded."""
        self._preferred = key
        self._dead_at.pop(key, None)

    def mark_dead(self, key: str) -> None:
        """Blacklist ``key`` for :data:`DEAD_COOLDOWN_SECONDS`."""
        self._dead_at[key] = time.monotonic()
        if self._preferred == key:
            self._preferred = None
        logger.warning(
            "%s key %s rejected by vendor - marking dead",
            self.base_env,
            mask_key(key),
        )

    def run(
        self,
        call: Callable[[str], object],
        is_key_dead: Callable[[Exception], bool],
    ) -> object:
        """Call ``call(key)`` for each key until one succeeds.

        ``call(key)`` raises on failure. If ``is_key_dead(exc)`` is True
        the key is blacklisted before moving to the next one; transient
        errors just move to the next key. On success the key is marked
        preferred and its result returned. Raises
        :class:`AllKeysRejectedError` when keys were rejected, the last
        exception when keys failed transiently, or ``ValueError`` when no
        key is configured.
        """
        last_error: Optional[Exception] = None
        attempted = 0
        rejected = 0
        for key in self.iter_keys():
            attempted += 1
            try:
                result = call(key)
            except Exception as exc:  # noqa: BLE001 — caller decides how to classify
                last_error = exc
                if is_key_dead(exc):
                    rejected += 1
                    self.mark_dead(key)
                continue
            self.mark_worked(key)
            return result
        if attempted == 0:
            raise ValueError(
                f"no keys configured for {self.base_env} — "
                f"set {self.base_env} or {self.base_env}_2, ..."
            )
        if rejected:
            raise AllKeysRejectedError(
                f"all {attempted} configured {self.base_env} key(s) "
                "were rejected by the vendor"
            )
        assert last_error is not None
        raise last_error
