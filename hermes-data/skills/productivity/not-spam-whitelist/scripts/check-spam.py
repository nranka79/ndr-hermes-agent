#!/usr/bin/env python3
"""Not-spam whitelist check — reads rules from sheet, moves matching spam to inbox.

Uses vault-based GWS token (gws-vault-server daemon at /run/gws-vault/vault.sock),
accessed via the sanctioned tools.gws_vault_client path with the canonical
vault uid + service key resolved at runtime.

FIXED (Jul 11, 2026): previously called tools.gws_vault_client.get_token()
directly with user_id="ndr@draas.com", service="google" -- a key that was
NEVER the real storage key, so it always raised VaultNoTokenError regardless
of whether the token was valid. Real storage key is the canonical vault uid
("ndr-<telegram-id>") + service "google-draas" (confirmed via has_token() against
the live vault -- returned True the whole time). See SKILL.md "OAuth Tokens"
section and references/jul-11-wrong-vault-key-bug.md for the full writeup.

FIXED (Jul 12, 2026): tools.gws_auth.load_credentials() builds Credentials
from HERMES_GWS_SCOPES (10 scopes, including 3 Photos) instead of the token's
own scopes (7, no Photos). The next creds.refresh() call requests the union
and Google rejects with 'invalid_scope: Bad Request'. get_creds() now
builds Credentials directly from tok["scopes"], which is the authoritative
scope list. See references/jul-12-scope-mismatch-bypass.md for the
diagnostic transcript and the verification that the bypass works in cron
context (confirmed live 2026-07-12 15:31 UTC — 3 spam emails checked, 0 moved,
no auth URL needed).

Run from cron:
    /opt/hermes/.venv/bin/python3 /data/hermes/skills/productivity/not-spam-whitelist/scripts/check-spam.py
"""
import json, os, sys, tempfile, traceback
from datetime import datetime, timezone

sys.path.insert(0, "/opt/hermes")
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from tools.gws_vault_client import get_token, resolve
from tools.gws_auth import load_credentials  # noqa: F401  -- kept for diagnostic helpers

SHEET_ID = "1w8_R0JzfHP1PIdPoCFpqdhDh9TFU0qPqbt3V2vfDyw0"
SHEET_RANGE = "Whitelist!A:I"
DRAAS_DOMAIN = "@draas.com"
DRAAS_UID = "ndr@draas.com"        # resolved to the canonical vault uid inside load_credentials()
DRAAS_SERVICE = "google-draas"     # actual vault service key -- NOT "google" (see Jul 11, 2026 fix above)

# ── column indices (0-based, A=0) ─────────────────────────────────────
#  0  A  #
#  1  B  Category
#  2  C  From Email / Domain   ← matching value
#  3  D  To Email
#  4  E  Subject Keywords
#  5  F  Content Description
#  6  G  Rule Type             ← exact_from / domain_from / etc.
#  7  H  Date Added
#  8  I  Notes


def get_creds():
    """Get credentials with auto-refresh, bypassing the Jul 12 scope-mismatch bug.

    tools.gws_auth.load_credentials() builds Credentials from the env constant
    HERMES_GWS_SCOPES (10 scopes, includes 3 Photos the ndr@draas.com token was
    never authorized for). When creds.refresh() runs, Google rejects with
    'invalid_scope: Bad Request'. See references/jul-12-scope-mismatch-bypass.md
    for the full diagnostic transcript.

    Workaround: build Credentials from the token's own scope list (the
    authoritative list — what the refresh token was actually authorized for).
    This works identically to load_credentials for all other purposes
    (auto-refreshes, builds googleapiclient services normally). The only
    difference: it does NOT write a refreshed token back to the vault.
    For a single cron run that's fine — the next refresh happens on the
    following cron tick.
    """
    uid = resolve("email", DRAAS_UID)
    tok = json.loads(get_token(uid, DRAAS_SERVICE, session_uid=uid))
    scopes = tok.get("scopes") or []
    creds = Credentials.from_authorized_user_info(tok, scopes)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def read_whitelist(sheets):
    r = sheets.spreadsheets().values().get(
        spreadsheetId=SHEET_ID, range=SHEET_RANGE
    ).execute()
    rows = r.get("values", [])
    if not rows or len(rows) < 2:
        return []
    rules = []
    for i, row in enumerate(rows[1:], 2):
        if len(row) < 3:
            continue
        rules.append({
            "row_num": i,
            "category": (row[1] if len(row) > 1 else "").strip(),
            "from_value": (row[2] if len(row) > 2 else "").strip(),
            "to_email": (row[3] if len(row) > 3 else "").strip(),
            "subject_kw": (row[4] if len(row) > 4 else "").strip(),
            "content_desc": (row[5] if len(row) > 5 else "").strip(),
            "rule_type": (row[6] if len(row) > 6 else "").strip().lower(),
        })
    return rules


