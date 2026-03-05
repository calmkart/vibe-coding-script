"""Shared formatting utilities for the dashboard."""
from __future__ import annotations

import os
import time
from datetime import datetime
from typing import Optional


def format_age(ts: float) -> str:
    """Format a unix timestamp as human-readable age like '2s ago', '5m ago'."""
    delta = int(time.time() - ts)
    if delta < 0:
        return "now"
    elif delta < 60:
        return f"{delta}s ago"
    elif delta < 3600:
        return f"{delta // 60}m ago"
    elif delta < 86400:
        return f"{delta // 3600}h ago"
    else:
        return f"{delta // 86400}d ago"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds // 60)}m {int(seconds % 60)}s"
    elif seconds < 86400:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        return f"{h}h {m}m"
    else:
        d = int(seconds // 86400)
        h = int((seconds % 86400) // 3600)
        return f"{d}d {h}h"


def shorten_path(path: str, max_len: int = 50) -> str:
    """Shorten a path with ~ for home and ellipsis if too long."""
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]
    if len(path) > max_len:
        path = "\u2026" + path[-(max_len - 1):]
    return path


def project_name_from_dir(dirname: str) -> str:
    """Extract human-readable project name from Claude's encoded directory name.

    e.g. '-Users-calmp-Desktop-code-lepton' -> 'lepton'
    """
    parts = dirname.strip("-").split("-")
    if parts:
        return parts[-1]
    return dirname


def format_tokens(count: int) -> str:
    """Format token count with appropriate unit suffix."""
    if count >= 1_000_000_000:
        return f"{count / 1_000_000_000:.1f}B"
    elif count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    elif count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


def format_filesize(size_bytes: int) -> str:
    """Format file size in human-readable units."""
    if size_bytes >= 1_073_741_824:
        return f"{size_bytes / 1_073_741_824:.1f} GB"
    elif size_bytes >= 1_048_576:
        return f"{size_bytes / 1_048_576:.1f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes} B"


def format_date(iso_str: str) -> str:
    """Format ISO date string to short date."""
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M")
    except (ValueError, AttributeError):
        return iso_str[:16] if iso_str else "?"


def format_cost(usd: float) -> str:
    """Format USD cost with appropriate precision."""
    if usd >= 100:
        return f"${usd:,.0f}"
    elif usd >= 1:
        return f"${usd:.2f}"
    elif usd >= 0.01:
        return f"${usd:.3f}"
    else:
        return f"${usd:.4f}"


def truncate_text(text: str, max_len: int = 100) -> str:
    """Truncate text with ellipsis."""
    if not text:
        return ""
    # Strip XML tags that may appear in prompts
    import re
    text = re.sub(r'<[^>]+>', '', text).strip()
    if len(text) > max_len:
        return text[:max_len - 1] + "\u2026"
    return text


def decode_project_path(dirname: str) -> str:
    """Decode Claude's encoded project directory name back to a path.

    e.g. '-Users-calmp-Desktop-code-lepton' -> '/Users/calmp/Desktop/code/lepton'
    """
    if dirname.startswith("-"):
        return "/" + dirname[1:].replace("-", "/")
    return dirname
