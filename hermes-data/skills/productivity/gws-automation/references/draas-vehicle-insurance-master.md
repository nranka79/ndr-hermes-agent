# DRAAS Vehicle Insurance Master — Lookup Reference

## Data Source

A consolidated Excel file (`DRAAS_Vehicle_Insurance_Master.xlsx`) on Drive contains all DRAAS vehicle insurance policies in one place.

- **Drive ID:** `1tLZRVTyrQR1iu4aSNTawVuf4JkEjXgi5`
- **Folder:** Vehicle Insurance Documents (`16R5MtZRoQrLM64Hpxejuij_wV08hfQ4E`)
- **Format:** Binary .xlsx (NOT Google Sheets) — use `get_media` + `openpyxl` to read
- **Last updated:** Jun 2026

## Sheet Structure

| Sheet | Content |
|-------|---------|
| **Summary** | All vehicles in one table: Vehicle, Reg No, Insurer, Policy No, Period From/To, Premium, IDV, NCB, Fuel, Mfg Year, PDF link |
| **Detailed View** | Per-vehicle blocks with full breakdown: Policy Info, Vehicle Details, Coverage & IDV, Nominee, Endorsements |
| **PDF Links Index** | Quick-access list of all PDF filenames with Drive links |

## Current Vehicles (as of Jun 2026)

| Vehicle | Reg No | Insurer | Period |
|---------|--------|---------|--------|
| BMW X1 | KA 03 ND 7705 | TATA AIG General Insurance | 27/11/2025 → 26/11/2026 |
| Volkswagen Vento | KA 05 MT 9001 | TATA AIG General Insurance | 27/05/2026 → 26/05/2027 |
| Toyota Innova | KA 04 NE 1550 | Bajaj Allianz General Insurance | OD: 05/08/2024 → 04/08/2025, TP: → 04/08/2027 |
| Jaguar XJ L | KA 04 MR 1001 | National Insurance Co. | 06/02/2026 → 05/02/2027 |

## When to Query

Use this master sheet as the **first stop** when a user asks about:
- "Is X vehicle insured?"
- "When does the insurance for [reg no] expire?"
- "What company insures [vehicle]?"
- "Find any other insurance policies for [reg no]"

## Lookup Workflow

### Step 1 — Download and read the master sheet

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import json, openpyxl, io

with open('the gws-vault daemon (no token files exist on disk — see api-references/google-workspace-api/references/token-access-canonical.md)') as f:
    data = json.load(f)
creds = Credentials(
    token=data['token'], refresh_token=data['refresh_token'],
    token_uri=data['token_uri'], client_id=data['client_id'],
    client_secret=data['client_secret'], scopes=data['scopes']
)
drive = build('drive', 'v3', credentials=creds)

# Download xlsx
fh = io.BytesIO()
request = drive.files().get_media(fileId='1tLZRVTyrQR1iu4aSNTawVuf4JkEjXgi5')
fh.write(request.execute())
wb = openpyxl.load_workbook(fh)

# Read Summary sheet
ws = wb['Summary']
for row in ws.iter_rows(min_row=4, values_only=True):
    vehicle, reg, insurer, policy_no, period_from, period_to = row[0], row[1], row[2], row[3], row[4], row[5]
    # Search for matching reg no or vehicle name
```

### Step 2 — Cross-reference with Gmail

Search for emails containing the reg no, vehicle name, or insurer:

```python
gmail = build('gmail', 'v1', credentials=creds)
results = gmail.users().messages().list(
    userId='me',
    q='KA04NE1550 OR innova insurance OR "Toyota Innova" insurance',
    maxResults=20
).execute()
```

### Step 3 — Check Vehicle Insurance documents folder

```python
# List files in the Vehicle Insurance folder
results = drive.files().list(
    q="'16R5MtZRoQrLM64Hpxejuij_wV08hfQ4E' in parents",
    fields="files(id, name, size, createdTime)"
).execute()
```

### Step 4 — Synthesise findings

Report whether the master sheet matches or conflicts with Gmail/Drive findings. The master sheet is authoritative for status — Gmail/Drive may have superseded or additional policies not yet entered.

## Pitfalls

- **OD vs TP periods differ** — Indian policies often list separate OD and TP expiry dates. The Summary sheet may show the OD period only; check the Detailed View and original PDF for TP dates.
- **Master sheet may be stale** — if a policy was renewed after the sheet was last updated, Gmail/Drive may have the new policy PDF but the sheet won't reflect it yet. Flag this when found.
- **.xlsx is binary** — use `get_media` + `openpyxl`, NOT Sheets API or `export_media`.
- **Innova OD expired** — confirmed Jun 2026: OD cover ended 04/08/2025, only TP cover remains active until 04/08/2027.
