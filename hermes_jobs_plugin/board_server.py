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
from typing import Any, Dict

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


async def api_create_job(request: web.Request) -> web.Response:
    """Create a queued job from the board (typed or dictated instruction).

    The gateway's existing job runner claims it from kanban.db exactly as it
    does a Telegram ``/job`` -- this endpoint only inserts the row, so job
    creation and execution keep one code path. Origin is ``web`` with no chat
    id, which means delivery.py deliberately skips chat notifications and the
    result is read from this board.
    """
    body = await request.json()
    instruction = (body.get("instruction") or "").strip()
    title = (body.get("title") or "").strip() or None
    if not instruction:
        return web.json_response({"error": "instruction is required"}, status=400)
    who = _who(request)
    try:
        job_id = store.create_job(
            instruction=instruction,
            title=title,
            tenant=who,
            origin_platform="web",
            origin_chat_id="",
            origin_thread_id="",
            origin_message_id="",
        )
    except ValueError as exc:
        return web.json_response({"error": str(exc)}, status=400)
    job = store.get_job(job_id)
    data = _serialize(job or {"id": job_id})
    data["lane"] = LANES.get(data.get("status"), "working")
    logger.info("job %s created from board by %s", job_id, who)
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
    return web.json_response(data)


async def api_answer(request: web.Request) -> web.Response:
    job_id = request.match_info["job_id"]
    body = await request.json()
    text = (body.get("text") or "").strip()
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
    logger.info("job %s answered by %s", job_id, _who(request))
    return web.json_response({"ok": True})


async def api_continue(request: web.Request) -> web.Response:
    job_id = request.match_info["job_id"]
    body = await request.json() if request.can_read_body else {}
    extra = (body.get("extra") or "").strip()
    ok = store.continue_job(job_id, extra_input=extra)
    if not ok:
        job = store.get_job(job_id)
        return web.json_response(
            {"error": "job is not in the failed lane",
             "status": (job or {}).get("status")},
            status=409,
        )
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
