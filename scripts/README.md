# Scripts

Local helper scripts for maintaining the vault.

## Search the Vault

```bash
python3 scripts/search_vault.py "retrieval augmented generation"
```

The search is intentionally simple and explainable. It prioritizes frontmatter fields such as `aliases`, `trigger_terms`, `related_questions`, `supports`, `challenges`, and `use_when`.

## Create a Paper Card

```bash
python3 scripts/new_paper_card.py \
  --title "Example Paper Title" \
  --year 2025 \
  --first-author "Smith" \
  --venue "NeurIPS" \
  --zotero-key "SMITH2025"
```
