---
name: research-web-tools
description: "Research and web tools umbrella — domain intelligence (passive OSINT), web search (DuckDuckGo), blog/RSS monitoring, arXiv paper search, ML paper writing, and Parallel CLI. Covers passive reconnaissance, content monitoring, academic research, and web scraping."
umbrella: research-web-tools
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Research, OSINT, Web Search, RSS, arXiv, Papers, Parallel CLI, Domain Intelligence, Content Monitoring, B2B Lead Generation]
---

# Research & Web Tools — Umbrella

This umbrella covers web research, passive intelligence gathering, content monitoring, and academic research tools.

## Decision Tree

```
What research task?
├── Passive domain reconnaissance (no API keys)
│   └── → Domain Intel (references/domain-intel.md)
│         Subdomains, SSL, WHOIS, DNS, availability checks.
├── Freelance marketplace research (Upwork/Fiverr profiles)
│   └── → Fiverr Research (references/fiverr-research.md)
│         Bot-safe browser workflow — use search box, not URL params.
├── Business entity due diligence / company investigation
│   └── → Company Due Diligence (references/company-due-diligence.md)
│         Systematic methodology: identity confirmation, website recon,
│         management credential analysis, regulatory compliance checks,
│         group/parent cross-reference, red flag assessment, report compilation.
│         No paid APIs — terminal + curl based.
├── Comprehensive website tech-stack analysis
│   └── → Website Tech-Stack Analysis (references/website-tech-stack-analysis.md)
│         Multi-dimensional: text stack, artwork/visuals, visual language/style,
│         page layout/composition, motion/animation, tracking/SEO.
│         curl-based extraction — no browser needed. Covers CMS fingerprinting,
│         font analysis, image format audit, animation engine detection, colour
│         palette inference, layout mapping, and coding-agent prompt generation.
├── Indian local services / business research
│   └── → India Local Services Search (references/india-local-services-search.md)
│         Directory-based search for Indian cities: JustDial, Sulekha,
│         BookMyPlayer, MyTribe. Bypasses Google/Bing JS obfuscation
│         and captchas. Covers sports coaching, gyms, clinics, tuition,
│         and general services.
├── Freelance / contractor talent research (specialized Indian tech skills)
│   └── → Freelance Talent Research (references/freelance-talent-research.md)
│         Two sourcing paths: X search for self-promoting freelancers + direct-to-vendor
│         partner networks (Exotel, Ozonetel). Platform limitation notes (Upwork/Fiverr
│         block scraping). Budget benchmarks, screening checklist, and job post template.
│         Covers telephony / AI voice / WhatsApp API / IVR / CCaaS consultants in India.
├── Reverse phone lookup / "who owns this +91 number" social footprint
│   └── → Phone Number OSINT (references/phone-number-osint-india.md)
│         Free-source ladder: DDG-via-Jina (3 number formats), Google News RSS,
│         Truecaller web (login-walled name), business-directory site: queries.
│         Zero hits across all = no public social/web footprint.
├── Free web search (no API key)
│   ├── → DuckDuckGo Search (references/duckduckgo.md)
│   │     Text, news, images, video via `ddg` CLI.
│   │     Also supports freelancer marketplace research
│   │     (Upwork/Fiverr profiles via site: operators).
│   ├── → DuckDuckGo Lite — Browser Search (references/duckduckgo-lite-browser-search.md)
│   │     Browser-based DDG Lite search when Firecrawl/web_search is down
│   │     or Google/Bing block with CAPTCHAs. Navigate browser to
│   │     lite.duckduckgo.com/lite/, extract URLs from `uddg=` redirect
│   │     params via browser_console. Works for finding listing page URLs
│   │     on MagicBricks, 99acres, SquareYards, and other portals.
│   │     Includes real estate portal URL pattern reference.
│   └── → Jina Reader (references/jina-reader.md)
│         Zero-config web access via `curl https://r.jina.ai/URL`.
│         Clean Markdown output, no browser required. Also works as
│         a search proxy via DuckDuckGo Lite. Covers: public web pages,
│         X/Twitter public profiles, GitHub releases, Reddit threads.
│         Installed by Agent Reach.
├── Find product/software UI screenshots — visual research
│   └── → Product UI Screenshot Research (references/product-ui-screenshot-research.md)
│         Bing Image Search workflow for when the user wants to SEE what a
│         software product's UI looks like. Covers: navigating Bing Images
│         from the VPS (Google Images is captcha-blocked), cycling results,
│         capturing screenshots via browser_vision, delivering via MEDIA: path.
│         Trigger: "what does [product] look like", "show me screenshots of",
│         "can you get me the UI of".
├── Reverse phone lookup / "who owns this +91 number" social footprint
│   └── → Phone Number OSINT (references/phone-number-osint-india.md)
│         Free-source ladder: DDG-via-Jina (3 number formats), Google News RSS,
│         Truecaller web (login-walled name), business-directory site: queries.
│         Zero hits across all = no public social/web footprint.
├── Browser tool / tunnel egress debugging (ERR_TUNNEL_CONNECTION_FAILED)
│   └── → Browser Tool vs Local Socks (references/browser-tool-local-socks.md)
│         browser.cloud_provider=browser-use sends browser_navigate to CLOUD CDP
│         (cdp.browser-use.com), not the local socks — tool error ≠ tunnel down.
│         Fix: hermes config set browser.cloud_provider local. Manual agent-browser
│         verification recipe, residential-router file location, daemon-kill pitfall.
├── Monitor blogs/RSS feeds for updates
│   └── → Blogwatcher (references/blogwatcher.md)
│         RSS/Atom monitoring, change detection.
├── Research an Indian government e-governance system's technical requirements — platform, biometric hardware, software dependency
│   └── → Indian Government E-Registration Tech Requirements (references/indian-government-e-registration-tech-requirements.md)
│         Methodology for researching whether a government portal works cross-platform (Chromebook/Linux/Windows),
│         including the critical Aadhaar RD Service constraint (Windows-only biometric middleware),
│         key questions to ask (web vs installed, device types, browser compatibility),
│         source discovery through Google News RSS, and step-by-step process documentation.
│         Covers Tamil Nadu STAR 3.0 / TNREGINET presence-less registration as a worked example.
│         Use when the user asks "can I use a Chromebook for TN property registration", "what biometric
│         devices do I need", "is this e-governance system web-only or needs installed software".
│   └── → Tamil Nadu STAR 3.0 / TN Data Reference (references/tamil-nadu-star-3-registration-system.md)
│         Tamil Nadu-specific data reference: Mantra device models and prices, RD Service architecture,
│         portal accessibility status, confirmed mobile app limitations (search-only, no registration),
│         Aadhaar OTP alternative confirmed from portal FAQ, 4 PDF user manuals, daily Webex training
│         for builders at 2PM, TCS software helpline, 5-step process from portal homepage.
│         Use when the user asks about TN presence-less registration specifically — "what hardware do I
│         need for TN", "how does mobile work in TN", "can I do TN registration on a phone".
├── Research Bangalore real estate statutory charges (BBMP/BDA betterment, improvement fees)
│   └── → BBMP Betterment Charges (references/bbmp-betterment-improvement-charges.md)
│         KMC Act 1976 legal framework, fee stages (plan sanction + OC), rate structure,
│         BBMP vs BDA distinction, relevant circulars and court orders.
│         Use when the user asks about betterment charge, improvement charge, BBMP fee,
│         sanction fee, or statutory levies on Bangalore property.
├── Research Bangalore urban rail (metro OR suburban rail) for land/real-estate context
│   ├── → Namma Metro knowledge bank (references/bangalore-metro-network.md)
│   │     All 8 metro lines + status, Red Line Phase 3A station list, Yellow Line +
│   │     Attibele extension, 72 km corridor, Sarjapur–Rathibele–Attibele facts.
│   └── → BSRP Suburban Rail knowledge bank (references/bangalore-suburban-rail-bsrp.md)
│         K-RIDE Bengaluru Suburban Railway: 4 corridors (Sampige/Mallige/Parijaata/
│         Kanaka), station lists, K-RIDE doubling projects, RLDA context, DPR PDF
│         location, and the R&D>Bangalore>Metro Drive folder (KML pack).
│         Use when the user asks about suburban rail, K-RIDE, railway station
│         integration, or wants metro+rail KML files on Drive.
├── Extract YouTube video metadata (title, description, chapters) without browser or transcript API
│   └── → YouTube Metadata Extraction (references/youtube-metadata-extraction.md)
│         Curl-based fallback when browser is down and youtube_transcript_api is IP-blocked.
│         oEmbed API for title/author → ytInitialData scrape for full description and chapters.
├── Find REAL YouTube video links for a topic (training programs, how-to guides, form demos)
│   └── → YouTube Video Link Sourcing (references/youtube-video-link-sourcing.md)
│         Browser go to youtube.com/results?search_query=... then console-extract
│         `a#video-title` hrefs → clean to watch?v=<ID> (strip &pp/&t). Never fabricate IDs.
│         Parallel-subagent pattern per category; prefer full-length instructional over Shorts.
│         Use when Tavily is down or per NDR no-API directive and a deliverable needs VERIFIED links.
├── Retrieve full text + embedded images from an X/Twitter post WITHOUT auth (no OAuth/API key)
│   └── → X Syndication Media Retrieval (references/x-syndication-media-retrieval.md)
│         cdn.syndication.twimg.com/tweet-result?id=<id>&token=a&lang=en → JSON with
│         text + mediaDetails[] (direct pbs.twimg.com image URLs). Resolve tweet IDs
│         from x_search results or URLs in articles; download images directly.
├── Monitor X/Twitter, LinkedIn, Reddit, or patient forums for medical research discussions
│   └── → Social Media Medical Monitoring (references/social-media-medical-monitoring.md)
│         Platform-by-platform setup: X/Twitter via xurl CLI (OAuth 2.0), LinkedIn via browser
│         automation (no public search API — use Apify/PhantomBuster for scale), Reddit via curl/PRAW
│         (free, 60 req/min), patient forums via browser tools, plus complementary research
│         databases (ClinicalTrials.gov, PubMed). Covers auth, rate limits, pitfalls, and cron
│         job patterns for recurring multi-platform monitoring.
├── Research a drug's safety profile, side effects, and monitoring requirements
│   └── → Pharmaceutical Drug Safety Research (references/pharmaceutical-drug-safety-research.md)
│         Browser-based extraction from Drugs.com ASHP monograph + NCI + DailyMed.
│         Covers organ-specific toxicity, pretreatment screening, patient monitoring,
│         dose escalation criteria, and combination therapy considerations.
├── Research a product's specifications (phone, gadget, device) via Wikipedia
│   └── → Wikipedia Product Research (references/wikipedia-product-research.md)
│         Two-phase extraction: Wikipedia API `prop=extracts` for full article plaintext
│         → mobile-page infobox regex for structured specs (dimensions, weight, OS, chipset,
│         display, battery, camera, multi-currency pricing, availability). Works when Tavily,
│         Apify, GSMArena curl, and browser tools are all blocked. Includes foldable-specific
│         dimension parsing (per-fold-state depth), currency conversion tips, and known
│         block/survival behavior for 91mobiles, Notebookcheck, Google search curl.
├── Deep-dive into a specific scientific study or claim — trace source studies, explain mechanisms, assess evidence quality, translate to practical action
│   └── → Scientific Research Deep-Dive (references/scientific-research-deep-dive.md)
│         Multi-phase workflow: initial summary (Phase 1) → source study identification (Phase 2A) →
│         evidence quality assessment (Phase 2B) → mechanism/pathway explanation (Phase 2C) →
│         category differentiation within labels (Phase 2D) → practical food/action-level translation (Phase 3).
│         Covers nutrition, longevity, and medical research. Handles the "summarize → elaborate" pattern
│         where the user pushes for deeper mechanism understanding and source verification.
├── Run a clinical/medical literature search (ad-hoc, single source)
    └── → PubMed Clinical Research (references/pubmed-clinical-research.md)
          Ad-hoc search via PubMed E-utilities API: query construction,
