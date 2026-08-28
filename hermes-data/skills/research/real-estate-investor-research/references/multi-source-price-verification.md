# Multi-Source Price Verification Protocol (Real Estate)

**Purpose:** Validate project pricing across 3+ independent sources before updating any deliverable. Eliminates stale-sheet risk and portal-cache drift.

## The Three-Source Method

```
Sheets (user's spreadsheet) ──┐
                              ├──► COMPARE → IDENTIFY DISCREPANCIES → VERIFY → UPDATE
Presentations (existing deck) ─┘
                                      │
                                      ▼
                            Online Portals (MB, 99acres, Housing.com)
```

## Step-by-Step Protocol

### Phase 1: Extract
1. **Read sheet data** — Pull all rows from the relevant sheet tab via Sheets API. Look for price columns (estimated price/sq.ft, current sale price, overall range).
2. **Export presentation** — Download existing Google Slides as .pptx via Drive API export (mimeType: `application/vnd.openxmlformats-officedocument.presentationml.presentation`).
3. **Extract presentation prices** — Scan each slide for `₹`, `sq.ft`, `Rate:`, `Lac`, `Cr` patterns. Build a project→price dictionary.

### Phase 2: Compare
4. **Cross-reference** — For each project, create a 3-column table:
   - Column A: Sheet says
   - Column B: Presentation says
   - Column C: (to be filled) Verified online
5. **Flag discrepancies** — Any gap >15% between sources is a red flag. Log the delta.

### Phase 3: Verify
6. **Search portals** — For each project, search MagicBricks (`site:magicbricks.com <project> <area>`), 99acres (`site:99acres.com <project> <area>`), and Housing.com.
7. **Extract portal price** — Look for the project-level average/range (not individual listings). MagicBricks typically has "Avg. Price ₹X/sq.ft" on the project page. 99acres shows "₹X - ₹Y/sq.ft" on the project overview.
8. **Cross-check with Google Search AI Overview** — The AI Overview box often has structured real estate data when portals block direct access. Query pattern: `<project> <area> Bangalore price sqft launch`.
9. **Resolve conflicts** — When sources disagree:
   - Portal 1 vs Portal 2 → prefer the HIGHER credible range (portals lag market, never lead it)
   - Portal vs Sheet → portal wins (sheets are often manually entered and stale)
   - Portal vs Presentation → portal wins unless presentation was recently verified

### Phase 4: Update
10. **Update presentation** — Use python-pptx to find-and-replace price text in slides. Target patterns:
    - `Rate: ₹X,XXX/sq.ft` → update the numerical value
    - Total price ranges (`₹X.XX Cr — ₹Y.YY Cr`)
    - Price comparison tables/summaries (slide 41 pattern)
    **Then re-upload:** .pptx → Drive → convert to Google Slides → share as editor.
11. **Update My Maps** — Two approaches:

    **A) Build KML from scratch** (when no map exists yet):
    - Each project as a `<Placemark>` with `<description><![CDATA[...]]>` containing:
      - Project name
      - **Highlighted current price** (yellow background span)
      - Sheet vs previous vs verified comparison
      - Source attribution
    - Upload KML to Drive
    - User imports manually (⋮ → Import KML file → create new layer)

    **B) Edit existing My Maps KML export** (when map already has placemarks, just update pin labels to show prices):
    - The map can be exported as KML via Drive (My Maps saved as KML in Drive, or download from My Maps menu → Export to KML)
    - Parse each `<Placemark>` block in the KML using a regex that handles both single-line and multi-line price formats:
      ```python
      price_match = re.search(
          r'💰 CURRENT PRICE:</b>\s*<span[^>]*>\s*([^<]+)\s*</span>',
          placemark_block, re.DOTALL
      )
      ```
    - Replace `<name>PROJECT_NAME</name>` with `<name>CURRENT_PRICE</name>` for each placemark
    - Clean the extracted price: strip `(built-up)` / `(resale)` suffixes, avoid appending `/sft` if `/sq.ft` already present
    - Upload the modified KML to Drive
    - User imports it into My Maps: delete existing layer features → import KML → select target layer
    
    **Known price format variations** (seen Jul 2026 in Sarjapur corridor KML):
    - Single-line: `<b>💰 CURRENT PRICE:</b> <span ...>₹10,700 — ₹11,200/sq.ft</span>`
    - Multi-line with leading `~`: `<b>💰 CURRENT PRICE:</b>\n<span ...> ~₹12,000/sq.ft (built-up)</span>`
    - The regex `[^<]+` captures the price — strip parentheses suffixes with `re.sub(r'\s*\([^)]*\)', '', price)`

## Common Pitfalls

- **Sheet-underestimates pattern:** Many sheets carry "estimated" prices that are 6-12 months stale. Sarjapur corridor projects consistently showed sheet prices 30-60% below verified market in Jul 2026. When sheet says ₹4,500-5,800/sq.ft but all portals show ₹8,500-12,900, trust the portals.
- **Presentation-overestimates pattern:** Some presentations inflate competitor prices to make the target project look better. Cross-check aggressively when a deck claims ₹15,500/sq.ft for a project that portals show at ₹8,500-11,300.
- **Total range vs per-sqft confusion:** Always verify whether a price is per-sqft built-up, per-sqft carpet, or total unit price. Portals mix these on the same page.
- **Resale contamination:** When a project is sold out, remaining listings are resale at 20-50% premium. Flag as "resale" in the KML description.
- **Property type misclassification:** Sheets sometimes label villa projects as "Plotted Development" or "Plotted / Villa Community" based on outdated assumptions. A project listed as "Plotted Development" on a sheet may actually be independent villas or row houses. Always verify property type by checking actual portal listings (MagicBricks, 99acres, developer site) — look for configuration (Villas, Plots), unit count, and project description. In the Sarjapur corridor, 4 of 4 projects labeled as plotted in the source sheet were villa projects.

## Tool Chain

```
Sheets API → read data
Drive API → export/import pptx
python-pptx → modify slide text (run.text)
Drive API → upload new pptx → copy as Google Slides → share
KML → Drive upload → manual My Maps import
```

## Source URLs for Key Portals

| Portal | URL Pattern | Notes |
|--------|-------------|-------|
| MagicBricks | `https://www.magicbricks.com/<project-slug>` | Best for project-level avg price |
| 99acres | `https://www.99acres.com/<project-slug>` | Best for resale prices |
| Housing.com | `https://housing.com/in/buy/projects/...` | Good cross-reference |
| HomzNSpace | `https://www.homznspace.com/...` | Useful secondary check |
