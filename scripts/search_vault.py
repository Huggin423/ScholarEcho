#!/usr/bin/env python3
"""Search ScholarEcho with simple, explainable ranking."""

from __future__ import annotations

import argparse

from vault_utils import ROOT, search


def main() -> None:
    parser = argparse.ArgumentParser(description="Search ScholarEcho notes.")
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
