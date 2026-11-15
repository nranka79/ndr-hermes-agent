"""Gbrain health dashboard for the admin-app (admin.ahfl.in/gbrain-health).

Each DRAAS user has a per-user PGLite brain at
/data/hermes/users/<slug>/.gbrain-writable/.gbrain/, and (for auto-provisioned
users) two cron jobs in the hermes gateway's cron store:
`gbrain-ingest-daily-<slug>` and `Run gbrain dream for <name> (...)`.

This container (hermes-apps) does not mount /data/hermes and gbrain itself only
exists inside hermes-hermes-1, so every read below goes through
`docker exec -u hermes hermes-hermes-1 ...`. The Docker CLI + socket are
mounted into this container for exactly this purpose.

Every command below is READ-ONLY:
  - `cat jobs.json` (cron schedule/last-run/last-status)
  - `gbrain doctor --json` (read-only diagnostic)
  - `cat config.json` + `.gbrain-provisioning.json`

`-u hermes` is used throughout so nothing here can leave root-owned files
behind under /data/hermes/**.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .gbrain_provision import read_status, start_provisioning
from .jinja_env import env

router = APIRouter()
logger = logging.getLogger("admin-app.gbrain_health")

HERMES_CONTAINER = "hermes-hermes-1"
HERMES_UID_FLAG = "hermes"
JOBS_JSON_PATH = "/data/hermes/cron/jobs.json"
GBRAIN_BIN = "/data/hermes/home/.local/bin/gbrain"
DOCTOR_TIMEOUT_S = 30
EXEC_TIMEOUT_S = 40

DOCTOR_MARKER = "@@@DOCTOR@@@"
CONFIG_MARKER = "@@@CONFIG@@@"
STATUS_MARKER = "@@@STATUS@@@"

_SLUG_RE = re.compile(r"/data/hermes/users/([A-Za-z0-9_.\-]+)/")
_SAFE_SLUG_RE = re.compile(r"^[A-Za-z0-9_.\-]+$")
_DREAM_NAME_RE = re.compile(r"gbrain dream for (.+?)\s*\(")
_DREAM_PREFIX = "Run gbrain dream for "
_INGEST_PREFIX = "gbrain-ingest-daily-"


async def _docker_exec(cmd: str, *, timeout: float = EXEC_TIMEOUT_S) -> tuple[int, str]:
    """Run `cmd` inside hermes-hermes-1 as the hermes user. Read-only use only."""
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", "-u", HERMES_UID_FLAG, HERMES_CONTAINER, "sh", "-c", cmd,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return 124, "(timed out)"
    return proc.returncode or 0, out.decode(errors="replace")


def _extract_json_object(text: str) -> dict | None:
    """Pull the first {...} JSON object out of mixed CLI output (banners, etc)."""
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


async def _fetch_cron_jobs() -> list[dict]:
    rc, out = await _docker_exec(f"cat {JOBS_JSON_PATH}")
    if rc != 0:
        logger.error("could not read gbrain cron jobs.json (exit %s): %s", rc, out[-500:])
        return []
    data = _extract_json_object(out) or {}
    jobs = data.get("jobs", data if isinstance(data, list) else [])
    if isinstance(jobs, dict):
        jobs = list(jobs.values())
    return [job for job in jobs if isinstance(job, dict) and _is_gbrain_job(job)]


def _job_label(job: dict) -> str:
    # Jobs created before the cron normaliser use "title"; newer create_job()
    # records use "name". Accept both.
    return str(job.get("name") or job.get("title") or "")


def _is_gbrain_job(job: dict) -> bool:
    label = _job_label(job)
    prompt_head = str(job.get("prompt") or "")[:300]
    return (
        label.startswith(_DREAM_PREFIX)
        or label.startswith("gbrain-dream-")
        or label.startswith(_INGEST_PREFIX)
        or prompt_head.startswith("Run gbrain dream for ")
        or prompt_head.startswith("Daily gbrain ingestion")
    )


async def _list_brains() -> set[str]:
    """Slugs that have a brain-copy directory or a provisioning status file."""
    cmd = (
        "find /data/hermes/users -maxdepth 2 "
        "\\( -name brain-copy -type d -o -name .gbrain-provisioning.json -type f \\) "
        "-printf '%h\\n' 2>/dev/null | xargs -r -n1 basename"
    )
    rc, out = await _docker_exec(cmd, timeout=20)
    if rc != 0:
        logger.error("could not list gbrain user dirs: %s", out[-400:])
        return set()
    return {line.strip() for line in out.splitlines() if _SAFE_SLUG_RE.fullmatch(line.strip())}


def _job_slug(job: dict) -> str | None:
    match = _SLUG_RE.search(str(job.get("prompt", "")))
    return match.group(1) if match else None


def _dream_jobs(jobs: list[dict]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for job in jobs:
        label = _job_label(job)
        if not (label.startswith(_DREAM_PREFIX) or label.startswith("gbrain-dream-")):
            continue
        slug = _job_slug(job)
        if slug and slug not in found:
            found[slug] = job
    return found


def _ingest_jobs(jobs: list[dict]) -> dict[str, dict]:
    found: dict[str, dict] = {}
    for job in jobs:
        label = _job_label(job)
        if not label.startswith(_INGEST_PREFIX):
            continue
        slug = label[len(_INGEST_PREFIX):]
        if slug:
            found[slug] = job
    return found


async def _fetch_live_health(slug: str) -> dict:
    """Run gbrain doctor + read config.json + provisioning status for one user."""
    home = f"/data/hermes/users/{slug}/.gbrain-writable"
    status_path = f"/data/hermes/users/{slug}/.gbrain-provisioning.json"
    cmd = (
        f'export HOME="{home}"; '
        f'echo "{DOCTOR_MARKER}"; '
        f'timeout {DOCTOR_TIMEOUT_S} {GBRAIN_BIN} doctor --json 2>&1; '
        f'echo "{CONFIG_MARKER}"; '
        f'cat "$HOME/.gbrain/config.json" 2>&1; '
        f'echo "{STATUS_MARKER}"; '
        f'cat "{status_path}" 2>/dev/null'
    )
    rc, out = await _docker_exec(cmd)
    result: dict = {
        "doctor_status": None,
        "health_score": None,
        "brain_score": None,
        "brain_score_detail": None,
        "brain_checks_score": None,
        "top_issues": [],
        "engine": None,
        "embedding_model": None,
        "provision_status": None,
        "error": None,
    }
    if DOCTOR_MARKER not in out:
        result["error"] = f"exec failed (exit {rc}): {out[-300:].strip()}"
        return result

    doctor_section, _, rest = out.partition(DOCTOR_MARKER)[2].partition(CONFIG_MARKER)
    config_section, _, status_section = rest.partition(STATUS_MARKER)

    doctor_json = _extract_json_object(doctor_section)
    if doctor_json:
        result["doctor_status"] = doctor_json.get("status")
        result["health_score"] = doctor_json.get("health_score")
        result["brain_checks_score"] = doctor_json.get("brain_checks_score")
        result["engine"] = doctor_json.get("engine")
        for check in doctor_json.get("checks") or []:
            if check.get("name") == "brain_score":
                message = check.get("message") or ""
                result["brain_score_detail"] = message
                match = re.search(r"Brain score\s+(\d+)/100", message)
                if match:
                    result["brain_score"] = int(match.group(1))
                break
        issues = doctor_json.get("top_issues") or []
        result["top_issues"] = [
            {"name": i.get("name"), "status": i.get("status"), "fix": i.get("fix")}
            for i in issues[:4]
        ]
    else:
        result["error"] = f"doctor produced no JSON: {doctor_section[-300:].strip()}"

    config_json = _extract_json_object(config_section)
    if config_json:
        result["embedding_model"] = config_json.get("embedding_model") or (
            "disabled (--no-embedding)" if config_json.get("embedding_disabled") else None
        )

    status_json = _extract_json_object(status_section)
    if status_json:
        result["provision_status"] = status_json

    return result


def _badge_class(status: str | None) -> str:
    if status in ("healthy", "ok"):
        return "bg-emerald-50 text-emerald-700 border-emerald-200"
    if status in ("unhealthy", "fail", "failed", "error"):
        return "bg-red-50 text-red-700 border-red-200"
    if status in ("partial", "warn", "degraded", "warnings"):
        return "bg-amber-50 text-amber-700 border-amber-200"
    return "bg-gray-50 text-gray-500 border-gray-200"


def _provision_badge_class(state: str | None) -> str:
    if state == "provisioned":
        return "bg-emerald-50 text-emerald-700 border-emerald-200"
    if state in ("failed", "missing", "not provisioned"):
        return "bg-red-50 text-red-700 border-red-200"
    if state in ("in_progress", "starting"):
        return "bg-amber-50 text-amber-700 border-amber-200"
    return "bg-gray-50 text-gray-500 border-gray-200"


def _score_class(score: int | None) -> str:
    if score is None:
        return "text-gray-400"
    if score >= 70:
        return "text-emerald-600"
    if score >= 40:
        return "text-amber-600"
    return "text-red-600"


@router.get("/gbrain-health")
async def gbrain_health_page(request: Request):
    jobs, slugs = await asyncio.gather(_fetch_cron_jobs(), _list_brains())

    dream_by_slug = _dream_jobs(jobs)
    ingest_by_slug = _ingest_jobs(jobs)
    all_slugs = set(slugs) | set(dream_by_slug) | set(ingest_by_slug)

    live_results = await asyncio.gather(
        *[_fetch_live_health(slug) for slug in sorted(all_slugs)],
        return_exceptions=True,
    )
    live_by_slug: dict[str, dict] = {}
    for slug, res in zip(sorted(all_slugs), live_results):
        if isinstance(res, Exception):
            logger.exception("gbrain doctor check failed for %s", slug)
            res = {
                "doctor_status": None, "health_score": None, "top_issues": [],
                "engine": None, "embedding_model": None, "provision_status": None,
                "error": str(res),
            }
        live_by_slug[slug] = res

    rows = []
    for slug in sorted(all_slugs):
        dream = dream_by_slug.get(slug)
        ingest = ingest_by_slug.get(slug)
        live = live_by_slug.get(slug, {})
        provision = live.get("provision_status") or {}
        name = provision.get("name")
        if not name and dream:
            match = _DREAM_NAME_RE.search(str(dream.get("prompt") or ""))
            name = match.group(1).strip() if match else None

        if provision:
            provision_state = provision.get("state") or "unknown"
        elif dream:
            provision_state = "legacy (pre-provisioner)"
        else:
            provision_state = "not provisioned"

        schedule = (dream or ingest or {}).get("schedule") or {}
        rows.append({
            "slug": slug,
            "name": name or slug,
            "schedule": schedule.get("display"),
            "last_run_at": (dream or {}).get("last_run_at"),
            "next_run_at": (dream or {}).get("next_run_at"),
            "last_status": (dream or {}).get("last_status"),
            "last_error": (dream or {}).get("last_error"),
            "enabled": (dream or {}).get("enabled", True),
            "has_dream_job": bool(dream),
            "has_ingest_job": bool(ingest),
            "provision_state": provision_state,
            "provision_step": provision.get("step"),
            "provision_error": provision.get("error"),
            "provision_updated_at": provision.get("updated_at"),
            "live": live,
            "badge_class": _badge_class(live.get("doctor_status")),
            "provision_badge_class": _provision_badge_class(provision_state),
            "score_class": _score_class(live.get("health_score")),
            "brain_score_class": _score_class(live.get("brain_score")),
        })

    rows.sort(key=lambda r: (r["live"].get("brain_score") is None, r["live"].get("brain_score") or 0))

    return HTMLResponse(env.get_template("gbrain_health.html").render(
        user=request.session.get("user"),
        rows=rows,
        fetch_failed=not jobs,
    ))


def _identity_for_slug(vault, slug: str) -> dict:
    """Best-effort Vault lookup so a retry for a never-provisioned user still
    gets a resolvable cron owner (email)."""
    try:
        for user in vault.list_users():
            identity = vault.get_identity(user.get("user_id"))
            if not identity:
                continue
            aliases = identity.get("identities", {}) or {}
            gbrain_home = str(identity.get("gbrain_home") or "")
            draas_ids = aliases.get("draas_user_id", []) or []
            emails = aliases.get("email", []) or []
            email = emails[0] if emails else ""
            matches = (
                gbrain_home.rstrip("/").endswith("/" + slug)
                or slug in draas_ids
                or (email and email.split("@")[0] == slug)
            )
            if matches:
                telegrams = aliases.get("telegram", []) or []
                return {
                    "email": email,
                    "name": identity.get("name") or "",
                    "telegram": telegrams[0] if telegrams else "",
                }
    except Exception:  # noqa: BLE001
        logger.warning("vault lookup failed for retry slug %s", slug, exc_info=True)
    return {}


@router.post("/gbrain-health/provision/{slug}")
async def retry_provisioning(request: Request, slug: str):
    if not _SAFE_SLUG_RE.fullmatch(slug):
        return HTMLResponse("invalid slug", status_code=400)
    status = await read_status(slug)
    if not status:
        status = _identity_for_slug(request.app.state.vault, slug)
    status = status or {}
    start_provisioning(
        slug=slug,
        email=status.get("email") or "",
        name=status.get("name") or "",
        telegram_id=status.get("telegram") or "",
    )
    return RedirectResponse(url="/gbrain-health", status_code=303)
