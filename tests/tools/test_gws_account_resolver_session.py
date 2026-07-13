"""Regression test for ``gws_account_resolver_tool._current_telegram_id``.

Pins the fix for a bug where the tool read ``os.environ`` directly instead of
``gateway.session_context.get_session_env``. Since the
``HERMES_SESSION_USER_ID`` refactor, the session user id lives in a per-task
``ContextVar`` and is never mirrored into process-global ``os.environ`` for
in-process tool calls -- ``gws_resolve_account`` runs in-process (no
subprocess), so the old code returned ``None`` (-> "No session user context")
in *every* session, interactive or cron. Confirmed live via repeated
``agent.log``/``errors.log`` entries in production, across ordinary
interactive session ids, not just cron.

The invariant this test enforces: once
``gateway.session_context.set_session_vars(user_id=...)`` has been called for
the current task (as the gateway does for every inbound message), a native
in-process tool must be able to see that id via ``_current_telegram_id()`` --
even though ``os.environ`` was never touched.
"""

import os
import threading

from gateway.session_context import clear_session_vars, set_session_vars
from tools.gws_account_resolver_tool import _current_telegram_id


def test_reads_contextvar_even_though_os_environ_is_untouched():
    """Reproduces the bug: contextvar set, os.environ deliberately untouched."""
    assert "HERMES_SESSION_USER_ID" not in os.environ  # sanity: no env leak

    tokens = set_session_vars(user_id="1000000001")
    try:
        assert _current_telegram_id() == "1000000001"
        # The whole point of the bug: os.environ was NEVER written for this.
        assert "HERMES_SESSION_USER_ID" not in os.environ
    finally:
        clear_session_vars(tokens)


def test_returns_none_when_session_explicitly_cleared():
    clear_session_vars([])
    assert _current_telegram_id() is None


def test_falls_back_to_os_environ_when_contextvar_was_never_set():
    """CLI/cron-style processes that never call ``set_session_vars()`` at all
    (the ContextVar stays at its never-set default) should still resolve via
    the ``os.environ`` fallback baked into ``get_session_env()`` -- this
    preserves existing CLI compatibility. A bare new OS thread gets a fresh,
    never-set ContextVar state (thread creation does not copy the parent
    thread's contextvars context), which is what we need to exercise that
    fallback path in isolation from the other tests in this module.
    """
    result = {}

    def _worker():
        os.environ["HERMES_SESSION_USER_ID"] = "9999999999"
        try:
            result["tid"] = _current_telegram_id()
        finally:
            os.environ.pop("HERMES_SESSION_USER_ID", None)

    t = threading.Thread(target=_worker)
    t.start()
    t.join()

    assert result["tid"] == "9999999999"
