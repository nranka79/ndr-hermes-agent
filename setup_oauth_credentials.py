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

    # Write .env file so gws CLI can locate credentials without per-invocation setup
    env_path = os.path.join(hermes_home, ".env")
    env_lines = [
        "# Auto-generated at startup from Railway environment variables.",
        "# Source: setup_oauth_credentials.py — do not edit manually.",
        "",
    ]
    account_env_keys = {
        "ndr@draas.com":          "GOOGLE_WORKSPACE_CLI_DRAAS_CREDENTIALS",
        "nishantranka@gmail.com": "GOOGLE_WORKSPACE_CLI_GMAIL_CREDENTIALS",
        "ndr@ahfl.in":            "GOOGLE_WORKSPACE_CLI_AHFL_CREDENTIALS",
    }
    for account in created_accounts:
        file_path = ACCOUNTS[account]["file_path"]
        env_key = account_env_keys[account]
        env_lines.append(f"{env_key}={file_path}")

    # Default GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE points to primary account
    primary = "ndr@draas.com"
    if primary in created_accounts:
        env_lines.append(f"GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE={ACCOUNTS[primary]['file_path']}")
    elif created_accounts:
        env_lines.append(f"GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE={ACCOUNTS[created_accounts[0]]['file_path']}")

    try:
        import tempfile
        fd, tmp = tempfile.mkstemp(dir=hermes_home, prefix=".env_", suffix=".tmp")
        with os.fdopen(fd, "w") as f:
            f.write("\n".join(env_lines) + "\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, env_path)
        os.chmod(env_path, 0o600)
        print(f"\n✓ Wrote {env_path} ({len(created_accounts)} account(s))")
    except Exception as e:
        print(f"\n⚠ Warning: could not write {env_path}: {e}")

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

def cleanup_stale_skills():
    """Remove skills that were deleted from the bundled skills/ but may linger in ~/.hermes/skills/."""
    print("\n" + "="*80)
    print("CLEANING UP STALE SKILLS")
    print("="*80)

    home = os.path.expanduser("~")
    hermes_skills = os.path.join(home, ".hermes", "skills")

    # Skills that have been removed from the bundled set and must not persist
    REMOVED_SKILLS = [
        os.path.join(hermes_skills, "productivity", "google-workspace"),
    ]

    import shutil
    for path in REMOVED_SKILLS:
        if os.path.exists(path):
            try:
                shutil.rmtree(path)
                print(f"  ✓ Removed stale skill: {path}")
            except Exception as e:
                print(f"  ⚠ Could not remove {path}: {e}")
        else:
            print(f"  ✓ Already clean: {path}")

    print("="*80 + "\n")


if __name__ == "__main__":
    # Setup OAuth credentials first
    oauth_success = setup_credentials()

    # Clean up skills that were removed from the bundled set
    cleanup_stale_skills()

    # Symlink official GWS skills
    skills_success = symlink_gws_skills()

    # Then setup model configuration
    model_success = setup_model_config()

    # Only fail hard if the PRIMARY account (ndr@draas.com) is missing.
    # Secondary accounts (ahfl.in, gmail) are optional — missing them is a warning,
    # not a reason to keep the bot from starting.
    primary_cred = ACCOUNTS["ndr@draas.com"]["file_path"]
    primary_ok = os.path.exists(primary_cred)
    if not primary_ok:
        print("\n✗ FATAL: Primary account credentials (ndr@draas.com) not created.")
        print("  Set DRAAS_OAUTH_REFRESH_TOKEN, DRAAS_OAUTH_CLIENT_ID, DRAAS_OAUTH_CLIENT_SECRET in Railway.")
        sys.exit(1)

    sys.exit(0)
