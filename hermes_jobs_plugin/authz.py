"""Vault-backed identity and authorization helpers for the jobs board.

The board trusts the ``X-Forwarded-Email`` header supplied by oauth2-proxy.
That only answers "who did Google say this is?" -- it does not tell us which
jobs belong to that person, because the same human can appear under several
email aliases and a Telegram user id in ``tasks.tenant``. This module resolves
the signed-in email to a canonical gws-vault identity and returns every alias
that identity owns, so the board can filter jobs consistently across surfaces.

Admin rights are deliberately strict: only ``identity["role"] == "admin"``
counts. ``permissions.vault_admin`` is NOT accepted here. This matches the
requested rule that only people whose vault role is admin may see all users'
jobs. If the vault is unreachable we fail closed: no admin rights, and the
caller keeps only their exact email as an owner alias.

The vault socket is mounted read-only into the jobs-board container. All calls
are short, local Unix-socket requests and are cached briefly to keep the 5s
board poll cheap.
"""

from __future__ import annotations

import json
import logging
import os
import socket
import threading
import time
from typing import Any, Dict, FrozenSet, NamedTuple, Optional

logger = logging.getLogger("jobs-board.authz")

# Path of the gws-vault Unix socket inside the jobs-board container. The host
# socket already exists at the same path; docker-compose bind-mounts it in.
VAULT_SOCKET = os.environ.get("GWS_VAULT_SOCKET", "/run/gws-vault/vault.sock")

# A short cache keeps per-request vault reads off the hot path. It is short
# enough that an admin/alias change in the vault appears within a minute.
CACHE_TTL_SECONDS = float(os.environ.get("BOARD_IDENTITY_CACHE_SECONDS", "60"))

# Never let a dead vault socket hang the aiohttp event loop thread.
CALL_TIMEOUT_SECONDS = float(os.environ.get("BOARD_VAULT_TIMEOUT_SECONDS", "3"))


class VaultError(RuntimeError):
    """Raised when the vault socket is missing, unreachable, or malformed."""


class Identity(NamedTuple):
    """The board's normalized view of one signed-in person.

    ``aliases`` is a lower-cased set of every identity value the vault links to
    this person (emails, Telegram ids, slugs, etc.). It is what ``tasks.tenant``
    is matched against. ``is_admin`` is true only for vault role ``admin``.
    """

    email: str
    user_id: Optional[str]
    aliases: FrozenSet[str]
    is_admin: bool


# email -> (expires_at_epoch_seconds, Identity). Guarded by a plain lock because
# aiohttp resolves identities through ``asyncio.to_thread`` (multiple worker
# threads can race on first access for the same email).
_identity_cache: Dict[str, tuple[float, Identity]] = {}
_cache_lock = threading.Lock()


def _call(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Send one newline-delimited JSON request to gws-vault and decode its reply.

    The vault protocol is a single JSON line in, a single JSON line out. Every
    failure is converted to ``VaultError`` so callers have one exception type to
    handle and can fail closed on any transport problem.
    """
    if not VAULT_SOCKET or not os.path.exists(VAULT_SOCKET):
        raise VaultError("vault socket not found at %s" % (VAULT_SOCKET))

    raw = (json.dumps(payload) + "\n").encode("utf-8")
    sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
    sock.settimeout(CALL_TIMEOUT_SECONDS)
    try:
        sock.connect(VAULT_SOCKET)
        sock.sendall(raw)
        buffer = b""
        while b"\n" not in buffer:
            chunk = sock.recv(65536)
            if not chunk:
                break
            buffer += chunk
        if not buffer:
            raise VaultError("vault closed the connection without a response")
        line = buffer.split(b"\n", 1)[0].decode("utf-8")
        response = json.loads(line)
        if not isinstance(response, dict):
            raise VaultError("vault returned a non-object response")
        return response
    except (OSError, ValueError) as exc:
        raise VaultError("vault request failed: %s" % exc) from exc
    finally:
        try:
            sock.close()
        except OSError:
            pass


def _resolve_email(email: str) -> Optional[str]:
    """Resolve an email alias to the vault's canonical ``user_id``.

    ``resolve`` needs no secret: it only maps an alias to an opaque user id and
    returns no token material. A miss returns ``None`` rather than raising.
    """
    response = _call({
        "op": "resolve",
        "identity_type": "email",
        "identity_value": email,
    })
    if not response.get("ok"):
        return None
    user_id = response.get("user_id")
    return str(user_id).strip() if user_id else None


def _get_identity(user_id: str) -> Optional[Dict[str, Any]]:
    """Read one identity record from the vault using its own user id.

    ``session_uid`` equals the target user id here, which is the vault's
    supported self-read path. No admin secret is needed, and no token is read.
    """
    response = _call({
        "op": "get_identity",
        "user_id": user_id,
        "session_uid": user_id,
    })
    if not response.get("ok"):
        return None
    identity = response.get("identity")
    return identity if isinstance(identity, dict) else None


def _aliases_from_identity(identity: Dict[str, Any], email: str, user_id: str) -> FrozenSet[str]:
    """Collect every lower-cased identifier that can appear in ``tasks.tenant``.

    The vault stores aliases in ``identity["identities"]``, a mapping such as
    ``{"email": ["a@x", "b@x"], "telegram": ["123"]}``. The canonical user id is
    included too, so a future creator that stores it directly still matches.
    """
    aliases = {email.lower(), user_id.lower()}
    identities = identity.get("identities") or {}
    if isinstance(identities, dict):
        for values in identities.values():
            if not isinstance(values, (list, tuple, set)):
                continue
            for value in values:
                text = str(value or "").strip().lower()
                if text:
                    aliases.add(text)
    return frozenset(aliases)


def identity_for_email(email: str) -> Identity:
    """Return the cached identity/alias/admin view for a signed-in email.

    This is the only function board_server.py needs. It never raises: a missing
    email, an unknown alias, or a vault outage all produce a safe non-admin
    identity whose only owner alias is the exact email (when one was supplied).
    That fail-closed behavior means a vault outage cannot accidentally grant
    All-jobs access.
    """
    normalized = (email or "").strip().lower()
    if not normalized or normalized == "unknown":
        return Identity(email=normalized, user_id=None, aliases=frozenset(), is_admin=False)

    now = time.time()
    with _cache_lock:
        cached = _identity_cache.get(normalized)
        if cached and cached[0] > now:
            return cached[1]

    aliases = frozenset({normalized})
    user_id: Optional[str] = None
    is_admin = False

    try:
        user_id = _resolve_email(normalized)
        if user_id:
            identity = _get_identity(user_id)
            if identity:
                aliases = _aliases_from_identity(identity, normalized, user_id)
                # Strict role check by design. Do not widen this to
                # permissions.vault_admin without an explicit product decision.
                is_admin = str(identity.get("role") or "").strip().lower() == "admin"
    except VaultError as exc:
        # Fail closed. The caller still sees jobs stored under their exact email.
        logger.warning("jobs board: vault identity lookup failed for %s: %s", normalized, exc)
    except Exception:
        logger.exception("jobs board: unexpected vault identity failure for %s", normalized)

    result = Identity(email=normalized, user_id=user_id, aliases=aliases, is_admin=is_admin)
    with _cache_lock:
        _identity_cache[normalized] = (now + CACHE_TTL_SECONDS, result)
    return result


def clear_cache() -> None:
    """Drop the cached identities (used by tests or after a manual vault change)."""
    with _cache_lock:
        _identity_cache.clear()
