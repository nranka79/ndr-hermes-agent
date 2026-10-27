"""Compose and track job delivery -- section 10 of the spec.

Deliberately PURE: no asyncio, no gateway/adapter import. This module only
reads the board and decides WHAT to send and to WHOM; actually sending is
the caller's job (ingress.py), because sending needs a live adapter object
that only exists on the gateway's event loop thread. Keeping the split lets
this module be unit-tested with nothing but a kanban.db copy.

Delivered-once semantics: each job carries a ``last_delivered_event_id``
cursor (mirrors kanban's own ``kanban_notify_subs.last_event_id`` for the
same "notify once, not every tick" problem). ``collect_pending()`` never
advances that cursor itself for a deliverable job -- the caller must call
:func:`hermes_jobs.store.set_last_delivered` after it ATTEMPTS the send
(success or failure), so a dead adapter degrades to "no retry" rather than
"resend forever".
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List

from . import store

logger = logging.getLogger(__name__)

# Event kinds that are human-facing. Deliberately excludes queued/claimed/
# run_started/answered/retry_requested/requeued_orphan -- those are either
# acknowledged synchronously by the ingress reply already, or are pure
# plumbing nobody needs pinged about.
NOTIFY_KINDS = {"needs_input", "completed", "failed", "dropped"}


def _compose(job: Dict[str, Any], kind: str, payload: Dict[str, Any]) -> str:
    jid = job["id"]
    title = (job.get("title") or "")[:60]

    if kind == "completed":
        summary = payload.get("summary") or job.get("result") or "(no summary)"
        artifacts = payload.get("artifacts") or []
        msg = "✅ Job `%s` done -- %s\n\n%s" % (jid, title, summary)
        if artifacts:
            msg += "\n\nArtifacts:\n" + "\n".join("  " + str(a) for a in artifacts)
        return msg

    if kind == "needs_input":
        question = job.get("question") or ""
        msg = "✋ Job `%s` needs you -- %s\n\n%s" % (jid, title, question)
        try:
            options = json.loads(job.get("suggested_options") or "[]")
        except Exception:
            options = []
        if options:
            msg += "\nOptions: " + ", ".join(str(o) for o in options)
        msg += "\n\nReply: /jobs answer %s <your answer>" % jid
        return msg

    if kind == "failed":
        err = (job.get("last_failure_error") or "")[:400]
        return (
            "⚠️ Job `%s` hit a problem -- %s\n\n%s\n\n"
            "Reply: /jobs continue %s [optional extra input]   or   /jobs drop %s"
            % (jid, title, err, jid, jid)
        )

    if kind == "dropped":
        return "\U0001F5D1 Job `%s` dropped -- %s" % (jid, title)

    return "Job `%s`: %s" % (jid, kind)


def collect_pending(limit: int = 500) -> List[Dict[str, Any]]:
    """Return undelivered notify-worthy events, oldest first per job.

    Each item: {job_id, platform, chat_id, thread_id, text, event_id}.
    Jobs with no deliverable origin (e.g. created from the CLI, no
    origin_chat_id) have their cursor advanced here directly -- there is
    nowhere to send and nothing to retry, so there is no "attempt" for the
    caller to account for.
    """
    out: List[Dict[str, Any]] = []
    for job in store.list_jobs(limit=limit):
        cursor = job.get("last_delivered_event_id") or 0
        events = store.list_events(job["id"], limit=50)
        pending = sorted(
            (e for e in events if e["id"] > cursor and e["kind"] in NOTIFY_KINDS),
            key=lambda e: e["id"],
        )
        if not pending:
            continue

        if not job.get("origin_platform") or not job.get("origin_chat_id"):
            store.set_last_delivered(job["id"], pending[-1]["id"])
            continue

        for ev in pending:
            try:
                payload = json.loads(ev.get("payload") or "{}")
            except Exception:
                payload = {}
            out.append({
                "job_id": job["id"],
                "platform": job["origin_platform"],
                "chat_id": job["origin_chat_id"],
                "thread_id": job.get("origin_thread_id") or "",
                "text": _compose(job, ev["kind"], payload),
                "event_id": ev["id"],
            })
    return out
