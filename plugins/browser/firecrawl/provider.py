"""Firecrawl cloud browser provider — plugin form.

Subclasses :class:`agent.browser_provider.BrowserProvider` (the plugin-facing
ABC introduced in PR #25214). The legacy in-tree module
``tools.browser_providers.firecrawl`` was removed in the same PR; this file
is now the canonical implementation.

This is the cloud-browser path — distinct from the firecrawl WEB plugin at
``plugins/web/firecrawl/`` which handles search/extract/crawl on
``/v2/search`` / ``/v2/scrape`` / ``/v2/crawl``. The two plugins share the
``FIRECRAWL_API_KEY`` env var but talk to different endpoints (this one
hits ``/v2/browser``).

Config keys this provider responds to::

    browser:
      cloud_provider: "firecrawl"   # explicit selection only — not in the
                                    # legacy auto-detect walk

Auth env vars::

    FIRECRAWL_API_KEY=...           # https://firecrawl.dev
    FIRECRAWL_API_URL=...           # optional override (default https://api.firecrawl.dev)
    FIRECRAWL_BROWSER_TTL=...       # optional, default 300 seconds
"""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, Dict, Optional

import requests

from agent.browser_provider import BrowserProvider
from tools.key_rotation import KEY_DEAD_STATUSES, KeyRotator, has_key_series

logger = logging.getLogger(__name__)

_FIRECRAWL_ROTATOR = KeyRotator("FIRECRAWL_API_KEY")

_BASE_URL = "https://api.firecrawl.dev"


class FirecrawlBrowserProvider(BrowserProvider):
    """Firecrawl (https://firecrawl.dev) cloud browser backend.

    Cloud-browser path only — search/extract/crawl live in the separate
    ``plugins/web/firecrawl/`` plugin.
    """

    @property
    def name(self) -> str:
        return "firecrawl"

    @property
    def display_name(self) -> str:
        return "Firecrawl"

    def is_available(self) -> bool:
        return has_key_series("FIRECRAWL_API_KEY")

    # ------------------------------------------------------------------
    # Session lifecycle
    # ------------------------------------------------------------------

    def _api_url(self) -> str:
        return os.environ.get("FIRECRAWL_API_URL", _BASE_URL)

    def _headers(self, api_key: Optional[str] = None) -> Dict[str, str]:
        if api_key is None:
            api_key = next(_FIRECRAWL_ROTATOR.iter_keys(), None)
        if not api_key:
            raise ValueError(
                "FIRECRAWL_API_KEY environment variable is required. "
                "Get your key at https://firecrawl.dev"
            )
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        }

    def create_session(self, task_id: str) -> Dict[str, object]:
        try:
            ttl = int(os.environ.get("FIRECRAWL_BROWSER_TTL", "300"))
        except (ValueError, TypeError):
            ttl = 300

        body: Dict[str, object] = {"ttl": ttl}
        url = f"{self._api_url()}/v2/browser"

        # Try each key in the FIRECRAWL_API_KEY series until one creates a
        # session; 401/402/403/429 = key rejected -> next key.
        last_error: Optional[Exception] = None
        rejected = False
        for key in _FIRECRAWL_ROTATOR.iter_keys():
            try:
                response = requests.post(
                    url,
                    headers=self._headers(key),
                    json=body,
                    timeout=30,
                )
            except requests.RequestException as exc:
                last_error = exc
                continue
            if not response.ok:
                if response.status_code in KEY_DEAD_STATUSES:
                    rejected = True
                    _FIRECRAWL_ROTATOR.mark_dead(key)
                    continue
                raise RuntimeError(
                    f"Failed to create Firecrawl browser session: "
                    f"{response.status_code} {response.text}"
                )
            _FIRECRAWL_ROTATOR.mark_worked(key)

            data = response.json()
            session_name = f"hermes_{task_id}_{uuid.uuid4().hex[:8]}"

            logger.info("Created Firecrawl browser session %s", session_name)

            return {
                "session_name": session_name,
                "bb_session_id": data["id"],
                "cdp_url": data["cdpUrl"],
                "features": {"firecrawl": True},
            }

        if rejected:
            raise RuntimeError(
                "all configured FIRECRAWL_API_KEY key(s) were rejected by Firecrawl"
            )
        if last_error is not None:
            raise RuntimeError(
                f"Firecrawl API connection failed: {last_error}"
            ) from last_error
        raise RuntimeError(
            "FIRECRAWL_API_KEY environment variable is required. "
            "Get your key at https://firecrawl.dev"
        )

    def close_session(self, session_id: str) -> bool:
        try:
            response = requests.delete(
                f"{self._api_url()}/v2/browser/{session_id}",
                headers=self._headers(),
                timeout=10,
            )
            if response.status_code in {200, 201, 204}:
                logger.debug("Successfully closed Firecrawl session %s", session_id)
                return True
            else:
                logger.warning(
                    "Failed to close Firecrawl session %s: HTTP %s - %s",
                    session_id,
                    response.status_code,
                    response.text[:200],
                )
                return False
        except Exception as e:
            logger.error("Exception closing Firecrawl session %s: %s", session_id, e)
            return False

    def emergency_cleanup(self, session_id: str) -> None:
        if not self.is_available():
            logger.warning(
                "Cannot emergency-cleanup Firecrawl session %s — missing credentials",
                session_id,
            )
            return
        try:
            requests.delete(
                f"{self._api_url()}/v2/browser/{session_id}",
                headers=self._headers(),
                timeout=5,
            )
        except Exception as e:
            logger.debug(
                "Emergency cleanup failed for Firecrawl session %s: %s", session_id, e
            )

    def get_setup_schema(self) -> Dict[str, Any]:
        return {
            "name": "Firecrawl",
            "badge": "paid",
            "tag": "Cloud browser with remote execution",
            "env_vars": [
                {
                    "key": "FIRECRAWL_API_KEY",
                    "prompt": "Firecrawl API key",
                    "url": "https://firecrawl.dev",
                },
            ],
            "post_setup": "agent_browser",
        }
