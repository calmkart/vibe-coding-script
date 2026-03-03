# Claude Code Scripts

[English](./README.md) | 中文

Claude Code CLI 工具的配置脚本集合。

## 快速开始（推荐）

一条命令安装所有功能 — 自动批准、Tab 状态指示、Session 管理面板：

```bash
# 克隆并安装（中文）
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./setup.sh install --lang zh

# 英文标签
./setup.sh install

# 查看状态
./setup.sh status

# 卸载全部
./setup.sh uninstall
```

安装内容：

| 功能 | 说明 |
|---|---|
| **自动批准** | Bash 命令自动执行，无需手动确认 |
| **Tab 指示器** | 松绿（执行中）/ 琥珀（待确认）/ 蓝色（等待输入）Tab 颜色 + 标题 |
| **Session 面板** | `📂 项目名` / `🌿 分支名` 水印 + 状态栏概览弹出面板 |

安装后重启 iTerm2。首次使用需手动操作（仅一次）：允许 Python API 连接，然后将 "Claude Sessions" 拖入状态栏。

---

## 高级用法（单独安装）

如需精细控制，每个功能可单独安装：

| 脚本 | 说明 |
|---|---|
| [auto-approve-setup.sh](#auto-approve-setupsh) | 自动批准 Bash 命令，无需手动确认 |
| [iterm-status-setup.sh](#iterm-status-setupsh) | iTerm2 tab 颜色和标题状态指示器 |
| [iterm-monitor-setup.sh](#iterm-monitor-setupsh) | 多 session 管理面板 — 紧凑标记水印、Dashboard 弹出面板、状态栏概览 |

---

### auto-approve-setup.sh

自动配置 Claude Code hooks，实现 Bash 命令自动批准，无需手动确认。

#### 功能

- 创建 `~/.claude/hooks/auto-approve.sh` hook 脚本
- 更新 `~/.claude/settings.json` 配置文件
- 自动合并现有配置，不会覆盖其他设置

#### 依赖

- `jq` - JSON 处理工具

```bash
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq
```

#### 使用方法

```bash
# 下载并执行
curl -fsSL https://raw.githubusercontent.com/calmkart/vibe-coding-script/main/claude-code/auto-approve-setup.sh | bash

# 或者克隆仓库后执行
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
chmod +x auto-approve-setup.sh
./auto-approve-setup.sh
```

#### 注意事项

- 此配置会自动批准所有 Bash 命令，请在信任的环境中使用
- 如需恢复手动确认，删除 `~/.claude/settings.json` 中对应的 hook 配置即可
- 脚本支持重复执行，不会产生重复配置

---

### iterm-status-setup.sh

为 iTerm2 tab 添加视觉状态指示器 — 根据 Claude Code 当前状态自动变色并更新标题。

#### 效果

| 状态 | Tab 颜色 | Tab 标题 | 触发时机 |
|---|---|---|---|
| **执行中** | 松绿 | `◉ 执行中 · 项目名` | 用户发送消息 |
| **待确认** | 琥珀 | `⏸ 待确认 · 项目名` | Claude 向用户提问 |
| **等待输入** | 蓝色 | `✓ 等待输入 · 项目名` | Claude 完成回复 |

#### 依赖

- **macOS** + iTerm2
- **Claude Code** CLI
- **Python 3**（macOS 自带）

#### 使用方法

```bash
./iterm-status-setup.sh install              # 英文
./iterm-status-setup.sh install --lang zh    # 中文
./iterm-status-setup.sh uninstall            # 卸载
./iterm-status-setup.sh status               # 查看状态
```

#### 语言

| 语言 | 执行中 | 待确认 | 等待输入 |
|---|---|---|---|
| `en`（默认） | `◉ Working` | `⏸ Action Needed` | `✓ Ready` |
| `zh` | `◉ 执行中` | `⏸ 待确认` | `✓ 等待输入` |

---

### iterm-monitor-setup.sh

为 iTerm2 添加 Python API 守护进程，用于管理多个 Claude Code session — 紧凑标记水印、Dashboard 管理面板、状态栏概览。

#### 效果

| 功能 | 说明 |
|---|---|
| **Badge 水印** | `📂 项目名` / `🌿 分支名` — 紧凑标注水印（占终端 15% 宽度，不遮挡内容） |
| **Worktree 标识** | worktree 分支带 `⤴` 后缀，与主仓库区分 |
| **Dashboard** | 点击状态栏打开深色主题管理面板 — 按状态排序的 session 卡片 |
| **状态栏** | `🤖 3 \| ◉2 ⏸1 ✓1` — 总 session 数 + 按状态统计 |

#### 依赖

- **macOS** + iTerm2
- **iterm-status-setup.sh** 已安装（前置条件）
- **Python 3** + **iterm2** pip 包（安装脚本会自动安装）

#### 使用方法

```bash
./iterm-monitor-setup.sh install
./iterm-monitor-setup.sh uninstall
./iterm-monitor-setup.sh status
```

#### 注意事项

- 必须先安装 `iterm-status-setup.sh`
- Badge 尺寸为 15% 宽 × 10% 高 — 可见但不遮挡终端内容
- 过期 session 自动清理（超过 5 分钟或进程已退出）
- Dashboard 按状态排序（执行中 → 待确认 → 等待输入），方便快速扫视
