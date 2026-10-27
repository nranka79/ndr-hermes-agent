"""The job runner: claim -> POST /v1/runs -> heartbeat + poll -> classify.

Execution model: jobs run *inside* the existing gateway via the HTTP run
endpoint. No subprocess workers -- on an 8 GB box already deep into swap,
a per-job ``hermes`` process (~500-700 MB) is not affordable. The run
endpoint creates one agent per run and keeps no agent cache, so memory is
bounded by CONCURRENCY, not by how many jobs exist. A parked job costs
zero RAM: it is rows.

Because we do not use kanban's dispatcher, we own the three things it
would have given us: heartbeating the claim, polling for completion, and
reconciling rows orphaned by a gateway restart.

Nothing here ever auto-retries and nothing ever auto-dies. A run that
breaks parks for a human decision (retry / add input / drop); a run that
asks a question parks for an answer. Only an explicit human drop is
terminal.
"""

from __future__ import annotations

import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from . import store

logger = logging.getLogger(__name__)

API_BASE = os.environ.get("HERMES_API_BASE", "http://127.0.0.1:8642")
POLL_SECONDS = 5
HEARTBEAT_SECONDS = 60
MAX_CONCURRENT_JOBS = 2          # gateway's own cap is 10, shared with chat.ahfl.in
RESTORE_BUDGET_MESSAGES = 120    # above this, resume with a digest instead
DIGEST_CHAR_BUDGET = 20_000


# ---------------------------------------------------------------------------
# preamble
# ---------------------------------------------------------------------------

JOB_PREAMBLE = """You are running as an autonomous Hermes job. NO human is watching this
session in real time. Complete the instruction below using your tools, then report.

RULES
1. Self-sufficiency first. Gather data, read files, search, compute, create
   documents, prepare deliverables. Do NOT stop to ask permission for obvious steps.
2. If -- and only if -- you need information, a decision, or a document that ONLY a
   human can provide, call job_clarify, then STOP. Before calling it, write any
   intermediate data you have gathered to a file under {tmp_dir} so the resumed run
   can re-read it instead of trusting a summary.
3. On completion call job_complete with a self-contained summary and the absolute
   path of every file you produced. Your final message is what reaches the human.
4. Never send email: Gmail is DRAFT-ONLY. Never send WhatsApp messages: DRAFT-ONLY.
   The delivery layer handles dispatch after a human reviews it.
5. Never fabricate. If a tool fails or data is unavailable, say so plainly in the
   summary. A partial job reported honestly is correct; a confident guess is not.
6. This job came from {origin}. Compose deliverables for that surface.
7. Budget: about {turn_budget} turns and {wall_clock_minutes} minutes. If you near
   it, call job_complete with partial results rather than stopping silently.
8. Write scratch files under {tmp_dir}, never into live trees.

JOB {job_id}
INSTRUCTION
{instruction}
"""

RESUME_HEADER = """This job was parked waiting for the human, and they have now replied.

YOUR EARLIER WORK IS ABOVE IN THIS CONVERSATION. Every message you sent and every
tool result you received on this job -- file writes, command output, query results --
has been restored verbatim into the context you are reading now. Scroll back and use
it. Do NOT claim you have no memory of this job, and do NOT redo work you can see
you already did; quote the earlier tool output instead. If a value you need is
genuinely absent from the transcript above, say exactly which value is missing.

Incorporate their reply, finish the job, and call job_complete. If you genuinely need
another decision, call job_clarify again -- there is no limit on rounds, but each one
costs the human an interruption.

THEIR REPLY
{answer}
"""


def _tmp_dir() -> str:
    return os.environ.get("HERMES_JOBS_TMP", "/data/hermes/tmp/jobs")


def build_instructions(job: Dict[str, Any]) -> str:
    origin = job.get("origin_platform") or "cli"
    if job.get("origin_chat_id"):
        origin = "%s chat %s" % (origin, job["origin_chat_id"])
    text = JOB_PREAMBLE.format(
        job_id=job["id"],
        instruction=job.get("body") or "",
        origin=origin,
        turn_budget=job.get("turn_budget") or 40,
        wall_clock_minutes=job.get("wall_clock_minutes") or 30,
        tmp_dir=_tmp_dir(),
    )
    if job.get("answer"):
        text += "\n" + RESUME_HEADER.format(answer=job["answer"])
    return text


