# Architecture

This vault separates durable knowledge from model execution.

```text
Sources -> Knowledge Objects -> Retrieval -> Agent Harness -> Outputs
```

## Layers

### Source Layer

Raw material stays close to the tool that owns it:

- Zotero: PDFs, bibliography, citation keys, reading status.
- Notion: legacy summaries and project notes.
- Local files: Markdown notes, scripts, indexes, traces.

### Knowledge Layer

The vault turns raw material into stable objects:

- Paper
- Concept
- Method
- Question
- Project
- Synthesis
- Output

Each object should be independently readable and linked to related objects.

### Retrieval Layer

Retrieval can evolve over time:

- Phase 1: filename, tag, and Markdown search.
- Phase 2: SQLite metadata index.
- Phase 3: vector index and concept graph.
- Phase 4: MCP server exposing search and write tools.

### Agent Harness

Agents are workflows, not just prompts.

The harness consists of:

- `AGENTS.md`: global operating rules.
- `agent/profiles/`: model/provider capability profiles.
- `agent/router.yaml`: task-to-model routing policy.
- `agent/skills/`: reusable research workflows.
- `agent/prompts/`: reusable prompt fragments.
- `agent/traces/`: audit trail of meaningful runs.

### Output Layer

The vault should eventually produce:

- related work drafts
- research proposals
- experiment plans
- reading maps
- thesis chapters
- presentation decks

## First Milestone

The first milestone is not full automation. It is a reliable loop:

```text
Read paper -> Structure note -> Link concepts -> Weekly synthesis -> Update research questions
```

