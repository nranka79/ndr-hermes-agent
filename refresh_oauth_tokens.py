#!/usr/bin/env python3
"""
Refresh OAuth tokens for Hermes Google Workspace accounts.

Run this locally whenever Railway reports 'invalid_grant'.
It opens a browser for each account, captures the auth code via a local
callback server, and prints the new refresh token to paste into Railway.

Usage:
    python refresh_oauth_tokens.py                  # refresh all 3 accounts
    python refresh_oauth_tokens.py draas            # refresh ndr@draas.com only
    python refresh_oauth_tokens.py gmail            # refresh nishantranka@gmail.com only
    python refresh_oauth_tokens.py ahfl             # refresh ndr@ahfl.in only

Prerequisites (already in pyproject.toml after latest deploy):
    pip install google-auth-oauthlib google-api-python-client

Railway env vars needed (already set):
    DRAAS_OAUTH_CLIENT_ID, DRAAS_OAUTH_CLIENT_SECRET
    GMAIL_OAUTH_CLIENT_ID,  GMAIL_OAUTH_CLIENT_SECRET
    AHFL_OAUTH_CLIENT_ID,   AHFL_OAUTH_CLIENT_SECRET
"""

import http.server
import json
import os
import sys
import threading
import urllib.parse
import webbrowser
from pathlib import Path

# ── Scopes ────────────────────────────────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/contacts",
    "https://www.googleapis.com/auth/tasks",
    "openid",
    "email",
    "profile",
]

REDIRECT_URI = "http://localhost:8765"

# ── Account definitions ────────────────────────────────────────────────────────
ACCOUNTS = {
    "draas": {
        "email":      "ndr@draas.com",
        "client_id_env":     "DRAAS_OAUTH_CLIENT_ID",
        "client_secret_env": "DRAAS_OAUTH_CLIENT_SECRET",
        "refresh_token_env": "DRAAS_OAUTH_REFRESH_TOKEN",
    },
    "gmail": {
        "email":      "nishantranka@gmail.com",
        "client_id_env":     "GMAIL_OAUTH_CLIENT_ID",
        "client_secret_env": "GMAIL_OAUTH_CLIENT_SECRET",
        "refresh_token_env": "GMAIL_OAUTH_REFRESH_TOKEN",
    },
    "ahfl": {
        "email":      "ndr@ahfl.in",
        "client_id_env":     "AHFL_OAUTH_CLIENT_ID",
        "client_secret_env": "AHFL_OAUTH_CLIENT_SECRET",
        "refresh_token_env": "AHFL_OAUTH_REFRESH_TOKEN",
    },
}


# ── One-shot local callback server ────────────────────────────────────────────

class _CallbackHandler(http.server.BaseHTTPRequestHandler):
    """Handles a single GET /  with ?code=... and stores the code."""
    def do_GET(self):
        params = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
        self.server.auth_code = params.get("code", [None])[0]
        self.server.auth_error = params.get("error", [None])[0]
        body = b"<html><body><h2>Authorization received. You can close this tab.</h2></body></html>"
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_):
        pass   # suppress request logs


def _wait_for_code(port: int = 8765, timeout: int = 120):
    """Start a local server, wait for the OAuth callback, return the code."""
    server = http.server.HTTPServer(("localhost", port), _CallbackHandler)
    server.auth_code = None
    server.auth_error = None
    server.timeout = timeout

    # Run in a thread so we can time out
    def _serve():
        server.handle_request()   # handles exactly one request

    t = threading.Thread(target=_serve, daemon=True)
    t.start()
    t.join(timeout=timeout + 2)

    if server.auth_error:
        raise RuntimeError(f"OAuth error from Google: {server.auth_error}")
    if not server.auth_code:
        raise TimeoutError("No auth code received within timeout. Did you complete the browser flow?")
    return server.auth_code


# ── Token exchange ─────────────────────────────────────────────────────────────