def _domain_match(sender_email, from_value):
    """Match sender email against a domain rule value.

    Handles three value formats stored in the sheet:
    - Starts with '@' (e.g. '@draas.com')      → suffix match on the whole value
    - Contains '@' but is a full address        → extract domain after '@', check suffix
      (e.g. 'creditcardalerts@kotak.bank.in' → match '@kotak.bank.in')
    - No '@' (e.g. 'manipalhospitals.com')      → prepend '@', check suffix
    """
    se = sender_email.lower().strip()
    fv = from_value.lower().strip()
    if not fv:
        return False
    if fv.startswith("@"):
        return se.endswith(fv)
    if "@" in fv:
        domain = fv.split("@", 1)[1]
        return se.endswith("@" + domain)
    return se.endswith("@" + fv)


def _subj_match(subject, kw_text):
    """Check if subject contains any comma-separated keyword."""
    if not subject or not kw_text:
        return False
    sl = subject.lower().strip()
    keywords = [k.strip().lower()
                for k in kw_text.replace("\n", ",").split(",")
                if k.strip()]
    return any(k in sl for k in keywords)


def matches_rule(sender_email, subject, rule):
    rt = rule["rule_type"]
    fv = rule["from_value"]
    kw = rule["subject_kw"]
    if rt == "exact_from":
        return sender_email.lower() == fv.lower()
    elif rt == "domain_from":
        return _domain_match(sender_email, fv)
    elif rt == "subject_contains":
        return _subj_match(subject, kw) if kw and subject else False
    elif rt == "combined":
        return _domain_match(sender_email, fv) and (
            _subj_match(subject, kw) if kw and subject else True
        )
    return False


