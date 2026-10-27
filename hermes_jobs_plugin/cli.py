"""Operator CLI for the pilot: create / list / show / run / answer / drop.

Run inside the Hermes container as the hermes user, e.g.

    python3 -m hermes_jobs.cli create "summarise today's calendar"
    python3 -m hermes_jobs.cli run-once
    python3 -m hermes_jobs.cli show job_1a2b3c4d
    python3 -m hermes_jobs.cli answer job_1a2b3c4d "use the 2026 ledger"
    python3 -m hermes_jobs.cli drop job_1a2b3c4d --reason "not needed"

The gateway-embedded runner comes in a later increment; for the pilot the
operator drives each step so every transition is observable.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict

from . import runner, store

_LANES = {
    store.ST_QUEUED: "queued",
    store.ST_RUNNING: "working",
    store.ST_WAIT_QUESTION: "needs you (question)",
    store.ST_WAIT_FAILURE: "needs you (failed)",
    store.ST_DONE: "done",
    store.ST_DROPPED: "dropped",
}


def _lane(row: Dict[str, Any]) -> str:
    return _LANES.get(row.get("status") or "", row.get("status") or "?")


def _fmt_ts(ts) -> str:
    if not ts:
        return "-"
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(float(ts)))


def cmd_create(args) -> int:
    job_id = store.create_job(
        instruction=args.instruction,
        tenant=args.tenant,
        origin_platform=args.origin,
        turn_budget=args.turns,
        wall_clock_minutes=args.minutes,
    )
    print(job_id)
    return 0


def cmd_list(args) -> int:
    rows = store.list_jobs(status=args.status, tenant=args.tenant, limit=args.limit)
    if not rows:
        print("(no jobs)")
        return 0
    for r in rows:
        extra = ""
        if r["status"] == store.ST_WAIT_QUESTION:
            extra = " | Q: %s" % (r.get("question") or "")[:60]
        elif r["status"] == store.ST_WAIT_FAILURE:
            extra = " | ERR: %s" % (r.get("last_failure_error") or "")[:60]
        print("%-14s %-20s rounds=%-2s fails=%-2s %s%s" % (
            r["id"], _lane(r), r.get("resume_rounds"),
            r.get("consecutive_failures"), (r.get("title") or "")[:40], extra,
        ))
    return 0


def cmd_show(args) -> int:
    row = store.get_job(args.job_id)
    if not row:
        print("no such job: %s" % args.job_id, file=sys.stderr)
        return 1
    print("job        %s" % row["id"])
    print("lane       %s" % _lane(row))
    print("tenant     %s" % row.get("tenant"))
    print("origin     %s %s" % (row.get("origin_platform"), row.get("origin_chat_id") or ""))
    print("session    %s" % row.get("session_id"))
    print("api_run    %s" % row.get("api_run_id"))
    print("rounds     %s   failures %s" % (row.get("resume_rounds"),
                                           row.get("consecutive_failures")))
    print("created    %s   completed %s" % (_fmt_ts(row.get("created_at")),
                                            _fmt_ts(row.get("completed_at"))))
    print("\ninstruction\n  %s" % (row.get("body") or "").replace("\n", "\n  "))
    if row.get("question"):
        print("\nwaiting on you\n  %s" % row["question"])
        if row.get("question_context"):
            print("  context: %s" % row["question_context"])
        opts = row.get("suggested_options")
        if opts and opts != "[]":
            print("  options: %s" % ", ".join(json.loads(opts)))
    if row.get("last_failure_error"):
        print("\nlast failure\n  %s" % row["last_failure_error"])
    if row.get("result"):
        print("\nresult\n  %s" % row["result"])
    if row.get("drop_reason") is not None and row["status"] == store.ST_DROPPED:
        print("\ndropped by %s: %s" % (row.get("dropped_by"), row.get("drop_reason")))
    print("\nevents")
    for e in reversed(store.list_events(args.job_id, limit=40)):
        print("  %s  %s" % (_fmt_ts(e["created_at"]), e["kind"]))
    return 0


def cmd_run_once(args) -> int:
    result = runner.run_one()
    if result is None:
        print("(queue empty)")
        return 0
    print(json.dumps(result, indent=2, default=str))
    return 0


def cmd_answer(args) -> int:
    if not store.answer_job(args.job_id, args.answer):
        print("could not answer %s (is it waiting on a question?)" % args.job_id,
              file=sys.stderr)
        return 1
    print("answered; job requeued")
    return 0


def cmd_continue(args) -> int:
    if not store.continue_job(args.job_id, extra_input=args.add or ""):
        print("could not continue %s (is it in the failed lane?)" % args.job_id,
              file=sys.stderr)
        return 1
    print("requeued")
    return 0


def cmd_drop(args) -> int:
    if not store.drop_job(args.job_id, by=args.by, reason=args.reason or ""):
        print("could not drop %s" % args.job_id, file=sys.stderr)
        return 1
    print("dropped; this job will never run again")
    return 0


def cmd_reconcile(args) -> int:
    ids = runner.reconcile()
    print("requeued: %s" % (", ".join(ids) if ids else "(none)"))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="hermes_jobs.cli")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create")
    c.add_argument("instruction")
    c.add_argument("--tenant", default="ndr")
    c.add_argument("--origin", default="cli")
    c.add_argument("--turns", type=int, default=40)
    c.add_argument("--minutes", type=int, default=30)
    c.set_defaults(fn=cmd_create)

    c = sub.add_parser("list")
    c.add_argument("--status")
    c.add_argument("--tenant")
    c.add_argument("--limit", type=int, default=50)
    c.set_defaults(fn=cmd_list)

    c = sub.add_parser("show")
    c.add_argument("job_id")
    c.set_defaults(fn=cmd_show)

    c = sub.add_parser("run-once")
    c.set_defaults(fn=cmd_run_once)

    c = sub.add_parser("answer")
    c.add_argument("job_id")
    c.add_argument("answer")
    c.set_defaults(fn=cmd_answer)

    c = sub.add_parser("continue")
    c.add_argument("job_id")
    c.add_argument("--add", help="extra input to add before retrying")
    c.set_defaults(fn=cmd_continue)

    c = sub.add_parser("drop")
    c.add_argument("job_id")
    c.add_argument("--by", default="ndr")
    c.add_argument("--reason")
    c.set_defaults(fn=cmd_drop)

    c = sub.add_parser("reconcile")
    c.set_defaults(fn=cmd_reconcile)

    args = p.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    raise SystemExit(main())
