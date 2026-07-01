"""
Tests for the Open WebUI subagent polling endpoints (Phase 2).

Covers:
- GET /v1/chats/{chat_id}/subagents
  - returns 404 for unknown chat_id
  - returns 400 for invalid chat_id (control chars, blank)
  - returns empty list when no children
  - returns children with status, summary, files_created
  - respects limit / include_full_message / include_files query params
  - auth gate (when API_SERVER_KEY set)
- GET /v1/chats/{chat_id}/subagents/{child_id}
  - returns 404 for unknown child_id
  - enforces chat_id → parent → child linkage (defense in depth)
  - returns full message history
  - returns files_created
"""

import asyncio
import time
from unittest.mock import MagicMock

import pytest
from aiohttp import web
from aiohttp.test_utils import TestClient, TestServer

from gateway.config import GatewayConfig, Platform, PlatformConfig
from gateway.platforms.api_server import APIServerAdapter


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def tmp_hermes_home(tmp_path, monkeypatch):
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    return home


def _make_adapter_with_db(tmp_hermes_home) -> APIServerAdapter:
    from hermes_state import SessionDB
    from gateway.config import PlatformConfig
    cfg = PlatformConfig(enabled=True)
    adapter = APIServerAdapter(cfg)
    adapter._api_key = "test-api-key-12345"
    # Use a fresh db_path per test (avoid the module-level DEFAULT_DB_PATH
    # which is captured at import time and shared across tests).
    db_path = tmp_hermes_home / "state.db"
    adapter._session_db = SessionDB(db_path=db_path)
    # Bypass the real connect() (which binds sockets). Build the app only.
    adapter._app = adapter._build_app_for_tests() if hasattr(adapter, "_build_app_for_tests") else None
    if adapter._app is None:
        from aiohttp import web
        from gateway.platforms.api_server import cors_middleware, body_limit_middleware, security_headers_middleware, MAX_REQUEST_BYTES
        mws = [mw for mw in (cors_middleware, body_limit_middleware, security_headers_middleware) if mw is not None]
        adapter._app = web.Application(middlewares=mws, client_max_size=MAX_REQUEST_BYTES)
        adapter._register_routes()
    return adapter


def _seed_completed_subagent(db, parent_id, child_id, ended_at, summary):
    db.create_session(
        session_id=child_id, source="subagent",
        model="deepseek-v4-flash",
        parent_session_id=parent_id,
    )
    db.end_session(child_id, "agent_close")
    db._conn.execute("UPDATE sessions SET ended_at = ? WHERE id = ?", (ended_at, child_id))
    db._conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp, finish_reason) "
        "VALUES (?, 'assistant', ?, ?, 'stop')",
        (child_id, summary, ended_at),
    )
    db._conn.commit()


# ---------------------------------------------------------------------------
# /v1/chats/{chat_id}/subagents
# ---------------------------------------------------------------------------


