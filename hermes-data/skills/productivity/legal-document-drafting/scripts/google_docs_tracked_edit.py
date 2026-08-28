#!/usr/bin/env python3
"""Google Docs tracked edit — NEW version with yellow highlights (DRAAS legal deed pattern).

Performs delete+insert+highlight edits on a Google Doc via the Docs API,
preserving original run styles. Used for "generate a new version, HIGHLIGHT THE CHANGES"
requests (R3N KAAJ partnership deed v2→v3→v4 workflow).

Usage:
  # 1. Copy the source doc FIRST (never edit the original):
  #    drive.files().copy(fileId=SRC_ID, body={'name': '20260825_..._v4'})
  # 2. Fill EDIT_SPECS below, then:
  #    python google_docs_tracked_edit.py <DOC_ID>

EDIT_SPECS fields:
  marker     — unique substring that identifies the target paragraph (must match exactly, incl. tabs)
  region_old — exact text to delete within that paragraph; '' = whole paragraph text
  insert     — replacement text; '' = deletion only (empty insert is SKIPPED — atomic batch guard)
  hl         — substring of the FINAL paragraph text to highlight yellow;
               '' = highlight the whole insert / whole new paragraph; '__WHOLE__' = whole paragraph

Run with the active Hermes venv: sys.path needs /opt/hermes on it (tools.gws_auth).
"""
import sys
sys.path.insert(0, '/opt/hermes')

from tools.gws_auth import build_service  # per-user gws-vault token; service_name from gws_resolve_account

SERVICE = 'google-draas'  # e.g. psingh@draas.com

# EXAMPLE specs from the R3N KAAJ NoSchedule edit (16 edits, v4). Replace with your own.
EDIT_SPECS = [
    # Full-paragraph rewrite: marker finds the para, region_old '' replaces the whole text
    dict(marker='The Second Partner was a partner of M/s. Satvik Developers', region_old='',
         insert='B. \tThe Second Partner, Mr. Ashok Kumar, presently holds title ... (new recital text).',
         hl=''),
    # Substring edit: swap one phrase, highlight the insert
    dict(marker='deployed by the Second Partner to the First Partner',
         region_old='the immovable properties allocated to Mr. C.R. Nagendra',
         insert='the FIRST PARTNER LANDS described in Recital C above',
         hl='FIRST PARTNER LANDS described in Recital C above'),
    # Pure deletion (skip insert): empty paragraph, keep trailing newline
    dict(marker='(d) \tReferences to the Partition Deed', region_old='__DELETE__', insert='', hl=''),
]

HIGHLIGHT = {'color': {'rgbColor': {'red': 1.0, 'green': 1.0, 'blue': 0.0}}}


def main(doc_id):
    docs = build_service('docs', 'v1', service_name=SERVICE)
    doc = docs.documents().get(documentId=doc_id).execute()
    body = doc.get('body', {}).get('content', [])

    def para_text(p):
        # CRITICAL: text lives at element['textRun']['content'], NOT element.get('text')
        return ''.join(r.get('textRun', {}).get('content', '') for r in p.get('elements', []) if 'textRun' in r)

    paras = []
    def walk(blocks, incell=False):
        for el in blocks:
            if 'paragraph' in el:
                paras.append({'start': el['startIndex'], 'end': el['endIndex'],
                              'text': para_text(el['paragraph']), 'para': el['paragraph']})
            elif 'table' in el:  # content can live inside tables
                for row in el['table'].get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        walk(cell.get('content', []), True)
    walk(body)

    def style_at(p, abs_idx):
        for r in p['para'].get('elements', []):
            if 'textRun' in r and r['startIndex'] <= abs_idx < r['endIndex']:
                return r['textRun'].get('textStyle', {})
        return {}

    def style_mask(sty):
        keys = ['bold', 'italic', 'underline', 'strikethrough', 'smallCaps', 'fontSize',
                'weightedFontFamily', 'foregroundColor', 'baselineOffset']
        present = [k for k in keys if k in sty]
        if not present:
            return None, None
        return ','.join(present), {k: sty[k] for k in present}

    plan = []
    for ed in EDIT_SPECS:
        hits = [p for p in paras if ed['marker'] in p['text']]
        assert len(hits) == 1, f"MARKER not unique/found: {ed['marker'][:50]} -> {len(hits)} hits"
        p = hits[0]
        content = p['text'][:-1]  # drop trailing newline
        body_start, body_end = p['start'], p['end'] - 1
        if ed['region_old'] == '__DELETE__':
            r_start, r_end, final_text, insert = body_start, body_end, '', ''
        elif ed['region_old'] == '':
            r_start, r_end, final_text, insert = body_start, body_end, ed['insert'], ed['insert']
        else:
            rel = content.find(ed['region_old'])
            assert rel >= 0, f"REGION not found: {ed['region_old'][:60]!r}"
            r_start = body_start + rel
            r_end = r_start + len(ed['region_old'])
            final_text = content[:rel] + ed['insert'] + content[rel + len(ed['region_old']):]
            insert = ed['insert']
        sty = style_at(p, r_start)
        mask, style_obj = style_mask(sty)
        plan.append((p['start'], ed, body_start, r_start, r_end, final_text, insert, mask, style_obj))

    plan.sort(key=lambda x: x[0], reverse=True)  # DESCENDING: lower indices stay valid

    requests = []
    for pstart, ed, body_start, r_start, r_end, final_text, insert, mask, style_obj in plan:
        requests.append({'deleteContentRange': {'range': {'startIndex': r_start, 'endIndex': r_end}}})
        if insert:  # empty insertText rejects the whole atomic batch — skip it
            requests.append({'insertText': {'location': {'index': r_start}, 'text': insert}})
            if mask:
                requests.append({'updateTextStyle': {
                    'range': {'startIndex': r_start, 'endIndex': r_start + len(insert)},
                    'textStyle': style_obj, 'fields': mask}})
        if ed['hl'] and final_text:
            hl_text = final_text if ed['hl'] == '__WHOLE__' else ed['hl']
            hl_rel = final_text.find(hl_text)
            assert hl_rel >= 0, f"HL not found: {hl_text[:60]!r}"
            requests.append({'updateTextStyle': {
                'range': {'startIndex': body_start + hl_rel, 'endIndex': body_start + hl_rel + len(hl_text)},
                'textStyle': {'backgroundColor': HIGHLIGHT}, 'fields': 'backgroundColor'}})

    print(f"Requests: {len(requests)}")
    docs.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
    print("batchUpdate OK")

    # Verification: banned terms must be 0, key phrases present, highlights > 0
    for term in ['Satvik', 'Nagendra']:  # example banned terms — set per task
        count = sum(p['text'].count(term) for p in paras)
        print(f"term {term!r} (pre-edit baseline): {count}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    main(sys.argv[1])