#!/usr/bin/env python3
"""
Generate OAuth refresh token for nishantranka@gmail.com
Run this directly in your terminal (Git Bash) - not through Claude
"""

from google_auth_oauthlib.flow import InstalledAppFlow
import json
import webbrowser
import sys

SCOPES = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/calendar.readonly',
    'https://www.googleapis.com/auth/contacts.readonly',
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/documents',
    'https://www.googleapis.com/auth/tasks'
]

def main():
    print("\n" + "="*80)
    print("GENERATING OAUTH REFRESH TOKEN FOR nishantranka@gmail.com")
    print("="*80)
    print("\nThis script will open your browser for OAuth authorization.\n")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'oauth_creds.json',
            scopes=SCOPES
        )

        # Try to run local server (will work on most systems)
        print("Starting local authorization server on http://localhost:8080/\n")
        print("If browser doesn't open automatically:")
        print("  1. Check if browser opened in background")
        print("  2. Manually visit: http://localhost:8080/\n")

        creds = flow.run_local_server(
            port=8080,
            open_browser=True
        )

        print("\n" + "="*80)
        print("SUCCESS! Token Generated")
        print("="*80)
        print("\nCopy these values to Railway Variables:\n")

        print("1. GMAIL_OAUTH_REFRESH_TOKEN:")
        print("-" * 80)
        print(creds.refresh_token)
        print("-" * 80)
        print()

        print("2. GMAIL_OAUTH_CLIENT_ID:")
        print("-" * 80)
        print(creds.client_id)
        print("-" * 80)
        print()

        print("3. GMAIL_OAUTH_CLIENT_SECRET:")
        print("-" * 80)
        print(creds.client_secret)
        print("-" * 80)
        print()

        print("="*80)
        print("\nNEXT STEPS:")
        print("1. Copy the 3 tokens above")
        print("2. Go to: https://railway.app → Hermes Service → Variables")
        print("3. Add these 3 variables")
        print("4. Continue with Step 2: Create service account for ndr@ahfl.in")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        print("TROUBLESHOOTING:")
        print("1. Make sure oauth_creds.json is in current directory")
        print("2. Make sure port 8080 is available (not in use)")
        print("3. Try closing other OAuth-related processes")
        print("4. Try a different port by editing this script\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