class TestListSubagentsEndpoint:
    @pytest.mark.asyncio
    async def test_404_for_unknown_chat_id(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/unknown-chat/subagents",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            assert resp.status == 404
            body = await resp.json()
            assert "Unknown chat_id" in body["error"]["message"]

    @pytest.mark.asyncio
    async def test_empty_list_for_known_chat_no_children(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/c1/subagents",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            assert resp.status == 200
            body = await resp.json()
            assert body["chat_id"] == "c1"
            assert body["count"] == 0
            assert body["subagents"] == []

    @pytest.mark.asyncio
    async def test_returns_completed_subagent(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        # Force the chat to point at p1 (get_or_create made a new owui- parent)
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = 'p1' WHERE chat_id = 'c1'"
        )
        adapter._session_db._conn.commit()
        _seed_completed_subagent(
            adapter._session_db, "p1", "sub-1",
            ended_at=time.time() - 30, summary="Bamboo result.",
        )
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/c1/subagents",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            assert resp.status == 200
            body = await resp.json()
            assert body["count"] == 1
            child = body["subagents"][0]
            assert child["id"] == "sub-1"
            assert child["status"] == "completed"
            assert child["summary_excerpt"] == "Bamboo result."
            assert child["files_created"] == []  # no real file scan, but key always present

    @pytest.mark.asyncio
    async def test_limit_query_param(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = 'p1' WHERE chat_id = 'c1'"
        )
        adapter._session_db._conn.commit()
        for i in range(5):
            _seed_completed_subagent(
                adapter._session_db, "p1", f"sub-{i}",
                ended_at=time.time() - 60 + i, summary=f"x{i}",
            )
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/c1/subagents?limit=2",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            body = await resp.json()
            assert body["count"] == 2

    @pytest.mark.asyncio
    async def test_include_full_message_query_param(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = 'p1' WHERE chat_id = 'c1'"
        )
        adapter._session_db._conn.commit()
        long_summary = "X" * 800
        _seed_completed_subagent(
            adapter._session_db, "p1", "sub-1",
            ended_at=time.time() - 10, summary=long_summary,
        )
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            # Default: excerpt
            r1 = await client.get(
                "/v1/chats/c1/subagents",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            b1 = await r1.json()
            assert "summary_excerpt" in b1["subagents"][0]
            assert "summary" not in b1["subagents"][0]
            assert len(b1["subagents"][0]["summary_excerpt"]) == 500
            # include_full_message=true
            r2 = await client.get(
                "/v1/chats/c1/subagents?include_full_message=true",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            b2 = await r2.json()
            assert "summary" in b2["subagents"][0]
            assert "summary_excerpt" not in b2["subagents"][0]
            assert len(b2["subagents"][0]["summary"]) == 800

    @pytest.mark.asyncio
    async def test_auth_required_when_key_set(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            # No auth header
            resp = await client.get("/v1/chats/c1/subagents")
            assert resp.status == 401
            # Wrong key
            resp = await client.get(
                "/v1/chats/c1/subagents",
                headers={"Authorization": "Bearer wrong-key"},
            )
            assert resp.status == 401

    @pytest.mark.asyncio
    async def test_400_for_blank_chat_id(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/%20/subagents",  # url-encoded space
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            assert resp.status == 400


# ---------------------------------------------------------------------------
# /v1/chats/{chat_id}/subagents/{child_id}
# ---------------------------------------------------------------------------


class TestGetSubagentEndpoint:
    @pytest.mark.asyncio
    async def test_404_for_unknown_child(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = 'p1' WHERE chat_id = 'c1'"
        )
        adapter._session_db._conn.commit()
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/c1/subagents/nonexistent",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            assert resp.status == 404

    @pytest.mark.asyncio
    async def test_enforces_chat_to_parent_linkage(self, tmp_hermes_home):
        """A child_id known to state.db but not under the chat's parent must 404."""
        adapter = _make_adapter_with_db(tmp_hermes_home)
        # Two different parent sessions, two different chats
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.create_session("p2", source="api_server", user_id="u2")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        adapter._session_db.get_or_create_chat_session("c2", source="api_server")
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = 'p1' WHERE chat_id = 'c1'"
        )
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = 'p2' WHERE chat_id = 'c2'"
        )
        adapter._session_db._conn.commit()
        # Child attached to p2
        _seed_completed_subagent(
            adapter._session_db, "p2", "sub-p2",
            ended_at=time.time() - 5, summary="x",
        )
        # Try to fetch via c1 (which is parent p1) — must 404
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/c1/subagents/sub-p2",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            assert resp.status == 404

    @pytest.mark.asyncio
    async def test_returns_full_child_with_messages(self, tmp_hermes_home):
        adapter = _make_adapter_with_db(tmp_hermes_home)
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = 'p1' WHERE chat_id = 'c1'"
        )
        adapter._session_db._conn.commit()
        ended = time.time() - 60
        _seed_completed_subagent(
            adapter._session_db, "p1", "sub-1",
            ended_at=ended, summary="Final answer.",
        )
        # Add a tool message too
        adapter._session_db._conn.execute(
            "INSERT INTO messages (session_id, role, content, tool_name, timestamp, finish_reason) "
            "VALUES (?, 'assistant', ?, 'web_search', ?, 'stop')",
            ("sub-1", '{"query": "bamboo"}', ended - 5),
        )
        adapter._session_db._conn.commit()

        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/c1/subagents/sub-1",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            assert resp.status == 200
            body = await resp.json()
            assert body["object"] == "subagent"
            assert body["chat_id"] == "c1"
            assert body["parent_session_id"] == "p1"
            assert body["subagent"]["id"] == "sub-1"
            assert body["subagent"]["status"] == "completed"
            assert len(body["messages"]) >= 2
            # Pick the final assistant message that has no tool_name
            # (the web_search one has tool_name set; the final answer doesn't).
            final_responses = [
                m for m in body["messages"]
                if m["role"] == "assistant" and not m.get("tool_name")
            ]
            assert final_responses, "expected at least one non-tool assistant message"
            assert final_responses[-1]["content"] == "Final answer."
            # Tool message is preserved
            tool_msgs = [m for m in body["messages"] if m.get("tool_name") == "web_search"]
            assert len(tool_msgs) == 1

    @pytest.mark.asyncio
    async def test_branch_child_rejected(self, tmp_hermes_home):
        """A non-subagent child (e.g. 'cli' branch child) must 404 from this endpoint."""
        adapter = _make_adapter_with_db(tmp_hermes_home)
        adapter._session_db.create_session("p1", source="api_server", user_id="u1")
        adapter._session_db.get_or_create_chat_session("c1", source="api_server")
        adapter._session_db._conn.execute(
            "UPDATE chat_session_map SET parent_session_id = 'p1' WHERE chat_id = 'c1'"
        )
        # A 'cli' child (not subagent)
        adapter._session_db.create_session(
            "branch-1", source="cli", parent_session_id="p1",
        )
        adapter._session_db._conn.commit()
        server = TestServer(adapter._app)
        async with TestClient(server) as client:
            resp = await client.get(
                "/v1/chats/c1/subagents/branch-1",
                headers={"Authorization": "Bearer test-api-key-12345"},
            )
            assert resp.status == 404
