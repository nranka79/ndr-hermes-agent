"""
Apify Actor Tool — runs pre-built Apify actors via the Apify REST API.

Apify actors are managed scrapers that run on Apify's infrastructure using
residential proxies (India targeting available). This is the reliable path
for sites that block datacenter IPs (99acres, MagicBricks, Housing.com,
Google Maps) — a plain browser on a datacenter IP gets network-blocked.

Built-in presets:
  magicbricks-99acres  -> fascinating_lentil/magicbricks-99acres-property-scraper
                          (sale/rent listings from both portals: price, BHK,
                          area, locality, project name, coords, URLs; ~$3 per
                          1,000 listings; input: source, transactionType,
                          cities[], minPrice/maxPrice, maxResults)
  99acres              -> stealth_mode/99acres-property-search-scraper
                          (99acres-only listings)
  google-places        -> compass/crawler-google-places
                          (Google Maps/Places results for a search query)

Any other actor can be given as ``owner/actor-name``.

Cost guardrails: every actor run is billed to the APIFY_API_KEY account
(pay-per-result + platform usage). Keep the actor's own input result caps
(e.g. ``maxResults``) small; ``max_items`` caps how many dataset records
are returned to the agent.

Registered as: apify_run_actor
Toolset:       web

Args:
  actor           (str, required)  Preset name or "owner/actor-name"
  input           (object, optional) Actor-specific JSON input
  max_items       (int, optional)  Cap on returned dataset records; default 50
  timeout_minutes (int, optional)  Max minutes to wait for the run; default 10

Returns JSON:
  {
    "status":     "completed" | "failed",
    "run_id":     str,
    "item_count": int,
    "items":      [ ... ] | null,
    "error":      str | null
  }
"""

import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request

from tools.registry import registry

logger = logging.getLogger(__name__)

_API_BASE = "https://api.apify.com/v2"
_POLL_INTERVAL = 5  # seconds between run-status polls

_ACTOR_PRESETS = {
    "magicbricks-99acres": "fascinating_lentil/magicbricks-99acres-property-scraper",
    "99acres": "stealth_mode/99acres-property-search-scraper",
    "google-places": "compass/crawler-google-places",
}

_FINISHED_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}


def _api_key() -> str:
    return (os.environ.get("APIFY_API_KEY") or "").strip()


def _resolve_actor(actor: str) -> str:
    """Map a preset or raw ``owner/name`` to the REST actor id form ``owner~name``."""
    if actor in _ACTOR_PRESETS:
        return _ACTOR_PRESETS[actor].replace("/", "~")
    return actor.strip().replace("/", "~")


def _req(method: str, path: str, body=None, key: str = "", timeout: int = 30):
    url = f"{_API_BASE}{path}"
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        url, data=data, method=method,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        parsed = json.loads(resp.read().decode())
    # Apify API v2 wraps most payloads in {"data": ...}, but some endpoints
    # (e.g. dataset items) return a bare array — only unwrap when present.
    if isinstance(parsed, dict) and "data" in parsed:
        return parsed["data"]
    return parsed


