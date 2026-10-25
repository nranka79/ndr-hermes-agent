#!/usr/bin/env python3
"""Drive inventory -> cleanup spreadsheet (DRAAS / NDR).

Fetches the N most recently CREATED files (owned + shared with me), computes
folder paths and cleanup heuristics, then builds a Google Sheets inventory on
the same Drive account with a Summary tab. Re-runnable; safe to re-run (creates
a NEW spreadsheet each run).

Usage:
    cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 \
        /data/hermes/skills/productivity/draas-drive-organization/scripts/drive-inventory-sheet.py

Notes:
- Must run via terminal() with the Hermes venv python (system python3 lacks
  googleapiclient; execute_code sandbox has no vault socket).
- Verify the AUTHED AS line == the account you meant before trusting output.
- First successful run: 2026-09-01, canonical sheet
  17bKPoC5XdlRZ_iUPOQzCjRZW96ablJgYN9DmXZID-M8 (stale after re-runs).
"""
import sys, json, re, os, time
sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service

SERVICE = 'google-draas'
TOP_N = 500

svc = build_service('drive', 'v3', service_name=SERVICE)
sheets = build_service('sheets', 'v4', service_name=SERVICE)
about = svc.about().get(fields='user').execute()
EMAIL = about['user']['emailAddress']
print("AUTHED AS:", EMAIL)

q = "( 'me' in owners or sharedWithMe = true ) and trashed = false and mimeType != 'application/vnd.google-apps.folder'"
files = []
page_token = None
while True:
    res = svc.files().list(
        q=q, pageSize=1000, pageToken=page_token,
        fields='nextPageToken, files(id,name,mimeType,createdTime,modifiedTime,webViewLink,size,owners,parents,shared)',
        orderBy='createdTime desc', supportsAllDrives=True).execute()
    files.extend(res.get('files', []))
    page_token = res.get('nextPageToken')
    if not page_token or len(files) >= TOP_N:
        break
files = files[:TOP_N]
print("FETCHED:", len(files))

folder_cache = {}
def get_folder(fid):
    if fid in folder_cache:
        return folder_cache[fid]
    try:
        f = svc.files().get(fileId=fid, fields='id,name,parents').execute()
        folder_cache[fid] = f
        return f
    except Exception:
        folder_cache[fid] = None
        return None

def get_location(f):
    """Full folder path. A folder with an empty/missing parents array IS My Drive
    root -- do NOT call about().get(fields='rootFolderId') (400 Invalid field)."""
    parents = f.get('parents') or []
    if not parents:
        return 'Shared with me (direct)'
    cur = parents[0]
    parts = []
    seen = set()
    depth = 0
    while cur and depth < 10:
        if cur in seen:
            break
        seen.add(cur)
        fo = get_folder(cur)
        if not fo:
            parts.append('?')
            break
        grand = fo.get('parents') or []
        if not grand:                      # no parents => this is drive root
            if not parts:
                return 'My Drive (root)'
            break
        parts.append(fo['name'])
        cur = grand[0]
        depth += 1
    if not parts:
        return 'My Drive (root)'
    return ' > '.join(reversed(parts))

MIME_SHORT = {
    'application/vnd.google-apps.document': 'Doc',
    'application/vnd.google-apps.spreadsheet': 'Sheet',
    'application/vnd.google-apps.presentation': 'Slides',
    'application/vnd.google-apps.drawing': 'Drawing',
    'application/vnd.google-apps.form': 'Form',
    'application/vnd.google-apps.map': 'MyMap',
    'application/pdf': 'PDF', 'application/zip': 'ZIP',
    'image/png': 'PNG', 'image/jpeg': 'JPG', 'image/gif': 'GIF',
    'image/webp': 'WEBP', 'image/svg+xml': 'SVG',
    'text/plain': 'TXT', 'text/csv': 'CSV', 'text/html': 'HTML',
    'application/msword': 'DOC',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document': 'DOCX',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': 'XLSX',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation': 'PPTX',
}
def short_kind(mt):
    if mt in MIME_SHORT:
        return MIME_SHORT[mt]
    if mt and mt.startswith('image/'): return 'IMG'
    if mt and mt.startswith('video/'): return 'VID'
    if mt and mt.startswith('audio/'): return 'AUD'
    return mt.split('.')[-1][:12] if mt else '?'

def human_size(sz):
    try:
        sz = int(sz)
    except (TypeError, ValueError):
        return ''
    if sz < 1024: return f"{sz} B"
    if sz < 1048576: return f"{sz/1024:.0f} KB"
    if sz < 1073741824: return f"{sz/1048576:.1f} MB"
    return f"{sz/1073741824:.2f} GB"

def norm(s):
    return re.sub(r'[^a-z0-9]', '', s.lower())

