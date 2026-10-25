#!/usr/bin/env python3
"""Sync Google Contacts names into the DRA WhatsApp directory.

Runs **inside the Hermes container**, because that is the only place with vault access to the
operator's Google OAuth tokens. The WhatsApp bridge therefore never holds a Google credential:
it only ever receives name/number pairs over its token-authenticated /v1 API.

    host: /opt/hermes/hermes-agent/tools/wa_contacts_sync.py
    container: /opt/hermes/tools/wa_contacts_sync.py

Environment:
    HERMES_SESSION_USER_ID   vault user id whose tokens to use (e.g. ndr-7449813913)
    WA_BASE_URL              default https://wa.ahfl.in
    WA_SERVICE_TOKEN         bridge service token
    WA_DEFAULT_CC            default country code for bare national numbers (default 91)
    WA_CONTACT_SERVICES      comma separated vault service names to pull

Privacy: this script logs counts only. It never prints a name or a phone number, because its
output goes to a cron log file.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/hermes")
sys.path.insert(0, "/opt/hermes/tools")

DEFAULT_SERVICES = ["google-ahfl", "google-draas", "google-gmail", "google-o3infotech"]
# E.164 allows at most 15 digits; a national number is at least 10 in the geographies we care
# about. Anything outside that is a shortcode, a landline fragment, or several numbers that were
# pasted into one field (the probe found 21-digit values).
MIN_DIGITS = 10
MAX_DIGITS = 15


def normalise_phone(raw: str, canonical: str | None, default_cc: str = "91") -> str | None:
    """Return E.164 digits without the '+', or None when the value is not dialable.

    Google supplies `canonicalForm` for ~97% of numbers and it is already E.164, so it is
    trusted when present. The remainder were measured and fall into these shapes:
      bare 10 digits            -> national, prepend the default country code
      leading 0 / 00            -> trunk or international prefix, strip it
      3-9 digits                -> shortcode or partial landline, reject
      16+ digits                -> several numbers in one field, reject
    """
    source = canonical or raw or ""
    digits = re.sub(r"\D", "", source)
    if not digits:
        return None

    if canonical:
        # Already E.164; only guard against obvious corruption.
        return digits if MIN_DIGITS <= len(digits) <= MAX_DIGITS else None

    if digits.startswith("00"):
        digits = digits[2:]
    digits = digits.lstrip("0")

    if len(digits) == MIN_DIGITS:
        digits = f"{default_cc}{digits}"

    if len(digits) < MIN_DIGITS or len(digits) > MAX_DIGITS:
        return None
    return digits


def pick_name(person: dict) -> str | None:
    """Prefer the name the operator chose; fall back to an organisation for business entries."""
    for n in person.get("names") or []:
        display = (n.get("displayName") or "").strip()
        if display:
            return display
    for o in person.get("organizations") or []:
        name = (o.get("name") or "").strip()
        if name:
            return name
    return None


def better(a: dict, b: dict) -> dict:
    """Deterministic winner when two Google accounts disagree about one number.

    Prefers a real name over a digits-only label, then the longer name. Deterministic matters:
    a cron job that reshuffles names every run would be worse than one that picks imperfectly.
    """
    a_name, b_name = a["displayName"], b["displayName"]
    a_digity = a_name.replace(" ", "").replace("+", "").isdigit()
    b_digity = b_name.replace(" ", "").replace("+", "").isdigit()
    if a_digity != b_digity:
        return b if a_digity else a
    if len(a_name) != len(b_name):
        return a if len(a_name) > len(b_name) else b
    return a if a_name <= b_name else b


def collect(service_name: str, default_cc: str) -> tuple[dict[str, dict], dict]:
    from gws_auth import build_service

    svc = build_service("people", "v1", service_name)
    merged: dict[str, dict] = {}
    seen = skipped = 0
    token = None
    while True:
        resp = (
            svc.people()
            .connections()
            .list(
                resourceName="people/me",
                pageSize=1000,
                pageToken=token,
                personFields="names,phoneNumbers,organizations",
            )
            .execute()
        )
        for person in resp.get("connections", []):
            seen += 1
            name = pick_name(person)
            if not name:
                skipped += 1
                continue
            orgs = person.get("organizations") or []
            org = (orgs[0].get("name") if orgs else None) or None
            given = family = None
            for n in person.get("names") or []:
                given = given or (n.get("givenName") or None)
                family = family or (n.get("familyName") or None)
            for ph in person.get("phoneNumbers") or []:
                e164 = normalise_phone(ph.get("value", ""), ph.get("canonicalForm"), default_cc)
                if not e164:
                    skipped += 1
                    continue
                entry = {
                    "phoneE164": e164,
                    "displayName": name,
                    "givenName": given,
                    "familyName": family,
                    "organisation": org,
                    "sourceRef": person.get("resourceName"),
                }
                merged[e164] = better(merged[e164], entry) if e164 in merged else entry
        token = resp.get("nextPageToken")
        if not token:
            break
    return merged, {"service": service_name, "contactsSeen": seen, "numbersUsable": len(merged), "skipped": skipped}


def post_directory(base_url: str, token: str, entries: list[dict], contacts_seen: int, skipped: int) -> dict:
    payload = json.dumps(
        {
            "source": "google",
            # All Google identities are merged into one row-per-number set, so the join in the
            # chat list stays one-to-one and no two accounts fight over the same number.
            "sourceAccount": "all-google",
            "entries": entries,
            "contactsSeen": contacts_seen,
            "skipped": skipped,
        }
    ).encode()
    req = urllib.request.Request(
        f"{base_url.rstrip('/')}/v1/directory/sync",
        data=payload,
        headers={"content-type": "application/json", "X-WA-Service-Token": token},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode())


def self_test() -> int:
    cases = [
        # (raw, canonical, expected)
        ("+91 98200 00000", "+919820000000", "919820000000"),
        ("9820000000", None, "919820000000"),          # bare national -> default cc
        ("09820000000", None, "919820000000"),         # trunk prefix stripped
        ("00919820000000", None, "919820000000"),      # international prefix stripped
        ("+1 415 555 0100", "+14155550100", "14155550100"),
        ("121", None, None),                           # shortcode
        ("12345678", None, None),                      # landline fragment, 8 digits
        ("123456789012345678901", None, None),         # several numbers in one field
        ("", None, None),
        ("abc", None, None),
        ("+62 812 0000 000", "+628120000000", "628120000000"),
    ]
    failures = 0
    for raw, canon, expected in cases:
        got = normalise_phone(raw, canon)
        if got != expected:
            failures += 1
            print(f"FAIL normalise_phone(len={len(raw)}, canonical={bool(canon)}) -> {got!r}, expected {expected!r}")
    name_cases = [
        ({"names": [{"displayName": "Madhur"}]}, "Madhur"),
        ({"organizations": [{"name": "Marudhar Traders"}]}, "Marudhar Traders"),
        ({"names": [{"displayName": "  "}], "organizations": [{"name": "Tehalka"}]}, "Tehalka"),
        ({}, None),
    ]
    for person, expected in name_cases:
        got = pick_name(person)
        if got != expected:
            failures += 1
            print(f"FAIL pick_name -> {got!r}, expected {expected!r}")
    # better() must be deterministic and prefer a real name over a digit label
    a = {"displayName": "+919820000000"}
    b = {"displayName": "Madhur"}
    if better(a, b)["displayName"] != "Madhur" or better(b, a)["displayName"] != "Madhur":
        failures += 1
        print("FAIL better() did not prefer a real name over a numeric label")
    print("self-test: " + ("PASS" if failures == 0 else f"{failures} FAILURES"))
    return 1 if failures else 0


def main() -> int:
    if "--self-test" in sys.argv:
        return self_test()

    base_url = os.environ.get("WA_BASE_URL", "https://wa.ahfl.in")
    token = os.environ.get("WA_SERVICE_TOKEN", "")
    default_cc = os.environ.get("WA_DEFAULT_CC", "91")
    services = [s.strip() for s in os.environ.get("WA_CONTACT_SERVICES", ",".join(DEFAULT_SERVICES)).split(",") if s.strip()]
    if not token:
        print("WA_SERVICE_TOKEN is not set", file=sys.stderr)
        return 2
    if not os.environ.get("HERMES_SESSION_USER_ID"):
        print("HERMES_SESSION_USER_ID is not set; cannot choose whose tokens to load", file=sys.stderr)
        return 2

    merged: dict[str, dict] = {}
    reports = []
    total_seen = total_skipped = 0
    for service_name in services:
        try:
            part, report = collect(service_name, default_cc)
        except Exception as exc:  # one broken account must not sink the whole sync
            print(f"{service_name}: FAILED ({type(exc).__name__})", file=sys.stderr)
            reports.append({"service": service_name, "error": type(exc).__name__})
            continue
        for phone, entry in part.items():
            merged[phone] = better(merged[phone], entry) if phone in merged else entry
        reports.append(report)
        total_seen += report["contactsSeen"]
        total_skipped += report["skipped"]
        print(f"{service_name}: contacts={report['contactsSeen']} usable_numbers={report['numbersUsable']} skipped={report['skipped']}")

    if not merged:
        print("no usable contacts collected; refusing to wipe the directory", file=sys.stderr)
        return 1

    entries = list(merged.values())
    try:
        result = post_directory(base_url, token, entries, total_seen, total_skipped)
    except urllib.error.HTTPError as exc:
        print(f"bridge rejected the sync: HTTP {exc.code}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"bridge unreachable: {type(exc).__name__}", file=sys.stderr)
        return 1

    cov = result.get("coverage", {})
    print(
        f"pushed merged_numbers={len(entries)} accepted={result.get('accepted')} rejected={result.get('rejected')} "
        f"directory_entries={cov.get('directory_entries')} "
        f"named_dms={cov.get('dm_chats_labelled')}/{cov.get('dm_chats_with_messages')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
