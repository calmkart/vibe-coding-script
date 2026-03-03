#!/usr/bin/env python3
"""
Claude Code Session Dashboard for iTerm2
AutoLaunch daemon — per-session badges with project/branch labels,
and a status bar dashboard for managing multiple Claude Code sessions.

Reads session metadata from /tmp/claude-sessions/*.json (written by iterm-status.sh hook).
Matches sessions to iTerm2 tabs by TTY, sets compact labeled badges, and provides
a rich dashboard popover via status bar component.

Install: place in ~/Library/Application Support/iTerm2/Scripts/AutoLaunch/
Requires: pip3 install iterm2
"""

import asyncio
import glob
import hashlib
import json
import os
import time

import iterm2

# --- Config ---
SESSION_DIR = "/tmp/claude-sessions"
SCAN_INTERVAL = 2       # seconds between polls
STALE_THRESHOLD = 300   # seconds — remove files older than this

# Badge sizing (fraction of terminal area, 0.0–1.0)
# Default iTerm2 is 0.5×0.5 which is too large; keep it subtle
BADGE_MAX_WIDTH = 0.15
BADGE_MAX_HEIGHT = 0.1


# --- Color Utilities ---

def project_color(name):
    """Hash project name to a stable HSL color, return as iterm2.Color."""
    h = int(hashlib.md5(name.encode()).hexdigest()[:8], 16) % 360
    s, l = 0.6, 0.45
    c = (1 - abs(2 * l - 1)) * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = l - c / 2
    if h < 60:      r, g, b = c, x, 0
    elif h < 120:   r, g, b = x, c, 0
    elif h < 180:   r, g, b = 0, c, x
    elif h < 240:   r, g, b = 0, x, c
    elif h < 300:   r, g, b = x, 0, c
    else:           r, g, b = c, 0, x
    return iterm2.Color(int((r + m) * 255), int((g + m) * 255), int((b + m) * 255), 180)


STATUS_BADGE_COLORS = {
    "working":   (50, 145, 80),
    "attention":  (200, 150, 50),
    "done":      (65, 105, 200),
}


def badge_color_for_status(status):
    r, g, b = STATUS_BADGE_COLORS.get(status, (128, 128, 128))
    return iterm2.Color(r, g, b, 160)


# --- Session File I/O ---

