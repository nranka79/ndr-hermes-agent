#!/usr/bin/env python3
"""List current SPAM folder contents for manual review, grouped by domain.

Companion to not_spam_check.py — use for the "flag whitelist candidates"
section of the cron report: it prints every message (date | From | Subject)
PLUS a BY-DOMAIN count summary so the agent can instantly spot repeat
offenders (e.g. housing-mailer.com lead alerts) worth recommending for a
new whitelist rule.

Uses the SANCTIONED auth path: tools.gws_auth.build_service(service_name=
'google-draas') — no direct vault client calls, no token files. Runs fine
in cron terminal when invoked as:

    cd /opt/hermes && env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy \
      -u https_proxy -u ALL_PROXY -u all_proxy \
      HERMES_SESSION_USER_ID=ndr GWS_VAULT_SOCKET=/run/gws-vault/vault.sock \
      timeout 300 /opt/hermes/.venv/bin/python3 \
      /data/hermes/skills/productivity/not-spam-whitelist/scripts/list-spam.py

(env -u of the proxy vars is REQUIRED in cron — httplib2 routes Google API
calls through the SOCKS tunnel otherwise; see SKILL.md Aug 14 note.)

Usage:
    list-spam.py [max_results]   (default 200)

Read-only. Never modifies or deletes anything.
"""
import sys
from collections import Counter

sys.path.insert(0, "/opt/hermes")
from tools.gws_auth import build_service

SERVICE = "google-draas"
MAX = int(sys.argv[1]) if len(sys.argv) > 1 else 200


def main():
    gmail = build_service("gmail", "v1", service_name=SERVICE)
    prof = gmail.users().getProfile(userId="me").execute()
    print(f"Gmail account: {prof.get('emailAddress', '?')}")

    # Paginate to the cap, same as the canonical check script.
    ids = []
    page_token = None
    while True:
        resp = gmail.users().messages().list(
            userId="me", labelIds=["SPAM"], maxResults=200, pageToken=page_token
        ).execute()
        batch = resp.get("messages", [])
        ids.extend(m["id"] for m in batch)
        page_token = resp.get("nextPageToken")
        if not page_token or len(ids) >= MAX:
            break
    ids = ids[:MAX]
    print(f"{len(ids)} spam messages:")

    domains = Counter()
    for mid in ids:
        try:
            msg = gmail.users().messages().get(
                userId="me", id=mid, format="metadata",
                metadataHeaders=["From", "Subject", "Date"],
            ).execute()
            h = {x["name"].lower(): x["value"] for x in msg.get("payload", {}).get("headers", [])}
            from_raw = h.get("from", "?")
            subj = h.get("subject", "(no subject)")
            date = h.get("date", "?")
            email = from_raw.split("<")[1].split(">")[0] if "<" in from_raw and ">" in from_raw else from_raw
            dom = email.split("@")[-1].lower() if "@" in email else "?"
            domains[dom] += 1
            print(f"  - {date[:22]:22s} | {from_raw[:60]:60s} | {subj[:80]}")
        except Exception as e:
            print(f"  - ERROR fetching msg {mid}: {e}")

    print("\n--- BY DOMAIN ---")
    for d, c in domains.most_common():
        print(f"{d}: {c}")


if __name__ == "__main__":
    main()