│         abstract extraction, rate limiting, result interpretation.
│         Do NOT use for automated ongoing monitoring.
├── Check pre-compiled clinical evidence on a specific drug-safety topic (e.g. ibuprofen + asthma in children)
│   └── → NSAID-Asthma Children Evidence Bank (references/nsaid-asthma-children-evidence.md)
│         Pre-researched evidence bundle with 5 PMIDs, full abstract summaries, NERD mechanism
│         explanation, prevalence data (2-5% children), practical assessment framework, and
│         recommendation template. Saves re-running PubMed searches for repeat family-medical questions.
├── Research treatment options for a specific condition (multi-source — clinical trials + literature + social media)
│   └── → Clinical Trials Research (references/clinical-trials-research.md)
│         Multi-source systematic scan: ClinicalTrials.gov API v2 + PubMed E-utilities +
│         attempted Reddit/X scan. Structured output with NCT IDs, PMIDs, direct links,
│         and evidence-tiered recommendations. Handles the parallel-scan-then-dive pattern
│         for rare diseases, specific mutations, and novel combination therapies.
│         Includes full ClinicalTrials.gov v2 API reference, PubMed pitfalls (nested quotes),
│         and a compile-phase template for the final report.
├── Research an Indian court case / find case numbers (High Court, Supreme Court)
│   └── → Indian Legal Case Research (references/indian-legal-case-research.md)
│         CDJ Law Journal, Karnataka HC judgment portal, Google News RSS,
│         case number naming conventions, worked examples.
├── B2B lead generation / contact database research (multi-channel outreach prep)
│   └── → B2B Lead Database Research (references/b2b-lead-database-research.md)
│         Multi-channel contact research across web, Twitter, LinkedIn for a target industry/location.
│         Parallel subagent dispatch, data extraction (company name, contact, designation, handles, email),
│         outreach message generation per channel (email vs LinkedIn vs Twitter), Google Sheet delivery.
├── Set up a self-growing research monitor (cron + source tracker sheet + cumulative recommendations doc)
│   └── → Medical Research Monitor (references/medical-research-monitor.md)
│         Weekly cron-based scan across clinical trials, PubMed, Reddit, regulatory agencies,
│         and patient organizations. Tracks sources in a spreadsheet, auto-discovers new ones,
│         accumulates evidence-backed recommendations in a growing Google Doc.
│         Supports two-track monitoring (condition + genetic variant VUS).
├── Book a healthcare appointment at an Indian hospital (browser-based)
│   └── → Healthcare Appointment Booking (references/healthcare-appointment-booking.md)
│         Browser workflow: DuckDuckGo discovery → hospital website modal handling →
│         Practo fallback → user confirmation. Covers the browser_console + JS
│         technique for elements hidden from the accessibility tree.
├── Analyze a large PDF legal judgment / court order (multi-agent)
│   └── → Multi-Agent PDF Judgment Analysis (references/multi-agent-pdf-judgment-analysis.md)
│         Parallel agents analyze sections → structured Google Doc summary
│         with paragraph-level citations → filed alongside source PDF on Drive.
├── Find academic ML/AI papers on arXiv
│   └── → arXiv Search (references/arxiv.md)
│         Keyword, author, category, paper ID search.
├── Write a publication-ready ML/AI paper
│   └── → ML Paper Writing (references/ml-paper-writing.md)
│         NeurIPS/ICML/ICLR format, section templates.
├── Research Indian pre-IPO/unlisted share investments (bonus, IPO valuation, return scenarios)
│   └── → Indian Pre-IPO Unlisted Stock Research (references/indian-pre-ipo-unlisted-stock-research.md)
│         Gmail thread extraction → corporate action check → grey market pricing → IPO status →
│         return scenario calculation. Covers NSE and similar unlisted equity.
├── Research Indian passport / government ID procedures (name changes, document rectification, deletion of spouse name)
│   └── → Indian Passport & ID Procedure Research (references/indian-passport-id-procedure-research.md)
│         Source hierarchy (official portal → VFS PDFs → consulate pages → advisory sites → forums),
│         key distinction between "change in personal particulars" vs "full name change" vs "name mismatch",
│         Section 4 of VFS Name Change Affidavit (what does NOT require newspaper/gazette),
│         PSK vs RPO authority escalation, senior citizen specifics, widow/deceased spouse name deletion.
├── Research Indian government schemes / agricultural subsidies
│   └── → Indian Government Scheme Research (references/indian-government-scheme-research.md)
│         Workflow when .gov.in sites are blocked or JS-rendered. Covers: 403 errors, Next.js
│         hydration portals, browser engine failures. Fallback tiers: subagent delegation →
│         PIB press releases → academic portals (TNAU, ICAR, IFGTB) → third-party aggregators.
│         Key data extraction structure for any subsidy scheme. Cross-reference pattern to
│         verify numbers from multiple sources.
├── Check LIVE status on an Indian government portal (RERA, DTCP, eCourts, MCA, land records)
│   └── → Indian Government Portal Geo-block Diagnosis (references/indian-government-portal-geoblock-diagnosis.md)
│         When the portal won't load at all (curl TCP timeouts, browser ERR_TIMED_OUT /
│         ERR_TUNNEL_CONNECTION_FAILED, 502 from their WAF proxy). Diagnose the geo-block in
│         ~2-3 min (DNS → curl http+https → browser → one proxy round → search/wayback/urlscan),
│         then HAND OFF to the user's Indian-IP phone instead of looping retries. Never
│         fabricate portal status; interpret the user's screenshot instead. Verify the real
│         domain first (e.g. www.tnrera.in is parked; rera.tn.gov.in is real).
├── Research Indian residential sales data for a city / "units sold 20XX" (esp. tier-2)
│   └── → India Residential Sales Data Sources (references/india-residential-sales-data-sources.md)
│         Coverage matrix (Anarock/KF/CBRE top metros only; PropEquity = tier-2 city-level),
│         PropEquity release cadence + restatement gotcha, Vizag & 15-city 2024-25 numbers,
│         Jina+DDG `uddg=` parse recipe for news-article numbers.
├── Find Indian government officer contact details (District Registrar, Tahsildar, DEO, State Dept officers)
│   └── → Indian Govt Officer Contact Lookup (references/indian-govt-officer-contact-lookup.md)
│         District vs State department architecture: district .nic.in whos-who only has Collector/SP/DRO;
│         state department officers (District Registrar, DR Co-op, etc.) live on state department portals
│         (tnreginet.gov.in etc.) which are often geo-blocked from VPS. DRO office as referral path.
│         Verified source matrix (Aug 2026).
├── Run parallel CLI tasks / web scraping
    └── → Parallel CLI (references/parallel-cli.md)
          Parallel curl, web scraping, batch operations.
