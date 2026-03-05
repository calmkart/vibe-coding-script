"""Full-text search across all conversation JSONL files."""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import List, Optional

from ..utils.format import project_name_from_dir, truncate_text


PROJECTS_DIR = os.path.expanduser("~/.claude/projects")


@dataclass
class SearchResult:
    session_id: str
    project_name: str
    project_dir: str
    jsonl_path: str
    role: str
    content_preview: str
    timestamp: str
    match_line: int


def search_conversations(
    query: str,
    project_filter: Optional[str] = None,
    max_results: int = 50,
) -> List[SearchResult]:
    """Search all JSONL files for a query string.

    Runs per-file searches in parallel using a thread pool.
    """
    if not query or not os.path.isdir(PROJECTS_DIR):
        return []

    query_lower = query.lower()
    results = []

    # Collect files to search
    search_targets = []
    for dirname in os.listdir(PROJECTS_DIR):
        if project_filter and project_filter.lower() not in dirname.lower():
            continue
        dirpath = os.path.join(PROJECTS_DIR, dirname)
        if not os.path.isdir(dirpath):
            continue
        project_name = project_name_from_dir(dirname)
        for fname in os.listdir(dirpath):
            if not fname.endswith(".jsonl"):
                continue
            fpath = os.path.join(dirpath, fname)
            search_targets.append((fpath, project_name, dirname))

    # Search files in parallel
    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = []
        for fpath, project_name, dirname in search_targets:
            futures.append(
                executor.submit(_search_file, fpath, query_lower, project_name, dirname, max_results)
            )

        for future in futures:
            try:
                file_results = future.result(timeout=10)
                results.extend(file_results)
                if len(results) >= max_results:
                    break
            except Exception:
                continue

    # Sort by timestamp descending
    results.sort(key=lambda r: r.timestamp, reverse=True)
    return results[:max_results]


def _search_file(
    jsonl_path: str,
    query_lower: str,
    project_name: str,
    project_dir: str,
    max_results: int,
) -> List[SearchResult]:
    """Search a single JSONL file for the query."""
    results = []
    session_id = os.path.basename(jsonl_path).replace(".jsonl", "")

    try:
        with open(jsonl_path, encoding="utf-8", errors="replace") as f:
            for line_num, line in enumerate(f, 1):
                if query_lower not in line.lower():
                    continue
                # This line contains the query; parse it
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = obj.get("message", {})
                role = msg.get("role", "")
                if role not in ("user", "assistant"):
                    continue

                content = msg.get("content", "")
                text = _extract_text(content)
                if query_lower not in text.lower():
                    continue

                # Find the context around the match
                preview = _extract_match_context(text, query_lower)

                results.append(SearchResult(
                    session_id=obj.get("sessionId", session_id),
                    project_name=project_name,
                    project_dir=project_dir,
                    jsonl_path=jsonl_path,
                    role=role,
                    content_preview=preview,
                    timestamp=obj.get("timestamp", ""),
                    match_line=line_num,
                ))

                if len(results) >= max_results:
                    break
    except OSError:
        pass

    return results


def _extract_text(content) -> str:
    """Extract plain text from message content (string or list of blocks)."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for block in content:
            if isinstance(block, dict):
                if block.get("type") == "text":
                    parts.append(block.get("text", ""))
                elif block.get("type") == "tool_use":
                    parts.append(f"[tool: {block.get('name', '')}]")
        return " ".join(parts)
    return str(content)


def _extract_match_context(text: str, query_lower: str, context_chars: int = 80) -> str:
    """Extract text around the first match occurrence."""
    idx = text.lower().find(query_lower)
    if idx == -1:
        return truncate_text(text, 160)

    start = max(0, idx - context_chars)
    end = min(len(text), idx + len(query_lower) + context_chars)

    preview = text[start:end]
    if start > 0:
        preview = "\u2026" + preview
    if end < len(text):
        preview = preview + "\u2026"
    return preview
