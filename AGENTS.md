# AGENTS.md

## Mission

This repository is a personal AI-ready research knowledge base for long-term graduate research.

The agent should help convert papers, notes, questions, project ideas, and writing drafts into structured, traceable, reusable research context.

The repository is provider-agnostic. Do not assume a specific model vendor. Follow the active model profile when one is provided.

## Core Principles

- Treat summaries as working memory, not final truth.
- Every important claim should be traceable to a paper, note, or explicit user statement.
- Prefer structured Markdown with YAML frontmatter over long unstructured prose.
- Preserve uncertainty with `confidence: low | medium | high`.
- Mark missing evidence with `needs_verification: true`.
- Do not invent citations, paper titles, author names, venues, DOI values, or arXiv ids.
- Do not overwrite human notes in a way that loses original meaning.
- Link each paper to at least one concept, method, question, project, or synthesis note when possible.
- Keep updates small, auditable, and easy for the user to review.

## Repository Map

- `00_inbox/`: raw imports from Zotero, Notion, web exports, and temporary sources.
- `01_papers/`: structured paper cards.
- `02_concepts/`: reusable concept cards.
- `03_methods/`: method, model, dataset, and experiment design cards.
- `04_questions/`: open research questions and hypothesis backlog.
- `05_projects/`: active research projects and context packs.
- `06_synthesis/`: weekly reviews, topic reviews, and cross-paper synthesis.
- `07_outputs/`: proposals, papers, slides, reports, and other deliverables.
- `agent/profiles/`: provider-specific model profiles.
- `agent/prompts/`: reusable prompt fragments.
- `agent/skills/`: reusable workflows.
- `agent/tools/`: tool and MCP integration notes.
- `agent/traces/`: logs of non-trivial agent runs.
- `agent/evals/`: checks for output quality and model consistency.
- `index/`: metadata, search indexes, embeddings, and graph files.
- `scripts/`: local maintenance scripts.

## Default Agent Loop

Use this loop for non-trivial work:

1. Observe: read relevant files, metadata, and user instructions.
2. Retrieve: find related papers, concepts, methods, questions, and project context.
3. Plan: briefly state the intended update when the change is substantial.
4. Act: create or update structured notes.
5. Verify: mark uncertain claims, missing sources, and citation gaps.
6. Write Memory: update links, tags, status fields, and trace logs.

## Writing Rules

Use Markdown with YAML frontmatter for durable knowledge files.

Prefer these sections for paper cards:

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

Prefer concise bullets over long essays. Do not hide uncertainty in polished prose.

## Citation Rules

When citing a paper, use at least one stable identifier:

- Zotero key
- DOI
- arXiv id
- BibTeX key
- local paper id

If a source is not available, write `source_missing: true`.

Never invent references. If a relationship between papers is inferred rather than directly stated, mark it as an inference.

## Trace Rules

For each non-trivial agent run, create or append a trace under `agent/traces/`.

A trace should include:

- timestamp
- model and provider if known
- active profile if known
- task
- files read
- files changed
- tools used
- uncertain claims
- next actions

## Provider-Agnostic Behavior

Skills and prompts must not hard-code a provider such as OpenAI, DeepSeek, Claude, or local models.

Use the active profile to adapt behavior:

- If context is limited, process documents in chunks.
- If tool calling is weak, ask for explicit file paths and produce machine-readable update plans.
- If JSON reliability is weak, prefer Markdown templates with strict headings.
- If citation reliability is weak, require source snippets before writing strong claims.
- If cost is high, summarize incrementally and cache intermediate notes.

## Safety for Personal Local Use

This is a personal local research repository. File access can be broad, but edits should still be conservative:

- Never delete source notes or PDFs.
- Never remove human-written content unless the user explicitly asks.
- Prefer adding `needs_review` notes over silently rewriting ambiguous content.
- Keep generated indexes and caches under `index/`.
- Do not commit secrets, API keys, private tokens, or raw credentials.

