# Project Classification & Sheet Organization (Real Estate)

**Purpose:** Classify competitive-landscape projects by property type (Villa, Rowhouse, Apartment, Plotted), verify labels via portals, and split into category-specific sheet tabs for clean presentation integration.

## Workflow

### Phase 1: Read & Classify

1. **Read the source sheet** — Use Sheets API to pull all rows from the relevant tab.
2. **Identify the header row** — Typically row 0 (title) or row 1 (title) with row 1 or 2 as the actual column headers. Verify by checking for known header labels like "Project Name", "Property Type", "Location".
3. **Classify each project by property type** using the `Property Type` column:
   - **Villa**: Contains "Villa"/"Villas" but NOT "Row" — e.g. "4 & 5 BHK Golf Villas", "3 & 4 BHK Luxury Villas", "4 & 5 BHK Eco Villas", "3 & 4 BHK Boutique Villas"
   - **Rowhouse**: Contains "Row" + "Villa" — e.g. "3 & 4 BHK Row Villas"
   - **Apartment**: Contains "Apartment", "High-rise", "Mid-rise", "Tower", or any multi-story configuration without "Villa"
   - **Plotted**: Contains "Plotted", "Plot", or "Eco Community" — BUT cross-verify (see Phase 2)

### Phase 2: Cross-Verify Classification (Critical)

**⚠️ Sheet labels are frequently wrong.** A project labeled "Plotted Development" on a sheet can actually be a villa project. Always verify:

1. **Search portals** — Search MagicBricks, 99acres, Housing.com for each project name + area.
2. **Check the actual unit config:**
   - Portal says "3 BHK Villa" → It's a **Villa**, even if the sheet says "Plotted Development"
   - Has floor count like G+1, actual unit types (3 BHK, 4 BHK) → **Villa**
   - Has "Plots" without built structure, plot sizes in sq.ft → **Plotted**
   - Shows unit sizes in SBA (super built-up area) → **Built product** (Villa/Rowhouse/Apartment)
3. **Check developer description:**
   - "Villa project", "Independent Villas", "gated community of villas" → **Villa**
   - "Layout", "plot dimensions", "land parcel" → **Plotted**
   - "Townhouse", "Row house", "Row villa" → **Rowhouse**
4. **Class-label confusion heuristics (common in Sarjapur/Bangalore):**
   - "Plotted / Villa Community" → Likely **Villa** (plots come with built villa packages)
   - "Plotted / Eco Community" → Cross-verify — could be villa or plotted
   - "Integrated Villa-Plots" → Check if built structure exists (villa) or raw plots (plotted)
5. **If still uncertain, check builder track record** — established builders like Prestige/Sobha/Brigade build primarily built product. Land developers like Chartered/Canterbury build primarily plotted.

### Phase 3: Create Category Sheets

1. **Create new sheets in the same workbook** using Sheets API `batchUpdate` with `addSheet`:
   ```python
   requests = [{"addSheet": {"properties": {"title": "Villas"}}}]
   service.spreadsheets().batchUpdate(spreadsheetId=id, body={"requests": requests}).execute()
   ```
2. **Write each sheet** with the same format structure as the source:
   - Row 0: Title (e.g. "Master Real Estate Directory: Villas — Sarjapur & South-East Bengaluru Corridor")
   - Row 1: Original column headers
   - Row 2+: Filtered project data
3. **Clear and rewrite** if the sheet already exists — first clear with `values().clear()`, then `values().update()` with `USER_ENTERED`.

### Phase 4: Add to Presentation

1. **Identify the right presentation** — Look for the most recently modified presentation containing the project name + "v3" or "Verified".
2. **Check Slides API availability** — If `HttpError 403 SERVICE_DISABLED`, the Slides API needs enabling at the Google Cloud Console.
3. **Alternative: Browser approach** — Navigate to the presentation and use browser tools to add slides manually if API is unavailable. Requires an authenticated Google session.

## Common Pitfalls

- **Header row detection:** Title rows (e.g. "Master Real Estate Directory: ...") and blank separator rows exist above the actual header. Always verify by scanning for known column labels like "Project Name", "Property Type".
- **"Plotted" does not mean "Plotted":** Sheet labels of "Plotted Development" or "Plotted / Villa Community" frequently refer to villa projects. The word "Plotted" can mean plots in a layout OR plots that come with a built villa. Check portal listings to determine the actual product type.
- **Rowhouse detection:** Rowhouses often have "Row" in the property type. "Villa" without "Row" is always a standalone villa. "Row Villas" are rowhouses.
- **Duplicate rows:** Rewriting sheets can cause duplicates if the script runs multiple times. Always verify after writing that all project names are unique.
- **Format consistency:** Source sheets may have 7-column summary format or 14-column detail format. Keep the same column structure in the category sheets for consistency.
