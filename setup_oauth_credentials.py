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

def init_submodules():
    """Ensure git submodules are initialized and updated."""
    print("\n" + "="*80)
    print("INITIALIZING GIT SUBMODULES")
    print("="*80)
    
    try:
        import subprocess
        # Check if we are in a git repo
        if not os.path.exists(".git"):
            print("⚠ Warning: Not in a git repository. Skipping submodule update.")
            return True
            
        print("→ Updating submodules (recursive)...")
        result = subprocess.run(
            ["git", "submodule", "update", "--init", "--recursive"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✓ Submodules initialized successfully")
            return True
        else:
            print(f"⚠ Warning: Submodule update returned code {result.returncode}")
            print(f"  Error: {result.stderr}")
            # Don't fail the whole setup, maybe some files are there
            return True 
    except Exception as e:
        print(f"✗ Error during submodule initialization: {e}")
        return True

def setup_credentials():
    """Read OAuth tokens from environment and create credential files."""
    # First, init submodules to ensure file paths exist
    init_submodules()

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

def symlink_gws_skills():
    """Symlink official GWS skills from vendor into Hermes skills folder."""
    print("\n" + "="*80)
    print("SYMLINKING GOOGLE WORKSPACE CLI SKILLS")
    print("="*80)

    # Current working directory (root of Core_Platform_Code)
    root = os.getcwd()
    vendor_skills = os.path.join(root, "vendor", "googleworkspace-cli", "skills")
    hermes_skills = os.path.join(root, "skills")

    if not os.path.exists(vendor_skills):
        print(f"\n✗ Error: vendor skills not found at {vendor_skills}")
        print("  Run: git submodule update --init --recursive")
        return False

    # Get all gws-* folders from vendor
    gws_folders = [f for f in os.listdir(vendor_skills) if f.startswith("gws-")]

    if not gws_folders:
        print(f"\n⚠ Warning: No gws-* folders found in {vendor_skills}")
        return False

    print(f"\n✓ Found {len(gws_folders)} GWS skill(s) in vendor")

    for folder in gws_folders:
        src = os.path.join(vendor_skills, folder)
        dst = os.path.join(hermes_skills, folder)

        # Create symlink (remove existing if it's already there)
        if os.path.lexists(dst):
            try:
                if os.path.islink(dst) or os.path.isfile(dst):
                    os.remove(dst)
                elif os.path.isdir(dst):
                    import shutil
                    shutil.rmtree(dst)
            except Exception as e:
                print(f"  ✗ Could not remove existing skill {dst}: {e}")
                continue

        try:
            # On windows, symlinking needs special privileges unless using junctions
            # On Linux (Railway), standard symlink works fine.
            if sys.platform == "win32":
                # For Windows testing/dev
                import subprocess
                subprocess.call(['mklink', '/J', dst, src], shell=True)
            else:
                os.symlink(src, dst)
            print(f"  ✓ Linked {folder}")
        except Exception as e:
            print(f"  ✗ Error linking {folder}: {e}")

    print("\n✓ Official GWS skills are now integrated!")
    print("="*80 + "\n")
    return True

if __name__ == "__main__":
    # Setup OAuth credentials first
    oauth_success = setup_credentials()

    # Symlink official GWS skills
    skills_success = symlink_gws_skills()

    # Then setup model configuration
    model_success = setup_model_config()

    # Exit with success only if both succeed (or model config is optional in future)
    # For now, OAuth is required, model config is nice-to-have
    sys.exit(0 if oauth_success else 1)
