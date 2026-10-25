#!/usr/bin/env python3
"""Extract text from every file in a Google Drive folder and keyword-scan it.

Use for relevance triage of a document folder / evidence pack: "keep only the documents
related to <person>". Prints files WITH hits and files with NO extractable text, and writes
a full analysis.json for classification.

Usage (MUST run inside terminal(), not execute_code -- the sandbox has no vault socket):

  cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 \
    /data/hermes/skills/productivity/draas-drive-organization/scripts/drive-doc-pack-extract.py \
    <FOLDER_ID> '<keyword-regex>' [outdir] [service_name]

Example keyword regex (name + co-allottee + unit + case no):
  'behera|sabyasachi|damayan|b1[ -/]?203|0006093'

Outputs in <outdir> (default /tmp/pack_scan):
  list.json      - Drive listing: name, id, mimeType, size
  downloaded.json- local path map
  analysis.json  - per file: method, text_len, n_hits, hits, snippets, head

Stdlib only for extraction (no openpyxl / pymupdf needed). Requires: pdftotext, pdftoppm,
tesseract, strings. Re-run safe (skips already-downloaded files).

PITFALL BAKED IN: classification keys use the Drive `name` field verbatim. Never build a
keep/delete key from a display tag like mimeType.split('.')[-1] -- for macro-enabled files
that yields artifacts such as "[12]".
"""
import io
import json
import os
import re
import subprocess
import sys
import zipfile

sys.path.insert(0, '/opt/hermes')
from tools.gws_auth import _load_credentials_direct                      # noqa: E402
from googleapiclient.discovery import build                              # noqa: E402
from googleapiclient.http import MediaIoBaseDownload                     # noqa: E402


def safe(name):
    return re.sub(r'[^A-Za-z0-9._-]', '_', name)


def strip_tags(text):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', text))


def pdf_text(path, pages=25):
    r = subprocess.run(['pdftotext', '-layout', '-f', '1', '-l', str(pages), path, '-'],
                       capture_output=True, timeout=120)
    return r.stdout.decode('utf-8', 'ignore')


def ocr_pdf(path, pages=2):
    out = []
    for p in range(1, pages + 1):
        subprocess.run(['pdftoppm', '-f', str(p), '-l', str(p), '-r', '150', '-gray',
                        '-png', path, '/tmp/_ocrpg'], capture_output=True, timeout=180)
        for cand in (f'/tmp/_ocrpg-{p}.png', f'/tmp/_ocrpg-0{p}.png'):
            if os.path.exists(cand):
                out.append(subprocess.run(['tesseract', cand, 'stdout'],
                                          capture_output=True, timeout=180)
                           .stdout.decode('utf-8', 'ignore'))
                os.remove(cand)
    return '\n'.join(out)


def xlsx_text(path):
    out = []
    with zipfile.ZipFile(path) as z:
        for n in z.namelist():
            if n.endswith('.xml') and ('sharedStrings' in n or 'sheet' in n):
                out.append(strip_tags(z.read(n).decode('utf-8', 'ignore')))
    return ' '.join(out)


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        return strip_tags(z.read('word/document.xml').decode('utf-8', 'ignore'))


def strings_text(path):
    r = subprocess.run(['strings', '-n', '4', path], capture_output=True, timeout=180)
    return r.stdout.decode('utf-8', 'ignore')


def html_text(path):
    t = open(path, encoding='utf-8', errors='ignore').read()
    t = re.sub(r'<style.*?</style>', ' ', t, flags=re.S | re.I)
    t = re.sub(r'<script.*?</script>', ' ', t, flags=re.S | re.I)
    return strip_tags(t)


def img_ocr(path):
    return subprocess.run(['tesseract', path, 'stdout'],
                          capture_output=True, timeout=240).stdout.decode('utf-8', 'ignore')


