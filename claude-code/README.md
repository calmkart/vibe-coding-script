# Claude Code Scripts

English | [中文](./README_CN.md)

A collection of configuration scripts for the Claude Code CLI tool.

## Scripts

| Script | Description |
|---|---|
| [auto-approve-setup.sh](#auto-approve-setupsh) | Auto-approve Bash commands without manual confirmation |
| [iterm-status-setup.sh](#iterm-status-setupsh) | iTerm2 tab color & title indicator for Claude Code status |

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

#### What It Does

After running the script:

1. Creates `~/.claude/hooks/` directory
2. Generates `auto-approve.sh` hook script
3. Adds PreToolUse hook configuration to `settings.json`

Once configured, Claude Code will automatically approve Bash commands without requiring manual confirmation.

#### Configuration Details

The script adds the following configuration to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "~/.claude/hooks/auto-approve.sh"
          }
        ]
      }
    ]
  }
}
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

#### How It Works

```
User sends message  → UserPromptSubmit  → 🟢 Green (Working)
Claude asks user    → PreToolUse        → 🟡 Amber (Action Needed)
User answers        → PostToolUse       → 🟢 Green (Working)
Claude finishes     → Stop              → 🔵 Blue  (Ready)
```

#### Requirements

- **macOS** with iTerm2
- **Claude Code** CLI installed
- **Python 3** (pre-installed on macOS)

No additional dependencies required.

#### Usage

```bash
# Install (English labels, default)
curl -fsSL https://raw.githubusercontent.com/calmkart/vibe-coding-script/main/claude-code/iterm-status-setup.sh | bash -s install

# Install with Chinese labels
curl -fsSL https://raw.githubusercontent.com/calmkart/vibe-coding-script/main/claude-code/iterm-status-setup.sh | bash -s install --lang zh

# Uninstall (cleanly removes all changes)
curl -fsSL https://raw.githubusercontent.com/calmkart/vibe-coding-script/main/claude-code/iterm-status-setup.sh | bash -s uninstall

# Or clone the repo
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./iterm-status-setup.sh install              # English
./iterm-status-setup.sh install --lang zh    # Chinese
./iterm-status-setup.sh uninstall            # Remove
./iterm-status-setup.sh status               # Check state
```

#### Commands

| Command | Description |
|---|---|
| `install` | Install with English labels (default) |
| `install --lang zh` | Install with Chinese labels |
| `uninstall` | Remove hook script, clean settings.json, remove env var |
| `status` | Show whether installed, current language |

#### What It Does

**Install:**

1. **Configures iTerm2** (via PlistBuddy) — enables Visual Bell, Flashing Bell, and sets tab title to show Session Name + Job Name for all profiles
2. **Creates hook script** `~/.claude/hooks/iterm-status.sh` — handles tab color and title changes via iTerm2 escape sequences, with TTY caching for performance
3. **Updates `~/.claude/settings.json`** — adds hooks for `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `Stop`, and `Notification` events; sets `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` to prevent Claude Code from overriding tab titles

**Uninstall:**

1. Removes `~/.claude/hooks/iterm-status.sh`
2. Removes all `iterm-status.sh` hook entries from `settings.json`
3. Removes `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` env var
4. Cleans up temp files
5. iTerm2 plist is left untouched (harmless settings)

#### Language

Language is set at install time and baked into the hook script. To switch, re-run install:

```bash
./iterm-status-setup.sh install --lang zh    # Switch to Chinese
./iterm-status-setup.sh install              # Switch back to English
```

| Language | Working | Action Needed | Ready |
|---|---|---|---|
| `en` (default) | `◉ Working` | `⏸ Action Needed` | `✓ Ready` |
| `zh` | `◉ 执行中` | `⏸ 待确认` | `✓ 等待输入` |

#### Testing

After setup, restart iTerm2 and run these directly in your shell:

```bash
echo '{}' | ~/.claude/hooks/iterm-status.sh working    # green tab
echo '{}' | ~/.claude/hooks/iterm-status.sh attention  # amber tab
echo '{}' | ~/.claude/hooks/iterm-status.sh done       # blue tab
echo '{}' | ~/.claude/hooks/iterm-status.sh reset      # restore default
```

#### Notes

- The script is idempotent — safe to run multiple times
- Merges with existing `settings.json` without overwriting other hooks or settings
- Restart iTerm2 after first setup to apply plist changes
