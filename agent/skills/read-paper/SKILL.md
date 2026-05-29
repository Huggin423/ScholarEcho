# Skill: Read Paper

## Purpose

Convert one paper into a structured, traceable paper card that can resurface during future research tasks.

## Inputs

- Paper PDF or extracted text.
- Zotero metadata when available.
- Existing project context from `05_projects/`.
- Related notes from `01_papers/`, `02_concepts/`, and `03_methods/`.

## Output

A Markdown paper card under `01_papers/` using `_template.md`.

## Workflow

1. Identify the active project or question first.
2. Retrieve existing notes using title terms, method names, concepts, author names, and project retrieval seeds.
3. Read available metadata.
4. Identify title, authors, year, venue, DOI, arXiv id, and Zotero key if available.
5. Read abstract, introduction, method, experiments, limitations, and conclusion.
6. Fill the paper card sections:
   - Activation
   - TL;DR
   - Research Problem
   - Core Claims
   - Method
   - Evidence
   - Limits
   - Connections
   - Useful For My Research
   - New Questions
   - Follow-up Papers
7. Add `trigger_terms`, `related_questions`, `supports`, `challenges`, and `use_when` frontmatter when useful.
8. Link the paper to at least one concept, method, question, or project when possible.
9. Mark uncertain claims with `confidence` and `needs_review`.
10. Create or update a trace under `agent/traces/`.

## Rules

- Do not invent citations or metadata.
- If full text is unavailable, clearly mark the note as based on metadata or abstract only.
- Prefer short, reusable bullets over long summaries.
- Separate direct claims from inferred implications.
- If the paper is not relevant to the active project, say why.
- Do not create a new concept or method card if an existing one can be updated.
- The most important output is not the summary; it is how this paper changes or supports an active question.

## Quality Checklist

- The paper card has stable identifiers when available.
- The TL;DR is short enough to skim.
- Claims are connected to evidence.
- Limits are explicit.
- At least one connection is recorded.
- Open questions are actionable.
- The note includes cues that will help future retrieval.