# ---------------------------------------------------------------------------
# resume strategy
# ---------------------------------------------------------------------------

def _session_message_count(session_id: str) -> int:
    try:
        data = _api_get("/api/sessions/%s" % session_id)
        return int((data.get("session") or {}).get("message_count") or 0)
    except Exception:
        return 0


def build_digest(session_id: str, char_budget: int = DIGEST_CHAR_BUDGET) -> str:
    """A3 fallback: a bounded prose recap of prior work.

    Used when a transcript is too large to restore wholesale. Prose works
    (verified): a tool result folded into assistant text is read correctly,
    whereas a raw tool message replayed without its tool_call_id is dropped
    silently -- which is why we never hand raw history to the run endpoint.
    """
    try:
        data = _api_get("/api/sessions/%s/messages" % session_id)
    except Exception as exc:
        logger.warning("digest: cannot read session %s: %s", session_id, exc)
        return ""
    lines: List[str] = []
    for m in data.get("data") or []:
        role = m.get("role")
        content = m.get("content")
        if not isinstance(content, str):
            content = json.dumps(content)[:400]
        content = content.strip()
        if not content:
            continue
        if role == "user":
            lines.append("[asked] %s" % content[:400])
        elif role == "assistant":
            lines.append("[you said] %s" % content[:400])
        elif role == "tool":
            lines.append("[tool %s returned] %s"
                         % (m.get("tool_name") or "?", content[:600]))
    kept: List[str] = []
    total = 0
    for line in reversed(lines):            # keep the most recent
        if total + len(line) > char_budget:
            break
        kept.append(line)
        total += len(line)
    kept.reverse()
    if not kept:
        return ""
    return ("\n\n## Work you already completed in this job (most recent last)\n"
            + "\n".join(kept))


# ---------------------------------------------------------------------------
# HTTP
# ---------------------------------------------------------------------------

def _api_key() -> str:
    key = os.environ.get("API_SERVER_KEY", "")
    if not key:
        raise RuntimeError("API_SERVER_KEY is not set in this process")
    return key


