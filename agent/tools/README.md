# Tools and MCP Notes

This directory describes future local tools and MCP servers. The first version does not require implementing all of them.

Implemented MCP servers:

- `scholarecho-mcp`: local vault, search, parser, citation, and Notion import tools.
- `zotero-mcp`: read Zotero metadata, tags, collections, and PDF paths.

Potential MCP servers:

- `vault-mcp`: implemented inside `scholarecho-mcp`.
- `search-mcp`: implemented inside `scholarecho-mcp`.
- `paper-parser-mcp`: implemented inside `scholarecho-mcp`.
- `citation-mcp`: implemented inside `scholarecho-mcp`.
- `notion-import-mcp`: implemented inside `scholarecho-mcp`.

Suggested local policy:

- Broad local read access is acceptable for personal use.
- Writes should be limited to the vault unless explicitly approved.
- Deletions should require human review.
- Generated indexes should stay under `index/`.

## ScholarEcho Local MCP

`scripts/scholarecho_mcp.py` exposes the local, provider-agnostic MCP tools for the vault. It keeps the project loop intact: retrieve first, write small notes conservatively, and keep citation uncertainty visible.

### Local Check

```bash
make scholar-mcp-check
```

### MCP Client Configuration

```json
{
  "mcpServers": {
    "scholarecho-local": {
      "command": "python3",
      "args": ["/Users/maoxiaoyi1/Documents/ScholarEcho/scripts/scholarecho_mcp.py"]
    }
  }
}
```

### Tool Groups

- Vault tools: `vault_list_notes`, `vault_read_note`, `vault_create_note`, `vault_append_note`, `vault_update_frontmatter`.
- Search tools: `search_vault`, `search_session_brief`, `search_retrieval_health`.
- Paper parser tools: `paper_parse_pdf`, `paper_parse_text`.
- Citation tools: `citation_extract_ids`, `citation_resolve_doi`, `citation_resolve_arxiv`.
- Notion import tools: `notion_list_exports`, `notion_preview_import`, `notion_import_draft`.

### Safety Policy

- Vault writes are limited to Markdown files inside ScholarEcho knowledge, inbox, output, and agent trace folders.
- The server never deletes source files or PDFs.
- Notion imports land as drafts under `00_inbox/notion_imports/converted/`.
- PDF parsing may read absolute local paths so Zotero attachment paths can be inspected, but write tools remain repository-scoped.

## Zotero MCP

ScholarEcho includes a small stdio MCP server at `scripts/zotero_mcp.py`. It uses the Zotero Web API for metadata and resolves local attachment paths best-effort from Zotero attachment fields.

### Environment

Copy `.env.example` to `.env` for local use and fill in the Zotero fields:

```bash
ZOTERO_LIBRARY_TYPE=user
ZOTERO_USER_ID=123456
ZOTERO_API_KEY=...
ZOTERO_DATA_DIR=~/Zotero
ZOTERO_STORAGE_DIR=~/Zotero/storage
```

For a group library, set:

```bash
ZOTERO_LIBRARY_TYPE=group
ZOTERO_GROUP_ID=123456
```

The API key may be omitted for public libraries, but private libraries require it.

### Local Check

```bash
make zotero-mcp-check
```

This validates environment variables and prints the resolved library and storage path without calling the Zotero API.

### MCP Client Configuration

Use this command from the repository root:

```bash
python3 scripts/zotero_mcp.py
```

Example stdio MCP configuration:

```json
{
  "mcpServers": {
    "scholarecho-zotero": {
      "command": "python3",
      "args": ["/Users/maoxiaoyi1/Documents/ScholarEcho/scripts/zotero_mcp.py"],
      "env": {
        "ZOTERO_LIBRARY_TYPE": "user",
        "ZOTERO_USER_ID": "123456",
        "ZOTERO_API_KEY": "replace-with-local-secret",
        "ZOTERO_DATA_DIR": "/Users/maoxiaoyi1/Zotero",
        "ZOTERO_STORAGE_DIR": "/Users/maoxiaoyi1/Zotero/storage"
      }
    }
  }
}
```

Do not commit real API keys. Keep secrets in your local MCP client config or an untracked `.env` file.

When run from this repository, the server reads `.env` automatically. Explicit environment values from the MCP client take precedence.

### Tools

- `zotero_search_items`: search Zotero items by free text, item type, tag, and limit.
- `zotero_get_item`: fetch one item by Zotero key, including child attachments and notes.
- `zotero_get_collections`: list collections.
- `zotero_get_collection_items`: list recent items from a collection.
- `zotero_paper_card_seed`: produce ScholarEcho paper-card fields and a `scripts/new_paper_card.py` command without writing files.

### Attachment Path Notes

For imported Zotero PDFs, the server maps `storage:paper.pdf` to:

```text
${ZOTERO_STORAGE_DIR}/${ATTACHMENT_KEY}/paper.pdf
```

If a path cannot be resolved or the file is absent, the tool returns the best candidate path with `path_exists: false`. Treat these paths as retrieval hints, not proof that the PDF is available.
