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
./setup.sh install iterm-status --lang zh   # 只装 Tab 指示器（中文）
./setup.sh install iterm-monitor --lang zh  # 只装 Session 面板（中文）
./setup.sh install dashboard                # 只装终端仪表盘
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
├── dashboard/                # 终端 TUI 仪表盘
│   ├── setup.sh
│   ├── app.py                # Textual 主程序
│   ├── requirements.txt
│   ├── data/                 # 数据层（session、历史、统计、搜索、缓存）
│   ├── screens/              # UI 页面（活跃、浏览、用量、对话）
│   ├── widgets/              # 可复用组件（session 卡片、图表、热力图等）
│   ├── utils/                # 格式化、定价、导出、iTerm 集成
│   └── styles/               # Textual CSS 主题
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

**Hook 事件映射：**

| 事件 | 设置状态 | 说明 |
|---|---|---|
| `UserPromptSubmit` | working | 用户发送消息 |
| `PreToolUse *` | attention | 仅限阻塞工具（见下方） |
| `PostToolUse *` | working | 工具执行完成 |
| `Notification` | done | 系统通知 |
| `Stop` | done | 回合结束 |

**阻塞工具白名单** — 仅以下工具会触发琥珀色"待确认"状态：

- `AskUserQuestion` / `EnterPlanMode` / `ExitPlanMode`
- `Bash` 命令匹配 `git.*push` 时
- 其他工具（Read、Edit、Grep 等）静默跳过，不改变状态

**状态锁** — attention 设置后会写入锁文件（`/tmp/iterm-attention-$PPID`），防止后续的 `Notification` 或 `Stop` 将状态覆盖回 done。只有 `working`（用户确认后 `PostToolUse` 触发）才能解除锁。

**目录锁** — Tab 标题中的项目目录名在首次 hook 调用时锁定，即使 Claude 编辑子目录中的文件也不会改变。

### iterm-monitor

多 session 管理面板 — 水印标记、状态栏、可点击跳转的 Dashboard 弹出面板。

| 功能 | 说明 |
|---|---|
| **Badge 水印** | `📂 项目名` / `🌿 分支名` — 紧凑水印（15% 宽度） |
| **Dashboard** | 点击状态栏打开 session 卡片，点击卡片跳转到对应终端 |
| **状态栏** | `🤖 3 │ ⚡2 🔔1 ✔️1` — 总数 + 按状态统计 |

图标含义：⚡ 运行中、🔔 等待确认、✔️ 空闲。

Session 基于 PID 存活检测持久化，只要 Claude 进程在运行就会显示（不再基于超时清除）。

支持 `--lang zh` 切换中文面板标签（运行中 / 待确认 / 空闲）。

依赖 iterm-status（缺失时自动安装）。

### dashboard

基于 Python + [Textual](https://textual.textualize.io/) 构建的终端 TUI 仪表盘，用于在终端中管理 Claude Code session。

**依赖：** Python 3，`textual>=0.47.0`，`rich>=13.0.0`（自动安装到 venv）

**安装与启动：**

```bash
./setup.sh install dashboard    # 安装
claude-dashboard                # 启动
```

**标签页：**

| # | 标签页 | 说明 |
|---|--------|------|
| 1 | **Active（活跃）** | 实时查看运行中的 Claude Code session，显示用量和费用（每 2 秒自动刷新） |
| 2 | **History（历史）** | 双栏浏览器 — 左侧项目列表（含费用），右侧 session 列表 |
| 3 | **Usage（用量）** | 每日活动、模型分布、按项目统计费用，支持按时间范围过滤（7天/30天/全部） |
| 4 | **Conversation（对话）** | 完整对话内容查看，支持富文本渲染 |

**快捷键：**

| 按键 | 功能 |
|------|------|
| `Tab` / `Shift+Tab` | 下一个 / 上一个标签 |
| `1`–`4` | 切换到指定标签页 |
| `↑` / `↓` | 上下导航 |
| `←` / `→` | 切换面板（历史页） / 切换时间范围（用量页） |
| `Enter` | 打开 / 选择 |
| `Escape` | 返回 / 关闭 |
| `Ctrl+F` 或 `/` | 全文对话搜索 |
| `Ctrl+R` | 刷新所有数据 |
| `Ctrl+G` | 跳转到 iTerm2 对应 tab（活跃页） |
| `r` | 恢复 session |
| `Delete` / `Backspace` | 删除 session（历史页，弹窗确认） |
| `e` | 导出为 Markdown |
| `t` | 切换显示 thinking blocks |
| `s` | 切换排序方式（历史页） |
| `Home` / `End` | 跳到顶部 / 底部（对话页） |
| `?` | 帮助面板 |
| `q` | 退出 |

**数据来源：**

| 数据 | 路径 |
|------|------|
| 活跃 session | `/tmp/claude-sessions/*.json` |
| 历史 session | `~/.claude/projects/` |
| 使用统计 | `~/.claude/stats-cache.json` |

**工作原理：**
- 仪表盘直接读取 Claude Code 的原生数据文件，无需额外的守护进程或代理。
- 活跃 session 通过 `/tmp/claude-sessions/` 中的 JSON 文件检测，基于 PID 存活检查。
- 历史数据通过扫描 `~/.claude/projects/` 中的 JSONL 文件加载（不依赖可能过期的 `sessions-index.json`）。
- 费用估算使用 Anthropic 官方定价（Opus / Sonnet / Haiku，含缓存层定价）。
- 内置异步 TTL 缓存层，避免重复读取文件。

---

## 单独使用

每个功能也可以独立运行：

```bash
cd auto-approve && ./setup.sh install
cd iterm-status && ./setup.sh install --lang zh
cd iterm-monitor && ./setup.sh install
cd dashboard && ./setup.sh install
```
