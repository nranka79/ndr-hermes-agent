#!/usr/bin/env python3
"""
Pre-flight check for an outbound DRAAS due-diligence / investor email body.

Run this on the BUILT HTML body BEFORE creating the Gmail draft. It answers the
two questions that have actually gone wrong on this class of mail:

  1. Does every Drive folder/file link in the email resolve?  A 404 almost always
     means a folder was deleted or moved in a cleanup pass but a link survived.
  2. Does the body still carry something that must NOT go to a lender/investor —
     a financial-model spreadsheet, the internal enterprise-data tab, a case
     document, a mortgage deed, or a JDA that was pulled from the pack?

Usage:
    cd /opt/hermes && PYTHONPATH=/opt/hermes python3 \
        /path/to/verify_dd_email_links.py /tmp/roasis/new_email_body.html

    # json output for piping:
    ... verify_dd_email_links.py body.html --json

Exit code 0 = clean, 1 = at least one problem. Wire it into the handoff so a
failure cannot be reported as success.

Adapt BANNED_STRINGS / BANNED_DRIVE_IDS per matter before relying on it.
"""
from __future__ import annotations

import argparse
import json
import re
import sys

sys.path.insert(0, "/opt/hermes")

# --- things that must never appear in an externally-shared DD mail -------------
# Keep this list matter-specific. Order roughly worst-first.
BANNED_STRINGS = {
    # internal-only workbooks / folders that were deliberately removed from the pack
    "1SubaopapjqfAVGbEoIYzaG": "integrated cash-flow model spreadsheet id",
    "10ByWef6MFqscVUpV8T5SqCm": "folder 07 Group & Enterprise Data id",
    "1OHVvyvfvIXfuLGNGOnBiySHXTQD7k3Ju": "folder 08 Project Cost & Revenue id",
    "Jiraaf_IRR": "internal Jiraaf IRR tab name",
    # pulled-from-pack agreements and matter documents
    "6157": "JDA 6157 (K. Harish) — removed from the pack",
    "Harish": "K. Harish JDA counterparty — removed from the pack",
    "mortgage": "mortgage deed",
    "Mortgage": "mortgage deed",
    # case / litigation material — never goes to a lender
    "affidavit": "case document",
    "Affidavit": "case document",
    "petition": "case document",
    "Petition": "case document",
    "writ": "case document",
    "notice issued": "case document",
}

DRIVE_URL_RE = re.compile(
    r"https://(?:drive|docs)\.google\.com/(?:drive/folders|file/d|spreadsheets/d|document/d)/([A-Za-z0-9_-]{20,})"
)
FOLDER_HINTS = ("/drive/folders/", "/file/d/")


def unique_ids(html: str) -> list[str]:
    seen: list[str] = []
    for m in DRIVE_URL_RE.finditer(html):
        if m.group(1) not in seen:
            seen.append(m.group(1))
    return seen


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("body_html")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--service-name", default="google-draas")
    args = ap.parse_args()

    html = open(args.body_html, encoding="utf-8").read()
    problems: list[str] = []

    # ---- 1. banned content scan (no network needed) --------------------------
    banned_hits = [
        f"{label}  (matched {token!r})"
        for token, label in BANNED_STRINGS.items()
        if token in html
    ]
    problems += [f"BANNED CONTENT: {b}" for b in banned_hits]

    # ---- 2. link resolution --------------------------------------------------
    ids = unique_ids(html)
    link_report = []
    try:
        from tools.gws_auth import build_service

        drive = build_service("drive", "v3", service_name=args.service_name)
        for fid in ids:
            try:
                f = drive.files().get(
                    fileId=fid,
                    fields="id,name,mimeType,trashed",
                    supportsAllDrives=True,
                ).execute()
                trashed = bool(f.get("trashed"))
                link_report.append(
                    {
                        "id": fid,
                        "name": f.get("name", ""),
                        "mimeType": (f.get("mimeType") or "").split(".")[-1],
                        "trashed": trashed,
                        "ok": not trashed,
                    }
                )
                if trashed:
                    problems.append(f"TRASHED LINK: {f.get('name')} ({fid})")
            except Exception as e:  # noqa: BLE001 - surface any Drive error verbatim
                link_report.append({"id": fid, "ok": False, "error": str(e)[:160]})
                problems.append(f"BROKEN LINK: {fid} -> {str(e)[:160]}")
    except Exception as e:  # noqa: BLE001
        problems.append(f"COULD NOT CHECK LINKS (Drive auth/build failed): {e}")
        link_report = [{"id": i, "ok": None} for i in ids]

    # ---- 3. structural assertions worth having -------------------------------
    headings = re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.S)
    headings = [re.sub(r"<[^>]+>", "", h).strip() for h in headings]
    if any(h.startswith("12.") for h in headings):
        problems.append("STRUCTURE: a section 12 heading exists — sections were not renumbered")
    if any("MIS" in h and h.startswith("10.") for h in headings[:20]):
        problems.append("STRUCTURE: '10. MIS' heading still present — Section 10 was meant to be deleted")

    result = {
        "body": args.body_html,
        "drive_links_found": len(ids),
        "headings": headings,
        "links": link_report,
        "problems": problems,
        "clean": not problems,
    }

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"body: {args.body_html}  ({len(html):,} chars)")
        print(f"headings: {len(headings)} -> {headings}")
        print(f"drive links: {len(ids)}")
        for r in link_report:
            flag = "OK  " if r.get("ok") else ("??  " if r.get("ok") is None else "FAIL")
            print(f"  {flag} {r.get('name', r.get('error', ''))[:66]}")
        if problems:
            print("\nPROBLEMS:")
            for p in problems:
                print("  !", p)
        else:
            print("\nCLEAN — no banned content, all links resolve.")

    return 0 if not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
