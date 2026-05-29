# Skill: Build Topic Map

## Purpose

Create or update a structured map of a research topic using papers, concepts, methods, and open questions.

## Inputs

- Topic name or project context.
- Relevant paper cards.
- Concept and method cards.
- Existing topic reviews.

## Output

A topic review under `06_synthesis/topic_reviews/` and optional updates to concept or method cards.

## Workflow

1. Define the topic scope.
2. Retrieve relevant papers, concepts, methods, and questions.
3. Cluster papers by theme or method family.
4. Identify central concepts and competing definitions.
5. Identify open problems and evidence gaps.
6. Link the map back to active projects.
7. Write a trace under `agent/traces/`.

## Rules

- Keep the map scoped. Do not turn every topic into a full literature review.
- Use `needs_review: true` when clusters are tentative.
- Preserve uncertainty and disagreement.
- Do not generate a graph file unless requested; Markdown is the first source of truth.

