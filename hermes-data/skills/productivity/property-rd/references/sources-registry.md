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
  Reachability: direct | web_search_snippet | apify | browser_cloud | blocked
  Search template: <url or query pattern that works>
  Yields: listings | project-announcements | price-discussion | suggested-projects
  Found: <date + belt, e.g. 2026-08 Anekal run>
  Notes: <one-liner>
```

## Property portals (reachability tested Aug-2026 from the VPS)

### Directly accessible (HTTP 200 via curl)
- **NoBroker** (nobroker.in) — plot/land listings with price + sqft; locality
  avg price/sq-yard. Search template: `https://www.nobroker.in/property/sale/bangalore/land?searchParam=...`
- **99sqft** (99sqft.com) — direct.
- **Propzilla** (propzilla.in) — direct.
- **QuikrHomes** (quikrhomes.com) — direct.
- **CrazyAssets** (crazyassets.com) — investment guides with per-sqft bands.
- **Homznspace** (homznspace.com) — per-project price tables.
- **PropertyCrow** (propertycrow.com) — per-project floor-plan price tables.
- **Proplocators** (proplocators.com) — per-project per-sqft rates.
- **HousingMan** (housingman.com) — per-project base price.
- **Bulwark / official builder sites** (e.g. bulwarkthewoodlandforest.in) —
  locality rate tables and plot pricing PDFs.
- **360Realtors, Regrob, RespaceInfra, LavishLiving, UrbanFlatsHub** —
  project microsites with price tables + market guides.

### Blocked from VPS (403/406 — Apify actor or Google snippet)
- **99acres** (99acres.com) — Apify actor `codingfrontend/99acres-projects-search-scraper`
  (id `hHadmAwXCpNrsHH2O`); locality-first searchUrls pattern:
  `https://www.99acres.com/{plots|villas|apartments|new-projects}-in-<locality>-<zone>-ffid`.
  Rate pages `property-rates-and-price-trends-in-<loc>-prffid` via Google snippet.
- **MagicBricks** (magicbricks.com) — rate pages `Property-Rates-Trends/...-<loc>-in-Bangalore`
  via Google snippet; Apify `magicbricks-99acres` preset is BROKEN (stale actor).
- **Housing.com** (406) — price-trends pages indexed by Google.
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

- **Karnataka RERA** — kanarera.karnataka.gov.in (project registration,
  developer, status). **Deferred workstream** — NDR wants this wired later.
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
