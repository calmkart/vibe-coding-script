# Claude Code Scripts

[English](./README.md) | 中文

Claude Code CLI 工具的配置脚本集合。

## 快速开始

一条命令安装所有功能：

```bash
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./setup.sh install --lang zh    # 中文
./setup.sh install              # 英文
```

也可以只安装某个功能：

```bash
./setup.sh install auto-approve             # 只装自动批准
./setup.sh install iterm-status --lang zh   # 只装 Tab 指示器
./setup.sh install iterm-monitor            # 只装 Session 面板
```

管理：

```bash
./setup.sh status                    # 查看所有组件状态
./setup.sh uninstall                 # 卸载全部
./setup.sh uninstall iterm-monitor   # 卸载指定功能
```

安装后重启 iTerm2。首次使用需手动操作（仅一次）：允许 Python API 连接，然后将 "Claude Sessions" 拖入状态栏。

---

## 功能模块

```
claude-code/
├── setup.sh                  # 统一入口
├── auto-approve/             # Bash 自动批准
│   └── setup.sh
├── iterm-status/             # Tab 颜色和标题指示器
│   └── setup.sh
├── iterm-monitor/            # Session 管理面板
│   ├── setup.sh
│   └── daemon.py
```

### auto-approve

自动批准 Bash 命令，无需手动确认。

- 创建 `~/.claude/hooks/auto-approve.sh`
- 依赖 `jq`（`brew install jq`）

### iterm-status

iTerm2 tab 根据 Claude Code 状态自动变色并更新标题。

| 状态 | Tab 颜色 | Tab 标题 |
|---|---|---|
| **执行中** | 松绿 | `◉ 执行中 · 项目名` |
| **待确认** | 琥珀 | `⏸ 待确认 · 项目名` |
| **等待输入** | 蓝色 | `✓ 等待输入 · 项目名` |

支持 `--lang zh` 切换中文标签。

### iterm-monitor

多 session 管理面板 — 水印标记、状态栏、Dashboard 弹出面板。

| 功能 | 说明 |
|---|---|
| **Badge 水印** | `📂 项目名` / `🌿 分支名` — 紧凑水印（15% 宽度） |
| **Dashboard** | 点击状态栏打开深色主题 session 卡片 |
| **状态栏** | `🤖 3 \| ◉2 ⏸1 ✓1` — 总数 + 按状态统计 |

依赖 iterm-status（缺失时自动安装）。

---

## 单独使用

每个功能也可以独立运行：

```bash
cd auto-approve && ./setup.sh install
cd iterm-status && ./setup.sh install --lang zh
cd iterm-monitor && ./setup.sh install
```
