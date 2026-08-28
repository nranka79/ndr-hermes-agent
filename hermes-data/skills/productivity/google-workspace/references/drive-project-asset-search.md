# Drive Project Asset Search — Renders, Elevations, Brochures, Videos

Search Drive for a real-estate project's marketing/visual assets (renders, elevations, brochures, video walkthroughs, master plans, allotment plans) on the `ndr@draas.com` (google-draas) account.

## Multi-Query Strategy

Run these queries serially — each catches what the prior might miss. The `orderBy` is critical: NDR's latest files are usually the most relevant.

### Query 1: Name-based (render/elevation/brochure keywords)

```python
q = "name contains '<Project>' and name contains '<ShortName>' and (name contains 'elevation' or name contains 'Elevation' or name contains 'render' or name contains 'Render' or name contains 'brochure' or name contains 'Brochure')"
orderBy='modifiedTime desc'
```

Catches files explicitly named with the asset type. Example: `Ranka Oasis Marketing Office 3D Render`, `20260316 Ranka Oasis G+2 Villa Render V2`, `Ranka Oasis Brochure.pdf`.

### Query 2: Image/video mimeType

```python
q = "name contains '<Project>' and name contains '<ShortName>' and (mimeType contains 'image/' or mimeType contains 'video/')"
orderBy='modifiedTime desc'
```

Catches JPEGs, PNGs, MP4s that may not have "elevation" or "render" in the filename. Example: `Ranka Oasis Master Plan Image.jpeg`, `RANKA OASIS_FINAL_OUTPUT-1.mp4`.

### Query 3: Plan/design/site/view keywords

```python
q = "name contains '<Project>' and name contains '<ShortName>' and (name contains '3D' or name contains 'visual' or name contains 'Visual' or name contains 'view' or name contains 'View' or name contains 'site' or name contains 'Site' or name contains 'plan' or name contains 'Plan' or name contains 'allotment' or name contains 'Allotment')"
orderBy='modifiedTime desc'
```

Catches layout plans, allotment plans, and site images. Example: `Ranka Oasis - Master Oasis Allotment Plan (Red Marked).pdf`.

## Folder Traversal (DRAAS Structured Folders)

