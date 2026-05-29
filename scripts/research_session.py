#!/usr/bin/env python3
"""Prepare a compact research session brief from a question or task."""

from __future__ import annotations

import argparse
import re
from datetime import datetime
from pathlib import Path

from vault_utils import ROOT, is_empty_value, object_type, parse_frontmatter, read_text, search


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:48] or "session"


def missing_cues(path: Path) -> list[str]:
    frontmatter = parse_frontmatter(read_text(path))
    note_type = object_type(path)
    required = {
        "paper": ["trigger_terms", "related_questions", "use_when"],
        "concept": ["aliases", "trigger_terms", "related_questions", "use_when"],
        "method": ["trigger_terms", "related_questions", "best_for", "weak_for"],
        "project": ["primary_questions", "retrieval_seeds"],
        "synthesis": ["trigger_terms", "questions"],
    }.get(note_type, [])

    missing: list[str] = []
    for field in required:
        if is_empty_value(frontmatter.get(field)):
            missing.append(field)
    return missing


def build_brief(query: str, limit: int) -> str:
    hits = search(query, limit)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines: list[str] = [
        "---",
        f"timestamp: {now}",
        f"query: {query}",
        "status: draft",
        "---",
        "",
        "# Research Session Brief",
        "",
        "## Current Question",
        "",
        query,
        "",
        "## Retrieved Context",
        "",
    ]

    if not hits:
        lines.extend(
            [
                "No matching notes found.",
                "",
                "This may mean the question is new, or existing notes need better trigger terms.",
                "",
            ]
        )
    else:
        for index, hit in enumerate(hits, start=1):
            rel = hit.path.relative_to(ROOT)
            lines.append(f"### {index}. {hit.title}")
            lines.append("")
            lines.append(f"- path: `{rel}`")
            lines.append(f"- type: {object_type(hit.path)}")
            lines.append(f"- score: {hit.score}")
            missing = missing_cues(hit.path)
            if missing:
                lines.append(f"- missing retrieval cues: {', '.join(missing)}")
            lines.append("- why it matched:")
            for snippet in hit.snippets:
                lines.append(f"  - {snippet}")
            lines.append("")

    lines.extend(
        [
            "## Before Writing",
            "",
            "- Check whether one of the retrieved notes should be updated instead of creating a new note.",
            "- Connect any new claim to a question, project, concept, method, or paper.",
            "- Add trigger terms if a useful note was hard to find.",
            "",
            "## Suggested Next Actions",
            "",
            "1. Open the top matching project or question note.",
            "2. Decide whether the current task is reading, comparison, synthesis, or writing.",
            "3. Update the smallest useful note after the session.",
            "",
        ]
    )
    return "\n".join(lines)


def save_brief(text: str, query: str) -> Path:
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = ROOT / "agent" / "traces" / f"{stamp}_session-{slugify(query)}.md"
    path.write_text(text, encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare a research session brief.")
    parser.add_argument("query", help="Current research question or task")
    parser.add_argument("--limit", type=int, default=8, help="Maximum retrieved notes")
    parser.add_argument("--save", action="store_true", help="Save brief to agent/traces")
    args = parser.parse_args()

    brief = build_brief(args.query, args.limit)
    print(brief)
    if args.save:
        path = save_brief(brief, args.query)
        print(f"\nSaved: {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