def _exchange_code(client_id: str, client_secret: str, code: str) -> dict:
    """Exchange auth code for tokens. Returns the full token dict."""
    import urllib.request

    data = urllib.parse.urlencode({
        "code":          code,
        "client_id":     client_id,
        "client_secret": client_secret,
        "redirect_uri":  REDIRECT_URI,
        "grant_type":    "authorization_code",
    }).encode()

    req = urllib.request.Request(
        "https://oauth2.googleapis.com/token",
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


# ── Auth URL builder ───────────────────────────────────────────────────────────

def _build_auth_url(client_id: str, login_hint: str) -> str:
    params = {
        "client_id":             client_id,
        "redirect_uri":          REDIRECT_URI,
        "response_type":         "code",
        "scope":                 " ".join(SCOPES),
        "access_type":           "offline",
        "prompt":                "consent",      # forces refresh_token to be returned
        "login_hint":            login_hint,
    }
    return "https://accounts.google.com/o/oauth2/v2/auth?" + urllib.parse.urlencode(params)


# ── Per-account flow ───────────────────────────────────────────────────────────

def refresh_account(key: str) -> dict:
    """Run the full OAuth flow for one account. Returns {'refresh_token': ...}."""
    cfg = ACCOUNTS[key]
    email = cfg["email"]

    client_id     = os.environ.get(cfg["client_id_env"])
    client_secret = os.environ.get(cfg["client_secret_env"])

    if not client_id or not client_secret:
        raise ValueError(
            f"Missing env vars for {email}:\n"
            f"  {cfg['client_id_env']} = {'SET' if client_id else 'MISSING'}\n"
            f"  {cfg['client_secret_env']} = {'SET' if client_secret else 'MISSING'}\n"
            "Set them in your local shell before running this script:\n"
            f"  export {cfg['client_id_env']}=...\n"
            f"  export {cfg['client_secret_env']}=..."
        )

    url = _build_auth_url(client_id, login_hint=email)

    print(f"\n{'='*70}")
    print(f"  Account: {email}")
    print(f"{'='*70}")
    print(f"\n  Opening browser for Google authorization...")
    print(f"\n  If the browser does not open, paste this URL manually:\n")
    print(f"  {url}\n")

    webbrowser.open(url)

    print("  Waiting for authorization (120s timeout)...")
    code = _wait_for_code()
    print("  ✓ Authorization code received.")

    tokens = _exchange_code(client_id, client_secret, code)

    refresh_token = tokens.get("refresh_token")
    if not refresh_token:
        raise RuntimeError(
            "No refresh_token in response. This usually means 'prompt=consent' was bypassed.\n"
            "Try revoking app access at https://myaccount.google.com/permissions and re-running."
        )

    print(f"\n  ✅ New refresh token obtained for {email}")
    print(f"\n  ┌─ Railway Variable ─────────────────────────────────────────────┐")
    print(f"  │  Name : {cfg['refresh_token_env']}")
    print(f"  │  Value: {refresh_token}")
    print(f"  └────────────────────────────────────────────────────────────────┘")
    print(f"\n  Copy the value above into Railway → Variables → {cfg['refresh_token_env']}")

    return {"email": email, "env_var": cfg["refresh_token_env"], "refresh_token": refresh_token}


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    args = sys.argv[1:]

    if args:
        keys = []
        for a in args:
            a = a.lower().strip()
            if a in ACCOUNTS:
                keys.append(a)
            else:
                # fuzzy: draas.com → draas, gmail.com → gmail, ahfl.in → ahfl
                for k in ACCOUNTS:
                    if k in a or a in ACCOUNTS[k]["email"]:
                        keys.append(k)
                        break
                else:
                    print(f"Unknown account '{a}'. Choose from: {', '.join(ACCOUNTS)}")
                    sys.exit(1)
    else:
        keys = list(ACCOUNTS)

    results = []
    for key in keys:
        try:
            r = refresh_account(key)
            results.append(r)
        except Exception as e:
            print(f"\n  ✗ Failed for {ACCOUNTS[key]['email']}: {e}")

    if results:
        print(f"\n\n{'='*70}")
        print("  SUMMARY — paste these into Railway → Variables → then Redeploy")
        print(f"{'='*70}\n")
        for r in results:
            print(f"  {r['env_var']}={r['refresh_token']}")
        print()


if __name__ == "__main__":
    main()
