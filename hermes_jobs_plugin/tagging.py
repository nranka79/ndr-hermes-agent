"""Best-effort job tagging: which people/projects/entities a job mentions,
plus a coarse work-type bucket (communication / follow_up / scheduling /
drafting_creative / research_lookup / compliance_finance / engineering).

PILOT SCOPE (2026-10-31): entity tags only use EXACT matches against the
shared contacts/projects/entities/land_proposals/topics registry
(tools.noun_resolver) -- never NounResolver.search()'s fuzzy/phonetic
results. Verified live against the real sheet before writing this:
search() returned confident-looking (score 0.9-1.0) but WRONG canonicals
for short/common tokens -- e.g. the single word "the" exact-matched a
contact whose stored alias is literally "The Ashok", and phonetic scoring
produced five different unrelated "Raghu *" contacts at 0.9 for one
"Raghu Iyer" mention. search() also collapses to ONE best hit per
canonical and that overwrite can silently replace a real exact hit with a
less reliable fuzzy/phonetic one for the same person. None of that is
reliable enough to put in front of a human as a tag, so this module talks
to the resolver's index directly and only keeps literal, whole-phrase
matches -- see _candidate_phrases for the exact noise-avoidance rule
(2-3 word windows, or single words of 4+ characters, to keep short
stopwords like "the"/"and"/"to" from ever being looked up at all).

NOISE CLEANUP (2026-11-01): backfilling all 190 real done jobs surfaced a
second, more insidious class of false positive that confidence scores
CANNOT distinguish: a single common word that happens to be the first
token of someone's multi-word contact name, e.g. "data" -> "Data Dorle",
"just" -> "just dial", "first" -> "First Bhavana", "bangalore" ->
"Bangalore Advertising". These score IDENTICALLY (confidence 0.85,
first-word-of-a-name tier) to the genuinely correct single-word matches
("bharat" -> "Bharat Hawaldar", "amir" -> "Amir Ahmadi") -- there is no
static signal in the match itself that tells them apart.

FIRST ATTEMPT, RETRACTED: corpus-frequency (a canonical's occurrence
rate across all tagged jobs) looked like a clean IDF-style signal --
collisions sat at 14-46% vs 8-11% for real contacts in an early sample.
It is NOT safe as an automatic filter: re-checked against the full
corpus, "nishant" -> "Nishant Gurjer" and "roshini" -> "Roshini Ranka"
ALSO cleared the threshold (24%, 25%) precisely BECAUSE they are real,
frequently-referenced people (Nishant is one of the two Telegram
operators) -- high frequency for a real person is the tag cloud WORKING
correctly, not noise. Frequency cannot tell "mentioned often because
it's a common word" apart from "mentioned often because they matter";
auto-suppressing by threshold would have silently hidden a true,
informative tag. Retracted in favour of:

  A short static stopword list (_SINGLE_WORD_STOPWORDS): grammar words
  plus generic place/business labels ("home", "data", "bangalore"...).
  This is a WORD-IDENTITY check, not a frequency check -- "data"/"just"/
  "them"/"first"/"road"/"bangalore" are ordinary English/place words
  checkable on sight; "nishant"/"roshini"/"bharat"/"kumar" are not, and
  never will be regardless of how often they're mentioned. Cheap, ships
  immediately, no job history required, and immune to the frequency
  trap above. ops/compute_tag_denylist.py still exists to SURFACE
  candidates (high word-only frequency) for a human to review and add
  to this list by hand -- it deliberately no longer auto-writes a
  suppression file, exactly because that auto-write is what caught
  Nishant and Roshini the first time.

TAG_DENYLIST_PATH / _read_denylist() remain as a safety net for a
manually-curated, hand-reviewed canonical name (never auto-populated)
in case a future word-identity gap surfaces that isn't worth a whole
new stopword -- empty/missing is the normal, expected state.

Tags are informational chips on the board, not something the agent acts
on, so false negatives (a name that didn't resolve, or one that got
suppressed) are the acceptable failure mode here -- never a wrong tag
presented as if it were right.
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# The registry is one shared company vault asset, not per-job-tenant --
# whichever chat/platform created the job, tags are resolved against this
# one identity's Google Sheets access (same sheet runner.py's owner_email
# binds for per-job actions, but tagging always uses this fixed account
# since it's a read of shared data, not an action taken as the job's owner).
TAG_IDENTITY_EMAIL = os.environ.get("HERMES_JOBS_TAG_IDENTITY_EMAIL", "ndr@ahfl.in")

# Lives OUTSIDE the plugin directory (same convention as settings.py's
# SETTINGS_PATH) so a plugin redeploy never resets a computed denylist.
TAG_DENYLIST_PATH = os.environ.get(
    "HERMES_JOBS_TAG_DENYLIST", "/data/hermes/hermes_jobs/tag_denylist.json",
)

_MIN_SINGLE_WORD_LEN = 4
MAX_TAGS = 20

# Work-type is classified from the INSTRUCTION's opening only, not the
# full instruction+result -- a long dictated transcript or a verbose
# agent reply has enough incidental vocabulary to trip almost every
# bucket at least once (verified: research_lookup alone fired on 42% of
# the real backfill). The opening is what a human would read first to
# answer "what kind of job is this", so it is also the most honest
# signal, not just the cheapest.
_WORK_TYPE_SCAN_CHARS = 220

_cached_uid: Optional[str] = None


def _tag_identity_uid() -> Optional[str]:
    """Resolve TAG_IDENTITY_EMAIL to a canonical vault user id, once.

    None (not a default/empty-string) means "could not resolve" so callers
    can tell that apart from "resolved to an empty id" and skip entity
    tagging entirely rather than silently tagging nothing forever without
    ever logging why.
    """
    global _cached_uid
    if _cached_uid is not None:
        return _cached_uid
    try:
        from tools import gws_vault_client as vault

        uid = vault.resolve("email", TAG_IDENTITY_EMAIL) or vault.resolve_any(TAG_IDENTITY_EMAIL)
    except Exception as exc:
        logger.warning("tagging: cannot reach vault to resolve %r: %s", TAG_IDENTITY_EMAIL, exc)
        uid = None
    if uid:
        _cached_uid = uid
    return uid


# Pure grammar/function words, plus generic business/location labels that
# are common enough to be the first token of a real contact's name
# without ever being a useful tag on their own ("home", "data", "call"...
# all confirmed live as real false positives, not hypothetical ones).
# Single-word candidates only -- a 2-3 word phrase made of these would be
# an unlikely coincidence, and dropping phrase matches is a much higher
# false-negative cost than dropping single words.
_SINGLE_WORD_STOPWORDS = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "have", "were",
    "was", "are", "is", "been", "will", "would", "could", "should",
    "there", "their", "they", "them", "then", "than", "when", "what",
    "which", "who", "whom", "whose", "where", "why", "how", "not", "but",
    "you", "your", "yours", "our", "ours", "his", "her", "hers", "its",
    "all", "any", "some", "each", "more", "most", "other", "such",
    "only", "own", "same", "just", "very", "can", "also", "into", "over",
    "after", "before", "about", "above", "below", "under", "again",
    "once", "here", "out", "off", "down", "up", "both", "few", "nor",
    "too", "home", "office", "team", "admin", "info", "help", "support",
    "sales", "data", "test", "demo", "call", "mail", "update", "status",
    "report", "note", "list", "form", "file", "first", "last", "next",
    "road", "city", "south", "north", "east", "west", "bangalore",
})


def _read_denylist() -> set:
    """Canonical names (lowercased) to never tag, re-read on every call.

    Same re-read-every-time convention as settings.max_concurrent_jobs():
    a recompute (ops/compute_tag_denylist.py) takes effect within
    whatever polling interval the caller runs at, no gateway restart. A
    missing/unreadable/malformed file is just "nothing suppressed yet",
    never an error that blocks tagging.
    """
    try:
        with open(TAG_DENYLIST_PATH) as fh:
            data = json.load(fh)
        names = data.get("suppressed_canonicals") or []
        return {str(n).strip().lower() for n in names if str(n).strip()}
    except FileNotFoundError:
        return set()
    except Exception as exc:
        logger.warning("tagging: cannot read denylist %s, ignoring: %s", TAG_DENYLIST_PATH, exc)
        return set()


def _candidate_phrases(normalized_text: str) -> "tuple[set, set]":
    """Returns (multi_word_phrases, single_word_phrases) separately.

    The split matters (2026-11-01): a canonical reached ONLY via a bare
    single word ("nishant" -> "Nishant Gurjer") is weak evidence -- it is
    structurally IDENTICAL to the real false positives ("data" -> "Data
    Dorle"), same 0.85 first-token-of-name confidence tier, no way to
    tell them apart from the match alone. A canonical reached via the
    full 2-3 word phrase actually present in the text ("nishant gurjer")
    is strong evidence a random common word cannot coincidentally
    produce. See extract_entity_tags: only word-only matches are ever
    checked against the frequency denylist; a phrase match always wins
    and is never suppressed.
    """
    words = normalized_text.split()
    multi: set = set()
    for n in (3, 2):
        for i in range(len(words) - n + 1):
            multi.add(" ".join(words[i:i + n]))
    single: set = set()
    for w in words:
        if len(w) >= _MIN_SINGLE_WORD_LEN and w not in _SINGLE_WORD_STOPWORDS:
            single.add(w)
    return multi, single


def _scan_entity_matches(text: str) -> List[Dict[str, str]]:
    """Like extract_entity_tags, but every match also carries ``via``
    ("phrase" or "word") so callers can apply the frequency denylist
    (or not) correctly. Internal -- extract_entity_tags is the public,
    denylist-applied shape every other caller should use.
    """
    uid = _tag_identity_uid()
    if not uid:
        return []
    from gateway.session_context import set_session_vars
    from tools.noun_resolver import get_resolver, _normalize

    set_session_vars(user_id=uid)
    resolver = get_resolver()
    if not resolver._index_built:
        return []
    multi, single = _candidate_phrases(_normalize(text))
    seen_canonicals: set = set()
    out: List[Dict[str, str]] = []
    with resolver._index_lock:
        # Multi-word phrases FIRST and unconditionally -- a canonical
        # confirmed this way is never reconsidered as word-only below,
        # regardless of set iteration order.
        for phrase in multi:
            entry = resolver._index.get(phrase)
            if not entry or entry["canonical"] in seen_canonicals:
                continue
            seen_canonicals.add(entry["canonical"])
            out.append({"type": entry["type"], "label": entry["canonical"], "via": "phrase"})
        for phrase in single:
            entry = resolver._index.get(phrase)
            if not entry or entry["canonical"] in seen_canonicals:
                continue
            seen_canonicals.add(entry["canonical"])
            out.append({"type": entry["type"], "label": entry["canonical"], "via": "word"})
    return out


def extract_entity_tags(text: str) -> List[Dict[str, str]]:
    """Exact-phrase scan against the shared registry. Returns [] on any
    failure (vault unreachable, index not built, etc) -- never raises;
    tagging must never be able to break job creation or completion.

    A word-only match (see _scan_entity_matches) is dropped if its
    canonical is on the frequency denylist; a phrase match never is.
    """
    text = (text or "").strip()
    if not text:
        return []
    try:
        denylist = _read_denylist()
        out: List[Dict[str, str]] = []
        for m in _scan_entity_matches(text):
            if m["via"] == "word" and m["label"].strip().lower() in denylist:
                continue
            out.append({"type": m["type"], "label": m["label"]})
        return out
    except Exception as exc:
        logger.warning("tagging: entity extraction failed, skipping: %s", exc)
        return []


# Ordered: first matching rule wins is NOT the semantic here -- a job can
# carry more than one work-type tag (e.g. "draft an email AND follow up
# next week" is both communication and follow_up). Keywords are matched
# as whole words against the lowercased text, not substrings, so
# "report" doesn't trigger on "reportedly" and "cal" doesn't trigger on
# "local". "call" was dropped from scheduling (2026-11-01): bare "call"
# is common in completely unrelated phrasing ("call job_complete") and
# fired on roughly half the real backfill -- "schedule"/"calendar"/
# "meeting"/"appointment" already cover the genuine scheduling case.
_WORK_TYPE_RULES: List[tuple] = [
    ("communication", (
        "email", "whatsapp", "message", "reply", "draft", "send", "write",
        "letter", "respond",
    )),
    ("follow_up", (
        "follow", "followup", "check back", "remind", "reminder", "nudge",
        "pending", "chase",
    )),
    ("scheduling", (
        "calendar", "schedule", "meeting", "slot", "invite",
        "appointment", "reschedule",
    )),
    ("drafting_creative", (
        "card", "image", "design", "creative", "invitation", "poster",
        "banner", "graphic",
    )),
    ("research_lookup", (
        "find", "search", "look up", "lookup", "research", "verify",
        "check status", "investigate",
    )),
    ("compliance_finance", (
        "tax", "filing", "invoice", "payment", "gst", "compliance",
        "accounts", "audit", "lease", "rent",
    )),
    ("engineering", (
        "code", "bug", "deploy", "script", "fix", "server", "database",
        "api", "endpoint", "repo",
    )),
]


def classify_work_type(text: str) -> List[str]:
    """Deterministic keyword rules, not an LLM call.

    See the module docstring: tags are informational, and these buckets
    are coarse by design -- a wrong/missing bucket is low-stakes, so a
    free, instant, fully-explainable rule set is the right tool here, not
    a model. Caller is expected to pass a bounded prefix, not the full
    instruction+result -- see _WORK_TYPE_SCAN_CHARS.
    """
    norm = (text or "").lower()
    hits: List[str] = []
    for label, keywords in _WORK_TYPE_RULES:
        for kw in keywords:
            if " " in kw:
                if kw in norm:
                    hits.append(label)
                    break
            elif re.search(r"\b%s\b" % re.escape(kw), norm):
                hits.append(label)
                break
    return hits


def compute_tags(instruction: str, extra_text: str = "") -> List[str]:
    """Combine entity + work-type tags into the flat ``"type:Label"``
    strings the board stores/renders.

    Entity extraction scans *instruction + extra_text* combined --
    verified live that a name mentioned only in a job's RESULT (e.g. the
    agent's own reply naming who it actually drafted something for) is
    real, useful signal, not noise, so this intentionally has no length
    cap. Work-type classification deliberately does NOT scan extra_text
    and only looks at a bounded prefix of instruction -- see
    classify_work_type / _WORK_TYPE_SCAN_CHARS.
    """
    combined = "\n".join(t for t in (instruction, extra_text) if t)
    if not combined.strip():
        return []
    out: List[str] = []
    for ent in extract_entity_tags(combined):
        out.append("%s:%s" % (ent["type"], ent["label"]))
    for work in classify_work_type((instruction or "")[:_WORK_TYPE_SCAN_CHARS]):
        out.append("work:%s" % work)
    return out[:MAX_TAGS]
