# Claude IDE Fix — Session Continuation

> **Load this file in a new Claude session inside Antigravity IDE, then say "continue the Claude IDE fix."** This is a handoff from a previous session that diagnosed and triaged the issue but stopped short of writing config (because the agent cannot safely kill its own IDE host).

## TL;DR

The **Claude Code extension (Anthropic) v2.1.197** inside Antigravity IDE is broken on this machine. The bundled `claude.exe` is a packaging mistake — it is just the **Bun runtime v1.4.0** with the Claude Code app payload missing. Update + reinstall does **not** fix it; the marketplace version itself has the bug.

**The fix:** point the extension at the working standalone npm `claude.cmd` via the `claudeCode.claudeProcessWrapper` setting, then reopen the IDE.

---

## What the previous session already did

1. **Diagnosed root cause** from the extension log:
   - File: `C:\Users\ruhaan\AppData\Roaming\Antigravity IDE\logs\<latest>\window1\exthost\Anthropic.claude-code\Claude VSCode.log`
   - Smoking gun (first error line): `From claude: error: Script not found "stream-json"` followed by `Error spawning Claude: Error: Claude Code process exited with code 1`.
   - Confirmed by running the bundled binary directly: `claude.exe --version` → `1.4.0`, `claude.exe --help` → Bun help text. The binary is 236 MB but contains no Claude app code.
2. **Tried Track A (update + reinstall extension in-IDE)** — did not help. The reinstalled extension folder is still v2.1.197, binary unchanged. The current marketplace version is itself broken.
3. **Decided on Track B (workaround)**: use `claudeCode.claudeProcessWrapper` to redirect the extension to the working npm CLI.
4. **Confirmed npm CLI works**: `C:\Users\ruhaan\AppData\Roaming\npm\claude.cmd --version` returns `2.1.197 (Claude Code)`, exit 0.
5. **Produced a cleanup script** the user ran from a separate PowerShell: `C:\Users\ruhaan\fix-claude-ide.bat`. It killed all `Antigravity IDE.exe` processes, removed the 76 stale lock files in `~/.claude/ide/`, and freed MCP port 39007.

**What is left for THIS session:** edit `settings.json` to add the wrapper setting, verify, and tell the user to reopen the IDE.

---

## Current system state (assumed after the .bat was run)

| Item | Value |
|---|---|
| Antigravity IDE process | **NOT running** (verify with `Get-Process -Name "Antigravity IDE" -ErrorAction SilentlyContinue` — should return nothing) |
| Broken extension folder (still installed, leave it) | `C:\Users\ruhaan\.antigravity-ide\extensions\anthropic.claude-code-2.1.197-win32-x64\` |
| Bundled (broken) binary | `C:\Users\ruhaan\.antigravity-ide\extensions\anthropic.claude-code-2.1.197-win32-x64\resources\native-binary\claude.exe` — 236 MB Bun 1.4.0, missing app payload |
| Working CLI to point the extension at | `C:\Users\ruhaan\AppData\Roaming\npm\claude.cmd` (v2.1.197) |
| Settings file to edit | `C:\Users\ruhaan\AppData\Roaming\Antigravity IDE\User\settings.json` |
| Lock files directory (already cleaned) | `C:\Users\ruhaan\.claude\ide\` |
| MCP port (already freed) | `localhost:39007` |

---

## Steps to complete the fix

### 1. Verify the IDE is actually closed

```powershell
Get-Process -Name "Antigravity IDE" -ErrorAction SilentlyContinue
```

If anything comes back, **stop and tell the user** they must fully quit the IDE before continuing. Touching `settings.json` or lock files while the IDE is running risks corrupting its config or being clobbered by it.

### 2. Back up the current settings.json

```powershell
$ts = Get-Date -Format "yyyyMMdd-HHmmss"
Copy-Item "$env:APPDATA\Antigravity IDE\User\settings.json" "$env:APPDATA\Antigravity IDE\User\settings.json.bak.$ts" -Verbose
```

### 3. Edit settings.json — add `claudeCode.claudeProcessWrapper`

Current full contents (use this as a reference for the merge — do **not** just overwrite):

```json
{
    "claudeCode.preferredLocation": "panel",
    "claudeCode.selectedModel": "haiku",
    "python.languageServer": "Default",
    "workbench.editor.enablePreview": false,
    "files.autoSave": "afterDelay",
    "securecoder.enabled": true
}
```

Use the safe-edit approach (preserves formatting and any keys added since):

```powershell
$settingsPath = "$env:APPDATA\Antigravity IDE\User\settings.json"
$settings = Get-Content $settingsPath -Raw | ConvertFrom-Json
$settings | Add-Member -NotePropertyName "claudeCode.claudeProcessWrapper" -NotePropertyValue "C:\Users\ruhaan\AppData\Roaming\npm\claude.cmd" -Force
$settings | ConvertTo-Json -Depth 10 | Set-Content $settingsPath -Encoding UTF8
```

**Note the backslashes** in the path — `ConvertTo-Json` will produce single backslashes in the JSON, which is what VS Code settings want. If you write the JSON by hand, use double-escaped backslashes (`"C:\\Users\\ruhaan\\AppData\\Roaming\\npm\\claude.cmd"`).

### 4. Verify the edit

```powershell
Get-Content "$env:APPDATA\Antigravity IDE\User\settings.json" -Raw
Get-Content "$env:APPDATA\Antigravity IDE\User\settings.json" -Raw | ConvertFrom-Json
```

The first should show the new `"claudeCode.claudeProcessWrapper"` key. The second should parse without error and show the new property on the resulting object.

### 5. Hand back to the user

Tell the user to **reopen Antigravity IDE manually** and try the Claude Code extension. The extension will now spawn `claude.cmd` instead of the broken bundled `claude.exe`.

---

## If it still doesn't work

Read the **new** extension log:

```
C:\Users\ruhaan\AppData\Roaming\Antigravity IDE\logs\<latest>\window1\exthost\Anthropic.claude-code\Claude VSCode.log
```

- If you see `Script not found "stream-json"` again → the wrapper path didn't take. Re-check `settings.json` (typos? wrong key? wrong escaping?).
- If you see `executable not found` / `cannot find wrapper` → verify `C:\Users\ruhaan\AppData\Roaming\npm\claude.cmd` exists and that the path in `settings.json` matches exactly.
- If you see a **different** error → read the head of the log and diagnose based on the new error text. Do not assume the diagnosis from the previous session still applies.
- If the npm `claude.cmd` itself starts misbehaving (auth, network, etc.), that's a separate issue — fall back to `claude doctor` for diagnostics.

---

## What NOT to do

- Do **not** try to fix the bundled `claude.exe` in the extension. It's a marketplace packaging bug, not something to patch locally.
- Do **not** add a new npm `claude` install — one already exists at the path above and works.
- Do **not** modify the extension's own `package.json` to point at a different binary — the `claudeCode.claudeProcessWrapper` setting is the supported override.
- Do **not** delete the broken extension folder. The settings workaround is enough; the bundled binary will just sit there unused. Deleting it may break extension update checks later.
- Do **not** start the IDE on the user's behalf. The user opens it manually after you finish the settings edit.
