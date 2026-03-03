# Claude Code Scripts

English | [中文](./README_CN.md)

A collection of configuration scripts for the Claude Code CLI tool.

## Quick Start (Recommended)

One command to install everything — auto-approve, tab status, session dashboard:

```bash
# Clone and install (English)
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./setup.sh install

# Chinese labels
./setup.sh install --lang zh

# Check status
./setup.sh status

# Uninstall everything
./setup.sh uninstall
```

What gets installed:

| Feature | Description |
|---|---|
| **Auto-approve** | Bash commands run without manual confirmation |
| **Tab indicator** | Green (Working) / Amber (Attention) / Blue (Ready) tab color + title |
| **Session dashboard** | `📂 project` / `🌿 branch` badge + status bar popover for all sessions |

After install, restart iTerm2. First-time only: allow Python API dialog, then drag "Claude Sessions" to the status bar.

---

## Advanced (Individual Scripts)

For granular control, each feature can be installed separately:

| Script | Description |
|---|---|
| [auto-approve-setup.sh](#auto-approve-setupsh) | Auto-approve Bash commands without manual confirmation |
| [iterm-status-setup.sh](#iterm-status-setupsh) | iTerm2 tab color & title indicator for Claude Code status |
| [iterm-monitor-setup.sh](#iterm-monitor-setupsh) | Multi-session dashboard — compact badges, rich dashboard popover, status bar overview |

---

### auto-approve-setup.sh

Automatically configures Claude Code hooks to auto-approve Bash commands without manual confirmation.

#### Features

- Creates `~/.claude/hooks/auto-approve.sh` hook script
- Updates `~/.claude/settings.json` configuration file
- Automatically merges with existing config without overwriting other settings

#### Dependencies

- `jq` - JSON processing tool

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq
```

#### Usage

```bash
# Download and execute
curl -fsSL https://raw.githubusercontent.com/calmkart/vibe-coding-script/main/claude-code/auto-approve-setup.sh | bash

# Or clone the repo and execute
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
chmod +x auto-approve-setup.sh
./auto-approve-setup.sh
```

#### Notes

- This configuration auto-approves all Bash commands - use only in trusted environments
- To restore manual confirmation, remove the corresponding hook configuration from `~/.claude/settings.json`
- The script is idempotent and won't create duplicate configurations

---

### iterm-status-setup.sh

Adds a visual status indicator to your iTerm2 tab — color and title change based on Claude Code's current state.

#### Demo

| State | Tab Color | Tab Title | Trigger |
|---|---|---|---|
| **Working** | Green | `◉ Working · project-name` | User sends a message |
| **Action Needed** | Amber | `⏸ Action Needed · project-name` | Claude asks a question |
| **Ready** | Blue | `✓ Ready · project-name` | Claude finishes responding |

#### Requirements

- **macOS** with iTerm2
- **Claude Code** CLI installed
- **Python 3** (pre-installed on macOS)

#### Usage

```bash
./iterm-status-setup.sh install              # English
./iterm-status-setup.sh install --lang zh    # Chinese
./iterm-status-setup.sh uninstall            # Remove
./iterm-status-setup.sh status               # Check state
```

#### Language

| Language | Working | Action Needed | Ready |
|---|---|---|---|
| `en` (default) | `◉ Working` | `⏸ Action Needed` | `✓ Ready` |
| `zh` | `◉ 执行中` | `⏸ 待确认` | `✓ 等待输入` |

---

### iterm-monitor-setup.sh

Adds an iTerm2 Python API daemon for managing multiple Claude Code sessions — compact labeled badges, a rich dashboard popover, and a status bar overview widget.

#### Demo

| Feature | Description |
|---|---|
| **Badge** | `📂 project-name` / `🌿 branch` — compact labeled watermark (15% width, won't obscure content) |
| **Worktree** | Worktree branch shown with `⤴` suffix to distinguish from main repo |
| **Dashboard** | Click status bar for a rich dark-mode dashboard — session cards with project, branch, directory, TTY, age |
| **Status Bar** | `🤖 3 \| ◉2 ⏸1 ✓1` — total sessions + count by state |

#### Requirements

- **macOS** with iTerm2
- **iterm-status-setup.sh** installed first (prerequisite)
- **Python 3** + **iterm2** pip package (installed automatically)

#### Usage

```bash
./iterm-monitor-setup.sh install
./iterm-monitor-setup.sh uninstall
./iterm-monitor-setup.sh status
```

#### Notes

- Requires `iterm-status-setup.sh` to be installed first
- Badge is sized to 15% width × 10% height — visible but won't obscure terminal content
- Stale sessions are automatically cleaned up (>5min old or dead PID)
- Dashboard sorts sessions by status (working → attention → done) for quick scanning
