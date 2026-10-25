#!/usr/bin/env python3
"""Recursive file/subfolder counter for Google Drive folder trees.

Why this exists: sweep/dedupe jobs get reported to NDR as totals, and a wrong
count is visible and costly. This implements the counting rules that are
actually correct:

  * a FRESH nextPageToken per folder (reusing one across sibling folders
    silently truncates or duplicates results -- the resulting undercount
    looks perfectly plausible, so you will not suspect it)
  * global dedupe by file id (a file with two parents would double-count)
  * only non-folder mime types count as "files"
  * prints files + subfolders, so the arithmetic is auditable

Usage (MUST run from terminal(), never execute_code -- the gws vault socket is
not present in the sandbox):

    cd /opt/hermes && HERMES_SESSION_USER_ID=ndr /opt/hermes/.venv/bin/python3 \\
        /data/hermes/skills/productivity/draas-drive-organization/scripts/count-drive-tree.py \\
        "*Ranka Amber"=1oBDneKVz7wpC0IheGIE0rW9LNWrHXcHo \\
        "*Ranka Amber"=1A3Foefaxfs39rzNPQOIxRNR8zTybXxPo

Arguments are LABEL=FOLDER_ID (or a bare FOLDER_ID, labelled with the id).
Quote labels containing spaces or *. Cross-check the result by also passing the
PARENT folder that contains the buckets -- total nodes should reconcile.

Set GWS_SERVICE to override the vault service key (default google-draas).
"""
import os
import sys

sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service  # noqa: E402

SERVICE = os.environ.get("GWS_SERVICE", "google-draas")
FOLDER_MIME = "application/vnd.google-apps.folder"


def walk(drv, fid, seen):
    """Walk one folder. Fresh page token per call. Returns (n_files, subfolder_ids)."""
    files, subs, tok = 0, [], None
    while True:
        resp = drv.files().list(
            q=f"'{fid}' in parents and trashed=false",
            fields="nextPageToken,files(id,mimeType)",
            pageSize=1000,
            pageToken=tok,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
        ).execute()
        for f in resp.get("files", []):
            if f["id"] in seen:
                continue
            seen.add(f["id"])
            if f["mimeType"] == FOLDER_MIME:
                subs.append(f["id"])
            else:
                files += 1
        tok = resp.get("nextPageToken")
        if not tok:
            break
    return files, subs


def main(roots):
    drv = build_service("drive", "v3", service_name=SERVICE)
    seen = set()
    tot_files = tot_dirs = 0
    for label, rid in roots:
        n, stack = walk(drv, rid, seen)
        subfolders = 0
        while stack:
            fc, deeper = walk(drv, stack.pop(), seen)
            n += fc
            subfolders += 1
            stack += deeper
        tot_files += n
        tot_dirs += subfolders
        print(f"{label[:40]:40} {n:5d} files {subfolders:4d} subfolders")
    print(f"{'TOTAL (recursive, deduped)':40} {tot_files:5d} files {tot_dirs:4d} subfolders")
    print(f"# nodes = {tot_files} files + {tot_dirs} subfolders = {tot_files + tot_dirs}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    roots = []
    for a in args:
        if "=" in a:
            label, fid = a.split("=", 1)
        else:
            label, fid = a, a
        roots.append((label, fid))
    main(roots)
