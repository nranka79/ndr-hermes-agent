"""Regression tests for cron job "owner" identity wiring.

Root cause pinned here: cron/scheduler.py::run_job deliberately clears
HERMES_SESSION_PLATFORM/CHAT_ID/USER_ID for every job run (so a cron job
can't impersonate a live chat for routing purposes -- see the comment in
run_job). A side effect nobody scoped: this also means GWS/vault tools have
no user id to resolve a token for, so any cron job touching Gmail/Calendar/
Drive/Sheets gets "No session user context" from tools.gws_auth and the
agent tells the user to re-authorize even when a valid token exists.

The fix: jobs carry an explicit ``owner`` field (canonical vault user_id of
whoever created them, set in tools/cronjob_tools.py at creation time). run_job
sets a narrow, separate ContextVar (HERMES_CRON_JOB_OWNER_ID) from
job["owner"] for the duration of the run. GWS/vault tools read it via
gateway.session_context.get_gws_identity_env(), which falls back to it only
when HERMES_SESSION_USER_ID is empty -- routing vars (platform/chat_id/etc.)
are untouched, preserving the existing isolation guarantees.
"""

from unittest.mock import MagicMock, patch

from cron.scheduler import run_job
from gateway.session_context import _VAR_MAP, get_gws_identity_env


def _run_job_with_agent_spy(job, tmp_path):
    """Run job() with AIAgent mocked out; capture what
    get_gws_identity_env() saw *during* the (fake) agent run, synchronously
    in the same execution context run_job uses (no thread/task hop for this
    mocked path, so ContextVar state set earlier in run_job is visible here).
    """
    seen = {}

    def _fake_run_conversation(*_a, **_kw):
        seen["gws_identity_during_run"] = get_gws_identity_env()
        return {"final_response": "ok"}

    fake_db = MagicMock()
    with patch("cron.scheduler._hermes_home", tmp_path), \
         patch("cron.scheduler._resolve_origin", return_value=None), \
         patch("dotenv.load_dotenv"), \
         patch("hermes_state.SessionDB", return_value=fake_db), \
         patch(
             "hermes_cli.runtime_provider.resolve_runtime_provider",
             return_value={
                 "api_key": "test-key",
                 "base_url": "https://example.invalid/v1",
                 "provider": "openrouter",
                 "api_mode": "chat_completions",
             },
         ), \
         patch("run_agent.AIAgent") as mock_agent_cls:
        mock_agent = MagicMock()
        mock_agent.run_conversation.side_effect = _fake_run_conversation
        mock_agent_cls.return_value = mock_agent

        result = run_job(job)

    return result, seen


class TestCronOwnerIdentity:
    def test_gws_identity_available_during_job_with_owner(self, tmp_path):
        job = {
            "id": "job-with-owner",
            "name": "Gmail cleanup",
            "prompt": "clean up my inbox",
            "owner": "ndr-1000000001",
        }

        result, seen = _run_job_with_agent_spy(job, tmp_path)

        assert result[0] is True
        assert seen["gws_identity_during_run"] == "ndr-1000000001"

    def test_gws_identity_empty_when_job_has_no_owner(self, tmp_path):
        """Legacy jobs created before the owner field existed must not crash --
        they just can't resolve a GWS token under cron until an owner is set,
        same failure mode as before this fix (no regression, no new crash)."""
        job = {
            "id": "job-no-owner",
            "name": "legacy job",
            "prompt": "do something",
        }

        result, seen = _run_job_with_agent_spy(job, tmp_path)

        assert result[0] is True
        assert seen["gws_identity_during_run"] == ""

    def test_owner_contextvar_cleared_after_job_completes(self, tmp_path):
        """The owner var must not leak into whatever runs next in this
        process (e.g. the next cron job, or a live interactive session sharing
        the same worker thread's context)."""
        job = {
            "id": "job-with-owner-2",
            "name": "Gmail cleanup",
            "prompt": "clean up my inbox",
            "owner": "ndr-1000000001",
        }

        _run_job_with_agent_spy(job, tmp_path)

        assert _VAR_MAP["HERMES_CRON_JOB_OWNER_ID"].get() == ""
        assert get_gws_identity_env() == ""

    def test_owner_does_not_leak_into_session_user_id(self, tmp_path):
        """HERMES_SESSION_USER_ID itself must stay cleared during cron runs --
        only the narrow GWS-identity helper should see the owner id. This
        preserves the existing routing-isolation guarantees documented in
        run_job (background-process notifications, TTS platform selection,
        skill-disable lists, send_message gating all key off
        HERMES_SESSION_USER_ID/PLATFORM/CHAT_ID)."""
        job = {
            "id": "job-with-owner-3",
            "name": "Gmail cleanup",
            "prompt": "clean up my inbox",
            "owner": "ndr-1000000001",
        }
        seen = {}

        def _fake_run_conversation(*_a, **_kw):
            from gateway.session_context import get_session_env
            seen["session_user_id"] = get_session_env("HERMES_SESSION_USER_ID", "")
            return {"final_response": "ok"}

        fake_db = MagicMock()
        with patch("cron.scheduler._hermes_home", tmp_path), \
             patch("cron.scheduler._resolve_origin", return_value=None), \
             patch("dotenv.load_dotenv"), \
             patch("hermes_state.SessionDB", return_value=fake_db), \
             patch(
                 "hermes_cli.runtime_provider.resolve_runtime_provider",
                 return_value={
                     "api_key": "test-key",
                     "base_url": "https://example.invalid/v1",
                     "provider": "openrouter",
                     "api_mode": "chat_completions",
                 },
             ), \
             patch("run_agent.AIAgent") as mock_agent_cls:
            mock_agent = MagicMock()
            mock_agent.run_conversation.side_effect = _fake_run_conversation
            mock_agent_cls.return_value = mock_agent
            run_job(job)

        assert seen["session_user_id"] == ""
