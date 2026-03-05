"""Live active session reader from /tmp/claude-sessions/*.json."""
from __future__ import annotations

import glob
import json
import os
import time
from dataclasses import dataclass
from typing import Dict, List, Optional


SESSION_DIR = "/tmp/claude-sessions"
STALE_THRESHOLD = 300  # seconds


@dataclass
class ActiveSession:
    tty: str
    pid: int
    status: str  # "working" | "attention" | "done"
    project: str
    branch: str
    worktree: str
    cwd: str
    timestamp: float
    # Usage data (populated by populate_active_usage)
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    estimated_cost: float = 0.0
    primary_model: str = ""
    message_count: int = 0

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp

    @property
    def is_alive(self) -> bool:
        """Check if the process is still running."""
        try:
            os.kill(self.pid, 0)
            return True
        except ProcessLookupError:
            return False
        except (PermissionError, ValueError, TypeError):
            return True  # Assume alive if we can't check

    @property
    def tty_short(self) -> str:
        return os.path.basename(self.tty)

    @property
    def status_icon(self) -> str:
        icons = {"working": "\u25c9", "attention": "\u23f8", "done": "\u2713"}
        return icons.get(self.status, "?")


def _is_pid_alive(pid: int) -> bool:
    """Check if a process is still running."""
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except (PermissionError, ValueError, TypeError):
        return True  # Assume alive if we can't check


def read_active_sessions() -> List[ActiveSession]:
    """Read all active session JSON files, prune dead ones.

    A session is kept as long as its process is alive, regardless of
    how old the timestamp is (idle sessions waiting for input can sit
    for hours).  Only sessions whose process has exited AND whose
    timestamp is older than STALE_THRESHOLD are cleaned up.
    """
    sessions = []
    now = time.time()

    if not os.path.isdir(SESSION_DIR):
        return sessions

    for path in glob.glob(os.path.join(SESSION_DIR, "*.json")):
        try:
            with open(path) as f:
                data = json.load(f)

            ts = data.get("timestamp", 0)
            pid = int(data.get("pid", 0))

            # If PID is alive, always keep the session
            if pid and _is_pid_alive(pid):
                sessions.append(ActiveSession(
                    tty=data.get("tty", ""),
                    pid=pid,
                    status=data.get("status", "unknown"),
                    project=data.get("project", "unknown"),
                    branch=data.get("branch", ""),
                    worktree=data.get("worktree", ""),
                    cwd=data.get("cwd", ""),
                    timestamp=ts,
                ))
                continue

            # PID is dead (or missing) — clean up stale files
            if now - ts > STALE_THRESHOLD:
                try:
                    os.unlink(path)
                except OSError:
                    pass

        except (json.JSONDecodeError, KeyError, OSError):
            continue

    # Populate usage data from matching JSONL files
    _populate_active_usage(sessions)

    # Sort: working first, then attention, then done
    priority = {"working": 0, "attention": 1, "done": 2}
    sessions.sort(key=lambda s: (priority.get(s.status, 3), -s.timestamp))
    return sessions


def _find_recent_jsonl(cwd: str, project: str) -> Optional[str]:
    """Find the most recently modified JSONL for an active session.

    Tries exact cwd encoding first, then walks up parent directories
    (since Claude Code may register the project root, not the subdirectory
    the user is working in).
    """
    projects_dir = os.path.expanduser("~/.claude/projects")
    if not os.path.isdir(projects_dir):
        return None

    # Try exact cwd, then each parent directory
    path = cwd
    while path and path != "/":
        encoded = path.replace("/", "-")
        dirpath = os.path.join(projects_dir, encoded)
        if os.path.isdir(dirpath):
            result = _best_jsonl_in_dir(dirpath)
            if result:
                return result
        path = os.path.dirname(path)

    return None


def _best_jsonl_in_dir(dirpath: str) -> Optional[str]:
    """Return the most recently modified JSONL file in a directory."""
    best_path = None
    best_mtime = 0.0
    for fname in os.listdir(dirpath):
        if fname.endswith(".jsonl"):
            fpath = os.path.join(dirpath, fname)
            try:
                mt = os.path.getmtime(fpath)
                if mt > best_mtime:
                    best_mtime = mt
                    best_path = fpath
            except OSError:
                continue
    return best_path


def _populate_active_usage(sessions: List[ActiveSession]) -> None:
    """Calculate usage/cost for active sessions from their JSONL files."""
    from .history import load_session_usage, SessionEntry

    for session in sessions:
        jsonl_path = _find_recent_jsonl(session.cwd, session.project)
        if not jsonl_path:
            continue

        # Create a temporary SessionEntry to reuse the existing usage loader
        tmp = SessionEntry(
            session_id="",
            project_name=session.project,
            project_path=session.cwd,
            project_dir="",
            jsonl_path=jsonl_path,
            first_prompt="",
            summary="",
            message_count=0,
            created="",
            modified="",
            git_branch=session.branch,
            is_sidechain=False,
            file_size=0,
        )
        load_session_usage(tmp)

        session.total_input_tokens = tmp.total_input_tokens
        session.total_output_tokens = tmp.total_output_tokens
        session.estimated_cost = tmp.estimated_cost
        session.primary_model = tmp.primary_model
        session.message_count = tmp.message_count or (
            tmp.total_input_tokens > 0 and 1 or 0
        )


def active_session_summary(sessions: List[ActiveSession]) -> Dict[str, int]:
    """Return status counts dict."""
    counts = {"working": 0, "attention": 0, "done": 0}
    for s in sessions:
        if s.status in counts:
            counts[s.status] += 1
    return counts
