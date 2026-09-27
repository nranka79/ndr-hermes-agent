"""Claude / Anthropic spend provider (in-admin-app, async httpx).

Anthropic publishes no credit-balance endpoint, so this reports month-to-date
spend from the Usage & Cost Admin API instead of a remaining balance.

Requires an **Admin API key** (``sk-ant-admin01-…``) or an org-scoped key that
is not tied to a workspace — a normal ``sk-ant-api03-…`` key is rejected with a
401 by this endpoint.
"""

from __future__ import annotations

import time

from .base import ProviderError, QuotaUnsupported

BASE = "https://api.anthropic.com/v1/organizations"
VERSION = "2023-06-01"
ADMIN_PREFIX = "sk-ant-admin"


def _month_start() -> str:
    t = time.gmtime()
    return time.strftime("%Y-%m-01T00:00:00Z", t)


async def fetch(account, client) -> dict:
    key = account.credential()
    # An anthropic entry in a rotation bucket is a normal API key that serves
    # traffic; the cost report 401s it. Say so plainly instead of flagging a
    # working key as broken.
    if not key.startswith(ADMIN_PREFIX):
        raise QuotaUnsupported(
            "a routing key cannot read the cost report — add an Admin API key "
            "as ANTHROPIC_ADMIN_API_KEY to see Claude spend"
        )
    starting_at = _month_start()
    resp = await client.get(
        f"{BASE}/cost_report",
        params={"starting_at": starting_at, "bucket_width": "1d", "limit": 31},
        headers={"x-api-key": key, "anthropic-version": VERSION},
    )
    if resp.status_code in (401, 403):
        raise ProviderError(
            f"{resp.status_code} — needs an Admin API key (sk-ant-admin01-…); "
            "a normal API key cannot read the cost report"
        )
    if resp.status_code != 200:
        raise ProviderError(f"HTTP {resp.status_code}: {resp.text[:200]}")

    buckets = (resp.json() or {}).get("data") or []
    # `amount` is a decimal string in the currency's lowest unit (cents).
    total_cents = 0.0
    day_cents = 0.0
    by_model: dict[str, float] = {}
    for i, bucket in enumerate(buckets):
        bucket_cents = 0.0
        for item in bucket.get("results") or []:
            try:
                cents = float(item.get("amount") or 0)
            except (TypeError, ValueError):
                continue
            bucket_cents += cents
            model = item.get("model")
            if model:
                by_model[model] = by_model.get(model, 0.0) + cents
        total_cents += bucket_cents
        if i == len(buckets) - 1:
            day_cents = bucket_cents

    return {
        "provider": "anthropic",
        "period_start": starting_at,
        "month_to_date_usd": round(total_cents / 100, 2),
        "today_usd": round(day_cents / 100, 2),
        "top_models": [
            {"model": m, "usd": round(c / 100, 2)}
            for m, c in sorted(by_model.items(), key=lambda kv: -kv[1])[:4]
        ],
    }
