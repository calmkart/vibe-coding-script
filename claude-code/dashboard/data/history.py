"""Session history reader from ~/.claude/projects/ directories."""
from __future__ import annotations

import json
import os
import re
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


PROJECTS_DIR = os.path.expanduser("~/.claude/projects")


@dataclass
class SessionEntry:
    session_id: str
    project_name: str
    project_path: str
    project_dir: str  # encoded directory name
    jsonl_path: str
    first_prompt: str
    summary: str
    message_count: int
    created: str
    modified: str
    git_branch: str
    is_sidechain: bool
    file_size: int
    # Per-session usage (populated by load_session_usage)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cache_read: int = 0
    total_cache_create: int = 0
    primary_model: str = ""
    estimated_cost: float = 0.0

    @property
    def short_prompt(self) -> str:
        text = re.sub(r'<[^>]+>', '', self.first_prompt).strip()
        if len(text) > 100:
            return text[:99] + "\u2026"
        return text


@dataclass
class ProjectInfo:
    name: str
    path: str
    dir_name: str
    session_count: int
    last_modified: str
    sessions: List[SessionEntry] = field(default_factory=list)


def _resolve_project_path(dirpath: str, dirname: str) -> str:
    """Resolve the real project path from available sources.

    Priority: sessions-index.json originalPath > JSONL cwd > dirname decode
    """
    if not os.path.isdir(dirpath):
        # Directory does not exist; fall back to decoding the dirname
        if dirname.startswith("-"):
            return "/" + dirname[1:].replace("-", "/")
        return dirname

    # 1. Try sessions-index.json
    index_path = os.path.join(dirpath, "sessions-index.json")
    if os.path.exists(index_path):
        try:
            with open(index_path) as f:
                idx = json.load(f)
            if idx.get("originalPath"):
                return idx["originalPath"]
        except (json.JSONDecodeError, OSError):
            pass

    # 2. Try reading cwd from first JSONL file (check first 10 lines)
    for fname in os.listdir(dirpath):
        if fname.endswith(".jsonl"):
            fpath = os.path.join(dirpath, fname)
            try:
                with open(fpath) as f:
                    for i, line in enumerate(f):
                        if i > 10:
                            break
                        try:
                            obj = json.loads(line.strip())
                            if obj.get("cwd"):
                                return obj["cwd"]
                        except json.JSONDecodeError:
                            continue
            except OSError:
                pass
            break  # Only try first JSONL file

    # 3. Fallback: decode dirname (imperfect due to hyphen ambiguity)
    if dirname.startswith("-"):
        return "/" + dirname[1:].replace("-", "/")
    return dirname


def discover_all_projects() -> List[ProjectInfo]:
    """Scan ~/.claude/projects/ and return project info list."""
    if not os.path.isdir(PROJECTS_DIR):
        return []

    projects = []
    for dirname in os.listdir(PROJECTS_DIR):
        dirpath = os.path.join(PROJECTS_DIR, dirname)
        if not os.path.isdir(dirpath):
            continue

        # Resolve original path from best available source
        original_path = _resolve_project_path(dirpath, dirname)

        # Project name = last meaningful path component
        project_name = os.path.basename(original_path.rstrip("/"))
        if not project_name or project_name in (".", ""):
            project_name = dirname

        sessions = load_project_sessions(dirname, original_path, project_name)
        if not sessions:
            continue

        last_mod = max(s.modified for s in sessions) if sessions else ""

        projects.append(ProjectInfo(
            name=project_name,
            path=original_path,
            dir_name=dirname,
            session_count=len(sessions),
            last_modified=last_mod,
            sessions=sessions,
        ))

    # Sort by last modified (most recent first)
    projects.sort(key=lambda p: p.last_modified, reverse=True)
    return projects


def load_project_sessions(
    project_dirname: str,
    original_path: Optional[str] = None,
    project_name: Optional[str] = None,
) -> List[SessionEntry]:
    """Load sessions for one project.

    Always scans JSONL files on disk to ensure no sessions are missed.
    Uses sessions-index.json as a metadata supplement (for summary,
    firstPrompt, etc.) but never as the sole source of truth.
    """
    dirpath = os.path.join(PROJECTS_DIR, project_dirname)
    index_path = os.path.join(dirpath, "sessions-index.json")

    if not original_path:
        original_path = _resolve_project_path(dirpath, project_dirname)
    if not project_name:
        project_name = os.path.basename(original_path.rstrip("/")) or project_dirname

    # 1. Always scan JSONL files on disk (ground truth)
    sessions = _load_from_jsonl_scan(dirpath, project_name, original_path, project_dirname)

    # 2. Enrich with index metadata where available
    if os.path.exists(index_path):
        _enrich_from_index(sessions, index_path)

    # Sort by modified date descending
    sessions.sort(key=lambda s: s.modified, reverse=True)
    # Load per-session token usage in parallel
    _populate_usage_for_sessions(sessions)
    return sessions


