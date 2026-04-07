#!/usr/bin/env python3
"""
Generate OAuth refresh token for ndr@ahfl.in
Uses port 8081 instead of 8080 to avoid conflicts
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
    print("GENERATING OAUTH REFRESH TOKEN FOR ndr@ahfl.in")
    print("="*80)
    print("\nThis script will open your browser for OAuth authorization.\n")

    try:
        flow = InstalledAppFlow.from_client_secrets_file(
            'ahfl_oauth_creds.json',  # Use ahfl_oauth_creds.json
            scopes=SCOPES
        )

        # Try to run local server on port 8081 (different from 8080)
        print("Starting local authorization server on http://localhost:8081/\n")
        print("If browser doesn't open automatically:")
        print("  1. Check if browser opened in background")
        print("  2. Manually visit: http://localhost:8081/\n")

        creds = flow.run_local_server(
            port=8081,  # Use different port
            open_browser=True
        )

        print("\n" + "="*80)
        print("SUCCESS! Token Generated")
        print("="*80)
        print("\nCopy these values to Railway Variables:\n")

        print("1. AHFL_OAUTH_REFRESH_TOKEN:")
        print("-" * 80)
        print(creds.refresh_token)
        print("-" * 80)
        print()

        print("2. AHFL_OAUTH_CLIENT_ID:")
        print("-" * 80)
        print(creds.client_id)
        print("-" * 80)
        print()

        print("3. AHFL_OAUTH_CLIENT_SECRET:")
        print("-" * 80)
        print(creds.client_secret)
        print("-" * 80)
        print()

        print("="*80)
        print("\nNEXT STEPS:")
        print("1. Copy the 3 tokens above")
        print("2. Go to: https://railway.app -> Hermes Service -> Variables")
        print("3. Add these 3 variables with AHFL_ prefix")
        print("4. Redeploy Railway")
        print("5. Test the multi-account access")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\nError: {e}\n")
        print("TROUBLESHOOTING:")
        print("1. Make sure ahfl_oauth_creds.json is in current directory")
        print("2. Make sure port 8081 is available")
        print("3. If port 8081 in use, try 8888 or another port")
        print("4. Try closing other OAuth-related processes\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
