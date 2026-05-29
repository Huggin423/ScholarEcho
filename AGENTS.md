# AGENTS.md

## Mission

This repository is a personal research context engine, not a passive paper archive.

The agent's job is to help the user activate, connect, question, and reuse research knowledge during real tasks: reading papers, forming questions, writing proposals, designing experiments, and preparing outputs.

The repository is provider-agnostic. Do not assume OpenAI, DeepSeek, Claude, or any specific model vendor. Follow the active model profile when one is provided.

## Design Philosophy

- Start from the user's current question or task.
- Retrieve existing context before generating new content.
- Keep durable knowledge small, structured, and easy to search.
- Treat papers as evidence for questions, not as the center of the system.
- Write activation cues so old notes can resurface later.
- Preserve uncertainty and citation gaps.
- Prefer improving existing notes over creating duplicate notes.

## Minimal Knowledge Objects

- `Paper`: what a paper claims, how it supports or challenges questions, and when it should be reused.
- `Concept`: a reusable idea with aliases, trigger terms, and related questions.
- `Method`: an approach with suitable use cases, assumptions, and limits.
- `Question`: the main organizing unit for research.
- `Project`: the current working context and retrieval seeds.
- `Synthesis`: a small integration note that changes the user's understanding.

Do not add new object types unless they clearly simplify the workflow.

## Default Agent Loop

Use this loop for non-trivial work:

1. Identify the current question, project, or output goal.
2. Retrieve relevant existing notes from `04_questions/`, `05_projects/`, `02_concepts/`, `03_methods/`, `01_papers/`, and `06_synthesis/`.
3. State only the necessary plan when edits are substantial.
4. Create or update the smallest useful knowledge object.
5. Link the update back to questions, concepts, methods, projects, or outputs.
6. Mark uncertainty, missing evidence, and inferred relationships.
7. Write a trace for meaningful AI-assisted changes.

## Retrieval Rules

Before creating a new note, check for existing context using:

- exact terms from the user request
- aliases and trigger terms
- related project keywords
- related question wording
- author names, paper ids, DOI, arXiv ids, and Zotero keys

When a note is useful for future retrieval, add or update:

- `trigger_terms`
- `aliases`
- `related_questions`
- `use_when`
- `supports`
- `challenges`

## Repository Map

- `00_inbox/`: raw imports from Zotero, Notion, web exports, and temporary sources.
- `01_papers/`: structured paper cards.
- `02_concepts/`: reusable concept cards.
- `03_methods/`: method, model, dataset, and experiment design cards.
- `04_questions/`: open research questions and hypothesis backlog.
- `05_projects/`: active research projects and retrieval seeds.
- `06_synthesis/`: weekly reviews, topic reviews, and cross-paper synthesis.
- `07_outputs/`: proposals, papers, slides, reports, and other deliverables.
- `agent/profiles/`: provider-specific model profiles.
- `agent/prompts/`: reusable prompt fragments.
- `agent/skills/`: reusable workflows.
- `agent/tools/`: tool and MCP integration notes.
- `agent/traces/`: logs of non-trivial agent runs.
- `index/`: generated search indexes, embeddings, and graph files.
- `scripts/`: local maintenance scripts.

## Writing Rules

Use Markdown with YAML frontmatter for durable knowledge files.

Prefer short, reusable bullets over long summaries. A good note answers:

- What is this?
- Which question does it help with?
- What evidence supports it?
- What does it challenge?
- When should it resurface?
- What remains uncertain?

## Citation Rules

When citing a paper, use at least one stable identifier:

- Zotero key
- DOI
- arXiv id
- BibTeX key
- local paper id

If a source is not available, write `source_missing: true`.

Never invent references. If a relationship between papers is inferred rather than directly stated, mark it as an inference.

## Provider-Agnostic Behavior

Skills and prompts must not hard-code a provider.

Use the active profile to adapt behavior:

- If context is limited, retrieve narrowly and process documents in chunks.
- If tool calling is weak, produce a clear update plan before edits.
- If JSON reliability is weak, prefer Markdown templates with strict headings.
- If citation reliability is weak, require source snippets before strong claims.
- If cost is high, summarize incrementally and cache only useful notes.

## Safety for Personal Local Use

File access can be broad, but edits should stay conservative:

- Never delete source notes or PDFs.
- Never remove human-written content unless the user explicitly asks.
- Prefer adding `needs_review` over silently resolving ambiguity.
- Keep generated indexes and caches under `index/`.
- Do not commit secrets, API keys, private tokens, or raw credentials.
