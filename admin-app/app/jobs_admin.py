"""Jobs runner settings for the admin-app (admin.ahfl.in/jobs-admin).

Edits the hermes_jobs plugin's live settings file:

    /opt/hermes/hermes-data/hermes_jobs/settings.json
    (= /data/hermes/hermes_jobs/settings.json inside the Hermes gateway)

The plugin's drain loop re-reads that file every few seconds (see
hermes_jobs/settings.py), so saving here takes effect without restarting
anything.

This container (hermes-apps) does not mount hermes-data, so -- as on
/keys-admin -- every read/write runs in a disposable python:3.12-slim
container launched via the Docker socket, with only the settings
directory bind-mounted and running as the gateway's uid so the file stays
owned by it.

Auth: no extra check here -- relies on the same AuthMiddleware/SSO that
protects the rest of admin.ahfl.in (see auth.py / ADMIN_EMAILS).
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse

from .jinja_env import env

router = APIRouter()
logger = logging.getLogger("admin-app.jobs")

SETTINGS_DIR = "/opt/hermes/hermes-data/hermes_jobs"
SETTINGS_FILE = "settings.json"
HERMES_UID = "10000:10000"
HELPER_IMAGE = "python:3.12-slim"

# Keep in sync with hermes_jobs/settings.py. The plugin clamps to the same
# range itself, so a stale copy here can only make this form stricter.
DEFAULT_MAX_CONCURRENT_JOBS = 2
HARD_MAX_CONCURRENT_JOBS = 8

_lock = asyncio.Lock()

# Reads (and, when NEW is set, merges + atomically writes) the settings
# file, then prints the resulting JSON.
_HELPER = r"""
import json, os
path = "/s/settings.json"
try:
    with open(path) as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        data = {}
except FileNotFoundError:
    data = {}
new = os.environ.get("NEW")
if new:
    data.update(json.loads(new))
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        json.dump(data, fh, indent=2, sort_keys=True)
        fh.write("\n")
    os.replace(tmp, path)
print(json.dumps(data))
"""


async def _run_helper(new: dict | None = None) -> dict:
    cmd = [
        "docker", "run", "--rm", "--network", "none",
        "--user", HERMES_UID,
        "-e", "OPCODE=" + base64.b64encode(_HELPER.encode()).decode(),
        "-e", "NEW=" + (json.dumps(new) if new else ""),
        "-v", f"{SETTINGS_DIR}:/s",
        HELPER_IMAGE, "python3", "-c",
        "import base64,os;exec(base64.b64decode(os.environ['OPCODE']).decode())",
    ]
    async with _lock:
        proc = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT,
        )
        out, _ = await proc.communicate()
    text = out.decode(errors="replace").strip()
    if proc.returncode:
        logger.error("jobs settings helper failed exit=%s: %s", proc.returncode, text[-2000:])
        raise RuntimeError(f"settings helper failed (exit {proc.returncode}) — check server logs")
    return json.loads(text.splitlines()[-1])


def _effective(data: dict) -> int:
    try:
        value = int(data.get("max_concurrent_jobs", DEFAULT_MAX_CONCURRENT_JOBS))
    except (TypeError, ValueError):
        value = DEFAULT_MAX_CONCURRENT_JOBS
    return max(1, min(value, HARD_MAX_CONCURRENT_JOBS))


def _render(request: Request, *, data: dict | None, message: str = None,
            error: str = None) -> HTMLResponse:
    return HTMLResponse(env.get_template("jobs_admin.html").render(
        user=request.session.get("user"),
        max_concurrent_jobs=_effective(data or {}),
        is_default="max_concurrent_jobs" not in (data or {}),
        default=DEFAULT_MAX_CONCURRENT_JOBS,
        hard_max=HARD_MAX_CONCURRENT_JOBS,
        settings_path=f"{SETTINGS_DIR}/{SETTINGS_FILE}",
        message=message, error=error,
    ))


@router.get("/jobs-admin")
async def jobs_admin_page(request: Request):
    try:
        data = await _run_helper()
    except Exception as exc:  # noqa: BLE001
        return _render(request, data=None, error=str(exc))
    return _render(request, data=data)


@router.post("/jobs-admin")
async def jobs_admin_save(request: Request, max_concurrent_jobs: int = Form(...)):
    if not 1 <= max_concurrent_jobs <= HARD_MAX_CONCURRENT_JOBS:
        return _render(
            request, data=await _run_helper(),
            error=f"Concurrent jobs must be between 1 and {HARD_MAX_CONCURRENT_JOBS}.",
        )
    try:
        data = await _run_helper({"max_concurrent_jobs": max_concurrent_jobs})
    except Exception as exc:  # noqa: BLE001
        return _render(request, data=None, error=str(exc))
    logger.info(
        "jobs max_concurrent_jobs set to %d by %s",
        max_concurrent_jobs, (request.session.get("user") or {}).get("email"),
    )
    return _render(
        request, data=data,
        message=f"Saved. Up to {max_concurrent_jobs} job(s) will run at once — applies within a few seconds.",
    )