def _handle_apify_run_actor(args: dict, **_) -> str:
    actor_name = args["actor"]
    run_input = args.get("input") or {}
    max_items = max(1, min(int(args.get("max_items", 50)), 500))
    timeout_minutes = max(1, min(float(args.get("timeout_minutes", 10)), 30))

    key = _api_key()
    if not key:
        return json.dumps({
            "status": "failed",
            "run_id": None,
            "item_count": 0,
            "items": None,
            "error": "APIFY_API_KEY is not set — add it to /opt/hermes/.env "
                     "(get a free token at console.apify.com) and recreate the container",
        })

    try:
        actor_id = _resolve_actor(actor_name)
        created = _req("POST", f"/acts/{actor_id}/runs", body=run_input, key=key)
        run_id = created.get("id")
        dataset_id = created.get("defaultDatasetId")
        status = created.get("status", "")
        if not run_id:
            logger.error("apify_run_actor: unexpected create response: %s", json.dumps(created)[:500])
            return json.dumps({
                "status": "failed", "run_id": None, "item_count": 0,
                "items": None,
                "error": f"Apify run not created — unexpected response: {json.dumps(created)[:300]}",
            })
        logger.info("apify_run_actor: actor=%s run=%s status=%s", actor_id, run_id, status)

        # Poll until the run finishes (or timeout)
        deadline = time.time() + timeout_minutes * 60
        while time.time() < deadline and status not in _FINISHED_STATUSES:
            time.sleep(_POLL_INTERVAL)
            try:
                run_info = _req("GET", f"/actor-runs/{run_id}", key=key)
                status = run_info.get("status", status)
                dataset_id = dataset_id or run_info.get("defaultDatasetId")
            except Exception as exc:  # transient poll failure — keep waiting
                logger.debug("apify_run_actor: poll error: %s", exc)

        if status != "SUCCEEDED":
            return json.dumps({
                "status": "failed",
                "run_id": run_id,
                "item_count": 0,
                "items": None,
                "error": f"Apify run {run_id} ended with status '{status}'",
            })

        # Fetch dataset items
        if not dataset_id:
            return json.dumps({
                "status": "failed",
                "run_id": run_id,
                "item_count": 0,
                "items": None,
                "error": "Run succeeded but no dataset id returned",
            })
        items = _req(
            "GET",
            f"/datasets/{dataset_id}/items?limit={max_items}",
            key=key,
            timeout=60,
        )
        if isinstance(items, dict):
            items = items.get("items", [])
        return json.dumps({
            "status": "completed",
            "run_id": run_id,
            "item_count": len(items),
            "items": items,
            "error": None,
        }, ensure_ascii=False)

    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace") if exc.fp else ""
        error = f"HTTP {exc.code}: {body[:500]}"
        logger.error("apify_run_actor: %s", error)
        return json.dumps({
            "status": "failed", "run_id": None, "item_count": 0,
            "items": None, "error": error,
        })
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        logger.error("apify_run_actor: %s", error)
        return json.dumps({
            "status": "failed", "run_id": None, "item_count": 0,
            "items": None, "error": error,
        })


def _check_available() -> bool:
    return bool(_api_key())


_APIFY_RUN_ACTOR_SCHEMA = {
    "name": "apify_run_actor",
        "description": (
            "Run a pre-built Apify actor (managed scraper on Apify's residential "
            "proxies, India targeting) and return its structured dataset. "
            "USE THIS for Indian property portals (99acres, MagicBricks, "
            "Housing.com) and Google Maps — those sites network-block datacenter "
            "IPs, so web_extract/browser on the VPS fails for them. Presets: "
            "magicbricks-99acres (sale/rent listings with price, BHK, area, "
            "locality, project name, coords, listing URL; input keys: source "
            "magicbricks|99acres|both, transactionType sale|rent, cities[...] "
            "using MAGICBRICKS CITY NAMES — e.g. \"Bangalore\", NOT \"Bengaluru\" "
            "(Bengaluru returns 0 results) — plus proxyConfiguration "
            "{useApifyProxy: true, apifyProxyGroups: [\"RESIDENTIAL\"], "
            "apifyProxyCountry: \"IN\"} (required for portal access), maxResults), "
            "99acres, google-places. Any other Apify actor as owner/actor-name. "
            "Cost: pay-per-result on your Apify account (~$3 per 1,000 portal "
            "listings) — keep input maxResults small."
        ),
    "parameters": {
        "type": "object",
        "properties": {
            "actor": {
                "type": "string",
                "description": "Preset: magicbricks-99acres | 99acres | google-places — or any Apify actor id as owner/actor-name.",
            },
            "input": {
                "type": "object",
                "description": "Actor-specific JSON input, e.g. {\"source\": \"magicbricks\", \"transactionType\": \"sale\", \"cities\": [\"Bangalore\"], \"maxResults\": 20, \"proxyConfiguration\": {\"useApifyProxy\": true, \"apifyProxyGroups\": [\"RESIDENTIAL\"], \"apifyProxyCountry\": \"IN\"}}. Cities use MagicBricks city names (Bangalore, NOT Bengaluru).",
            },
            "max_items": {
                "type": "integer",
                "description": "Cap on dataset records returned to the agent. Default 50, max 500.",
                "default": 50,
            },
            "timeout_minutes": {
                "type": "integer",
                "description": "Max minutes to wait for the run. Default 10, max 30.",
                "default": 10,
            },
        },
        "required": ["actor"],
    },
}


# NOTE: registration must be a BARE top-level call — the auto-discovery AST
# scan (tools/registry.py::_module_registers_tools) only picks up modules with
# a top-level ``registry.register(...)`` expression statement. Wrapping it in
# a function or try-block silently disables the tool.
registry.register(
    name="apify_run_actor",
    toolset="web",
    schema=_APIFY_RUN_ACTOR_SCHEMA,
    handler=_handle_apify_run_actor,
    check_fn=_check_available,
    is_async=False,
    description=_APIFY_RUN_ACTOR_SCHEMA["description"],
    emoji="🤖",
)
logger.info("apify_run_actor tool registered")
