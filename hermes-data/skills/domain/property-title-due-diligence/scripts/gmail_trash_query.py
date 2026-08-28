#!/usr/bin/env python3
"""Paginated Gmail search + count + trash with dry-run default.

Usage:
  python3 gmail_trash_query.py --query 'from:x subject:"y"' [--service google-draas] [--apply]

Default is DRY-RUN (prints match count, trashes nothing). Add --apply to trash.
Prints JSON: {account, matched, trashed}. Run from a terminal with GWS vault env
(HERMES_SESSION_USER_ID / GWS_VAULT_SOCKET / GWS_VAULT_SECRET), e.g. via cron.

Pitfalls baked in:
  - counts real message IDs (never trusts resultSizeEstimate)
  - default scope excludes Trash/Spam — pass --anywhere to include them
"""
import argparse
import json
import sys

sys.path.insert(0, "/opt/hermes")

from tools.gws_auth import build_service, has_token

SERVICES = ["google-draas", "google-ahfl", "google-gmail"]


def collect_ids(gm, query):
    ids = []
    page_token = None
    while True:
        req = {"userId": "me", "q": query, "maxResults": 500}
        if page_token:
            req["pageToken"] = page_token
        resp = gm.users().messages().list(**req).execute()
        ids.extend(m["id"] for m in resp.get("messages", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return ids


def run(query, service, apply, anywhere):
    if not has_token(service):
        return {"service": service, "status": "no_token"}
    if anywhere and not query.lower().startswith("in:anywhere"):
        query = f"in:anywhere {query}"
    gm = build_service("gmail", "v1", service_name=service)
    profile = gm.users().getProfile(userId="me").execute()
    ids = collect_ids(gm, query)
    trashed = 0
    if apply:
        for mid in ids:
            gm.users().messages().trash(userId="me", id=mid).execute()
            trashed += 1
    return {
        "service": service,
        "account": profile.get("emailAddress", "?"),
        "query": query,
        "matched": len(ids),
        "trashed": trashed if apply else "dry-run (use --apply)",
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--query", required=True, help="Gmail search query")
    ap.add_argument("--service", default="google-draas", choices=SERVICES)
    ap.add_argument("--apply", action="store_true", help="actually trash (default dry-run)")
    ap.add_argument("--anywhere", action="store_true", help="include Trash+Spam via in:anywhere")
    args = ap.parse_args()

    result = run(args.query, args.service, args.apply, args.anywhere)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
