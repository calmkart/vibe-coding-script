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
import json
import os
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import iterm2

# --- Config ---
SESSION_DIR = "/tmp/claude-sessions"
SCAN_INTERVAL = 2       # seconds between polls
STALE_THRESHOLD = 300   # seconds — remove files without PID older than this
LANG = "en"             # "en" or "zh", replaced by setup.sh during install

# Badge sizing (fraction of terminal area, 0.0–1.0)
BADGE_MAX_WIDTH = 0.15
BADGE_MAX_HEIGHT = 0.1

# --- Shared state for navigation server ---
_connection = None
_loop = None
_nav_port = 0

# --- i18n ---
_STRINGS = {
    "en": {
        "no_sessions": "No sessions",
        "running": "running", "waiting": "waiting", "idle": "idle",
        "no_active": "No active sessions",
        "start_hint": "Start Claude Code in a terminal to see sessions here",
        "title": "Claude Sessions",
        "active": "active",
        "branch": "branch",
        "nav_hint": "click card to switch session",
    },
    "zh": {
        "no_sessions": "\u65e0\u4f1a\u8bdd",
        "running": "\u8fd0\u884c\u4e2d", "waiting": "\u5f85\u786e\u8ba4", "idle": "\u7a7a\u95f2",
        "no_active": "\u65e0\u6d3b\u8dc3\u4f1a\u8bdd",
        "start_hint": "\u5728\u7ec8\u7aef\u4e2d\u542f\u52a8 Claude Code \u5373\u53ef\u770b\u5230\u4f1a\u8bdd",
        "title": "Claude \u4f1a\u8bdd",
        "active": "\u6d3b\u8dc3",
        "branch": "\u5206\u652f",
        "nav_hint": "\u70b9\u51fb\u5361\u7247\u8df3\u8f6c\u5230\u5bf9\u5e94\u4f1a\u8bdd",
    },
}


def _s(key):
    """Get localized string."""
    return _STRINGS.get(LANG, _STRINGS["en"]).get(key, key)


# --- Color Utilities ---

STATUS_BADGE_COLORS = {
    "working":   (50, 145, 80),
    "attention":  (200, 150, 50),
    "done":      (65, 105, 200),
}


def badge_color_for_status(status):
    r, g, b = STATUS_BADGE_COLORS.get(status, (128, 128, 128))
    return iterm2.Color(r, g, b, 160)


# --- Navigation HTTP Server ---

class _NavHandler(BaseHTTPRequestHandler):
    """Handles session-switch requests from dashboard popover."""

    def do_GET(self):
        params = parse_qs(urlparse(self.path).query)
        sid = params.get("sid", [""])[0]
        if sid and _loop and _connection:
            asyncio.run_coroutine_threadsafe(
                _activate_session(sid), _loop
            )
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def log_message(self, *args):
        pass  # suppress HTTP logs


async def _activate_session(session_id):
    """Switch to a specific iTerm2 session by its ID."""
    try:
        app = await iterm2.async_get_app(_connection)
        for window in app.terminal_windows:
            for tab in window.tabs:
                for session in tab.sessions:
                    if session.session_id == session_id:
                        await session.async_activate()
                        await window.async_activate()
                        return
    except Exception:
        pass


def _start_nav_server():
    global _nav_port
    server = HTTPServer(("127.0.0.1", 0), _NavHandler)
    _nav_port = server.server_address[1]
    server.serve_forever()


# --- Session File I/O ---

def read_sessions():
    """Read all session JSON files. Returns dict keyed by TTY path."""
    sessions = {}
    now = time.time()
    for path in glob.glob(os.path.join(SESSION_DIR, "*.json")):
        try:
            with open(path) as f:
                data = json.load(f)
            # Check PID alive first (macOS has no /proc)
            pid = data.get("pid")
            if pid:
                try:
                    os.kill(int(pid), 0)
                except ProcessLookupError:
                    # Process dead — remove session file
                    os.unlink(path)
                    continue
                except (PermissionError, ValueError, TypeError):
                    pass
                # PID alive — always keep, regardless of timestamp age
            else:
                # No PID field — fallback to timestamp-based cleanup
                if now - data.get("timestamp", 0) > STALE_THRESHOLD:
                    os.unlink(path)
                    continue
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
        return f"{delta}s"
    elif delta < 3600:
        return f"{delta // 60}m"
    else:
        return f"{delta // 3600}h"


def shorten_path(path, max_len=40):
    """Shorten a path with ~ for home and ellipsis if too long."""
    home = os.path.expanduser("~")
    if path.startswith(home):
        path = "~" + path[len(home):]
    if len(path) > max_len:
        path = "\u2026" + path[-(max_len - 1):]
    return path


# --- Status Icons ---
# Using clear, color-distinguishable indicators

STATUS_ICON = {"working": "\u26a1", "attention": "\U0001f514", "done": "\U0001f4a4"}


