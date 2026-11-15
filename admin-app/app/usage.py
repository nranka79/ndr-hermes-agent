"""Usage dashboard for the llm-gateway.

Reads the gateway's internal /v1/usage/* API (service token) and renders
per-user / per-session / per-job consumption plus the raw-retention settings.
"""

from __future__ import annotations

import os
import re
import time

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response

from .jinja_env import env

router = APIRouter()

GATEWAY = os.environ.get("LLM_GATEWAY_USAGE_URL", "http://llm-gateway:8321").rstrip("/")
USAGE_TOKEN = os.environ.get("LLM_USAGE_API_TOKEN", "").strip()

_FILTER_KEYS = ("user_id", "platform", "client", "provider", "bucket", "call_type", "model")

_IDENTITY_CACHE = {"at": 0.0, "map": {}}


def _telegram_map(vault) -> dict:
    """telegram id -> {email, name}, cached briefly. Never fails the page."""
    now = time.time()
    if now - float(_IDENTITY_CACHE.get("at") or 0) < 60 and _IDENTITY_CACHE.get("map"):
        return _IDENTITY_CACHE["map"]
    out: dict[str, dict] = {}
    try:
        for user in vault.list_users() or []:
            email = str(user.get("email") or user.get("user_id") or "")
            name = str(user.get("name") or "")
            ids = list(user.get("telegram_ids") or [])
            if user.get("telegram"):
                ids.append(user.get("telegram"))
            for tid in ids:
                tid = str(tid or "").strip()
                if tid:
                    out[tid] = {"email": email, "name": name}
    except Exception:  # noqa: BLE001 - identity mapping is optional
        pass
    _IDENTITY_CACHE.update({"at": now, "map": out})
    return out


def _enrich(rows: list[dict], id_map: dict) -> list[dict]:
    for row in rows:
        uid = str(row.get("name") or row.get("user_id") or "")
        candidates = [uid]
        # Canonical ids can be prefixed (telegram_123, ndr-123); the vault
        # maps the raw channel id, so try the suffix too.
        if "-" in uid:
            candidates.append(uid.rsplit("-", 1)[-1])
        if "_" in uid:
            candidates.append(uid.rsplit("_", 1)[-1])
        mapped = next((id_map[c] for c in candidates if c in id_map), None)
        if mapped:
            row["email"] = mapped.get("email") or ""
            row["display_name"] = mapped.get("name") or row.get("user_label") or ""
    return rows


_USER_SUM_FIELDS = (
    "requests", "prompt_tokens", "completion_tokens", "cached_tokens",
    "reasoning_tokens", "total_tokens", "images", "audio_seconds",
    "characters", "cost_usd", "notional_cost_usd",
)


def _merge_user_rows(rows: list[dict]) -> list[dict]:
    """Collapse aliases of the same person (telegram id, cron id, email)."""
    merged: dict[str, dict] = {}
    order: list[str] = []
    for row in rows:
        key = str(
            row.get("email") or row.get("display_name") or row.get("user_label")
            or row.get("name") or "unknown"
        ).strip().lower()
        if key not in merged:
            new = dict(row)
            new["name"] = row.get("email") or row.get("user_label") or row.get("name") or "unknown"
            new["email"] = row.get("email") or (new["name"] if "@" in new["name"] else "")
            merged[key] = new
            order.append(key)
            continue
        dst = merged[key]
        for field in _USER_SUM_FIELDS:
            try:
                dst[field] = float(dst.get(field) or 0) + float(row.get(field) or 0)
            except (TypeError, ValueError):
                pass
        if not dst.get("display_name") and row.get("display_name"):
            dst["display_name"] = row["display_name"]
    return [merged[k] for k in order]


_PHONE_CACHE = {"at": 0.0, "map": {}}


def _digits(value) -> str:
    return re.sub(r"\D", "", str(value or ""))


def _vault_phone_map(vault) -> dict:
    """Normalized phone digits -> {user_id, email, name}, cached briefly."""
    now = time.time()
    if now - float(_PHONE_CACHE.get("at") or 0) < 60 and _PHONE_CACHE.get("map"):
        return _PHONE_CACHE["map"]
    out: dict[str, dict] = {}
    try:
        for user in vault.list_users() or []:
            uid = user.get("user_id")
            if not uid:
                continue
            record = vault.get_identity(uid) or {}
            phone = _digits(record.get("phone"))
            if not phone:
                continue
            emails = (record.get("identities") or {}).get("email") or []
            entry = {
                "user_id": uid,
                "email": emails[0] if emails else (user.get("email") or ""),
                "name": record.get("name") or user.get("name") or "",
            }
            out[phone] = entry
            if len(phone) >= 10:
                out.setdefault(phone[-10:], entry)
    except Exception:  # noqa: BLE001 - identity resolution is best-effort
        pass
    _PHONE_CACHE.update({"at": now, "map": out})
    return out


