"""Token Harbor credit provider (in-admin-app, async httpx).

Token Harbor publishes no balance endpoint in its public docs, so this probes
the shapes an OpenAI-compatible gateway usually exposes and reports whichever
one answers. If none do, it raises QuotaUnsupported so the card says "no quota
surface" instead of showing a scary error — same degrade-loudly stance as the
SuperGrok adapter.
"""

from __future__ import annotations

from .base import ProviderError, QuotaUnsupported

BASE = "https://tokenharbor.ai/v1"

# Probed in order; first 200 with a recognizable body wins.
CANDIDATES = ("/credits", "/dashboard/billing/credit_grants", "/wallet", "/me")


def _num(value) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _normalize(path: str, body: dict) -> dict | None:
    """Map a probe response onto {total_purchased, total_used, balance}."""
    data = body.get("data") if isinstance(body.get("data"), dict) else body
    if not isinstance(data, dict):
        return None

    total = _num(data.get("total_credits") or data.get("total_granted") or data.get("granted"))
    used = _num(data.get("total_usage") or data.get("total_used") or data.get("used"))
    balance = _num(
        data.get("balance")
        if data.get("balance") is not None
        else data.get("total_available")
        if data.get("total_available") is not None
        else data.get("credits")
    )
    if balance is None and total is not None and used is not None:
        balance = round(total - used, 2)
    if total is None and used is None and balance is None:
        return None
    return {
        "credits": {"total_purchased": total, "total_used": used, "balance": balance},
        "source_endpoint": path,
    }


async def fetch(account, client) -> dict:
    key = account.credential()
    base = (account.base or BASE).rstrip("/")
    headers = {"Authorization": f"Bearer {key}"}

    last_status = None
    for path in CANDIDATES:
        try:
            resp = await client.get(f"{base}{path}", headers=headers)
        except Exception:  # noqa: BLE001 - probe failures are expected, try the next shape
            continue
        last_status = resp.status_code
        if resp.status_code == 401:
            raise ProviderError("401 — bad or revoked key")
        if resp.status_code != 200:
            continue
        try:
            body = resp.json() or {}
        except Exception:  # noqa: BLE001 - HTML error page etc.
            continue
        out = _normalize(path, body)
        if out:
            return {"provider": "tokenharbor", **out}

    raise QuotaUnsupported(
        "Token Harbor exposes no documented balance endpoint"
        + (f" (last probe returned HTTP {last_status})" if last_status else "")
    )
