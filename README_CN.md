# Vibe Coding Scripts

[English](./README.md) | 中文

收集各种 vibe coding 相关工具的实用脚本。

## 目录结构

```
vibe-coding-script/
├── claude-code/          # Claude Code 相关脚本
│   ├── setup.sh          # ⭐ 一键安装（推荐）
│   ├── auto-approve-setup.sh
│   ├── iterm-status-setup.sh
│   ├── iterm-monitor-setup.sh
│   └── iterm-monitor-daemon.py
├── README.md             # 英文说明
└── README_CN.md          # 中文说明
```

## 包含的工具

### Claude Code

位于 `claude-code/` 目录。一键安装：

```bash
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./setup.sh install --lang zh    # 中文
./setup.sh install              # 英文
```

一条命令安装所有功能：
- **自动批准** — Bash 命令自动执行，无需手动确认
- **Tab 指示器** — iTerm2 tab 颜色和标题随 Claude Code 状态自动变化
- **Session 面板** — 项目水印、状态栏概览、Dashboard 弹出面板

详见 [claude-code/README_CN.md](./claude-code/README_CN.md)

## 贡献

欢迎提交新的 vibe coding 工具脚本，请按照现有目录结构组织文件，并提供完整的使用说明。

## License

MIT
