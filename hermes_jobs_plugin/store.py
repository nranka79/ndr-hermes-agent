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
    # Chained jobs (D-none, built 2026-10-27): set when a job was created
    # via the done-job "Next job" action. The child job's own instruction
    # is whatever the human typed next; create_job folds the parent's
    # instruction+result into the child's body as context (see board_server
    # api_create_job) so this column is for traceability/UI display, not
    # re-derivation -- the context text is already baked into body.
    ("parent_job_id", "parent_job_id TEXT"),
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
            # The board's list query is WHERE created_by = 'hermes_jobs'
            # ORDER BY created_at DESC, which full-scans + sorts without
            # this. Unlike an FTS trigger, an index is behaviourally
            # transparent to kanban's own code -- it costs a little write
            # amplification and changes nothing else -- so it is safe to
            # add to the shared table.
            # Covers the exact keyset ORDER BY (created_at DESC, id DESC);
            # without the trailing id SQLite falls back to a temp b-tree
            # for the tiebreaker. Superseded name is dropped so this
            # self-migrates on the next boot.
            #
            # Known limit: a lane query adds `status IN (...)`, which this
            # index filters inline while walking in date order. Ideal when
            # the lane holds most rows (done), but a near-empty lane scans
            # the whole index. Fine to tens of thousands of rows; revisit
            # with a (created_by, status, created_at DESC) index if lane
            # queries ever get slow.
            conn.execute("DROP INDEX IF EXISTS idx_hermes_jobs_created")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_hermes_jobs_page "
                "ON tasks(created_by, created_at DESC, id DESC)"
            )
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
    parent_job_id: Optional[str] = None,
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
                "  wall_clock_minutes, parent_job_id"
                ") VALUES (?, ?, ?, NULL, ?, 0, ?, ?, 'scratch', ?, ?,"
                "          NULL, NULL, ?, NULL, 0, ?, ?, ?, ?, ?, ?, ?)",
                (
                    job_id, auto_title, instruction.strip(), ST_QUEUED, MARKER,
                    now, tenant, idempotency_key, job_id,
                    origin_platform, origin_chat_id, origin_thread_id,
                    origin_message_id, turn_budget, wall_clock_minutes,
                    parent_job_id,
                ),
            )
            log_event(conn, job_id, "queued", {
                "origin": origin_platform, "tenant": tenant,
                "parent_job_id": parent_job_id,
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


# Columns the board's LIST view needs. Deliberately excludes the big text
# blobs (body/result/question/answer in full) -- those are only ever read
# through get_job()/api_get_job for ONE job at a time. The list used to
# return everything for every job, which at 59 jobs was already 278 KB per
# poll every 5s; a snippet is all a row can display anyway.
_LIST_COLUMNS = """
    id, title, status, created_at, completed_at, dropped_at, pending_kind,
    resume_rounds, parent_job_id, origin_platform, origin_chat_id, tenant,
    substr(COALESCE(question, ''), 1, 240)           AS snip_question,
    substr(COALESCE(last_failure_error, ''), 1, 240) AS snip_failure,
    substr(COALESCE(result, ''), 1, 240)             AS snip_result,
    substr(COALESCE(body, ''), 1, 240)               AS snip_body
"""

MAX_PAGE_LIMIT = 200
MAX_QUERY_LENGTH = 200

# Backslash, written as a normal (non-raw) Python escape.
LIKE_ESCAPE = "\\"


def _escape_like(term: str) -> str:
    """Neutralise LIKE wildcards in user input.

    Without this, searching for "job_abc" would have "_" match any
    character, and a lone "%" would match everything.
    """
    out = term.replace(LIKE_ESCAPE, LIKE_ESCAPE + LIKE_ESCAPE)
    return out.replace("%", LIKE_ESCAPE + "%").replace("_", LIKE_ESCAPE + "_")


# Columns a free-text search looks at. id is included so pasting a job id
# finds it directly.
_SEARCH_COLUMNS = ("title", "body", "result", "question", "last_failure_error", "id")


def _filter_sql(
    *, statuses=None, q=None, created_from=None, created_to=None,
):
    """Build the WHERE tail shared by the page query AND the counts query.

    Both must apply byte-identical filters or the lane badges would
    disagree with the list they label, so the predicate is built once
    here rather than written twice.
    """
    sql = ""
    args: list = []
    if statuses:
        sql += " AND status IN (%s)" % ",".join("?" for _ in statuses)
        args.extend(statuses)
    if q:
        needle = "%" + _escape_like(q[:MAX_QUERY_LENGTH]) + "%"
        clauses = " OR ".join(
            "%s LIKE ? ESCAPE '%s'" % (col, LIKE_ESCAPE) for col in _SEARCH_COLUMNS
        )
        sql += " AND (%s)" % clauses
        args.extend([needle] * len(_SEARCH_COLUMNS))
    if created_from is not None:
        sql += " AND created_at >= ?"
        args.append(int(created_from))
    if created_to is not None:
        sql += " AND created_at < ?"
        args.append(int(created_to))
    return sql, args


def encode_cursor(row: Dict[str, Any]) -> str:
    return "%d:%s" % (int(row.get("created_at") or 0), row["id"])


def decode_cursor(cursor: str):
    """Return (created_at, id). Raises ValueError on anything malformed.

    Deliberately strict rather than silently falling back to page 1: a
    bad cursor that quietly returns the first page again would make the
    UI's infinite scroll loop forever on the same rows.
    """
    ts, _, job_id = (cursor or "").partition(":")
    if not ts or not job_id:
        raise ValueError("malformed cursor")
    return int(ts), job_id


def list_jobs_page(
    *, statuses: Optional[List[str]] = None, q: Optional[str] = None,
    created_from: Optional[int] = None, created_to: Optional[int] = None,
    limit: int = 50, cursor: Optional[str] = None, conn=None,
):
    """One keyset-paginated page of jobs, newest first.

    Keyset (``created_at``, ``id``) rather than OFFSET: jobs are created
    continuously here, and OFFSET silently skips or repeats rows when a
    new job lands while the user is paging. ``id`` is the tiebreaker --
    ``created_at`` is epoch SECONDS, so a burst of jobs can share one.

    Returns ``(rows, next_cursor)``; ``next_cursor`` is None on the last
    page.
    """
    own = conn is None
    conn = conn or connect()
    try:
        limit = max(1, min(int(limit or 50), MAX_PAGE_LIMIT))
        sql = "SELECT %s FROM tasks WHERE created_by = ?" % _LIST_COLUMNS
        args: list = [MARKER]
        filt_sql, filt_args = _filter_sql(
            statuses=statuses, q=q,
            created_from=created_from, created_to=created_to,
        )
        sql += filt_sql
        args.extend(filt_args)
        if cursor:
            ts, job_id = decode_cursor(cursor)
            sql += " AND (created_at < ? OR (created_at = ? AND id < ?))"
            args.extend([ts, ts, job_id])
        # +1 row tells us whether another page exists without a COUNT.
        sql += " ORDER BY created_at DESC, id DESC LIMIT ?"
        args.append(limit + 1)

        rows = [dict(r) for r in conn.execute(sql, args)]
        next_cursor = None
        if len(rows) > limit:
            rows = rows[:limit]
            next_cursor = encode_cursor(rows[-1])
        return rows, next_cursor
    finally:
        if own:
            conn.close()


def count_jobs_by_status(
    *, q: Optional[str] = None, created_from: Optional[int] = None,
    created_to: Optional[int] = None, conn=None,
) -> Dict[str, int]:
    """Totals per status across ALL matching jobs, not just the loaded page.

    The lane badges have to count everything or they would just report
    how far the user has scrolled. Deliberately takes the search/date
    filters but NOT a status filter: each lane's badge has to stay
    correct while the user is looking at a different lane.
    """
    own = conn is None
    conn = conn or connect()
    try:
        filt_sql, filt_args = _filter_sql(
            q=q, created_from=created_from, created_to=created_to,
        )
        return {
            r[0]: r[1] for r in conn.execute(
                "SELECT status, COUNT(*) FROM tasks WHERE created_by = ?"
                + filt_sql + " GROUP BY status",
                [MARKER] + filt_args,
            )
        }
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


# ---------------------------------------------------------------------------
# input attachments
# ---------------------------------------------------------------------------
# Files the human uploads when creating, answering, or retrying a job. Stored
# on kanban's existing per-task attachment infra (task_attachments_dir +
# add_attachment) so this reuses tested code instead of inventing a second
# file store; the only addition is the 'role' column (added above) tagging
# these rows 'input' so they can be told apart from any future produced-file
# rows (there are none yet -- job_complete's artifacts live in the event log
# and are resolved by the board server directly from the filesystem; see
# board_server._completed_artifacts).

def _safe_attachment_filename(name: str) -> str:
    """Strip any path component and keep this a bare filename."""
    name = os.path.basename((name or "").strip().replace("\\", "/"))
    return name or "upload"


def record_input_attachment(
    job_id: str, *, filename: str, data: bytes,
    content_type: Optional[str] = None, uploaded_by: Optional[str] = None,
    conn=None,
) -> int:
    """Write an uploaded file to disk and record it against job_id.

    Returns the new attachment id. Raises ValueError if the job does not
    exist (mirrors kb.add_attachment's own check).
    """
    own = conn is None
    conn = conn or connect()
    try:
        safe_name = _safe_attachment_filename(filename)
        dest_dir = kb.task_attachments_dir(job_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / safe_name
        if dest_path.exists():
            stem, suffix = os.path.splitext(safe_name)
            dest_path = dest_dir / ("%s-%s%s" % (stem, secrets.token_hex(3), suffix))
        dest_path.write_bytes(data)
        attachment_id = kb.add_attachment(
            conn, job_id,
            filename=(filename or safe_name).strip() or safe_name,
            stored_path=str(dest_path),
            content_type=content_type,
            size=len(data),
            uploaded_by=uploaded_by,
        )
        with kb.write_txn(conn):
            conn.execute(
                "UPDATE task_attachments SET role = 'input' WHERE id = ?",
                (attachment_id,),
            )
        return attachment_id
    finally:
        if own:
            conn.close()


def list_input_attachments(job_id: str, *, conn=None) -> List[Dict[str, Any]]:
    own = conn is None
    conn = conn or connect()
    try:
        return [dict(r) for r in conn.execute(
            "SELECT id, filename, stored_path, content_type, size, uploaded_by,"
            "  created_at FROM task_attachments"
            " WHERE task_id = ? AND role = 'input' ORDER BY created_at ASC, id ASC",
            (job_id,),
        )]
    finally:
        if own:
            conn.close()
