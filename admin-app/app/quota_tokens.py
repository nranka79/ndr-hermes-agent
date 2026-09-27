"""Device tokens for the Android quota app.

The Android app signs in with Google (Google Sign-In SDK), sends its Google ID
token to /quota/api/device-login, and this module issues a long-lived HMAC
token the app (and its widget) reuse until it expires — no server state.

Signed with SESSION_SECRET (the admin-app's own secret), so no new env var.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time

DEVICE_TTL_DAYS = 30


def _secret() -> str:
    return os.environ.get("SESSION_SECRET", "")


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _unb64(s: str) -> bytes:
    return base64.urlsafe_b64decode(s + "=" * (-len(s) % 4))


def issue_device_token(email: str) -> str:
    payload = {"email": email, "exp": int(time.time()) + DEVICE_TTL_DAYS * 86400}
    body = _b64(json.dumps(payload).encode())
    sig = _b64(hmac.new(_secret().encode(), body.encode(), hashlib.sha256).digest())
    return f"{body}.{sig}"


def verify_device_token(token: str) -> str | None:
    """Return the token's email, or None if invalid/expired."""
    if not token or not _secret():
        return None
    try:
        body, sig = token.split(".")
        expected = hmac.new(_secret().encode(), body.encode(), hashlib.sha256).digest()
        if not hmac.compare_digest(_unb64(sig), expected):
            return None
        payload = json.loads(_unb64(body))
        if payload.get("exp", 0) < time.time():
            return None
        return payload.get("email")
    except Exception:  # noqa: BLE001
        return None