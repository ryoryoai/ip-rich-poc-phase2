#!/usr/bin/env python3
"""
Migrate docs-site Markdown/MDX content into Notion using the Notion API.

Requirements:
  - NOTION_TOKEN env var set
  - Notion Integration shared to the target parent page

Usage:
  python tools/notion_migrate_docs.py --parent <page_id_or_url> [--root-title "docs-site import"] [--dry-run]
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple
from urllib import error, request


NOTION_VERSION = "2022-06-28"
API_BASE = "https://api.notion.com/v1"

DOCS_ROOT = Path("docs-site")
DEFAULT_ROOT_TITLE = f"docs-site import ({dt.date.today().isoformat()})"


def normalize_page_id(value: str) -> str:
    value = value.strip()
    # Extract 32-char hex or dashed UUID
    m = re.search(r"([0-9a-fA-F]{32})", value)
    if not m:
        m = re.search(
            r"([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})",
            value,
        )
    if not m:
        raise ValueError("Could not extract Notion page ID from input.")
    raw = m.group(1).replace("-", "").lower()
    # Insert dashes
    return f"{raw[0:8]}-{raw[8:12]}-{raw[12:16]}-{raw[16:20]}-{raw[20:32]}"


def notion_headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def notion_request(
    method: str,
    path: str,
    token: str,
    payload: Dict[str, Any] | None = None,
    retries: int = 5,
) -> Dict[str, Any]:
    url = f"{API_BASE}{path}"
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")

    for attempt in range(retries):
        req = request.Request(url, data=data, method=method, headers=notion_headers(token))
        try:
            with request.urlopen(req, timeout=60) as resp:
                body = resp.read().decode("utf-8")
                return json.loads(body)
        except error.HTTPError as e:
            body = e.read().decode("utf-8") if e.fp else ""
            if e.code in (429, 500, 502, 503, 504) and attempt < retries - 1:
                sleep_for = 0.5 * (2**attempt)
                time.sleep(sleep_for)
                continue
            raise RuntimeError(f"Notion API error {e.code}: {body}") from e
        except error.URLError as e:
            if attempt < retries - 1:
                time.sleep(0.5 * (2**attempt))
                continue
            raise RuntimeError(f"Notion API request failed: {e}") from e

    raise RuntimeError("Notion API request failed after retries.")


def create_page(token: str, parent_page_id: str, title: str) -> str:
    payload = {
        "parent": {"page_id": parent_page_id},
        "properties": {
            "title": {
                "title": [
                    {
                        "type": "text",
                        "text": {"content": title},
                    }
                ]
            }
        },
    }
    resp = notion_request("POST", "/pages", token, payload=payload)
    return resp["id"]


def append_blocks(token: str, page_id: str, blocks: List[Dict[str, Any]]) -> None:
    if not blocks:
        return
    # Notion limit: 100 blocks per request
    chunk_size = 100
    for i in range(0, len(blocks), chunk_size):
        chunk = blocks[i : i + chunk_size]
        payload = {"children": chunk}
        notion_request("PATCH", f"/blocks/{page_id}/children", token, payload=payload)
        time.sleep(0.35)


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text
    end_index = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end_index = i
            break
    if end_index is None:
        return {}, text
    fm_lines = lines[1:end_index]
    body = "\n".join(lines[end_index + 1 :])
    fm: Dict[str, str] = {}
    for line in fm_lines:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip()] = value.strip().strip('"').strip("'")
    return fm, body


def split_rich_text(content: str, link: str | None = None, code: bool = False) -> List[Dict[str, Any]]:
    if content == "":
        return []
    max_len = 2000
    chunks = [content[i : i + max_len] for i in range(0, len(content), max_len)]
    out = []
    for chunk in chunks:
        out.append(
            {
                "type": "text",
                "text": {
                    "content": chunk,
                    "link": {"url": link} if link else None,
                },
                "annotations": {
                    "bold": False,
                    "italic": False,
                    "strikethrough": False,
                    "underline": False,
                    "code": bool(code),
                    "color": "default",
                },
            }
        )
    return out


def parse_inline(text: str) -> List[Dict[str, Any]]:
    if not text:
        return []
    result: List[Dict[str, Any]] = []
    i = 0
    buffer = []

    def flush_buffer() -> None:
        nonlocal buffer
        if buffer:
            result.extend(split_rich_text("".join(buffer)))
            buffer = []

    def is_valid_link(url: str) -> bool:
        return url.startswith("http://") or url.startswith("https://") or url.startswith("mailto:") or url.startswith("tel:")

    while i < len(text):
        if text[i] == "`":
            end = text.find("`", i + 1)
            if end != -1:
                flush_buffer()
                code_text = text[i + 1 : end]
                result.extend(split_rich_text(code_text, code=True))
                i = end + 1
                continue
        if text[i] == "[":
            mid = text.find("](", i + 1)
            end = text.find(")", mid + 2) if mid != -1 else -1
            if mid != -1 and end != -1:
                label = text[i + 1 : mid]
                url = text[mid + 2 : end]
                if is_valid_link(url):
                    flush_buffer()
                    result.extend(split_rich_text(label, link=url))
                    i = end + 1
                    continue
                # Invalid/relative URL: treat as plain text
                buffer.append(text[i : end + 1])
                i = end + 1
                continue
        buffer.append(text[i])
        i += 1

    flush_buffer()
    return result


def block_paragraph(text: str) -> Dict[str, Any]:
    return {"type": "paragraph", "paragraph": {"rich_text": parse_inline(text)}}


def block_heading(level: int, text: str) -> Dict[str, Any]:
    level = min(max(level, 1), 3)
    key = f"heading_{level}"
    return {"type": key, key: {"rich_text": parse_inline(text)}}


def block_bulleted(text: str) -> Dict[str, Any]:
    return {"type": "bulleted_list_item", "bulleted_list_item": {"rich_text": parse_inline(text)}}


def block_numbered(text: str) -> Dict[str, Any]:
    return {"type": "numbered_list_item", "numbered_list_item": {"rich_text": parse_inline(text)}}


def block_quote(text: str) -> Dict[str, Any]:
    return {"type": "quote", "quote": {"rich_text": parse_inline(text)}}


def block_divider() -> Dict[str, Any]:
    return {"type": "divider", "divider": {}}


def block_code(code: str, language: str = "plain text") -> Dict[str, Any]:
    return {
        "type": "code",
        "code": {
            "language": language,
            "rich_text": split_rich_text(code),
        },
    }


NOTION_CODE_LANGUAGES = {
    "abap",
    "abc",
    "agda",
    "arduino",
    "ascii art",
    "assembly",
    "bash",
    "basic",
    "bnf",
    "c",
    "c#",
    "c++",
    "clojure",
    "coffeescript",
    "coq",
    "css",
    "dart",
    "dhall",
    "diff",
    "docker",
    "ebnf",
    "elixir",
    "elm",
    "erlang",
    "f#",
    "flow",
    "fortran",
    "gherkin",
    "glsl",
    "go",
    "graphql",
    "groovy",
    "haskell",
    "hcl",
    "html",
    "idris",
    "java",
    "javascript",
    "json",
    "julia",
    "kotlin",
    "latex",
    "less",
    "lisp",
    "livescript",
    "llvm ir",
    "lua",
    "makefile",
    "markdown",
    "markup",
    "matlab",
    "mathematica",
    "mermaid",
    "nix",
    "notion formula",
    "objective-c",
    "ocaml",
    "pascal",
    "perl",
    "php",
    "plain text",
    "powershell",
    "prolog",
    "protobuf",
    "purescript",
    "python",
    "r",
    "racket",
    "reason",
    "ruby",
    "rust",
    "sass",
    "scala",
    "scheme",
    "scss",
    "shell",
    "smalltalk",
    "solidity",
    "sql",
    "swift",
    "toml",
    "typescript",
    "vb.net",
    "verilog",
    "vhdl",
    "visual basic",
    "webassembly",
    "xml",
    "yaml",
    "java/c/c++/c#",
}


def normalize_code_language(raw: str) -> str:
    if not raw:
        return "plain text"
    token = raw.strip().lower()
    # If language has extra words (e.g., "plantuml Phase 2"), keep first token
    token = token.split()[0]
    aliases = {
        "sh": "shell",
        "shellscript": "shell",
        "zsh": "shell",
        "bash": "bash",
        "ts": "typescript",
        "tsx": "typescript",
        "js": "javascript",
        "jsx": "javascript",
        "yml": "yaml",
        "md": "markdown",
        "mdx": "markdown",
        "plaintext": "plain text",
        "text": "plain text",
        "plantuml": "plain text",
        "puml": "plain text",
        "mermaid": "mermaid",
    }
    token = aliases.get(token, token)
    return token if token in NOTION_CODE_LANGUAGES else "plain text"


def detect_table(lines: List[str], idx: int) -> Tuple[bool, int]:
    if idx + 1 >= len(lines):
        return False, idx
    line = lines[idx]
    sep = lines[idx + 1]
    if "|" not in line:
        return False, idx
    if not re.match(r"^\s*\|?[\s:-]+\|?[\s|:-]*$", sep):
        return False, idx
    # find end of table
    end = idx + 2
    while end < len(lines) and "|" in lines[end]:
        end += 1
    return True, end


def parse_markdown_to_blocks(text: str) -> List[Dict[str, Any]]:
    lines = text.splitlines()
    blocks: List[Dict[str, Any]] = []
    paragraph_buf: List[str] = []
    in_code = False
    code_lang = "plain text"
    code_buf: List[str] = []

    def flush_paragraph() -> None:
        nonlocal paragraph_buf
        if paragraph_buf:
            paragraph = " ".join(s.strip() for s in paragraph_buf).strip()
            if paragraph:
                blocks.append(block_paragraph(paragraph))
            paragraph_buf = []

    def flush_code() -> None:
        nonlocal code_buf
        if code_buf:
            blocks.append(block_code("\n".join(code_buf), code_lang))
            code_buf = []

    i = 0
    while i < len(lines):
        line = lines[i]

        if in_code:
            if line.strip().startswith("```"):
                in_code = False
                flush_code()
                i += 1
                continue
            code_buf.append(line)
            i += 1
            continue

        if line.strip().startswith("```"):
            flush_paragraph()
            in_code = True
            lang = line.strip().lstrip("```").strip()
            code_lang = normalize_code_language(lang)
            i += 1
            continue

        is_table, table_end = detect_table(lines, i)
        if is_table:
            flush_paragraph()
            table_text = "\n".join(lines[i:table_end])
            blocks.append(block_code(table_text, "plain text"))
            i = table_end
            continue

        if line.strip() == "":
            flush_paragraph()
            i += 1
            continue

        if re.match(r"^\s*[-*_]{3,}\s*$", line):
            flush_paragraph()
            blocks.append(block_divider())
            i += 1
            continue

        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush_paragraph()
            level = len(m.group(1))
            text = m.group(2).strip()
            blocks.append(block_heading(level, text))
            i += 1
            continue

        if line.lstrip().startswith("> "):
            flush_paragraph()
            quote_text = line.lstrip()[2:].strip()
            blocks.append(block_quote(quote_text))
            i += 1
            continue

        m = re.match(r"^\s*([-*+])\s+(.*)$", line)
        if m:
            flush_paragraph()
            blocks.append(block_bulleted(m.group(2).strip()))
            i += 1
            continue

        m = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if m:
            flush_paragraph()
            blocks.append(block_numbered(m.group(2).strip()))
            i += 1
            continue

        paragraph_buf.append(line)
        i += 1

    flush_paragraph()
    if in_code:
        flush_code()
    return blocks


def collect_files() -> List[Path]:
    roots = []
    docs = DOCS_ROOT / "docs"
    if docs.exists():
        roots.append(docs)
    versioned = DOCS_ROOT / "versioned_docs"
    if versioned.exists():
        roots.append(versioned)
    src_pages = DOCS_ROOT / "src" / "pages"
    if src_pages.exists():
        roots.append(src_pages)

    files: List[Path] = []
    for root in roots:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in (".md", ".mdx"):
                files.append(path)
    return sorted(files)


def ensure_dir_pages(
    token: str,
    root_page_id: str,
    files: Iterable[Path],
    base_dir: Path,
    dry_run: bool,
) -> Dict[str, str]:
    dir_pages: Dict[str, str] = {"": root_page_id}
    dirs = set()
    for f in files:
        rel = f.relative_to(base_dir)
        dir_path = str(rel.parent).replace("\\", "/")
        if dir_path != ".":
            dirs.add(dir_path)
    # Sort by depth
    for dir_path in sorted(dirs, key=lambda p: p.count("/")):
        parent_path = "/".join(dir_path.split("/")[:-1])
        parent_id = dir_pages.get(parent_path, root_page_id)
        title = Path(dir_path).name
        if dry_run:
            dir_pages[dir_path] = f"dry-run:{dir_path}"
            continue
        page_id = create_page(token, parent_id, title)
        dir_pages[dir_path] = page_id
        time.sleep(0.35)
    return dir_pages


def migrate(
    token: str,
    parent_page_id: str,
    root_title: str,
    dry_run: bool = False,
) -> None:
    if not DOCS_ROOT.exists():
        raise RuntimeError("docs-site directory not found.")

    files = collect_files()
    if not files:
        print("No Markdown/MDX files found.")
        return

    if dry_run:
        root_page_id = "dry-run:root"
    else:
        root_page_id = create_page(token, parent_page_id, root_title)
        time.sleep(0.35)

    dir_pages = ensure_dir_pages(token, root_page_id, files, DOCS_ROOT, dry_run)

    created = []
    for f in files:
        rel = f.relative_to(DOCS_ROOT).as_posix()
        fm, body = parse_frontmatter(f.read_text(encoding="utf-8"))
        title = fm.get("title") or fm.get("sidebar_label") or f.stem

        dir_path = str(f.relative_to(DOCS_ROOT).parent).replace("\\", "/")
        parent_id = dir_pages.get(dir_path if dir_path != "." else "", root_page_id)

        if dry_run:
            created.append({"file": rel, "title": title, "page_id": None})
            continue

        page_id = create_page(token, parent_id, title)
        time.sleep(0.35)

        blocks = []
        blocks.append(block_paragraph(f"Source: {rel}"))
        content_blocks = parse_markdown_to_blocks(body)
        blocks.extend(content_blocks)
        append_blocks(token, page_id, blocks)

        created.append({"file": rel, "title": title, "page_id": page_id})
        time.sleep(0.35)

    out_path = Path("tools") / "notion_migrate_docs_report.json"
    out_path.write_text(json.dumps(created, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Done. Report written to {out_path}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--parent", required=True, help="Notion parent page ID or URL")
    parser.add_argument("--root-title", default=DEFAULT_ROOT_TITLE, help="Root page title")
    parser.add_argument("--dry-run", action="store_true", help="No API calls; print plan only")
    args = parser.parse_args()

    token = os.getenv("NOTION_TOKEN", "")
    if not token:
        print("NOTION_TOKEN env var is not set.", file=sys.stderr)
        return 1

    parent_id = normalize_page_id(args.parent)

    migrate(
        token=token,
        parent_page_id=parent_id,
        root_title=args.root_title,
        dry_run=args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
