import json
import logging

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from .jinja_env import env
from .vault_client import VaultClient

router = APIRouter()
logger = logging.getLogger("admin-app.tokens")


@router.get("")
async def list_tokens(request: Request):
    vault: VaultClient = request.app.state.vault
    try:
        users = vault.list_users()
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)

    user_tokens = []
    for u in users:
        uid = u.get("user_id")
        if not uid:
            continue
        try:
            services = vault.list_token_services(uid)
        except Exception:
            services = []
        if services:
            for svc in services:
                user_tokens.append({
                    "user_id": uid,
                    "name": u.get("name", uid),
                    "email": u.get("email", ""),
                    "service": svc,
                })

    return HTMLResponse(env.get_template("tokens.html").render(
        user=request.session.get("user"), user_tokens=user_tokens,
    ))


@router.post("/{user_id}/{service}/delete")
async def delete_token(request: Request, user_id: str, service: str):
    vault: VaultClient = request.app.state.vault
    try:
        vault.delete_token(user_id, service)
    except Exception as e:
        return HTMLResponse(env.get_template("error.html").render(
            user=request.session.get("user"), error=str(e)
        ), status_code=500)
    return RedirectResponse(url="/tokens", status_code=303)
