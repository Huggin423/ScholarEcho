---
timestamp: 2026-05-31 16:47
task: "Complete remaining MCP tools and draw architecture"
status: completed
---

# Trace

## Context Retrieved

- Ran `make session q="补齐 ScholarEcho MCP 剩余功能 vault search paper parser citation notion import 架构图"`.
- Relevant context was project-level architecture and tool notes, not a durable research object.

## Changes

- Added `scripts/scholarecho_mcp.py` as the unified local MCP server for vault, search, paper parsing, citation lookup, and Notion import staging.
- Added Make targets `scholar-mcp` and `scholar-mcp-check`.
- Updated `agent/tools/README.md` with the new MCP server configuration, tool groups, and safety policy.
- Added a Mermaid architecture diagram to `docs/architecture.md`.
- Kept MCP write tools scoped to inbox, durable knowledge directories, and outputs.

## Uncertainty

- PDF parsing uses `pdftotext` when available and falls back to macOS `strings`; scanned PDFs still need OCR outside this first local MCP layer.
- Citation resolution uses public Crossref and arXiv endpoints. Returned metadata should still be checked before being promoted into paper cards.
- Notion import writes draft Markdown into inbox conversion space and does not automatically promote notes into durable knowledge objects.
