# Vibe Coding Scripts

English | [中文](./README_CN.md)

A collection of utility scripts for various vibe coding tools.

## Directory Structure

```
vibe-coding-script/
├── claude-code/
│   ├── setup.sh              # ⭐ One-click install
│   ├── auto-approve/         # Bash auto-approve
│   ├── iterm-status/         # Tab color & title indicator
│   ├── iterm-monitor/        # Session dashboard
│   └── dashboard/            # Terminal TUI dashboard
├── README.md
└── README_CN.md
```

## Included Tools

### Claude Code

```bash
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./setup.sh install --lang zh    # Install all (Chinese)
./setup.sh install              # Install all (English)
./setup.sh install auto-approve # Install specific feature
```

Features:
- **auto-approve** — Bash commands run without manual confirmation
- **iterm-status** — iTerm2 tab color & title changes by Claude Code status
- **iterm-monitor** — Per-project badges, status bar overview, click-to-navigate dashboard
- **dashboard** — Terminal TUI for session monitoring, history browsing, usage stats & conversation search

See [claude-code/README.md](./claude-code/README.md) for details.

## Contributing

Contributions welcome. Please follow the existing directory structure.

## License

MIT
