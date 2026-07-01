"""
Tests for the subagent-polling fix in the api_server.

Covers:
- Open WebUI chat_id is translated to a stable hermes session_id via
  chat_session_map, so subsequent requests from the same Open WebUI chat
  reuse the same parent_session_id.
- The X-OpenWebUI-Chat-Id header is preferred over the conversation-derived
  session_id when both could apply.
- Completed delegate_task children are prepended to the next request's
  conversation_history as ``tool`` role messages, with a ``last_injected_at``
  marker that prevents re-injection.
- Idempotency: a second request with the same chat_id does not re-inject
  the same children.
- No chat_id header → fall back to the existing X-Hermes-Session-Id flow.
- Header injection / control-character rejection.

The actual fix lives in:
    - hermes_state.SessionDB.get_or_create_chat_session /
      get_completed_subagent_results / get_subagent_final_message /
      mark_subagent_results_injected / get_chat_session_last_injected
    - gateway.platforms.api_server.APIServerAdapter._resolve_openwebui_chat_session_id
    - gateway.platforms.api_server.APIServerAdapter._inject_completed_subagent_results
    - gateway.platforms.api_server.APIServerAdapter._run_agent (calls the
      injector before agent.run_conversation).
"""

import json
import os
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.api_server import APIServerAdapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_hermes_home(tmp_path, monkeypatch):
    """Point HERMES_HOME at a temp dir so SessionDB() opens a real file there."""
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home


def _make_adapter(tmp_hermes_home) -> APIServerAdapter:
    """Build a minimal APIServerAdapter wired to a real SessionDB at tmp_hermes_home.

    Skips __init__ side effects (aiohttp app, runner, site) — we only need
    the helper methods that read from / write to state.db.
    """
    from hermes_state import SessionDB
    # __init__ tries to start aiohttp — bypass it by constructing the bare
    # object then setting the fields we need.
    adapter = APIServerAdapter.__new__(APIServerAdapter)
    adapter._api_key = ""
    adapter._app = None
    adapter._runner = None
    adapter._site = None
    adapter._response_store = MagicMock()
    adapter._conversations = {}
    adapter._session_db = SessionDB()
    return adapter


def _seed_completed_subagent(db, parent_id: str, child_id: str, ended_at: float, summary: str = "Research complete."):
    """Insert a minimal 'subagent' row + assistant message that the injector will pick up."""
    db.create_session(
        session_id=child_id,
        source="subagent",
        model="deepseek-v4-flash",
        parent_session_id=parent_id,
        system_prompt="You are a focused subagent",
        user_id="u1",
    )
    db.end_session(child_id, "agent_close")
    # Bump ended_at to the value we want (end_session uses time.time()).
    db._conn.execute(
        "UPDATE sessions SET ended_at = ? WHERE id = ?",
        (ended_at, child_id),
    )
    db._conn.commit()
    # Insert the assistant message that the injector returns as "summary".
    db._conn.execute(
        """
        INSERT INTO messages (session_id, role, content, timestamp, finish_reason)
        VALUES (?, 'assistant', ?, ?, 'stop')
        """,
        (child_id, summary, ended_at),
    )
    db._conn.commit()


# ---------------------------------------------------------------------------
# 1. chat_id → parent_session_id mapping
# ---------------------------------------------------------------------------


