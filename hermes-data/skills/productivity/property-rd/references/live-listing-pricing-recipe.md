# Live-Listing Pricing Re-Run Recipe (NDR mandate, 2026-08-11)

Trigger: NDR says "where did that average come from / verify this project's
price on the portal / the psf is wrong". Root cause of the original miss:
the sheet's psf came from the **rate-bank reference file** (curated from
older/mixed sources), NOT from the project's own recent listings — the
99acres deep-scrape returned null prices for that project (npxid page with
no listing section), so the pipeline fell back to the bank range.

## The mandate (NDR, verbatim intent)
> "The only way we want the data to confirm is across the property portals,
> popular ones. Look at the most recent listings and take the pricing data
> from the most recent listings. Maybe about three or four most recent
> listings is good enough to triangulate."

So: psf per project = triangulation of the **3-4 most recent individual
listings** (area + total + computed psf + URL + date) from 99acres /
MagicBricks / Housing.com. Bank figures are fallback-only, flagged
low-confidence. Never present a bank figure as listing-derived.

## Step 1 — verify ONE project end-to-end (the PPD model)

Use `browser_use_cloud` on the project's 99acres npxid page:

```
task: "Open https://www.99acres.com/<project>-...-npxid-rXXXXXX. Find the
section listing individual properties for sale in <Project> (usually
'Listings in <Project>' / resale listings). Extract EVERY listing: plot/flat
area, total price, price per sqft if shown, posting age/date (e.g. '3 weeks
ago'). Report the most recent 3-4 first."
```

PPD result (verified): 2346sqft@Rs2.64Cr=Rs11,253 (yesterday); 2400sqft@
Rs3.00Cr=Rs12,500 (3d); 1200sqft@Rs1.32Cr=Rs11,000 (4d); 1200sqft@Rs1.29Cr=
Rs10,750 (1w). → sheet psf "Rs 10,750-12,500/sqft (4 recent 99acres
listings)". KML label takes the low end (Rs 10,750/sqft).

## Step 2 — scale to all competitors (parallel browser waves)

- Batch ~6 projects per `browser_use_cloud` session, run 3 sessions in
  parallel (18 projects/wave). ~4 waves covered 61 projects.
- 99acres npxid project pages are often **informational brochures with NO
  listing section** (GSG Riviera Sky, PC Park Lane, Nakshatri, Velociti,
  Lodha Fiorana all empty). When that happens tell the agent to fall back to
  **MagicBricks search + Google snippets** from 99acres/MB/Housing.com.
- 99acres itself frequently 418s/captchas the cloud browser; MagicBricks
  search snippets worked more reliably.
- For the stragglers use `web_search('<project> Devanahalli price per sqft')`
  snippets — validated against raw snippet text (Sattva Park Cubix II
  ₹8,050-8,900; Valmark ₹5,800-10,416; Nakshatri official ₹8,499; Embassy
  Springs NoBroker avg ₹10,170).

## Step 3 — Apify 99acres deep-scrape as a supplement

- `codingfrontend/99acres-projects-search-scraper` with locality-first
  `-ffid` searchUrls + `enableDeepScraping: true` returns npspid
  **listing-level** records (price.min/max + area.min/max) for plots/villas
  — psf = price/area IS computable (Sumadhura ₹8,000; Secret Lake
  ₹7,000-7,250; Arvind Orchards ₹12,851; Assetz City of Palms ₹9,008;
  Prestige Crystal Lawns ₹8,494; Greenbrook ₹8,244; TE TUG ₹9,003; Arvind
  The Park ₹10,000; IVC Northshire ₹8,995).
- The actor caps at **maxItems ≤ 200** (validation error above that) and
  effectively returns ~31 records per run regardless of searchUrls
  (captcha/pagination wall) — plan multiple targeted runs, don't expect
  full belt coverage.
- npxid records in the same output carry NULL price/area — project
  brochures, not listings.

## Step 4 — sheet writes (the row-offset trap)

- Physical sheet row = `#` value + 1 (header is row 1). `update_cell` with
  `F13` for a `#13` project clobbers the `#12` row. ALWAYS
  physical_row = int(#) + 1.
- After EVERY batch: re-read `A{r}:P{r}` raw and confirm project name
  matches the row you intended to write. One off-by-one = 10 corrupted rows
  (restore + rewrite round-trip needed).
- Append listing rows to `Listings & Sources` (no `#` column) as raw
  list-of-lists — `append_rows(sheet, tab, rows)` takes the LIST directly,
  not a file path.

## Step 5 — rebuild + verify

1. `kml_generator.py --sheet <id> ... --labels price --drive-file-id <same id>`
   — labels take low end of psf range.
2. Download the KML back (`get_drive_file_media`) and grep the `<name>`
   labels for the corrected projects — confirms the Drive link carries the
   new data. (Watch: a naive check that strips commas from the needle but
   not the haystack will false-negative on "Rs 10,750/sqft".)
3. Patch the rate-bank reference file with a CORRECTED marker so the stale
   figure never resurfaces (done for PPD in
   property-pricing-sources/references/devanahalli-per-sqft-curated-aug2026.md).
