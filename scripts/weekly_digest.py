#!/usr/bin/env python3
"""Prepare a small weekly digest candidate from recent git changes."""

from __future__ import annotations

import argparse
import subprocess
from collections import defaultdict
from pathlib import Path

from vault_utils import ROOT, object_type, read_text, title_for


def changed_files(since: str) -> list[Path]:
    cmd = ["git", "log", f"--since={since}", "--name-only", "--pretty=format:"]
    result = subprocess.run(cmd, cwd=ROOT, check=False, capture_output=True, text=True)
    if result.returncode != 0:
        return []

    paths: list[Path] = []
    seen: set[Path] = set()
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or not line.endswith(".md"):
            continue
        path = ROOT / line
        if path.name.startswith("_") or path.name == "README.md":
            continue
        if path.exists() and path not in seen:
            seen.add(path)
            paths.append(path)
    return sorted(paths)


def main() -> None:
    parser = argparse.ArgumentParser(description="Show weekly synthesis candidates.")
    parser.add_argument("--since", default="7 days ago", help="Git date expression")
    args = parser.parse_args()

    groups: dict[str, list[Path]] = defaultdict(list)
    for path in changed_files(args.since):
        if path.relative_to(ROOT).parts[0] in {"docs", "agent", "scripts"}:
            continue
        groups[object_type(path)].append(path)

    print("# Weekly Digest Candidate")
    print("")
    print(f"Since: {args.since}")
    print("")

    if not groups:
        print("No changed knowledge notes found.")
        return

    for note_type in ["question", "project", "paper", "concept", "method", "synthesis", "output"]:
        paths = groups.get(note_type, [])
        if not paths:
            continue
        print(f"## {note_type.title()} Notes")
        print("")
        for path in paths:
            text = read_text(path)
            rel = path.relative_to(ROOT)
            print(f"- `{rel}`: {title_for(text, path)}")
        print("")

    print("## Review Prompts")
    print("")
    print("- Which old note became relevant again this week?")
    print("- Which active question became clearer or more confusing?")
    print("- Which note needs better trigger terms so it can resurface later?")
    print("- What is the smallest useful next action?")


if __name__ == "__main__":
    main()
