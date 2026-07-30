import logging
from pathlib import Path

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .jinja_env import env
from .vault_client import VaultClient, VaultError, MANAGED_APPS

router = APIRouter()
logger = logging.getLogger("admin-app.users")

VAULT_SERVICE_NAMES = {
    "gmail": "gmail",
    "calendar": "calendar",
    "docs": "docs",
    "sheets": "sheets",
    "tasks": "tasks",
    "contacts": "contacts",
    "drive": "drive",
    "vocab": "STT vocabulary",
}


def _pretty_service(svc: str) -> str:
    """Return a human-readable label for a vault service key."""
    if svc in VAULT_SERVICE_NAMES:
        return VAULT_SERVICE_NAMES[svc]
    if svc.startswith("google-"):
        return f"Google ({svc.removeprefix('google-')})"
    if svc.startswith("mcp-"):
        return f"MCP {svc.removeprefix('mcp-')}"
    return svc


def _slug_from_email(email: str) -> str:
    return "".join(c for c in email.split("@")[0] if c.isalnum() or c in "._-")


@router.get("")
async def list_users(request: Request):
    vault: VaultClient = request.app.state.vault
    try:
        users = vault.list_users()
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return HTMLResponse(env.get_template("users.html").render(
        user=request.session.get("user"), users=users,
    ))


@router.get("/new")
async def new_user_form(request: Request):
    return HTMLResponse(env.get_template("user_form.html").render(
        user=request.session.get("user"), editing=False, user_data={},
    ))


@router.post("/new")
async def create_user(
    request: Request,
    user_id: str = Form(...),
    email: str = Form(...),
    telegram_id: str = Form(""),
    phone: str = Form(""),
    name: str = Form(""),
    role: str = Form("employee"),
):
    vault: VaultClient = request.app.state.vault
    slug = user_id or _slug_from_email(email)
    gbrain_home = f"/data/hermes/users/{slug}"
    permissions = {
        "vault_admin": role == "admin",
        "manage_users": role == "admin",
        "multi_google": False,
        "cross_message_allowed": False,
        "apps": {app: True for app in MANAGED_APPS},
    }
    try:
        vault.add_identity(
            user_id=email,
            identity_type="email",
            identity_value=email,
            name=name,
            role=role,
            permissions=permissions,
            gbrain_home=gbrain_home,
            phone=phone or None,
        )
        vault.add_identity(user_id=email, identity_type="draas_user_id", identity_value=slug)
        if telegram_id:
            vault.add_identity(user_id=email, identity_type="telegram", identity_value=telegram_id)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)

    hermes_home = request.app.state.hermes_home
    if hermes_home:
        gbrain_dir = Path(hermes_home) / "users" / slug
        gbrain_dir.mkdir(parents=True, exist_ok=True)

    return RedirectResponse(url="/users", status_code=303)


@router.get("/{user_id}")
async def view_user(request: Request, user_id: str):
    vault: VaultClient = request.app.state.vault
    try:
        identity = vault.get_identity(user_id)
        if not identity:
            return HTMLResponse(env.get_template("error.html").render(
                user=request.session.get("user"), error=f"User {user_id} not found"
            ), status_code=404)
        services = vault.list_token_services(user_id)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)

    identities_map = identity.get("identities", {}) or {}
    emails = identities_map.get("email", [])
    telegrams = identities_map.get("telegram", [])
    phones = identities_map.get("phone", [])

    apps_perms = (identity.get("permissions", {}) or {}).get("apps", {}) or {}
    app_states = {app: apps_perms.get(app, True) for app in MANAGED_APPS}

    full_permissions = identity.get("permissions", {}) or {}
    oauth_providers = full_permissions.get("oauth_providers", {}) or {}
    oauth_google_emails = oauth_providers.get("google", []) or []
    oauth_kelsa = oauth_providers.get("kelsa", False)

    return HTMLResponse(env.get_template("user_detail.html").render(
        user=request.session.get("user"), user_data=identity,
        identities_map=identities_map,
        email_display=", ".join(emails) if emails else "-",
        telegram_display=", ".join(telegrams) if telegrams else "-",
        phone_display=", ".join(phones) if phones else "-",
        services=services, VAULT_SERVICE_NAMES=VAULT_SERVICE_NAMES,
        pretty_service=_pretty_service,
        managed_apps=MANAGED_APPS, app_states=app_states,
        full_permissions=full_permissions,
        oauth_providers=oauth_providers,
        oauth_google_emails=oauth_google_emails,
        oauth_kelsa=oauth_kelsa,
    ))


@router.post("/{user_id}/apps")
async def update_app_permissions(request: Request, user_id: str):
    vault: VaultClient = request.app.state.vault
    form = await request.form()
    desired = {app: (app in form) for app in MANAGED_APPS}
    try:
        vault.set_app_permissions(user_id, desired)
    except VaultError as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/permissions")
async def update_user_permissions(request: Request, user_id: str):
    vault: VaultClient = request.app.state.vault
    form = await request.form()
    name = form.get("name", "").strip()
    role = form.get("role", "").strip()
    phone = form.get("phone", "").strip()
    cross_message = "cross_message_allowed" in form
    multi_google = "multi_google" in form

    try:
        identity = vault.get_identity(user_id)
        if not identity:
            return HTMLResponse(env.get_template("error.html").render(
                user=request.session.get("user"), error=f"User {user_id} not found"
            ), status_code=404)

        permissions = dict(identity.get("permissions", {}) or {})
        permissions["cross_message_allowed"] = cross_message
        permissions["multi_google"] = multi_google

        emails = (identity.get("identities", {}) or {}).get("email", [])
        primary_email = emails[0] if emails else user_id

        vault.add_identity(
            user_id=user_id,
            identity_type="email",
            identity_value=primary_email,
            name=name or None,
            role=role if role in ("admin", "employee") else None,
            permissions=permissions,
            phone=phone or None,
        )
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/oauth-providers")
async def update_oauth_providers(request: Request, user_id: str):
    """Update the oauth_providers permission block for a user.

    Accepts form fields:
      - google_emails: comma-separated list of authorized Google emails
      - kelsa: "on" or missing (checkbox)
      - Any future provider as a checkbox or comma-separated list
    """
    vault: VaultClient = request.app.state.vault
    form = await request.form()

    try:
        identity = vault.get_identity(user_id)
        if not identity:
            return HTMLResponse(env.get_template("error.html").render(
                user=request.session.get("user"), error=f"User {user_id} not found"
            ), status_code=404)

        google_raw = form.get("google_emails", "").strip()
        google_emails = [e.strip() for e in google_raw.split(",") if e.strip()]

        kelsa = "kelsa" in form

        permissions = dict(identity.get("permissions", {}) or {})
        permissions["oauth_providers"] = {
            "google": google_emails,
            "kelsa": kelsa,
        }

        vault.update_permissions(user_id, {"oauth_providers": permissions["oauth_providers"]})
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/add-identity")
async def add_user_identity(request: Request, user_id: str,
                            identity_type: str = Form(...),
                            identity_value: str = Form(...)):
    vault: VaultClient = request.app.state.vault
    try:
        vault.add_identity(user_id=user_id, identity_type=identity_type, identity_value=identity_value)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/delete-identity")
async def delete_identity(request: Request, user_id: str,
                          identity_type: str = Form(...),
                          identity_value: str = Form(...)):
    vault: VaultClient = request.app.state.vault
    try:
        vault.remove_identity(user_id, identity_type, identity_value)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/delete")
async def delete_user(request: Request, user_id: str):
    vault: VaultClient = request.app.state.vault
    try:
        vault.delete_user(user_id)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url="/users", status_code=303)
