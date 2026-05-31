---
timestamp: 2026-05-31 16:42
task: "Add Zotero MCP connection"
status: completed
---

# Trace

## Context Retrieved

- Ran `make session q="连接 Zotero 的 MCP"`.
- No matching notes were found, so this was treated as a new tool integration rather than an update to an existing note.

## Changes

- Added `scripts/zotero_mcp.py`, a dependency-free stdio MCP server for Zotero metadata, collections, attachments, and ScholarEcho paper-card seeds.
- Added Make targets for running and checking the Zotero MCP server.
- Expanded `.env.example` with Zotero library and local storage settings.
- Updated `agent/tools/README.md` with setup instructions, client configuration, and path-resolution caveats.
- Added automatic `.env` loading inside the server while keeping explicit MCP client environment variables authoritative.
- Made initialization echo the client MCP protocol version when provided.

## Uncertainty

- Local PDF paths depend on the user's Zotero data directory and attachment mode. The MCP server returns `path_exists` so missing or inferred paths remain visible.
- The server is read-only for Zotero and does not write paper cards directly; it returns a seed command for human or agent review.
