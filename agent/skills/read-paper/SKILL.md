# Skill: Read Paper

## Purpose

Convert one paper into a structured, traceable paper card.

## Inputs

- Paper PDF or extracted text.
- Zotero metadata when available.
- Existing project context from `05_projects/`.
- Related notes from `01_papers/`, `02_concepts/`, and `03_methods/`.

## Output

A Markdown paper card under `01_papers/` using `_template.md`.

## Workflow

1. Read available metadata first.
2. Identify title, authors, year, venue, DOI, arXiv id, and Zotero key if available.
3. Read abstract, introduction, method, experiments, limitations, and conclusion.
4. Fill the paper card sections:
   - TL;DR
   - Research Problem
   - Core Claims
   - Method
   - Evidence
   - Limitations
   - Connections
   - Useful For My Research
   - Questions
   - Follow-up Papers
5. Link the paper to at least one concept, method, question, or project when possible.
6. Mark uncertain claims with `confidence` and `needs_review`.
7. Create or update a trace under `agent/traces/`.

## Rules

- Do not invent citations or metadata.
- If full text is unavailable, clearly mark the note as based on metadata or abstract only.
- Prefer short, reusable bullets over long summaries.
- Separate direct claims from inferred implications.
- If the paper is not relevant to the active project, say why.

## Quality Checklist

- The paper card has stable identifiers when available.
- The TL;DR is short enough to skim.
- Claims are connected to evidence.
- Limitations are explicit.
- At least one connection is recorded.
- Open questions are actionable.

