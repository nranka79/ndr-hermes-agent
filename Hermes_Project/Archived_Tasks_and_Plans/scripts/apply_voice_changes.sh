#!/bin/bash
# Script to apply voice response opt-in changes to Hermes in Railway
# Run this in the Railway container: bash /data/hermes/apply_voice_changes.sh

set -e

HERMES_HOME="${HERMES_HOME:=/data/hermes}"
cd "$HERMES_HOME"

echo "=========================================="
echo "Updating Hermes Voice Settings"
echo "=========================================="
echo "Working directory: $(pwd)"
echo ""

# ============================================================================
# 1. Update gateway/run.py - Set default voice mode to "off"
# ============================================================================

if [ -f "gateway/run.py" ]; then
    echo "[*] Modifying gateway/run.py..."

    # Backup original
    cp gateway/run.py gateway/run.py.backup

    # Change 1: Update voice mode defaults
    # Find the line where voice modes are initialized and ensure default is "off"
    sed -i.tmp 's/self\._voice_mode = {}/self._voice_mode = {}  # Default: text-only responses/g' gateway/run.py

    # Change 2: Find voice mode checks and ensure they default to "off"
    # This pattern handles: self._voice_mode.get(chat_id, "something")
    sed -i.tmp 's/self\._voice_mode\.get(\([^,]*\), "[^"]*")/self._voice_mode.get(\1, "off")/g' gateway/run.py

    # Change 3: Update _auto_tts_disabled_chats to _auto_tts_enabled_chats
    # (Voice is disabled by default, must be explicitly enabled)
    if grep -q "_auto_tts_disabled_chats" gateway/run.py; then
        sed -i.tmp 's/_auto_tts_disabled_chats/_auto_tts_enabled_chats/g' gateway/run.py
        echo "  [+] Changed auto-TTS logic: now opt-in instead of opt-out"
    fi

    # Cleanup temp backup
    rm -f gateway/run.py.tmp

    echo "  [✓] gateway/run.py updated"
else
    echo "  [!] gateway/run.py not found - skipping"
fi

# ============================================================================
# 2. Update gateway/platforms/base.py - Change auto-TTS logic
# ============================================================================

if [ -f "gateway/platforms/base.py" ]; then
    echo "[*] Modifying gateway/platforms/base.py..."

    # Backup original
    cp gateway/platforms/base.py gateway/platforms/base.py.backup

    # Change the auto-TTS decision logic:
    # From: "TTS enabled unless in disabled set"
    # To: "TTS enabled only if in enabled set"
    sed -i.tmp 's/if chat_id not in self\._auto_tts_disabled_chats:/if chat_id in self._auto_tts_enabled_chats:/g' gateway/platforms/base.py

    # Cleanup
    rm -f gateway/platforms/base.py.tmp

    echo "  [✓] gateway/platforms/base.py updated"
else
    echo "  [!] gateway/platforms/base.py not found - skipping"
fi

# ============================================================================
# 3. Create/update config with voice settings
# ============================================================================

echo "[*] Creating/updating voice configuration..."

mkdir -p .hermes

cat >> .hermes/config.yaml << 'EOF'

# Voice response settings (OPT-IN mode)
voice:
  # Disable automatic voice responses by default
  auto_response: false

  # Require explicit user request to enable voice
  require_explicit_request: true

  # Default mode: "off" (text-only), "voice_only" (voice-only), or "all" (text+voice)
  default_mode: "off"

  # Users must explicitly enable with: /voice on
  opt_in_only: true
EOF

echo "  [✓] Voice configuration created in .hermes/config.yaml"

# ============================================================================
# 4. Git commit the changes
# ============================================================================

echo "[*] Staging changes for git sync..."

git add -A
git status

echo ""
echo "=========================================="
echo "[SUCCESS] Voice settings updated!"
echo "=========================================="
echo ""
echo "Changes:"
echo "  - Default voice mode: OFF (text-only)"
echo "  - Voice requires explicit /voice on command"
echo "  - Auto voice responses disabled"
echo ""
echo "User commands:"
echo "  /voice on     → Enable voice responses"
echo "  /voice off    → Disable voice responses"
echo "  /voice only   → Voice-only responses"
echo ""
echo "Git sync daemon will:"
echo "  - Detect these file changes"
echo "  - Commit them to local git"
echo "  - Push to GitHub (nranka79/ndr-hermes-agent)"
echo ""
echo "=========================================="
