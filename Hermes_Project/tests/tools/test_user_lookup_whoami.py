"""Tests for tools/user_lookup_tool.py — focused on session-identity reads.

Verifies that the ``whoami`` operation returns the *current* request's
user identity, not whatever stale value is sitting in ``os.environ`` from
process startup or a prior request.  Regression for the misidentification
bug: ``os.environ.get("HERMES_SESSION_USER_ID")`` was reading a stale
value left over from a previous request that ran in the same
long-lived gateway process, so the agent misidentified the active user.
"""

import json
import os
import sys
from unittest.mock import patch

import pytest

from gateway.session_context import (
    _SESSION_USER_ID,
    _SESSION_USER_NAME,
    _UNSET,
    set_session_vars,
    clear_session_vars,
)


@pytest.fixture(autouse=True)
def _isolate_session():
    """Reset session contextvars around each test to avoid cross-test
    state leak (we are running pytest directly, not under the
    subprocess-per-test isolation plugin)."""
    _SESSION_USER_ID.set(_UNSET)
    _SESSION_USER_NAME.set(_UNSET)
    yield
    _SESSION_USER_ID.set(_UNSET)
    _SESSION_USER_NAME.set(_UNSET)


def test_whoami_returns_contextvar_value_when_set():
    """Happy path: gateway has bound the current request's identity
    into the contextvar.  ``whoami`` must return that value, not
    whatever's in ``os.environ``."""
    from tools.user_lookup_tool import _whoami

    tokens = set_session_vars(user_id="ndr@draas.com", user_name="Nishant Ranka")
    try:
        with patch.dict(
            os.environ,
            {
                "HERMES_SESSION_USER_ID": "stale-from-prior-request",
                "HERMES_SESSION_USER_NAME": "Stale User",
            },
            clear=False,
        ):
            result = json.loads(_whoami())
    finally:
        clear_session_vars(tokens)

    assert result["telegram_id"] == "ndr@draas.com", (
        f"contextvar must win over stale os.environ; got {result['telegram_id']!r}"
    )
    assert result["telegram_username"] == "Nishant Ranka"


def test_whoami_returns_stale_value_when_contextvar_unset_cli_fallback():
    """CLI / cron / test paths never call ``set_session_vars`` — the
    contextvars stay at their default ``_UNSET`` sentinel.  In that
    case, ``get_session_env()`` falls back to ``os.environ``, which is
    the documented behaviour for those paths.  This is the regression
    guard: we must NOT silently break the CLI/cron fallback by always
    returning empty."""
    from tools.user_lookup_tool import _whoami

    # Force contextvar to _UNSET (other tests in this file may have left
    # it at "" via clear_session_vars).
    _SESSION_USER_ID.set(_UNSET)
    _SESSION_USER_NAME.set(_UNSET)

    with patch.dict(
        os.environ,
        {
            "HERMES_SESSION_USER_ID": "cli-fallback-user",
            "HERMES_SESSION_USER_NAME": "CLI User",
        },
        clear=True,
    ):
        result = json.loads(_whoami())

    assert result["telegram_id"] == "cli-fallback-user"
    assert result["telegram_username"] == "CLI User"


def test_whoami_returns_error_when_no_identity_anywhere():
    """No contextvar set AND no os.environ fallback — must return the
    documented error, never a misleading default."""
    from tools.user_lookup_tool import _whoami

    _SESSION_USER_ID.set(_UNSET)
    _SESSION_USER_NAME.set(_UNSET)

    # Make sure os.environ doesn't accidentally have it.
    env_without_session = {
        k: v for k, v in os.environ.items() if not k.startswith("HERMES_SESSION_")
    }
    with patch.dict(os.environ, env_without_session, clear=True):
        result = json.loads(_whoami())

    assert "error" in result
    assert "user_id not available" in result["error"]


def test_whoami_empty_username_is_none_not_string():
    """The schema documents ``telegram_username`` as nullable.  When
    the contextvar is set but the username is empty, we must return
    ``None`` (JSON null), not the empty string — so downstream JSON
    consumers don't have to special-case ``""``."""
    from tools.user_lookup_tool import _whoami

    tokens = set_session_vars(user_id="ndr@draas.com", user_name="")
    try:
        with patch.dict(
            os.environ,
            {"HERMES_SESSION_USER_ID": "stale", "HERMES_SESSION_USER_NAME": "stale"},
            clear=False,
        ):
            result = json.loads(_whoami())
    finally:
        clear_session_vars(tokens)

    assert result["telegram_id"] == "ndr@draas.com"
    assert result["telegram_username"] is None
