"""Standalone HTTP backend for the jobs.ahfl.in PWA.

Runs as its OWN container (reusing the ``hermes-hermes:latest`` image,
which already has every dependency ``hermes_cli.kanban_db`` and this
plugin need -- it's the exact same import path the gateway process
itself uses). It never touches ``hermes-hermes-1`` or ``hermes-apps-1``.

Auth model: this process trusts the ``X-Forwarded-Email`` header and
assumes nginx + oauth2-proxy sit in front of it and that NOTHING else can
reach it -- it binds 127.0.0.1 only, inside a container with no public
port. The real access boundary is oauth2-proxy's allowed-email list, not
this code. Within that boundary, every authenticated person sees EVERY
job (admin-sees-all, D6) -- this is a personal/small-team control panel,
not a multi-tenant product, so per-tenant filtering would just hide your
own Telegram-created jobs from your own browser session (they're scoped
by platform user id, e.g. a Telegram numeric id, not by email -- there
is no shared identity between surfaces). ``_DISPLAY_NAMES`` below is
cosmetic labelling only, never an access check.

Run: python3 board_server.py
Env: BOARD_PORT (default 8900), API_SERVER_KEY (to call /v1/runs if ever
     needed), HERMES_API_BASE (default http://hermes:8642 -- the
     in-network container name, NOT 127.0.0.1, since this runs in a
     different container than the gateway).
"""

from __future__ import annotations

import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, "/data/hermes/plugins")
sys.path.insert(0, "/opt/hermes")

from aiohttp import web, ClientSession, FormData  # noqa: E402

from hermes_jobs import store  # noqa: E402

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
    platform = job.get("origin_platform") or "cli"
    if platform == "web":
        return "jobs.ahfl.in"
    chat_id = job.get("origin_chat_id") or job.get("tenant") or ""
    label = _DISPLAY_NAMES.get((platform, str(chat_id)))
    if label:
        return label
    return "%s%s" % (platform, (" " + chat_id) if chat_id else "")


async def _cleanup_dictation(session: ClientSession, raw_text: str) -> str:
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
            json={"transcription": raw_text},
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
        "session_id": job.get("session_id"),
        "parent_job_id": job.get("parent_job_id"),
    }


def _who(request: web.Request) -> str:
    return request.headers.get(AUTH_HEADER, "unknown")


async def require_auth(request: web.Request, handler):
    # Defense in depth only -- see module docstring. The real gate is
    # oauth2-proxy; this just refuses to silently treat a misconfigured
    # proxy pass-through as "someone logged in".
    if not request.headers.get(AUTH_HEADER):
        if os.environ.get("BOARD_ALLOW_NO_AUTH") == "1":
            return await handler(request)
        return web.json_response({"error": "no identity header from proxy"}, status=401)
    return await handler(request)


@web.middleware
async def auth_middleware(request: web.Request, handler):
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


async def api_list_jobs(request: web.Request) -> web.Response:
    rows = store.list_jobs(limit=500)
    jobs = [_serialize(r) for r in rows]
    for j in jobs:
        j["lane"] = LANES.get(j["status"], "other")
    counts: Dict[str, int] = {}
    for j in jobs:
        counts[j["lane"]] = counts.get(j["lane"], 0) + 1
    return web.json_response({"jobs": jobs, "counts": counts})


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
    if not instruction:
        return web.json_response({"error": "instruction is required"}, status=400)

    parent = store.get_job(parent_job_id) if parent_job_id else None
    if parent_job_id and not parent:
        return web.json_response({"error": "parent job not found"}, status=404)

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
    job = store.get_job(request.match_info["job_id"])
    if not job:
        return web.json_response({"error": "not found"}, status=404)
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
    job = store.get_job(job_id)
    if not job:
        return web.json_response({"error": "not found"}, status=404)
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
    job_id = request.match_info["job_id"]
    fields, files = await _parse_body_and_files(request)
    text = (fields.get("text") or "").strip()
    if not text:
        return web.json_response({"error": "text is required"}, status=400)
    ok = store.answer_job(job_id, text)
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
    job_id = request.match_info["job_id"]
    fields, files = await _parse_body_and_files(request)
    extra = (fields.get("extra") or "").strip()
    ok = store.continue_job(job_id, extra_input=extra)
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
    job_id = request.match_info["job_id"]
    body = await request.json() if request.can_read_body else {}
    reason = (body.get("reason") or "").strip()
    who = _who(request)
    ok = store.drop_job(job_id, by=who, reason=reason)
    if not ok:
        return web.json_response({"error": "could not drop"}, status=409)
    logger.info("job %s dropped by %s", job_id, who)
    return web.json_response({"ok": True})


async def api_transcribe(request: web.Request) -> web.Response:
    """Proxy an audio blob to the shared STT chain and return text.

    Primary: the AI Model Gateway's OpenAI-compatible
    ``/v1/audio/transcriptions`` (same Groq-whisper -> AssemblyAI pools that
    voice.ahfl.in and chat.ahfl.in dictation use). Fallbacks: the voice-app
    STT bridge, then the free-whisper gateway's OpenAI-compatible endpoint.
    The legacy ``/transcribe`` route is not used: it expects a raw audio body,
    while this PWA sends multipart.
    """
    reader = await request.multipart()
    field = await reader.next()
    if field is None or field.name not in ("audio", "file"):
        return web.json_response({"error": "expected multipart field 'audio'"}, status=400)
    audio_bytes = await field.read(decode=False)
    if not audio_bytes:
        return web.json_response({"error": "empty audio upload"}, status=400)
    if len(audio_bytes) > 25 * 1024 * 1024:
        return web.json_response({"error": "audio too large"}, status=413)

    ctype = field.headers.get("Content-Type") or "audio/webm"
    urls = [STT_URL] + [u for u in STT_FALLBACK_URLS if u and u != STT_URL]
    last_error = ""
    async with ClientSession() as session:
        for url in urls:
            form = FormData()
            form.add_field(
                "file", audio_bytes, filename="audio.webm", content_type=ctype,
            )
            try:
                async with session.post(url, data=form, timeout=230) as resp:
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
                        logger.info(
                            "transcribed %d bytes via %s", len(audio_bytes), url,
                        )
                        text = await _cleanup_dictation(session, text)
                    return web.json_response({
                        "text": text or "",
                        "provider": (result or {}).get("provider") if isinstance(result, dict) else None,
                    })
            except Exception as exc:
                last_error = str(exc)
                logger.warning("transcribe %s unreachable: %s", url, exc)

    logger.error("all transcription backends failed: %s", last_error)
    return web.json_response(
        {"error": "transcription failed", "detail": last_error[:300]}, status=502,
    )


async def api_whoami(request: web.Request) -> web.Response:
    return web.json_response({"email": _who(request)})


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
    app.router.add_get("/api/jobs/{job_id}", api_get_job)
    app.router.add_get("/api/jobs/{job_id}/artifact", api_download_artifact)
    app.router.add_post("/api/jobs/{job_id}/answer", api_answer)
    app.router.add_post("/api/jobs/{job_id}/continue", api_continue)
    app.router.add_post("/api/jobs/{job_id}/drop", api_drop)
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
