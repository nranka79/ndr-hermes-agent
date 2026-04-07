#!/usr/bin/env python3
"""
Test script to verify OAuth credential files work with Google APIs.
Tests each of the 3 accounts.
"""

import json
import sys
import os

# Set encoding for Windows
os.environ['PYTHONIOENCODING'] = 'utf-8'

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar.readonly",
]

ACCOUNTS = {
    "ndr@draas.com": "oauth-draas.json",
    "nishantranka@gmail.com": "oauth-gmail.json",
    "ndr@ahfl.in": "oauth-ahfl.json"
}

def test_account(account_email, cred_file):
    """Test if an account's credentials work."""
    print(f"\n{'='*80}")
    print(f"Testing: {account_email}")
    print(f"File: {cred_file}")
    print('='*80)

    try:
        # Read credential file
        with open(cred_file, "r") as f:
            cred_data = json.load(f)
        print("[OK] Credential file loaded")

        # Create credentials object
        credentials = Credentials(
            token=None,
            refresh_token=cred_data.get("refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=cred_data.get("client_id"),
            client_secret=cred_data.get("client_secret"),
            scopes=SCOPES
        )
        print("[OK] Credentials object created")

        # Refresh to get valid access token
        print("  Refreshing access token...")
        credentials.refresh(Request())
        print("[OK] Access token refreshed successfully")

        # Test Drive API
        print("  Testing Drive API...")
        drive_service = build("drive", "v3", credentials=credentials)
        results = drive_service.files().list(pageSize=1, fields="files(id, name)").execute()
        files = results.get("files", [])
        print(f"[OK] Drive API works! (Found {len(files)} file(s))")

        # Test Gmail API
        print("  Testing Gmail API...")
        gmail_service = build("gmail", "v1", credentials=credentials)
        results = gmail_service.users().messages().list(userId="me", maxResults=1).execute()
        messages = results.get("messages", [])
        print(f"[OK] Gmail API works! (Found {len(messages)} message(s))")

        # Test Calendar API
        print("  Testing Calendar API...")
        calendar_service = build("calendar", "v3", credentials=credentials)
        results = calendar_service.calendarList().list(maxResults=1).execute()
        calendars = results.get("items", [])
        print(f"[OK] Calendar API works! (Found {len(calendars)} calendar(s))")

        print(f"\n[PASS] {account_email} - ALL TESTS PASSED!")
        return True

    except FileNotFoundError as e:
        print(f"[ERROR] File not found: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"[ERROR] Invalid JSON: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("\n" + "="*80)
    print("OAUTH CREDENTIAL TEST SUITE")
    print("="*80)

    results = {}
    for account_email, cred_file in ACCOUNTS.items():
        results[account_email] = test_account(account_email, cred_file)

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for account, passed_test in results.items():
        status = "[PASS]" if passed_test else "[FAIL]"
        print(f"{status} - {account}")

    print(f"\nTotal: {passed}/{total} accounts passed")
    print("="*80 + "\n")

    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
