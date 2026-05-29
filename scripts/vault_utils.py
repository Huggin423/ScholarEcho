"""Shared helpers for local vault scripts."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
KNOWLEDGE_DIRS = [
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
CJK_STOPWORDS = {
    "什么",
    "如何",
    "怎么",
    "为什么",
    "这个",
    "那个",
    "用于",
    "以及",
    "还是",
    "是否",
}


@dataclass
class Hit:
    score: int
    path: Path
    title: str
    snippets: list[str]


def tokenize(query: str) -> list[str]:
    parts = re.findall(r"[\w\-\u4e00-\u9fff]+", query.lower())
    terms: list[str] = []
    seen: set[str] = set()

    for part in parts:
        candidates = cjk_terms(part) if has_cjk(part) else [part]
        for term in candidates:
            if len(term) <= 1 or term in CJK_STOPWORDS or term in seen:
                continue
            seen.add(term)
            terms.append(term)
    return terms


def has_cjk(value: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in value)


def cjk_terms(value: str) -> list[str]:
    cjk_chars = [char for char in value if "\u4e00" <= char <= "\u9fff"]
    if len(cjk_chars) <= 2:
        return ["".join(cjk_chars)]

    compact = "".join(cjk_chars)
    bigrams = [compact[index : index + 2] for index in range(len(compact) - 1)]
    return [compact, *bigrams]


def iter_markdown_files(directories: list[str] | None = None) -> list[Path]:
    files: list[Path] = []
    for directory in directories or KNOWLEDGE_DIRS:
        base = ROOT / directory
        if base.exists():
            files.extend(
                path
                for path in base.rglob("*.md")
                if path.is_file()
                and not path.name.startswith("_")
                and path.name != "README.md"
            )
    return sorted(files)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def title_for(text: str, path: Path) -> str:
    frontmatter = parse_frontmatter(text)
    for key in ("title", "name", "id"):
        value = frontmatter.get(key)
        if isinstance(value, str) and value:
            return value

    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def parse_frontmatter(text: str) -> dict[str, str | list[str] | bool]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}

    data: dict[str, str | list[str] | bool] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        key = key.strip()
        raw = raw.strip()
        data[key] = parse_value(raw)
    return data


def parse_value(raw: str) -> str | list[str] | bool:
    if raw in {"true", "false"}:
        return raw == "true"
    if raw == "[]":
        return []
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip('"').strip("'") for part in inner.split(",")]
    return raw.strip('"').strip("'")


def is_empty_value(value: object) -> bool:
    return value is None or value == "" or value is False or value == []


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

        score += field_weight(line) * len(matched)
        if len(snippets) < 3:
            snippets.append(line[:220])

    return score, snippets


def search(query: str, limit: int) -> list[Hit]:
    terms = tokenize(query)
    if not terms:
        raise SystemExit("Query must contain at least one searchable term.")

    hits: list[Hit] = []
    for path in iter_markdown_files():
        text = read_text(path)
        score, snippets = score_file(text, terms)
        if score:
            hits.append(Hit(score, path, title_for(text, path), snippets))

    hits.sort(key=lambda hit: (-hit.score, str(hit.path)))
    return hits[:limit]


def object_type(path: Path) -> str:
    rel = path.relative_to(ROOT)
    top = rel.parts[0]
    return {
        "01_papers": "paper",
        "02_concepts": "concept",
        "03_methods": "method",
        "04_questions": "question",
        "05_projects": "project",
        "06_synthesis": "synthesis",
        "07_outputs": "output",
    }.get(top, "note")
