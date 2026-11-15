"""Launch and observe per-user gbrain auto-provisioning.

The real work happens inside the hermes gateway container (the only place the
gbrain CLI, its Bun runtime, and /data/hermes live). This module just:

  * starts ``/data/hermes/scripts/gbrain_provision.py`` inside hermes-hermes-1
    via ``docker exec``, from a background asyncio task so create_user stays
    fast and cannot time out on a slow gbrain init;
  * reads the JSON status file the provisioner writes back.

The provisioner is idempotent (per-user flock + existence checks), so a retry
after a partial failure is always safe. Failures never roll back the Vault
identity -- the dashboard surfaces "failed" and offers a retry instead.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re

logger = logging.getLogger("admin-app.gbrain_provision")

HERMES_CONTAINER = "hermes-hermes-1"
PROVISION_SCRIPT = "/data/hermes/scripts/gbrain_provision.py"
STATUS_PATH = "/data/hermes/users/{slug}/.gbrain-provisioning.json"
EXEC_TIMEOUT_S = 1800
_AUTO_ENV = "GBRAIN_AUTO_PROVISION"

_SLUG_RE = re.compile(r"^[A-Za-z0-9_.-]+$")

# Keep strong references so tasks are not garbage-collected mid-flight.
_tasks: set[asyncio.Task] = set()


def auto_provision_enabled() -> bool:
    return os.environ.get(_AUTO_ENV, "1").strip().lower() not in ("0", "false", "no", "off")


async def _docker_exec(argv: list[str], timeout: float = 60) -> tuple[int, str]:
    proc = await asyncio.create_subprocess_exec(
        "docker", "exec", "-u", "hermes", HERMES_CONTAINER, *argv,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        return 124, "(timed out)"
    return proc.returncode or 0, out.decode(errors="replace")


async def _provision(slug: str, email: str, name: str, telegram_id: str) -> None:
    argv = [
        "python3", PROVISION_SCRIPT,
        "--slug", slug,
        "--email", email or "",
        "--name", name or "",
    ]
    if telegram_id:
        argv += ["--telegram", str(telegram_id)]
    try:
        rc, out = await _docker_exec(argv, timeout=EXEC_TIMEOUT_S)
        tail = out.strip().splitlines()[-1] if out.strip() else ""
        if rc == 0:
            logger.info("gbrain provisioning finished for %s: %s", slug, tail[-400:])
        else:
            logger.error("gbrain provisioning failed for %s (exit %s): %s", slug, rc, out[-2000:])
    except Exception:  # noqa: BLE001
        logger.exception("gbrain provisioning crashed for %s", slug)


def start_provisioning(slug: str, email: str = "", name: str = "", telegram_id: str = ""):
    """Fire-and-forget provisioning for a newly created Vault user."""
    if not auto_provision_enabled():
        logger.info("gbrain auto-provisioning disabled via %s; skipping %s", _AUTO_ENV, slug)
        return None
    if not slug or not _SLUG_RE.fullmatch(slug):
        logger.warning("refusing to provision invalid slug %r", slug)
        return None
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        logger.warning("no running event loop; cannot start gbrain provisioning for %s", slug)
        return None
    task = loop.create_task(_provision(slug, email, name, str(telegram_id or "")))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)
    logger.info("gbrain provisioning queued for %s", slug)
    return task


async def read_status(slug: str) -> dict | None:
    if not slug or not _SLUG_RE.fullmatch(slug):
        return None
    path = STATUS_PATH.format(slug=slug)
    rc, out = await _docker_exec(["sh", "-c", f"cat {path} 2>/dev/null"], timeout=20)
    if rc != 0 or not out.strip():
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None
