#!/usr/bin/env python3
"""Search the vault with simple, explainable ranking."""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEARCH_DIRS = [
    "04_questions",
    "05_projects",
    "02_concepts",
    "03_methods",
    "01_papers",
    "06_synthesis",
    "07_outputs",
]
FRONTMATTER_FIELDS = {
    "id",
    "title",
    "name",
    "aliases",
    "trigger_terms",
    "related_questions",
    "supports",
    "challenges",
    "use_when",
    "retrieval_seeds",
}


@dataclass
class Hit:
    score: int
    path: Path
    title: str
    snippets: list[str]


def tokenize(query: str) -> list[str]:
    parts = re.findall(r"[\w\-\u4e00-\u9fff]+", query.lower())
    return [part for part in parts if len(part) > 1]


def iter_markdown_files() -> list[Path]:
    files: list[Path] = []
    for directory in SEARCH_DIRS:
        base = ROOT / directory
        if base.exists():
            files.extend(
                path
                for path in base.rglob("*.md")
                if path.is_file() and not path.name.startswith("_")
            )
    return sorted(files)


def title_for(text: str, path: Path) -> str:
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
        if line.startswith("title:") or line.startswith("name:"):
            value = line.split(":", 1)[1].strip().strip('"')
            if value:
                return value
    return path.stem


def field_weight(line: str) -> int:
    key = line.split(":", 1)[0].strip()
    if key in FRONTMATTER_FIELDS:
        return 5
    if line.startswith("#"):
        return 3
    return 1


def score_file(text: str, terms: list[str]) -> tuple[int, list[str]]:
    score = 0
    snippets: list[str] = []

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        lower = line.lower()
        matched = [term for term in terms if term in lower]
        if not matched:
            continue

        weight = field_weight(line)
        score += weight * len(matched)
        if len(snippets) < 3:
            snippets.append(line[:220])

    return score, snippets


def search(query: str, limit: int) -> list[Hit]:
    terms = tokenize(query)
    if not terms:
        raise SystemExit("Query must contain at least one searchable term.")

    hits: list[Hit] = []
    for path in iter_markdown_files():
        text = path.read_text(encoding="utf-8", errors="ignore")
        score, snippets = score_file(text, terms)
        if score:
            hits.append(Hit(score, path, title_for(text, path), snippets))

    hits.sort(key=lambda hit: (-hit.score, str(hit.path)))
    return hits[:limit]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search research vault notes.")
    parser.add_argument("query", help="Keyword, phrase, or research question")
    parser.add_argument("--limit", type=int, default=10, help="Maximum results")
    args = parser.parse_args()

    for hit in search(args.query, args.limit):
        rel = hit.path.relative_to(ROOT)
        print(f"{hit.score:>3}  {rel}  |  {hit.title}")
        for snippet in hit.snippets:
            print(f"     {snippet}")


if __name__ == "__main__":
    main()
