#!/usr/bin/env python3
"""Verify a DRA Content artifact version WITHOUT depending on the render route's bytes.

    python3 verify_artifact_version.py DRA-ART-2026-000024 [path/to/local/index.html]

Why this exists: `/a/{id}` answers in two shapes (a 200 shell carrying the iframe,
or a 302 to a signed capability URL whose body is empty), and that signed URL is
usually NOT fetchable server-side (403 — it wants browser cookies). So the cheap,
honest check is API metadata + a size-identity comparison against the local build,
followed by a browser load of /a/{id}/v/{n} for the actual render check.

Prints:
  * title, current_version, canonical URL
  * every version: number, size_bytes, file_count, entry_file, publication_status
  * SIZE IDENTITY: latest version's size_bytes vs the local file (if given)
  * the shell route's status code and the signed capability URL from Location
  * whether that capability URL is fetchable server-side (a 403 is EXPECTED)

Reads DRA_CONTENT_API_URL and DRA_CONTENT_SERVICE_TOKEN from the environment.
Never prints the token. Stdlib only.
"""
import json
import os
import sys
import urllib.error
import urllib.request

ON_BEHALF = os.environ.get("DRA_ON_BEHALF_OF", "ndr@draas.com")


def creds():
    base = (os.environ.get("DRA_CONTENT_API_URL") or "").rstrip("/")
    token = os.environ.get("DRA_CONTENT_SERVICE_TOKEN") or ""
    if not base or not token:
        sys.exit(
            "Set DRA_CONTENT_API_URL and DRA_CONTENT_SERVICE_TOKEN first "
            "(both are in the Hermes environment; never hardcode them)."
        )
    return base, token


def headers(token):
    return {
        "Authorization": f"Bearer {token}",
        "X-DRA-On-Behalf-Of": ON_BEHALF,
    }


def get(url, token, follow=True):
    """Return (status, body_bytes, headers). Does not raise on 4xx/5xx."""
    opener = urllib.request.build_opener() if follow else urllib.request.build_opener(NoRedirect)
    req = urllib.request.Request(url, headers=headers(token))
    try:
        with opener.open(req, timeout=120) as r:
            return r.status, r.read(), dict(r.headers)
    except urllib.error.HTTPError as e:
        try:
            body = e.read()
        except Exception:
            body = b""
        return e.code, body, dict(e.headers or {})
    except Exception as e:  # noqa: BLE001 - report, never crash the check
        return "ERR", str(e).encode(), {}


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    art = sys.argv[1]
    local_path = sys.argv[2] if len(sys.argv) > 2 else None
    base, token = creds()

    # --- artifact metadata -------------------------------------------------
    status, body, _ = get(f"{base}/api/artifacts/{art}", token)
    if status != 200:
        sys.exit(f"could not read artifact {art}: HTTP {status} {body[:200]!r}")
    meta = json.loads(body)
    cur = meta.get("current_version")
    print(f"title            : {meta.get('title')}")
    print(f"current_version  : {cur}")
    print(f"url              : {meta.get('url')}")
    print(f"project/category : {meta.get('project')} / {meta.get('category')}")

    # --- version list ------------------------------------------------------
    status, body, _ = get(f"{base}/api/artifacts/{art}/versions", token)
    latest = None
    if status == 200:
        versions = json.loads(body)
        print("\nversions:")
        for v in versions:
            n = v.get("version_number")
            print(
                f"  v{n:<3} size={v.get('size_bytes'):>9} files={v.get('file_count')} "
                f"entry={v.get('entry_file')} status={v.get('publication_status')}"
            )
            if n == cur:
                latest = v
        if latest:
            note = (latest.get("change_summary") or "").strip().replace("\n", " ")
            print(f"\n  current change_summary: {note[:300]}")
        print("\n  NOTE: `checksum` is NOT the sha256 of the stored file -- do not use it")
        print("        for byte identity. size_bytes + entry_file + file_count are the ones that match.")
    else:
        print(f"\nversions: HTTP {status}")

    # --- size identity ----------------------------------------------------
    if local_path and latest:
        try:
            n = os.path.getsize(local_path)
        except OSError as e:
            print(f"\nsize identity: cannot stat {local_path}: {e}")
        else:
            sv = latest.get("size_bytes")
            verdict = "MATCH" if sv == n else "MISMATCH"
            print(f"\nsize identity : local={n} drive={sv} -> {verdict}")
            if verdict == "MISMATCH":
                print("  The live version is NOT your local build. Re-run the version push,")
                print("  or confirm you are comparing against the right build directory.")

    # --- shell route: what shape is it answering in? -----------------------
    print("\nshell route   : /a/<id>")
    st, body, hdrs = get(f"{base}/a/{art}", token, follow=False)
    print(f"  status      : {st}")
    loc = hdrs.get("Location") or hdrs.get("location")
    if loc:
        print(f"  Location    : {loc[:120]}{'...' if len(loc) > 120 else ''}")
    else:
        # 200 shell: pull the iframe src out of the body
        import re

        txt = body.decode("utf-8", "replace")
        srcs = re.findall(r'<iframe[^>]*\ssrc="([^"]+)"', txt)
        print(f"  body bytes  : {len(body)}")
        print(f"  iframe srcs : {srcs[:2] or 'NONE FOUND'}")
        print(f"  CSP         : {hdrs.get('Content-Security-Policy', '-')[:110]}")

    if loc and loc.startswith("http"):
        st2, b2, _ = get(loc, token, follow=True)
        print(f"  capability URL fetched: HTTP {st2}, {len(b2)} bytes")
        if st2 in (403, 401):
            print("    (403 here is EXPECTED -- needs browser cookies. Use the browser tool")
            print("     or the API metadata above; do not retry with more headers.)")

    print(f"\nrender check  : open {base}/a/{art}/v/{cur} in the browser and assert")
    print("                brokenImgs == 0 and the new set's rows/panels are present.")


if __name__ == "__main__":
    main()
