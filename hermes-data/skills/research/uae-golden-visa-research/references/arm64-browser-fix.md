# Camofox Browser — ARM64 Container Workaround

## Problem

Camofox browser binary (`camoufox-bin`) is x86_64 only. On `aarch64` containers:
- Binary launches but exits immediately
- Error: `libgtk-3.so.0: cannot open shared object file` (despite the library existing in `/usr/lib/aarch64-linux-gnu/`)
- The actual error is arch mismatch — binary needs x86_64 GTK3 libs, but container only has ARM64 libs

## Symptoms

```json
{"error": "browserType.launch: Failed to launch the browser process.\n...
[pid=34794][err] XPCOMGlueLoad error for file /root/.cache/camoufox/libmozgtk.so:
[pid=34794][err] libgtk-3.so.0: cannot open shared object: No such file or directory
[pid=34794] <process did exit: exitCode=255, signal=null>"}
```

## Confirmed

- `libgtk-3-0t64` is already installed (version 3.24.49-3) but wrong arch for the binary
- `dpkg --print-architecture` → `arm64`
- Browser will not run in this environment until a ARM64-compatible Firefox build is available

## Workarounds Attempted

1. `apt-get install libgtk-3-0` — already satisfied, doesn't help (arch mismatch)
2. `apt-get install chromium` — not available on ARM64 from default repos
3. `playwright install chromium` — playwright not installed
4. `npm start` from `@askjo/camofox-browser` — server starts, browser binary fails

## What Would Work

- ARM64 build of Firefox/Camoufox (not currently available in package)
- Alternative: use a hosted browser-use-cloud service (not available in this env)
- Alternative: use `search_files` toolset (limited, did not find contacts)

## Current Status

- Camofox server health check passes: `GET /health` → `{"ok":true,"engine":"camoufox",...}`
- Tab creation fails: `POST /tabs` → browser binary error
- `browser_navigate` tool in Hermes uses camofox → won't work until ARM64 Firefox is available
