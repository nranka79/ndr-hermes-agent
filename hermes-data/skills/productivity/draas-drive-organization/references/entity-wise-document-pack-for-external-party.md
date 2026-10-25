# Consolidated entity-wise document pack for an external party (finance/lender/advisor)

Verified 2026-09-21 (V-Gro Finserv Services request: 3 entities × 5 document categories).

Trigger: an external party (NBFC/financier/advisor) sends a document-request list covering
MULTIPLE DRA entities, and the user wants the documents consolidated per entity and shared —
usually with a reply email. Example ask: *"3-Years Audited Balance Sheet / Company & Promoter
Profile / Debt Profile / Ongoing & Upcoming Project Details / Existing Sanction Letter"* for
DRA Realty Pvt Ltd, Sevaganapalli Land Partners and DRA Thindlu Land Partners.

## 1. Read the requester's OWN templates first

Their mail usually attaches the blank formats (xlsx/pdf). Download and read them — the column
headers define exactly what to supply, so you can report real gaps instead of guessing.

```python
# openpyxl is NOT preinstalled in /opt/hermes/.venv; install with uv, not pip:
#   uv pip install --python /opt/hermes/.venv/bin/python3 openpyxl
import openpyxl
wb = openpyxl.load_workbook(path, data_only=True)
for ws in wb.worksheets:
    for r in ws.iter_rows(min_row=1, max_row=min(ws.max_row, 30), values_only=True):
        print(' | '.join('' if c is None else str(c)[:42] for c in r))
```

Real find: the "Ongoing Projects" template expects Dev-Share Ratio %, Developer Share area,
sold/unsold split, RPSF, and a **cover ratio against outstanding loan** — i.e. it is a
lender-style credit template, not a marketing project list. Knowing that shapes what you flag.

## 2. Inventory Drive per entity BEFORE creating anything

Search by entity name, then walk each entity's "firm related documents" folder. Map what
exists against each requested category and record the MISSING ones.

```bash
cd /opt/hermes && /opt/hermes/.venv/bin/python3 -c "
import sys; sys.path.insert(0,'/opt/hermes')
from tools.gws_auth import build_service
d = build_service('drive','v3',service_name='google-draas')
for q in ['DRA Realty','Sevaganapalli','Thindlu','Balance Sheet','Sanction Letter']:
    r = d.files().list(q=\"name contains '\"+q+\"'\", pageSize=25,
        fields='files(id,name,mimeType,size,modifiedTime,parents)',
        supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
    for f in r.get('files',[]): print(f['id'],'|',f['name'],'|',f.get('parents'))
"
```

What the real inventory looked like (useful shape to expect):

| Entity | Financials present | Gaps |
|---|---|---|
| DRA Realty Pvt Ltd | Full 3-yr audited sets FY23/24/25 (ITR + P&L + BS + Auditor Report), Director's Report | no sanction letter; no promoter CV/profile as such |
| Sevaganapalli Land Partners | Statement of Income AY24-25 + ITR forms FY24/25/26 | no audited BS (audit not statutorily applicable to firms) |
| DRA Thindlu Land Partners | ITR forms FY25/26 + acks | no audited BS; no balance sheet at all |

`fullText contains '<entity>' and (name contains 'Balance' or name contains 'Financial' or
name contains 'Audit')` is a good targeted probe — but expect it to surface unrelated hits
(police complaints, loan agreements) and treat those as noise.

## 3. Build the pack: one parent + one folder per entity

```python
def mkfolder(name, parent):
    return d.files().create(body={'name': name,
        'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent]},
        fields='id,name,webViewLink', supportsAllDrives=True).execute()['id']

def copyinto(fid, parent):   # COPY, never move — the originals stay in their project folders
    return d.files().copy(fileId=fid, body={'parents': [parent]},
        fields='id,name', supportsAllDrives=True).execute()['id']
```

- **Copy, don't move.** The entity's firm-documents folder is the record; the outbound pack is
  a snapshot. Moving would break the project folders and any links pointing at them.
- Name folders `1. <Entity>`, `2. <Entity>` … so the order matches the requester's list.
- Keep the source folder structure alone (e.g. `DRA Realty Pvt Ltd - firm related documents`,
  `Sevaganapalli Land Partners - firm related documents`) as the inventory source of truth.

## 4. Apply grants to the PARENT and EVERY subfolder

Drive does NOT cascade a parent-folder grant to existing children reliably — apply to each:

```python
for label, fid in {'ROOT': ROOT, **SUBS}.items():
    for u in USERS:                      # requester + their colleagues + DRA colleagues
        d.permissions().create(fileId=fid,
            body={'type':'user','role':'reader','emailAddress':u},
            sendNotificationEmail=False, supportsAllDrives=True,
            fields='id,role,type,emailAddress').execute()
```

- Role string on this API version is **`reader`** (not `viewer`) — see the drive-sharing
  notes in this skill's other references.
- `sendNotificationEmail=False` prevents a blast of share emails to an external party; the
  draft email carries the links instead.
- **The requester's colleagues matter** — take the full To/Cc set from their mail (`praveen@`,
  `sudheer@vgrofinserv.com`), not just the sender.
- Add the DRA-side people the user names (here `ndr@draas.com` on the mail; `psingh@draas.com`
  as a viewer) so both sides can see the same pack.

## 5. Report gaps IN THE EMAIL, do not paper over them

Where a requested document does not exist, put it in a highlighted callout box and ask a
clarifying question — this is what makes the reply useful rather than merely compliant:

- **Debt Profile** — "confirm whether you require this at promoter-entity level or group level."
- **Existing Sanction Letter** — state plainly there is no live sanction for these entities and
  ask whether a group-entity sanction serves, or whether they propose fresh credit.
- **Audited financials for partnership firms** — audit is not statutorily applicable; ITR
  filings enclosed in lieu; ask if anything further is required.
- **Project Details sheet** — say it follows separately rather than attaching a partial sheet.

Never write "as requested, please find enclosed" over a category that is empty. Same
ship-truth rule as attachments in the email-drafter skill.

## 6. Do NOT park this pack in TMP

The TMP-first rule governs files created for a session/NDR review. A pack built expressly to be
shared with an external party is the deliverable itself — create it as a named top-level folder
(e.g. `V-Gro Finserv — Consolidated Document Pack (Sep 2026)`) and share it. Flag to the user
where it lives so it can be relocated if they prefer.
