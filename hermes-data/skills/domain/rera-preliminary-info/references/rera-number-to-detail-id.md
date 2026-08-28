# RERA number → detail_id lookup + degraded quick-facts path

## Why you need this
K-RERA detail pages are fetched by an opaque `detail_id`, NOT the RERA string
(e.g. `PRM/KA/RERA/1251/309/PR/040426/008572`). If you only have the RERA number
or project name, you must resolve the `detail_id` from the district index first.

## Resolution recipe

**IMPORTANT POST FORMAT GOTCHA (verified 2026-08-21):** K-RERA's POST handlers reject JSON bodies. Both `projectViewDetails` and `projectDetails` require `application/x-www-form-urlencoded` content type. The JSON variants (`{"district": "..."}` / `{"action": <id>}`) silently return error pages or empty tables.

### 1. Resolve the detail_id from the district index

POST `https://rera.karnataka.gov.in/projectViewDetails` with `application/x-www-form-urlencoded`:
- `district=Bengaluru+Urban` (or `Bengaluru++Rural` with TWO spaces)
- Optional: `regNo2=<RERA_STRING>&btn1=Search` to narrow (the search-filtered response is ~32MB vs the full-district ~6MB which is JS-only with no table)

The search-filtered response contains `<table id="approvedTable">` with full rows including `<a id="<detail_id>" class="btn btn-md" title="View Project Details">`. Parse with BeautifulSoup on `table#approvedTable`.

The plain district-only POST (JSON or form-encoded) returns only the ~6MB JS autocomplete array — the DataTable rows are client-side only and BeautifulSoup finds nothing. **Always include the search params** or the response has no `<tr>`/`<td>` to parse.

### 2. Fetch the detail page

POST `https://rera.karnataka.gov.in/projectDetails` with `application/x-www-form-urlencoded`:
- `action=<detail_id>`
- Headers: `Content-Type: application/x-www-form-urlencoded`, `Referer: https://rera.karnataka.gov.in/viewAllProjects`, `X-Requested-With: XMLHttpRequest`

The JSON body `{"action": <id>}` returns HTTP 400 "Requested resource is not available" — do NOT use it.

Response is ~780KB HTML with the full detail page, tower tables, and uploaded document list. Apply the existing field extractors (flattened-text search, p.text-right sibling, tower table regex).

### 3. (Optional) Search directly by RERA number

If you already have the RERA number, POST form-encoded to `projectViewDetails` with `regNo2=<RERA_STRING>&btn1=Search&district=Bengaluru+Urban`. The response contains the full `approvedTable` with the matching row and its detail_id.

All requests MUST go through the residential SOCKS
`socks5h://hermes-utilities:1000` (baked into session `proxies`, not env-only).

## Degraded "quick facts" path — when the tunnel node is down
Verified 2026-08-20 (TVS Emerald Altura): SOCKS returned `0x03: Network unreachable`
for many minutes across many retries, AND browser `Page.navigate` also timed out.
When the node is down, no retry wins. Instead deliver the **quick facts** the user
asked for (land, towers, floors, units, RERA no) from corroborating public sources:

- Official promoter project page (e.g. `tvsemerald.com/projects/<name>`) — authoritative on configs, size, floors.
- 99acres / NoBroker project pages — repeat the RERA no, acreage, unit count.
- Channel-partner / agent sites — new-launch specifics.

Cross-check figures across 2–3 sources; if they agree → high confidence. The RERA
number itself carries a hint: `.../040426/008572` → `040426` = project applied/filed
~04 Apr 2026 (good as an indicator, not the certified issue date).

EXPLICITLY FLAG the one field you couldn't pull live from the portal (typically the
exact RERA registration certificate date / FAR sanctioned), and offer to retry when
the node returns. Do not fabricate the portal-only value.

Script pattern (worked): POST index → find detail_id → POST detail → extract via the
`label_value` / `header_block` / flat-scan extractors from `kgera_detail_v8.py`.
