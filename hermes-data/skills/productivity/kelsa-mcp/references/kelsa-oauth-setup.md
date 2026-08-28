# Kelsa MCP OAuth Setup — Headless Environment Walkthrough

**Date:** 26 Jun 2026
**Context:** Kelsa removed static MCP token support; only OAuth with localhost redirect works.

## Step-by-Step Transcript

### 1. Start the OAuth process

Run in background + PTY (foreground "non-interactive environment" error):

```python
# From execute_code or terminal:
terminal(
    command="/opt/hermes/.venv/bin/hermes mcp add Kelsa-Read --url \"https://kelsa.io/mcp\" --auth oauth",
    background=True,
    pty=True,
    timeout=600,
    notify_on_complete=True
)
```

The process output will show:

```
Starting OAuth flow for 'Kelsa-Read'...
✓ OAuth configured (tokens will be acquired on first connection)

Connecting to 'Kelsa-Read'...

MCP OAuth: authorization required.
Open this URL in your browser:

  https://kelsa.io/oauth/authorize?response_type=code&client_id=...&redirect_uri=http%3A%2F%2F127.0.0.1%3A<PORT>%2Fcallback&state=<STATE>&...

(Headless environment detected — open the URL manually.)

Or paste the redirect URL here (or the ?code=...&state=... portion) and press Enter. Type skip + Enter to continue without this server:
```

### 2. User authorizes

Send the user the OAuth URL from the output. They open it in their browser, log into Kelsa, and authorize Hermes. Browser redirects to:

```
http://127.0.0.1:<PORT>/callback?code=<CODE>&state=<STATE>
```

This page will NOT load on the user's machine — expected since it's the Hermes server's localhost. The user copies the full URL from their browser address bar and pastes it into the chat.

### 3. ⚠️ Answer "Save config anyway?" BEFORE Accepting the Paste

~40s after starting, the connection attempt to Kelsa times out. The process shows:

```
✗ Failed to connect: MCP call timed out after 40.0s
Save config anyway (you can test later)? [y/N]:
```

**Do NOT submit the user's paste URL yet.** First, answer "y" to save the config:

```python
process(action='submit', session_id='<SESSION_ID>', data='y')
```

After answering "y", the paste prompt re-appears within 1-2s.

### 4. Complete the flow

Now submit the user's redirect URL (or just the `?code=...&state=...` part) to the waiting background process:

```python
process(action='submit', session_id='<SESSION_ID>', data='<USER_PASTED_URL>')
```

The process should respond with:

```
Got authorization code from paste — completing flow.
```

Followed by confirmation. The server is now authenticated and configured.

### 5. Verify

```bash
hermes mcp test Kelsa-Read
```

### Common Failure Mode — Paste URL Lands on "Save Config Anyway?" Prompt

**This is the #1 failure mode in headless Kelsa OAuth.** The most common outcome is NOT a clean auth — it's the race condition documented below. Read and understand this BEFORE starting the flow.

### How the failure happens

The `hermes mcp add` process has this sequence:

```
1. Show OAuth URL + paste prompt (immediate)
2. Start 40s connection attempt to Kelsa (immediate, runs in background)
3. ~40s later → "✗ Failed to connect: MCP call timed out after 40.0s"
4. "Save config anyway (you can test later)? [y/N]:" prompt appears
```

The **paste prompt** appears at step 1, but by step 4 it's been replaced by "Save config anyway?". The user, who was still opening the URL and authorizing, finally pastes their redirect URL — but it lands on the "Save config anyway?" prompt instead.

