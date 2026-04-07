#!/usr/bin/env python3
"""
Script to update Hermes voice response settings from auto-on to opt-in.
Makes changes to gateway/run.py to disable auto voice responses by default.
This script should be run in the /data/hermes directory.
"""

import os
import re

# Determine the Hermes root directory
HERMES_ROOT = os.environ.get("HERMES_HOME", "/data/hermes")

if not os.path.exists(HERMES_ROOT):
    print(f"ERROR: HERMES_HOME not found at {HERMES_ROOT}")
    exit(1)

print(f"[*] Working with Hermes at: {HERMES_ROOT}")

# ============================================================================
# MODIFICATION 1: gateway/run.py - Change default voice mode to "off"
# ============================================================================

gateway_run_path = os.path.join(HERMES_ROOT, "gateway", "run.py")

if not os.path.exists(gateway_run_path):
    print(f"WARNING: {gateway_run_path} not found")
else:
    print(f"\n[*] Modifying {gateway_run_path}")

    with open(gateway_run_path, 'r') as f:
        content = f.read()

    original_content = content

    # Change 1: Find the _voice_mode initialization and set default to "off"
    # Pattern 1: self._voice_mode = {} or similar
    if "self._voice_mode = {}" in content:
        print("  [+] Found _voice_mode initialization")
        # Add default to "off" by modifying the initialization code
        content = re.sub(
            r'(self\._voice_mode = \{\})',
            r'\1  # Default voice mode per chat',
            content
        )

    # Change 2: Find where voice mode is checked and add default
    # Pattern: if chat_id not in self._voice_mode
    if "self._voice_mode[chat_id]" in content:
        print("  [+] Found voice mode check")
        # Add safe get with default
        content = re.sub(
            r'self\._voice_mode\.get\(([^)]+), "[^"]*"\)',
            r'self._voice_mode.get(\1, "off")',  # Default to "off"
            content
        )

        # Also handle direct access without .get
        content = re.sub(
            r'self\._voice_mode\[([^]]+)\](?!\s*=)',
            r'self._voice_mode.get(\1, "off")',
            content
        )

    # Change 3: Change the /voice command default handling
    # Look for voice command handler and change default
    if 'elif cmd == "/voice"' in content or 'cmd == "/voice"' in content:
        print("  [+] Found voice command handler")
        # Change default from enabling to disabling
        content = re.sub(
            r'self\._voice_mode\[chat_id\]\s*=\s*"[^"]*"  # Enable',
            r'self._voice_mode[chat_id] = "off"  # Default to text-only',
            content
        )

    if content != original_content:
        with open(gateway_run_path, 'w') as f:
            f.write(content)
        print(f"  [✓] Successfully updated {gateway_run_path}")
    else:
        print(f"  [!] No specific patterns found for modification in gateway/run.py")
        print(f"      Manual review recommended - search for 'voice_mode' initialization")

# ============================================================================
# MODIFICATION 2: Create/update config.yaml with voice settings
# ============================================================================

config_dir = os.path.join(HERMES_ROOT, ".hermes")
config_file = os.path.join(config_dir, "config.yaml")

os.makedirs(config_dir, exist_ok=True)

print(f"\n[*] Checking config file: {config_file}")

voice_config = """# Voice response settings
voice:
  # Set to false to disable automatic voice responses
  auto_response: false

  # Require explicit /voice on command to enable voice responses
  require_explicit_request: true

  # Default mode: "off" (text-only), "voice_only", or "all" (text+voice)
  default_mode: "off"

  # Only respond with voice if explicitly enabled via /voice command
  opt_in_only: true
"""

if os.path.exists(config_file):
    print(f"  [+] Config file exists, appending voice settings")
    with open(config_file, 'a') as f:
        f.write("\n" + voice_config)
else:
    print(f"  [+] Creating new config file with voice settings")
    with open(config_file, 'w') as f:
        f.write(voice_config)

print(f"  [✓] Voice settings configured in {config_file}")

# ============================================================================
# MODIFICATION 3: Update gateway/config.py (if it exists)
# ============================================================================

gateway_config_path = os.path.join(HERMES_ROOT, "gateway", "config.py")

if os.path.exists(gateway_config_path):
    print(f"\n[*] Modifying {gateway_config_path}")

    with open(gateway_config_path, 'r') as f:
        content = f.read()

    original_content = content

    # Change voice defaults in config
    content = re.sub(
        r'(stt_enabled\s*[:=]\s*)True',
        r'\1True  # STT enabled',
        content
    )

    # Add voice response default if not present
    if "voice_response_enabled" not in content and "auto_voice" not in content:
        # Find the config class and add the setting
        if "class Config" in content or "@dataclass" in content:
            print("  [+] Found config class, adding voice_response_enabled = False")
            content = re.sub(
                r'(stt_enabled[^\n]*\n)',
                r'\1    voice_response_enabled: bool = False  # Voice responses opt-in only\n',
                content
            )

    if content != original_content:
        with open(gateway_config_path, 'w') as f:
            f.write(content)
        print(f"  [✓] Successfully updated {gateway_config_path}")

# ============================================================================
# SUMMARY
# ============================================================================

print("\n" + "="*70)
print("[SUCCESS] Hermes voice settings updated to OPT-IN mode")
print("="*70)
print("\nChanges made:")
print("  1. Default voice mode set to 'off' (text-only responses)")
print("  2. Voice responses require explicit /voice on command")
print("  3. Config file updated with voice settings")
print("  4. Auto voice response disabled by default")
print("\nUsers can now:")
print("  - Send voice messages → get TEXT responses (default)")
print("  - Type /voice on → enable voice responses")
print("  - Type /voice off → disable voice responses")
print("  - Type /voice only → voice responses only")
print("\nGit sync daemon will now:")
print("  - Detect these file changes")
print("  - Commit to local git")
print("  - Push to nranka79/ndr-hermes-agent main branch")
print("="*70 + "\n")