def _headers() -> dict:
    return {"Authorization": f"Bearer {USAGE_TOKEN}"} if USAGE_TOKEN else {}


async def _get(path: str, params: dict | None = None) -> dict:
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(GATEWAY + path, params=params or {}, headers=_headers())
    if resp.status_code != 200:
        raise RuntimeError(f"gateway {path} -> HTTP {resp.status_code}: {resp.text[:200]}")
    return resp.json()


def _query(request: Request) -> dict:
    q = {k: v for k, v in request.query_params.items() if v}
    q.setdefault("group_by", "user")
    return q


@router.get("/usage")
async def usage_page(request: Request):
    q = _query(request)
    summary, sessions, jobs, upstream, settings, health = [], [], [], [], {}, {}
    error = ""
    try:
        summary = (await _get("/v1/usage/summary", q)).get("rows", [])
        sessions = (await _get("/v1/usage/sessions", q)).get("rows", [])
        jobs = (await _get("/v1/usage/jobs", q)).get("rows", [])
        upstream = (await _get("/v1/usage/upstream", q)).get("rows", [])
        settings = await _get("/v1/usage/settings")
        health = await _get("/v1/usage/health")
    except Exception as exc:  # noqa: BLE001 - render the page with a banner
        error = str(exc)
    vault = getattr(request.app.state, "vault", None)
    id_map = _telegram_map(vault) if vault is not None else {}
    if id_map:
        _enrich(summary, id_map)
        _enrich(sessions, id_map)
        _enrich(jobs, id_map)
    if q.get("group_by", "user") == "user":
        summary = _merge_user_rows(summary)
    totals = {
        "requests": sum(int(r.get("requests") or 0) for r in summary),
        "tokens": sum(int(r.get("total_tokens") or 0) for r in summary),
        "cost": sum(float(r.get("cost_usd") or 0) for r in summary),
        "notional": sum(float(r.get("notional_cost_usd") or 0) for r in summary),
        "sessions": len(sessions),
        "jobs": len(jobs),
    }
    return HTMLResponse(env.get_template("usage.html").render(
        user=request.session.get("user"),
        error=error,
        summary=summary,
        sessions=sessions,
        jobs=jobs,
        upstream=upstream,
        settings=settings,
        health=health,
        totals=totals,
        filters=q,
        filter_keys=_FILTER_KEYS,
        query_string=request.url.query,
    ))


@router.get("/usage/identity/resolve")
async def usage_identity_resolve(request: Request, phone: str = ""):
    """Internal phone -> vault user lookup for the gateway (service token)."""
    auth = request.headers.get("Authorization", "")
    if USAGE_TOKEN and auth != f"Bearer {USAGE_TOKEN}":
        raise HTTPException(401, "invalid usage token")
    digits = _digits(phone)
    if not digits:
        raise HTTPException(400, "phone required")
    vault = getattr(request.app.state, "vault", None)
    if vault is None:
        raise HTTPException(503, "vault unavailable")
    mapping = _vault_phone_map(vault)
    record = mapping.get(digits) or mapping.get(digits[-10:])
    if not record:
        return JSONResponse({"ok": False})
    return JSONResponse({"ok": True, **record})


@router.get("/usage/data")
async def usage_data(request: Request):
    try:
        return JSONResponse(await _get("/v1/usage/summary", _query(request)))
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, str(exc))


@router.get("/usage/export.csv")
async def usage_export(request: Request):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                GATEWAY + "/v1/usage/export.csv",
                params=_query(request),
                headers=_headers(),
            )
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, str(exc))
    if resp.status_code != 200:
        raise HTTPException(resp.status_code, resp.text[:300])
    return Response(
        content=resp.content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=llm-usage.csv"},
    )


@router.post("/usage/settings")
async def usage_settings(request: Request):
    form = await request.form()
    payload = {
        "raw_retention_days": form.get("raw_retention_days", "7"),
        "capture_raw": form.get("capture_raw") == "on",
        "include_stream_usage": form.get("include_stream_usage") == "on",
        "reject_unknown": form.get("reject_unknown") == "on",
    }
    if form.get("prune_now") == "on":
        payload["prune_now"] = True
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                GATEWAY + "/v1/usage/settings", json=payload, headers=_headers()
            )
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(502, str(exc))
    return RedirectResponse("/usage", status_code=303)
