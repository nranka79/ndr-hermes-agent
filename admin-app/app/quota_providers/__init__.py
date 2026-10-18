"""Provider adapters for the quota dashboard, folded INTO the admin-app.

These are the same adapters that used to run in the standalone account-quota
service. They now live in the admin-app and fetch quota/credit data directly
from the provider APIs (OpenCode Go, OpenRouter, Token Harbor, Claude/Anthropic,
SuperGrok) so the quota path runs entirely under admin.ahfl.in on the
production box.

Each module exposes ``async fetch(account, client) -> dict`` where client is a
shared ``httpx.AsyncClient``. Providers raise ``ProviderError`` for
auth/network/shape failures, or ``QuotaUnsupported`` when the upstream simply
publishes no quota surface, so a broken or silent account degrades per-account
instead of breaking the whole snapshot.
"""

from .base import Account, ProviderError, QuotaUnsupported, mask  # noqa: F401
