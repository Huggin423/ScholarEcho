#!/usr/bin/env python3
"""Check whether notes are likely to be retrievable and reusable."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from vault_utils import ROOT, is_empty_value, iter_markdown_files, object_type, parse_frontmatter, read_text, title_for


REQUIRED_BY_TYPE = {
    "paper": ["id", "title", "status", "trigger_terms", "related_questions", "use_when"],
    "concept": ["id", "name", "aliases", "trigger_terms", "related_questions", "use_when"],
    "method": ["id", "name", "trigger_terms", "related_questions", "best_for", "weak_for"],
    "project": ["id", "name", "status", "primary_questions", "retrieval_seeds"],
    "project_note": ["id", "project", "status"],
    "synthesis": ["id", "status"],
}


@dataclass
class Issue:
    path: Path
    severity: str
    message: str


def check_file(path: Path) -> list[Issue]:
    text = read_text(path)
    frontmatter = parse_frontmatter(text)
    note_type = "project_note" if is_project_note(path) else object_type(path)
    title = title_for(text, path)
    issues: list[Issue] = []

    if not frontmatter:
        issues.append(Issue(path, "warn", f"{title}: missing YAML frontmatter"))
        return issues

    for field in REQUIRED_BY_TYPE.get(note_type, []):
        if is_empty_value(frontmatter.get(field)):
            issues.append(Issue(path, "warn", f"{title}: missing or empty `{field}`"))

    if "needs_review" in frontmatter and frontmatter.get("needs_review") is True:
        issues.append(Issue(path, "info", f"{title}: still marked `needs_review`"))

    if note_type in {"paper", "concept", "method"} and "use_when" not in frontmatter:
        issues.append(Issue(path, "warn", f"{title}: missing activation field `use_when`"))

    return issues


def is_project_note(path: Path) -> bool:
    rel = path.relative_to(ROOT)
    return rel.parts[0] == "05_projects" and path.name != "context.md"


def main() -> None:
    parser = argparse.ArgumentParser(description="Check vault retrieval health.")
    parser.add_argument("--strict", action="store_true", help="Exit with status 1 on warnings")
    args = parser.parse_args()

    issues: list[Issue] = []
    for path in iter_markdown_files():
        issues.extend(check_file(path))

    if not issues:
        print("Vault health: no issues found.")
        return

    for issue in issues:
        rel = issue.path.relative_to(ROOT)
        print(f"{issue.severity.upper():<5} {rel}: {issue.message}")

    warn_count = sum(1 for issue in issues if issue.severity == "warn")
    info_count = sum(1 for issue in issues if issue.severity == "info")
    print(f"\nSummary: {warn_count} warnings, {info_count} info notes.")

    if args.strict and warn_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
