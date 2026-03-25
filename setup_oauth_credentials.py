#!/usr/bin/env python3
"""
Setup script to create OAuth credential files from Railway environment variables.
This script runs at Hermes startup and creates the necessary credential files in /data/hermes/

It reads the OAuth tokens from Railway environment variables and writes them to JSON files
that Hermes can use to access multiple Google Workspace accounts.
"""

import os
import json
import sys

# Accounts and their environment variable mappings
ACCOUNTS = {
    "ndr@draas.com": {
        "refresh_token_env": "DRAAS_OAUTH_REFRESH_TOKEN",
        "client_id_env": "DRAAS_OAUTH_CLIENT_ID",
        "client_secret_env": "DRAAS_OAUTH_CLIENT_SECRET",
        "file_path": "/data/hermes/oauth-draas.json"
    },
    "nishantranka@gmail.com": {
        "refresh_token_env": "GMAIL_OAUTH_REFRESH_TOKEN",
        "client_id_env": "GMAIL_OAUTH_CLIENT_ID",
        "client_secret_env": "GMAIL_OAUTH_CLIENT_SECRET",
        "file_path": "/data/hermes/oauth-gmail.json"
    },
    "ndr@ahfl.in": {
        "refresh_token_env": "AHFL_OAUTH_REFRESH_TOKEN",
        "client_id_env": "AHFL_OAUTH_CLIENT_ID",
        "client_secret_env": "AHFL_OAUTH_CLIENT_SECRET",
        "file_path": "/data/hermes/oauth-ahfl.json"
    }
}

def setup_credentials():
    """Read OAuth tokens from environment and create credential files."""
    print("\n" + "="*80)
    print("HERMES OAUTH CREDENTIALS SETUP")
    print("="*80)

    # Ensure /data/hermes directory exists
    hermes_home = "/data/hermes"
    os.makedirs(hermes_home, exist_ok=True)
    print(f"\n✓ Ensured {hermes_home} directory exists")

    created_accounts = []
    missing_accounts = []

    for account, config in ACCOUNTS.items():
        print(f"\nProcessing {account}...")

        # Get tokens from environment
        refresh_token = os.environ.get(config["refresh_token_env"])
        client_id = os.environ.get(config["client_id_env"])
        client_secret = os.environ.get(config["client_secret_env"])

        # Check if all tokens are available
        if not all([refresh_token, client_id, client_secret]):
            missing = []
            if not refresh_token:
                missing.append(config["refresh_token_env"])
            if not client_id:
                missing.append(config["client_id_env"])
            if not client_secret:
                missing.append(config["client_secret_env"])

            print(f"  ✗ Missing environment variables: {', '.join(missing)}")
            missing_accounts.append(account)
            continue

        # Create OAuth credential object
        credentials = {
            "type": "authorized_user",
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "account_email": account
        }

        # Write to file
        file_path = config["file_path"]
        try:
            with open(file_path, "w") as f:
                json.dump(credentials, f, indent=2)

            # Set restrictive permissions (readable only by owner)
            os.chmod(file_path, 0o600)

            print(f"  ✓ Created {file_path}")
            created_accounts.append(account)
        except Exception as e:
            print(f"  ✗ Error creating {file_path}: {e}")
            missing_accounts.append(account)

    # Summary
    print("\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    print(f"\n✓ Successfully created credentials for {len(created_accounts)} account(s):")
    for account in created_accounts:
        print(f"  • {account}")

    if missing_accounts:
        print(f"\n✗ Failed to create credentials for {len(missing_accounts)} account(s):")
        for account in missing_accounts:
            print(f"  • {account}")
        print("\nMake sure the following environment variables are set in Railway:")
        for account, config in ACCOUNTS.items():
            if account in missing_accounts:
                print(f"\n  {account}:")
                print(f"    - {config['refresh_token_env']}")
                print(f"    - {config['client_id_env']}")
                print(f"    - {config['client_secret_env']}")
        return False

    print("\n✓ All OAuth credentials are ready!")
    print("="*80 + "\n")
    return True


def setup_model_config():
    """Write config.yaml to configure MiniMax as default model provider."""
    print("\n" + "="*80)
    print("HERMES MODEL CONFIGURATION SETUP")
    print("="*80)

    hermes_home = "/data/hermes"
    config_path = os.path.join(hermes_home, "config.yaml")

    # Check if Minimax API key is configured
    minimax_key = os.environ.get("MINIMAX_API_KEY")
    if not minimax_key:
        print("\n⚠ MINIMAX_API_KEY not set — skipping model config write")
        print("  Set MINIMAX_API_KEY in Railway Variables to use MiniMax as default model")
        print("="*80 + "\n")
        return False

    config = {
        "model": {
            "provider": "minimax",
            "default": "MiniMax-M2.7",
            "base_url": "https://api.minimax.io/v1"
        }
    }

    # Merge with existing config.yaml if present (preserve other settings)
    existing = {}
    if os.path.exists(config_path):
        try:
            import yaml
            with open(config_path) as f:
                existing = yaml.safe_load(f) or {}
            print(f"\n✓ Found existing {config_path} — merging configuration")
        except Exception as e:
            print(f"\n⚠ Warning: could not read existing {config_path}: {e}")
            print("  Will create new config file")

    # Update or set model section
    existing["model"] = config["model"]

    # Write config.yaml
    try:
        import yaml
        with open(config_path, "w") as f:
            yaml.dump(existing, f, default_flow_style=False, sort_keys=False)
        print(f"\n✓ Wrote {config_path}")
        print("  - provider: minimax")
        print("  - model: MiniMax-M2.7")
        print("  - base_url: https://api.minimax.io/v1")
        print("\n✓ MiniMax-M2.7 is now the default model!")
        print("="*80 + "\n")
        return True
    except Exception as e:
        print(f"\n✗ Error writing {config_path}: {e}")
        print("="*80 + "\n")
        return False

if __name__ == "__main__":
    # Setup OAuth credentials first
    oauth_success = setup_credentials()

    # Then setup model configuration
    model_success = setup_model_config()

    # Exit with success only if both succeed (or model config is optional in future)
    # For now, OAuth is required, model config is nice-to-have
    sys.exit(0 if oauth_success else 1)