def extract(path, ext, mime):
    """Return (text, method). Scanned PDFs fall back to OCR of pages 1-2 and are tagged
    'ocr2pg' -- treat those as 'first 2 pages only', not as a full-text verdict."""
    try:
        if ext == '.pdf' or mime == 'application/pdf':
            t = pdf_text(path)
            if len(t.strip()) < 80:
                return ocr_pdf(path, 2), 'ocr2pg'
            return t, 'pdftotext'
        if ext in ('.xlsx', '.xlsm'):
            return xlsx_text(path), 'xlsx'
        if ext == '.docx':
            return docx_text(path), 'docx'
        if ext in ('.doc', '.bin', '.mpp', '.xls'):
            return strings_text(path), 'strings'
        if ext in ('.html', '.htm'):
            return html_text(path), 'html'
        if ext in ('.jpg', '.jpeg', '.png'):
            return img_ocr(path), 'imgocr'
        if ext in ('.csv', '.md', '.txt'):
            return open(path, encoding='utf-8', errors='ignore').read(), 'text'
        return strings_text(path), 'strings'
    except Exception as e:                                                # noqa: BLE001
        return f'EXTRACT_ERROR {e}', 'error'


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    folder, pattern = sys.argv[1], sys.argv[2]
    outdir = sys.argv[3] if len(sys.argv) > 3 else '/tmp/pack_scan'
    service_name = sys.argv[4] if len(sys.argv) > 4 else 'google-draas'
    os.makedirs(outdir, exist_ok=True)

    svc = build('drive', 'v3', credentials=_load_credentials_direct(service_name))
    print('AUTH AS:', svc.about().get(fields='user(emailAddress)')
          .execute()['user']['emailAddress'], flush=True)

    items, token = [], None
    while True:
        res = svc.files().list(q=f"'{folder}' in parents and trashed=false",
                               fields='nextPageToken, files(id,name,mimeType,size)',
                               pageSize=200, pageToken=token,
                               supportsAllDrives=True, includeItemsFromAllDrives=True).execute()
        items.extend(res.get('files', []))
        token = res.get('nextPageToken')
        if not token:
            break
    json.dump(items, open(f'{outdir}/list.json', 'w'), indent=1)
    print(f'files in folder: {len(items)}', flush=True)

    rx = re.compile(pattern, re.I)
    results = []
    for i, it in enumerate(items, 1):
        if it['mimeType'] == 'application/vnd.google-apps.folder':
            continue
        path = os.path.join(outdir, safe(it['name']))
        if not os.path.exists(path):
            try:
                with open(path, 'wb') as fh:
                    dl = MediaIoBaseDownload(fh, svc.files().get_media(fileId=it['id']),
                                             chunksize=8 * 1024 * 1024)
                    done = False
                    while not done:
                        _, done = dl.next_chunk()
            except Exception as e:                                        # noqa: BLE001
                print('DL FAIL', it['name'], e, flush=True)
                continue
        ext = os.path.splitext(it['name'])[1].lower()
        text, method = extract(path, ext, it['mimeType'])
        hits = [m.group(0).lower() for m in rx.finditer(text)]
        snips = [re.sub(r'\s+', ' ', text[max(0, m.start() - 70):m.end() + 70])
                 for m in list(rx.finditer(text))[:4]]
        results.append({
            'name': it['name'], 'id': it['id'], 'ext': ext, 'method': method,
            'text_len': len(text), 'n_hits': len(hits), 'hits': sorted(set(hits)),
            'snips': snips, 'head': re.sub(r'\s+', ' ', text[:300]),
        })
        if i % 20 == 0:
            print(f'  scanned {i}/{len(items)}', flush=True)

    json.dump(results, open(f'{outdir}/analysis.json', 'w'), indent=1)
    hit = [r for r in results if r['n_hits']]
    noext = [r for r in results if r['text_len'] < 80]
    print(f'\nTOTAL {len(results)} | HITS {len(hit)} | NO TEXT {len(noext)}', flush=True)
    print('\n=== HITS (read the snippets -- counts false-positive on amounts/IDs) ===')
    for r in hit:
        print(f"[{r['n_hits']}] {r['name']} -> {r['hits']}")
    print('\n=== NO / FIRST-2-PAGES-ONLY TEXT (verify manually, do NOT call these irrelevant) ===')
    for r in noext:
        print(f"({r['method']}) {r['name']}")
    print(f'\nFull detail: {outdir}/analysis.json')


if __name__ == '__main__':
    main()
