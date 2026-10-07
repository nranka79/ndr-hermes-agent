---
name: tailortalk-mcp
description: TailorTalk MCP integration — per-user OAuth login (tailortalk_login) and ephemeral, vault-token-backed calls to https://api.tailortalk.ai/mcp via tailortalk_list_tools / tailortalk_call_tool. Same workflow and guard rails as the Kelsa MCP integration.
version: 1.0.0
author: Hermes Agent
license: MIT
---

# TailorTalk MCP

TailorTalk is reached ONLY through three native tools, exactly like Kelsa:

| Tool | Purpose |
|---|---|
| `tailortalk_login` | Sends the user an "Authorize TailorTalk" button/link through the current channel. One-time per user. |
| `tailortalk_list_tools` | Lists the tools the TailorTalk MCP server exposes for the logged-in user (name, description, input schema). |
| `tailortalk_call_tool` | Calls one TailorTalk tool with `tool_name` + `arguments`. |

## Workflow

1. User asks for anything TailorTalk-related ("what can TailorTalk do", "send this to TailorTalk", ...).
2. Call `tailortalk_list_tools`.
   - Error `Not authorized with TailorTalk yet` → call `tailortalk_login` once, tell the user to tap the button and look for **Authorization successful!** in the browser, then stop and wait.
   - After the user confirms, call `tailortalk_list_tools` again — the HTTPS callback has already stored the token in the vault.
3. Pick the exact tool name from the listing and call `tailortalk_call_tool`. Never guess tool names.

## Hard rules (same as Kelsa)

- NEVER build, paste or transcribe a TailorTalk OAuth URL yourself. `tailortalk_login` delivers it and returns only a status.
- NEVER use `send_oauth_url` for TailorTalk — it is Google-only and will send a mislabeled Google link.
- NEVER ask the user for an authorization code or a pasted URL. The callback at `https://transcribe.ahfl.in/tailortalk/auth/callback` completes the exchange.
- NEVER read, copy or delete the vault token (`mcp-tailortalk`) via `terminal` / `execute_code`, and never import `tools.tailortalk_auth` from there — both are guarded and will refuse.
- Do NOT add TailorTalk under `hermes mcp add ... --auth oauth`; that legacy flow cannot complete in the headless gateway.

## Troubleshooting

| Symptom | Meaning | Action |
|---|---|---|
| `Not authorized with TailorTalk yet` | No vault token for this user | `tailortalk_login` |
| `tailortalk_login` → `Already authorized` but calls fail with `connection failed ... TaskGroup` | Token present but rejected (revoked/expired beyond refresh) | The tool already retried once with a refreshed token. Ask the user to revoke Hermes in the TailorTalk dashboard, then `tailortalk_login` again. |
| `A TailorTalk authorization is already pending` | A button was sent in the last 5 minutes | Do not call `tailortalk_login` again; wait for the user. |
| Repeated failures | — | Ask the user to share the chat history with @ndr_ra. |

## Server facts (probed 2026-10-07)

- MCP endpoint `https://api.tailortalk.ai/mcp`; OAuth metadata at `/.well-known/oauth-authorization-server` and `/.well-known/oauth-protected-resource/mcp`.
- Dynamic client registration at `/register`; Hermes registers once as a public PKCE client (stored in the vault under `hermes-system/tailortalk-dcr`). Scope `mcp`.
- Consent page lives at `dashboard.tailortalk.ai/connect`.
