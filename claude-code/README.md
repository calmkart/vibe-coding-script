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
./setup.sh install iterm-status --lang zh   # Only tab indicator
./setup.sh install iterm-monitor            # Only session dashboard
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

### iterm-monitor

Multi-session dashboard with badges, status bar, and popover.

| Feature | Description |
|---|---|
| **Badge** | `📂 project` / `🌿 branch` — compact watermark (15% width) |
| **Dashboard** | Click status bar for dark-mode session cards |
| **Status Bar** | `🤖 3 \| ◉2 ⏸1 ✓1` — total + count by state |

Requires iterm-status (auto-installed if missing).

---

## Standalone Use

Each feature can also be run independently:

```bash
cd auto-approve && ./setup.sh install
cd iterm-status && ./setup.sh install --lang zh
cd iterm-monitor && ./setup.sh install
```
