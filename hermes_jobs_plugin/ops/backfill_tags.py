"""Recompute tags for every done job from scratch, replacing (not
merging into) whatever is already stored.

Run AFTER compute_tag_denylist.py so the recompute benefits from the
current denylist, on the Hermes host:

    docker exec -u hermes hermes-hermes-1 python3 \\
        /data/hermes/plugins/hermes_jobs/ops/backfill_tags.py

Uses store.replace_job_tags (full overwrite) rather than add_job_tags
(merge-only) -- this is the one place that is correct, since a cleanup
pass needs to be able to drop a tag a worse, earlier algorithm wrote.
The live per-job path in runner.py must keep using add_job_tags; never
switch that to replace_job_tags (see its own docstring).

Idempotent: recomputes purely from each job's own instruction + result,
never from the currently-stored tags, so re-running after further
tagging.py changes is always safe.
"""

from __future__ import annotations

import sys

sys.path.insert(0, "/data/hermes/plugins")
sys.path.insert(0, "/opt/hermes")

from hermes_jobs import store  # noqa: E402
from hermes_jobs import tagging  # noqa: E402


def main() -> None:
    rows = store.list_jobs(status=store.ST_DONE, limit=10000)
    print("found %d done jobs" % len(rows))

    changed = 0
    empty = 0
    errors = 0
    for row in rows:
        jid = row["id"]
        try:
            tags = tagging.compute_tags(row.get("body") or "", row.get("result") or "")
            store.replace_job_tags(jid, tags)
            if tags:
                changed += 1
            else:
                empty += 1
        except Exception as exc:
            errors += 1
            print("ERROR %s: %s" % (jid, exc))

    print("done: tagged=%d empty=%d errors=%d total=%d" % (
        changed, empty, errors, len(rows),
    ))


if __name__ == "__main__":
    main()
