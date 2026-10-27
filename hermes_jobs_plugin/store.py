"""Job-spine persistence, layered additively on the shared kanban board.

Why direct SQL instead of ``kanban_db.create_task`` / ``claim_task``:
those helpers carry side effects we must not inherit (they open
``task_runs`` rows, set ``worker_pid``, and apply the parent/claim and
runtime-cap semantics designed for *subprocess* workers). Job rows must
satisfy five isolation rules so the gateway's embedded kanban dispatcher
never touches them -- see README. So we own the writes, and borrow only
kanban's connection + transaction discipline (WAL + BEGIN IMMEDIATE + CAS).

Every mutation is scoped ``WHERE created_by = 'hermes_jobs'`` so a bug in
here can never move an ordinary kanban card.
"""

from __future__ import annotations

import json
import os
import secrets
import socket
import time
from typing import Any, Dict, List, Optional

from hermes_cli import kanban_db as kb

MARKER = "hermes_jobs"
CLAIM_TTL_SECONDS = 15 * 60

# Job lanes, mapped onto kanban's enforced VALID_STATUSES.
ST_QUEUED = "ready"            # waiting for the runner to claim
ST_RUNNING = "running"         # a Hermes run is in flight
ST_WAIT_QUESTION = "blocked"   # agent asked the human something
ST_WAIT_FAILURE = "review"     # run broke; human picks retry / continue / drop
ST_DONE = "done"
ST_DROPPED = "archived"        # human dropped it; terminal, never revived

PENDING_CLARIFICATION = "clarification"
PENDING_FAILURE = "failure"

# Additive columns: (column_name, full DDL)
_TASK_COLUMNS = [
    ("api_run_id", "api_run_id TEXT"),
    ("resume_rounds", "resume_rounds INTEGER NOT NULL DEFAULT 0"),
    ("pending_kind", "pending_kind TEXT"),
    ("question", "question TEXT"),
    ("question_context", "question_context TEXT"),
    ("suggested_options", "suggested_options TEXT"),
    ("answer", "answer TEXT"),
    ("dropped_at", "dropped_at INTEGER"),
    ("dropped_by", "dropped_by TEXT"),
    ("drop_reason", "drop_reason TEXT"),
    ("origin_platform", "origin_platform TEXT"),
    ("origin_chat_id", "origin_chat_id TEXT"),
    ("origin_thread_id", "origin_thread_id TEXT"),
    ("origin_message_id", "origin_message_id TEXT"),
    ("turn_budget", "turn_budget INTEGER"),
    ("wall_clock_minutes", "wall_clock_minutes INTEGER"),
    ("delivered_at", "delivered_at INTEGER"),
    ("delivery_error", "delivery_error TEXT"),
    # Cursor into task_events: the highest event id already pushed to
    # the origin surface. Mirrors kanban_notify_subs.last_event_id, which
    # already solves exactly this "notify once, not every drain tick"
    # problem for kanban cards -- same pattern, scoped to our own rows.
    ("last_delivered_event_id", "last_delivered_event_id INTEGER NOT NULL DEFAULT 0"),
]
_ATTACHMENT_COLUMNS = [
    ("role", "role TEXT"),  # 'input' | 'produced'
]


# ---------------------------------------------------------------------------
# connection + schema
# ---------------------------------------------------------------------------

def connect():
    """Open the board DB (WAL, auto-init). Caller closes."""
    return kb.connect()


def _existing_columns(conn, table: str) -> set:
    return {r[1] for r in conn.execute("PRAGMA table_info(%s)" % table)}


def ensure_schema(conn=None) -> Dict[str, List[str]]:
    """Add the job columns if missing. Idempotent; safe to run on every boot."""
    own = conn is None
    conn = conn or connect()
    added: Dict[str, List[str]] = {"tasks": [], "task_attachments": []}
    try:
        with kb.write_txn(conn):
            for table, cols in (
                ("tasks", _TASK_COLUMNS),
                ("task_attachments", _ATTACHMENT_COLUMNS),
            ):
                have = _existing_columns(conn, table)
                for name, ddl in cols:
                    if name in have:
                        continue
                    conn.execute("ALTER TABLE %s ADD COLUMN %s" % (table, ddl))
                    added[table].append(name)
    finally:
        if own:
            conn.close()
    return added


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def new_job_id() -> str:
    return "job_" + secrets.token_hex(4)


def _claimer_id() -> str:
    return "%s:%d" % (socket.gethostname(), os.getpid())


