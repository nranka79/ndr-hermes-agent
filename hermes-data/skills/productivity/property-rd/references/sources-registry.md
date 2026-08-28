# Sources Registry — Known Property Sources of Truth (India)

The knowledge base of every portal / forum / group / social channel that can
surface property listings, project announcements, or area discussion.

**How to use (mandatory):**
1. At the START of any R&D run, read this file. It is the source inventory
   for the discovery phase — portal search, Google search, and the social
   leg all start from here.
2. Whenever the run discovers a NEW source that yielded listings or
   discussion (a portal, a Reddit sub, a Facebook group, an Insta handle, a
   forum, a YouTube channel), **append it here** with the fields below. This
   file is the growing "sources of truth" database — the skill is only as
   good as this registry.
3. Never delete an entry without NDR approval (a source that dies today may
   come back, and its reachability history matters).

## Entry format

```
- Name: <human name>
  Type: portal | reddit | facebook | instagram | forum | telegram | youtube | other
  URL: <base url>
  Reachability: direct | tunnel | web_search_snippet | apify | browser_cloud | blocked
  Search template: <url or query pattern that works>
  Yields: listings | project-announcements | price-discussion | suggested-projects
  Found: <date + belt, e.g. 2026-08 Anekal run>
  Notes: <one-liner>
```

## Property portals (reachability tested Aug-2026 from the VPS)

### Tunnel-reachable (HTTP 200 via `curl -x socks5h://hermes-utilities:1000` or Playwright with that SOCKS — verified 2026-08-12 Hosur run)
- **MagicBricks** (magicbricks.com) — server-rendered JSON-LD + card text.
  URL patterns: `/villa-for-sale-in-<loc>-pppfs` (carries geo),
  `/property-for-sale-in-<loc>-pppfs` (all types), paginate `?page=N`.
  NOT `/plots-for-sale-in-<loc>-pppfs` (404). Full recipe:
  real-estate-portal-research `references/tunnel-portal-scraping-recipes.md`.
  The old `magicbricks-99acres` Apify preset is BROKEN (stale actor).
- **NoBroker** (nobroker.in) — plot/land listing with price + sqft; the
  SEO pages (`/villas-for-sale-in-<loc>_<city>`) render cards client-side:
  Escape the login popup, read body text. API
  `/api/v3/multi/property/BUY/filter` needs a locality token — skip it.
- **rera.tn.gov.in** — see Official/gov sources below (tunnel verified 200).

### Blocked from VPS (403/406 — Apify actor or Google snippet)
- **99acres** (99acres.com) — Akamai browser fingerprinting; 403 even via
  the residential tunnel (verified 2026-08-12) — curl AND Playwright.
  Apify actor `codingfrontend/99acres-projects-search-scraper`
  (id `hHadmAwXCpNrsHH2O`); locality-first searchUrls pattern:
  `https://www.99acres.com/{plots|villas|apartments|new-projects}-in-<locality>-<zone>-ffid`.
  Rate pages `property-rates-and-price-trends-in-<loc>-prffid` via Google snippet.
- **Housing.com** (406 direct; tunnel render not yet verified) — price-trends
  pages indexed by Google.
- **CommonFloor** (403, Quikr-owned), **SquareYards** (403), **Makaan** (406),
  **Sulekha Properties** (403), **PropTiger** (404/effectively dead).

### Google Maps / Places
- **Places crawler** (Apify `compass~crawler-google-places`, id `nwua9Gu5YrADL7ZDj`)
  — POI coords, project pins, nearby discovery. ALWAYS pass locationQuery +
  countryCode (see area-research pitfalls — town anchors are zero-result traps).

## Community / discussion sources

### Reddit groups (search via `web_search("site:reddit.com <project|area>")`
or old.reddit search; results are discussion, pricing chatter, launch news)
- r/bangalore — city-wide real estate discussion
- r/indianrealestate — national real estate discussion
- r/RealEstateIndia — national
- r/Bengaluru (alias community)
- Search template: `https://www.reddit.com/search/?q=<area>+property` then
  filter to subreddits above; `web_search("site:reddit.com/r/indianrealestate <project>")`