The CLI **recognizes the paste text as a redirect URL** (not a y/n answer) and transitions to "Got authorization code from paste — completing flow." But the config was never saved (because the answer wasn't "y"). The state machine is now in the wrong branch: it has the auth code, but the config wasn't persisted. The process **hangs forever** and never produces a token file.

### Symptom signature

```
✗ Failed to connect: MCP call timed out after 43.0s (configured timeout: 40.0s)
Save config anyway (you can test later)? [y/N]: http://127.0.0.1:36851/callback?code=amFuUCPgEBPGIJiVwslVN-gyBq1DCr0A5DHfz4ABifc&state=DCZI2derd_x5SA78uRbPwHsRVQkPFOaP2uTUDjwZSyI
Got authorization code from paste — completing flow.
```

Then the process hangs at "completing flow" for minutes. `hermes mcp test Kelsa-Read` shows auth was never established.

### Correct sequence (agent-side)

1. **Start the process** — `hermes mcp add Kelsa-Read --url "https://kelsa.io/mcp" --auth oauth` in background PTY
2. **Answer "y" to overwrite** if server already exists
3. **Send the OAuth URL** to the user
4. **⏰ ~25s after showing the URL, start polling** for the "Save config anyway?" prompt
5. **AS SOON AS you see "Save config anyway (you can test later)? [y/N]:"** — answer "y" via `process(action='submit', data='y')`. Do this BEFORE submitting the user's paste URL.
6. **Wait briefly for the paste prompt to re-appear** (it may take 1-2s)
7. **Now submit the user's redirect URL** via `process(action='submit', data='<URL>')`
8. **Poll for completion** — expect "✓ OAuth configured" or "✓ Connection successful"

**Critical:** The "Save config anyway" prompt fires ~40s from START, not from when you show the URL. If the user takes longer than 40s to authorize, you've already lost the race. Monitor for it proactively — don't wait for the user's paste first.

### Recovery: process died before paste could be submitted

If the background process exits (exit code 137/killed by outer timeout) before the user pastes back:

```bash
# Non-interactive server removal (cleaner than keeping stale state)
echo "y" | hermes mcp remove Kelsa-Read

# Then start a FRESH add — old auth code is one-time-use, cannot be reused
terminal(
    command="hermes mcp add Kelsa-Read --url 'https://kelsa.io/mcp' --auth oauth",
    background=True, pty=True
)
```

The user will need a **new** OAuth URL from the fresh process.

### Recovery: process hangs at "completing flow" (paste landed on wrong prompt)

1. Kill the process: `process(action='kill', session_id='<ID>')`
2. Check whether auth actually succeeded: `hermes mcp test Kelsa-Read`
3. If auth is valid, the exchange completed despite the hang. Restart the gateway to pick it up.
4. If auth is not valid, the auth code was consumed but token exchange failed. Clean up and restart:
   ```bash
   echo "y" | hermes mcp remove Kelsa-Read
   ```
   Then start a fresh `hermes mcp add` — the user needs to authorize again with a new URL.

## Pitfalls

- **Diagnose auth state first** — Before running the OAuth flow, run `hermes mcp test Kelsa-Read` to see which failure mode you're in (invalid credentials → re-auth needed; permission errors → re-auth rewrites ownership; no credentials → OAuth never completed). Do NOT inspect the MCP credential store on disk. All three run the same fix below.

- **40s timeout on initial connect is NORMAL** — the process tries to connect to Kelsa before auth is complete. It will fail with "✗ Failed to connect: MCP call timed out after 40.0s" and show "Save config anyway? [y/N]:". This is where most agents make a mistake (see failure mode above). Answer "y" immediately, then wait for the paste prompt to re-appear before submitting the user's redirect URL.
- **Do NOT kill the process** — the first attempt worked (got auth code) but was killed prematurely. Keep the process alive until the user provides the redirect URL.
- **Each attempt generates a new OAuth URL** with a unique `state` parameter and port. The user must authorize against the URL from the SAME process that will receive their paste. If you kill and restart, you need a fresh URL. **Cannot reuse an auth code from a prior flow.**
- **After auth succeeds, user must start a new conversation** — MCP tools only load at conversation startup. Even with valid tokens, the current session won't retroactively gain Kelsa tools.
- **Difference from the old approach:** Previously, Kelsa supported generating a static token from Settings → API & Integrations → Generate MCP Token, and `hermes mcp add --auth header` would accept it. This method returns 401 as of late June 2026.
- **OAuth does NOT need HTTPS** — Kelsa accepts `http://127.0.0.1:<port>/callback`. No SSH tunnel or public URL needed.
- **Gateway restart is NOT a fix** — `hermes gateway restart` reconnects MCP connections but does not refresh expired OAuth tokens.

### If Config Was Saved Without Auth (old method artifact)

```bash
hermes mcp remove Kelsa-Read
# Then re-run the OAuth flow from step 1
```
