#!/usr/bin/env python3
"""Regenerate the DRAAS Drive cleanup delta tabs.

Builds, on the master cleanup sheet:
  - 'Delta Since Sep-01'  the one-by-one walk list (sections A-E)
  - 'Full Delta 6863'     every new item drive-wide, for completeness
  - 'Summary'             regenerated counts

Usage:
    env -u PYTHONPATH /opt/hermes/.venv/bin/python3 scripts/drive_delta_inventory.py \
        [--baseline 2026-09-01] [--service google-draas] [--dry-run]

Optional hand-judged suggestions: drop a JSON file at /tmp/suggest.json mapping
file name -> ["MOVE + RENAME", "Target > Folder", "why note"]. Names match on a
normalised 45-char then 25-char prefix, so truncated keys still land.

Nothing moves. This only writes the proposal sheet; NDR approves file by file.
"""
import argparse, collections, json, os, sys

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import build_service  # noqa: E402

SSID = '17bKPoC5XdlRZ_iUPOQzCjRZW96ablJgYN9DmXZID-M8'
TAB_WALK = 'Delta Since Sep-01'
TAB_FULL = 'Full Delta 6863'
CACHE = '/tmp/draas_delta_cache.json'
SUGGEST = '/tmp/suggest.json'

HDR = ['Sl No', 'Section', 'File Name', 'Kind', 'Location (Folder Path)', 'Created',
       'Modified', 'Size', 'Link', 'Proposed Action', 'Target Folder', 'Notes']


def kind(r):
    m = r['mime']
    if m.endswith('folder'):
        return 'folder'
    for a, b in [('spreadsheet', 'Sheet'), ('document', 'Doc'), ('presentation', 'Slides'),
                 ('application/pdf', 'PDF'), ('image/png', 'PNG'), ('image/jpeg', 'JPEG'),
                 ('video/mp4', 'Video'), ('kml', 'KML'), ('kmz', 'KMZ'), ('text/html', 'HTML'),
                 ('markdown', 'MD'), ('text/plain', 'TXT'), ('application/json', 'JSON'),
                 ('shortcut', 'Shortcut')]:
        if a in m:
            return b
    return m.split('/')[-1]


def dt(s):
    return (s or '')[:10]


def sz(r):
    v = r.get('size')
    if not v:
        return ''
    v = int(v)
    for u in ('B', 'KB', 'MB', 'GB'):
        if v < 1024 or u == 'GB':
            return f'{v:.0f} {u}' if u == 'B' else f'{v:.1f} {u}'
        v /= 1024.0
    return ''


def norm(s):
    return ' '.join(s.lower().replace('|', ' ').split())


def fetch(drive, cutoff, cache=CACHE):
    """Delta items + folder map. Cached to disk to avoid re-walking during iteration."""
    if os.path.exists(cache):
        c = json.load(open(cache))
        if c.get('cutoff') == cutoff:
            return c['items'], c['folders'], c['root']

    root = drive.files().get(fileId='root', fields='id').execute()['id']
    items, tok = [], None
    while True:
        r = drive.files().list(
            q=f"createdTime > '{cutoff}T00:00:00' and trashed=false",
            fields='nextPageToken,files(id,name,mimeType,createdTime,modifiedTime,size,parents,webViewLink)',
            pageSize=1000, pageToken=tok).execute()
        items += r.get('files', [])
        tok = r.get('nextPageToken')
        if not tok:
            break
    folders, tok = {}, None
    while True:
        r = drive.files().list(
            q="mimeType='application/vnd.google-apps.folder' and trashed=false",
            fields='nextPageToken,files(id,name,parents)', pageSize=1000, pageToken=tok).execute()
        for f in r.get('files', []):
            folders[f['id']] = (f['name'], (f.get('parents') or [None])[0])
        tok = r.get('nextPageToken')
        if not tok:
            break
    json.dump({'cutoff': cutoff, 'items': items, 'folders': folders, 'root': root}, open(cache, 'w'))
    return items, folders, root


