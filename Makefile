.PHONY: search session check week new-paper scholar-mcp scholar-mcp-check zotero-mcp zotero-mcp-check

search:
	@python3 scripts/search_vault.py "$(q)"

session:
	@python3 scripts/research_session.py "$(q)"

check:
	@python3 scripts/check_vault.py

week:
	@python3 scripts/weekly_digest.py

new-paper:
	@python3 scripts/new_paper_card.py --title "$(title)" --year "$(year)" --first-author "$(author)" --venue "$(venue)" --zotero-key "$(zotero)"

scholar-mcp:
	@python3 scripts/scholarecho_mcp.py

scholar-mcp-check:
	@python3 scripts/scholarecho_mcp.py --check

zotero-mcp:
	@python3 scripts/zotero_mcp.py

zotero-mcp-check:
	@python3 scripts/zotero_mcp.py --check-config
