"""Tunnel router dashboard proxy — serves /tunnel/* behind the SAME
Google SSO as the rest of this admin panel.

The tunnel router's admin API (hermes-utilities :8742) is bearer-token
protected. Instead of exposing that token to browsers (the earlier
nginx-injection approach let anyone who could reach admin.ahfl.in open
the dashboard with no login), this app proxies read-only GET traffic to
it, adding the Authorization header server-side. AuthMiddleware protects
every path not in its public list, so /tunnel/* is only reachable after
the same Google OAuth login — which is restricted to ADMIN_EMAILS
(ndr@draas.com), see auth.py.

Read-only on purpose: only GET is proxied (the dashboard page needs GET
/live and GET /dashboard). Any future method is an explicit, deliberate
addition here.
"""
import os
import logging

import httpx
from fastapi import APIRouter, Request, Response

router = APIRouter(prefix="/tunnel")

ROUTER_API_URL = os.environ.get("HERMES_TUNNEL_API_URL", "http://hermes-utilities:8742")
ROUTER_API_TOKEN = os.environ.get("HERMES_API_TOKEN", "")

logger = logging.getLogger("admin-app.tunnel")


@router.get("/{path:path}")
async def tunnel_proxy(path: str, request: Request):
    url = f"{ROUTER_API_URL}/{path}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                url,
                params=dict(request.query_params),
                headers={"Authorization": f"Bearer {ROUTER_API_TOKEN}"},
            )
    except httpx.HTTPError as e:
        logger.warning(f"tunnel proxy upstream error: {e}")
        return Response("tunnel router unreachable", status_code=502, media_type="text/plain")

    content_type = resp.headers.get("content-type", "application/octet-stream")
    return Response(content=resp.content, status_code=resp.status_code, media_type=content_type)