### Facebook groups (login-walled — discovery via Google snippet
`site:facebook.com/groups <area> property`; content via browser_use_cloud
when a group is public-ish)
- (none logged yet — first run that finds a group, append here)

### Instagram (login-walled — snippets via `site:instagram.com <area> realestate`;
hashtag feeds via browser_use_cloud or apify instagram actors)
- Search template: `https://www.instagram.com/explore/tags/<area>realestate/`
- (none logged yet — append builder/broker handles that advertise belt projects)

### Forums / communities
- Team-BHP property threads — price/legal discussion (snippet-reachable)
- Indian Real Estate Forum (indianrealestateforum.com) — listing + discussion
- (append more as found)

### YouTube (project walkthroughs, launch vlogs — snippet searchable)
- Search template: `web_search("site:youtube.com <project> walkthrough OR review")`

## Official / gov sources (see also property-pricing-sources references)

- **Karnataka RERA** — rera.karnataka.gov.in (project registration,
  developer, status; via karnataka-rera-collector — index by district,
  enrich per project; VPS needs the residential tunnel, see that skill).
  NOT kanarera.karnataka.gov.in (wrong domain, corrected Aug-2026).
- **Tamil Nadu RERA** — rera.tn.gov.in (registered-project register).
  Three categories under Registrations → Projects → Registered Projects
  in Tamil Nadu: Building (`/building/list-project`), Layout
  (`/layout/list-project`), Regularisation of Layout
  (`/regularisation/list-project`). Each has Online registrations plus
  Offline registrations organized year by year; the ONLINE registers are
  server-rendered tables at `/registered-building/tn`,
  `/registered-layout/tn`, `/registered_reglayout` (NOT `-list-projects`
  slugs — those 404). District code TN/30 = Hosur/Krishnagiri. Full
  recipe: property-rd `references/tn-rera-registers.md`. VPS egress needs
  the residential tunnel (`socks5://hermes-utilities:1000`) — direct IP
  and fetch proxies blocked, tunnel verified 200 2026-08-12.
  Added: 2026-08-12 NDR (corrected 2026-08-12).
- **SEZ India** — sezindia.gov.in "List of Notified SEZs" PDF (authoritative
  for SEZ inventory; search it, don't guess).
- **Kaveri 2.0 / IGR guidance values** — per-acre land benchmarks
  (property-pricing-sources references/karnataka-land-price-govt-sources.md).

## Discovery rules

- New portal found while Googling for listings → append with search template.
- New Reddit sub / FB group / Insta handle that surfaces projects in a belt
  → append; these ARE the community leg for future belts.
- Mark reachability honestly (direct / snippet / apify / blocked) — the
  reachability table in property-pricing-sources SKILL.md is the operational
  truth and must match this registry.

## Aug-2026 Uganavadi run additions

- **devanahallinewprojects.com** — Type: portal (project-announcements).
  Reachability: direct. Yields: new launches, price lists (Bulwark Township
  Rs 85L-1.9Cr, The Woodland Forest Rs 75L-1.8Cr, Arvind Orchards Rs 85L).
  Found: 2026-08 Uganavadi run.
- **embassysprings.org** — Type: portal (builder microsite). Reachability:
  direct. Yields: project-announcements (Embassy Springs from Rs 61L).
  Found: 2026-08 Uganavadi run.
- **godrej.bangaloreupcomingprojects.com** — Type: portal. Reachability:
  direct. Yields: project-announcements (Godrej Shettigere from Rs 1.18 Cr).
  Found: 2026-08 Uganavadi run.
- **thebrigaderedearth.in** — Type: portal (builder microsite). Reachability:
  direct. Yields: gated-plot comparisons (Brigade Red Earth 380 plots/17 ac,
  Rs 86.4L; vs Brigade Oasis/Godrej Reserve/Sobha Chartered Windsong/Embassy
  Springs/Birla Trimaya). Found: 2026-08 Uganavadi run.
- **aurumproptech.in/pulse/localities/** — Type: portal (locality pulse).
  Reachability: direct. Yields: locality rates/pros-cons (Uganavadi page).
  Found: 2026-08 Uganavadi run.
