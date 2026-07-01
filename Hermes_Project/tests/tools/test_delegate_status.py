"""
Tests for the delegate_status tool (Phase 2 of the subagent-polling fix).

Covers:
- Returns list of subagent children of the current parent
- Marks running vs completed correctly
- Includes summary excerpt for completed children
- include_full_message swaps the excerpt for the full text
- include_files=False skips the filesystem scan
- Empty result when no children exist
- Error path when no parent_agent
- Limit parameter is respected and capped
- The function is also registered in the tool registry
"""

import json
import time
from unittest.mock import MagicMock

import pytest

from tools.delegate_tool import (
    DELEGATE_STATUS_SCHEMA,
    _scan_files_created,
    check_delegate_requirements,
    delegate_status,
)


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


def _make_parent(session_id: str = "parent-test-001"):
    p = MagicMock()
    p.session_id = session_id
    return p


def _seed_subagent(db, parent_id, child_id, ended_at=None, summary=""):
    db.create_session(
        session_id=child_id,
        source="subagent",
        model="deepseek-v4-flash",
        parent_session_id=parent_id,
        system_prompt="focused subagent",
    )
    if ended_at is not None:
        db.end_session(child_id, "agent_close")
        db._conn.execute("UPDATE sessions SET ended_at = ? WHERE id = ?", (ended_at, child_id))
        db._conn.execute(
            "INSERT INTO messages (session_id, role, content, timestamp, finish_reason) "
            "VALUES (?, 'assistant', ?, ?, 'stop')",
            (child_id, summary, ended_at),
        )
    else:
        # Still running: don't end_session
        pass
    db._conn.commit()
    return child_id


# ---------------------------------------------------------------------------
# Schema sanity
# ---------------------------------------------------------------------------


class TestDelegateStatusSchema:
    def test_schema_present_and_well_formed(self):
        assert DELEGATE_STATUS_SCHEMA["name"] == "delegate_status"
        params = DELEGATE_STATUS_SCHEMA["parameters"]
        assert params["type"] == "object"
        assert "limit" in params["properties"]
        assert "include_full_message" in params["properties"]
        assert "include_files" in params["properties"]

    def test_always_available(self):
        assert check_delegate_requirements() is True


# ---------------------------------------------------------------------------
# Function-level tests
# ---------------------------------------------------------------------------


