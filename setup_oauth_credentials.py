#!/usr/bin/env python3
"""
Setup script to create OAuth credential files from Railway environment variables.
This script runs at Hermes startup and creates the necessary credential files in /data/hermes/

It reads the OAuth tokens from Railway environment variables and writes them to JSON files
that Hermes can use to access multiple Google Workspace accounts.
"""

import os
import json
import shutil
import sys


def _find_gws_binary() -> list:
    """
    Return the argv prefix to invoke gws (e.g. ['/app/node_modules/.bin/gws']).
    Falls back to npx if the binary isn't found at known locations.
    The script runs from the app root, so node_modules/.bin/gws is relative to cwd.
    """
    candidates = [
        os.path.join(os.getcwd(), "node_modules", ".bin", "gws"),
        "/app/node_modules/.bin/gws",
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return [c]
    on_path = shutil.which("gws")
    if on_path:
        return [on_path]
    # Last resort: npx (slower, may download)
    npx = shutil.which("npx") or "npx"
    return [npx, "--yes", "@googleworkspace/cli"]

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
    """Write config.yaml to configure OpenRouter gemini-2.5-flash-lite as default model."""
    print("\n" + "="*80)
    print("HERMES MODEL CONFIGURATION SETUP")
    print("="*80)

    hermes_home = "/data/hermes"
    config_path = os.path.join(hermes_home, "config.yaml")

    # Check if OpenRouter API key is configured
    openrouter_key = os.environ.get("OPENROUTER_API_KEY")
    if not openrouter_key:
        print("\n⚠ OPENROUTER_API_KEY not set — skipping model config write")
        print("  Set OPENROUTER_API_KEY in Railway Variables to use OpenRouter as default provider")
        print("="*80 + "\n")
        return False

    config = {
        "model": {
            "provider": "openrouter",
            "default": "google/gemini-2.5-flash-lite",
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
        print("  - provider: openrouter")
        print("  - model: google/gemini-2.5-flash-lite")
        print("\n✓ google/gemini-2.5-flash-lite (via OpenRouter) is now the default model!")
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
    """Remove skills that were deleted from the bundled skills/ but may linger in seeded paths."""
    print("\n" + "="*80)
    print("CLEANING UP STALE SKILLS")
    print("="*80)

    import shutil

    home = os.path.expanduser("~")

    # All possible roots where skills may have been seeded
    skill_roots = [
        os.path.join(home, ".hermes", "skills"),
        "/app/skills",                             # Railway container app dir
        os.path.join(os.getcwd(), "skills"),       # Local dev / working dir
    ]

    # Skill directory names (relative to any skill root) that must not persist.
    # These were removed from the bundled skills/ and contain stale instructions
    # that reference deleted scripts and wrong tool names.
    REMOVED_SKILL_RELPATHS = [
        os.path.join("productivity", "google-workspace"),
        "google-workspace",   # flat fallback path
    ]

    found_any = False
    for root in skill_roots:
        for relpath in REMOVED_SKILL_RELPATHS:
            path = os.path.join(root, relpath)
            if os.path.exists(path):
                found_any = True
                try:
                    shutil.rmtree(path)
                    print(f"  ✓ Removed stale skill: {path}")
                except Exception as e:
                    print(f"  ⚠ Could not remove {path}: {e}")

    if not found_any:
        print("  ✓ No stale skills found")

    print("="*80 + "\n")


def setup_registry_sheet():
    """Create the entity registry tabs (projects, land_proposals, entities) in the contacts sheet."""
    print("\n" + "="*80)
    print("SETTING UP ENTITY REGISTRY SHEET TABS")
    print("="*80)

    SHEET_ID = "1XbSRAXxPLY4cXMTm2rmvKh11Nx3x0aKUxxuWualoV9g"
    CRED_FILE = ACCOUNTS["ndr@draas.com"]["file_path"]

    if not os.path.exists(CRED_FILE):
        print(f"\n⚠ Skipping sheet setup — draas.com credentials not found at {CRED_FILE}")
        print("="*80 + "\n")
        return False

    import subprocess

    env = os.environ.copy()
    env["GOOGLE_WORKSPACE_CLI_CREDENTIALS_FILE"] = CRED_FILE

    # Step 1: get existing sheet names
    try:
        result = subprocess.run(
            _find_gws_binary() + ["sheets", "spreadsheets", "get",
             "--spreadsheetId", SHEET_ID],
            capture_output=True, text=True, env=env, timeout=30
        )
        existing_titles = set()
        if result.returncode == 0:
            import json as _json
            data = _json.loads(result.stdout)
            for sheet in data.get("sheets", []):
                title = sheet.get("properties", {}).get("title", "")
                if title:
                    existing_titles.add(title)
            print(f"\n  Existing tabs: {sorted(existing_titles)}")
        else:
            print(f"\n  ⚠ Could not read sheet metadata: {result.stderr[:200]}")
            print("="*80 + "\n")
            return False
    except Exception as e:
        print(f"\n  ⚠ Sheet metadata error: {e}")
        print("="*80 + "\n")
        return False

    # Step 2: define tabs to create
    TABS = {
        "projects": [
            "canonical_name", "aliases", "voice_misspellings",
            "associated_contacts", "associated_entities",
            "associated_land_proposals", "status", "notes"
        ],
        "land_proposals": [
            "canonical_name", "aliases", "voice_misspellings",
            "location", "entity", "associated_contacts",
            "associated_projects", "status", "notes"
        ],
        "entities": [
            "canonical_name", "aliases", "voice_misspellings",
            "type", "associated_contacts", "associated_projects", "notes"
        ],
    }

    import json as _json
    all_ok = True
    for tab_name, headers in TABS.items():
        if tab_name in existing_titles:
            print(f"  ✓ Tab already exists: {tab_name}")
            continue

        # Create the tab
        body = _json.dumps({"requests": [{"addSheet": {"properties": {"title": tab_name}}}]})
        try:
            r = subprocess.run(
                _find_gws_binary() + ["sheets", "spreadsheets", "batchUpdate",
                 "--spreadsheetId", SHEET_ID, "--body", body],
                capture_output=True, text=True, env=env, timeout=30
            )
            if r.returncode != 0:
                print(f"  ✗ Could not create tab '{tab_name}': {r.stderr[:200]}")
                all_ok = False
                continue
            print(f"  ✓ Created tab: {tab_name}")
        except Exception as e:
            print(f"  ✗ Error creating tab '{tab_name}': {e}")
            all_ok = False
            continue

        # Write headers to row 1
        hdr_range = f"{tab_name}!A1:{chr(ord('A') + len(headers) - 1)}1"
        hdr_body = _json.dumps({"values": [headers]})
        try:
            r = subprocess.run(
                _find_gws_binary() + ["sheets", "values", "update",
                 "--spreadsheetId", SHEET_ID,
                 "--range", hdr_range,
                 "--valueInputOption", "RAW",
                 "--body", hdr_body],
                capture_output=True, text=True, env=env, timeout=30
            )
            if r.returncode != 0:
                print(f"  ✗ Could not write headers to '{tab_name}': {r.stderr[:200]}")
                all_ok = False
            else:
                print(f"  ✓ Headers written to: {tab_name}")
        except Exception as e:
            print(f"  ✗ Error writing headers for '{tab_name}': {e}")
            all_ok = False

    if all_ok:
        print("\n✓ Entity registry sheet is ready!")
    print("="*80 + "\n")
    return all_ok


if __name__ == "__main__":
    # Log gws binary resolution so it's visible in Railway deploy logs
    gws_cmd = _find_gws_binary()
    print(f"\n✓ GWS binary resolved to: {' '.join(gws_cmd)}")

    # Setup OAuth credentials first
    oauth_success = setup_credentials()

    # Clean up skills that were removed from the bundled set
    cleanup_stale_skills()

    # Symlink official GWS skills
    skills_success = symlink_gws_skills()

    # Create entity registry tabs in contacts sheet (idempotent — skips existing tabs)
    setup_registry_sheet()

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
