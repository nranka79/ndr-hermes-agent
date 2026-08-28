# Social Media Follower Audit — Indian Real Estate (verified Aug 2026)

When NDR asks "check YouTube/LinkedIn/Twitter/Instagram followers of <builders> vs DRA" —
a brand benchmarking task (distinct from project-level R&D). First run: Aug 14, 2026,
10 developers × 4 platforms, benchmark = DRA Homes.

## Method (platform by platform)

1. **Search sweep first.** Run `web_search` with these query shapes (limit 4-5, print
   title/description/url — Google-indexed snippets carry exact counts):
   - `"<Company> YouTube channel subscribers"`
   - `"<Company> Instagram followers"`
   - `"<Company> LinkedIn followers"`
   - `"<Company> Twitter followers"`
   Snippet formats that contain counts:
   - Instagram: `143K followers · 3,183 following` (profile page cached)
   - LinkedIn: `401,919 followers • 1,001-5,000 employees` (company page cached)
   - X: `4737Posts. 170Following. 3304Followers.` (only when Google cached the profile
     with `?lang=en`; NOT always present — fall through to browser)

2. **X counts → browser.** `web_extract` on `x.com/<handle>` renders the bio but NOT the
   follower count. Use `browser_navigate` on the profile — logged-out public profiles
   render `link "X,XXX Followers"` in the accessibility snapshot (verified live:
   prestigegroup 8,866 / BrigadeGroup 5,616 / DLFLimitedIndia 33 / arihantspaces 1,614).
   A 404 page = the handle doesn't exist (Appasamy has no official X account — report
   "nil", don't invent one). Social Blade 404s on most Indian handles — skip it.

3. **LinkedIn counts → web_extract.** `https://in.linkedin.com/company/<slug>` extracts
   (via Tavily) as a rendered "LinkedIn Company Profile Summary" with a Followers row —
   authoritative (verified: Appaswamy 15,366, Puravankara 91,664, Sumadhura 43,984).
   Search snippets can show STALE numbers from cached posts (e.g. Puravankara post said
   96,921 vs company-page 91,664) — company-page extract wins. Look for `<slug>` in the
   snippet URL rather than guessing.

4. **YouTube → snippets only.** Channel `/about` pages fail web_extract ("Error fetching
   content"). Rely on Google snippets of channel/video pages: `105K subscribers•524
   videos`. A video page snippet sometimes carries the channel's sub count too.

5. **Instagram → snippets only.** `instagram.com/<handle>?hl=en` in search results gives
   the count; direct extract usually fails.

## Disambiguation rules (critical — counts are meaningless if wrong entity)

- **Lookalikes**: Prestige Group UK (@PrestigeGrpUK), Prestige Group Inc (PA), "Brigade"
  NY marketing firm, Samudra Group LLC (Austin) — filter to the Indian developer's
  official account. Verify by bio + website link + joined date.
- **Multi-account builders**: DLF runs DLF Limited (@DLFLimitedIndia, new May-2025, 33),
  DLF Homes (@dlfrealty 205), DLF Mall of India (@DLFMoI 1,960), DLF Emporio. Report the
  main account + note the split — "DLF X is dead" is itself a finding.
- **Voice transcription**: "Samudra" in a voice message → Sumadhura Group (Bengaluru
  tier-2, since 1996). Flag the assumption explicitly rather than silently picking.

## Baseline data — Aug 14, 2026 (YT = YouTube subs, IG = Instagram, LI = LinkedIn, X = Twitter)

| Developer | YT | IG | LI | X |
|---|---|---|---|---|
| Prestige Group | 105K | 143K | 401,919 | 8,866 |
| Brigade Group | 68.6K | 74.7K | 275,701 | 5,616 |
| DLF | 3.67K (DLF Homes) | 40.3K | 328,342 | ~200 (fragmented) |
| Puravankara | 9.6K | 78K | 91,664 | 3,304 |
| Shriram Properties | 11K | 47.2K | 69,798 | 3,913 |
| Sumadhura (the "Samudra") | 62.8K | 42.5K | 43,984 | 713 |
| My Home Group (Hyd) | 15K | 115K | 45,587 | 2,005 |
| Arihant (Arihant Spaces) | 218 | 20.5K | 3,346 | 1,614 |
| Appasamy (Appaswamy RE) | 9.19K | 134K | 15,366 | nil |
| **DRA Homes (benchmark)** | **90.9K** | **77K** | **9,730** | **305** |

Official handles: Prestige @prestigegroupindia / @prestigeconstructions / prestige-group-bangalore.
Brigade BrigadeGroupOfficial / @brigade.group / brigadegroup. Puravankara @puravankara /
@puravankara_official / puravankara. Shriram @shriramproperties / @shriram.properties /
shriram-properties-ltd. Sumadhura Sumadhuragroupbuilders / @sumadhurainfracon /
sumadhura-infracon-pvt-ltd. My Home MyhomeconstructionsPvtLtdHyd / @myhomeconstructions_ /
my-home-constructions. Arihant @arihantspaces (all three). Appasamy @appaswamy_realestates /
appaswamy-real-estates-ltd. DRA @DRAHomes / @drahomesindia / dra-homes / @DRA_HOMES.

## Comparison framing (what NDR wants)

- Per-platform ranking vs the benchmark (e.g. DRA YT = #2 of 10, LI = #9 of 10).
- **Total reach** = sum of 4 platforms: Prestige ~659K, Brigade ~425K, DLF ~372K,
  Puravankara ~183K, My Home ~178K, **DRA ~178K**, Appasamy ~158K, Sumadhura ~150K,
  Shriram ~132K, Arihant ~26K.
- Call out the gap platform explicitly (DRA: LinkedIn 9.7K vs tier-2 peers 44–92K).
- Counts drift — label the audit date; refresh = re-run the sweep, don't reuse.
- Offer to write to a Google Sheet if NDR wants it tracked over time.
