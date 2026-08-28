---
name: bangalore-metro-research
description: "Bangalore Metro / Namma Metro infrastructure research for real-estate decisions — all lines (operational, under-construction, proposed), station lists, corridor alignments, approval status, route-map images, and KML/GeoJSON deliverables. Triggers: 'which metro line serves X', 'proposed metro routes', 'metro connectivity for <project/locality>', 'Sarjapur-Electronic City metro', 'metro station near <place>', 'get me the metro maps / KML', suburban rail (K-RIDE) and Metrolite questions."
metadata:
  hermes:
    tags: [bangalore, metro, namma-metro, transit, real-estate, infrastructure, kml, maps]
    related_skills: [location-research, bengaluru-town-planning, research-web-tools]
version: 1.0.0
author: NDR + Hermes
license: MIT
---

# Bangalore Metro Research

Bangalore Metro (Namma Metro) is a top real-estate value driver for DRAAS work —
metro connectivity questions recur for land deals, project dossiers, and
location research. This skill covers the class: which line serves a corridor,
what's proposed/approved/under construction, station lists, status, maps, and
KML deliverables.

**Network snapshot (lines, stations, statuses, the Sarjapur–Attibele answer):
`references/bangalore-metro-network-2026.md`.** Read it first for any
"which line / proposed route" question — it saves most of the search work.

## Trigger Conditions

- "Which metro line serves <locality/project>?" / "is there a metro near X?"
- "Proposed metro routes" / "metro alignment" / "metro connectivity for <area>"
- "Get me the metro maps / route images / KML files"
- Any question about a specific corridor (e.g. Sarjapur Road, Electronic City,
  Hosur Road, ORR, Bannerghatta Road, Whitefield, Airport line)
- Metrolite / suburban rail (K-RIDE) questions (same sources, different agency)

## Workflow

1. **Consult the network reference first** — `references/bangalore-metro-network-2026.md`
   has line inventory, the Red Line (Phase 3A) full station list, the 73-km
   Kalena Agrahara–Kadugodi corridor, Bommasandra–Attibele extension, and the
   Phase 4 feasibility corridors. Verify dates/status with a fresh search if the
   question is time-sensitive.
2. **Get the authoritative station list** for the corridor in question:
   - Wikipedia line pages via the wikitext API (cleanest, fastest):
     `https://en.wikipedia.org/w/api.php?action=parse&page=<Line_Name_(Namma_Metro)>&prop=wikitext&format=json&formatversion=2`
     The `== Stations ==` section has the full ordered list + interchange notes.
   - Metro Rail Guy (`themetrorailguy.com/bangalore-metro-<phase>-information-map-status-updates`)
     has route/status/station pages and cost figures; page text is extractable
     with a UA header (their images are not inline — don't waste time scraping
     `<img>` from their pages for maps).
3. **Verify status from recent news** — Wikipedia infobox status can be stale
   or internally contradictory (Red Line infobox said "Under Construction" while
   the article said "awaits nod"). Cross-check Deccan Herald / The Hindu /
   News18 via search snippets or Tavily extract.
4. **Collect map images** — the route maps doing the rounds are on X posts;
   retrieve them WITHOUT auth via the syndication API (see
   `research-web-tools` → `references/x-syndication-media-retrieval.md`):
   `https://cdn.syndication.twimg.com/tweet-result?id=<tweet_id>&token=a&lang=en`
   → `mediaDetails[].media_url_https` gives direct `pbs.twimg.com` image URLs.
   Known-good accounts: @ever_pessimist, @ChristinMP_, @DeccanHerald,
   @blrmetrotracker, @WF_Watcher, @GunjurCharan.
5. **Deliverable: schematic KML/GeoJSON** when the user wants the routing on a
   map:
   - Geocode each station/locality via OSM Nominatim search
     (`https://nominatim.openstreetmap.org/search?format=json&q=...`), ~1.2 s
     delay between calls to respect the rate limit; expect some misses
     (small villages) — fill estimates and mark them `(approx)`.
   - Build a KML Document with one LineString per corridor + Point placemarks
     per station, and a matching GeoJSON FeatureCollection.
   - **Label it SCHEMATIC** in the file description: station points are
     locality-geocoded, corridor lines are straight segments between anchors —
     the official BMRCL DPR alignment is NOT public for proposed lines.
   - Save under a dated research folder (e.g. `/opt/data/metro_research/` in
     this deployment) with the downloaded images and a README listing source URLs.

## Search Stack (this deployment)

- `web_search`/`web_extract` tools are NOT exposed as agent tools here; instead
  call the **Tavily API directly from terminal-run python** using
  `TAVILY_API_KEY_2` (env keys are NOT inherited inside the execute_code
  sandbox — run via `python3 script.py` in terminal, writing scripts with
  write_file). POST to `https://api.tavily.com/search` (query) and
  `https://api.tavily.com/extract` (page content when the site 403s).
- **Datacenter IP blocks**: The Hindu, MagicBricks, Times Now, News18 return
  403 to plain fetch → use Tavily `/extract` (worked for MagicBricks; The Hindu
  is paywalled so fall back to snippet-level info). Karnataka gov sites
  (bbmp/UDD/BMRCL) need Apify residential proxies per `bengaluru-town-planning` P4.
- Wikipedia and themetrorailguy.com fetch fine directly with a UA header.

## Pitfalls

- **"Ratibalei"-style transliterations**: NDR's locality names are phonetic
  ("Ratibalei" = **Attibele**, "Dunnasandra" = Dommasandra, "Muthanal" =
  Muthanallur). Map the name to the real locality before searching.
- **Press station lists are loose**: route order in news/Instagram summaries is
  frequently jumbled (e.g. "Attibele → Sarjapur → Dommasandra" while the DPR
  order differs). Trust the Wikipedia wikitext table or Metro Rail Guy order;
  treat press order as directional only.
- **"Phase 3" is ambiguous**: Phase 3 (approved 2024) = JP Nagar 4th
  Ph–Kempapura (ORR) + Hosahalli–Kadabagere; Phase 3A (sometimes "Red Line") =
  Hebbal–Sarjapur, state-approved Dec 2024, still awaiting GoI nod; the 73-km
  Kalena Agrahara–Kadugodi line is a Phase-4-era feasibility proposal, DPR not
  sanctioned. Don't conflate them.
- **Don't claim alignment precision for proposed lines** — no official
  alignment exists until the DPR is published. Say "schematic/approximate".
- **Wikipedia infobox status can be wrong** (see Workflow step 3).

## References

- `references/bangalore-metro-network-2026.md` — network snapshot: operational /
  under-construction / proposed lines, Red Line station list, 73-km corridor,
  Sarjapur–Attibele–Electronic City answer, source + image URLs.
