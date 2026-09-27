#!/usr/bin/env python3
"""Publish or update a DRA Content artifact by driving content-api directly.

Use this instead of the content_publish tool when the artifact is large or
image-bearing (the tool carries file content as JSON string arguments, so a
multi-MB base64 payload cannot be passed through it, and it refuses binary
extensions outright).

Drives the same endpoint the tool uses, with the same auth model:
    Authorization: Bearer <service token>   -- transport credential
    X-DRA-On-Behalf-Of: <acting human>      -- ACL is evaluated as this person

Usage:
  # publish a new artifact from a directory (must contain index.html)
  python3 publish_artifact.py --dir ./pub2 --title "..." --project "Ranka Oasis" \
      --type comparison --category Design --tags "Ranka Oasis,Godrej Florenne"

  # update an existing artifact (new version, same ID + URL)
  python3 publish_artifact.py --dir ./pub2 --artifact DRA-ART-2026-000024 \
      --change-summary "Rebuilt as single-file: render origin blocks external files"

  # dry run: report sizes and payload, do not POST
  python3 publish_artifact.py --dir ./pub2 --title "..." --dry-run

Never prints the service token.
"""
import argparse
import base64
import json
import os
import sys
import urllib.error
import urllib.request

TEXT_EXT = (".html", ".htm", ".css", ".js", ".mjs", ".json", ".csv", ".txt", ".md", ".svg")


def build_files(directory):
    if not os.path.isdir(directory):
        sys.exit(f"not a directory: {directory}")
    names = sorted(os.listdir(directory))
    if "index.html" not in names:
        sys.exit("directory must contain index.html (it is the entry file)")
    files = []
    for name in names:
        path = os.path.join(directory, name)
        if not os.path.isfile(path):
            continue
        ext = os.path.splitext(name)[1].lower()
        if ext not in TEXT_EXT:
            print(f"  skip {name} (not a supported text type)")
            continue
        raw = open(path, "rb").read()
        files.append({
            "path": name,
            "content_b64": base64.b64encode(raw).decode("ascii"),
        })
        print(f"  {name:16} {len(raw)/1024:9.1f} KB")
    if not files:
        sys.exit("no publishable files found")
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True, help="directory holding index.html (+ any text assets)")
    ap.add_argument("--title")
    ap.add_argument("--artifact", help="existing human_id -> publish a NEW VERSION instead of a new artifact")
    ap.add_argument("--change-summary", default="Initial version")
    ap.add_argument("--description")
    ap.add_argument("--type", default="document")
    ap.add_argument("--project")
    ap.add_argument("--entity")
    ap.add_argument("--category")
    ap.add_argument("--tags", default="", help="comma-separated")
    ap.add_argument("--actor", default="ndr@draas.com",
                    help="the human the ACL is evaluated as (X-DRA-On-Behalf-Of)")
    ap.add_argument("--timeout", type=float, default=180.0)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base = os.environ.get("DRA_CONTENT_API_URL", "").rstrip("/")
    token = os.environ.get("DRA_CONTENT_SERVICE_TOKEN", "")
    if not base or not token:
        sys.exit("DRA_CONTENT_API_URL / DRA_CONTENT_SERVICE_TOKEN not set in this environment")

    print(f"reading {args.dir}")
    files = build_files(args.dir)

    if args.artifact:
        url = f"{base}/api/artifacts/{args.artifact}/versions"
        body = {"files": files, "change_summary": args.change_summary}
    else:
        if not args.title:
            sys.exit("--title is required when publishing a NEW artifact")
        url = f"{base}/api/artifacts"
        body = {
            "title": args.title,
            "files": files,
            "entry_file": "index.html",
            "description": args.description,
            "artifact_type": args.type,
            "project": args.project,
            "entity": args.entity,
            "category": args.category,
            "tags": [t.strip() for t in args.tags.split(",") if t.strip()],
            "source_session_id": args.change_summary,
            "change_summary": args.change_summary,
        }
        body = {k: v for k, v in body.items() if v is not None}

    payload = json.dumps(body).encode("utf-8")
    print(f"\nPOST {url}")
    print(f"payload {len(payload)/1024/1024:.2f} MB")
    if args.dry_run:
        print("dry run -- not posting")
        return

    req = urllib.request.Request(url, data=payload, method="POST", headers={
        "Authorization": f"Bearer {token}",
        "X-DRA-On-Behalf-Of": args.actor,
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=args.timeout) as r:
            out = json.load(r)
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.read().decode("utf-8", "replace")[:1500])
        sys.exit(1)

    print("\nOK")
    for k in ("human_id", "title", "current_version", "url"):
        if k in out:
            print(f"  {k}: {out[k]}")
    print("\nNEXT: verify it actually RENDERS (a 200 proves nothing).")
    print("  shell:  <url>            (behind SSO)")
    print("  iframe: grep the src= of view.content.ahfl.in out of the shell, then")
    print("          load that capability URL directly -- no login needed -- and")
    print("          look at the page + console.")


if __name__ == "__main__":
    main()