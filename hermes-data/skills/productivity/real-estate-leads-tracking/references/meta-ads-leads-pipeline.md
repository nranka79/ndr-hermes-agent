# Meta Ads → Kelsa Pipeline 10 (Daily Cron Import)

Meta (Facebook/Instagram) ad leads arrive as a Google Sheet populated by the "I Am Here Software Labs" ad management system. A daily cron script reads the sheet, imports new leads to Kelsa Pipeline 10, and updates the sheet.

This is a different lead source from portal extraction (MagicBricks, Housing.com, etc.) — no Gmail scraping involved, just sheet-based ETL.

## Lead Source Config

| Field | Value |
|-------|-------|
| Source | `I Am Here Software Labs` |
| SourceDetails | `Meta` |
| Channel | `DigitalAds` |
| Project | `Ranka udaya` |

## Script Locations

| File | Purpose |
|------|---------|
| `/data/hermes/scripts/daily_meta_import.py` | **Main entry point.** Reads sheet, finds unimported rows, delegates to batch script, writes results back. |
| `/data/hermes/scripts/batch_import_leads.py` | **Batch worker.** Connects to Kelsa MCP, creates leads in Pipeline 10 one by one, outputs JSON results. |
| `/data/hermes/scripts/cron_chunk.json` | Temp — chunk of leads the batch script processes. |
| `/data/hermes/scripts/cron_output.json` | Temp — results from the batch script (lead IDs, statuses, Kelsa URLs). |

## Sheet Structure

- **Sheet ID:** `1yaUwSos6DO56Oni2iiVJ0L26K-rRn7wzYsHKweNxUB0`
- **Sheet name:** `Ranka Udaya - Meta`
- **Data range:** 1316 rows as of Aug 2026 (grows daily)
- **Row layout:** Row 0 = headers, data starts at row 1
- **Columns (A–K, 0-indexed):**

| Index | Header | Content |
|-------|--------|---------|
| A (0) | Date | dd/mm/yyyy |
| B (1) | What is the investment amount you are comfortable with? | ₹ range (e.g. ₹ 50 L+) |
| C (2) | Would you like to visit the site? | Visit preference |
| D (3) | Full name | **Lead name** |
| E (4) | Phone Number | **Phone (91XXXXXXXXXX)** |
| F (5) | Email | Email address |
| G (6) | City | City name |
| H (7) | Status | Mostly blank or empty |
| I (8) | Remarks | Call notes / feedback |
| J (9) | Next Follow Up | **"Already Exists"** for imported leads, or other follow-up text |
| K (10) | (Kelsa URL) | **https://app.kelsa.io/5/leads/{id}** for imported leads |

> ⚠️ **"Already Exists" is in col J (Next Follow Up), NOT col H (Status) or col I (Remarks).** The Kelsa URL is in col K — some leads have "Already Exists" in J without a Kelsa URL in K, and vice versa. Always check BOTH columns to determine import status.

## Import Logic

The daily import script:
1. Reads all rows from the sheet
2. Skips rows already imported — checks col J for "Already Exists" OR col K for a kelsa.io link
3. Validates each row has name + phone (10+ digits)
4. Creates a **contact first in Pipeline 3429 (DRA Sales Contacts)** with `cf_contact` structured object containing name + phone + email
5. Then creates a **lead in Pipeline 10 (DRA Sales Leads)** linking to the contact via `cf_contact1: {id: <contact_id>}`
6. Updates the sheet: col J = status text, col K = Kelsa URL

**Dedup is at the Kelsa level** — the script searches Pipeline 10 by phone before creating. Duplicates are marked as "Already Exists" in the sheet.

### Cross-check (one-time audit)

For a one-time cross-check (not daily cron), run a scan over ALL rows and classify:
- Already in Kelsa = col J contains "Already Exists" OR col K contains "kelsa.io"
- NOT in Kelsa = neither condition met AND has a non-empty phone
- Skip = no phone number

From Aug 2026 data: 694/1316 already in Kelsa, 595 pending import.

**The cross-check query:**

## ⚠️ CRITICAL: Cron Job Env Requirements

The script uses **`gws_auth.build_service('sheets', 'v4', service_name='google-draas')`** to read/write the sheet. This requires `HERMES_SESSION_USER_ID` to be set — it's how `gws_auth` resolves which user token to load.

**The cron job environment does NOT have this set.** Running the script directly from cron will fail with:
```
ValueError: No session user context (HERMES_SESSION_USER_ID not set).
Cannot determine which user's token to load.
```

**Fix — always run with the env var:**
```bash
HERMES_SESSION_USER_ID=ndr python3 /data/hermes/scripts/daily_meta_import.py
```

Where `ndr` is the canonical slug for Nishant Ranka (owns the `google-draas` service token that has access to the DRAAS sheet).

## Kelsa Pipeline Config

- **Pipeline:** 10 (DRA Sales Leads)
- **Account:** 5
- **Auth:** Kelsa OAuth token via `tools.kelsa_auth.get_valid_access_token("[REDACTED-TID]")` (Nishant's user ID for the token vault)
- **MCP endpoint:** `https://kelsa.io/mcp`

Lead fields created by batch import:

**Two-step creation (contact first, then lead):**

Step 1 — Create contact in **Pipeline 3429 (DRA Sales Contacts):**
```json
{
  "pipeline_id": 3429,
  "field_values": {
    "cf_contact": {
      "name": "<lead name>",
      "phone": "91XXXXXXXXXX",
      "email": "<lead email>"
    }
  }
}
```

Step 2 — Create lead in **Pipeline 10 (DRA Sales Leads):**
| Field | Value |
|-------|-------|
| `cf_contact1` | `{id: <contact_id_from_step_1>}` |
| `cf_source` | `I Am Here Software Labs` (dropdown) |
| `cf_sourcedetails` | `Meta` |
| `cf_campaign` | `DigitalAds` (dropdown) |
| `cf_project` | `Ranka udaya` (master field) |

The lead automatically enters the **Cold** stage — no explicit stage field needed.

**Caveats:**
- `cf_campaign` dropdown value is `DigitalAds`, not `Digital` — the label must match exactly
- `cf_source` dropdown value is `I Am Here Software Labs` — case-sensitive
- `cf_project` is a master field (linked to `dra_project_unit_master_data`) — the string `Ranka udaya` works as its display value
- Batch import of 500+ leads: write a Python script that creates contacts+leads via the Kelsa MCP with a 0.3-0.5s delay between rows. Use `re.search(r'ID: (\d+)', ct)` to extract contact IDs from the MCP response text.

## Typical Output

Running the import produces something like:
```
Found 26 unimported leads (rows 690-715)
✅ Added: 24 | ❌ Failed: 0 | ⏭️ Already Exists: 2
Updated sheet: 52 cells at 'Ranka Udaya - Meta'!J690:K715
```

Each new lead gets a Kelsa URL like `https://app.kelsa.io/5/leads?current_item_id=54017579`.

## Fixing a Failed Run

If the script fails mid-way (e.g. network timeout, auth error):
1. Check `cron_output.json` for partial results
2. Manually mark already-imported rows in the sheet (col J = "Added", col K = URL)
3. Re-run with `HERMES_SESSION_USER_ID=ndr`
4. The script will skip rows with non-empty J/K columns and only process genuinely unimported ones

## Related

- `references/portal-to-kelsa-crm.md` — Portal leads (MagicBricks/Housing) → Kelsa Pipeline 10 (different source, same target pipeline)
- `real-estate-leads-tracking` umbrella skill — covers all lead source pipelines
