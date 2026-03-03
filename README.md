# Vibe Coding Scripts

English | [中文](./README_CN.md)

A collection of utility scripts for various vibe coding tools.

## Directory Structure

```
vibe-coding-script/
├── claude-code/          # Claude Code related scripts
│   ├── setup.sh          # ⭐ One-click install (recommended)
│   ├── auto-approve-setup.sh
│   ├── iterm-status-setup.sh
│   ├── iterm-monitor-setup.sh
│   └── iterm-monitor-daemon.py
├── README.md             # English documentation
└── README_CN.md          # Chinese documentation
```

## Included Tools

### Claude Code

Located in the `claude-code/` directory. One-click setup:

```bash
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./setup.sh install --lang zh    # Chinese
./setup.sh install              # English
```

Installs all features at once:
- **Auto-approve** — Bash commands run without manual confirmation
- **Tab indicator** — iTerm2 tab color & title changes by Claude Code status
- **Session dashboard** — per-project badges, status bar overview, rich popover

See [claude-code/README.md](./claude-code/README.md) for details.

## Contributing

Contributions of new vibe coding tool scripts are welcome. Please follow the existing directory structure and provide comprehensive documentation.

## License

MIT