DRAAS project Drive folders are organized under the **Sevaganapalli Land Partners** top-level folder (or the project's own folder). Marketing assets live in:

```
📁 Sevaganapalli Land Partners  (or project root folder)
  └── 📁 06_Marketing_and_Brochures/
      ├── 📁 Presentations/
      ├── 📁 Site_Photos/
      ├── 📁 Photos_and_Renders/         (may be empty)
      └── 📁 Brochures/
  └── 📁 04_Engineering_and_Design/
      ├── 📁 Villa_Designs/
      ├── 📁 Floor_Plan_Configs/
      ├── 📁 Layout_Plans/
      └── 📁 Survey_and_Topography/
```

Additional asset locations found in practice (Ranka Oasis):

| Folder | Path | What's inside |
|--------|------|---------------|
| Villa_Designs | `04_Engineering_and_Design/Villa_Designs/` | 3D villa renders, elevations, AI-generated villa concept images |
| Floor_Plan_Configs | `04_Engineering_and_Design/Floor_Plan_Configs/` | `.dwg` files, floor plan PDFs, screenshots |
| RENDERS (inside Floor_Plan_Configs) | `Floor_Plan_Configs/02.07/RENDERS/` | Full scene renders (Scene 1–5), interior/exterior images (PNG, JPG) |
| Entrance_Concepts (inside Villa_Designs) | `Villa_Designs/Ranka Oasis/Entrance_Concepts/` | Entrance gate/JPG concepts |
| Ranka Oasis Proposed Villa Designs | `Villa_Designs/Ranka Oasis/Ranka Oasis Proposed Villa Designs/` | 3D renders, Master Plan image, AI-generated villa concepts |
| Floor_Plan_Config | Top-level: `Ranka Oasis Floor Plan Configurations` | Dated subfolders (27.06, 28.06, 29.06, 02.07) with DWG, PDF floor plans, and RENDERS subfolder |

## Full Search Script Template

```python
import os, sys
os.environ['GWS_VAULT_SOCKET'] = '/run/gws-vault/vault.sock'
os.environ['GWS_VAULT_TOKEN_DIR'] = '/opt/gws-vault/tokens'

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

service = build_service('drive', 'v3', service_name='google-draas')

# Define project name parts
project = "<Project>"      # e.g. "Ranka"
short = "<ShortName>"      # e.g. "Oasis"

# Query list
queries = [
    f"name contains '{project}' and name contains '{short}' and (name contains 'elevation' or name contains 'Elevation' or name contains 'render' or name contains 'Render' or name contains 'brochure' or name contains 'Brochure')",
    f"name contains '{project}' and name contains '{short}' and (mimeType contains 'image/' or mimeType contains 'video/')",
    f"name contains '{project}' and name contains '{short}' and (name contains '3D' or name contains 'visual' or name contains 'Visual' or name contains 'view' or name contains 'View' or name contains 'site' or name contains 'Site' or name contains 'plan' or name contains 'Plan' or name contains 'allotment' or name contains 'Allotment')",
]

for i, q in enumerate(queries):
    results = service.files().list(
        q=q,
        spaces='drive',
        orderBy='modifiedTime desc',
        pageSize=30,
        fields='files(id, name, mimeType, modifiedTime, size)'
    ).execute()
    files = results.get('files', [])
    print(f"\nQuery {i+1}: {len(files)} files")
    for f in files:
        mod = f.get('modifiedTime', '?')[:19]
        sz = int(f.get('size', 0)) // 1024 if f.get('size') else 0
        print(f"  [{mod}] {f['name']} | {f['mimeType']} | {sz}KB | {f['id']}")
```

## Folder Content Enumeration

To list any known folder's contents:

```python
folder_id = '<folder_id>'  # from search results or known
results = service.files().list(
    q=f"'{folder_id}' in parents",
    orderBy='modifiedTime desc',
    pageSize=50,
    fields='files(id, name, mimeType, modifiedTime, size)'
).execute()
```

## Brochure / Presentation Assets

Search for marketing deliverables specifically:

| Type | Example filename | Size | Date |
|------|-----------------|------|------|
| Brochure PDF | `Ranka Oasis Brochure.pdf` | 20.8MB | Jul 23, 2026 |
| Video walkthrough | `RANKA OASIS_FINAL_OUTPUT-1.mp4` | 128MB | Aug 6, 2026 |
| Video walkthrough | `Ranka Oasis First Cut Fiverr.mp4` | 190MB | Jul 25, 2026 |
| Presentation | `RANKA Oasis v3.pptx` | 127KB | Jul 21, 2026 |
| Google Slides | `20260824_Ranka_Oasis_DPR_Editable_Slides` | - | Aug 25, 2026 |
| Google Slides | `RANKA Oasis — Market Research Report (Brochure Edition)` | - | Jul 16, 2026 |
| Allotment Plan | `Ranka Oasis - Master Oasis Allotment Plan (Red Marked).pdf` | 904KB | Aug 6, 2026 |
| Land Area Plan | `RANKA OASIS - TOTAL PROJECT LAND AREA PLAN 26714.pdf` | 433KB | Jul 14, 2026 |
| Layout Plan | `Ranka Oasis Layout Plan Presentation.pdf` | 409KB | Jul 15, 2025 |

## Tips

- Query 1 (name-based) should run first — it's the most precise
- Query 2 (mimeType) catches images/videos that don't have "render" or "elevation" in the name
- Query 3 (plan/site/design) catches layout PDFs and allotment plans
- For video walkthroughs, the mimeType query catches `.mp4` files directly
- For older projects (2024–2025), traverse subfolders manually — older renders may only exist in dated subfolder structures
- The `modifiedTime` field is the actual last-modified timestamp; files moved between folders keep their original creation date for `createdTime`