#!/usr/bin/env python3
"""DRAAS Drive ROOT-POLLUTION SWEEP — move session-created files out of My Drive root into TMP.

Enforces the HARD RULE in draas-drive-organization/SKILL.md:
every chat-session artifact belongs inside the root TMP folder, never at My Drive root.

Run (terminal(), NOT execute_code — the vault socket is only available in the terminal env):

    cd /opt/hermes && HERMES_SESSION_USER_ID=ndr \
      /opt/hermes/.venv/bin/python3 \
      /data/hermes/skills/productivity/draas-drive-organization/scripts/drive-root-pollution-sweep.py \
      --since 2026-09-15

Options
    --since YYYY-MM-DD   only sweep items CREATED on/after this date (default: 7 days ago)
    --account NAME       vault service name (default google-draas)
    --tmp FOLDER_ID      override the TMP folder id
    --apply              actually move. WITHOUT this flag the script is a DRY RUN.
    --passes N           repeat the sweep N times (default 3) — concurrent chat sessions drop
                         new files at root mid-sweep; re-running catches them.

Moving is non-destructive: removeParents only UNLINKS the item from root. Nothing is deleted,
file IDs, links and sharing are preserved.
"""

import argparse
import datetime as _dt
import sys
import time

sys.path.insert(0, "/opt/hermes")

from tools.gws_auth import _load_credentials_direct  # noqa: E402
from googleapiclient.discovery import build  # noqa: E402

ROOT = "0AFOc8cSaJXPGUk9PVA"                      # ndr@draas.com My Drive root
TMP = "18p74II2uL32sNDzDDwXzmlOUdJJOTmE-"         # DRAAS root TMP folder
ROOT_ALIAS = "root"                               # works in queries on any account


def build_svc(account):
    creds = _load_credentials_direct(account)
    svc = build("drive", "v3", credentials=creds)
    who = svc.about().get(fields="user").execute()["user"]["emailAddress"]
    print(f"MAILBOX: {who}")
    return svc, who


def root_items(svc, since_iso, page_size=200):
    q = f"'{ROOT_ALIAS}' in parents and trashed = false and createdTime >= '{since_iso}'"
    out, page = [], None
    while True:
        r = svc.files().list(
            q=q,
            # NOTE: `parents` is NOT selectable in a list call's fields mask (HttpError 400
            # "Invalid field selection parents") — fetch it per-file with files().get if needed.
            fields="nextPageToken,files(id,name,mimeType,createdTime,owners)",
            pageSize=page_size,
            pageToken=page,
        ).execute()
        out += r["files"]
        page = r.get("nextPageToken")
        if not page:
            break
    return out


def sweep(svc, since_iso, tmp_id, apply_changes):
    items = sorted(root_items(svc, since_iso), key=lambda f: f["createdTime"])
    if not items:
        print("  nothing at root in window")
        return 0
    moved = 0
    for f in items:
        stamp = f["createdTime"][:19]
        label = f"{stamp} | {f['name']}"
        if not apply_changes:
            print(f"  WOULD MOVE  {label}")
            continue
        try:
            svc.files().update(
                fileId=f["id"], addParents=tmp_id, removeParents=ROOT, fields="id,parents"
            ).execute()
            chk = svc.files().get(fileId=f["id"], fields="id,name,parents").execute()
            ok = tmp_id in chk.get("parents", [])
            print(f"  {'MOVED' if ok else 'VERIFY-FAIL'}  {label} -> parents {chk.get('parents')}")
            moved += 1 if ok else 0
        except Exception as e:  # noqa: BLE001 — report and keep going, never abort a sweep
            print(f"  FAIL   {label} :: {type(e).__name__} {str(e)[:180]}")
    return moved


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--since", default=None, help="YYYY-MM-DD (default: 7 days ago)")
    ap.add_argument("--account", default="google-draas")
    ap.add_argument("--tmp", default=TMP)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--apply", action="store_true", help="without this it is a DRY RUN")
    a = ap.parse_args()

    since = a.since or (_dt.date.today() - _dt.timedelta(days=7)).isoformat()
    since_iso = f"{since}T00:00:00"
    print(f"SWEEP root since {since_iso} -> TMP {a.tmp}  ({'APPLY' if a.apply else 'DRY RUN'})")

    svc, _ = build_svc(a.account)

    total = 0
    for p in range(1, a.passes + 1):
        print(f"--- pass {p}/{a.passes}")
        total += sweep(svc, since_iso, a.tmp, a.apply)
        if not a.apply:
            break
        time.sleep(3)

    if a.apply:
        left = root_items(svc, since_iso)
        print(f"\nMOVED {total}. Still at root: {len(left)}")
        for f in left:
            print("  STILL:", f["createdTime"][:19], f["name"])
        if left:
            print("  -> re-run with --passes 5, or a parallel session is actively writing "
                  "to root; report the remaining names to NDR.")
    print("DONE")


if __name__ == "__main__":
    main()