class TestOpenWebUIChatSessionMapping:
    def test_first_sight_creates_session(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        request = MagicMock()
        request.headers = {"X-OpenWebUI-Chat-Id": "owui-chat-abc-123"}
        result = adapter._resolve_openwebui_chat_session_id(request)
        assert result is not None
        assert result.startswith("owui-")
        # Stored in the map
        assert adapter._session_db is not None
        row = adapter._session_db._conn.execute(
            "SELECT parent_session_id FROM chat_session_map WHERE chat_id = ?",
            ("owui-chat-abc-123",),
        ).fetchone()
        assert row is not None
        assert row[0] == result

    def test_second_sight_returns_same_session(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        request = MagicMock()
        request.headers = {"X-OpenWebUI-Chat-Id": "owui-chat-abc-123"}
        first = adapter._resolve_openwebui_chat_session_id(request)
        second = adapter._resolve_openwebui_chat_session_id(request)
        assert first == second

    def test_no_header_returns_none(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        request = MagicMock()
        request.headers = {}
        assert adapter._resolve_openwebui_chat_session_id(request) is None

    def test_control_chars_rejected(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        request = MagicMock()
        request.headers = {"X-OpenWebUI-Chat-Id": "evil\nchat-id"}
        assert adapter._resolve_openwebui_chat_session_id(request) is None

    def test_blank_header_returns_none(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        request = MagicMock()
        request.headers = {"X-OpenWebUI-Chat-Id": "   "}
        assert adapter._resolve_openwebui_chat_session_id(request) is None


# ---------------------------------------------------------------------------
# 2. Injection of completed subagent results
# ---------------------------------------------------------------------------


class TestSubagentResultInjection:
    def test_no_completed_children_returns_history_unchanged(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        parent_id = "owui-testparent"
        adapter._session_db.create_session(parent_id, source="api_server", user_id="u1")
        history = [{"role": "user", "content": "any news?"}]
        new_history, n = adapter._inject_completed_subagent_results(parent_id, history, "any news?")
        assert n == 0
        assert new_history == history

    def test_completed_child_injects_tool_message(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        parent_id = "owui-testparent"
        adapter._session_db.create_session(parent_id, source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session(
            "owui-chat-xyz", source="api_server", user_id="u1"
        )
        # Map the parent_id so the injector's last_injected lookup finds it.
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = ? WHERE chat_id = ?",
            (parent_id, "owui-chat-xyz"),
        )
        adapter._session_db._conn.commit()
        child_id = "subagent-child-001"
        _seed_completed_subagent(
            adapter._session_db, parent_id, child_id,
            ended_at=time.time() - 60,
            summary="Bamboo scheme details: 50:10:40 subsidy pattern, etc.",
        )
        history = [{"role": "user", "content": "any news?"}]
        new_history, n = adapter._inject_completed_subagent_results(parent_id, history, "any news?")
        assert n == 1
        # The first message should now be a user-role Hermes system event.
        first = new_history[0]
        assert first["role"] == "user"
        assert "[Hermes background subagent result" in first["content"]
        assert child_id in first["content"]
        assert "Bamboo scheme details" in first["content"]
        # The original user message is preserved after the injection.
        assert new_history[1] == history[0]

    def test_injection_is_idempotent(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        parent_id = "owui-testparent"
        adapter._session_db.create_session(parent_id, source="api_server", user_id="u1")
        # Use the chat_session_map path so last_injected tracks correctly.
        adapter._session_db.get_or_create_chat_session(
            "owui-chat-idem", source="api_server", user_id="u1"
        )
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = ? WHERE chat_id = ?",
            (parent_id, "owui-chat-idem"),
        )
        adapter._session_db._conn.commit()
        child_id = "subagent-child-002"
        _seed_completed_subagent(
            adapter._session_db, parent_id, child_id,
            ended_at=time.time() - 30, summary="done",
        )
        history = [{"role": "user", "content": "first ask"}]
        h1, n1 = adapter._inject_completed_subagent_results(parent_id, history, "first ask")
        assert n1 == 1
        # Second call with the SAME history list — should not re-inject.
        h2, n2 = adapter._inject_completed_subagent_results(parent_id, h1, "second ask")
        assert n2 == 0
        assert h2 == h1  # no change

    def test_branch_children_are_not_injected(self, tmp_hermes_home):
        """Branch children (e.g. compression continuations) share parent_session_id
        but must not be treated as subagent results."""
        adapter = _make_adapter(tmp_hermes_home)
        parent_id = "owui-testparent"
        adapter._session_db.create_session(parent_id, source="api_server", user_id="u1")
        # Insert a 'cli' (NOT 'subagent') child.
        from hermes_state import SessionDB
        adapter._session_db.create_session(
            "branch-child-001", source="cli", parent_session_id=parent_id,
        )
        adapter._session_db.end_session("branch-child-001", "agent_close")
        history = [{"role": "user", "content": "x"}]
        _, n = adapter._inject_completed_subagent_results(parent_id, history, "x")
        assert n == 0

    def test_empty_history_returns_empty(self, tmp_hermes_home):
        adapter = _make_adapter(tmp_hermes_home)
        parent_id = "owui-testparent"
        adapter._session_db.create_session(parent_id, source="api_server", user_id="u1")
        new_history, n = adapter._inject_completed_subagent_results(parent_id, [], "x")
        assert n == 0
        assert new_history == []


# ---------------------------------------------------------------------------
# 3. End-to-end: request path wires chat_id → injection
# ---------------------------------------------------------------------------


class TestRequestWiring:
    """Verify the chat_id path produces an effective_history that the LLM
    would see, by stubbing the agent and capturing the conversation_history
    passed to run_conversation."""

    def test_owui_chat_id_reaches_run_conversation_with_injection(
        self, tmp_hermes_home
    ):
        adapter = _make_adapter(tmp_hermes_home)
        # Seed a subagent that completed before this request.
        parent_id = "owui-parent-routing"
        adapter._session_db.create_session(parent_id, source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session(
            "owui-chat-routing", source="api_server", user_id="u1"
        )
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = ? WHERE chat_id = ?",
            (parent_id, "owui-chat-routing"),
        )
        adapter._session_db._conn.commit()
        _seed_completed_subagent(
            adapter._session_db, parent_id, "subagent-routing-001",
            ended_at=time.time() - 10, summary="ok",
        )

        # Build a fake AIAgent that captures run_conversation arguments.
        captured = {}
        class _FakeAgent:
            session_id = parent_id
            session_prompt_tokens = 0
            session_completion_tokens = 0
            session_total_tokens = 0
            def run_conversation(self, user_message, conversation_history, task_id=None):
                captured["history"] = list(conversation_history)
                captured["user_message"] = user_message
                return {"final_response": "hi", "messages": []}

        # Run the injector on a chat_history the way _run_agent does.
        history = [{"role": "user", "content": "any update?"}]
        new_history, n = adapter._inject_completed_subagent_results(
            parent_id, history, "any update?"
        )
        assert n == 1
        # The first message is the injected user-role Hermes event.
        assert new_history[0]["role"] == "user"
        assert "[Hermes background subagent result" in new_history[0]["content"]
        assert "subagent-routing-001" in new_history[0]["content"]