def _api_get(path: str) -> Dict[str, Any]:
    req = urllib.request.Request(
        API_BASE + path, headers={"Authorization": "Bearer " + _api_key()},
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def _api_post(path: str, body: Dict[str, Any]) -> Dict[str, Any]:
    req = urllib.request.Request(
        API_BASE + path,
        data=json.dumps(body).encode(),
        headers={
            "Authorization": "Bearer " + _api_key(),
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise RuntimeError("POST %s -> HTTP %d: %s" % (path, exc.code, detail))


# ---------------------------------------------------------------------------
# one job
# ---------------------------------------------------------------------------

def start_run(job: Dict[str, Any]) -> str:
    """Kick off a run for an already-claimed job. Returns the api run id."""
    session_id = job.get("session_id") or job["id"]
    instructions = build_instructions(job)
    resuming = bool(job.get("answer"))

    restore = False
    if resuming:
        count = _session_message_count(session_id)
        if count and count <= RESTORE_BUDGET_MESSAGES:
            restore = True            # A1: exact transcript, tool results intact
        else:
            digest = build_digest(session_id)
            if digest:
                instructions += digest  # A3: bounded recap
            logger.info(
                "job %s: transcript too large (%d msgs) -- resuming with digest",
                job["id"], count,
            )

    payload: Dict[str, Any] = {
        "input": job.get("answer") or (job.get("body") or ""),
        "instructions": instructions,
        "session_id": session_id,
    }
    if restore:
        payload["restore_history"] = True

    resp = _api_post("/v1/runs", payload)
    run_id = resp.get("run_id") or ""
    if not run_id:
        raise RuntimeError("run endpoint returned no run_id: %r" % resp)
    store.set_api_run_id(job["id"], run_id)
    logger.info("job %s -> run %s (restore_history=%s)", job["id"], run_id, restore)
    return run_id


def _terminal(status: str) -> bool:
    return status in ("completed", "failed", "error", "cancelled", "interrupted")


def await_run(job_id: str, run_id: str, wall_clock_minutes: int) -> Tuple[str, str]:
    """Poll a run to its end, heartbeating the claim. Returns (status, text)."""
    deadline = time.time() + max(1, wall_clock_minutes) * 60
    last_beat = 0.0
    status, text = "unknown", ""
    while True:
        # A parked job ends its own run: the tool already moved the row, so
        # stop polling as soon as we are no longer the running job.
        row = store.get_job(job_id)
        if row and row["status"] != store.ST_RUNNING:
            return "left_running_lane", ""

        if time.time() - last_beat > HEARTBEAT_SECONDS:
            store.heartbeat(job_id)
            last_beat = time.time()

        try:
            info = _api_get("/v1/runs/%s" % run_id)
            status = info.get("status") or "unknown"
            text = info.get("output") or ""
        except Exception as exc:
            logger.warning("job %s: poll failed: %s", job_id, exc)

        if _terminal(status):
            return status, text

        if time.time() > deadline:
            try:
                _api_post("/v1/runs/%s/stop" % run_id, {})
            except Exception:
                pass
            return "budget_exceeded", text

        time.sleep(POLL_SECONDS)


def run_one(job: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Claim (or take a given) job, run it, classify the outcome.

    Returns a small result dict, or None when the queue was empty.
    """
    job = job or store.claim_next()
    if job is None:
        return None
    job_id = job["id"]
    try:
        run_id = start_run(job)
    except Exception as exc:
        store.park_failure(job_id, error="could not start run: %s" % exc)
        return {"job_id": job_id, "outcome": "failed", "error": str(exc)}

    status, text = await_run(
        job_id, run_id, int(job.get("wall_clock_minutes") or 30),
    )

    if status == "left_running_lane":
        # The row moved itself: job_complete -> done, job_clarify -> blocked,
        # a human drop -> archived. Classify; never assume a park.
        row = store.get_job(job_id) or {}
        state = row.get("status")
        if state == store.ST_DONE:
            return {"job_id": job_id, "outcome": "completed",
                    "summary": row.get("result")}
        if state == store.ST_DROPPED:
            return {"job_id": job_id, "outcome": "dropped",
                    "reason": row.get("drop_reason")}
        if state == store.ST_WAIT_FAILURE:
            return {"job_id": job_id, "outcome": "failed",
                    "error": row.get("last_failure_error")}
        return {"job_id": job_id, "outcome": "parked", "status": state,
                "question": row.get("question")}

    row = store.get_job(job_id)
    if row and row["status"] == store.ST_DONE:
        return {"job_id": job_id, "outcome": "completed", "summary": row["result"]}

    if status == "completed":
        # The run ended cleanly but the agent never called job_complete.
        # Kanban treats this as a protocol violation rather than success, and
        # so do we -- a silent finish is not a result. Park for a human.
        store.park_failure(
            job_id,
            error="run ended without calling job_complete or job_clarify. "
                  "Final message: " + (text or "")[:600],
        )
        return {"job_id": job_id, "outcome": "no_terminal_call", "text": text[:400]}

    if status == "budget_exceeded":
        store.park_failure(job_id, error="wall-clock budget exceeded; run stopped")
        return {"job_id": job_id, "outcome": "budget_exceeded"}

    store.park_failure(job_id, error="run ended with status=%s" % status)
    return {"job_id": job_id, "outcome": "failed", "status": status}


# ---------------------------------------------------------------------------
# reconcile
# ---------------------------------------------------------------------------

def reconcile() -> List[str]:
    """Re-queue jobs whose run vanished (gateway restart mid-flight).

    A row stuck in ``running`` whose api run is unknown or no longer live is
    not evidence of failure, so it goes back to the queue ONCE rather than
    being marked failed. If it breaks again the normal failure path parks it
    for a human.
    """
    requeued: List[str] = []
    for row in store.list_jobs(status=store.ST_RUNNING):
        run_id = row.get("api_run_id")
        alive = False
        if run_id:
            try:
                info = _api_get("/v1/runs/%s" % run_id)
                alive = not _terminal(info.get("status") or "")
            except Exception:
                alive = False
        if alive:
            continue
        if store.requeue_orphan(row["id"], api_run_id=run_id):
            requeued.append(row["id"])
    return requeued
