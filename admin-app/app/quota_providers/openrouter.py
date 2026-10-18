"""OpenRouter account provider (in-admin-app, async httpx)."""

from __future__ import annotations

import os

from .base import ProviderError

BASE = "https://openrouter.ai/api/v1"


async def fetch(account, client) -> dict:
    key = account.credential()
    base = (account.base or BASE).rstrip("/")
    resp = await client.get(f"{base}/key", headers={"Authorization": f"Bearer {key}"})
    if resp.status_code == 401:
        raise ProviderError("401 — bad or revoked key")
    if resp.status_code == 402:
        raise ProviderError("402 — account out of credit")
    if resp.status_code != 200:
        raise ProviderError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    data = (resp.json() or {}).get("data") or {}
    out = {
        "provider": "openrouter",
        "key_label": data.get("label"),
        "creator_user_id": data.get("creator_user_id"),
        "limit": data.get("limit"),
        "limit_remaining": data.get("limit_remaining"),
        "limit_reset": data.get("limit_reset"),
        "is_free_tier": data.get("is_free_tier"),
        "usage": {
            "all_time": data.get("usage"),
            "daily": data.get("usage_daily"),
            "weekly": data.get("usage_weekly"),
            "monthly": data.get("usage_monthly"),
        },
    }
    mgmt_env = account.extra.get("management_key_env")
    mgmt_key = (os.environ.get(mgmt_env) or "").strip() if mgmt_env else ""
    try:
        creds = await client.get(
            f"{base}/credits", headers={"Authorization": f"Bearer {mgmt_key or key}"}
        )
        if creds.status_code == 200:
            cd = (creds.json() or {}).get("data") or {}
            total = cd.get("total_credits")
            used = cd.get("total_usage")
            out["credits"] = {
                "total_purchased": total,
                "total_used": used,
                "balance": round((total or 0) - (used or 0), 2),
            }
    except Exception:  # noqa: BLE001, S110 - balance is best-effort, never fatal
        pass
    return out