# Tools and MCP Notes

This directory describes future local tools and MCP servers. The first version does not require implementing all of them.

Potential MCP servers:

- `vault-mcp`: read and write Markdown knowledge objects.
- `zotero-mcp`: read Zotero metadata, tags, collections, and PDF paths.
- `search-mcp`: full-text search, vector search, and metadata search.
- `paper-parser-mcp`: parse PDF text, sections, figures, and references.
- `citation-mcp`: resolve DOI, arXiv, BibTeX, and citation graph metadata.
- `notion-import-mcp`: import legacy Notion notes into structured Markdown.

Suggested local policy:

- Broad local read access is acceptable for personal use.
- Writes should be limited to the vault unless explicitly approved.
- Deletions should require human review.
- Generated indexes should stay under `index/`.