def read_sessions():
    """Read all session JSON files. Returns dict keyed by TTY path."""
    sessions = {}
    now = time.time()
    for path in glob.glob(os.path.join(SESSION_DIR, "*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            # Prune stale
            if now - data.get("timestamp", 0) > STALE_THRESHOLD:
                os.unlink(path)
                continue
            # Check PID alive (macOS has no /proc)
            pid = data.get("pid")
            if pid:
                try:
                    os.kill(int(pid), 0)
                except ProcessLookupError:
                    os.unlink(path)
                    continue
                except (PermissionError, ValueError, TypeError):
                    pass
            sessions[data.get("tty", "")] = data
        except (json.JSONDecodeError, KeyError, OSError):
            continue
    return sessions


def format_age(ts):
    """Format timestamp as human-readable age like '2s', '1m', '5m'."""
    delta = int(time.time() - ts)
    if delta < 0:
        return "now"
    elif delta < 60:
        return f"{delta}s ago"
    elif delta < 3600:
        return f"{delta // 60}m ago"
    else:
        return f"{delta // 3600}h ago"


def shorten_path(path, max_len=50):
    """Shorten a path with ~ for home and ellipsis if too long."""
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]
    if len(path) > max_len:
        path = "\u2026" + path[-(max_len - 1):]
    return path


def session_summary(sessions):
    """Return status bar string like '🤖 3 | ◉2 ⏸1 ✓1'."""
    if not sessions:
        return "No Claude sessions"
    counts = {"attention": 0, "working": 0, "done": 0}
    for s in sessions.values():
        st = s.get("status", "")
        if st in counts:
            counts[st] += 1
    parts = []
    if counts["working"]:
        parts.append(f"\u25c9{counts['working']}")
    if counts["attention"]:
        parts.append(f"\u23f8{counts['attention']}")
    if counts["done"]:
        parts.append(f"\u2713{counts['done']}")
    total = sum(counts.values())
    summary = " ".join(parts) if parts else "\u2014"
    return f"\U0001f916 {total} | {summary}"


# --- Dashboard HTML ---

def dashboard_html(sessions):
    """Build rich dark-mode dashboard HTML for the popover."""
    if not sessions:
        return (
            '<html><body style="font-family:-apple-system,sans-serif;padding:32px 24px;'
            'background:#1a1a2e;color:#888;text-align:center">'
            '<p style="font-size:40px;margin:0 0 12px 0">\U0001f916</p>'
            '<p style="font-size:14px;color:#aaa;margin:0 0 6px 0">No active sessions</p>'
            '<p style="font-size:12px;color:#555">Start Claude Code in a terminal to see sessions here</p>'
            '</body></html>'
        )

    # Count by status
    counts = {"working": 0, "attention": 0, "done": 0}
    for s in sessions.values():
        st = s.get("status", "")
        if st in counts:
            counts[st] += 1
    total = sum(counts.values())

    # Stats pills
    stats_parts = []
    if counts["working"]:
        stats_parts.append(
            f'<span style="background:#1b3a2a;color:#4ade80;padding:2px 8px;border-radius:10px;font-size:11px">'
            f'\u25c9 {counts["working"]} working</span>'
        )
    if counts["attention"]:
        stats_parts.append(
            f'<span style="background:#3a2e1b;color:#fbbf24;padding:2px 8px;border-radius:10px;font-size:11px">'
            f'\u23f8 {counts["attention"]} attention</span>'
        )
    if counts["done"]:
        stats_parts.append(
            f'<span style="background:#1b2640;color:#60a5fa;padding:2px 8px;border-radius:10px;font-size:11px">'
            f'\u2713 {counts["done"]} done</span>'
        )
    stats_html = " ".join(stats_parts)

    # Session cards
    icon_map = {"working": "\u25c9", "attention": "\u23f8", "done": "\u2713"}
    color_map = {"working": "#4ade80", "attention": "#fbbf24", "done": "#60a5fa"}
    border_map = {"working": "#22c55e", "attention": "#f59e0b", "done": "#3b82f6"}
    bg_map = {"working": "#0f2418", "attention": "#1f1a0f", "done": "#0f1724"}

    cards = []
    for s in sorted(sessions.values(), key=lambda x: (
        {"working": 0, "attention": 1, "done": 2}.get(x.get("status", ""), 3),
        x.get("project", ""),
    )):
        status = s.get("status", "")
        icon = icon_map.get(status, "?")
        color = color_map.get(status, "#888")
        border = border_map.get(status, "#444")
        bg = bg_map.get(status, "#1e1e1e")
        project = s.get("project", "?")
        branch = s.get("worktree") or s.get("branch") or ""
        cwd = s.get("cwd", "")
        tty = os.path.basename(s.get("tty", ""))
        ts = s.get("timestamp", 0)
        age = format_age(ts) if ts else "?"
        short_cwd = shorten_path(cwd) if cwd else ""

        worktree_badge = ""
        if s.get("worktree"):
            worktree_badge = (
                ' <span style="background:#2a2040;color:#a78bfa;font-size:9px;'
                'padding:1px 5px;border-radius:3px;margin-left:4px;vertical-align:middle'
                '">worktree</span>'
            )

        meta_items = []
        if branch:
            meta_items.append(f'<span style="color:#aaa">\U0001f33f {branch}{worktree_badge}</span>')
        if short_cwd:
            meta_items.append(f'<span style="color:#666">\U0001f4c2 {short_cwd}</span>')
        meta_html = '<span style="margin:0 6px;color:#333">\u2502</span>'.join(meta_items)

        cards.append(
            f'<div style="background:{bg};border-radius:8px;padding:10px 12px;margin-bottom:6px;'
            f'border-left:3px solid {border}">'
            # Row 1: project name + tty/age
            f'<div style="display:flex;align-items:center;justify-content:space-between">'
            f'<span style="font-size:13px;font-weight:600;color:#fff">'
            f'<span style="color:{color}">{icon}</span> {project}</span>'
            f'<span style="font-size:10px;color:#555">{tty} \u00b7 {age}</span>'
            f'</div>'
            # Row 2: branch + cwd
            f'<div style="margin-top:5px;font-size:11px;line-height:1.4">{meta_html}</div>'
            f'</div>'
        )

    return (
        '<html><head><style>'
        '*{box-sizing:border-box}'
        'body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;margin:0;padding:0;'
        'background:#1a1a2e;color:#e0e0e0}'
        '::-webkit-scrollbar{width:6px}'
        '::-webkit-scrollbar-track{background:#1a1a2e}'
        '::-webkit-scrollbar-thumb{background:#333;border-radius:3px}'
        '</style></head><body>'
        # Header
        '<div style="background:linear-gradient(135deg,#16213e,#1a1a2e);'
        'padding:14px 16px;border-bottom:1px solid #2a2a4a">'
        '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">'
        '<span style="font-size:14px;font-weight:600;color:#fff">'
        '\U0001f916 Claude Code Dashboard</span>'
        f'<span style="font-size:11px;color:#666">{total} session{"s" if total != 1 else ""}</span>'
        '</div>'
        f'<div style="display:flex;gap:6px;flex-wrap:wrap">{stats_html}</div>'
        '</div>'
        # Cards
        f'<div style="padding:8px 10px;overflow-y:auto;max-height:320px">{"".join(cards)}</div>'
        '</body></html>'
    )


# --- Main Daemon ---

async def main(connection):
    app = await iterm2.async_get_app(connection)
    applied_state = {}  # session_id -> {project, status, branch}

    # --- Register Status Bar Component ---
    component = iterm2.StatusBarComponent(
        short_description="Claude Sessions",
        detailed_description="Dashboard for all active Claude Code sessions",
        knobs=[],
        exemplar="\U0001f916 3 | \u25c92 \u23f81",
        update_cadence=SCAN_INTERVAL,
        identifier="com.calmp.claude-session-monitor",
    )

    @iterm2.StatusBarRPC
    async def statusbar_coro(knobs):
        return session_summary(read_sessions())

    @iterm2.RPC
    async def onclick(session_id):
        html = dashboard_html(read_sessions())
        await component.async_open_popover(
            session_id, html, iterm2.util.Size(520, 400)
        )

    await component.async_register(connection, statusbar_coro, onclick=onclick)

    # --- Polling Loop ---
    while True:
        await asyncio.sleep(SCAN_INTERVAL)
        try:
            app = await iterm2.async_get_app(connection)
            sessions_data = read_sessions()
            if not sessions_data:
                continue

            # Build TTY -> iTerm2 Session map
            tty_map = {}
            for window in app.terminal_windows:
                for tab in window.tabs:
                    for session in tab.sessions:
                        try:
                            tty = await session.async_get_variable("tty")
                            if tty:
                                tty_map[tty] = session
                        except Exception:
                            continue

            # Apply badges to matched sessions
            for tty, data in sessions_data.items():
                session = tty_map.get(tty)
                if not session:
                    continue

                project = data.get("project", "unknown")
                status = data.get("status", "")
                branch = data.get("branch", "")
                worktree = data.get("worktree", "")
                sid = session.session_id

                current = {"project": project, "status": status, "branch": branch}
                if applied_state.get(sid) == current:
                    continue
                applied_state[sid] = current

                # Badge text: compact labeled format
                # 📂 project-name
                # 🌿 branch-name
                lines = [f"\U0001f4c2 {project}"]
                if worktree:
                    lines.append(f"\U0001f33f {worktree} \u2934")
                elif branch:
                    lines.append(f"\U0001f33f {branch}")
                badge = "\n".join(lines)

                change = iterm2.LocalWriteOnlyProfile()
                change.set_badge_text(badge)
                change.set_badge_color(badge_color_for_status(status))
                try:
                    change.set_badge_max_width(BADGE_MAX_WIDTH)
                    change.set_badge_max_height(BADGE_MAX_HEIGHT)
                except AttributeError:
                    pass  # older iterm2 package may not have these
                await session.async_set_profile_properties(change)

        except Exception:
            pass


iterm2.run_forever(main)
