"""The two job-mode tools: ``job_clarify`` and ``job_complete``.

Binding: a job's Hermes ``session_id`` *is* its job id, and the gateway
exposes the running session id through a ``ContextVar`` (task-local, not
process env -- see gateway/session_context.py). So each concurrent job
run resolves its own job with zero cross-talk, and no task id has to be
threaded through the model. An explicit ``job_id`` argument is accepted
as a fallback for odd call paths.

These tools are registered globally but gated by ``check_fn``: they only
appear in runs whose session id looks like a job (``job_<hex>``), so
interactive Telegram / CLI / web sessions never see them. ``job_clarify``
is deliberately distinct from the built-in blocking ``clarify``: it parks
the job, ends the run cleanly and frees the slot instead of holding a
thread for 600 seconds.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, List, Optional

from . import store

JOB_SESSION_PREFIX = "job_"


# ---------------------------------------------------------------------------
# binding
# ---------------------------------------------------------------------------

def _current_session_id() -> str:
    """Resolve the job id from the task-local session context.

    HERMES_SESSION_ID alone is NOT enough on the api_server path: that
    handler calls ``set_session_vars(platform=..., session_key=...,
    user_id=...)``, and that helper sets EVERY variable -- so session_id is
    explicitly set to "", which also suppresses the os.environ fallback.
    HERMES_SESSION_KEY, however, is populated with
    ``gateway_session_key or session_id or run_id``, which for a job run is
    the job id. So we check both and take whichever looks like a job.
    """
    candidates = []
    try:
        from gateway.session_context import get_session_env

        candidates.append(get_session_env("HERMES_SESSION_ID", "") or "")
        candidates.append(get_session_env("HERMES_SESSION_KEY", "") or "")
    except Exception:
        pass
    candidates.append(os.environ.get("HERMES_SESSION_ID", "") or "")
    for value in candidates:
        if value.startswith(JOB_SESSION_PREFIX):
            return value
    return next((c for c in candidates if c), "")


def _resolve_job_id(args: Dict[str, Any]) -> Optional[str]:
    explicit = (args.get("job_id") or "").strip()
    if explicit:
        return explicit
    sid = _current_session_id()
    return sid if sid.startswith(JOB_SESSION_PREFIX) else None


def in_job_mode() -> bool:
    """True when the current task context belongs to a job run.

    NOT usable as a registry ``check_fn``: tools/registry.py TTL-caches
    check_fn results for 30s keyed only by the callable, so one interactive
    session's answer would be served to a concurrent job run and vice versa
    (and worse, a job run's True would briefly expose these tools to
    Telegram). Availability is therefore gated per-request in
    :func:`strip_job_tools_middleware` instead.
    """
    return _current_session_id().startswith(JOB_SESSION_PREFIX)


JOB_TOOL_NAMES = frozenset({"job_clarify", "job_complete"})


def _tool_name(entry) -> str:
    if not isinstance(entry, dict):
        return ""
    direct = entry.get("name")
    if isinstance(direct, str) and direct:
        return direct
    fn = entry.get("function")
    if isinstance(fn, dict):
        nested = fn.get("name")
        if isinstance(nested, str):
            return nested
    return ""


def _log_job_payload(session_id, request) -> None:
    """Record what actually reaches the provider for a job run.

    Cheap observability for the one question that matters on resume: did
    the restored transcript survive the agent's sanitisers all the way to
    the wire? Logs a role histogram, not content.
    """
    try:
        if not session_id.startswith(JOB_SESSION_PREFIX):
            return
        msgs = request.get("messages")
        if not isinstance(msgs, list):
            return
        hist = {}
        tool_names = []
        for m in msgs:
            if not isinstance(m, dict):
                continue
            role = str(m.get("role"))
            hist[role] = hist.get(role, 0) + 1
            if role == "assistant" and m.get("tool_calls"):
                hist["assistant_with_tool_calls"] = hist.get(
                    "assistant_with_tool_calls", 0) + 1
            if role == "tool" and m.get("name"):
                tool_names.append(str(m.get("name")))
        logging.getLogger(__name__).info(
            "[hermes-jobs] wire payload for %s: %d message(s) %s tools=%s",
            session_id, len(msgs), hist, tool_names[:8],
        )
    except Exception:
        pass


def strip_job_tools_middleware(**payload):
    """Remove the job tools from any request that is not a job run.

    Runs on every LLM request in the process, so it is deliberately tiny and
    swallows everything: returning None leaves the request untouched.
    """
    try:
        request = payload.get("request")
        if not isinstance(request, dict):
            return None
        tools = request.get("tools")
        if not isinstance(tools, list) or not tools:
            return None
        session_id = payload.get("session_id") or ""
        if session_id.startswith(JOB_SESSION_PREFIX):
            _log_job_payload(session_id, request)
            return None          # a real job run: leave the tools in place
        _log_job_payload(session_id, request)
        kept = [t for t in tools if _tool_name(t) not in JOB_TOOL_NAMES]
        if len(kept) == len(tools):
            return None          # nothing of ours present: no rewrite
        request["tools"] = kept
        return {"request": request}
    except Exception:
        return None


# ---------------------------------------------------------------------------
# job_clarify
# ---------------------------------------------------------------------------

JOB_CLARIFY_SCHEMA = {
    "name": "job_clarify",
    "description": (
        "Park this job and ask the human ONE question. Use this only when you "
        "need information, a decision, or a document that ONLY a human can "
        "provide -- never to ask permission for an obvious step, and never "
        "instead of trying. Calling this ends your run cleanly: the job moves "
        "to 'needs you' on the board, the human is notified once, and your "
        "full context (including every tool result) is restored when they "
        "answer. After calling it, STOP -- do not guess, do not continue on "
        "invented assumptions. Before calling it, persist any intermediate "
        "data you have gathered to a file so the resumed run can re-read it."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": (
                    "The single question, phrased so it can be answered "
                    "without reading your whole transcript."
                ),
            },
            "context": {
                "type": "string",
                "description": (
                    "What you have already established, and why this decision "
                    "is blocking. Shown verbatim on the job board."
                ),
            },
            "suggested_options": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Concrete choices, when the answer is a pick rather than "
                    "free text. Rendered as buttons on the board."
                ),
            },
            "requested_artifact": {
                "type": "string",
                "description": (
                    "If you need a file from the human, describe it here "
                    "(e.g. 'the signed PO as PDF')."
                ),
            },
            "job_id": {
                "type": "string",
                "description": "Optional override; normally inferred.",
            },
        },
        "required": ["question"],
    },
}


def handle_job_clarify(args: Dict[str, Any], **_kw) -> str:
    job_id = _resolve_job_id(args)
    if not job_id:
        return (
            "job_clarify failed: not running as a job (no job session bound). "
            "If you are in an interactive session, use clarify instead."
        )
    question = (args.get("question") or "").strip()
    if not question:
        return "job_clarify failed: 'question' is required."
    context = (args.get("context") or "").strip()
    requested = (args.get("requested_artifact") or "").strip()
    if requested:
        context = (context + "\n\nRequested artifact: " + requested).strip()
    options = args.get("suggested_options") or []
    if isinstance(options, str):
        try:
            options = json.loads(options)
        except Exception:
            options = [options]
    options = [str(o) for o in options if str(o).strip()]

    ok = store.park_question(
        job_id, question=question, context=context, options=options,
    )
    if not ok:
        job = store.get_job(job_id)
        state = job.get("status") if job else "unknown"
        return (
            "job_clarify could not park %s (current status: %s). "
            "Do not retry; finish with job_complete and report what is "
            "missing." % (job_id, state)
        )
    return (
        "Job %s parked and waiting on the human. Your question has been "
        "recorded and the origin notified once. STOP NOW -- end your turn "
        "without further tool calls. You will be resumed with full context "
        "once they answer." % job_id
    )


# ---------------------------------------------------------------------------
# job_complete
# ---------------------------------------------------------------------------

JOB_COMPLETE_SCHEMA = {
    "name": "job_complete",
    "description": (
        "Mark this job finished and hand back the result. ``summary`` is what "
        "the human reads, so make it self-contained: what you did, what you "
        "found, what you produced, and honestly note anything that failed or "
        "was unavailable. List absolute paths of every file you produced in "
        "``artifacts`` -- they are delivered to the origin surface alongside "
        "the summary. Never fabricate a result: a partial job reported "
        "honestly is correct, a confident guess is not."
    ),
    "parameters": {
        "type": "object",
        "properties": {
            "summary": {
                "type": "string",
                "description": "Self-contained completion report for the human.",
            },
            "artifacts": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Absolute paths of files you produced.",
            },
            "deliver_to_origin": {
                "type": "boolean",
                "description": (
                    "Default true. Set false only when the human explicitly "
                    "asked for no notification."
                ),
            },
            "job_id": {
                "type": "string",
                "description": "Optional override; normally inferred.",
            },
        },
        "required": ["summary"],
    },
}


def handle_job_complete(args: Dict[str, Any], **_kw) -> str:
    job_id = _resolve_job_id(args)
    if not job_id:
        return "job_complete failed: not running as a job."
    summary = (args.get("summary") or "").strip()
    if not summary:
        return "job_complete failed: 'summary' is required."

    raw = args.get("artifacts") or []
    if isinstance(raw, str):
        raw = [raw]
    verified: List[str] = []
    rejected: List[str] = []
    for path in [str(p) for p in raw if str(p).strip()]:
        try:
            if os.path.isfile(path) and os.path.getsize(path) > 0:
                verified.append(path)
            else:
                rejected.append(path)
        except OSError:
            rejected.append(path)

    ok = store.complete_job(job_id, summary=summary, artifacts=verified)
    if not ok:
        job = store.get_job(job_id)
        state = job.get("status") if job else "unknown"
        return (
            "job_complete could not close %s (current status: %s)."
            % (job_id, state)
        )
    msg = "Job %s marked complete." % job_id
    if verified:
        msg += " Artifacts recorded: %d." % len(verified)
    if rejected:
        # Surface rather than swallow: a missing artifact usually means the
        # agent reported a file it never actually wrote.
        msg += (
            " WARNING -- these paths do not exist or are empty and were NOT "
            "recorded: %s. If the human needs them, say so in your final "
            "message." % ", ".join(rejected)
        )
    return msg


# ---------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------

TOOLS = (
    ("job_clarify", JOB_CLARIFY_SCHEMA, handle_job_clarify, "\U0001F91A"),
    ("job_complete", JOB_COMPLETE_SCHEMA, handle_job_complete, "✅"),
)


def register_tools(ctx) -> None:
    for name, schema, handler, emoji in TOOLS:
        ctx.register_tool(
            name=name,
            toolset="jobs",
            schema=schema,
            handler=handler,
            check_fn=None,
            description=schema["description"][:200],
            emoji=emoji,
        )
