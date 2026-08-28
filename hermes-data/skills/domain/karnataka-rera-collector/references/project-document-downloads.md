# K-RERA Project Plan Downloads — Worked Example (2026-08-11)

## Task class
"Find ~N recent <product-type> projects in Bangalore and download their
Karnataka RERA plans (approval plan, site plan, section, elevation plan)."
Two legs: (1) discovery on the open web, (2) RERA register lookup + PDF
download. Leg 2 may be blocked by a site-wide outage — see below.

## Discovery leg (Tavily from the datacenter IP — worked)
Queries that produced candidates:
- `row villa projects Bangalore 2025 new launch`
- `row house projects Bangalore RERA registered 2025`
- `best row villa projects Bangalore` / `row villa projects Bangalore 2026`
- per-project confirmation: `<project name> RERA number PRM`

Terms that work in search: "row villa", "row house", "townhouse" —
"row house" is the common Indian portal term; standalone-bungalow and
apartment results pollute the results, filter them out.

## The 5 projects selected (recent Bangalore row villas / row houses)
| Project | Promoter | Location | RERA (as published by aggregators) |
|---|---|---|---|
| Sattva Springs | Salarpuria Sattva | Kanakapura Rd (Kaggalipura) | PRM/KA/RERA/1251/310/PR/240724/006948 |
| Sattva La Vita | Salarpuria Sattva | off Hennur Main Rd (Byrathi) | not published anywhere — name-match |
| Assetz Earth & Essence | Assetz | North BLR (Hosahalli, Airport Rd) | PRM/KA/RERA/1251/309/PR/180621/001907 (+ 2nd phase PR/070522/004860) |
| Prestige Park Grove | Prestige | Whitefield (Kadugodi) | PRM/KA/RERA/1251/446/PR/100823/006141 |
| Ashish ANR Row House | Ashish/ANR | Whitefield East | not published — name-match |

Aggregator sources that DO expose the number: housing.com project pages
("registered under RERA with the number ..."), commonfloor, 99acres /
magicbricks listing snippets, developer-specific new-launch sites
(sattvanewlaunch.com), FAQ pages (nobroker). Developer marketing sites
(assetzproperty.com, prestigesouthernstar.info) usually do NOT.

## Site-down verification recipe (site down ≠ our IP blocked)
2026-08-11 rera.karnataka.gov.in was down for everyone. Evidence set:
- `curl https://rera.karnataka.gov.in/` from VPS AND via the SOCKS tunnel
  (AGENT_BROWSER_PROXY=socks5://hermes-utilities:1000) both time out;
- public fetch proxies return Cloudflare **522** (origin unreachable from
  Cloudflare's edge too):
  `https://api.allorigins.win/raw?url=<url>` and
  `https://api.codetabs.com/v1/proxy?quest=<url>`;
- `https://r.jina.ai/<url>` times out ("TimeoutError: page.goto");
- Tavily `/extract` returns `"Failed to fetch url"` in failed_results.

Google/other sites still 200 through the same paths → general egress is
fine; the target is down. Once confirmed:
- stop hammering; run the discovery/aggregator leg instead;
- Wayback availability API (`http://archive.org/wayback/available?url=...`)
  tells you what's cached — HTML pages only, `/download_jc?DOC_ID=` PDFs
  are almost never archived;
- arm the cron watchdog (scripts/rera_plan_watchdog.sh) and let it fire
  the downloader when the site returns.

## Cron `no_agent` watchdog semantics (Hermes)
- non-empty stdout → delivered verbatim; EMPTY stdout → silent tick;
  non-zero exit → error alert. Perfect for "do nothing until X is back".
- script path must be a bare filename under the Hermes scripts dir
  (`/data/hermes/scripts/`); absolute paths are rejected.
- schedule `"20m"` = ONE-SHOT (fires once in 20 min); `"every 20m"` =
  recurring. Use "every …" for watchdogs, and set an explicit `repeat`
  bound so a long outage doesn't poll forever.
- a `.done` marker file makes the watchdog self-silencing after success
  so a recurring job doesn't re-report every tick.

## Env/API notes (this host)
- No `/opt/hermes/.env` here. Keys are in the process env as suffixed
  variants: `TAVILY_API_KEY_2` / `_3`, `APIFY_API_KEY` / `_2` / `_3`,
  `FIRECRAWL_API_KEY_2` / `_3`. Verify with `env | grep -iE 'tavily|apify'`.
- `execute_code`'s venv may not inherit these vars (401 Unauthorized on
  Tavily) while the terminal does — run Tavily calls from terminal python
  (`urllib`/curl), not execute_code.
- Tavily search: `POST https://api.tavily.com/search` with
  `Authorization: Bearer <key>`; extract: `POST /extract` with
  `{"urls": [...]}` — failed_results["error"] distinguishes block vs
  unreachable.
