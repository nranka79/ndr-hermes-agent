import logging
from typing import Optional

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .jinja_env import env
from .vault_client import VaultClient

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
}


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
    telegram_id: str = Form(...),
    name: str = Form(""),
    role: str = Form("employee"),
):
    vault: VaultClient = request.app.state.vault
    permissions = {"vault_admin": role == "admin", "manage_users": role == "admin"}
    try:
        vault.add_identity(
            user_id=user_id,
            identity_type="email",
            identity_value=email,
            name=name,
            role=role,
            permissions=permissions,
        )
        if telegram_id:
            vault.add_identity(
                user_id=user_id,
                identity_type="telegram",
                identity_value=telegram_id,
            )
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
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
    return HTMLResponse(env.get_template("user_detail.html").render(
        user=request.session.get("user"), user_data=identity,
        services=services, VAULT_SERVICE_NAMES=VAULT_SERVICE_NAMES,
    ))


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