def log_event(conn, job_id: str, kind: str, payload: Optional[dict] = None) -> None:
    conn.execute(
        "INSERT INTO task_events (task_id, run_id, kind, payload, created_at) "
        "VALUES (?, NULL, ?, ?, ?)",
        (job_id, kind, json.dumps(payload or {}), int(time.time())),
    )


def _row_to_dict(row) -> Optional[Dict[str, Any]]:
    return dict(row) if row is not None else None


# ---------------------------------------------------------------------------
# lifecycle
# ---------------------------------------------------------------------------

def create_job(
    *,
    instruction: str,
    title: Optional[str] = None,
    tenant: Optional[str] = None,
    origin_platform: str = "cli",
    origin_chat_id: str = "",
    origin_thread_id: str = "",
    origin_message_id: str = "",
    turn_budget: int = 40,
    wall_clock_minutes: int = 30,
    idempotency_key: Optional[str] = None,
    conn=None,
) -> str:
    """Insert a queued job row. ``session_id`` == job id: readable and bindable."""
    if not instruction or not instruction.strip():
        raise ValueError("instruction is required")
    own = conn is None
    conn = conn or connect()
    try:
        job_id = new_job_id()
        now = int(time.time())
        auto_title = (title or instruction.strip().splitlines()[0])[:120]
        with kb.write_txn(conn):
            if idempotency_key:
                dup = conn.execute(
                    "SELECT id FROM tasks WHERE idempotency_key = ? "
                    "AND status != 'archived' LIMIT 1",
                    (idempotency_key,),
                ).fetchone()
                if dup:
                    return dup[0]
            conn.execute(
                "INSERT INTO tasks ("
                "  id, title, body, assignee, status, priority, created_by,"
                "  created_at, workspace_kind, tenant, idempotency_key,"
                "  worker_pid, max_runtime_seconds, session_id,"
                "  api_run_id, resume_rounds, origin_platform, origin_chat_id,"
                "  origin_thread_id, origin_message_id, turn_budget,"
                "  wall_clock_minutes"
                ") VALUES (?, ?, ?, NULL, ?, 0, ?, ?, 'scratch', ?, ?,"
                "          NULL, NULL, ?, NULL, 0, ?, ?, ?, ?, ?, ?)",
                (
                    job_id, auto_title, instruction.strip(), ST_QUEUED, MARKER,
                    now, tenant, idempotency_key, job_id,
                    origin_platform, origin_chat_id, origin_thread_id,
                    origin_message_id, turn_budget, wall_clock_minutes,
                ),
            )
            log_event(conn, job_id, "queued", {
                "origin": origin_platform, "tenant": tenant,
            })
        return job_id
    finally:
        if own:
            conn.close()


def claim_next(*, claimer: Optional[str] = None, conn=None) -> Optional[Dict[str, Any]]:
    """Atomically take the oldest queued job. Returns the row, or None."""
    own = conn is None
    conn = conn or connect()
    lock = claimer or _claimer_id()
    try:
        now = int(time.time())
        claimed = None
        with kb.write_txn(conn):
            row = conn.execute(
                "SELECT id FROM tasks WHERE created_by = ? AND status = ? "
                "AND claim_lock IS NULL ORDER BY priority DESC, created_at ASC "
                "LIMIT 1",
                (MARKER, ST_QUEUED),
            ).fetchone()
            if row is None:
                return None
            job_id = row[0]
            cur = conn.execute(
                "UPDATE tasks SET status = ?, claim_lock = ?, claim_expires = ?,"
                "  last_heartbeat_at = ?, started_at = COALESCE(started_at, ?),"
                "  pending_kind = NULL"
                " WHERE id = ? AND created_by = ? AND status = ?"
                "   AND claim_lock IS NULL",
                (ST_RUNNING, lock, now + CLAIM_TTL_SECONDS, now, now,
                 job_id, MARKER, ST_QUEUED),
            )
            if cur.rowcount != 1:
                return None  # lost the race
            log_event(conn, job_id, "claimed", {"claimer": lock})
            claimed = conn.execute(
                "SELECT * FROM tasks WHERE id = ?", (job_id,)
            ).fetchone()
        return _row_to_dict(claimed)
    finally:
        if own:
            conn.close()


