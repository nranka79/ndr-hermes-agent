# MCP SDK Connection Verification — Kelsa-Read

Reference for verifying the Kelsa-Read MCP server is reachable and authenticated from Python when the `mcp_kelsa_read_*` tools are not surfaced in the current conversation.

## Tool Check

```bash
# Check if MCP server is connected
/opt/hermes/.venv/bin/hermes mcp list

# Expected output:
# Kelsa-Read       https://kelsa.io/mcp           all          ✓ enabled
```

If the server shows ✓ enabled but tools aren't in-conversation, see "Server Enabled But Tools Not Surfaced in Conversation" in the main skill.

## Direct MCP SDK Connection Test

This test verifies the connection by creating a fresh `streamable_http_client` + `ClientSession` from Python:

```python
import asyncio, httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def test():
    async with httpx.AsyncClient(follow_redirects=True) as http_client:
        async with streamable_http_client(
            'https://kelsa.io/mcp', http_client=http_client
        ) as (read_stream, write_stream, get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                init_result = await session.initialize()
                print("Server:", init_result.serverInfo)
                tools = await session.list_tools()
                print("Tools:", [t.name for t in tools.tools])

asyncio.run(test())
```

**If this works**, the MCP server is reachable — and if tools still aren't in-conversation, the issue is the session vs. gateway init timing.

**If this returns 401**, try with the OAuth provider:

```python
import asyncio, httpx, sys
sys.path.insert(0, '/opt/hermes')
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from tools.mcp_oauth_manager import get_manager

async def test():
    manager = get_manager()
    auth = manager.get_or_build_provider(
        'Kelsa-Read', 'https://kelsa.io/mcp', None
    )
    async with httpx.AsyncClient(follow_redirects=True, auth=auth) as http_client:
        async with streamable_http_client(
            'https://kelsa.io/mcp', http_client=http_client
        ) as (read_stream, write_stream, get_session_id):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                tools = await session.list_tools()
                print("Tools:", [t.name for t in tools.tools])

asyncio.run(test())
```

## Known Permission Block

If the OAuth provider shows:

```
Failed to read /data/hermes/mcp-tokens/Kelsa-Read.json: [Errno 13] Permission denied
```

Then the stored credentials are unreadable by the `hermes` user (UID 10000).

**Resolution**: Re-run the OAuth flow via `hermes mcp add Kelsa-Read --url "https://kelsa.io/mcp" --auth oauth` in a background PTY terminal (see main skill), which rewrites the credentials with hermes ownership. Do NOT attempt to read or chmod credential files directly.

## Gateway Process Memory (Cannot Use)

The running gateway (PID 130) has the OAuth token in process memory but:
- `/proc/130/mem` is unreadable (YAMA ptrace_scope = 1)
- No API endpoint on the gateway exposes MCP tools directly
- The token cannot be extracted from a separate Python process
