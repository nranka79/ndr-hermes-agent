# Kelsa-Read MCP — Ad-Hoc Access via mcporter

**⚠️ DEPRECATED — Kelsa no longer supports static MCP tokens (updated 26 Jun 2026).**
Only OAuth with localhost redirect is accepted. See `kelsa-mcp` skill → OAuth Authentication section and `references/kelsa-oauth-setup.md` for the current setup process.

The old approach of `https://kelsa.io/mcp?token=<token>` returns 401. Do not attempt static token auth.

For ad-hoc access from terminal after OAuth is configured, use the Hermes CLI's configured MCP tools (they become available as native tools after `hermes mcp add Kelsa-Read --auth oauth` completes successfully).
