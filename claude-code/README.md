# Claude Code Scripts

English | [中文](./README_CN.md)

A collection of configuration scripts for the Claude Code CLI tool.

## Quick Start

One command to install everything:

```bash
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./setup.sh install              # English
./setup.sh install --lang zh    # Chinese labels
```

Or install a specific feature:

```bash
./setup.sh install auto-approve             # Only auto-approve
./setup.sh install iterm-status --lang zh   # Only tab indicator (Chinese)
./setup.sh install iterm-monitor --lang zh  # Only session dashboard (Chinese)
./setup.sh install dashboard                # Only terminal TUI dashboard
```

Management:

```bash
./setup.sh status                    # Show all component status
./setup.sh uninstall                 # Remove everything
./setup.sh uninstall iterm-monitor   # Remove specific feature
```

After install, restart iTerm2. First-time only: allow Python API dialog, then drag "Claude Sessions" to the status bar.

---

## Features

```
claude-code/
├── setup.sh                  # Unified entry point
├── auto-approve/             # Bash auto-approve
│   └── setup.sh
├── iterm-status/             # Tab color & title indicator
│   └── setup.sh
├── iterm-monitor/            # Session dashboard
│   ├── setup.sh
│   └── daemon.py
├── dashboard/                # Terminal TUI dashboard
│   ├── setup.sh
│   ├── app.py                # Main Textual application
│   ├── requirements.txt
│   ├── data/                 # Data layer (sessions, history, stats, search, cache)
│   ├── screens/              # UI screens (active, browser, usage, conversation)
│   ├── widgets/              # Reusable widgets (session card, chart, heatmap, etc.)
│   ├── utils/                # Formatting, pricing, export, iTerm integration
│   └── styles/               # Textual CSS theme
```

### auto-approve

Auto-approve Bash commands without manual confirmation.

- Creates `~/.claude/hooks/auto-approve.sh`
- Requires `jq` (`brew install jq`)

### iterm-status

iTerm2 tab color & title changes based on Claude Code status.

| State | Tab Color | Tab Title |
|---|---|---|
| **Working** | Green | `◉ Working · project-name` |
| **Action Needed** | Amber | `⏸ Action Needed · project-name` |
| **Ready** | Blue | `✓ Ready · project-name` |

Supports `--lang zh` for Chinese labels (执行中 / 待确认 / 等待输入).

**Hook events:**

| Event | Status set | Description |
|---|---|---|
| `UserPromptSubmit` | working | User sent a message |
| `PreToolUse *` | attention | Only for blocking tools (see below) |
| `PostToolUse *` | working | Tool completed |
| `Notification` | done | System notification |
| `Stop` | done | Turn ended |

**Blocking tool whitelist** — only these trigger the Amber "Action Needed" state:

- `AskUserQuestion` / `EnterPlanMode` / `ExitPlanMode`
- `Bash` commands matching `git.*push`
- All other tools (Read, Edit, Grep, etc.) are silently skipped

**State lock** — once attention is set, a lock file (`/tmp/iterm-attention-$PPID`) prevents `Notification` or `Stop` from overriding it back to done. Only `working` (from `PostToolUse` after user confirms) clears the lock.

### iterm-monitor

Multi-session dashboard with badges, status bar, and click-to-navigate popover.

| Feature | Description |
|---|---|
| **Badge** | `📂 project` / `🌿 branch` — compact watermark (15% width) |
| **Dashboard** | Click status bar → session cards, click card → jump to that terminal |
| **Status Bar** | `🤖 3 │ ⚡2 🔔1 ✔️1` — total + count by state |

Icons: ⚡ running, 🔔 waiting for input, ✔️ idle.

Sessions persist as long as the Claude process is alive (PID-based tracking, not timeout-based).

Supports `--lang zh` for Chinese dashboard labels (运行中 / 待确认 / 空闲).

Requires iterm-status (auto-installed if missing).

### dashboard

A rich terminal TUI built with Python + [Textual](https://textual.textualize.io/) for managing Claude Code sessions from your terminal.

**Requirements:** Python 3, `textual>=0.47.0`, `rich>=13.0.0` (auto-installed in a venv)

**Install & launch:**

```bash
./setup.sh install dashboard    # Install
claude-dashboard                # Launch
```

**Tabs:**

| # | Tab | Description |
|---|-----|-------------|
| 1 | **Active** | Real-time view of running Claude Code sessions (auto-refreshes every 2s) |
| 2 | **History** | Dual-pane browser — projects on the left, sessions on the right |
| 3 | **Usage** | Daily activity chart, model breakdown, estimated cost per model |
| 4 | **Conversation** | Full conversation viewer with rich text rendering |

**Keyboard shortcuts:**

| Key | Action |
|-----|--------|
| `Tab` / `Shift+Tab` | Next / prev tab |
| `1`–`4` | Switch to specific tab |
| `↑` / `↓` | Navigate items |
| `←` / `→` | Switch panes (History) / Change period (Usage) |
| `Enter` | Open / Select |
| `Escape` | Back / Close |
| `Ctrl+F` or `/` | Search conversations |
| `Ctrl+R` | Refresh all data |
| `Ctrl+G` | Jump to iTerm2 tab (Active) |
| `r` | Resume session |
| `Del` / `Backspace` | Delete session (History, with confirmation) |
| `e` | Export to Markdown |
| `t` | Toggle thinking blocks |
| `s` | Cycle sort order (History) |
| `Home` / `End` | Scroll to top / bottom (Conversation) |
| `?` | Help overlay |
| `q` | Quit |

**Data sources:**

| Data | Path |
|------|------|
| Active sessions | `/tmp/claude-sessions/*.json` |
| Session history | `~/.claude/projects/` |
| Usage stats | `~/.claude/stats-cache.json` |

**How it works:**
- The dashboard reads Claude Code's native data files — no additional daemons or agents needed.
- Active sessions are detected via `/tmp/claude-sessions/` JSON files with PID-based liveness checks.
- History is loaded from `~/.claude/projects/` including `sessions-index.json` and conversation JSONL files.
- Cost estimates use official Anthropic pricing (Opus / Sonnet / Haiku, including cache tiers).
- An async TTL cache layer avoids redundant file reads.

---

## Standalone Use

Each feature can also be run independently:

```bash
cd auto-approve && ./setup.sh install
cd iterm-status && ./setup.sh install --lang zh
cd iterm-monitor && ./setup.sh install
cd dashboard && ./setup.sh install
```
