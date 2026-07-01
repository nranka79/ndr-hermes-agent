"""Tests for the gateway-boot ``HERMES_SESSION_*`` os.environ scrub.

Defense-in-depth regression for the misidentification bug: a long-lived
gateway process can have stale ``HERMES_SESSION_USER_ID`` (or related
session vars) sitting in ``os.environ`` from process startup.  The
contextvar path is the source of truth, but ``get_session_env()`` falls
back to ``os.environ`` when the contextvar is at its default ``_UNSET``
sentinel.  That fallback MUST return ``""`` after the scrub, not the
stale value, so any tool that runs in the gateway without an explicit
session binding still gets a safe empty string.
"""

import os
import subprocess
import sys
import textwrap

import pytest

from gateway.session_context import (
    _SESSION_USER_ID,
    _UNSET,
    get_session_env,
    scrub_stale_session_env_from_environ,
)


# All session var prefixes the scrub is responsible for.  The function
# must scrub BOTH ``HERMES_SESSION_*`` and ``HERMES_CRON_AUTO_DELIVER_*``
# (the cron auto-delivery contextvars are bound per-cron-job and must
# never bleed into a regular gateway request via os.environ fallback).
SCRUB_PREFIXES = ("HERMES_SESSION_", "HERMES_CRON_AUTO_DELIVER_")


@pytest.fixture(autouse=True)
def _isolate_session():
    """Reset contextvars so prior tests don't pollute the fallback path."""
    _SESSION_USER_ID.set(_UNSET)
    yield
    _SESSION_USER_ID.set(_UNSET)


def _env_with_stale_session_vars() -> dict:
    """A pretend-host env that simulates every leak path the user has
    actually hit in production:
      * a shell that ``export``'d HERMES_SESSION_USER_ID
      * a docker-compose env block that set HERMES_SESSION_USER_NAME
      * a previous gateway process that wrote HERMES_SESSION_KEY
      * a cron job that left HERMES_CRON_AUTO_DELIVER_PLATFORM around
    Plus a non-session var (PATH) that must NOT be touched.
    """
    return {
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "HERMES_SESSION_USER_ID": "sales1.blr@draas.com",
        "HERMES_SESSION_USER_NAME": "Bharat Hawaldar",
        "HERMES_SESSION_KEY": "stale-session-key",
        "HERMES_SESSION_PLATFORM": "telegram",
        "HERMES_SESSION_CHAT_ID": "stale-chat",
        "HERMES_CRON_AUTO_DELIVER_PLATFORM": "telegram",
        "HERMES_CRON_AUTO_DELIVER_CHAT_ID": "stale-cron-chat",
        "HERMES_HOME": "/data/hermes",
    }


def test_scrub_removes_every_hermes_session_var():
    """All HERMES_SESSION_* and HERMES_CRON_AUTO_DELIVER_* keys are
    removed; non-session vars (PATH, HERMES_HOME) are preserved."""
    with pytest.MonkeyPatch.context() as mp:
        for k, v in _env_with_stale_session_vars().items():
            mp.setenv(k, v)

        pre_scrub_session_keys = {
            k for k in os.environ
            if k.startswith(SCRUB_PREFIXES)
        }
        assert pre_scrub_session_keys, "test setup failed: no session vars to scrub"

        removed = scrub_stale_session_env_from_environ()

    # Every session var gone …
    for k in os.environ:
        assert not k.startswith(SCRUB_PREFIXES), (
            f"scrub left {k!r} in os.environ (value={os.environ.get(k)!r})"
        )
    # … and we got the right count back.
    assert removed == len(pre_scrub_session_keys)
    # HERMES_HOME is not a session var — preserved (conftest sets it
    # to a tmpdir for test isolation, so we just check it's still set).
    assert "HERMES_HOME" in os.environ


def test_scrub_is_idempotent():
    """Calling twice is a no-op the second time, so wrapping it in
    startup code is safe even if multiple entry points call it."""
    with pytest.MonkeyPatch.context() as mp:
        for k, v in _env_with_stale_session_vars().items():
            mp.setenv(k, v)

        first = scrub_stale_session_env_from_environ()
        second = scrub_stale_session_env_from_environ()
        third = scrub_stale_session_env_from_environ()

    assert first > 0
    assert second == 0
    assert third == 0


