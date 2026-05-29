# Skill: Compare Papers

## Purpose

Compare two or more papers around a specific research question.

## Inputs

- A research question or project goal.
- Two or more paper cards from `01_papers/`.
- Related concept and method cards.
- Optional project context from `05_projects/`.

## Output

A synthesis note under `06_synthesis/topic_reviews/` or an update to an existing project note.

## Workflow

1. State the question being compared.
2. Retrieve relevant paper, concept, method, and synthesis notes before writing.
3. Read each paper card and identify:
   - research problem
   - core claims
   - method
   - evidence
   - limits
   - use_when
4. Build a compact comparison table.
5. Identify agreements, disagreements, missing evidence, and practical implications.
6. Update related questions, project context, or hypotheses if useful.
7. Write a trace under `agent/traces/`.

## Comparison Dimensions

- Problem framing
- Assumptions
- Method family
- Data or benchmark
- Evaluation metric
- Claimed contribution
- Failure modes
- Relevance to my project
- Whether it supports or challenges the active question

## Rules

- Do not force a relationship if the papers are only loosely related.
- Mark inferred relationships as inference.
- Preserve minority or conflicting viewpoints.
- Avoid collapsing different definitions into one concept without review.
- Do not produce a broad literature review unless requested.
