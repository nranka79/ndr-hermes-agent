"""Standalone HTTP backend for the jobs.ahfl.in PWA.

Runs as its OWN container (reusing the ``hermes-hermes:latest`` image,
which already has every dependency ``hermes_cli.kanban_db`` and this
plugin need -- it's the exact same import path the gateway process
itself uses). It never touches ``hermes-hermes-1`` or ``hermes-apps-1``.

Auth model: this process trusts the ``X-Forwarded-Email`` header and
assumes nginx + oauth2-proxy sit in front of it and that NOTHING else can
reach it -- it binds 127.0.0.1 only, inside a container with no public
port. The real access boundary is oauth2-proxy's allowed-email list, not
this code. Within that boundary, each signed-in person sees and acts on
ONLY their own jobs. Ownership is the job row's ``tenant`` column: the
email for board-created jobs, or the platform user id for chat-created
jobs (for example a Telegram numeric id). Because those surfaces do not
share an identifier, ``authz.py`` resolves the signed-in email through
gws-vault and returns every alias linked to that person. A job is visible
when its tenant is in that alias set.

Admins are exactly the vault identities whose ``role`` is ``"admin"``.
They may view every job, and (per explicit product decision) may also
answer, continue, or drop any job from the All jobs view. Everyone else
gets a 403 when they address another user's job by id, including through
the direct ``/api/jobs/{id}`` URL. A missing job is still a 404.

``_DISPLAY_NAMES`` below is cosmetic labelling only, never an access check.

Run: python3 board_server.py
Env: BOARD_PORT (default 8900), API_SERVER_KEY (to call /v1/runs if ever
     needed), HERMES_API_BASE (default http://hermes:8642 -- the
     in-network container name, NOT 127.0.0.1, since this runs in a
     different container than the gateway).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, "/data/hermes/plugins")
sys.path.insert(0, "/opt/hermes")

from aiohttp import web, ClientSession, FormData  # noqa: E402

from hermes_jobs import authz, store  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("jobs-board")

STATIC_DIR = Path(__file__).parent / "static"
# Same STT chain as chat.ahfl.in / voice.ahfl.in, but addressed through the
# AI Model Gateway (llm-gateway) so jobs dictation shares the central
# Groq -> AssemblyAI fallback pools. The voice-app bridge and the legacy
# free-whisper endpoint remain as fallbacks (see HERMES_STT_FALLBACK_URLS).
STT_URL = os.environ.get(
    "HERMES_STT_URL", "http://llm-gateway:8321/v1/audio/transcriptions",
)
STT_FALLBACK_URLS = [
    u.strip() for u in os.environ.get(
        "HERMES_STT_FALLBACK_URLS",
        "http://hermes-apps:3000/v1/audio/transcriptions,"
        "http://hermes-apps:8100/v1/audio/transcriptions",
    ).split(",") if u.strip()
]
AUTH_HEADER = "X-Forwarded-Email"

# Same dictation-redraft + sheet/AI noun-correction pipeline voice.ahfl.in's
# "email" reformat button and the WhatsApp voice-note workflows use (n8n
# workflow "Thought2CleanText": LLM redraft -> markdown strip -> Hermes Noun
# Corrector against the shared contacts/projects/entities sheets). Optional:
# if unset or unreachable, /api/transcribe falls back to the raw STT text
# rather than blocking dictation on it.
CLEANTEXT_WEBHOOK_URL = os.environ.get("CLEANTEXT_WEBHOOK_URL", "")

# Cosmetic display labels only (see module docstring) -- never used for
# access control. Edit freely; an unknown id just falls back to raw text.
_DISPLAY_NAMES = {
    ("telegram", "7449813913"): "Nishant (Telegram)",
    ("telegram", "8717455402"): "Bharat (Telegram)",
}


def _display_origin(job: Dict[str, Any]) -> str:
    """Return the human-facing origin label for a job row.

    Web jobs show the board host; chat jobs show a cosmetic person label when
    one is known, otherwise a platform + id fallback. This is presentation only
    and is never used to authorize anything.
    """
    platform = job.get("origin_platform") or "cli"
    if platform == "web":
        return "jobs.ahfl.in"
    chat_id = job.get("origin_chat_id") or job.get("tenant") or ""
    label = _DISPLAY_NAMES.get((platform, str(chat_id)))
    if label:
        return label
    return "%s%s" % (platform, (" " + chat_id) if chat_id else "")


def _display_owner(job: Dict[str, Any]) -> str:
    """Return a useful owner label for the admin-only All jobs view.

    A web job's tenant is already an email, which is the clearest owner label.
    For chat-created jobs it is a numeric platform id, so reuse the existing
    cosmetic origin label (for example "Nishant (Telegram)") instead of showing
    a bare number. Never an access decision -- only display.
    """
    tenant = str(job.get("tenant") or "").strip()
    if not tenant:
        return ""
    if "@" in tenant:
        return tenant
    return _display_origin(job) or tenant


async def _cleanup_dictation(session: ClientSession, raw_text: str,
                             user_email: str = "", user_label: str = "") -> str:
    """Redraft + noun-correct a raw STT transcript via the shared n8n webhook.

    Best-effort: any failure (unset URL, timeout, bad response) returns the
    raw text unchanged rather than failing the whole dictation flow -- a
    slightly rough transcript is fine, no transcript at all is not.
    """
    if not CLEANTEXT_WEBHOOK_URL or not raw_text.strip():
        return raw_text
    try:
        async with session.post(
            CLEANTEXT_WEBHOOK_URL,
            json={
                "transcription": raw_text,
                "user_email": user_email or "unknown",
                "user_label": user_label or user_email or "unknown",
            },
            timeout=100,
        ) as resp:
            if resp.status != 200:
                logger.warning("cleantext webhook HTTP %s", resp.status)
                return raw_text
            data = await resp.json(content_type=None)
            cleaned = (data or {}).get("text")
            return cleaned if isinstance(cleaned, str) and cleaned.strip() else raw_text
    except Exception as exc:
        logger.warning("cleantext webhook failed, using raw transcript: %s", exc)
        return raw_text


def _completed_artifacts(job_id: str) -> List[Dict[str, Any]]:
    """Return the file list the agent reported via ``job_complete``.

    Reads the most recent ``completed`` task_event's payload -- the only
    place ``artifacts`` is currently persisted (see ``store.complete_job``).
    Each entry is re-verified against disk on every call rather than
    trusted blindly: a file a prior run produced may since have been
    cleaned up, and this list doubles as the download endpoint's
    allowlist, so it must reflect what is actually readable right now.
    """
    for e in store.list_events(job_id, limit=50):
        if e["kind"] != "completed":
            continue
        try:
            payload = json.loads(e.get("payload") or "{}")
        except Exception:
            payload = {}
        out: List[Dict[str, Any]] = []
        for raw_path in payload.get("artifacts") or []:
            p = str(raw_path)
            size = None
            try:
                if os.path.isfile(p):
                    size = os.path.getsize(p)
            except OSError:
                size = None
            out.append({"path": p, "name": os.path.basename(p) or p, "size": size})
        return out
    return []


def _parse_tags(raw: Any) -> List[str]:
    """Decode the JSON-array string stored in ``tasks.tags`` safely."""
    try:
        tags = json.loads(raw or "[]")
    except Exception:
        return []
    return tags if isinstance(tags, list) else []


MAX_TAG_LENGTH = 80


def _normalize_tag(raw: Any) -> str:
    """Normalize a user-entered tag into the board's ``type:Label`` shape.

    Existing tags are ``contacts:Name``, ``projects:Name``, ``work:follow_up``,
    etc. A person editing tags may type a bare noun ("Raghu Iyer") or a fully
    typed tag ("work:follow_up"). Bare values become ``manual:<text>`` so they
    remain valid, neutral-coloured chips and can later be promoted into the
    controlled noun universe. Returns "" for empty/oversized input.
    """
    text = " ".join(str(raw or "").replace("\n", " ").split())
    if not text or len(text) > MAX_TAG_LENGTH:
        return ""
    if ":" not in text:
        text = "manual:" + text
    tag_type, _, label = text.partition(":")
    tag_type = tag_type.strip().lower() or "manual"
    label = label.strip()
    if not label:
        return ""
    return ("%s:%s" % (tag_type, label))[:MAX_TAG_LENGTH]


def _serialize(job: Dict[str, Any]) -> Dict[str, Any]:
    try:
        options = json.loads(job.get("suggested_options") or "[]")
    except Exception:
        options = []
    return {
        "id": job["id"],
        "title": job.get("title") or "",
        "instruction": job.get("body") or "",
        "status": job.get("status"),
        "tags": _parse_tags(job.get("tags")),
        "pending_kind": job.get("pending_kind"),
        "question": job.get("question"),
        "question_context": job.get("question_context"),
        "suggested_options": options,
        "answer": job.get("answer"),
        "result": job.get("result"),
        "last_failure_error": job.get("last_failure_error"),
        "resume_rounds": job.get("resume_rounds") or 0,
        "consecutive_failures": job.get("consecutive_failures") or 0,
        "created_at": job.get("created_at"),
        "completed_at": job.get("completed_at"),
        "dropped_at": job.get("dropped_at"),
        "drop_reason": job.get("drop_reason"),
        "origin_platform": job.get("origin_platform"),
        "origin_display": _display_origin(job),
        # Owner fields are additive. They let the admin All jobs view show
        # whose row it is without changing any existing field's meaning.
        "owner": job.get("tenant") or "",
        "owner_display": _display_owner(job),
        "session_id": job.get("session_id"),
        "parent_job_id": job.get("parent_job_id"),
    }


def _who(request: web.Request) -> str:
    """Return the normalized signed-in email supplied by oauth2-proxy.

    Emails are lower-cased here because every ownership comparison and every
    vault lookup is case-insensitive. The literal fallback "unknown" is only
    reachable in the BOARD_ALLOW_NO_AUTH development path; it owns no jobs.
    """
    return (request.headers.get(AUTH_HEADER, "unknown") or "unknown").strip().lower()


def _identity(request: web.Request) -> authz.Identity:
    """Return the vault-resolved identity cached on this request by middleware.

    Handlers call this instead of re-reading the header so one request performs
    exactly one (possibly cached) vault lookup. The fallback is safe: an
    identity that owns only the exact header email and has no admin rights.
    """
    identity = request.get("identity")
    if isinstance(identity, authz.Identity):
        return identity
    return authz.identity_for_email(_who(request))


def _owner_tenants(request: web.Request) -> Optional[List[str]]:
    """Return the tenant filter for a write/read, or None for a vault admin.

    ``None`` is the only value that disables owner filtering in store.py, so
    this function is the single place that decides "is this caller allowed to
    bypass ownership?" Only a strict vault role-admin produces None.
    """
    identity = _identity(request)
    if identity.is_admin:
        return None
    return sorted(identity.aliases)


def _load_visible_job(request: web.Request, job_id: str):
    """Load a job and return ``(job, error_response)`` with the right status.

    The first read is already owner-scoped in SQL: a non-admin passes their
    alias list to ``store.get_job``, so another person's row is never returned
    to application code. If that scoped read misses, one unfiltered existence
    check distinguishes "someone else's job" (403, the explicit product
    requirement for direct /api/jobs/{id} access) from "does not exist" (404).
    Admins pass ``None`` and therefore get the job on the first read.

    This helper is used by every detail/read/write endpoint so the rule cannot
    drift between routes.
    """
    if not job_id:
        return None, web.json_response({"error": "not found"}, status=404)

    tenants = _owner_tenants(request)
    job = store.get_job(job_id, tenants=tenants)
    if job:
        return job, None

    if tenants is not None and store.get_job(job_id) is not None:
        return None, web.json_response({"error": "forbidden"}, status=403)
    return None, web.json_response({"error": "not found"}, status=404)


async def require_auth(request: web.Request, handler):
    """Authenticate an /api request and attach its vault identity.

    Defense in depth only -- see module docstring. The real gate is
    oauth2-proxy; this refuses to silently treat a misconfigured proxy
    pass-through as "someone logged in". The vault lookup runs in a worker
    thread because it is a blocking Unix-socket call and must not stall the
    aiohttp event loop.
    """
    if not request.headers.get(AUTH_HEADER):
        if os.environ.get("BOARD_ALLOW_NO_AUTH") != "1":
            return web.json_response({"error": "no identity header from proxy"}, status=401)

    # Resolve once per request. authz.py owns its short TTL cache, so the 5s
    # board poll normally performs no vault I/O at all.
    request["identity"] = await asyncio.to_thread(authz.identity_for_email, _who(request))
    return await handler(request)


@web.middleware
async def auth_middleware(request: web.Request, handler):
    """Apply the API identity gate only to /api/* routes.

    Static shell files and /health deliberately bypass it: oauth2-proxy already
    protects public traffic, and the PWA shell must remain loadable for the
    service worker/manifest paths.
    """
    if request.path.startswith("/api/"):
        return await require_auth(request, handler)
    return await handler(request)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

LANES = {
    store.ST_QUEUED: "working",
    store.ST_RUNNING: "working",
    store.ST_WAIT_QUESTION: "needs_you",
    store.ST_WAIT_FAILURE: "needs_you",
    store.ST_DONE: "done",
    store.ST_DROPPED: "dropped",
}


# lane -> the statuses it contains (inverse of LANES above).
LANE_STATUSES: Dict[str, List[str]] = {}
for _status, _lane in LANES.items():
    LANE_STATUSES.setdefault(_lane, []).append(_status)

DEFAULT_PAGE_LIMIT = 50


def _snippet(row: Dict[str, Any]) -> str:
    """One line of preview text, mirroring what the row used to show.

    Same precedence the frontend's jobSummary() applied client-side, moved
    server-side so the list no longer has to ship the full question /
    result / instruction text just to render three clamped lines.
    """
    if row.get("pending_kind") == store.PENDING_CLARIFICATION:
        return row.get("snip_question") or "Waiting on your answer."
    if row.get("pending_kind") == store.PENDING_FAILURE:
        return row.get("snip_failure") or "The run failed."
    if row.get("status") == store.ST_DONE:
        return row.get("snip_result") or "No final reply recorded."
    return row.get("snip_body") or ""


def _serialize_slim(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "title": row.get("title") or "",
        "status": row.get("status"),
        "lane": LANES.get(row.get("status"), "other"),
        "pending_kind": row.get("pending_kind"),
        "snippet": _snippet(row),
        "tags": _parse_tags(row.get("tags")),
        "created_at": row.get("created_at"),
        "completed_at": row.get("completed_at"),
        "dropped_at": row.get("dropped_at"),
        "resume_rounds": row.get("resume_rounds") or 0,
        "parent_job_id": row.get("parent_job_id"),
        "origin_platform": row.get("origin_platform"),
        "origin_display": _display_origin(row),
        # Same owner fields as the full serializer. The list query already
        # selects tenant via _LIST_COLUMNS, so this adds no database cost.
        "owner": row.get("tenant") or "",
        "owner_display": _display_owner(row),
        # Tells the UI this object is a list row, not a full job -- the
        # detail modal must wait for /api/jobs/{id} before it can render
        # instruction/result/question bodies.
        "slim": True,
    }


async def api_list_jobs(request: web.Request) -> web.Response:
    """One page of jobs for a lane, newest first, plus global lane counts.

    Paginated because the old "return every job in full" response was
    278 KB at 59 jobs and the board re-fetches it every 5 seconds.

    ``scope=all`` is the admin-only cross-user view. Everyone, including an
    admin, defaults to ``scope=mine``. A non-admin requesting ``all`` is refused
    rather than silently downgraded, so the client can never think it is seeing
    the whole board when it is not. The same tenant scope is passed to both the
    page query and the counts query so the lane badges cannot leak a total from
    jobs the list refuses to show.
    """
    lane = (request.query.get("lane") or "").strip()
    statuses = LANE_STATUSES.get(lane) if lane else None
    if lane and statuses is None:
        return web.json_response({"error": "unknown lane %r" % lane}, status=400)

    identity = _identity(request)
    scope = (request.query.get("scope") or "mine").strip().lower()
    if scope not in ("mine", "all"):
        return web.json_response({"error": "scope must be 'mine' or 'all'"}, status=400)
    scope_all = scope == "all"
    if scope_all and not identity.is_admin:
        return web.json_response({"error": "forbidden"}, status=403)

    # Optional owner chip filter. It only makes sense inside the admin-only All
    # jobs view; accepting it in My jobs would silently turn an owner-scoped
    # request into someone else's jobs, so reject that combination outright.
    owner = (request.query.get("owner") or "").strip()
    if owner and not scope_all:
        return web.json_response(
            {"error": "owner filter requires scope=all"}, status=403,
        )

    # None means no owner filter and is reachable only after the strict vault
    # role-admin check above. A selected owner chip narrows All jobs to that
    # exact tenant; otherwise non-admins get their concrete alias set.
    if scope_all:
        tenants: Optional[List[str]] = [owner] if owner else None
    else:
        tenants = sorted(identity.aliases)

    try:
        limit = int(request.query.get("limit") or DEFAULT_PAGE_LIMIT)
    except ValueError:
        return web.json_response({"error": "limit must be an integer"}, status=400)

    q = (request.query.get("q") or "").strip() or None

    # Date bounds arrive as epoch seconds computed by the BROWSER from
    # local midnight. The server never derives a calendar day itself: it
    # has no idea what timezone the user is in, and bucketing by UTC date
    # would file an early-morning IST job under the previous day.
    def _epoch(name):
        raw = request.query.get(name)
        if raw in (None, ""):
            return None
        return int(raw)

    try:
        created_from = _epoch("from")
        created_to = _epoch("to")
    except ValueError:
        return web.json_response(
            {"error": "from/to must be epoch seconds"}, status=400,
        )

    cursor = request.query.get("cursor") or None
    try:
        rows, next_cursor = store.list_jobs_page(
            statuses=statuses, q=q, created_from=created_from,
            created_to=created_to, tenants=tenants, limit=limit, cursor=cursor,
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    by_status = store.count_jobs_by_status(
        q=q, created_from=created_from, created_to=created_to,
        tenants=tenants,
    )
    counts: Dict[str, int] = {}
    for status, n in by_status.items():
        counts[LANES.get(status, "other")] = counts.get(LANES.get(status, "other"), 0) + n

    return web.json_response({
        "jobs": [_serialize_slim(r) for r in rows],
        "next_cursor": next_cursor,
        "counts": counts,
        "total": sum(by_status.values()),
    })


async def api_list_owners(request: web.Request) -> web.Response:
    """List every job owner for the admin-only All jobs filter chips.

    This is intentionally admin-only: the list itself reveals which people use
    the board and how many jobs each has. The endpoint returns raw ``tenant``
    (the exact value stored on jobs, used as the filter key) plus a cosmetic
    ``display`` label and total count. Non-admins receive 403, matching the
    scope=all rule on the list endpoint.
    """
    if not _identity(request).is_admin:
        return web.json_response({"error": "forbidden"}, status=403)

    owners = []
    for row in store.list_owners():
        owners.append({
            "tenant": row.get("tenant") or "",
            "display": _display_owner(row),
            "count": row.get("count") or 0,
        })
    return web.json_response({"owners": owners, "total": len(owners)})


MAX_ATTACHMENT_BYTES = 20 * 1024 * 1024
MAX_ATTACHMENTS_PER_REQUEST = 10


async def _parse_body_and_files(request: web.Request):
    """Accept either application/json or multipart/form-data.

    Multipart lets the same POST carry files alongside the text fields a
    plain JSON body would send (instruction/text/extra/title/parent_job_id),
    so the browser never needs two round trips to attach a file to an
    action. Returns (fields, files); files is a list of
    (filename, bytes, content_type), always [] for a JSON body.
    """
    files = []
    if (request.content_type or "").startswith("multipart/"):
        fields = {}
        reader = await request.multipart()
        while True:
            part = await reader.next()
            if part is None:
                break
            if part.filename:
                data = await part.read(decode=False)
                if data:
                    files.append((
                        part.filename, data,
                        part.headers.get("Content-Type") or "application/octet-stream",
                    ))
            else:
                raw = await part.read(decode=False)
                fields[part.name] = raw.decode("utf-8", errors="replace")
        return fields, files
    body = await request.json() if request.can_read_body else {}
    return body, files


def _store_uploaded_files(job_id, files, uploaded_by):
    stored = 0
    for filename, data, content_type in files:
        if stored >= MAX_ATTACHMENTS_PER_REQUEST:
            logger.warning("job %s: too many files in one request, dropping the rest", job_id)
            break
        if len(data) > MAX_ATTACHMENT_BYTES:
            logger.warning(
                "job %s: attachment %r too large (%d bytes), skipped",
                job_id, filename, len(data),
            )
            continue
        try:
            store.record_input_attachment(
                job_id, filename=filename, data=data,
                content_type=content_type, uploaded_by=uploaded_by,
            )
            stored += 1
        except Exception:
            logger.exception("job %s: failed to store attachment %r", job_id, filename)
    return stored


async def api_create_job(request: web.Request) -> web.Response:
    """Create a queued job from the board (typed or dictated instruction).

    The gateway's existing job runner claims it from kanban.db exactly as it
    does a Telegram ``/job`` -- this endpoint only inserts the row, so job
    creation and execution keep one code path. Origin is ``web`` with no chat
    id, which means delivery.py deliberately skips chat notifications and the
    result is read from this board.

    parent_job_id (optional) makes this a chained "Next job": the new
    job's own instruction is whatever the human asked for next, and the
    parent's instruction + result are folded in as context so the agent
    does not need the human to repeat what was already established.
    """
    fields, files = await _parse_body_and_files(request)
    instruction = (fields.get("instruction") or "").strip()
    title = (fields.get("title") or "").strip() or None
    parent_job_id = (fields.get("parent_job_id") or "").strip() or None
    idempotency_key = (fields.get("idempotency_key") or "").strip() or None
    if not instruction:
        return web.json_response({"error": "instruction is required"}, status=400)

    # A "Next job" chain folds the parent's instruction and result into the new
    # job body. That makes the parent lookup an information-disclosure surface:
    # a caller must not be able to read another user's parent content by
    # supplying its id. Admin has full control, so _load_visible_job also
    # permits it there.
    parent = None
    if parent_job_id:
        parent, parent_error = _load_visible_job(request, parent_job_id)
        if parent_error:
            return parent_error

    body_text = instruction
    if parent:
        body_text = (
            "%s\n\n--- Context: continuing job %s ---\n"
            "Previous instruction:\n%s\n\n"
            "Previous result:\n%s\n"
        ) % (
            instruction, parent["id"],
            parent.get("body") or "", parent.get("result") or "(no result recorded)",
        )

    who = _who(request)
    try:
        job_id = store.create_job(
            instruction=body_text,
            title=title,
            tenant=who,
            origin_platform="web",
            origin_chat_id="",
            origin_thread_id="",
            origin_message_id="",
            parent_job_id=parent["id"] if parent else None,
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    _store_uploaded_files(job_id, files, who)

    job = store.get_job(job_id)
    data = _serialize(job or {"id": job_id})
    data["lane"] = LANES.get(data.get("status"), "working")
    logger.info(
        "job %s created from board by %s%s", job_id, who,
        (" (chained from %s)" % parent["id"]) if parent else "",
    )
    return web.json_response({"ok": True, "job": data}, status=201)


async def api_get_job(request: web.Request) -> web.Response:
    """Return one job's full detail only to its owner or a vault admin.

    This is the endpoint the SPA opens when a job row is clicked, and also the
    endpoint a pasted /api/jobs/{id} URL hits. Missing = 404, someone else's job
    = 403, so the check happens before any body/result/attachment is serialized.
    """
    job, error = _load_visible_job(request, request.match_info["job_id"])
    if error:
        return error
    data = _serialize(job)
    data["lane"] = LANES.get(data["status"], "other")
    data["events"] = [
        {"kind": e["kind"], "created_at": e["created_at"]}
        for e in reversed(store.list_events(job["id"], limit=50))
    ]
    data["artifacts"] = _completed_artifacts(job["id"]) if job["status"] == store.ST_DONE else []
    data["input_attachments"] = [
        {
            "path": a["stored_path"], "name": a["filename"], "size": a.get("size"),
            "uploaded_by": a.get("uploaded_by"), "created_at": a.get("created_at"),
        }
        for a in store.list_input_attachments(job["id"])
    ]
    data["parent_job_id"] = job.get("parent_job_id")
    return web.json_response(data)


async def api_download_artifact(request: web.Request) -> web.Response:
    """Stream a file this job either produced or had uploaded to it.

    The only allowlist is "is this path exactly one this job's own
    job_complete artifacts OR its own input attachments list" --
    re-derived fresh from the event log / attachments table on every
    request, never trusted from the query string alone. This is what stops
    the endpoint from becoming an arbitrary-file-read: a path that is not
    in that job's own file list is refused outright, regardless of whether
    it exists on disk.
    """
    job_id = request.match_info["job_id"]
    # Authorization comes before the path allowlist check. A non-owner must not
    # even learn whether a guessed path belongs to this job or exists on disk.
    job, error = _load_visible_job(request, job_id)
    if error:
        return error
    requested = request.query.get("path") or ""
    allowed = {a["path"] for a in _completed_artifacts(job_id)}
    allowed |= {a["stored_path"] for a in store.list_input_attachments(job_id)}
    if not requested or requested not in allowed:
        return web.json_response({"error": "not a known file for this job"}, status=403)
    if not os.path.isfile(requested):
        return web.json_response({"error": "file no longer exists on disk"}, status=404)
    return web.FileResponse(
        requested,
        headers={"Content-Disposition": 'attachment; filename="%s"' % os.path.basename(requested)},
    )


async def api_answer(request: web.Request) -> web.Response:
    """Answer a job's clarification question.

    The job is authorized before the body is even parsed, and the UPDATE itself
    also receives the caller's tenant filter (None for admins). That double
    guard means a non-owner cannot mutate another user's job even if a future
    refactor accidentally drops the pre-check.
    """
    job_id = request.match_info["job_id"]
    _, error = _load_visible_job(request, job_id)
    if error:
        return error
    fields, files = await _parse_body_and_files(request)
    text = (fields.get("text") or "").strip()
    if not text:
        return web.json_response({"error": "text is required"}, status=400)
    ok = store.answer_job(job_id, text, tenants=_owner_tenants(request))
    if not ok:
        job = store.get_job(job_id)
        return web.json_response(
            {"error": "job is not waiting on a question",
             "status": (job or {}).get("status")},
            status=409,
        )
    _store_uploaded_files(job_id, files, _who(request))
    logger.info("job %s answered by %s", job_id, _who(request))
    return web.json_response({"ok": True})


async def api_continue(request: web.Request) -> web.Response:
    """Retry a failed job with optional extra input.

    Same two-layer owner guard as answer: a visibility pre-check plus a
    tenant-restricted UPDATE. Admins pass None and may retry any user's job.
    """
    job_id = request.match_info["job_id"]
    _, error = _load_visible_job(request, job_id)
    if error:
        return error
    fields, files = await _parse_body_and_files(request)
    extra = (fields.get("extra") or "").strip()
    ok = store.continue_job(
        job_id, extra_input=extra, tenants=_owner_tenants(request),
    )
    if not ok:
        job = store.get_job(job_id)
        return web.json_response(
            {"error": "job is not in the failed lane",
             "status": (job or {}).get("status")},
            status=409,
        )
    _store_uploaded_files(job_id, files, _who(request))
    logger.info("job %s continued by %s", job_id, _who(request))
    return web.json_response({"ok": True})


async def api_drop(request: web.Request) -> web.Response:
    """Permanently drop a job (terminal archived state).

    The visibility check happens before parsing the body, and the UPDATE carries
    the caller's tenant filter for non-admins. Admins have full control and may
    drop any user's job from the All jobs view.
    """
    job_id = request.match_info["job_id"]
    _, error = _load_visible_job(request, job_id)
    if error:
        return error
    body = await request.json() if request.can_read_body else {}
    reason = (body.get("reason") or "").strip()
    who = _who(request)
    ok = store.drop_job(
        job_id, by=who, reason=reason, tenants=_owner_tenants(request),
    )
    if not ok:
        return web.json_response({"error": "could not drop"}, status=409)
    logger.info("job %s dropped by %s", job_id, who)
    return web.json_response({"ok": True})


async def api_update_tags(request: web.Request) -> web.Response:
    """Add or remove one tag on a job.

    Body: ``{"action": "add"|"remove", "tag": "..."}``.

    Authorization uses the same owner-or-admin rule as every other job action.
    Non-admins pass their alias set into the store write, so even a direct API
    call cannot edit tags on someone else's job. Admins have full control from
    the All jobs view. The response returns the job's resulting tag list so the
    UI can re-render immediately without a second detail fetch.
    """
    job_id = request.match_info["job_id"]
    _, error = _load_visible_job(request, job_id)
    if error:
        return error

    body = await request.json() if request.can_read_body else {}
    action = (body.get("action") or "").strip().lower()
    raw_tag = body.get("tag") or ""
    if action not in ("add", "remove"):
        return web.json_response(
            {"error": "action must be 'add' or 'remove'"}, status=400,
        )

    if action == "add":
        tag = _normalize_tag(raw_tag)
        if not tag:
            return web.json_response({"error": "tag is required"}, status=400)
        ok = store.add_job_tags(
            job_id, [tag], tenants=_owner_tenants(request),
        )
    else:
        tag = str(raw_tag or "").strip()
        if not tag:
            return web.json_response({"error": "tag is required"}, status=400)
        ok = store.remove_job_tag(
            job_id, tag, tenants=_owner_tenants(request),
        )

    if not ok:
        return web.json_response({"error": "could not update tags"}, status=409)

    job = store.get_job(job_id, tenants=_owner_tenants(request))
    if not job:
        return web.json_response({"error": "not found"}, status=404)
    tags = _parse_tags(job.get("tags"))
    # add_job_tags is merge-only and applies a hard cap. If the requested tag
    # is still absent after the write, the cap (not a duplicate) swallowed it;
    # tell the user to remove a chip first rather than reporting a false success.
    if action == "add" and tag not in tags:
        return web.json_response(
            {"error": "tag limit reached; remove a tag first", "tags": tags},
            status=409,
        )
    logger.info("job %s tag %s by %s: %s", job_id, action, _who(request), tag)
    return web.json_response({"ok": True, "tags": tags})


MAX_AUDIO_BYTES = 25 * 1024 * 1024


async def _read_audio_field(request: web.Request):
    """Pull the 'audio' (or legacy 'file') multipart field out of a request.

    Shared by every endpoint that accepts a recorded clip. Returns
    (audio_bytes, content_type, error_response) -- exactly one of the
    first two or the third is meaningful; check error_response first.
    """
    reader = await request.multipart()
    field = await reader.next()
    if field is None or field.name not in ("audio", "file"):
        return None, None, web.json_response(
            {"error": "expected multipart field 'audio'"}, status=400,
        )
    audio_bytes = await field.read(decode=False)
    if not audio_bytes:
        return None, None, web.json_response({"error": "empty audio upload"}, status=400)
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        return None, None, web.json_response({"error": "audio too large"}, status=413)
    ctype = field.headers.get("Content-Type") or "audio/webm"
    return audio_bytes, ctype, None


async def _transcribe_bytes(session: ClientSession, audio_bytes: bytes, content_type: str,
                            identity: dict | None = None):
    """Run audio through the STT fallback chain. Returns (text, provider, error).

    Primary: the AI Model Gateway's OpenAI-compatible
    /v1/audio/transcriptions (same Groq-whisper -> AssemblyAI pools that
    voice.ahfl.in and chat.ahfl.in dictation use). Fallbacks: the voice-app
    STT bridge, then the free-whisper gateway's OpenAI-compatible endpoint.
    On total failure, text is None and error explains why -- the caller
    decides what HTTP status that becomes.
    """
    urls = [STT_URL] + [u for u in STT_FALLBACK_URLS if u and u != STT_URL]
    last_error = ""
    for url in urls:
        form = FormData()
        form.add_field("file", audio_bytes, filename="audio.webm", content_type=content_type)
        headers = {
            "X-Hermes-Client": "jobs-board",
            "X-Hermes-Platform": "jobs",
            "X-Hermes-Job-Type": "jobs",
        }
        headers.update(identity or {})
        try:
            async with session.post(url, data=form, headers=headers, timeout=230) as resp:
                raw = await resp.text()
                if resp.status != 200:
                    last_error = "HTTP %s: %s" % (resp.status, raw[:200])
                    logger.warning("transcribe %s failed: %s", url, last_error)
                    continue
                try:
                    result = json.loads(raw)
                except Exception:
                    result = {"text": raw}
                text = result.get("text") if isinstance(result, dict) else None
                if text:
                    logger.info("transcribed %d bytes via %s", len(audio_bytes), url)
                provider = (result or {}).get("provider") if isinstance(result, dict) else None
                return text or "", provider, None
        except Exception as exc:
            last_error = str(exc)
            logger.warning("transcribe %s unreachable: %s", url, exc)
    logger.error("all transcription backends failed: %s", last_error)
    return None, None, last_error


async def api_transcribe(request: web.Request) -> web.Response:
    """Proxy an audio blob to the shared STT chain and return text.

    The legacy /transcribe route is not used: it expects a raw audio
    body, while this PWA sends multipart.
    """
    audio_bytes, ctype, err = await _read_audio_field(request)
    if err:
        return err
    who = _who(request)
    async with ClientSession() as session:
        text, provider, error = await _transcribe_bytes(
            session, audio_bytes, ctype,
            {"X-Hermes-User-Id": who, "X-Hermes-User-Label": who},
        )
        if text is None:
            return web.json_response(
                {"error": "transcription failed", "detail": (error or "")[:300]}, status=502,
            )
        if text:
            text = await _cleanup_dictation(session, text, who, who)
        return web.json_response({"text": text, "provider": provider})


# Whisper-family models are known to hallucinate short stock phrases on
# silence or pure noise -- an artifact of training data that included a
# lot of YouTube captions. Reproduced live: a silent clip returned the
# raw transcript "Thank you." (not empty, so the normal empty-text check
# never caught it), which the cleanup webhook then correctly recognised
# as nothing to redraft and replied with ITS OWN commentary -- which this
# endpoint was about to save as the job's instruction verbatim, because
# nothing here has a human reviewing the text before it becomes a job
# (unlike the textarea dictation flow, where a person sees "Thank you."
# in the box and just doesn't submit it). Two checks close that gap:
# the raw transcript against a short denylist of known hallucinations
# before paying for a cleanup call at all, and the cleanup webhook's own
# output against a few of its characteristic "nothing to redraft" phrases
# as a backstop for hallucinations not on the first list.
_SILENCE_HALLUCINATIONS = {
    "thank you", "thanks for watching", "please subscribe",
    "subscribe to my channel", "like and subscribe", "bye", "goodbye",
    "you", "i'm sorry", "okay", "um", "uh", "hmm", "bye bye",
}
_CLEANUP_NOTHING_MARKERS = (
    "no dictation", "nothing to redraft", "no content to redraft",
    "no speech", "empty transcript", "no transcription provided",
    "no audio content",
)


def _looks_like_silence(raw_text: str) -> bool:
    normalized = raw_text.strip().lower().rstrip(".!? ")
    if not normalized:
        return True
    return len(normalized.split()) <= 4 and normalized in _SILENCE_HALLUCINATIONS


def _cleanup_signals_nothing(cleaned_text: str) -> bool:
    lowered = cleaned_text.strip().lower()
    return len(cleaned_text) < 120 and any(m in lowered for m in _CLEANUP_NOTHING_MARKERS)


async def api_create_job_from_dictation(request: web.Request) -> web.Response:
    """Transcribe, clean up, and create a job in ONE request.

    This is what the board's "New job by voice" FAB posts to -- the whole
    point is that the client enqueues the audio and moves on immediately,
    so the entire STT -> cleanup -> create_job chain has to happen
    server-side in a single call rather than as a client-orchestrated
    sequence the UI would otherwise have to wait on step by step.

    idempotency_key (query string -- the body here is multipart audio, not
    JSON) is the client's queue-item id. If a retry fires after an earlier
    attempt actually succeeded server-side but the client never saw the
    response (tab backgrounded/killed mid-request), this returns the SAME
    job instead of creating a duplicate -- create_job() already refuses a
    second insert for a key that exists on a non-archived row.
    """
    audio_bytes, ctype, err = await _read_audio_field(request)
    if err:
        return err
    idempotency_key = (request.query.get("idempotency_key") or "").strip() or None

    who = _who(request)
    async with ClientSession() as session:
        text, provider, error = await _transcribe_bytes(
            session, audio_bytes, ctype,
            {"X-Hermes-User-Id": who, "X-Hermes-User-Label": who},
        )
        if text is None:
            return web.json_response(
                {"error": "transcription failed", "detail": (error or "")[:300]}, status=502,
            )
        if not text.strip() or _looks_like_silence(text):
            return web.json_response(
                {"error": "no speech detected", "raw_transcript": text}, status=422,
            )
        instruction = await _cleanup_dictation(session, text, who, who)
        if _cleanup_signals_nothing(instruction):
            return web.json_response(
                {"error": "no speech detected", "raw_transcript": text}, status=422,
            )

    try:
        job_id = store.create_job(
            instruction=instruction,
            tenant=who,
            origin_platform="web",
            origin_chat_id="",
            origin_thread_id="",
            origin_message_id="",
            idempotency_key=idempotency_key,
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    job = store.get_job(job_id)
    data = _serialize(job or {"id": job_id})
    data["lane"] = LANES.get(data.get("status"), "working")
    logger.info(
        "job %s created from voice-only dictation by %s (idempotency_key=%s)",
        job_id, who, idempotency_key,
    )
    return web.json_response({"ok": True, "job": data, "transcript": instruction}, status=201)


async def api_whoami(request: web.Request) -> web.Response:
    """Tell the shell who is signed in and whether to show the All jobs toggle.

    ``is_admin`` comes from the request identity resolved by middleware, which
    is a strict vault role check. The frontend uses this only for presentation;
    every actual authorization decision is repeated server-side on each API
    route, so hiding/showing the button can never be the security boundary.
    """
    identity = _identity(request)
    return web.json_response({
        "email": _who(request),
        "is_admin": identity.is_admin,
    })


async def health(request: web.Request) -> web.Response:
    return web.json_response({"ok": True})


async def serve_index(request: web.Request) -> web.Response:
    # aiohttp's add_static has no "default file for /" behaviour the way
    # nginx does -- show_index=True just lists the directory. Root (and
    # the PWA's own fallback navigations) need an explicit handler.
    return web.FileResponse(STATIC_DIR / "index.html")


# ---------------------------------------------------------------------------
# app
# ---------------------------------------------------------------------------

def build_app() -> web.Application:
    try:
        store.ensure_schema()
    except Exception:
        logger.exception("jobs board: schema check failed (continuing)")
    app = web.Application(middlewares=[auth_middleware])
    app.router.add_get("/health", health)
    app.router.add_get("/api/whoami", api_whoami)
    app.router.add_get("/api/jobs", api_list_jobs)
    app.router.add_post("/api/jobs", api_create_job)
    app.router.add_post("/api/jobs/from-dictation", api_create_job_from_dictation)
    # Static /owners must be registered before the dynamic {job_id} route or
    # aiohttp would treat "owners" as a job id.
    app.router.add_get("/api/jobs/owners", api_list_owners)
    app.router.add_get("/api/jobs/{job_id}", api_get_job)
    app.router.add_get("/api/jobs/{job_id}/artifact", api_download_artifact)
    app.router.add_post("/api/jobs/{job_id}/answer", api_answer)
    app.router.add_post("/api/jobs/{job_id}/continue", api_continue)
    app.router.add_post("/api/jobs/{job_id}/drop", api_drop)
    app.router.add_post("/api/jobs/{job_id}/tags", api_update_tags)
    app.router.add_post("/api/transcribe", api_transcribe)
    app.router.add_get("/", serve_index)
    app.router.add_get("/index.html", serve_index)
    # show_index=False now that "/" has an explicit handler -- a raw
    # directory listing of every other path is not something to expose.
    app.router.add_static("/", STATIC_DIR, show_index=False, name="static")
    return app


if __name__ == "__main__":
    port = int(os.environ.get("BOARD_PORT", "8900"))
    web.run_app(build_app(), host="0.0.0.0", port=port)
