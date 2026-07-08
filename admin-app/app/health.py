import json
import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from .vault_client import VaultClient

router = APIRouter()
logger = logging.getLogger("admin-app.health")


@router.get("")
async def health(request: Request):
    vault: VaultClient = request.app.state.vault
    vault_health = vault.health()
    return JSONResponse({
        "status": "ok" if vault_health["status"] == "ok" else "degraded",
        "vault": vault_health,
    })