class TestDelegateStatus:
    def test_no_parent_returns_error(self):
        result = json.loads(delegate_status(parent_agent=None))
        assert "error" in result

    def test_parent_with_no_session_id_returns_error(self):
        p = MagicMock()
        p.session_id = None
        result = json.loads(delegate_status(parent_agent=p))
        assert "error" in result

    def test_empty_result_when_no_children(self, tmp_hermes_home):
        from hermes_state import SessionDB
        db = SessionDB()
        db.create_session("parent-empty", source="api_server", user_id="u1")
        result = json.loads(delegate_status(parent_agent=_make_parent("parent-empty")))
        assert result["parent_session_id"] == "parent-empty"
        assert result["count"] == 0
        assert result["subagents"] == []

    def test_running_child_marked_running(self, tmp_hermes_home):
        from hermes_state import SessionDB
        db = SessionDB()
        db.create_session("p-run", source="api_server", user_id="u1")
        _seed_subagent(db, "p-run", "child-run", ended_at=None)
        result = json.loads(delegate_status(parent_agent=_make_parent("p-run")))
        assert result["count"] == 1
        child = result["subagents"][0]
        assert child["id"] == "child-run"
        assert child["status"] == "running"
        assert child["summary_excerpt"] is None

    def test_completed_child_marked_completed_with_excerpt(
        self, tmp_hermes_home
    ):
        from hermes_state import SessionDB
        db = SessionDB()
        db.create_session("p-done", source="api_server", user_id="u1")
        _seed_subagent(
            db, "p-done", "child-done",
            ended_at=time.time() - 30,
            summary="Bamboo research: 50:10:40 subsidy pattern confirmed.",
        )
        result = json.loads(delegate_status(parent_agent=_make_parent("p-done")))
        assert result["count"] == 1
        child = result["subagents"][0]
        assert child["status"] == "completed"
        assert "Bamboo research" in child["summary_excerpt"]

    def test_completed_child_full_message(self, tmp_hermes_home):
        from hermes_state import SessionDB
        db = SessionDB()
        db.create_session("p-full", source="api_server", user_id="u1")
        long_summary = "x" * 1500
        _seed_subagent(
            db, "p-full", "child-full",
            ended_at=time.time() - 10,
            summary=long_summary,
        )
        # Default = 500-char excerpt
        r1 = json.loads(delegate_status(parent_agent=_make_parent("p-full")))
        assert len(r1["subagents"][0]["summary_excerpt"]) == 500
        # With include_full_message=True
        r2 = json.loads(
            delegate_status(parent_agent=_make_parent("p-full"), include_full_message=True)
        )
        assert "summary" in r2["subagents"][0]
        assert "summary_excerpt" not in r2["subagents"][0]
        assert len(r2["subagents"][0]["summary"]) == 1500

    def test_branch_children_excluded(self, tmp_hermes_home):
        """Branch children (e.g. compression continuations) share parent_session_id
        but must not be treated as subagent runs."""
        from hermes_state import SessionDB
        db = SessionDB()
        db.create_session("p-mixed", source="api_server", user_id="u1")
        # A 'cli' (not 'subagent') child
        db.create_session("branch-1", source="cli", parent_session_id="p-mixed")
        db.end_session("branch-1", "agent_close")
        # A real subagent
        _seed_subagent(db, "p-mixed", "sub-1", ended_at=time.time() - 10, summary="ok")
        result = json.loads(delegate_status(parent_agent=_make_parent("p-mixed")))
        assert result["count"] == 1
        assert result["subagents"][0]["id"] == "sub-1"

    def test_limit_respected_and_capped(self, tmp_hermes_home):
        from hermes_state import SessionDB
        db = SessionDB()
        db.create_session("p-many", source="api_server", user_id="u1")
        # 10 completed subagents
        now = time.time() - 100
        for i in range(10):
            _seed_subagent(db, "p-many", f"sub-{i:02d}", ended_at=now + i, summary=f"x{i}")
        # limit=3
        r = json.loads(delegate_status(parent_agent=_make_parent("p-many"), limit=3))
        assert r["count"] == 3
        # limit=999 should cap at 50
        r2 = json.loads(delegate_status(parent_agent=_make_parent("p-many"), limit=999))
        assert r2["count"] == 10  # we only have 10

    def test_include_files_false_skips_scan(self, tmp_hermes_home, monkeypatch):
        from hermes_state import SessionDB
        db = SessionDB()
        db.create_session("p-nofile", source="api_server", user_id="u1")
        _seed_subagent(db, "p-nofile", "child-1", ended_at=time.time() - 5, summary="x")
        r = json.loads(
            delegate_status(parent_agent=_make_parent("p-nofile"), include_files=False)
        )
        assert r["subagents"][0]["files_created"] == []

    def test_sorted_newest_first(self, tmp_hermes_home):
        from hermes_state import SessionDB
        db = SessionDB()
        db.create_session("p-order", source="api_server", user_id="u1")
        now = time.time() - 1000
        _seed_subagent(db, "p-order", "oldest", ended_at=now + 1, summary="o")
        _seed_subagent(db, "p-order", "middle", ended_at=now + 2, summary="m")
        _seed_subagent(db, "p-order", "newest", ended_at=now + 3, summary="n")
        r = json.loads(delegate_status(parent_agent=_make_parent("p-order")))
        ids = [c["id"] for c in r["subagents"]]
        assert ids == ["newest", "middle", "oldest"]


# ---------------------------------------------------------------------------
# _scan_files_created — filesystem scan
# ---------------------------------------------------------------------------


class TestScanFilesCreated:
    def test_safe_root_missing(self, tmp_hermes_home, monkeypatch):
        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", "/nonexistent/path/xyz")
        result = _scan_files_created("c1", 0, time.time())
        assert result == []

    def test_scans_files_in_window(self, tmp_hermes_home, monkeypatch):
        import os
        # Create a temp safe root with a file inside the window
        safe = tmp_hermes_home / "safe"
        safe.mkdir()
        target = safe / "report.md"
        target.write_text("# report")
        # mtime a few seconds ago
        now = time.time()
        os.utime(target, (now - 5, now - 5))
        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe))
        result = _scan_files_created("c1", now - 60, now)
        assert any(p.endswith("report.md") for p in result)

    def test_skips_files_outside_window(self, tmp_hermes_home, monkeypatch):
        import os
        safe = tmp_hermes_home / "safe"
        safe.mkdir()
        target = safe / "old.md"
        target.write_text("old")
        now = time.time()
        # File mtime is 1 hour ago
        os.utime(target, (now - 3700, now - 3700))
        monkeypatch.setenv("HERMES_WRITE_SAFE_ROOT", str(safe))
        # Window: last 60s
        result = _scan_files_created("c1", now - 60, now)
        assert not any(p.endswith("old.md") for p in result)