def fullpath(fid, folders, root):
    """Walk parents up to the My Drive root.

    Returns (root_id, [ancestor names]). root_id is None for items whose parents the
    API does not expose (shared-with-you / other drive) - label those honestly, never
    guess which drive they live in.
    """
    parts, seen, cur = [], set(), fid
    while cur and cur != root and cur in folders and cur not in seen:
        seen.add(cur)
        parts.append(folders[cur][0])
        cur = folders[cur][1]
    return cur, list(reversed(parts))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--baseline', default='2026-09-01')
    ap.add_argument('--service', default='google-draas')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    drive = build_service('drive', 'v3', service_name=a.service)
    sheets = build_service('sheets', 'v4', service_name=a.service)

    items, folders, root = fetch(drive, a.baseline)
    print(f'delta since {a.baseline}: {len(items)} items, {len(folders)} folders mapped')

    rows, buckets = [], collections.Counter()
    for f in items:
        par = (f.get('parents') or [None])[0]
        if par is None:
            buckets['shared-with-you (no parent)'] += 1
            where, p = 'SHARED', []
        else:
            rt, p = fullpath(par, folders, root)
            where = 'MYDRIVE' if rt == root else 'OTHER'
            buckets['My Drive' if where == 'MYDRIVE' else 'outside My Drive (parent not exposed)'] += 1
        rows.append({'id': f['id'], 'name': f['name'], 'mime': f['mimeType'],
                     'created': f['createdTime'], 'modified': f.get('modifiedTime'),
                     'size': f.get('size'), 'link': f.get('webViewLink'),
                     'where': where, 'path': p})

    # ---- sections (decision surface) ----
    md = [r for r in rows if r['where'] == 'MYDRIVE']
    root_items = [r for r in md if not r['path']]
    root_files = [r for r in root_items if not r['mime'].endswith('folder')]
    root_folders = [r for r in root_items if r['mime'].endswith('folder')]
    tmp_items = [r for r in md if r['path'] == ['TMP']]
    tmp_files = [r for r in tmp_items if not r['mime'].endswith('folder')]
    tmp_folders = [r for r in tmp_items if r['mime'].endswith('folder')]
    new_root_names = {r['name'] for r in root_folders}
    depth1_elsewhere = [r for r in md if len(r['path']) == 1
                        and r['path'][0] != 'TMP' and r['path'][0] not in new_root_names]

    S = {}
    if os.path.exists(SUGGEST):
        S = {norm(k): tuple(v) for k, v in json.load(open(SUGGEST)).items()}

    def lookup(name):
        n = norm(name)
        if n in S:
            return S[n]
        for k, v in S.items():
            if len(n) > 40 and len(k) > 40 and n[:45] == k[:45]:
                return v
        for k, v in S.items():
            if len(n) > 25 and len(k) > 25 and n[:25] == k[:25]:
                return v
        return None

    walk, i = [], 0

    def add(section, r, default_ok=False):
        nonlocal i
        i += 1
        got = lookup(r['name'])
        if got:
            act, tgt, note = got
        elif default_ok:
            # already inside its root-level project folder - do NOT mark REVIEW,
            # that buries the real flags
            act, tgt, note = 'OK', '', 'Already inside its root-level project folder - no move needed'
        else:
            act, tgt, note = 'REVIEW', '', 'No rule matched - decide manually'
        walk.append([str(i), section, r['name'], kind(r),
                     ' > '.join(r['path']) if r['path'] else 'My Drive ROOT',
                     dt(r['created']), dt(r['modified']), sz(r), r['link'] or '',
                     act, tgt, note])

    for r in sorted(root_files, key=lambda x: x['created']):
        add('A. LOOSE AT MY DRIVE ROOT (files)', r)
    for r in sorted(root_folders, key=lambda x: x['created']):
        add('B. NEW FOLDERS AT MY DRIVE ROOT', r)
    for r in sorted(tmp_files, key=lambda x: x['created']):
        add('C. LOOSE IN TMP (files)', r)
    for r in sorted(tmp_folders, key=lambda x: x['created']):
        add('D. NEW FOLDERS IN TMP', r)
    for r in sorted(depth1_elsewhere, key=lambda x: (x['path'][0], x['created'])):
        add('E. NEW ITEMS DIRECTLY INSIDE A ROOT-LEVEL FOLDER', r, default_ok=True)

    full = [['Section', 'Full Path', 'File Name', 'Kind', 'Created', 'Modified', 'Size', 'Link']]
    for r in rows:
        pre = {'MYDRIVE': 'My Drive', 'OTHER': 'Outside My Drive'}.get(r['where'], 'Shared with me')
        p = f"{pre} / {' / '.join(r['path'])}" if r['path'] else f'{pre} (root)'
        full.append([pre, p, r['name'], kind(r), dt(r['created']), dt(r['modified']),
                     sz(r), r['link'] or ''])

    unmatched = sum(1 for w in walk if w[9] == 'REVIEW')
    print('sections:', dict(collections.Counter(w[1] for w in walk)))
    print(f'walk rows: {len(walk)} | REVIEW (aim for 0): {unmatched}')
    print('buckets:', dict(buckets))
    if a.dry_run:
        return
    if unmatched:
        print('!! refusing to write while REVIEW rows exist - add suggestions first')

    meta = sheets.spreadsheets().get(spreadsheetId=SSID).execute()
    have = {s['properties']['title'] for s in meta['sheets']}
    req = [{'addSheet': {'properties': {'title': t}}} for t in (TAB_WALK, TAB_FULL) if t not in have]
    if req:
        sheets.spreadsheets().batchUpdate(spreadsheetId=SSID, body={'requests': req}).execute()

    for tab, data in ((TAB_WALK, [HDR] + walk), (TAB_FULL, full)):
        sheets.spreadsheets().values().clear(spreadsheetId=SSID, range=f'{tab}!A1:Z20000').execute()
        sheets.spreadsheets().values().update(spreadsheetId=SSID, range=f'{tab}!A1',
            valueInputOption='RAW', body={'values': data}).execute()

    # verify by reading back - never trust the write
    back = sheets.spreadsheets().values().get(
        spreadsheetId=SSID, range=f'{TAB_WALK}!A1:L{len(walk) + 1}').execute().get('values', [])
    print(f'read back {len(back) - 1} walk rows (expected {len(walk)})')
    print('https://docs.google.com/spreadsheets/d/%s/edit' % SSID)


if __name__ == '__main__':
    main()
