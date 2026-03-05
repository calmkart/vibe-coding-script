# Vibe Coding Scripts

[English](./README.md) | 中文

收集各种 vibe coding 相关工具的实用脚本。

## 目录结构

```
vibe-coding-script/
├── claude-code/
│   ├── setup.sh              # ⭐ 一键安装
│   ├── auto-approve/         # Bash 自动批准
│   ├── iterm-status/         # Tab 颜色和标题指示器
│   ├── iterm-monitor/        # Session 管理面板
│   └── dashboard/            # 终端 TUI 仪表盘
├── README.md
└── README_CN.md
```

## 包含的工具

### Claude Code

```bash
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./setup.sh install --lang zh    # 安装全部（中文）
./setup.sh install              # 安装全部（英文）
./setup.sh install auto-approve # 安装指定功能
```

功能：
- **auto-approve** — Bash 命令自动执行，无需手动确认
- **iterm-status** — iTerm2 tab 颜色和标题随 Claude Code 状态自动变化
- **iterm-monitor** — 项目水印、状态栏概览、可点击跳转的 Dashboard 面板
- **dashboard** — 终端 TUI 仪表盘，支持 session 监控、历史浏览、用量统计和对话搜索

详见 [claude-code/README_CN.md](./claude-code/README_CN.md)

## 贡献

欢迎提交新的工具脚本，请按照现有目录结构组织文件。

## License

MIT