def main():
    print(f"=== Not-Spam Whitelist Check === {datetime.now(timezone.utc).isoformat()}")

    try:
        creds = get_creds()
    except Exception as e:
        print(f"\n❌ TOKEN ERROR: {e}")
        traceback.print_exc()
        print()
        return

    sheets = build("sheets", "v4", credentials=creds)
    gmail = build("gmail", "v1", credentials=creds)

    prof = gmail.users().getProfile(userId="me").execute()
    print(f"Gmail account: {prof.get('emailAddress', '?')}")

    # Identity guard — see SKILL.md "⚠️ Jul 13, 2026 — google-draas slot
    # holds the WRONG Google account". A clean token read + valid scopes
    # is not proof the right human is behind the token. Verify the
    # authenticated identity before proceeding; the Sheets API 403 will
    # look like a sheet-share issue and waste diagnostic time otherwise.
    expected = "ndr@draas.com"
    actual = prof.get("emailAddress", "").lower()
    if actual != expected:
        print(
            f"\n{'=' * 60}\n"
            f"❌ VAULT SLOT MISCONFIG\n"
            f"{'=' * 60}\n"
            f"google-draas authenticates as '{prof.get('emailAddress')}', "
            f"not '{expected}'.\n"
            f"\n"
            f"The token is valid but holds the wrong Google account.\n"
            f"Likely cause: a recent re-auth was completed with the wrong\n"
            f"account signed in, and the callback state resolved via\n"
            f"canonical_uid() to this same uid + service slot.\n"
            f"\n"
            f"FIX: re-authorize {expected} with state=ndr@draas.com to\n"
            f"overwrite the bad slot. Use env-var client credentials\n"
            f"(HERMES_OAUTH_CLIENT_ID / HERMES_OAUTH_CLIENT_SECRET).\n"
            f"After the callback completes, the next cron tick picks up\n"
            f"the corrected token automatically.\n"
            f"\n"
            f"See references/jul-13-wrong-account-in-vault-slot.md for\n"
            f"the full transcript and a one-line diagnostic.\n"
            f"{'=' * 60}\n"
        )
        # Hard stop — do NOT fall through to a partial run. A misconfig
        # is a config bug, not a transient state; it deserves a human
        # looking at the report, not a quietly-degraded cron run.
        return

    rules = read_whitelist(sheets)
    if not rules:
        print("No whitelist rules found.")
        return
    print(f"Read {len(rules)} whitelist rules\n")
    for r in rules:
        print(f"  Rule {r['row_num']}: [{r['rule_type']}] "
              f"{r['from_value'][:50]} kw={r['subject_kw'][:40] or '-'}")

    spam = gmail.users().messages().list(
        userId="me", labelIds=["SPAM"], maxResults=200
    ).execute()
    msgs = spam.get("messages", [])
    if not msgs:
        print("\nNo spam messages to check.")
        return
    print(f"\nFound {len(msgs)} messages in SPAM\n")

    moved, errors = [], []
    checked = no_match = via_skipped = 0

    for summ in msgs:
        mid = summ["id"]
        try:
            msg = gmail.users().messages().get(
                userId="me", id=mid, format="metadata",
                metadataHeaders=["From", "Subject", "To"]
            ).execute()
            headers = {h["name"]: h["value"] for h in msg["payload"]["headers"]}
            sender = headers.get("From", "")
            subject = headers.get("Subject", "")
            sender_email = sender.split("<")[-1].rstrip(">") if "<" in sender else sender
        except Exception as e:
            errors.append(f"Msg {mid} fetch fail: {e}")
            continue

        checked += 1

        # ── @draas.com catch-all (From-only rule) ─────────────────
        if sender_email.lower().endswith(DRAAS_DOMAIN):
            if " via " in sender.lower():
                via_skipped += 1
                print(f"  [{sender[:60]}] -> @draas.com 'via' pattern — SKIP")
                continue
            print(f"  [{sender_email}] -> @draas.com catch-all", end="")
            try:
                gmail.users().messages().modify(
                    userId="me", id=mid,
                    body={"removeLabelIds": ["SPAM"], "addLabelIds": ["INBOX"]}
                ).execute()
                moved.append({"from": sender, "subject": subject,
                              "rule": "@draas.com catch-all"})
                print(" MOVED")
            except Exception as e:
                errors.append(f"Move {sender_email} fail: {e}")
            continue

        # ── Whitelist rules ───────────────────────────────────────
        matched = False
        for r in rules:
            if matches_rule(sender_email, subject, r):
                print(f"  [{sender_email}] -> rule [{r['rule_type']}] "
                      f"{r['from_value'][:50]}", end="")
                try:
                    gmail.users().messages().modify(
                        userId="me", id=mid,
                        body={"removeLabelIds": ["SPAM"],
                              "addLabelIds": ["INBOX"]}
                    ).execute()
                    moved.append({
                        "from": sender, "subject": subject,
                        "rule": f"{r['rule_type']}:{r['from_value']}"
                    })
                    print(" MOVED")
                except Exception as e:
                    errors.append(f"Move {sender_email} fail: {e}")
                matched = True
                break

        if not matched:
            no_match += 1

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'=' * 50}")
    print(f"RESULTS: {checked} checked, {len(moved)} moved, "
          f"{no_match} unmatched, {via_skipped} via-skipped, "
          f"{len(errors)} errors")
    print(f"{'=' * 50}")
    if moved:
        print("\nMoved to inbox:")
        for m in moved:
            s = m["subject"][:80] if m["subject"] else "(no subject)"
            print(f"  ✅ {m['from'][:60]} — \"{s}\" ({m['rule']})")
    if errors:
        print(f"\nErrors ({len(errors)}):")
        for e in errors:
            print(f"  ❌ {e}")


if __name__ == "__main__":
    main()
