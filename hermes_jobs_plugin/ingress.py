"""Telegram ``/job`` ingress + ``/jobs`` board-via-chat. Zero vendor edits.

Mechanism: registers on the ``pre_gateway_dispatch`` plugin hook, which
fires once per incoming MessageEvent -- for every platform -- AFTER the
internal-event guard but BEFORE auth/pairing, the busy guard, and session
keying (see hermes_cli/plugins.py VALID_HOOKS doc comment). A callback
returning ``{"action": "skip"}`` there makes ``_handle_message`` return
``None`` immediately; nothing else in the interactive pipeline runs for
that message. That gives us D1/D2's exact required ordering without
touching ``gateway/run.py``.

R1 is satisfied BY CONSTRUCTION, not by testing hope: for any message
that does not match ``/job`` or ``/jobs``, :func:`on_pre_gateway_dispatch`
returns ``None``. ``invoke_hook`` only collects non-``None`` results, so
when this plugin is the only hook on ``pre_gateway_dispatch``,
``_hook_results`` is simply ``[]`` for every non-/job message and
``_handle_message`` runs exactly as if this plugin did not exist.

The hook callback itself is synchronous (``invoke_hook`` never awaits a
callback) and must stay O(1) -- no DB I/O inline, mirroring the vendor's
own ``/kanban`` handler, which explicitly runs its DB work in a thread
pool "so the gateway event loop stays responsive". We go one step
further: the hook only does cheap regex matching and schedules a task;
all actual work (DB reads/writes via ``asyncio.to_thread``, replies) runs
inside that task, never on the hook's own call stack.

Runner loop: no vendor hook fires at gateway *startup* (checked -- the
only gateway-fired hooks are this one, ``on_session_finalize``, and the
per-turn ones). So the claim/run/poll loop is lazily started the first
time ANY message arrives after the gateway boots, idempotently, from
inside this same hook. Known gap: on a gateway that has just restarted
and receives no traffic at all (any platform, any content), the loop
does not start until the next message -- including the very ``/job``
that creates the first row, which self-triggers it. Documented, not
hidden; the clean fix is a dedicated ``on_gateway_ready`` vendor hook,
which would be a one-line, additive, low-risk upstream contribution.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Optional

from . import delivery, runner, store

logger = logging.getLogger(__name__)

# D1 scope for this increment: Telegram DMs only. Extend this set (not
# the matching/handling logic below) when WhatsApp/other surfaces are
# wired in later increments.
_INGRESS_PLATFORMS = {"telegram"}

_JOB_RE = re.compile(r"^/job(s)?\b(.*)$", re.IGNORECASE | re.DOTALL)

_DRAIN_IDLE_SECONDS = 5
_DRAIN_BUSY_SECONDS = 0.5

# Module-level singletons. A plugin's register() runs once per process and
# has no natural place of its own to keep state, so (as elsewhere in this
# plugin, e.g. tools.py's check_fn discussion) module globals are the
# idiom here. Exactly one Gateway exists per process, so "the last one we
# saw" is "the only one there is".
_drain_task: Optional["asyncio.Task"] = None
_gateway_ref: Any = None


# ---------------------------------------------------------------------------
# drain loop (claim -> run -> poll -> classify -> deliver)
# ---------------------------------------------------------------------------

def _ensure_drain_loop() -> None:
    global _drain_task
    if _drain_task is not None and not _drain_task.done():
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return  # not inside an event loop (e.g. a bare CLI invocation)
    _drain_task = loop.create_task(_drain_loop())
    logger.info("hermes-jobs: background runner loop started")


async def _drain_loop() -> None:
    try:
        reclaimed = await asyncio.to_thread(runner.reconcile)
        if reclaimed:
            logger.info(
                "hermes-jobs: requeued %d orphaned job(s) on startup", len(reclaimed),
            )
    except Exception:
        logger.exception("hermes-jobs: startup reconcile failed")

    while True:
        did_work = False
        try:
            result = await asyncio.to_thread(runner.run_one)
            did_work = result is not None
            if result is not None:
                logger.info("hermes-jobs: job finished: %s", result)
        except Exception:
            logger.exception("hermes-jobs: runner tick raised")

        try:
            pending = await asyncio.to_thread(delivery.collect_pending)
        except Exception:
            logger.exception("hermes-jobs: delivery collection failed")
            pending = []
        for item in pending:
            did_work = True
            await _deliver_one(item)

        await asyncio.sleep(_DRAIN_BUSY_SECONDS if did_work else _DRAIN_IDLE_SECONDS)


async def _deliver_one(item: dict) -> None:
    """Send one pending notification, then advance its cursor regardless.

    At-most-once (D5): a dead adapter or a raised exception from
    ``adapter.send`` is logged and the cursor still advances -- we would
    rather miss one notification on a transient failure than resend the
    same event forever. See delivery.py's module docstring.
    """
    try:
        from gateway.config import Platform

        plat = Platform(item["platform"])
    except Exception:
        logger.warning(
            "hermes-jobs: unknown origin platform %r for job %s; cannot deliver",
            item.get("platform"), item.get("job_id"),
        )
        await asyncio.to_thread(store.set_last_delivered, item["job_id"], item["event_id"])
        return

    adapter = _gateway_ref.adapters.get(plat) if _gateway_ref is not None else None
    if adapter is None:
        logger.warning(
            "hermes-jobs: no live adapter for %s; job %s notification dropped this tick",
            plat, item["job_id"],
        )
        await asyncio.to_thread(store.set_last_delivered, item["job_id"], item["event_id"])
        return

    metadata = {"thread_id": item["thread_id"]} if item.get("thread_id") else {}
    try:
        await adapter.send(item["chat_id"], item["text"], metadata=metadata)
    except Exception:
        logger.exception("hermes-jobs: delivery send failed for job %s", item["job_id"])
    finally:
        await asyncio.to_thread(store.set_last_delivered, item["job_id"], item["event_id"])


# ---------------------------------------------------------------------------
# the hook
# ---------------------------------------------------------------------------

def on_pre_gateway_dispatch(event=None, gateway=None, session_store=None, **_kw):
    global _gateway_ref
    if gateway is not None:
        _gateway_ref = gateway
    _ensure_drain_loop()

    # TEMPORARY diagnostic (2026-10-26) -- fires for EVERY message on EVERY
    # platform, unconditionally, before any filtering. Remove once the
    # /jobs-not-replying report is root-caused; this is too noisy to keep.
    try:
        _src = getattr(event, "source", None)
        logger.info(
            "hermes-jobs DIAG: event_present=%s platform=%r chat_type=%r text=%r",
            event is not None,
            str(getattr(getattr(_src, "platform", None), "value", getattr(_src, "platform", None))),
            getattr(_src, "chat_type", None),
            (getattr(event, "text", None) or "")[:80],
        )
    except Exception:
        logger.exception("hermes-jobs DIAG: logging itself failed")

    if event is None:
        return None
    source = getattr(event, "source", None)
    if source is None:
        return None

    platform = str(getattr(source.platform, "value", source.platform) or "")
    if platform not in _INGRESS_PLATFORMS:
        return None
    # D1 lock: DMs only. Group/channel text starting with /job is left
    # completely alone -- falls through to normal handling, unchanged.
    if getattr(source, "chat_type", "dm") != "dm":
        return None

    text = (getattr(event, "text", "") or "").strip()
    m = _JOB_RE.match(text)
    logger.info(
        "hermes-jobs: hook saw platform=%s chat_type=%s text=%r matched=%s",
        platform, getattr(source, "chat_type", "dm"), text, bool(m),
    )
    if not m:
        return None  # not ours -- R1: every other message is untouched

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return None  # should not happen inside the gateway; fail open

    is_list = bool(m.group(1))
    rest = (m.group(2) or "").strip()
    loop.create_task(_async_dispatch(event, source, is_list, rest))
    return {"action": "skip", "reason": "hermes_jobs"}


async def _async_dispatch(event, source, is_list: bool, rest: str) -> None:
    try:
        if is_list:
            await _handle_jobs_command(event, source, rest)
        else:
            await _handle_job_create(event, source, rest)
    except Exception:
        logger.exception("hermes-jobs: ingress handler failed")
        await _reply(source, "Job system hit an internal error -- check the logs.",
                    reply_to=event.message_id)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _tenant_for(source) -> str:
    return str(getattr(source, "user_id", None) or source.chat_id)


async def _reply(source, text: str, reply_to=None) -> None:
    adapter = _gateway_ref.adapters.get(source.platform) if _gateway_ref else None
    if adapter is None:
        logger.warning(
            "hermes-jobs: no adapter for platform %s (gateway_ref=%s, known adapters=%s)",
            source.platform, _gateway_ref is not None,
            list(_gateway_ref.adapters.keys()) if _gateway_ref else None,
        )
        return
    try:
        result = await adapter.send(source.chat_id, text, reply_to=reply_to)
        logger.info("hermes-jobs: reply sent to chat=%s result=%r", source.chat_id, result)
    except Exception:
        logger.exception("hermes-jobs: reply send failed to chat=%s", source.chat_id)


def _owns(job: Optional[dict], source) -> bool:
    # Per-user scoping (D6): chat commands act only on the caller's own
    # jobs. Cross-user admin visibility is a board feature, not a chat
    # command -- deferred.
    return job is not None and job.get("tenant") == _tenant_for(source)


# ---------------------------------------------------------------------------
# /job <instruction>
# ---------------------------------------------------------------------------

async def _handle_job_create(event, source, instruction: str) -> None:
    if not instruction:
        await _reply(
            source,
            "Usage: /job <instruction>\nExample: /job summarise today's calendar",
            reply_to=event.message_id,
        )
        return
    job_id = await asyncio.to_thread(
        store.create_job,
        instruction=instruction,
        tenant=_tenant_for(source),
        origin_platform="telegram",
        origin_chat_id=str(source.chat_id),
        origin_thread_id=str(source.thread_id or ""),
        origin_message_id=str(event.message_id or ""),
    )
    await _reply(
        source,
        "\U0001F9ED Job `%s` queued -- it runs independently of this chat. "
        "I'll message you here when it's done or needs you. Track it with /jobs."
        % job_id,
        reply_to=event.message_id,
    )


# ---------------------------------------------------------------------------
# /jobs [list | answer <id> <text> | continue <id> [extra] | drop <id> [reason]]
# ---------------------------------------------------------------------------

_LANE_LABEL = {
    store.ST_QUEUED: "⏳ queued",
    store.ST_RUNNING: "⚙️ working",
    store.ST_WAIT_QUESTION: "✋ needs you",
    store.ST_WAIT_FAILURE: "⚠️ needs you (failed)",
    store.ST_DONE: "✅ done",
    store.ST_DROPPED: "\U0001F5D1 dropped",
}


async def _handle_jobs_command(event, source, rest: str) -> None:
    parts = rest.split(None, 1)
    sub = parts[0].lower() if parts else ""
    arg = parts[1] if len(parts) > 1 else ""

    if sub == "answer":
        await _handle_jobs_answer(event, source, arg)
    elif sub == "drop":
        await _handle_jobs_drop(event, source, arg)
    elif sub == "continue":
        await _handle_jobs_continue(event, source, arg)
    else:
        await _handle_jobs_list(event, source)


async def _handle_jobs_list(event, source) -> None:
    rows = await asyncio.to_thread(store.list_jobs, tenant=_tenant_for(source), limit=15)
    if not rows:
        await _reply(source, "No jobs yet. Send /job <instruction> to create one.",
                    reply_to=event.message_id)
        return
    lines = ["*Your jobs* (most recent first):"]
    for r in rows:
        label = _LANE_LABEL.get(r["status"], r["status"])
        title = (r.get("title") or "")[:48]
        line = "`%s` %s -- %s" % (r["id"], label, title)
        if r["status"] == store.ST_WAIT_QUESTION and r.get("question"):
            line += "\n   ❓ %s" % r["question"][:120]
        elif r["status"] == store.ST_WAIT_FAILURE and r.get("last_failure_error"):
            line += "\n   ⚠️ %s" % r["last_failure_error"][:120]
        lines.append(line)
    lines.append(
        "\nReply: /jobs answer <id> <text>  |  /jobs continue <id> [extra]  "
        "|  /jobs drop <id> [reason]"
    )
    await _reply(source, "\n".join(lines), reply_to=event.message_id)


async def _handle_jobs_answer(event, source, arg: str) -> None:
    parts = arg.split(None, 1)
    if len(parts) < 2:
        await _reply(source, "Usage: /jobs answer <job_id> <your answer>",
                    reply_to=event.message_id)
        return
    job_id, answer = parts[0], parts[1]
    job = await asyncio.to_thread(store.get_job, job_id)
    if not _owns(job, source):
        await _reply(source, "No such job of yours: `%s`" % job_id, reply_to=event.message_id)
        return
    ok = await asyncio.to_thread(store.answer_job, job_id, answer)
    if not ok:
        await _reply(
            source,
            "Job `%s` is not waiting on a question right now (status: %s)."
            % (job_id, job.get("status")),
            reply_to=event.message_id,
        )
        return
    await _reply(source, "Got it -- job `%s` is resuming." % job_id, reply_to=event.message_id)


async def _handle_jobs_continue(event, source, arg: str) -> None:
    job_id, _, extra = arg.partition(" ")
    job = await asyncio.to_thread(store.get_job, job_id)
    if not _owns(job, source):
        await _reply(source, "No such job of yours: `%s`" % job_id, reply_to=event.message_id)
        return
    ok = await asyncio.to_thread(store.continue_job, job_id, extra_input=extra.strip())
    if not ok:
        await _reply(
            source,
            "Job `%s` is not in the failed lane right now (status: %s)."
            % (job_id, job.get("status")),
            reply_to=event.message_id,
        )
        return
    await _reply(source, "Retrying job `%s`." % job_id, reply_to=event.message_id)


# ---------------------------------------------------------------------------
# PluginContext.register_command() fallback handlers
#
# These exist ONLY so hermes_cli.commands.should_bypass_active_session()
# (patched -- see ops/patches/0002) recognizes "job"/"jobs" as REAL
# commands and lets them bypass a busy session. In the normal case
# on_pre_gateway_dispatch intercepts first (it runs earlier in
# _handle_message than plugin-command dispatch does) and these never
# actually execute. They return a short, honest message rather than
# nothing, so a future regression in the hook degrades gracefully
# instead of silently.
# ---------------------------------------------------------------------------

def register_command_job(raw_args: str) -> str:
    return (
        "Usage: /job <instruction> -- create a job. "
        "(You are seeing this fallback reply because the primary ingress "
        "hook did not intercept this message; please report that.)"
    )


def register_command_jobs(raw_args: str) -> str:
    return (
        "Usage: /jobs | /jobs answer <id> <text> | /jobs continue <id> "
        "[extra] | /jobs drop <id> [reason]. "
        "(You are seeing this fallback reply because the primary ingress "
        "hook did not intercept this message; please report that.)"
    )


async def _handle_jobs_drop(event, source, arg: str) -> None:
    job_id, _, reason = arg.partition(" ")
    job = await asyncio.to_thread(store.get_job, job_id)
    if not _owns(job, source):
        await _reply(source, "No such job of yours: `%s`" % job_id, reply_to=event.message_id)
        return
    await asyncio.to_thread(
        store.drop_job, job_id, by=_tenant_for(source), reason=reason.strip(),
    )
    await _reply(source, "Job `%s` dropped -- it will never run again." % job_id,
                reply_to=event.message_id)
