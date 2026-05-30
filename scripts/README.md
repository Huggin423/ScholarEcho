# Scripts

Local helper scripts for maintaining ScholarEcho.

## Start a Research Session

```bash
python3 scripts/research_session.py "How should I frame my proposal?"
```

Use this before reading, writing, or asking an AI to synthesize. It retrieves relevant notes and points out missing retrieval cues.

## Search the Vault

```bash
python3 scripts/search_vault.py "retrieval augmented generation"
```

The search is intentionally simple and explainable. It prioritizes frontmatter fields such as `aliases`, `trigger_terms`, `related_questions`, `supports`, `challenges`, and `use_when`.

## Check Retrieval Health

```bash
python3 scripts/check_vault.py
```

This reports notes that are likely to be hard to retrieve later because they lack trigger terms, related questions, or use conditions.

## Weekly Digest Candidate

```bash
python3 scripts/weekly_digest.py
```

This lists recently changed knowledge notes and gives prompts for a small weekly synthesis.

## Create a Paper Card

```bash
python3 scripts/new_paper_card.py \
  --title "Example Paper Title" \
  --year 2025 \
  --first-author "Smith" \
  --venue "NeurIPS" \
  --zotero-key "SMITH2025"
```