def heartbeat(job_id: str, *, conn=None) -> bool:
    """Push ``claim_expires`` forward so kanban's reclaimers leave us alone."""
    own = conn is None
    conn = conn or connect()
    try:
        now = int(time.time())
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET claim_expires = ?, last_heartbeat_at = ? "
                "WHERE id = ? AND created_by = ? AND status = ?",
                (now + CLAIM_TTL_SECONDS, now, job_id, MARKER, ST_RUNNING),
            )
        return cur.rowcount == 1
    finally:
        if own:
            conn.close()


def set_api_run_id(job_id: str, api_run_id: str, *, conn=None) -> None:
    own = conn is None
    conn = conn or connect()
    try:
        with kb.write_txn(conn):
            conn.execute(
                "UPDATE tasks SET api_run_id = ? WHERE id = ? AND created_by = ?",
                (api_run_id, job_id, MARKER),
            )
            log_event(conn, job_id, "run_started", {"api_run_id": api_run_id})
    finally:
        if own:
            conn.close()


def park_question(
    job_id: str, *, question: str, context: str = "",
    options: Optional[List[str]] = None, conn=None,
) -> bool:
    """Agent asked the human something. Run ends, slot frees, no auto-retry."""
    own = conn is None
    conn = conn or connect()
    try:
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET status = ?, pending_kind = ?, question = ?,"
                "  question_context = ?, suggested_options = ?, answer = NULL,"
                "  claim_lock = NULL, claim_expires = NULL"
                " WHERE id = ? AND created_by = ? AND status = ?",
                (ST_WAIT_QUESTION, PENDING_CLARIFICATION, question, context,
                 json.dumps(options or []), job_id, MARKER, ST_RUNNING),
            )
            ok = cur.rowcount == 1
            if ok:
                log_event(conn, job_id, "needs_input", {
                    "kind": PENDING_CLARIFICATION, "question": question,
                })
        return ok
    finally:
        if own:
            conn.close()


def park_failure(job_id: str, *, error: str, conn=None) -> bool:
    """Run broke or hit budget. Never auto-retried -- a human decides."""
    own = conn is None
    conn = conn or connect()
    try:
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET status = ?, pending_kind = ?,"
                "  last_failure_error = ?,"
                "  consecutive_failures = consecutive_failures + 1,"
                "  claim_lock = NULL, claim_expires = NULL"
                " WHERE id = ? AND created_by = ? AND status = ?",
                (ST_WAIT_FAILURE, PENDING_FAILURE, (error or "")[:2000],
                 job_id, MARKER, ST_RUNNING),
            )
            ok = cur.rowcount == 1
            if ok:
                log_event(conn, job_id, "failed", {"error": (error or "")[:500]})
        return ok
    finally:
        if own:
            conn.close()


def complete_job(
    job_id: str, *, summary: str, artifacts: Optional[List[str]] = None, conn=None,
) -> bool:
    own = conn is None
    conn = conn or connect()
    try:
        now = int(time.time())
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET status = ?, result = ?, completed_at = ?,"
                "  pending_kind = NULL, question = NULL, claim_lock = NULL,"
                "  claim_expires = NULL, consecutive_failures = 0"
                " WHERE id = ? AND created_by = ? AND status IN (?, ?)",
                (ST_DONE, summary, now, job_id, MARKER, ST_RUNNING,
                 ST_WAIT_QUESTION),
            )
            ok = cur.rowcount == 1
            if ok:
                log_event(conn, job_id, "completed", {
                    "artifacts": artifacts or [],
                })
        return ok
    finally:
        if own:
            conn.close()


def answer_job(job_id: str, answer: str, *, conn=None) -> bool:
    """Human answered a clarification -> requeue. Rounds counted, never capped."""
    own = conn is None
    conn = conn or connect()
    try:
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET status = ?, answer = ?, pending_kind = NULL,"
                "  resume_rounds = resume_rounds + 1,"
                "  claim_lock = NULL, claim_expires = NULL"
                " WHERE id = ? AND created_by = ? AND status = ?",
                (ST_QUEUED, answer, job_id, MARKER, ST_WAIT_QUESTION),
            )
            ok = cur.rowcount == 1
            if ok:
                log_event(conn, job_id, "answered", {"answer": answer[:500]})
        return ok
    finally:
        if own:
            conn.close()


