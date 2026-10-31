"""Surface candidate entity-tag collisions for a HUMAN to review -- does
NOT write the denylist automatically. See tagging.py's module docstring
for why: an earlier version of this script DID auto-write, and its first
real run suppressed "Nishant Gurjer" and "Roshini Ranka" -- real,
frequently-referenced people, not word collisions -- purely because
frequency alone cannot tell "mentioned often because it's secretly a
common word" apart from "mentioned often because they matter". That is
now tagging.py's primary defense (_SINGLE_WORD_STOPWORDS, a word-identity
check: is the matched word ordinary English/place vocabulary on its
face, independent of how often it shows up).

This script is what you run to catch whatever the static stopword list
didn't anticipate. It still uses the phrase-vs-word provenance split
(tagging._scan_entity_matches): a canonical is only a candidate if jobs
mention it WITHOUT ever also containing its full name phrase, which is
exactly the pattern a real person's name never has but a common-word
collision always does.

Run on the Hermes host:

    docker exec -u hermes hermes-hermes-1 python3 \\
        /data/hermes/plugins/hermes_jobs/ops/compute_tag_denylist.py

Review the printed candidates. For each one that is genuinely a word
collision (not a real, if frequently-mentioned, person/project), add the
matched WORD to tagging.py's _SINGLE_WORD_STOPWORDS by hand -- that is
the permanent fix, checked into source. TAG_DENYLIST_PATH exists only
for a canonical you want suppressed without a clean single-word cause;
edit that file by hand too if you ever need it. Nothing here writes
either automatically.
"""

from __future__ import annotations

import sys
from collections import Counter

sys.path.insert(0, "/data/hermes/plugins")
sys.path.insert(0, "/opt/hermes")

from hermes_jobs import store  # noqa: E402
from hermes_jobs import tagging  # noqa: E402

THRESHOLD = 0.12


def main() -> None:
    rows = store.list_jobs(status=store.ST_DONE, limit=10000)
    total = len(rows)
    print("scanning %d done jobs" % total)
    if not total:
        print("nothing to scan")
        return

    word_only_counts: Counter = Counter()
    raw_counts: Counter = Counter()
    for row in rows:
        text = "\n".join(t for t in (row.get("body"), row.get("result")) if t)
        if not text.strip():
            continue
        try:
            matches = tagging._scan_entity_matches(text)
        except Exception:
            matches = []
        phrase_names = {m["label"].strip().lower() for m in matches if m["via"] == "phrase"}
        word_names = {m["label"].strip().lower() for m in matches if m["via"] == "word"}
        for name in phrase_names | word_names:
            raw_counts[name] += 1
        for name in word_names - phrase_names:
            word_only_counts[name] += 1

    candidates = sorted(
        ((n / total, name) for name, n in word_only_counts.items() if (n / total) >= THRESHOLD),
        reverse=True,
    )

    if not candidates:
        print("no candidates at >= %.0f%% word-only occurrence -- nothing to review" % (
            THRESHOLD * 100,
        ))
        return

    print(
        "\nCANDIDATES for human review (word-only occurrence >= %.0f%%).\n"
        "For each: is this a real person/project (leave alone), or a common\n"
        "word/place name that happens to start their stored name (add that\n"
        "word to tagging.py's _SINGLE_WORD_STOPWORDS)?\n" % (THRESHOLD * 100)
    )
    for rate, name in candidates:
        print("  word-only %5.1f%% (raw %5.1f%%)  %s" % (
            100.0 * rate, 100.0 * raw_counts[name] / total, name,
        ))
    print("\nNothing was written. Edit tagging.py / tag_denylist.json by hand.")


if __name__ == "__main__":
    main()
