import logging
import os

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .gbrain_provision import start_provisioning
from .jinja_env import env
from .openwebui import sync_chat_users
from .vault_client import VaultClient, VaultError, MANAGED_APPS, write_app_emails_file

# llm_gateway is deliberately NOT in MANAGED_APPS -- that list defaults every
# app to True for an unset key (see app_states below), which is wrong here.
# llm_gateway mirrors the vault daemon's own check_access semantics exactly:
# admins are granted automatically, everyone else needs the explicit toggle.

def _is_admin_identity(identity: dict) -> bool:
    perms = identity.get("permissions", {}) or {}
    return identity.get("role") == "admin" or perms.get("vault_admin") is True


def llm_gateway_state(identity: dict) -> bool:
    apps = (identity.get("permissions", {}) or {}).get("apps", {}) or {}
    return _is_admin_identity(identity) or apps.get("llm_gateway") is True


def whatsapp_state(identity: dict) -> bool:
    """DRA WhatsApp (wa.ahfl.in). Same explicit opt-in semantics as llm_gateway, and for
    the same reason: it is deliberately NOT in MANAGED_APPS, whose unset-means-True display
    default would show every employee as having WhatsApp access they do not actually hold.
    The vault's check_access is the enforcement point (admins implicit, everyone else needs
    permissions.apps.whatsapp is True); this mirrors it exactly."""
    apps = (identity.get("permissions", {}) or {}).get("apps", {}) or {}
    return _is_admin_identity(identity) or apps.get("whatsapp") is True


CHAT_EMAILS_FILE = os.environ.get("CHAT_EMAILS_FILE", "/secrets/chat-emails.txt")
# jobs.ahfl.in oauth2-proxy sidecar reads this via --authenticated-emails-file
# and hot-reloads on change (no restart needed), same mechanism as chat above.
# Added 2026-11-01 -- jobs access used to be a manual, admin-panel-invisible
# file edit; now it is vault-backed like every other MANAGED_APPS entry.
JOBS_EMAILS_FILE = os.environ.get("JOBS_EMAILS_FILE", "/opt/hermes/oauth2-proxy-jobs/emails.txt")


def _sync_chat_emails() -> None:
    """Push a chat-access change out to everything that enforces it.

    The vault is the single source of truth: it feeds oauth2-proxy's email
    allowlist (who may reach chat.ahfl.in at all) and Open WebUI, where each
    allowed user is created, activated and put in the Hermes group — and each
    revoked one is taken out of it and set back to pending. Ticking or
    unticking "chat" here is therefore the whole job, in both directions;
    nothing is granted or revoked inside Open WebUI itself.
    """
    try:
        write_app_emails_file("chat", CHAT_EMAILS_FILE)
    except Exception:  # noqa: BLE001
        logger.warning("chat emails regeneration failed", exc_info=True)
    try:
        sync_chat_users()
    except Exception:  # noqa: BLE001
        logger.warning("Open WebUI chat user sync failed", exc_info=True)
    try:
        write_app_emails_file("jobs", JOBS_EMAILS_FILE)
    except Exception:  # noqa: BLE001
        logger.warning("jobs emails regeneration failed", exc_info=True)

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
    user_id: str = Form(""),
    email: str = Form(...),
    telegram_id: str = Form(""),
    phone: str = Form(""),
    name: str = Form(""),
    role: str = Form("employee"),
):
    vault: VaultClient = request.app.state.vault
    form = await request.form()
    slug = user_id or _slug_from_email(email)
    gbrain_home = f"/data/hermes/users/{slug}"
    if role == "admin":
        # Admins get all apps by default (vault check_access also honors this).
        apps = {app: True for app in MANAGED_APPS}
    else:
        apps = {app: (form.get(f"app_{app}") is not None) for app in MANAGED_APPS}
    apps["llm_gateway"] = (role == "admin")
    # WhatsApp inbox: admins implicitly, employees only when ticked on this form.
    apps["whatsapp"] = (role == "admin") or (form.get("app_whatsapp") is not None)
    permissions = {
        "vault_admin": role == "admin",
        "manage_users": role == "admin",
        "multi_google": False,
        "cross_message_allowed": False,
        "apps": apps,
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

    # Auto-provision a fully-configured gbrain for this user in the background.
    # The provisioner runs inside hermes-hermes-1 (this container has no
    # /data/hermes mount); it creates the dirs, initialises the brain, applies
    # the gateway/pricing/cycle config, and creates the daily ingest + dream
    # cron jobs. Failures never roll back the Vault identity -- /gbrain-health
    # shows the failed state with a retry button.
    start_provisioning(slug=slug, email=email, name=name, telegram_id=telegram_id)

    _sync_chat_emails()
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
        token_meta = vault.list_token_metadata(user_id)
        password_entries = vault.list_passwords(user_id)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)

    identities_map = identity.get("identities", {}) or {}
    emails = identities_map.get("email", [])
    telegrams = identities_map.get("telegram", [])
    phone_value = identity.get("phone") or ""
    apps_perms = (identity.get("permissions", {}) or {}).get("apps", {}) or {}
    app_states = {app: apps_perms.get(app, True) for app in MANAGED_APPS}
    llm_gateway_enabled = llm_gateway_state(identity)
    whatsapp_enabled = whatsapp_state(identity)

    full_permissions = identity.get("permissions", {}) or {}
    oauth_providers = full_permissions.get("oauth_providers", {}) or {}
    oauth_google_emails = oauth_providers.get("google", []) or []
    oauth_kelsa = oauth_providers.get("kelsa", False)
    oauth_tailortalk = oauth_providers.get("tailortalk", False)

    return HTMLResponse(env.get_template("user_detail.html").render(
        user=request.session.get("user"), user_data=identity,
        identities_map=identities_map,
        email_display=", ".join(emails) if emails else "-",
        telegram_display=", ".join(telegrams) if telegrams else "-",
        phone_display=phone_value or "-",
        services=services, token_meta=token_meta, password_entries=password_entries,
        VAULT_SERVICE_NAMES=VAULT_SERVICE_NAMES,
        pretty_service=_pretty_service,
        managed_apps=MANAGED_APPS, app_states=app_states,
        llm_gateway_enabled=llm_gateway_enabled,
        whatsapp_enabled=whatsapp_enabled,
        full_permissions=full_permissions,
        oauth_providers=oauth_providers,
        oauth_google_emails=oauth_google_emails,
        oauth_kelsa=oauth_kelsa,
        oauth_tailortalk=oauth_tailortalk,
    ))


