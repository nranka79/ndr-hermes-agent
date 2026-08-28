#!/usr/bin/env python3
"""Update a native Google Doc DPR section in place via the Docs API.

Pattern: find a placeholder paragraph by substring, delete it, insert replacement
text at the same location. Use this instead of files().update with docx media —
a native Google Doc's mimeType cannot be changed by media upload.

Usage: adjust DPS below (doc_id -> marker substring + lines), then run from the
Hermes venv with the vault identity, e.g.:
  HERMES_SESSION_USER_ID=psingh /opt/hermes/.venv/bin/python3 dpr_google_doc_update.py
"""
from tools.gws_auth import build_service

DOCS = build_service('docs', 'v1', service_name='google-draas')

# Example: Section 5.2 competitor analysis fill. doc_id + marker + lines.
DPS = {
    # "amber": {
    #     "doc_id": "<doc id>",
    #     "marker": "Benchmarking against nearby competing projects",
    #     "lines": [
    #         "Benchmarking against nearby competing projects in Whitefield (Aug 2026):",
    #         "• Project A — Premium 3 BHK — ~₹XX,XXX/sq.ft (source, date)",
    #         "Positioning: <own-rate> is priced X vs band Y, supporting margin Z.",
    #         "Sources: <label>: <url>",
    #     ],
    # },
}

def main():
    for key, cfg in DPS.items():
        doc_id = cfg["doc_id"]
        d = DOCS.documents().get(documentId=doc_id).execute()
        target = None
        for item in d.get('body', {}).get('content', []):
            para = item.get('paragraph')
            if not para:
                continue
            text = ''.join(e.get('textRun', {}).get('content', '') for e in para.get('elements', []))
            if cfg["marker"] in text:
                target = (item['startIndex'], item['endIndex'], text)
                break
        if not target:
            print(f"[{key}] marker not found: {cfg['marker']!r}")
            continue
        start, end, old = target
        repl = "\n".join(cfg["lines"])
        DOCS.documents().batchUpdate(documentId=doc_id, body={'requests': [
            {'deleteContentRange': {'range': {'startIndex': start, 'endIndex': end}}},
            {'insertText': {'location': {'index': start}, 'text': repl + "\n"}},
        ]}).execute()
        print(f"[{key}] updated at {start}-{end}")
    print("DONE")

if __name__ == '__main__':
    main()