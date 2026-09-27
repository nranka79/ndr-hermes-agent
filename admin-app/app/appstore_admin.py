"""AppStore management for the admin-app.

Pages at /appstore-admin let the admin:
  - edit the allowlist (who may sign in at apps.ahfl.in)
  - edit the app catalog (app cards, install steps, YouTube video links, downloads)

Both call the appstore admin API (apps.ahfl.in) with APPSTORE_ADMIN_TOKEN.
Env: APPSTORE_URL (https://apps.ahfl.in), APPSTORE_ADMIN_TOKEN (shared).
"""

import logging
import os

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from .jinja_env import env

router = APIRouter()
logger = logging.getLogger("admin-app.appstore")

APPSTORE_URL = os.environ.get("APPSTORE_URL", "https://apps.ahfl.in")
APPSTORE_ADMIN_TOKEN = os.environ.get("APPSTORE_ADMIN_TOKEN", "")


async def _api(path: str, method: str = "get", payload: dict | None = None):
    headers = {"X-Admin-Token": APPSTORE_ADMIN_TOKEN}
    async with httpx.AsyncClient(timeout=15) as c:
        if method == "get":
            return await c.get(f"{APPSTORE_URL}{path}", headers=headers)
        return await c.post(
            f"{APPSTORE_URL}{path}",
            headers={**headers, "Content-Type": "application/json"},
            json=payload or {},
        )


async def _fetch_allowlist() -> dict:
    try:
        r = await _api("/admin/allowlist")
        if r.status_code == 200:
            return (r.json().get("allowlist") or {})
    except Exception as exc:  # noqa: BLE001
        logger.warning("appstore allowlist fetch failed: %s", exc)
    return {"domains": [], "emails": []}


async def _fetch_apps() -> list:
    try:
        r = await _api("/admin/apps")
        if r.status_code == 200:
            return list(r.json().get("apps") or [])
    except Exception as exc:  # noqa: BLE001
        logger.warning("appstore catalog fetch failed: %s", exc)
    return []


def _collect_apps(form) -> list:
    """Collect indexed app fields (app_name_0, app_name_1, ...) from the form."""
    apps = []
    i = 0
    while True:
        name = (form.get(f"app_name_{i}") or "").strip()
        if not name:
            break
        app_id = (form.get(f"app_id_{i}") or "").strip()
        if not app_id:
            app_id = name.lower().replace(" ", "-").replace("/", "-")

        links = []
        j = 0
        while j < 30:
            label = (form.get(f"app_links_label_{i}_{j}") or "").strip()
            url = (form.get(f"app_links_url_{i}_{j}") or "").strip()
            if url:
                links.append({"label": label or url, "url": url})
            j += 1

        apps.append({
            "id": app_id,
            "name": name,
            "type": (form.get(f"app_type_{i}") or "").strip(),
            "version": (form.get(f"app_version_{i}") or "").strip(),
            "description": (form.get(f"app_desc_{i}") or "").strip(),
            "long_description": (form.get(f"app_long_{i}") or "").strip(),
            "install_steps": [
                s.strip() for s in (form.get(f"app_steps_{i}") or "").splitlines() if s.strip()
            ],
            "links": links,
            "download_url": (form.get(f"app_url_{i}") or "").strip(),
            "file": (form.get(f"app_file_{i}") or "").strip(),
        })
        i += 1
    return apps


async def _save_apps(apps: list):
    try:
        r = await _api("/admin/apps", method="post", payload={"apps": apps})
        return r.status_code == 200, f"save HTTP {r.status_code}"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


@router.get("/appstore-admin")
async def page(request: Request):
    allowlist = await _fetch_allowlist()
    apps = await _fetch_apps()
    return HTMLResponse(env.get_template("appstore_admin.html").render(
        user=request.session.get("user"), allowlist=allowlist, apps=apps,
        error=None, saved=None, appstore_configured=bool(APPSTORE_ADMIN_TOKEN)))


@router.post("/appstore-admin")
async def save(request: Request):
    form = await request.form()
    action = form.get("action") or "allowlist"
    error = None
    saved = None
    allowlist = await _fetch_allowlist()
    apps = await _fetch_apps()

    if action == "allowlist":
        domains = [d.strip() for d in (form.get("domains") or "").split(",") if d.strip()]
        emails = [e.strip() for e in (form.get("emails") or "").split(",") if e.strip()]
        try:
            r = await _api("/admin/allowlist", method="post", payload={"domains": domains, "emails": emails})
            if r.status_code == 200:
                allowlist = (r.json().get("allowlist") or {})
                saved = "Allowlist saved."
            else:
                error = f"save HTTP {r.status_code}"
        except Exception as exc:  # noqa: BLE001
            error = str(exc)
    elif action == "catalog":
        new_apps = _collect_apps(form)
        ok, msg = await _save_apps(new_apps)
        if ok:
            apps = new_apps
            saved = f"Catalog saved ({len(new_apps)} apps)."
        else:
            error = f"catalog save failed: {msg}"

    return HTMLResponse(env.get_template("appstore_admin.html").render(
        user=request.session.get("user"), allowlist=allowlist, apps=apps,
        error=error, saved=saved, appstore_configured=bool(APPSTORE_ADMIN_TOKEN)))