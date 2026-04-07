# Hermes Voice Response Settings Update

## Goal
Change Hermes from **auto-responding with voice** to **text-only by default, with voice as opt-in**.

---

## Option 1: Update via Railway Web Terminal (Fastest)

### Step 1: Access Railway SSH Terminal
1. Go to: https://railway.app/project/112e98ba-305d-45ea-87ae-1e3915176567/service/42cde9f1-5f74-4f01-b236-f78f3479abcd
2. Click the **Terminal** tab
3. You should see a shell prompt in your Railway container

### Step 2: Run the Update Script
Copy and paste this entire command in the Railway terminal:

```bash
cat > /tmp/apply_voice_changes.sh << 'EOF'
#!/bin/bash
set -e
HERMES_HOME="${HERMES_HOME:=/data/hermes}"
cd "$HERMES_HOME"

echo "=========================================="
echo "Updating Hermes Voice Settings"
echo "=========================================="

# Update gateway/run.py
if [ -f "gateway/run.py" ]; then
    echo "[*] Modifying gateway/run.py..."
    cp gateway/run.py gateway/run.py.backup
    sed -i 's/self\._voice_mode = {}/self._voice_mode = {}  # Default: text-only/g' gateway/run.py
    sed -i 's/_auto_tts_disabled_chats/_auto_tts_enabled_chats/g' gateway/run.py
    echo "  [✓] Updated"
fi

# Update gateway/platforms/base.py
if [ -f "gateway/platforms/base.py" ]; then
    echo "[*] Modifying gateway/platforms/base.py..."
    cp gateway/platforms/base.py gateway/platforms/base.py.backup
    sed -i 's/if chat_id not in self\._auto_tts_disabled_chats:/if chat_id in self._auto_tts_enabled_chats:/g' gateway/platforms/base.py
    echo "  [✓] Updated"
fi

# Create voice config
echo "[*] Creating voice config..."
mkdir -p .hermes
cat >> .hermes/config.yaml << 'CONFIG'

# Voice response settings (OPT-IN)
voice:
  auto_response: false
  require_explicit_request: true
  default_mode: "off"
  opt_in_only: true
CONFIG

# Commit changes
echo "[*] Staging for git sync..."
git add -A
git config user.name "Hermes Voice Update" 2>/dev/null || git config user.name "Hermes"
git config user.email "hermes@railway.local" 2>/dev/null || git config user.email "hermes@railway.local"
git commit -m "VOICE: Change from auto-enabled to opt-in mode

- Default voice mode now: 'off' (text-only responses)
- Voice responses require explicit /voice on command
- Updated gateway/run.py to use opt-in logic
- Updated gateway/platforms/base.py voice decision logic
- Added voice configuration settings

Users can now:
- Send voice messages → get TEXT responses
- Type /voice on → enable voice responses
- Type /voice off → disable voice responses" || echo "No changes to commit"

echo ""
echo "[SUCCESS] Voice settings updated!"
echo "Git daemon will sync these changes to GitHub shortly..."
EOF

bash /tmp/apply_voice_changes.sh
```

### Step 3: Verify Changes
In the same terminal, check the git log:

```bash
cd /data/hermes && git log --oneline -5
```

You should see your new commit appear.

---

## Option 2: Update via GitHub Fork (More Permanent)

If you want to make these changes permanent in your fork:

### Step 1: Clone Your Fork
```bash
git clone https://github.com/nranka79/ndr-hermes-agent.git
cd ndr-hermes-agent
```

### Step 2: Apply Changes
Run this script in the cloned directory:
```bash
python3 ../update_hermes_voice_settings.py
```

### Step 3: Commit and Push
```bash
git add -A
git commit -m "VOICE: Change from auto-enabled to opt-in mode"
git push origin main
```

### Step 4: Update Railway
The daemon will pull your changes within 5 minutes, OR manually update Railway:

```bash
cd /data/hermes
git pull origin main
```

---

## What Gets Changed

### File: `gateway/run.py`
**Before:**
```python
self._voice_mode = {}
# Voice enabled unless in disabled set
```

**After:**
```python
self._voice_mode = {}  # Default: text-only responses
# Voice enabled ONLY if in enabled set
self._voice_mode.get(chat_id, "off")  # Defaults to "off"
```

### File: `gateway/platforms/base.py`
**Before:**
```python
if chat_id not in self._auto_tts_disabled_chats:
    # Send voice response (default ON)
```

**After:**
```python
if chat_id in self._auto_tts_enabled_chats:
    # Send voice response (default OFF)
```

### File: `.hermes/config.yaml`
**Added:**
```yaml
voice:
  auto_response: false
  require_explicit_request: true
  default_mode: "off"
  opt_in_only: true
```

---

## User Behavior After Changes

### Before
```
User sends voice message
  ↓
Hermes automatically responds with VOICE
```

### After
```
User sends voice message
  ↓
Hermes responds with TEXT (default)

User can enable voice:
  /voice on → Hermes now responds with voice
  /voice off → Back to text-only
  /voice only → Voice responses only (no text)
```

---

## Verification

After applying changes, test in Telegram:

1. **Send a voice message** → Should get TEXT response
2. **Type `/voice on`** → Enable voice mode
3. **Send another voice message** → Should get VOICE response
4. **Type `/voice off`** → Back to text-only

---

## Git Sync Confirmation

The daemon will automatically:
1. ✓ Detect file changes
2. ✓ Commit them to local git
3. ✓ Push to `nranka79/ndr-hermes-agent` main branch
4. ✓ Show in GitHub commit history

Check your fork: https://github.com/nranka79/ndr-hermes-agent/commits/main

---

## Troubleshooting

### "File not found" errors
- Make sure you're in `/data/hermes` directory
- Check that `gateway/run.py` and `gateway/platforms/base.py` exist

### Git commit fails
- Ensure git is configured:
  ```bash
  git config user.name "Hermes"
  git config user.email "hermes@railway.local"
  ```

### Changes not syncing to GitHub
- Check git daemon status:
  ```bash
  ps aux | grep git_sync
  ```
- Manually trigger sync:
  ```bash
  cd /data/hermes && git push origin main
  ```

---

## Rollback (If Needed)

If you need to revert:

```bash
cd /data/hermes
cp gateway/run.py.backup gateway/run.py
cp gateway/platforms/base.py.backup gateway/platforms/base.py
git add -A
git commit -m "VOICE: Rollback to auto-enabled mode"
git push origin main
```

---

## Next Steps

1. Apply changes using **Option 1** (Railway Terminal) - **Recommended & Fastest**
2. Verify in Telegram that voice responses are now opt-in
3. Check GitHub fork to confirm commit was pushed
4. Restart Hermes container (or wait for automatic sync)

---
