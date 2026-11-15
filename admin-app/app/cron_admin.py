"""Cron Jobs control centre for the admin-app (admin.ahfl.in/cron-admin).

Lists every cron job from the Hermes gateway's REST API (GET /api/jobs on
hermes-hermes-1:8642), enriches each job with owner identity (name/email/
telegram, via the vault socket already wired up for the rest of admin-app)
and a handful of computed display fields, and serves it with server-side
search / filter / sort / cursor paging for infinite scroll.

Writes (pause/resume/run/delete/edit/bulk) forward to the gateway's cron
REST API with the signed-in admin's email as X-Admin-Actor -- the gateway
itself appends the audit log entry (gateway/platforms/api_server.py,
cron/admin_audit.jsonl) and routes every mutation through cron/jobs.py's
in-process lock. This page never writes jobs.json directly.

Auth: no extra check here -- relies on the same AuthMiddleware/SSO that
protects the rest of admin.ahfl.in (see auth.py / ADMIN_EMAILS).

Reachability: hermes-apps-1 and hermes-hermes-1 are both on the
`hermes_default` docker network, so the container name resolves directly
(verified 2026-11-03).
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse

from .jinja_env import env
from .vault_client import VaultClient

router = APIRouter()
logger = logging.getLogger("admin-app.cron_admin")

GATEWAY_URL = "http://hermes-hermes-1:8642"
GATEWAY_API_KEY = os.environ.get("HERMES_API_SERVER_KEY", "")
HERMES_CONTAINER = "hermes-hermes-1"
IST = ZoneInfo("Asia/Kolkata")
BULK_MAX_IDS = 200

# ---------------------------------------------------------------------------
# Jobs cache: 5s TTL, matches the "cheap enough" guidance in the plan for a
# few hundred jobs. Avoids hammering the gateway on every keystroke of the
# search box / every infinite-scroll page. Any write invalidates it.
# ---------------------------------------------------------------------------
_jobs_cache: dict = {"at": 0.0, "jobs": []}
_jobs_lock = asyncio.Lock()
JOBS_TTL_S = 5.0

# Owner identity cache: 5 min TTL per owner id.
_owner_cache: dict[str, tuple[float, dict | None]] = {}
_owner_lock = asyncio.Lock()
OWNER_TTL_S = 300.0

_vault = VaultClient()


def _invalidate_jobs_cache() -> None:
    _jobs_cache["at"] = 0.0


async def _fetch_jobs() -> list[dict]:
    async with _jobs_lock:
        now = time.monotonic()
        if now - _jobs_cache["at"] < JOBS_TTL_S and _jobs_cache["jobs"]:
            return _jobs_cache["jobs"]
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{GATEWAY_URL}/api/jobs",
                    params={"include_disabled": "true"},
                    headers={"Authorization": f"Bearer {GATEWAY_API_KEY}"},
                )
            resp.raise_for_status()
            jobs = resp.json().get("jobs", [])
        except Exception as exc:  # noqa: BLE001
            logger.error("cron-admin: gateway /api/jobs fetch failed: %s", exc)
            # Serve the last good cache (even if stale) rather than an
            # empty page, if we have one.
            if _jobs_cache["jobs"]:
                return _jobs_cache["jobs"]
            raise
        _jobs_cache["at"] = now
        _jobs_cache["jobs"] = jobs
        return jobs


async def _owner_identity(owner_id: str | None) -> dict | None:
    if not owner_id:
        return None
    now = time.monotonic()
    cached = _owner_cache.get(owner_id)
    if cached and now - cached[0] < OWNER_TTL_S:
        return cached[1]
    async with _owner_lock:
        cached = _owner_cache.get(owner_id)
        if cached and now - cached[0] < OWNER_TTL_S:
            return cached[1]
        try:
            identity = await asyncio.to_thread(_vault.get_identity, owner_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("cron-admin: vault lookup failed for %s: %s", owner_id, exc)
            identity = None
        _owner_cache[owner_id] = (now, identity)
        return identity


def _admin_email(request: Request) -> str:
    user = request.session.get("user") or {}
    return (user.get("email") or "").strip() or "unknown-admin"


async def _gateway_request(
    method: str, path: str, *, actor: str, json_body: dict | None = None, params: dict | None = None,
) -> tuple[int, dict]:
    """Forward a write to the gateway's cron REST API with the admin's
    email as X-Admin-Actor (the gateway appends the audit log entry and
    routes the mutation through cron/jobs.py's in-process lock -- this
    page never writes jobs.json directly). Returns (status_code, body).
    """
    headers = {
        "Authorization": f"Bearer {GATEWAY_API_KEY}",
        "X-Admin-Actor": actor,
    }
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.request(method, f"{GATEWAY_URL}{path}", headers=headers, json=json_body, params=params)
        try:
            body = resp.json()
        except Exception:  # noqa: BLE001
            body = {"error": resp.text or f"HTTP {resp.status_code}"}
        if resp.status_code < 400:
            _invalidate_jobs_cache()
        return resp.status_code, body
    except Exception as exc:  # noqa: BLE001
        logger.error("cron-admin: gateway request %s %s failed: %s", method, path, exc)
        return 502, {"error": f"gateway unreachable: {exc}"}


async def _docker_exec_hermes(cmd: str, *, timeout: float = 15.0) -> str:
    """Run a READ-ONLY shell command inside hermes-hermes-1 as the hermes
    user, for the one thing the gateway's own REST API doesn't expose yet:
    reading admin_audit.jsonl (hermes-apps-1 has no /data/hermes mount, but
    does have the Docker socket -- same pattern as gbrain_health.py).
    """
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", "-u", "hermes", HERMES_CONTAINER, "sh", "-c", cmd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return ""
    return out.decode(errors="replace")


async def _audit_entries_for_job(job_id: str, limit: int = 50) -> list[dict]:
    raw = await _docker_exec_hermes(f"grep -F '\"job_id\": \"{job_id}\"' /data/hermes/cron/admin_audit.jsonl 2>/dev/null | tail -n {limit}")
    entries = []
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    entries.sort(key=lambda e: e.get("ts", ""), reverse=True)
    return entries


def _parse_iso(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _relative(dt: datetime | None, *, now: datetime) -> str | None:
    if dt is None:
        return None
    delta = (dt - now).total_seconds()
    past = delta < 0
    delta = abs(delta)
    if delta < 60:
        unit = f"{int(delta)}s"
    elif delta < 3600:
        unit = f"{int(delta // 60)}m"
    elif delta < 86400:
        unit = f"{int(delta // 3600)}h"
    else:
        unit = f"{int(delta // 86400)}d"
    return f"{unit} ago" if past else f"in {unit}"


def _ist(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    return dt.astimezone(IST).strftime("%Y-%m-%d %H:%M IST")


def _display_name(job: dict) -> tuple[str, bool]:
    name = (job.get("name") or "").strip()
    if name:
        return name, False
    fallback = (job.get("prompt") or job.get("script") or job.get("id") or "").strip()
    return (fallback[:50] or job.get("id", "?")), True


def _job_type(job: dict) -> str:
    return "script" if job.get("script") else "agent"


def _status(job: dict) -> str:
    if not job.get("enabled", True):
        return "paused"
    if job.get("last_status") == "error" or job.get("last_delivery_error"):
        return "failing"
    state = job.get("state")
    if state == "completed":
        return "completed"
    repeat = job.get("repeat") or {}
    times = repeat.get("times")
    completed = repeat.get("completed") or 0
    if times is not None and completed >= times:
        return "completed"
    if not job.get("last_run_at"):
        return "never_run"
    return "active"


def _delivery_preview(job: dict, owner: dict | None) -> dict:
    """Preview of where a result goes, mirroring the gateway's own B1
    owner-based resolution (cron/scheduler.py::_resolve_owner_delivery):
    owner's Telegram, else owner's primary email, else unresolved. "local"
    jobs are shown separately. Computed here only for display -- the
    gateway is the actual source of truth at delivery time.
    """
    deliver = job.get("deliver") or "local"
    if deliver == "local":
        return {"kind": "local", "label": "Local (no notification)"}
    if owner:
        telegrams = (owner.get("identities") or {}).get("telegram") or []
        if telegrams:
            return {"kind": "telegram", "label": f"Telegram: {owner.get('name')} ({telegrams[0]})"}
        emails = (owner.get("identities") or {}).get("email") or []
        if emails:
            return {"kind": "email", "label": f"Email: {emails[0]}"}
    return {"kind": "unresolved", "label": "Unresolved — no owner/telegram/email"}


async def _enrich(job: dict, *, now: datetime) -> dict:
    owner_id = job.get("owner")
    owner = await _owner_identity(owner_id)
    name, unnamed = _display_name(job)
    schedule = job.get("schedule") or {}
    next_run = _parse_iso(job.get("next_run_at"))
    last_run = _parse_iso(job.get("last_run_at"))
    repeat = job.get("repeat") or {}
    return {
        **job,
        "display_name": name,
        "unnamed": unnamed,
        "type": _job_type(job),
        "status": _status(job),
        "schedule_kind": schedule.get("kind"),
        "next_run_ist": _ist(next_run),
        "next_run_relative": _relative(next_run, now=now),
        "last_run_ist": _ist(last_run),
        "last_run_relative": _relative(last_run, now=now),
        "runs_completed": repeat.get("completed") or 0,
        "runs_limit": repeat.get("times"),
        "owner_name": (owner or {}).get("name") or owner_id or "(no owner)",
        "owner_email": ((owner or {}).get("identities") or {}).get("email", [None])[0] if owner else None,
        "owner_telegram": ((owner or {}).get("identities") or {}).get("telegram", [None])[0] if owner else None,
        "ownerless": owner_id is None,
        "delivery_preview": _delivery_preview(job, owner),
    }


async def _enriched_jobs() -> list[dict]:
    jobs = await _fetch_jobs()
    now = datetime.now(timezone.utc)
    return await asyncio.gather(*(_enrich(j, now=now) for j in jobs))


def _matches_query(job: dict, q: str) -> bool:
    q = q.lower()
    haystack = " ".join(str(job.get(k) or "") for k in (
        "display_name", "prompt", "script", "id", "owner", "owner_name",
    )).lower()
    return q in haystack


_SORT_KEYS = {
    "name": lambda j: (j.get("display_name") or "").lower(),
    "next_run": lambda j: j.get("next_run_at") or "",
    "last_run": lambda j: j.get("last_run_at") or "",
    "owner": lambda j: (j.get("owner_name") or "").lower(),
    "status": lambda j: j.get("status") or "",
}


def _facet_counts(jobs: list[dict]) -> dict:
    facets: dict[str, dict[str, int]] = {
        "status": {}, "type": {}, "owner": {}, "deliver": {}, "schedule_kind": {}, "label": {},
    }
    for j in jobs:
        facets["status"][j["status"]] = facets["status"].get(j["status"], 0) + 1
        facets["type"][j["type"]] = facets["type"].get(j["type"], 0) + 1
        facets["owner"][j["owner_name"]] = facets["owner"].get(j["owner_name"], 0) + 1
        dk = j["delivery_preview"]["kind"]
        facets["deliver"][dk] = facets["deliver"].get(dk, 0) + 1
        sk = j.get("schedule_kind") or "unknown"
        facets["schedule_kind"][sk] = facets["schedule_kind"].get(sk, 0) + 1
        for lbl in (j.get("labels") or []):
            facets["label"][lbl] = facets["label"].get(lbl, 0) + 1
    return facets


@router.get("/cron-admin")
async def cron_admin_page(request: Request):
    return HTMLResponse(env.get_template("cron_admin.html").render(
        user=request.session.get("user"),
    ))


@router.get("/cron-admin/api/jobs")
async def cron_admin_api_jobs(
    request: Request,
    q: str = "",
    status: str = "",
    owner: str = "",
    deliver: str = "",
    kind: str = "",
    label: str = "",
    sort: str = "next_run",
    dir: str = "asc",
    cursor: int = 0,
    limit: int = 50,
):
    try:
        jobs = await _enriched_jobs()
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"error": f"gateway unavailable: {exc}"}, status_code=502)

    facets_all = _facet_counts(jobs)

    if q:
        jobs = [j for j in jobs if _matches_query(j, q)]
    if status:
        jobs = [j for j in jobs if j["status"] == status]
    if owner:
        jobs = [j for j in jobs if j["owner_name"] == owner]
    if deliver:
        jobs = [j for j in jobs if j["delivery_preview"]["kind"] == deliver]
    if kind:
        jobs = [j for j in jobs if j.get("schedule_kind") == kind]
    if label:
        jobs = [j for j in jobs if label in (j.get("labels") or [])]

    key_fn = _SORT_KEYS.get(sort, _SORT_KEYS["next_run"])
    jobs.sort(key=key_fn, reverse=(dir == "desc"))

    total = len(jobs)
    limit = max(1, min(limit, 200))
    page = jobs[cursor: cursor + limit]
    next_cursor = cursor + limit if cursor + limit < total else None

    return JSONResponse({
        "items": page,
        "next_cursor": next_cursor,
        "total": total,
        "facets": facets_all,
    })


@router.get("/cron-admin/api/jobs/{job_id}")
async def cron_admin_api_job_detail(job_id: str):
    jobs = await _enriched_jobs()
    job = next((j for j in jobs if j.get("id") == job_id), None)
    if not job:
        return JSONResponse({"error": "Job not found"}, status_code=404)

    runs: list[dict] = []
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{GATEWAY_URL}/api/jobs/{job_id}/runs",
                params={"limit": 20},
                headers={"Authorization": f"Bearer {GATEWAY_API_KEY}"},
            )
        if resp.status_code == 200:
            runs = resp.json().get("runs", [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("cron-admin: runs fetch failed for %s: %s", job_id, exc)

    audit = await _audit_entries_for_job(job_id)

    return JSONResponse({"job": job, "runs": runs, "audit": audit})


@router.get("/cron-admin/api/schedule-preview")
async def cron_admin_schedule_preview(schedule: str = ""):
    if not schedule.strip():
        return JSONResponse({"valid": False, "error": "schedule is required"}, status_code=400)
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{GATEWAY_URL}/api/jobs/schedule-preview",
                params={"schedule": schedule},
                headers={"Authorization": f"Bearer {GATEWAY_API_KEY}"},
            )
        return JSONResponse(resp.json(), status_code=resp.status_code)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"valid": False, "error": f"gateway unreachable: {exc}"}, status_code=502)


@router.get("/cron-admin/api/jobs/{job_id}/script-preview")
async def cron_admin_script_preview(job_id: str):
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(
                f"{GATEWAY_URL}/api/jobs/{job_id}/script-preview",
                headers={"Authorization": f"Bearer {GATEWAY_API_KEY}"},
            )
        return JSONResponse(resp.json(), status_code=resp.status_code)
    except Exception as exc:  # noqa: BLE001
        return JSONResponse({"error": f"gateway unreachable: {exc}"}, status_code=502)


@router.patch("/cron-admin/api/jobs/{job_id}")
async def cron_admin_update_job(job_id: str, request: Request):
    body = await request.json()
    status_code, resp_body = await _gateway_request(
        "PATCH", f"/api/jobs/{job_id}", actor=_admin_email(request), json_body=body,
    )
    return JSONResponse(resp_body, status_code=status_code)


@router.delete("/cron-admin/api/jobs/{job_id}")
async def cron_admin_delete_job(job_id: str, request: Request):
    status_code, resp_body = await _gateway_request(
        "DELETE", f"/api/jobs/{job_id}", actor=_admin_email(request),
    )
    return JSONResponse(resp_body, status_code=status_code)


@router.post("/cron-admin/api/jobs/{job_id}/pause")
async def cron_admin_pause_job(job_id: str, request: Request):
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = {}
    status_code, resp_body = await _gateway_request(
        "POST", f"/api/jobs/{job_id}/pause", actor=_admin_email(request), json_body=body,
    )
    return JSONResponse(resp_body, status_code=status_code)


@router.post("/cron-admin/api/jobs/{job_id}/resume")
async def cron_admin_resume_job(job_id: str, request: Request):
    status_code, resp_body = await _gateway_request(
        "POST", f"/api/jobs/{job_id}/resume", actor=_admin_email(request),
    )
    return JSONResponse(resp_body, status_code=status_code)


@router.post("/cron-admin/api/jobs/{job_id}/run")
async def cron_admin_run_job(job_id: str, request: Request):
    status_code, resp_body = await _gateway_request(
        "POST", f"/api/jobs/{job_id}/run", actor=_admin_email(request),
    )
    return JSONResponse(resp_body, status_code=status_code)


@router.post("/cron-admin/api/jobs/bulk")
async def cron_admin_bulk(request: Request):
    """Bulk pause / resume / add_label / remove_label / set_owner.

    Capped at BULK_MAX_IDS ids; returns per-id results so a partial
    failure (e.g. one unresolvable new owner) doesn't hide successes.
    """
    body = await request.json()
    ids = list(dict.fromkeys(body.get("ids") or []))[:BULK_MAX_IDS]
    action = (body.get("action") or "").strip()
    actor = _admin_email(request)
    if not ids:
        return JSONResponse({"error": "ids is required"}, status_code=400)
    if action not in {"pause", "resume", "add_label", "remove_label", "set_owner"}:
        return JSONResponse({"error": f"Unknown bulk action {action!r}"}, status_code=400)

    jobs_by_id = {}
    if action in {"add_label", "remove_label"}:
        jobs_by_id = {j["id"]: j for j in await _enriched_jobs()}

    results = {}
    for job_id in ids:
        try:
            if action == "pause":
                code, resp = await _gateway_request("POST", f"/api/jobs/{job_id}/pause", actor=actor, json_body={"reason": body.get("reason")})
            elif action == "resume":
                code, resp = await _gateway_request("POST", f"/api/jobs/{job_id}/resume", actor=actor)
            elif action == "set_owner":
                new_owner = (body.get("owner") or "").strip()
                code, resp = await _gateway_request("PATCH", f"/api/jobs/{job_id}", actor=actor, json_body={"owner": new_owner})
            else:  # add_label / remove_label
                label = (body.get("label") or "").strip().lower()
                current = list((jobs_by_id.get(job_id) or {}).get("labels") or [])
                if action == "add_label" and label and label not in current:
                    current.append(label)
                elif action == "remove_label" and label in current:
                    current = [l for l in current if l != label]
                code, resp = await _gateway_request("PATCH", f"/api/jobs/{job_id}", actor=actor, json_body={"labels": current})
            results[job_id] = {"ok": code < 400, "status": code, "body": resp}
        except Exception as exc:  # noqa: BLE001
            results[job_id] = {"ok": False, "status": 500, "body": {"error": str(exc)}}

    _invalidate_jobs_cache()
    ok_count = sum(1 for r in results.values() if r["ok"])
    return JSONResponse({"results": results, "ok_count": ok_count, "total": len(ids)})