def session_summary(sessions):
    """Return status bar string like '\U0001f916 3 \u2502 \u26a12 \U0001f5141'."""
    if not sessions:
        return f"\U0001f916 {_s('no_sessions')}"
    counts = {"working": 0, "attention": 0, "done": 0}
    for s in sessions.values():
        st = s.get("status", "")
        if st in counts:
            counts[st] += 1
    parts = []
    if counts["working"]:
        parts.append(f"\u26a1{counts['working']}")
    if counts["attention"]:
        parts.append(f"\U0001f514{counts['attention']}")
    if counts["done"]:
        parts.append(f"\U0001f4a4{counts['done']}")
    total = sum(counts.values())
    summary = " ".join(parts) if parts else "\u2014"
    return f"\U0001f916 {total} \u2502 {summary}"


# --- Dashboard HTML ---

def dashboard_html(sessions, tty_sid_map=None, nav_port=0):
    """Build rich dark-mode dashboard HTML for the popover."""
    if not sessions:
        return (
            '<html><body style="font-family:-apple-system,sans-serif;padding:32px 24px;'
            'background:#111;color:#888;text-align:center">'
            '<p style="font-size:36px;margin:0 0 12px 0">\U0001f916</p>'
            f'<p style="font-size:13px;color:#aaa;margin:0 0 6px 0">{_s("no_active")}</p>'
            f'<p style="font-size:11px;color:#555">{_s("start_hint")}</p>'
            '</body></html>'
        )

    if tty_sid_map is None:
        tty_sid_map = {}

    # Count by status
    counts = {"working": 0, "attention": 0, "done": 0}
    for s in sessions.values():
        st = s.get("status", "")
        if st in counts:
            counts[st] += 1
    total = sum(counts.values())

    # Stats pills
    pill_cfg = {
        "working":   ("\u26a1", _s("running"),  "#0d2818", "#4ade80", "#22c55e"),
        "attention": ("\U0001f514", _s("waiting"),  "#2a1f0a", "#fbbf24", "#f59e0b"),
        "done":      ("\U0001f4a4", _s("idle"),     "#1a0d2e", "#c084fc", "#a855f7"),
    }
    stats_parts = []
    for key in ("working", "attention", "done"):
        if counts[key]:
            icon, label, bg, fg, _ = pill_cfg[key]
            stats_parts.append(
                f'<span style="background:{bg};color:{fg};padding:3px 10px;'
                f'border-radius:12px;font-size:11px;font-weight:500">'
                f'{icon} {counts[key]} {label}</span>'
            )
    stats_html = " ".join(stats_parts)

    # Card style maps
    color_map = {"working": "#4ade80", "attention": "#fbbf24", "done": "#c084fc"}
    border_map = {"working": "#22c55e", "attention": "#f59e0b", "done": "#a855f7"}
    bg_map = {"working": "#0a1f14", "attention": "#1a150a", "done": "#150a20"}
    hover_bg_map = {"working": "#0f2a1c", "attention": "#241c0f", "done": "#1f0f2c"}

    # Build cards
    cards = []
    for s in sorted(sessions.values(), key=lambda x: (
        {"working": 0, "attention": 1, "done": 2}.get(x.get("status", ""), 3),
        x.get("project", ""),
    )):
        status = s.get("status", "")
        icon = STATUS_ICON.get(status, "?")
        _status_label = {"working": _s("running"), "attention": _s("waiting"), "done": _s("idle")}
        label = _status_label.get(status, status)
        color = color_map.get(status, "#888")
        border = border_map.get(status, "#444")
        bg = bg_map.get(status, "#1e1e1e")
        hover_bg = hover_bg_map.get(status, "#252525")
        project = s.get("project", "?")
        branch = s.get("worktree") or s.get("branch") or ""
        cwd = s.get("cwd", "")
        tty_path = s.get("tty", "")
        tty = os.path.basename(tty_path)
        ts = s.get("timestamp", 0)
        age = format_age(ts) if ts else "?"
        short_cwd = shorten_path(cwd) if cwd else ""

        # Click-to-navigate
        sid = tty_sid_map.get(tty_path, "")
        click_attr = ""
        cursor = "default"
        if sid and nav_port:
            click_attr = (
                f' onclick="fetch(\'http://127.0.0.1:{nav_port}/switch?sid={sid}\''
                f').catch(()=>{{}})"'
            )
            cursor = "pointer"

        worktree_badge = ""
        if s.get("worktree"):
            worktree_badge = (
                ' <span style="background:#1f1535;color:#a78bfa;font-size:9px;'
                'padding:1px 6px;border-radius:4px;margin-left:4px;'
                'vertical-align:middle">wt</span>'
            )

        meta_items = []
        if branch:
            meta_items.append(
                f'<span style="color:#999">'
                f'<span style="color:#666">{_s("branch")}</span> {branch}{worktree_badge}</span>'
            )
        if short_cwd:
            meta_items.append(f'<span style="color:#555">{short_cwd}</span>')
        meta_html = (
            '<span style="margin:0 6px;color:#333">\u00b7</span>'.join(meta_items)
        )

        # Status label pill
        status_pill = (
            f'<span style="color:{color};font-size:10px;font-weight:500;'
            f'background:{bg};border:1px solid {border};'
            f'padding:1px 6px;border-radius:4px">{icon} {label}</span>'
        )

        cards.append(
            f'<div class="card" style="background:{bg};border-radius:8px;'
            f'padding:10px 14px;margin-bottom:6px;border-left:3px solid {border};'
            f'cursor:{cursor};transition:background .15s"'
            f' onmouseover="this.style.background=\'{hover_bg}\'"'
            f' onmouseout="this.style.background=\'{bg}\'"'
            f'{click_attr}>'
            # Row 1: project + status + tty/age
            f'<div style="display:flex;align-items:center;justify-content:space-between">'
            f'<div style="display:flex;align-items:center;gap:8px">'
            f'<span style="font-size:13px;font-weight:600;color:#eee">{project}</span>'
            f'{status_pill}'
            f'</div>'
            f'<span style="font-size:10px;color:#444">{tty} \u00b7 {age}</span>'
            f'</div>'
            # Row 2: branch + cwd
            f'<div style="margin-top:5px;font-size:11px;line-height:1.5">{meta_html}</div>'
            f'</div>'
        )

    # Navigation hint
    nav_hint = ""
    if tty_sid_map and nav_port:
        nav_hint = (
            '<div style="text-align:center;padding:4px 0 2px 0;font-size:10px;color:#444">'
            f'{_s("nav_hint")}</div>'
        )

    return (
        '<html><head><style>'
        '*{box-sizing:border-box;-webkit-user-select:none}'
        'body{font-family:-apple-system,BlinkMacSystemFont,sans-serif;margin:0;padding:0;'
        'background:#111;color:#e0e0e0}'
        '::-webkit-scrollbar{width:5px}'
        '::-webkit-scrollbar-track{background:#111}'
        '::-webkit-scrollbar-thumb{background:#333;border-radius:3px}'
        '</style></head><body>'
        # Header
        '<div style="background:linear-gradient(135deg,#0d1117,#111);'
        'padding:14px 16px;border-bottom:1px solid #222">'
        '<div style="display:flex;align-items:center;justify-content:space-between;'
        'margin-bottom:8px">'
        '<span style="font-size:14px;font-weight:600;color:#eee">'
        f'\U0001f916 {_s("title")}</span>'
        f'<span style="font-size:11px;color:#555">{total} {_s("active")}</span>'
        '</div>'
        f'<div style="display:flex;gap:6px;flex-wrap:wrap">{stats_html}</div>'
        '</div>'
        # Cards
        f'<div style="padding:8px 10px;overflow-y:auto;max-height:320px">'
        f'{"".join(cards)}</div>'
        f'{nav_hint}'
        '</body></html>'
    )


