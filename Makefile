.PHONY: search session check week new-paper

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