```

## Sub-Skill Reference

| Skill | Task | Key Feature |
|-------|------|-------------|
| `references/company-due-diligence.md` | Company investigation / business entity due diligence | Systematic methodology: identity confirmation, website recon, management analysis, regulatory checks, group cross-reference, red flag assessment |
| `references/website-tech-stack-analysis.md` | Comprehensive website analysis | Text stack, artwork/visuals, visual language/style, page layout, motion/animation, tracking/SEO, coding-agent prompt generation — all curl-based |
| `references/indian-legal-case-research.md` | Indian court case / case number research | CDJ Law Journal, Karnataka HC judgment portal, Google News RSS, case number conventions |
| `references/indian-government-e-registration-tech-requirements.md` | Indian government e-registration system technical requirements — platform/OS, biometric hardware, software | Windows-only (Aadhaar RD Service), UIDAI-approved device models, web+installed hybrid architecture, Chromebook/Linux/macOS incompatibility. Covers: research methodology, key questions (web vs installed, device types, browser), Aadhaar OTP mobile alternative, TNREGINET STAR 3.0 as worked example |
| `references/india-local-services-search.md` | Indian local business/service research | Directory-based: JustDial, Sulekha, BookMyPlayer, MyTribe — bypasses search engine JS/captcha walls |
| `references/domain-intel.md` | Passive domain OSINT | Zero dependencies, no API keys |
| `references/duckduckgo.md` | Web search via ddg CLI | Free, no API key |
| `references/duckduckgo-lite-browser-search.md` | Browser-based DDG Lite search for CAPTCHA-blocked environments | Navigate browser to lite.duckduckgo.com/lite/, extract portal URLs via browser_console from uddg= params — works for MagicBricks, 99acres, SquareYards and other listing portals |\n| `references/phone-number-osint-india.md` | Reverse lookup of Indian mobile numbers / social-footprint hunt | Free-source ladder: DDG-via-Jina in 3 formats, Google News RSS, Truecaller web (name login-walled), directory site: queries. Zero hits across all = no public footprint |\n| `references/browser-tool-local-socks.md` | Browser tool tunnel egress debugging (ERR_TUNNEL_CONNECTION_FAILED) | browser.cloud_provider routes to cloud CDP, not local socks; fix = set provider local; manual agent-browser verification; residential router file location; daemon-kill self-match pitfall |\n| `references/jina-reader.md` | Zero-config web access via Agent Reach's Jina Reader | Clean Markdown, no browser, search proxy via DuckDuckGo Lite |
| `references/india-residential-sales-data-sources.md` | Indian residential sales data research (Anarock/KF/CBRE/PropEquity coverage matrix, Vizag & tier-2 city numbers, Jina+DDG parse recipe) | Which firm covers which city; PropEquity revision gotcha; publisher-URL extraction via `uddg=` |
| `references/direct-browser-search-no-api.md` | Direct browser/search research WITHOUT Apify or Tavily (NDR directive 2026-08-15) | Google News RSS, Wikipedia API, OSM Overpass/Nominatim, Jina page+search proxy, Commons/GitHub APIs; engine-by-engine block behavior; playwright headless recipe; KML build from OSM |
| `references/bangalore-metro-network.md` | Namma (Bangalore) Metro network knowledge bank (Aug 2026) | All 8 lines + status, Red Line Phase 3A station list, Yellow Line + Attibele extension, 72 km corridor, Sarjapur–Rathibele–Attibele corridor facts, sources |
| `references/bangalore-suburban-rail-bsrp.md` | Bengaluru Suburban Railway (K-RIDE) knowledge bank (Aug 2026) | 4 BSRP corridors + station lists, K-RIDE doubling projects (Baiyyappanahalli–Hosur, Yeshwanthpur–Channasandra), RLDA context, DPR PDF, R&D>Bangalore>Metro Drive folder |
| `references/bangalore-real-estate-research.md` | Bangalore north real estate research | Devanahalli/Doddaballapur project data, ddgs workflow, project list |
| `references/real-estate-investor-research.md` | Real estate investor research | Comprehensive research framework for investor presentations — India land development (TN/Karnataka), infrastructure projects, employment generators, competitor pricing, demand drivers — for the Bengaluru–Hosur–Shoolagiri corridor and similar contexts. |
| `references/draas-pdf-styling.md` | Extract design from DRAAS PDF + generate matching HTML | PyMuPDF extraction, CSS token system, competitive analysis HTML layout |
| `references/blogwatcher.md` | RSS/Atom monitoring | Change detection |
| `references/arxiv.md` | Academic paper search | Keyword/author/category |
| `references/ml-paper-writing.md` | Paper writing | Publication format templates |
| `references/parallel-cli.md` | Parallel CLI | Batch web operations |
| `references/youtube-video-link-sourcing.md` | Find & verify REAL YouTube video links for a topic (training/how-to/form demos) | Browser search + `a#video-title` console extraction → clean watch?v= URLs; never fabricate IDs; prefer full-length instructional over Shorts |
| `references/freelance-talent-research.md` | Freelance/contractor talent research — specialized Indian technical skills | Two sourcing paths: X search + direct-vendor partner networks. Budget benchmarks, screening checklist, job post template |
| `references/medical-research-monitor.md` | Medical research monitoring (cron + source tracker) | Weekly self-growing scan: source tracker sheet → scan 18-30+ sources → auto-discover → append to cumulative recommendations doc → briefing. Supports two-track monitoring. |
| `references/source-tracker-research-monitor.md` | Self-growing research monitor (cron + source tracker) | Cron-driven weekly scan across multiple sources with auto-discovery. Sheet-backed tracking with structured briefing. |
| `references/indian-pre-ipo-unlisted-stock-research.md` | Indian pre-IPO/unlisted share research | Gmail → corporate actions → grey market → IPO valuation → return scenarios |
| `references/flight-price-research.md` | Scrape JavaScript-rendered flight booking sites | Playwright + wa.me link generation for airfare queries |
| `references/clinical-trials-research.md` | Multi-source clinical treatment research (trials + lit + social) | ClinicalTrials.gov API v2 + PubMed + structured output; parallel-scan-then-dive pattern |
| `references/healthcare-appointment-booking.md` | Indian hospital appointment booking (browser-based) | DuckDuckGo discovery → hospital website → Practo fallback; browser_console JS for hidden elements; user confirmation workflow |
| `references/multi-agent-pdf-judgment-analysis.md` | Multi-agent PDF legal judgment analysis | Parallel agents → structured Google Doc summary with paragraph citations → Drive filing |
| `references/social-media-medical-monitoring.md` | Social media monitoring for medical research | Platform-by-platform: xurl (X/Twitter), browser automation (LinkedIn), curl/PRAW (Reddit), browser (patient forums) + research databases |
| `references/x-syndication-media-retrieval.md` | Retrieve X post text + embedded images without auth | cdn.syndication.twimg.com/tweet-result → mediaDetails[] pbs.twimg.com URLs; no OAuth/API key needed |
| `references/indian-government-scheme-research.md` | Indian government scheme / subsidy research | Fallback workflow for 403-blocked .gov.in sites; PIB → academic → aggregator tiers |
| `references/indian-govt-officer-contact-lookup.md` | Find Indian govt officer contacts (District Registrar, DEO, Tahsildar, state-dept officers) | District .nic.in whos-who = Collector/SP/DRO only; state-dept officers on department portals (often VPS geo-blocked); DRO office referral path; verified source matrix |
| `references/indian-passport-id-procedure-research.md` | Indian passport & government ID procedure research | Source hierarchy, change-in-personal-particulars vs full name change, Section 4 exclusions, PSK vs RPO authority, widow/deceased spouse deletion |
| `references/b2b-lead-database-research.md` | B2B lead database / multi-channel contact research | Parallel subagent dispatch across categories, multi-source contact discovery, outreach message generation, Google Sheet delivery |
| `references/pharmaceutical-drug-safety-research.md` | Drug safety / side effects / monitoring research | Browser-based Drugs.com ASHP monograph extraction; organ toxicity, pretreatment screening, dose escalation criteria |
| `references/scientific-research-deep-dive.md` | In-depth analysis and explanation of scientific studies | Multi-phase workflow: source tracing, evidence quality assessment, mechanism explanation, category differentiation, practical translation |
| `references/wikipedia-product-research.md` | Product specs via Wikipedia API (phones, gadgets, devices) | Two-phase: article text + infobox extraction; foldable dimension parsing; multi-currency pricing; works when all other tools blocked |
| `references/nsaid-asthma-children-evidence.md` | Pre-compiled evidence bank: ibuprofen + asthma in children | 5 PMIDs, prevalence data (2-5%), NERD mechanism, clinical recommendation template |
| `references/product-ui-screenshot-research.md` | Find product/software UI screenshots via Bing Image Search | Bing Image Search workflow, browser_vision capture, MEDIA delivery, cycling results — for when the user wants to SEE a UI

