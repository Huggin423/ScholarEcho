#!/usr/bin/env python3
"""MCP server for reading Zotero metadata into ScholarEcho workflows.

This server intentionally uses only the Python standard library. It speaks a
small, stdio-friendly subset of MCP over JSON-RPC and calls the Zotero Web API.
Local PDF paths are resolved best-effort from Zotero attachment metadata.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "scholarecho-zotero-mcp"
SERVER_VERSION = "0.1.0"
ZOTERO_API_VERSION = "3"
DEFAULT_API_BASE = "https://api.zotero.org"
ROOT = Path(__file__).resolve().parents[1]


class McpError(Exception):
    """JSON-RPC error that can be returned to the MCP client."""

    def __init__(self, code: int, message: str, data: Any | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


@dataclass(frozen=True)
class ZoteroConfig:
    api_base: str
    library_type: str
    library_id: str
    api_key: str
    storage_dir: Path

    @property
    def library_path(self) -> str:
        if self.library_type == "group":
            return f"groups/{self.library_id}"
        return f"users/{self.library_id}"


def env(name: str, default: str = "") -> str:
    return os.environ.get(name, default).strip()


def load_dotenv(path: Path = ROOT / ".env") -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def load_config() -> ZoteroConfig:
    load_dotenv()
    library_type = env("ZOTERO_LIBRARY_TYPE", "user").lower()
    if library_type not in {"user", "group"}:
        raise McpError(-32000, "ZOTERO_LIBRARY_TYPE must be `user` or `group`.")

    library_id = (
        env("ZOTERO_GROUP_ID")
        if library_type == "group"
        else env("ZOTERO_USER_ID") or env("ZOTERO_LIBRARY_ID")
    )
    if not library_id:
        key_name = "ZOTERO_GROUP_ID" if library_type == "group" else "ZOTERO_USER_ID"
        raise McpError(-32000, f"Missing {key_name} for Zotero MCP.")

    return ZoteroConfig(
        api_base=env("ZOTERO_API_BASE", DEFAULT_API_BASE).rstrip("/"),
        library_type=library_type,
        library_id=library_id,
        api_key=env("ZOTERO_API_KEY"),
        storage_dir=zotero_storage_dir(),
    )


def zotero_storage_dir() -> Path:
    load_dotenv()
    data_dir = Path(env("ZOTERO_DATA_DIR", str(Path.home() / "Zotero"))).expanduser()
    return Path(env("ZOTERO_STORAGE_DIR", str(data_dir / "storage"))).expanduser()


def zotero_request(path: str, params: dict[str, Any] | None = None) -> Any:
    config = load_config()
    clean_params = {key: value for key, value in (params or {}).items() if value not in {None, ""}}
    query = urllib.parse.urlencode(clean_params, doseq=True)
    url = f"{config.api_base}/{config.library_path}/{path.lstrip('/')}"
    if query:
        url = f"{url}?{query}"

    headers = {
        "Accept": "application/json",
        "Zotero-API-Version": ZOTERO_API_VERSION,
    }
    if config.api_key:
        headers["Zotero-API-Key"] = config.api_key

    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="ignore")
        raise McpError(-32010, f"Zotero API returned HTTP {exc.code}.", detail[:1000]) from exc
    except urllib.error.URLError as exc:
        raise McpError(-32011, f"Could not reach Zotero API: {exc.reason}") from exc

    if not raw:
        return None
    return json.loads(raw)


def item_data(item: dict[str, Any]) -> dict[str, Any]:
    return item.get("data", item)


def creator_name(creator: dict[str, Any]) -> str:
    if creator.get("name"):
        return str(creator["name"])
    parts = [creator.get("firstName", ""), creator.get("lastName", "")]
    return " ".join(part for part in parts if part).strip()


def summarize_item(item: dict[str, Any]) -> dict[str, Any]:
    data = item_data(item)
    creators = [creator_name(creator) for creator in data.get("creators", [])]
    return {
        "key": data.get("key"),
        "item_type": data.get("itemType"),
        "title": data.get("title"),
        "creators": [name for name in creators if name],
        "year": year_from_date(str(data.get("date", ""))),
        "date": data.get("date"),
        "publication": data.get("publicationTitle") or data.get("conferenceName"),
        "doi": data.get("DOI"),
        "url": data.get("url"),
        "tags": [tag.get("tag") for tag in data.get("tags", []) if tag.get("tag")],
        "collections": data.get("collections", []),
        "date_modified": data.get("dateModified"),
    }


def year_from_date(value: str) -> str:
    for token in value.replace("/", "-").split("-"):
        if len(token) == 4 and token.isdigit():
            return token
    return ""


def resolve_attachment_path(data: dict[str, Any]) -> str:
    filename = data.get("filename") or ""
    raw_path = data.get("path") or ""
    attachment_key = data.get("key") or ""
    storage_dir = zotero_storage_dir()

    if raw_path.startswith("storage:"):
        name = raw_path.removeprefix("storage:")
        return str(storage_dir / attachment_key / name)
    if raw_path and Path(raw_path).expanduser().is_absolute():
        return str(Path(raw_path).expanduser())
    if filename and attachment_key:
        return str(storage_dir / attachment_key / filename)
    return ""


def summarize_attachment(item: dict[str, Any]) -> dict[str, Any]:
    data = item_data(item)
    path = resolve_attachment_path(data)
    result = {
        "key": data.get("key"),
        "title": data.get("title"),
        "content_type": data.get("contentType"),
        "link_mode": data.get("linkMode"),
        "filename": data.get("filename"),
        "path": path,
    }
    if path:
        result["path_exists"] = Path(path).exists()
    return result


def zotero_search_items(arguments: dict[str, Any]) -> dict[str, Any]:
    limit = bounded_limit(arguments.get("limit", 10), maximum=50)
    params = {
        "format": "json",
        "q": arguments.get("query") or arguments.get("q"),
        "limit": limit,
        "sort": arguments.get("sort", "dateModified"),
        "direction": arguments.get("direction", "desc"),
        "itemType": arguments.get("item_type"),
        "tag": arguments.get("tag"),
    }
    items = zotero_request("items", params)
    return {"items": [summarize_item(item) for item in items]}


def zotero_get_item(arguments: dict[str, Any]) -> dict[str, Any]:
    key = required(arguments, "key")
    item = zotero_request(f"items/{key}", {"format": "json"})
    result = summarize_item(item)
    result["raw_data"] = item_data(item)

    if arguments.get("include_children", True):
        children = zotero_request(f"items/{key}/children", {"format": "json", "limit": 100})
        result["attachments"] = [
            summarize_attachment(child)
            for child in children
            if item_data(child).get("itemType") == "attachment"
        ]
        result["notes"] = [
            {
                "key": item_data(child).get("key"),
                "title": item_data(child).get("title"),
                "note": item_data(child).get("note"),
            }
            for child in children
            if item_data(child).get("itemType") == "note"
        ]
    return result


def zotero_get_collections(arguments: dict[str, Any]) -> dict[str, Any]:
    limit = bounded_limit(arguments.get("limit", 50), maximum=100)
    collections = zotero_request("collections", {"format": "json", "limit": limit})
    return {
        "collections": [
            {
                "key": item_data(collection).get("key"),
                "name": item_data(collection).get("name"),
                "parent_collection": item_data(collection).get("parentCollection"),
                "number_of_items": collection.get("meta", {}).get("numItems"),
            }
            for collection in collections
        ]
    }


def zotero_get_collection_items(arguments: dict[str, Any]) -> dict[str, Any]:
    collection_key = required(arguments, "collection_key")
    limit = bounded_limit(arguments.get("limit", 25), maximum=100)
    items = zotero_request(
        f"collections/{collection_key}/items",
        {"format": "json", "limit": limit, "sort": "dateModified", "direction": "desc"},
    )
    return {"items": [summarize_item(item) for item in items]}


def zotero_paper_card_seed(arguments: dict[str, Any]) -> dict[str, Any]:
    item = zotero_get_item({"key": required(arguments, "key"), "include_children": True})
    creators = item.get("creators", [])
    first_author = last_name(creators[0]) if creators else ""
    attachments = item.get("attachments", [])
    pdf_path = next(
        (
            attachment.get("path", "")
            for attachment in attachments
            if "pdf" in str(attachment.get("content_type", "")).lower()
            or str(attachment.get("filename", "")).lower().endswith(".pdf")
        ),
        "",
    )
    return {
        "paper_card_fields": {
            "title": item.get("title", ""),
            "authors": creators,
            "year": item.get("year", ""),
            "venue": item.get("publication", ""),
            "zotero_key": item.get("key", ""),
            "doi": item.get("doi", ""),
            "url": item.get("url", ""),
            "pdf_path": pdf_path,
            "trigger_terms": item.get("tags", []),
            "source_missing": False,
            "needs_review": True,
        },
        "new_paper_command": command_for_new_paper(item, first_author),
        "attachments": attachments,
    }


def last_name(name: str) -> str:
    parts = name.split()
    return parts[-1] if parts else name


def command_for_new_paper(item: dict[str, Any], first_author: str) -> str:
    args = {
        "--title": item.get("title", ""),
        "--year": item.get("year", ""),
        "--first-author": first_author,
        "--venue": item.get("publication", ""),
        "--zotero-key": item.get("key", ""),
        "--doi": item.get("doi", ""),
    }
    pieces = ["python3", "scripts/new_paper_card.py"]
    for flag, value in args.items():
        if value:
            pieces.extend([flag, shell_quote(str(value))])
    return " ".join(pieces)


def shell_quote(value: str) -> str:
    return "'" + value.replace("'", "'\"'\"'") + "'"


def required(arguments: dict[str, Any], name: str) -> str:
    value = str(arguments.get(name, "")).strip()
    if not value:
        raise McpError(-32602, f"Missing required argument `{name}`.")
    return value


def bounded_limit(value: Any, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 10
    return max(1, min(parsed, maximum))


TOOLS = {
    "zotero_search_items": {
        "description": "Search Zotero items by query, item type, or tag.",
        "handler": zotero_search_items,
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Free-text Zotero search query."},
                "item_type": {"type": "string", "description": "Optional Zotero item type, e.g. journalArticle."},
                "tag": {"type": "string", "description": "Optional Zotero tag filter."},
                "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
            },
        },
    },
    "zotero_get_item": {
        "description": "Fetch one Zotero item by key, including child attachments and notes by default.",
        "handler": zotero_get_item,
        "inputSchema": {
            "type": "object",
            "required": ["key"],
            "properties": {
                "key": {"type": "string", "description": "Zotero item key."},
                "include_children": {"type": "boolean", "default": True},
            },
        },
    },
    "zotero_get_collections": {
        "description": "List Zotero collections.",
        "handler": zotero_get_collections,
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
            },
        },
    },
    "zotero_get_collection_items": {
        "description": "List recent items from a Zotero collection.",
        "handler": zotero_get_collection_items,
        "inputSchema": {
            "type": "object",
            "required": ["collection_key"],
            "properties": {
                "collection_key": {"type": "string"},
                "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 25},
            },
        },
    },
    "zotero_paper_card_seed": {
        "description": "Build a ScholarEcho paper-card seed from a Zotero item without writing files.",
        "handler": zotero_paper_card_seed,
        "inputSchema": {
            "type": "object",
            "required": ["key"],
            "properties": {
                "key": {"type": "string", "description": "Zotero item key."},
            },
        },
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
            "error": {
                "code": -32603,
                "message": str(exc),
                "data": traceback.format_exc(),
            },
        }


def call_tool(params: dict[str, Any]) -> dict[str, Any]:
    name = params.get("name")
    arguments = params.get("arguments") or {}
    spec = TOOLS.get(name)
    if not spec:
        raise McpError(-32602, f"Unknown tool: {name}")
    payload = spec["handler"](arguments)
    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, ensure_ascii=False, indent=2),
            }
        ],
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
    parser = argparse.ArgumentParser(description="Run the ScholarEcho Zotero MCP server.")
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Validate Zotero environment variables and print the resolved config.",
    )
    args = parser.parse_args()

    if args.check_config:
        config = load_config()
        print(
            json.dumps(
                {
                    "api_base": config.api_base,
                    "library_type": config.library_type,
                    "library_id": config.library_id,
                    "api_key_set": bool(config.api_key),
                    "storage_dir": str(config.storage_dir),
                    "storage_dir_exists": config.storage_dir.exists(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    serve()


if __name__ == "__main__":
    main()