# --- Main Daemon ---

async def main(connection):
    global _connection, _loop
    _connection = connection
    _loop = asyncio.get_event_loop()

    # Start navigation HTTP server in background thread
    nav_thread = threading.Thread(target=_start_nav_server, daemon=True)
    nav_thread.start()
    # Wait for port assignment
    while _nav_port == 0:
        await asyncio.sleep(0.05)

    app = await iterm2.async_get_app(connection)
    applied_state = {}  # session_id -> {project, status, branch}

    # Cached TTY -> iTerm2 session ID map (refreshed in polling loop)
    tty_sid_map = {}

    # --- Register Status Bar Component ---
    component = iterm2.StatusBarComponent(
        short_description="Claude Sessions",
        detailed_description="Dashboard for all active Claude Code sessions",
        knobs=[],
        exemplar="\U0001f916 3 \u2502 \u26a12 \U0001f4a41",
        update_cadence=SCAN_INTERVAL,
        identifier="com.calmp.claude-session-monitor",
    )

    @iterm2.StatusBarRPC
    async def statusbar_coro(knobs):
        return session_summary(read_sessions())

    @iterm2.RPC
    async def onclick(session_id):
        sessions = read_sessions()
        # Build fresh TTY -> session ID map for click navigation
        click_map = {}
        try:
            cur_app = await iterm2.async_get_app(connection)
            for window in cur_app.terminal_windows:
                for tab in window.tabs:
                    for sess in tab.sessions:
                        try:
                            tty = await sess.async_get_variable("tty")
                            if tty:
                                click_map[tty] = sess.session_id
                        except Exception:
                            continue
        except Exception:
            pass
        html = dashboard_html(sessions, click_map, _nav_port)
        await component.async_open_popover(
            session_id, html, iterm2.util.Size(520, 420)
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

            # Update cached map for onclick
            tty_sid_map.clear()
            for tty, sess in tty_map.items():
                tty_sid_map[tty] = sess.session_id

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

                # Badge text
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