## Absorbed Skills

The following skills have been absorbed into this umbrella (archived):
- `domain-intel` → `references/domain-intel.md`
- `duckduckgo-search` → `references/duckduckgo.md`
- `blogwatcher` → `references/blogwatcher.md`
- `arxiv` → `references/arxiv.md`
- `ml-paper-writing` → `references/ml-paper-writing.md`
- `parallel-cli` → `references/parallel-cli.md`

## Direct Browser / No-API Research (NDR directive, 2026-08-15)

NDR: "dont use apify of tavily. use direct browser search" — the standing
tunnel-direct-over-APIs preference now applies to ALL web research, not just
property portals. When Tavily/Apify are excluded (or down), work this ladder —
all free, all reachable from the datacenter IP:

1. **Google News RSS** — `https://news.google.com/rss/search?q=<query>&hl=en-IN&gl=IN&ceid=IN:en`. Reliable title+link feed, no captcha. Best first move for India news (metro, real estate, infra). Parse `<item>` blocks; note the `<link>`s are JS redirects that can't be statically resolved.
2. **Wikipedia API** — `action=query&prop=extracts&explaintext=1&titles=...` for clean article text; `prop=images` reveals map files; Commons `imageinfo` (with `iiurlwidth`) for direct image thumbs.
3. **OSM Overpass + Nominatim** — geocoding (villages, stations, lakes) and real line/relation geometry for KML/GeoJSON. Heavy regex queries 504 — use targeted `way(id:...)` / small bboxes instead.
4. **Jina reader** (`r.jina.ai/<url>`) — page→markdown, AND a search proxy: `r.jina.ai/https://html.duckduckgo.com/html/?q=...` returns REAL DDG results. Jina BLOCKS `news.google.com/rss/articles/...` redirect links — get the publisher URL via DDG-via-Jina first, then Jina-fetch the real URL.
5. **GitHub API + raw files** (e.g. `geohacker/namma-metro` GeoJSON), **Wikimedia Commons API** for official route-map images.