def test_get_session_env_returns_empty_after_scrub_when_contextvar_unset():
    """The full defense-in-depth chain: with a stale os.environ set,
    the contextvar at _UNSET, AFTER the scrub, get_session_env() must
    return "" — NOT the stale value.  This is the bug the user hit:
    tools reading get_session_env("HERMES_SESSION_USER_ID") saw a
    previous request's user because os.environ leaked.
    """
    with pytest.MonkeyPatch.context() as mp:
        for k, v in _env_with_stale_session_vars().items():
            mp.setenv(k, v)
        _SESSION_USER_ID.set(_UNSET)  # CLI / test path: no explicit bind

        # Pre-scrub: fallback returns the stale value (the bug surface).
        assert get_session_env("HERMES_SESSION_USER_ID") == "sales1.blr@draas.com"

        # Scrub and re-check: fallback now returns "" (the fix).
        scrub_stale_session_env_from_environ()
        assert get_session_env("HERMES_SESSION_USER_ID") == ""
        assert get_session_env("HERMES_SESSION_USER_NAME") == ""
        assert get_session_env("HERMES_SESSION_KEY") == ""
        assert get_session_env("HERMES_SESSION_PLATFORM") == ""
        assert get_session_env("HERMES_SESSION_CHAT_ID") == ""
        assert get_session_env("HERMES_CRON_AUTO_DELIVER_PLATFORM") == ""
        assert get_session_env("HERMES_CRON_AUTO_DELIVER_CHAT_ID") == ""


def test_get_session_env_still_uses_contextvar_after_scrub():
    """The scrub must NOT touch the contextvar path.  When the
    contextvar is explicitly bound, get_session_env() must keep
    returning that value, even after a scrub ran.  The contextvar is
    still the source of truth.
    """
    with pytest.MonkeyPatch.context() as mp:
        for k, v in _env_with_stale_session_vars().items():
            mp.setenv(k, v)
        from gateway.session_context import set_session_vars
        tokens = set_session_vars(
            user_id="ndr@draas.com",
            user_name="Nishant Ranka",
            session_key="real-session",
        )
        try:
            scrub_stale_session_env_from_environ()
            # Contextvar path — still wins.
            assert get_session_env("HERMES_SESSION_USER_ID") == "ndr@draas.com"
            assert get_session_env("HERMES_SESSION_USER_NAME") == "Nishant Ranka"
            assert get_session_env("HERMES_SESSION_KEY") == "real-session"
        finally:
            from gateway.session_context import clear_session_vars
            clear_session_vars(tokens)


def test_scrub_runs_in_subprocess_with_real_python_import(monkeypatch):
    """The scrub must be import-safe in a fresh subprocess — no
    implicit dependencies on prior state, on conftest, or on the
    gateway runtime.  This is the real-world call path:
    ``hermes gateway run`` → python starts → imports gateway.run →
    start_gateway() runs the scrub on a brand-new process.
    """
    # Set the env on the parent so the child inherits it.
    for k, v in _env_with_stale_session_vars().items():
        monkeypatch.setenv(k, v)

    child_script = textwrap.dedent("""
        import os, sys
        from gateway.session_context import scrub_stale_session_env_from_environ
        n = scrub_stale_session_env_from_environ()
        # What remains in os.environ after the scrub?
        remaining = sorted(k for k in os.environ if k.startswith(("HERMES_SESSION_", "HERMES_CRON_AUTO_DELIVER_")))
        print(f"REMOVED={n}")
        print(f"REMAINING={','.join(remaining)}")
        # Exit code 0 = clean; 1 = leak.
        sys.exit(0 if not remaining else 1)
    """)
    result = subprocess.run(
        [sys.executable, "-c", child_script],
        capture_output=True,
        text=True,
        env={**os.environ},  # child inherits the monkeypatched parent env
    )
    assert result.returncode == 0, (
        f"child leaked HERMES_SESSION_* after scrub:\n"
        f"  stdout: {result.stdout}\n  stderr: {result.stderr}"
    )
    assert "REMOVED=7" in result.stdout, (
        f"expected to remove 7 session vars, got: {result.stdout!r}"
    )
    # REMAINING is followed by an empty string (the join of an empty list)
    # then a newline from print() — that's the "no leak" signal.  If the
    # scrub missed a var, REMAINING would contain a non-empty key list.
    assert "REMAINING=\n" in result.stdout, (
        f"expected empty REMAINING, got: {result.stdout!r}"
    )
