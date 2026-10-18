"""SuperGrok subscription provider (in-admin-app, async httpx).

UNDOCUMENTED grok.com billing surface — best-effort, degrades loudly.
"""

from __future__ import annotations

from .base import ProviderError

BASE = "https://cli-chat-proxy.grok.com/v1"


async def fetch(account, client) -> dict:
    token = account.credential()
    resp = await client.get(
        f"{BASE}/billing?format=credits",
        headers={"Authorization": f"Bearer {token}", "X-XAI-Token-Auth": "xai-grok-cli"},
    )
    if resp.status_code == 401:
        raise ProviderError("401 — token expired/invalid; re-run grok login")
    if resp.status_code != 200:
        raise ProviderError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    body = resp.json()
    config = body.get("config") or {}
    percent = config.get("creditUsagePercent")
    try:
        percent = float(percent) if percent is not None else None
    except (TypeError, ValueError):
        percent = None
    period = config.get("currentPeriod") or {}
    products = config.get("productUsage") or []
    return {
        "provider": "supergrok",
        "weekly_percent": percent,
        "period_start": period.get("start"),
        "resets_at": period.get("end") or config.get("billingPeriodEnd"),
        "products": [
            {"product": p.get("product"), "percent": p.get("usagePercent")} for p in products
        ],
        "extra_credits": (config.get("prepaidBalance") or {}).get("val"),
        "on_demand_used": (config.get("onDemandUsed") or {}).get("val"),
    }