Blocked from the VPS (don't burn retries — verified 2026-08-15): Google SERP (unusual-traffic captcha), Bing (serves anti-bot junk), DDG lite/html direct (block page), searx public instances (antibot), Mojeek (SOCKS refused). Full working recipe (playwright venv, headless-shell path, socks proxy, engine behavior, KML build): `references/direct-browser-search-no-api.md`.

## Quick Reference

### Government Portal Research (Accordion UI + DOM Inspection)

When researching Indian government e-governance portals (TNREGINET, RERA, etc.):

```bash
# Step 1: Navigate to portal, switch to English
browser_navigate(url="https://tnreginet.gov.in")
# Click the English/Tamil toggle link

# Step 2: Navigate menus to find User Manual / FAQ
# Click "Help" dropdown, then "User Manual" or "FAQ"

# Step 3: Click accordion sections to expand
browser_click(ref="@e73")  # ref from browser_snapshot

# Step 4: Read expanded content from browser console
browser_console(expression="document.body.innerText.substring(0, 15000)")

# Step 5: For PDFs behind JS onclick handlers, extract the mpgId
browser_console(expression="Array.from(document.querySelectorAll('a[onclick]')).filter(el => el.textContent.includes('Download')).map(el => el.getAttribute('onclick'))")

# Step 6: Check mobile app capabilities via Play Store
browser_navigate(url="https://play.google.com/store/apps/details?id=com.tnreginet.tnigrs")
# Read reviews + developer responses for real capabilities
```

### Domain Intel — Passive OSINT (no API keys)
```bash
python3 scripts/domain_intel.py subdomains example.com
python3 scripts/domain_intel.py ssl example.com
python3 scripts/domain_intel.py whois example.com
python3 scripts/domain_intel.py dns example.com
python3 scripts/domain_intel.py availability example.com
```

### DuckDuckGo Search
```bash
# Text search
ddg "machine learning transformers"
# News search
ddg "AI research" --news
# Images
ddg "architecture diagram" --images
```

### Blogwatcher RSS Monitoring
```bash
blogwatcher watch https://example.com/feed.xml
blogwatcher list
blogwatcher diff --name example-feed
```

### arXiv Paper Search
```bash
arxiv search "attention is all you need"
arxiv search --author "Ashish Vaswani" --category cs.CL
arxiv fetch 2103.14030
```

## Resources

- **Domain Intel**: Pure Python stdlib — no dependencies
- **DuckDuckGo**: https://duckduckgo.com
- **Blogwatcher**: blogwatcher-cli tool
- **arXiv**: https://arxiv.org
- **ML Paper Writing**: NeurIPS/ICML/ICLR format guidelines
- **Parallel CLI**: https://github.com/parallel-cli/parallel
