# The Roots by SVAM / SRK Infra — K-RERA pull (12 Aug 2026)

## The project
- Marketing name: "The Roots" by SVAM Realty (aka SRK The Roots, promoter
  SRK Infra Projects Pvt Ltd) — 100 × 4BHK row villas, 5.4 acres,
  Sadahalli, Devanahalli taluk (airport corridor, ~2.8 km from the
  Uganavadi subject pin 13.220644,77.675830).
- Already in the Uganavadi competitor sheet row 12 ("Srk The Roots") —
  same project, portal name vs marketing alias. If a future run searches
  "The Roots" or "SVAM", dedupe must alias it to Srk The Roots.

## RERA numbers (two registrations, same project family)
1. `PRM/KA/RERA/1250/303/PR/090925/008075` — THE ROOTS, promoter SRK
   INFRA PROJECTS PRIVATE LIMITED, Devanahalli, Bengaluru  Rural,
   APPROVED, Residential/Group Housing, detail_id 13697. Full doc set.
2. `PRM/KA/RERA/1251/446/PR/041225/008303` — The Roots by SVAM Realty
   Prime (New Launch marketing, "Off Sadahalli Main Road, Kannamangala",
   aka Mana Verdant Terraces docs). Fetched on the retry run.

## How we got the docs (worked)
- VPS datacenter IP is network-blocked by rera.karnataka.gov.in (curl
  timeout). The user confirmed the site is NOT down globally.
- Fix: route through the Hermes tunnel SOCKS
  `socks5://hermes-utilities:1000` (same path browser tools use).
  The proxy MUST be baked into the requests session in every fetch
  script (`s.proxies = {...}` in get_session) — env-var only does NOT
  survive cron/background runs (hit this: first retry ran direct,
  SITE_DOWN). PySocks required
  (`uv pip install --python /opt/hermes/.venv/bin/python PySocks`).
- First full run via `krera_download_plans.py` grabbed 105 files
  (149MB) before the client node flapped (Errno 111 connection refused).
  Key files on disk: approved Development Plan, Basement Plan, all block
  plans (2,3A-C,3D-F,4,5A-B,6,7A-C,7D), ground floor, STP Layout, CC,
  Roots DP (19.7MB), Longitude & Latitude doc, Survey ADLR sketch, Sale
  Deed, Structural Stability Cert, RERA Agreement.
- **Retry run (client node back from sleep) — `krera_retry_missing.py`
  with proxy baked in + PROJ_SPECS loop for both registrations:
  201 new docs downloaded, 0 failures.** Deleted 30 zero-byte files the
  site served. Final: 306 PDFs on disk (~301MB).
- **Everything uploaded to NDR's TMP Drive folder** "The Roots RERA
  Plans (SRK/Svam)" — 305 PDFs, ~300MB:
  https://drive.google.com/drive/folders/1N2lLp3Ed28_hbFVcApLo8Xh4bL5c5dQq
  Uploader pattern: `upload_to_tmp.py` (create/confirm subfolder under
  TMP root `18p74II2uL32sNDzDDwXzmlOUdJJOTmE-`, list existing names in
  folder, skip duplicates by name, resumable across runs, then verify
  count from Drive after — don't trust local file count).
- Priority docs NDR asked for, all present with links delivered:
  - Agreement of Sale: 55_ROOTS__RERA_Agreement__05-07-2025
    (id 1Z70rYueE94PHXGlWMvYBse3Byw-ad1zV) + 165_SL_NO_-_6_AGREEMENT
    FOR_SALE_MANA_VERDANTH (1rrP8vS9mVuJ3BRARVf4syQXFyXAeVwbd)
  - Allotment Letter: 56_Allotment_Letter_Draft
    (139-m5U9lVtoXhuHpYtc4KN7_83OHaSvd) + 94 (1Yt-BbtLpBegHI7DEboPA3tvc)
  - Project Estimation: 95_Project_Estimation_1_
    (1TG_gtImIdK4d4nspsuPUXv_5az8Tt2RA)
  - Also: Development Plan approved (1ZlgC3EQFUOaFmHD3OnBfKSEzpOVBldSf),
    Basement Plan (1TiPxsRfgmmjdjyG8suecfL3JKWXg7J8l), Longitude/Latitude
    (1m478lySHxuYblsernwVVrWpO0eN4zPUM), brochure, sale deeds, structural
    certs, BESCOM NOC.

## Watchdog
- Cron `d5faad93d736` "K-RERA The Roots watchdog" every 20m (no_agent,
  script `rera_watchdog.sh` v2): probes the site THROUGH the tunnel
  (direct probe would never fire — datacenter IP blocked), then runs the
  retry script. Silent while unreachable. Stale duplicate job
  `211d69fcc3aa` was removed.

## Key lesson (also in SKILL.md)
Proxy-test "global outage" inference is unreliable: allorigins 408 /
codetabs 522 / jina 422 all fired while the site was up — those probes
egress from IPs the site blocks. Always check with the user before
declaring the site down. Conversely, a dead tunnel (SOCKS5 err 3 /
curl 000) is NOT a dead site — the client node may be asleep and will
wake; re-probe later, don't tell NDR it's unreachable permanently.