def continue_job(job_id: str, *, extra_input: str = "", conn=None) -> bool:
    """Human retries a failed job, optionally with extra input. No round count."""
    own = conn is None
    conn = conn or connect()
    try:
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET status = ?, pending_kind = NULL,"
                "  answer = CASE WHEN ? != '' THEN ? ELSE answer END,"
                "  claim_lock = NULL, claim_expires = NULL"
                " WHERE id = ? AND created_by = ? AND status = ?",
                (ST_QUEUED, extra_input, extra_input, job_id, MARKER,
                 ST_WAIT_FAILURE),
            )
            ok = cur.rowcount == 1
            if ok:
                log_event(conn, job_id, "retry_requested", {
                    "extra_input": extra_input[:500],
                })
        return ok
    finally:
        if own:
            conn.close()


def drop_job(job_id: str, *, by: str = "ndr", reason: str = "", conn=None) -> bool:
    """Terminal. A dropped job is never claimed, retried or revived."""
    own = conn is None
    conn = conn or connect()
    try:
        now = int(time.time())
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET status = ?, dropped_at = ?, dropped_by = ?,"
                "  drop_reason = ?, pending_kind = NULL, claim_lock = NULL,"
                "  claim_expires = NULL"
                " WHERE id = ? AND created_by = ? AND status != ?",
                (ST_DROPPED, now, by, reason, job_id, MARKER, ST_DROPPED),
            )
            ok = cur.rowcount == 1
            if ok:
                log_event(conn, job_id, "dropped", {"by": by, "reason": reason})
        return ok
    finally:
        if own:
            conn.close()


# ---------------------------------------------------------------------------
# reads
# ---------------------------------------------------------------------------

def get_job(job_id: str, *, conn=None) -> Optional[Dict[str, Any]]:
    own = conn is None
    conn = conn or connect()
    try:
        row = conn.execute(
            "SELECT * FROM tasks WHERE id = ? AND created_by = ?",
            (job_id, MARKER),
        ).fetchone()
        return _row_to_dict(row)
    finally:
        if own:
            conn.close()


def list_jobs(
    *, status: Optional[str] = None, tenant: Optional[str] = None,
    limit: int = 100, conn=None,
) -> List[Dict[str, Any]]:
    own = conn is None
    conn = conn or connect()
    try:
        sql = "SELECT * FROM tasks WHERE created_by = ?"
        args: list = [MARKER]
        if status:
            sql += " AND status = ?"
            args.append(status)
        if tenant:
            sql += " AND tenant = ?"
            args.append(tenant)
        sql += " ORDER BY created_at DESC LIMIT ?"
        args.append(limit)
        return [dict(r) for r in conn.execute(sql, args)]
    finally:
        if own:
            conn.close()


def list_events(job_id: str, *, limit: int = 50, conn=None) -> List[Dict[str, Any]]:
    own = conn is None
    conn = conn or connect()
    try:
        return [dict(r) for r in conn.execute(
            "SELECT id, kind, payload, created_at FROM task_events "
            "WHERE task_id = ? ORDER BY id DESC LIMIT ?",
            (job_id, limit),
        )]
    finally:
        if own:
            conn.close()


def requeue_orphan(job_id: str, *, api_run_id: Optional[str] = None, conn=None) -> bool:
    """Put a ``running`` row whose run vanished back on the queue, once.

    A gateway restart kills in-flight runs; the row is left claiming to be
    running. That is not evidence of failure, so it returns to the queue
    rather than the failed lane. If the work breaks again, the normal
    failure path parks it for a human.
    """
    own = conn is None
    conn = conn or connect()
    try:
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET status = ?, claim_lock = NULL,"
                "  claim_expires = NULL"
                " WHERE id = ? AND created_by = ? AND status = ?",
                (ST_QUEUED, job_id, MARKER, ST_RUNNING),
            )
            ok = cur.rowcount == 1
            if ok:
                log_event(conn, job_id, "requeued_orphan",
                          {"api_run_id": api_run_id})
        return ok
    finally:
        if own:
            conn.close()


def set_last_delivered(job_id: str, event_id: int, *, conn=None) -> bool:
    """Advance the delivery cursor past ``event_id``.

    Called once per delivery ATTEMPT (success or failure) so a dead
    adapter or a send exception cannot turn into a resend-forever loop --
    matches D5's "notifies the origin once" at-most-once semantics, not
    guaranteed delivery. Monotonic: never moves the cursor backwards.
    """
    own = conn is None
    conn = conn or connect()
    try:
        with kb.write_txn(conn):
            cur = conn.execute(
                "UPDATE tasks SET last_delivered_event_id = ? "
                "WHERE id = ? AND created_by = ? AND last_delivered_event_id < ?",
                (event_id, job_id, MARKER, event_id),
            )
        return cur.rowcount == 1
    finally:
        if own:
            conn.close()
