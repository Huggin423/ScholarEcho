#!/usr/bin/env python3
"""Create a new paper card from basic metadata."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PAPER_DIR = ROOT / "01_papers"
TEMPLATE = PAPER_DIR / "_template.md"


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "untitled"


def yaml_quote(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a structured paper card.")
    parser.add_argument("--title", required=True, help="Paper title")
    parser.add_argument("--year", required=True, help="Publication year")
    parser.add_argument("--first-author", required=True, help="First author surname")
    parser.add_argument("--venue", default="", help="Venue name")
    parser.add_argument("--zotero-key", default="", help="Zotero key")
    parser.add_argument("--doi", default="", help="DOI")
    parser.add_argument("--arxiv-id", default="", help="arXiv id")
    args = parser.parse_args()

    short_title = "-".join(slugify(args.title).split("-")[:5])
    author = slugify(args.first_author)
    paper_id = f"paper-{args.year}-{author}-{short_title}"
    path = PAPER_DIR / f"{args.year}_{author}_{short_title}.md"

    if path.exists():
        raise SystemExit(f"Paper card already exists: {path}")

    text = TEMPLATE.read_text(encoding="utf-8")
    replacements = {
        "id: paper-yyyy-author-shorttitle": f"id: {paper_id}",
        "title:": f"title: {yaml_quote(args.title)}",
        "authors: []": f"authors: [{yaml_quote(args.first_author)}]",
        "year:": f"year: {args.year}",
        "venue:": f"venue: {yaml_quote(args.venue)}",
        "zotero_key:": f"zotero_key: {yaml_quote(args.zotero_key)}",
        "doi:": f"doi: {yaml_quote(args.doi)}",
        "arxiv_id:": f"arxiv_id: {yaml_quote(args.arxiv_id)}",
    }

    for old, new in replacements.items():
        text = text.replace(old, new, 1)

    path.write_text(text, encoding="utf-8")
    print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