def suggest(name, loc, all_norms, this_norm):
    acts = []
    low = name.lower()
    generic = (
        re.match(r'^(untitled|new document|copy|document|doc|sheet|slide|drawing|export)\b', low)
        or re.search(r'\((\d+)\)$', name)
        or re.search(r'(?i)\b(copy|final|final[0-9]|draft|new)\b', low)
        or re.search(r'[ _-]v\d+[._ -]?\d*$', name)
        or bool(re.search(r'(?i)-(\d+|final)$', name))
    )
    if generic:
        acts.append('Review name')
    if loc == 'My Drive (root)':
        acts.append('File into folder')
    if all_norms[this_norm] > 1:
        acts.append('Possible duplicate/merge')
    m = re.match(r'(?i)^\s*(copy of|copy)\s+(.*)$', name.strip())
    if m and norm(m.group(2)) in all_norms:
        acts.append('Copy of existing - merge')
    return '; '.join(acts) if acts else 'OK'

rows = []
all_norms = {}
for f in files:
    n = norm(f.get('name', ''))
    all_norms[n] = all_norms.get(n, 0) + 1

for f in files:
    name = f.get('name', '')
    loc = get_location(f)
    owner_list = f.get('owners') or []
    owner = 'Me' if (owner_list and owner_list[0].get('me')) else (owner_list[0].get('emailAddress') if owner_list else '?')
    rows.append({
        'name': name,
        'kind': short_kind(f.get('mimeType', '')),
        'loc': loc,
        'created': f.get('createdTime', '')[:10],
        'modified': f.get('modifiedTime', '')[:10],
        'owner': owner,
        'size': human_size(f.get('size')),
        'link': f.get('webViewLink', ''),
        'action': suggest(name, loc, all_norms, norm(name)),
    })
rows.sort(key=lambda r: r['created'], reverse=True)

with open('/tmp/drive_inventory.json', 'w') as fp:
    json.dump({'email': EMAIL, 'rows': rows}, fp, indent=1)

name = f"{time.strftime('%Y%m%d')}_Drive_Inventory_Recent_500_Files_Cleanup_Sheet"
created = svc.files().create(body={'name': name, 'mimeType': 'application/vnd.google-apps.spreadsheet'},
                             fields='id, webViewLink').execute()
ss_id = created['id']
smeta = sheets.spreadsheets().get(spreadsheetId=ss_id, fields='sheets.properties').execute()
sheet_title = smeta['sheets'][0]['properties']['title']
sheet_meta_id = smeta['sheets'][0]['properties']['sheetId']

header = ["Sl No", "File Name", "Kind", "Location (Folder Path)", "Created",
          "Modified", "Owner", "Size", "Link", "Cleanup Suggestion"]
values = [header]
for i, r in enumerate(rows, 1):
    link_val = f'=HYPERLINK("{r["link"]}","open")' if r['link'] else ''
    values.append([i, r['name'], r['kind'], r['loc'], r['created'], r['modified'],
                   r['owner'], r['size'], link_val, r['action']])
sheets.spreadsheets().values().batchUpdate(
    spreadsheetId=ss_id,
    body={'valueInputOption': 'USER_ENTERED',
          'data': [{'range': f'{sheet_title}!A1:J{len(values)}', 'values': values}]}).execute()

sheets.spreadsheets().batchUpdate(spreadsheetId=ss_id, body={'requests': [
    {"repeatCell": {"range": {"sheetId": sheet_meta_id, "startRowIndex": 0, "endRowIndex": 1},
                    "cell": {"userEnteredFormat": {"textFormat": {"bold": True},
                                                   "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}}},
                    "fields": "userEnteredFormat.textFormat.bold,userEnteredFormat.backgroundColor"}},
    {"updateSheetProperties": {"properties": {"sheetId": sheet_meta_id, "gridProperties": {"frozenRowCount": 1}},
                               "fields": "gridProperties.frozenRowCount"}},
    {"autoResizeDimensions": {"dimensions": {"sheetId": sheet_meta_id, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 4}}},
    {"autoResizeDimensions": {"dimensions": {"sheetId": sheet_meta_id, "dimension": "COLUMNS", "startIndex": 8, "endIndex": 9}}},
]}).execute()

summary_rows = [
    ["DRAAS Drive Cleanup - Summary", ""],
    ["Generated", "2026-09-01"],
    ["Account", EMAIL],
    ["Files inventoried (most recent by created time)", len(rows)],
    ["", ""],
    ["Files at My Drive root (need filing)", len([r for r in rows if r['loc'] == 'My Drive (root)'])],
    ["Files flagged for rename review", len([r for r in rows if 'Review name' in r['action']])],
    ["Files flagged as possible duplicate/merge", len([r for r in rows if 'duplicate' in r['action'] or 'Copy of' in r['action']])],
    ["Files already OK", len([r for r in rows if r['action'] == 'OK'])],
    ["", ""],
    ["Tip: Filter column J (Cleanup Suggestion) to see what needs attention.", ""],
    ["Tip: Column I has clickable links to each file.", ""],
]
res = sheets.spreadsheets().batchUpdate(spreadsheetId=ss_id, body={'requests': [{"addSheet": {"properties": {"title": "Summary"}}}]}).execute()
sm_id = res['replies'][0]['addSheet']['properties']['sheetId']
sheets.spreadsheets().values().update(
    spreadsheetId=ss_id, range='Summary!A1:B12',
    body={'values': summary_rows}, valueInputOption='USER_ENTERED').execute()

print("DONE")
print("FINAL_LINK:", created['webViewLink'])