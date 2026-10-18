"""OpenCode Go quota provider (in-admin-app, async httpx)."""

from __future__ import annotations

from .base import ProviderError

BASE = "https://opencode.ai"
CAPS = {"rolling": 12.0, "weekly": 30.0, "monthly": 60.0}


async def fetch(account, client) -> dict:
    key = account.credential()
    resp = await client.get(
        f"{BASE}/zen/go/v1/usage",
        headers={"Authorization": f"Bearer {key}"},
    )
    if resp.status_code == 403:
        raise ProviderError("403 EntitlementError — key has no Go plan")
    if resp.status_code != 200:
        raise ProviderError(f"HTTP {resp.status_code}: {resp.text[:200]}")
    body = resp.json()
    usage = body.get("usage") or body.get("data", {}).get("usage") or {}

    windows = {}
    for window, cap in CAPS.items():
        w = usage.get(window) or {}
        percent = w.get("percent")
        try:
            percent = float(percent) if percent is not None else None
        except (TypeError, ValueError):
            percent = None
        entry = {"status": w.get("status") or "unknown", "percent": percent, "limit_usd": cap}
        if percent is not None:
            entry["used_usd"] = round(cap * percent / 100, 2)
            entry["remaining_usd"] = round(cap * (100 - percent) / 100, 2)
        if w.get("resetsAt"):
            entry["resets_at"] = w["resetsAt"]
        windows[window] = entry

    if not windows:
        raise ProviderError("unexpected usage payload")
    return {"provider": "opencode-go", "windows": windows}