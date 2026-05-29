# Skill: Build Topic Map

## Purpose

Create or update a small topic map only when it helps answer an active question.

## Inputs

- Topic name and active question.
- Project context.
- Relevant paper cards.
- Concept and method cards.
- Existing topic reviews.

## Output

A topic review under `06_synthesis/topic_reviews/` and optional updates to concept or method cards.

## Workflow

1. Define the topic scope in one paragraph.
2. Retrieve relevant papers, concepts, methods, questions, and synthesis notes.
3. Cluster only the material needed for the active question.
4. Identify central concepts, competing definitions, and method families.
5. Identify open problems and evidence gaps.
6. Add `trigger_terms` and `use_when` so the map can resurface later.
7. Link the map back to active projects and questions.
8. Write a trace under `agent/traces/`.

## Rules

- Keep the map scoped. Do not turn every topic into a full literature review.
- Use `needs_review: true` when clusters are tentative.
- Preserve uncertainty and disagreement.
- Do not generate a graph file unless requested; Markdown is the first source of truth.
- If the topic map becomes too broad, split by question rather than by subfield.