@router.post("/{user_id}/passwords")
async def save_password(
    request: Request,
    user_id: str,
    domain: str = Form(...),
    username: str = Form(...),
    password: str = Form(...),
    origins: str = Form(""),
    label: str = Form(""),
):
    """Create/update an encrypted website credential in the vault. The
    plaintext is sent over HTTPS to this admin app, then to the vault over
    its Unix socket; it is never logged or rendered back."""
    vault: VaultClient = request.app.state.vault
    origin_list = [o.strip() for o in origins.split(",") if o.strip()]
    try:
        vault.put_password(
            user_id, domain.strip(), username.strip(), password,
            origin_list, label.strip(),
        )
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/passwords/{domain}/delete")
async def delete_password(request: Request, user_id: str, domain: str):
    vault: VaultClient = request.app.state.vault
    try:
        vault.delete_password(user_id, domain)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


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
    _sync_chat_emails()
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/whatsapp")
async def update_whatsapp_access(request: Request, user_id: str):
    """Toggle permissions.apps.whatsapp (DRA WhatsApp inbox at wa.ahfl.in). Takes effect
    at the next request to wa.ahfl.in: the bridge asks the vault's check_access on every
    request with a 60s cache, so revocation lands within a minute, no restart anywhere."""
    vault: VaultClient = request.app.state.vault
    form = await request.form()
    enabled = "whatsapp" in form
    try:
        vault.set_app_permissions(user_id, {"whatsapp": enabled})
    except VaultError as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/llm-gateway")
async def update_llm_gateway_access(request: Request, user_id: str):
    """Toggle the llm_gateway flag. Kept separate from /apps (MANAGED_APPS)
    because that endpoint's semantics ("checked" == explicit True for every
    app in the list) would be correct too, but llm_gateway is intentionally
    NOT in MANAGED_APPS -- see the comment on llm_gateway_state() above."""
    vault: VaultClient = request.app.state.vault
    form = await request.form()
    enabled = "llm_gateway" in form
    try:
        vault.set_app_permissions(user_id, {"llm_gateway": enabled})
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
    _sync_chat_emails()
    return RedirectResponse(url=f"/users/{user_id}", status_code=303)


@router.post("/{user_id}/oauth-providers")
async def update_oauth_providers(request: Request, user_id: str):
    """Update the oauth_providers permission block for a user.

    Accepts form fields:
      - google_emails: comma-separated list of authorized Google emails
      - kelsa: "on" or missing (checkbox)
      - tailortalk: "on" or missing (checkbox)
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
        tailortalk = "tailortalk" in form

        permissions = dict(identity.get("permissions", {}) or {})
        permissions["oauth_providers"] = {
            "google": google_emails,
            "kelsa": kelsa,
            "tailortalk": tailortalk,
        }

        vault.update_permissions(user_id, {"oauth_providers": permissions["oauth_providers"]})
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    _sync_chat_emails()
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
    _sync_chat_emails()
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
    _sync_chat_emails()
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
    _sync_chat_emails()
    return RedirectResponse(url="/users", status_code=303)
