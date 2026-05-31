#!/usr/bin/env python3
"""Unified local MCP server for ScholarEcho.

This server covers the non-Zotero local tools:

- vault note reads and conservative writes
- explainable vault search and session briefs
- lightweight PDF/text parsing
- citation identifier extraction and public metadata lookup
- Notion export staging into inbox drafts

It uses only the Python standard library and speaks stdio MCP over JSON-RPC.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from check_vault import check_file
from research_session import build_brief
from vault_utils import (
    KNOWLEDGE_DIRS,
    ROOT,
    iter_markdown_files,
    object_type,
    parse_frontmatter,
    read_text,
    search,
    title_for,
)


PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "scholarecho-local-mcp"
SERVER_VERSION = "0.1.0"
INBOX_NOTION_DIR = ROOT / "00_inbox" / "notion_imports"
CONVERTED_NOTION_DIR = INBOX_NOTION_DIR / "converted"
ALLOWED_WRITE_TOPS = {
    "00_inbox",
    "01_papers",
    "02_concepts",
    "03_methods",
    "04_questions",
    "05_projects",
    "06_synthesis",
    "07_outputs",
}
TEMPLATES = {
    "paper": ROOT / "01_papers" / "_template.md",
    "concept": ROOT / "02_concepts" / "_template.md",
    "method": ROOT / "03_methods" / "_template.md",
    "topic_review": ROOT / "06_synthesis" / "topic_reviews" / "_template.md",
    "weekly_synthesis": ROOT / "06_synthesis" / "weekly_synthesis" / "_template.md",
}
TYPE_DIRS = {
    "paper": ROOT / "01_papers",
    "concept": ROOT / "02_concepts",
    "method": ROOT / "03_methods",
    "question": ROOT / "04_questions",
    "project": ROOT / "05_projects",
    "synthesis": ROOT / "06_synthesis",
    "output": ROOT / "07_outputs",
    "topic_review": ROOT / "06_synthesis" / "topic_reviews",
    "weekly_synthesis": ROOT / "06_synthesis" / "weekly_synthesis",
}


class McpError(Exception):
    def __init__(self, code: int, message: str, data: Any | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:72] or "untitled"


def path_in_root(path: Path) -> bool:
    try:
        path.resolve().relative_to(ROOT)
        return True
    except ValueError:
        return False


def relative_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def resolve_repo_path(value: str, *, must_exist: bool = True) -> Path:
    if not value:
        raise McpError(-32602, "Path is required.")

    path = Path(value).expanduser()
    if not path.is_absolute():
        path = ROOT / path
    path = path.resolve()

    if not path_in_root(path):
        raise McpError(-32602, f"Path is outside ScholarEcho: {value}")
    if must_exist and not path.exists():
        raise McpError(-32602, f"Path does not exist: {value}")
    return path


def ensure_safe_write(path: Path) -> None:
    if not path_in_root(path):
        raise McpError(-32602, f"Refusing to write outside ScholarEcho: {path}")
    rel = path.relative_to(ROOT)
    if not rel.parts or rel.parts[0] not in ALLOWED_WRITE_TOPS:
        raise McpError(-32602, f"Refusing to write outside allowed vault areas: {path}")
    if path.suffix != ".md":
        raise McpError(-32602, "ScholarEcho MCP writes only Markdown files.")


def required(args: dict[str, Any], name: str) -> str:
    value = str(args.get(name, "")).strip()
    if not value:
        raise McpError(-32602, f"Missing required argument `{name}`.")
    return value


def bounded_limit(value: Any, default: int = 10, maximum: int = 100) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def truncate(value: str, max_chars: int) -> str:
    return value if len(value) <= max_chars else value[:max_chars] + "\n...[truncated]"


def yaml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, list):
        inner = ", ".join(yaml_value(item) for item in value)
        return f"[{inner}]"
    if value is None:
        return ""
    text = str(value)
    if not text:
        return '""'
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def split_frontmatter(text: str) -> tuple[list[str], list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return [], lines

    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return lines[1:index], lines[index + 1 :]
    return [], lines


def render_frontmatter(data: dict[str, Any]) -> str:
    lines = ["---"]
    for key, value in data.items():
        lines.append(f"{key}: {yaml_value(value)}")
    lines.append("---")
    return "\n".join(lines)


def replace_frontmatter(text: str, updates: dict[str, Any]) -> str:
    frontmatter_lines, body_lines = split_frontmatter(text)
    if not frontmatter_lines:
        data = dict(updates)
    else:
        data = parse_frontmatter(text)
        existing_order = [line.split(":", 1)[0].strip() for line in frontmatter_lines if ":" in line]
        for key in existing_order:
            data.setdefault(key, "")
        data.update(updates)

    return render_frontmatter(data) + "\n" + "\n".join(body_lines).lstrip("\n") + "\n"


def vault_list_notes(args: dict[str, Any]) -> dict[str, Any]:
    note_type = str(args.get("object_type", "")).strip()
    limit = bounded_limit(args.get("limit", 50), default=50, maximum=500)
    directories = None
    if note_type:
        directory = TYPE_DIRS.get(note_type)
        if not directory:
            raise McpError(-32602, f"Unknown object_type: {note_type}")
        directories = [str(directory.relative_to(ROOT))]

    notes = []
    for path in iter_markdown_files(directories)[:limit]:
        text = read_text(path)
        notes.append(
            {
                "path": relative_path(path),
                "object_type": object_type(path),
                "title": title_for(text, path),
                "frontmatter": parse_frontmatter(text),
            }
        )
    return {"notes": notes}


def vault_read_note(args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(required(args, "path"))
    if path.suffix != ".md":
        raise McpError(-32602, "Only Markdown notes can be read through vault_read_note.")
    text = read_text(path)
    return {
        "path": relative_path(path),
        "object_type": object_type(path),
        "title": title_for(text, path),
        "frontmatter": parse_frontmatter(text),
        "text": truncate(text, bounded_limit(args.get("max_chars", 20000), default=20000, maximum=100000)),
    }


def vault_create_note(args: dict[str, Any]) -> dict[str, Any]:
    note_type = required(args, "object_type")
    title = required(args, "title")
    target_dir = TYPE_DIRS.get(note_type)
    if not target_dir:
        raise McpError(-32602, f"Unknown object_type: {note_type}")

    slug = slugify(str(args.get("slug") or title))
    if note_type == "paper":
        filename = f"{datetime.now().year}_unknown_{slug}.md"
    else:
        filename = f"{slug}.md"
    path = (target_dir / filename).resolve()
    ensure_safe_write(path)
    if path.exists():
        raise McpError(-32602, f"Note already exists: {relative_path(path)}")

    fields = dict(args.get("fields") or {})
    fields.setdefault("id", f"{note_type}-{slug}")
    if note_type == "concept":
        fields.setdefault("name", title)
    elif note_type in {"method", "project"}:
        fields.setdefault("name", title)
    else:
        fields.setdefault("title", title)
    fields.setdefault("status", "draft")
    fields.setdefault("needs_review", True)

    template = TEMPLATES.get(note_type)
    if template and template.exists():
        text = replace_frontmatter(template.read_text(encoding="utf-8"), fields)
    else:
        text = render_frontmatter(fields) + f"\n\n# {title}\n\n"

    body = str(args.get("body", "")).strip()
    if body:
        text = text.rstrip() + "\n\n" + body + "\n"

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return {"path": relative_path(path), "created": True}


def vault_append_note(args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(required(args, "path"))
    ensure_safe_write(path)
    text = required(args, "text")
    heading = str(args.get("heading", "")).strip()
    existing = read_text(path)
    addition = f"\n\n## {heading}\n\n{text.strip()}\n" if heading else f"\n\n{text.strip()}\n"
    path.write_text(existing.rstrip() + addition, encoding="utf-8")
    return {"path": relative_path(path), "appended": True}


def vault_update_frontmatter(args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(required(args, "path"))
    ensure_safe_write(path)
    fields = args.get("fields")
    if not isinstance(fields, dict) or not fields:
        raise McpError(-32602, "`fields` must be a non-empty object.")
    updated = replace_frontmatter(read_text(path), fields)
    path.write_text(updated, encoding="utf-8")
    return {"path": relative_path(path), "updated_fields": sorted(fields.keys())}


def search_vault(args: dict[str, Any]) -> dict[str, Any]:
    query = required(args, "query")
    limit = bounded_limit(args.get("limit", 10), maximum=50)
    return {
        "hits": [
            {
                "score": hit.score,
                "path": relative_path(hit.path),
                "object_type": object_type(hit.path),
                "title": hit.title,
                "snippets": hit.snippets,
            }
            for hit in search(query, limit)
        ]
    }


def search_session_brief(args: dict[str, Any]) -> dict[str, Any]:
    query = required(args, "query")
    limit = bounded_limit(args.get("limit", 8), default=8, maximum=30)
    return {"brief": build_brief(query, limit)}


def search_retrieval_health(args: dict[str, Any]) -> dict[str, Any]:
    limit = bounded_limit(args.get("limit", 200), default=200, maximum=1000)
    issues = []
    for path in iter_markdown_files():
        for issue in check_file(path):
            issues.append(
                {
                    "path": relative_path(issue.path),
                    "severity": issue.severity,
                    "message": issue.message,
                }
            )
    return {"issues": issues[:limit], "total": len(issues)}


def resolve_read_path(value: str) -> Path:
    path = Path(value).expanduser()
    if not path.is_absolute():
        path = (ROOT / path).resolve()
    if not path.exists():
        raise McpError(-32602, f"Path does not exist: {value}")
    if path.is_dir():
        raise McpError(-32602, f"Path is a directory: {value}")
    return path


def parse_text_file(args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_read_path(required(args, "path"))
    max_chars = bounded_limit(args.get("max_chars", 20000), default=20000, maximum=200000)
    text = path.read_text(encoding="utf-8", errors="ignore")
    return {
        "path": str(path),
        "text": truncate(text, max_chars),
        "identifiers": extract_identifiers(text),
        "headings": extract_headings(text),
    }


def parse_pdf(args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_read_path(required(args, "path"))
    if path.suffix.lower() != ".pdf":
        raise McpError(-32602, "paper_parse_pdf expects a .pdf file.")
    max_chars = bounded_limit(args.get("max_chars", 20000), default=20000, maximum=200000)
    text, method = pdf_text(path)
    return {
        "path": str(path),
        "method": method,
        "metadata": pdf_metadata(path),
        "identifiers": extract_identifiers(text),
        "headings": extract_probable_sections(text),
        "text": truncate(text, max_chars),
        "note": "Fallback extraction may be noisy if the PDF stores text in compressed streams or scanned images.",
    }


def pdf_text(path: Path) -> tuple[str, str]:
    pdftotext = shutil.which("pdftotext")
    if pdftotext:
        result = subprocess.run(
            [pdftotext, "-layout", str(path), "-"],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.stdout.strip():
            return result.stdout, "pdftotext"

    strings = shutil.which("strings")
    if strings:
        result = subprocess.run(
            [strings, "-n", "5", str(path)],
            check=False,
            capture_output=True,
            text=True,
            timeout=60,
        )
        return result.stdout, "strings"

    return "", "unavailable"


def pdf_metadata(path: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {"size_bytes": path.stat().st_size}
    mdls = shutil.which("mdls")
    if not mdls:
        return metadata
    result = subprocess.run(
        [mdls, "-name", "kMDItemTitle", "-name", "kMDItemAuthors", "-name", "kMDItemNumberOfPages", str(path)],
        check=False,
        capture_output=True,
        text=True,
        timeout=15,
    )
    for line in result.stdout.splitlines():
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        metadata[key.strip()] = value.strip()
    return metadata


def extract_headings(text: str) -> list[str]:
    headings = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("#"):
            headings.append(stripped)
    return headings[:40]


def extract_probable_sections(text: str) -> list[str]:
    sections = []
    pattern = re.compile(r"^(abstract|introduction|background|method|methods|experiments|evaluation|results|discussion|conclusion|references)\b", re.I)
    for line in text.splitlines():
        stripped = line.strip()
        if len(stripped) <= 80 and pattern.search(stripped):
            if stripped not in sections:
                sections.append(stripped)
    return sections[:30]


def extract_identifiers(text: str) -> dict[str, list[str]]:
    doi_pattern = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", re.I)
    arxiv_pattern = re.compile(r"\b(?:arXiv:)?(\d{4}\.\d{4,5}(?:v\d+)?|[a-z\-]+(?:\.[A-Z]{2})?/\d{7}(?:v\d+)?)\b", re.I)
    dois = sorted({match.group(0).rstrip(".,;)") for match in doi_pattern.finditer(text)})
    arxiv_ids = sorted({match.group(1).rstrip(".,;)") for match in arxiv_pattern.finditer(text)})
    return {"doi": dois[:20], "arxiv_id": arxiv_ids[:20]}


def citation_extract_ids(args: dict[str, Any]) -> dict[str, Any]:
    text = required(args, "text")
    return extract_identifiers(text)


def citation_resolve_doi(args: dict[str, Any]) -> dict[str, Any]:
    doi = required(args, "doi").removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    url = f"https://api.crossref.org/works/{urllib.parse.quote(doi, safe='')}"
    data = json_request(url)
    message = data.get("message", {})
    return {
        "doi": doi,
        "title": first(message.get("title")),
        "authors": crossref_authors(message.get("author", [])),
        "year": crossref_year(message),
        "container_title": first(message.get("container-title")),
        "publisher": message.get("publisher"),
        "url": message.get("URL"),
        "source": "crossref",
    }


def citation_resolve_arxiv(args: dict[str, Any]) -> dict[str, Any]:
    arxiv_id = required(args, "arxiv_id").removeprefix("arXiv:")
    url = "https://export.arxiv.org/api/query?" + urllib.parse.urlencode({"id_list": arxiv_id})
    raw = urlopen_text(url)
    root = ET.fromstring(raw)
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entry = root.find("atom:entry", ns)
    if entry is None:
        raise McpError(-32020, f"No arXiv entry found for {arxiv_id}.")
    return {
        "arxiv_id": arxiv_id,
        "title": text_of(entry, "atom:title", ns),
        "summary": text_of(entry, "atom:summary", ns),
        "published": text_of(entry, "atom:published", ns),
        "updated": text_of(entry, "atom:updated", ns),
        "authors": [author.findtext("atom:name", default="", namespaces=ns) for author in entry.findall("atom:author", ns)],
        "url": text_of(entry, "atom:id", ns),
        "source": "arxiv",
    }


def json_request(url: str) -> dict[str, Any]:
    raw = urlopen_text(url, headers={"Accept": "application/json"})
    return json.loads(raw)


def urlopen_text(url: str, headers: dict[str, str] | None = None) -> str:
    request = urllib.request.Request(url, headers=headers or {})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise McpError(-32021, f"HTTP {exc.code} while fetching citation metadata.", detail[:1000]) from exc
    except urllib.error.URLError as exc:
        raise McpError(-32022, f"Could not fetch citation metadata: {exc.reason}") from exc


def first(value: Any) -> str:
    if isinstance(value, list) and value:
        return str(value[0])
    return str(value or "")


def crossref_authors(authors: list[dict[str, Any]]) -> list[str]:
    names = []
    for author in authors:
        parts = [author.get("given", ""), author.get("family", "")]
        name = " ".join(part for part in parts if part).strip()
        if name:
            names.append(name)
    return names


def crossref_year(message: dict[str, Any]) -> str:
    for key in ("published-print", "published-online", "issued"):
        parts = message.get(key, {}).get("date-parts", [])
        if parts and parts[0]:
            return str(parts[0][0])
    return ""


def text_of(entry: ET.Element, selector: str, ns: dict[str, str]) -> str:
    value = entry.findtext(selector, default="", namespaces=ns)
    return re.sub(r"\s+", " ", value).strip()


def notion_list_exports(args: dict[str, Any]) -> dict[str, Any]:
    base = resolve_repo_path(str(args.get("base_path") or "00_inbox/notion_imports"))
    if not base.is_dir():
        raise McpError(-32602, f"Notion import path is not a directory: {relative_path(base)}")
    files = []
    for path in sorted(base.rglob("*")):
        if path.is_file() and path.suffix.lower() in {".md", ".markdown", ".html", ".txt", ".csv"}:
            files.append({"path": relative_path(path), "size_bytes": path.stat().st_size})
    return {"files": files[:bounded_limit(args.get("limit", 100), default=100, maximum=1000)]}


def notion_preview_import(args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(required(args, "path"))
    text = read_notion_source(path)
    converted = notion_to_markdown(path, text)
    return {
        "source_path": relative_path(path),
        "suggested_title": notion_title(path, text),
        "converted_markdown": truncate(converted, bounded_limit(args.get("max_chars", 12000), default=12000, maximum=50000)),
    }


def notion_import_draft(args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_repo_path(required(args, "path"))
    text = read_notion_source(path)
    converted = notion_to_markdown(path, text)
    title = notion_title(path, text)
    target = CONVERTED_NOTION_DIR / f"{slugify(title)}.md"
    ensure_safe_write(target)
    if target.exists() and not args.get("overwrite", False):
        raise McpError(-32602, f"Draft already exists: {relative_path(target)}")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(converted, encoding="utf-8")
    return {"source_path": relative_path(path), "draft_path": relative_path(target), "created": True}


def read_notion_source(path: Path) -> str:
    if path.suffix.lower() == ".html":
        raw = path.read_text(encoding="utf-8", errors="ignore")
        return re.sub(r"<[^>]+>", " ", raw)
    return path.read_text(encoding="utf-8", errors="ignore")


def notion_title(path: Path, text: str) -> str:
    for line in text.splitlines():
        stripped = line.strip().lstrip("#").strip()
        if stripped:
            return stripped[:120]
    return path.stem


def notion_to_markdown(path: Path, text: str) -> str:
    title = notion_title(path, text)
    body = text.strip()
    if path.suffix.lower() == ".html":
        body = re.sub(r"\s+", " ", body).strip()
    frontmatter = {
        "id": f"notion-import-{slugify(title)}",
        "title": title,
        "source": "notion_export",
        "source_path": relative_path(path),
        "status": "draft",
        "trigger_terms": [],
        "related_questions": [],
        "use_when": [],
        "confidence": "low",
        "needs_review": True,
    }
    return (
        render_frontmatter(frontmatter)
        + "\n\n# "
        + title
        + "\n\n"
        + "## Imported Content\n\n"
        + body
        + "\n\n## Conversion Notes\n\n- Imported as a draft from Notion export; review links, citations, and activation cues before promoting into durable knowledge.\n"
    )


ToolHandler = Callable[[dict[str, Any]], dict[str, Any]]


TOOLS: dict[str, dict[str, Any]] = {
    "vault_list_notes": {
        "description": "List ScholarEcho Markdown notes and their frontmatter.",
        "handler": vault_list_notes,
        "inputSchema": {
            "type": "object",
            "properties": {
                "object_type": {"type": "string", "description": "Optional type such as paper, concept, method, question, project, synthesis, output."},
                "limit": {"type": "integer", "default": 50, "minimum": 1, "maximum": 500},
            },
        },
    },
    "vault_read_note": {
        "description": "Read one Markdown note inside the ScholarEcho repository.",
        "handler": vault_read_note,
        "inputSchema": {
            "type": "object",
            "required": ["path"],
            "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer", "default": 20000}},
        },
    },
    "vault_create_note": {
        "description": "Create a conservative draft knowledge note from an existing template when available.",
        "handler": vault_create_note,
        "inputSchema": {
            "type": "object",
            "required": ["object_type", "title"],
            "properties": {
                "object_type": {"type": "string"},
                "title": {"type": "string"},
                "slug": {"type": "string"},
                "fields": {"type": "object"},
                "body": {"type": "string"},
            },
        },
    },
    "vault_append_note": {
        "description": "Append Markdown to an existing note. Does not delete or rewrite human content.",
        "handler": vault_append_note,
        "inputSchema": {
            "type": "object",
            "required": ["path", "text"],
            "properties": {"path": {"type": "string"}, "heading": {"type": "string"}, "text": {"type": "string"}},
        },
    },
    "vault_update_frontmatter": {
        "description": "Update YAML frontmatter fields on a note while preserving body content.",
        "handler": vault_update_frontmatter,
        "inputSchema": {
            "type": "object",
            "required": ["path", "fields"],
            "properties": {"path": {"type": "string"}, "fields": {"type": "object"}},
        },
    },
    "search_vault": {
        "description": "Run ScholarEcho's explainable local search.",
        "handler": search_vault,
        "inputSchema": {"type": "object", "required": ["query"], "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 10}}},
    },
    "search_session_brief": {
        "description": "Build a compact research session brief for a current question.",
        "handler": search_session_brief,
        "inputSchema": {"type": "object", "required": ["query"], "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "default": 8}}},
    },
    "search_retrieval_health": {
        "description": "Report notes missing retrieval cues or review markers.",
        "handler": search_retrieval_health,
        "inputSchema": {"type": "object", "properties": {"limit": {"type": "integer", "default": 200}}},
    },
    "paper_parse_pdf": {
        "description": "Extract rough text, metadata, sections, and identifiers from a PDF.",
        "handler": parse_pdf,
        "inputSchema": {"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer", "default": 20000}}},
    },
    "paper_parse_text": {
        "description": "Extract headings and citation identifiers from a text or Markdown file.",
        "handler": parse_text_file,
        "inputSchema": {"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer", "default": 20000}}},
    },
    "citation_extract_ids": {
        "description": "Extract DOI and arXiv identifiers from text.",
        "handler": citation_extract_ids,
        "inputSchema": {"type": "object", "required": ["text"], "properties": {"text": {"type": "string"}}},
    },
    "citation_resolve_doi": {
        "description": "Resolve DOI metadata through Crossref.",
        "handler": citation_resolve_doi,
        "inputSchema": {"type": "object", "required": ["doi"], "properties": {"doi": {"type": "string"}}},
    },
    "citation_resolve_arxiv": {
        "description": "Resolve arXiv metadata through the arXiv API.",
        "handler": citation_resolve_arxiv,
        "inputSchema": {"type": "object", "required": ["arxiv_id"], "properties": {"arxiv_id": {"type": "string"}}},
    },
    "notion_list_exports": {
        "description": "List Notion export files staged under 00_inbox/notion_imports.",
        "handler": notion_list_exports,
        "inputSchema": {"type": "object", "properties": {"base_path": {"type": "string"}, "limit": {"type": "integer", "default": 100}}},
    },
    "notion_preview_import": {
        "description": "Preview a Notion export converted to a ScholarEcho draft without writing files.",
        "handler": notion_preview_import,
        "inputSchema": {"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}, "max_chars": {"type": "integer", "default": 12000}}},
    },
    "notion_import_draft": {
        "description": "Convert a Notion export into an inbox draft under 00_inbox/notion_imports/converted.",
        "handler": notion_import_draft,
        "inputSchema": {"type": "object", "required": ["path"], "properties": {"path": {"type": "string"}, "overwrite": {"type": "boolean", "default": False}}},
    },
}


def tool_specs() -> list[dict[str, Any]]:
    return [
        {
            "name": name,
            "description": spec["description"],
            "inputSchema": spec["inputSchema"],
        }
        for name, spec in TOOLS.items()
    ]


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params") or {}

    try:
        if method == "initialize":
            result: dict[str, Any] = {
                "protocolVersion": params.get("protocolVersion") or PROTOCOL_VERSION,
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            }
        elif method == "ping":
            result = {}
        elif method == "tools/list":
            result = {"tools": tool_specs()}
        elif method == "tools/call":
            result = call_tool(params)
        elif method in {"notifications/initialized", "notifications/cancelled"}:
            return None
        elif request_id is None:
            return None
        else:
            raise McpError(-32601, f"Unknown method: {method}")
        if request_id is None:
            return None
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    except McpError as exc:
        if request_id is None:
            return None
        error: dict[str, Any] = {"code": exc.code, "message": exc.message}
        if exc.data is not None:
            error["data"] = exc.data
        return {"jsonrpc": "2.0", "id": request_id, "error": error}
    except Exception as exc:  # pragma: no cover - keeps MCP session alive.
        if request_id is None:
            return None
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32603, "message": str(exc), "data": traceback.format_exc()},
        }


def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    spec = TOOLS.get(name)
    if not spec:
        raise McpError(-32602, f"Unknown tool: {name}")
    payload = spec["handler"](arguments)
    return {
        "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False, indent=2)}],
        "isError": False,
    }


def read_message(stdin: Any) -> dict[str, Any] | None:
    first = stdin.readline()
    if not first:
        return None
    stripped = first.strip()
    if not stripped:
        return read_message(stdin)
    if stripped.startswith(b"{"):
        return json.loads(stripped.decode("utf-8"))

    headers: dict[str, str] = {}
    line = first
    while line.strip():
        key, _, value = line.decode("utf-8").partition(":")
        headers[key.lower()] = value.strip()
        line = stdin.readline()

    length = int(headers.get("content-length", "0"))
    if length <= 0:
        raise McpError(-32700, "Missing Content-Length header.")
    body = stdin.read(length)
    return json.loads(body.decode("utf-8"))


def write_message(stdout: Any, message: dict[str, Any]) -> None:
    body = json.dumps(message, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    stdout.write(f"Content-Length: {len(body)}\r\n\r\n".encode("ascii"))
    stdout.write(body)
    stdout.flush()


def serve() -> None:
    stdin = sys.stdin.buffer
    stdout = sys.stdout.buffer
    while True:
        request = read_message(stdin)
        if request is None:
            return
        response = handle_request(request)
        if response is not None:
            write_message(stdout, response)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the ScholarEcho local MCP server.")
    parser.add_argument("--check", action="store_true", help="Print server info and available tools.")
    args = parser.parse_args()

    if args.check:
        print(
            json.dumps(
                {
                    "root": str(ROOT),
                    "server": SERVER_NAME,
                    "version": SERVER_VERSION,
                    "tools": sorted(TOOLS.keys()),
                    "knowledge_dirs": KNOWLEDGE_DIRS,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    serve()


if __name__ == "__main__":
    main()
