"""Account config + error type for the in-admin-app quota providers."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


class ProviderError(Exception):
    """Raised when a provider cannot produce a snapshot (auth/network/shape)."""


class QuotaUnsupported(Exception):
    """Raised when a provider has no quota surface at all.

    Distinct from ProviderError: nothing is broken, the upstream simply does
    not publish credits/usage, so the UI shows an informational note instead
    of an error.
    """


def mask(value: str | None) -> str | None:
    value = (value or "").strip()
    if not value:
        return None
    return ("…" + value[-4:]) if len(value) > 4 else ("…" + value)


@dataclass
class Account:
    """One quota account.

    Credentials arrive either as an env var name (flat legacy vars) or as a
    literal key lifted out of an ``LLM_*_POOL`` entry, so the quota page covers
    exactly the keys the keys-admin page manages.
    """

    id: str
    provider: str
    label: str
    api_key_env: str = ""
    token_env: str = ""
    api_key: str = ""
    modality: str = "llm"      # llm | multimodal
    tier: str = "api"          # free | subscription | api
    bucket: str = ""           # keys-admin bucket id this entry came from
    model: str = ""
    base: str = ""
    extra: dict[str, Any] = field(default_factory=dict)

    def credential(self) -> str:
        if self.api_key:
            return self.api_key.strip()
        env = self.api_key_env or self.token_env
        if not env:
            return ""
        return (os.environ.get(env) or "").strip()

    def credential_env(self) -> str:
        return self.api_key_env or self.token_env or f"{self.bucket or 'pool'} entry"