def _load_from_index(
    index_path: str,
    project_name: str,
    project_path: str,
    project_dirname: str,
) -> List[SessionEntry]:
    """Load sessions from sessions-index.json."""
    try:
        with open(index_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return []

    sessions = []
    for entry in data.get("entries", []):
        jsonl_path = entry.get("fullPath", "")
        try:
            file_size = os.path.getsize(jsonl_path) if os.path.exists(jsonl_path) else 0
        except OSError:
            file_size = 0

        sessions.append(SessionEntry(
            session_id=entry.get("sessionId", ""),
            project_name=project_name,
            project_path=entry.get("projectPath", project_path),
            project_dir=project_dirname,
            jsonl_path=jsonl_path,
            first_prompt=entry.get("firstPrompt", ""),
            summary=entry.get("summary", ""),
            message_count=entry.get("messageCount", 0),
            created=entry.get("created", ""),
            modified=entry.get("modified", ""),
            git_branch=entry.get("gitBranch", ""),
            is_sidechain=entry.get("isSidechain", False),
            file_size=file_size,
        ))
    return sessions


def _enrich_from_index(
    sessions: List[SessionEntry],
    index_path: str,
) -> None:
    """Enrich scanned sessions with richer metadata from sessions-index.json.

    The index may contain summary, firstPrompt, messageCount, gitBranch, etc.
    that aren't easily extracted from a quick JSONL scan.
    """
    try:
        with open(index_path) as f:
            data = json.load(f)
    except (json.JSONDecodeError, OSError):
        return

    # Build lookup: sessionId -> index entry
    index_map: Dict[str, Dict] = {}
    for entry in data.get("entries", []):
        sid = entry.get("sessionId", "")
        if sid:
            index_map[sid] = entry

    for session in sessions:
        entry = index_map.get(session.session_id)
        if not entry:
            continue
        # Supplement fields if the scanned version is empty/weak
        if entry.get("summary") and not session.summary:
            session.summary = entry["summary"]
        if entry.get("firstPrompt") and not session.first_prompt:
            session.first_prompt = entry["firstPrompt"]
        if entry.get("gitBranch") and not session.git_branch:
            session.git_branch = entry["gitBranch"]
        if entry.get("messageCount", 0) > session.message_count:
            session.message_count = entry["messageCount"]


def _load_from_jsonl_scan(
    dirpath: str,
    project_name: str,
    project_path: str,
    project_dirname: str,
) -> List[SessionEntry]:
    """Fallback: scan JSONL files to extract session metadata."""
    sessions = []
    if not os.path.isdir(dirpath):
        return sessions
    for fname in os.listdir(dirpath):
        if not fname.endswith(".jsonl"):
            continue
        fpath = os.path.join(dirpath, fname)
        session_id = fname.replace(".jsonl", "")

        try:
            file_size = os.path.getsize(fpath)
            file_mtime = os.path.getmtime(fpath)
        except OSError:
            continue

        # Read first few lines to get metadata
        first_prompt = ""
        git_branch = ""
        created = ""
        session_id_from_file = ""
        msg_count = 0

        try:
            with open(fpath) as f:
                for i, line in enumerate(f):
                    if i > 50:  # Only check first 50 lines
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if not created and obj.get("timestamp"):
                        created = obj["timestamp"]
                    if not session_id_from_file and obj.get("sessionId"):
                        session_id_from_file = obj["sessionId"]
                    if not git_branch and obj.get("gitBranch"):
                        git_branch = obj["gitBranch"]

                    msg = obj.get("message", {})
                    msg_role = msg.get("role", "")
                    if msg_role in ("user", "assistant"):
                        msg_count += 1
                    if not first_prompt and msg_role == "user":
                        content = msg.get("content", "")
                        if isinstance(content, str):
                            first_prompt = content[:200]
                        elif isinstance(content, list):
                            for block in content:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    first_prompt = block.get("text", "")[:200]
                                    break
        except OSError:
            continue

        # Estimate total message count from file size if we only read 50 lines
        if msg_count > 0 and file_size > 50000:
            # Rough estimate based on average line length
            msg_count = max(msg_count, file_size // 2000)

        from datetime import datetime
        modified_iso = datetime.fromtimestamp(file_mtime).isoformat()

        sessions.append(SessionEntry(
            session_id=session_id_from_file or session_id,
            project_name=project_name,
            project_path=project_path,
            project_dir=project_dirname,
            jsonl_path=fpath,
            first_prompt=first_prompt,
            summary="",
            message_count=msg_count,
            created=created,
            modified=modified_iso,
            git_branch=git_branch,
            is_sidechain=False,
            file_size=file_size,
        ))
    return sessions


def load_conversation(jsonl_path: str, max_messages: int = 500) -> List[Dict[str, Any]]:
    """Load conversation messages from a JSONL file.

    Only returns user and assistant messages (skips progress, meta, etc.).
    Uses fast pre-filtering to avoid parsing every line.
    """
    messages = []
    if max_messages <= 0:
        return messages
    if not os.path.exists(jsonl_path):
        return messages

    try:
        with open(jsonl_path, encoding='utf-8', errors='replace') as f:
            for line in f:
                # Fast pre-filter: skip lines that definitely don't have message roles.
                # The "role" field is nested in "message" so it can appear anywhere in the line.
                # We check for "role" anywhere since lines without it are meta/progress.
                if '"role"' not in line:
                    continue

                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = obj.get("message", {})
                role = msg.get("role", "")
                if role not in ("user", "assistant"):
                    continue

                content = msg.get("content", "")
                timestamp = obj.get("timestamp", "")

                # For assistant messages, content is usually a list of blocks
                parsed_content = content
                if isinstance(content, list):
                    parsed_content = content  # Keep as-is for rich rendering
                elif isinstance(content, str):
                    parsed_content = content

                messages.append({
                    "role": role,
                    "content": parsed_content,
                    "timestamp": timestamp,
                    "uuid": obj.get("uuid", ""),
                })

                if len(messages) >= max_messages:
                    break
    except OSError:
        pass

    return messages


def load_session_usage(session: SessionEntry) -> None:
    """Scan a JSONL file and populate the session's token/cost fields.

    Only processes final assistant messages (stop_reason != null) to avoid
    double-counting streaming partial messages.
    """
    if not os.path.exists(session.jsonl_path):
        return

    input_tok = 0
    output_tok = 0
    cache_read = 0
    cache_create = 0
    model_counts: Dict[str, int] = {}  # model -> output_tokens (to find primary)

    try:
        with open(session.jsonl_path, encoding='utf-8', errors='replace') as f:
            for line in f:
                # Fast pre-filter: only parse lines that look like final assistant msgs
                if '"stop_reason"' not in line or '"null"' in line:
                    if '"stop_reason":null' in line or '"stop_reason": null' in line:
                        continue
                    if '"stop_reason"' not in line:
                        continue

                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg = obj.get("message", {})
                if msg.get("role") != "assistant":
                    continue
                stop = msg.get("stop_reason")
                if stop is None:
                    continue

                usage = msg.get("usage", {})
                if not usage:
                    continue

                inp = usage.get("input_tokens", 0)
                out = usage.get("output_tokens", 0)
                cr = usage.get("cache_read_input_tokens", 0)
                cc = usage.get("cache_creation_input_tokens", 0)

                input_tok += inp
                output_tok += out
                cache_read += cr
                cache_create += cc

                model = msg.get("model", "")
                if model:
                    model_counts[model] = model_counts.get(model, 0) + out
    except OSError:
        return

    session.total_input_tokens = input_tok
    session.total_output_tokens = output_tok
    session.total_cache_read = cache_read
    session.total_cache_create = cache_create

    if model_counts:
        session.primary_model = max(model_counts, key=model_counts.get)

    # Calculate cost
    from ..utils.pricing import calculate_cost
    session.estimated_cost = calculate_cost(
        model=session.primary_model or "claude-opus-4-6",
        input_tokens=input_tok,
        output_tokens=output_tok,
        cache_read_tokens=cache_read,
        cache_creation_tokens=cache_create,
    )


def _populate_usage_for_sessions(sessions: List[SessionEntry]) -> None:
    """Load usage data for all sessions (parallel)."""
    with ThreadPoolExecutor(max_workers=4) as pool:
        pool.map(load_session_usage, sessions)


def delete_session(session: SessionEntry) -> bool:
    """Delete a session's JSONL file and remove from index."""
    try:
        if os.path.exists(session.jsonl_path):
            os.unlink(session.jsonl_path)

        # Update sessions-index.json if it exists
        dirpath = os.path.join(PROJECTS_DIR, session.project_dir)
        index_path = os.path.join(dirpath, "sessions-index.json")
        if os.path.exists(index_path):
            with open(index_path) as f:
                index = json.load(f)
            index["entries"] = [
                e for e in index.get("entries", [])
                if e.get("sessionId") != session.session_id
            ]
            with open(index_path, "w") as f:
                json.dump(index, f, indent=2)
        return True
    except OSError:
        return False
