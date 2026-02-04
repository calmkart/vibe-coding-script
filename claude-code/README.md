# Claude Code Scripts

English | [中文](./README_CN.md)

A collection of configuration scripts for the Claude Code CLI tool.

## Scripts

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
