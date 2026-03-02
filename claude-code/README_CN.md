# Claude Code Scripts

[English](./README.md) | 中文

Claude Code CLI 工具的配置脚本集合。

## 脚本列表

| 脚本 | 说明 |
|---|---|
| [auto-approve-setup.sh](#auto-approve-setupsh) | 自动批准 Bash 命令，无需手动确认 |
| [iterm-status-setup.sh](#iterm-status-setupsh) | iTerm2 tab 颜色和标题状态指示器 |

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

#### 执行效果

脚本执行后会：

1. 创建 `~/.claude/hooks/` 目录
2. 生成 `auto-approve.sh` hook 脚本
3. 在 `settings.json` 中添加 PreToolUse hook 配置

配置完成后，Claude Code 执行 Bash 命令时将自动批准，不再需要手动确认。

#### 配置说明

脚本会在 `~/.claude/settings.json` 中添加以下配置：

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

#### 工作原理

```
用户发消息       → UserPromptSubmit  → 🟢 松绿（执行中）
Claude 提问      → PreToolUse        → 🟡 琥珀（待确认）
用户回答问题     → PostToolUse       → 🟢 松绿（恢复执行）
Claude 完成      → Stop              → 🔵 蓝色（等待输入）
```

#### 依赖

- **macOS** + iTerm2
- **Claude Code** CLI
- **Python 3**（macOS 自带）

无需安装额外依赖。

#### 使用方法

```bash
# 安装（英文标签，默认）
curl -fsSL https://raw.githubusercontent.com/calmkart/vibe-coding-script/main/claude-code/iterm-status-setup.sh | bash -s install

# 安装（中文标签）
curl -fsSL https://raw.githubusercontent.com/calmkart/vibe-coding-script/main/claude-code/iterm-status-setup.sh | bash -s install --lang zh

# 卸载（清理所有修改）
curl -fsSL https://raw.githubusercontent.com/calmkart/vibe-coding-script/main/claude-code/iterm-status-setup.sh | bash -s uninstall

# 或者克隆仓库后执行
git clone https://github.com/calmkart/vibe-coding-script.git
cd vibe-coding-script/claude-code
./iterm-status-setup.sh install              # 英文
./iterm-status-setup.sh install --lang zh    # 中文
./iterm-status-setup.sh uninstall            # 卸载
./iterm-status-setup.sh status               # 查看状态
```

#### 命令说明

| 命令 | 说明 |
|---|---|
| `install` | 安装，默认英文标签 |
| `install --lang zh` | 安装，中文标签 |
| `uninstall` | 删除 hook 脚本，清理 settings.json，移除环境变量 |
| `status` | 显示是否已安装及当前语言 |

#### 执行效果

**安装：**

1. **配置 iTerm2**（通过 PlistBuddy）— 为所有 profile 开启 Visual Bell、Flashing Bell，设置 tab 标题显示 Session Name + Job Name
2. **创建 hook 脚本** `~/.claude/hooks/iterm-status.sh` — 通过 iTerm2 escape sequence 控制 tab 颜色和标题，使用 TTY 缓存提升性能
3. **更新 `~/.claude/settings.json`** — 添加 `UserPromptSubmit`、`PreToolUse`、`PostToolUse`、`Stop`、`Notification` 等 hook；设置 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` 防止 Claude Code 覆盖 tab 标题

**卸载：**

1. 删除 `~/.claude/hooks/iterm-status.sh`
2. 从 `settings.json` 中移除所有 `iterm-status.sh` 相关 hook 条目
3. 移除 `CLAUDE_CODE_DISABLE_TERMINAL_TITLE` 环境变量
4. 清理临时文件
5. iTerm2 plist 不做改动（保留的设置无副作用）

#### 语言设置

语言在安装时写入 hook 脚本，切换语言只需重新安装：

```bash
./iterm-status-setup.sh install --lang zh    # 切换到中文
./iterm-status-setup.sh install              # 切换回英文
```

| 语言 | 执行中 | 待确认 | 等待输入 |
|---|---|---|---|
| `en`（默认） | `◉ Working` | `⏸ Action Needed` | `✓ Ready` |
| `zh` | `◉ 执行中` | `⏸ 待确认` | `✓ 等待输入` |

#### 测试

安装后重启 iTerm2，在 shell 中运行：

```bash
echo '{}' | ~/.claude/hooks/iterm-status.sh working    # 松绿
echo '{}' | ~/.claude/hooks/iterm-status.sh attention  # 琥珀
echo '{}' | ~/.claude/hooks/iterm-status.sh done       # 蓝色
echo '{}' | ~/.claude/hooks/iterm-status.sh reset      # 恢复默认
```

#### 注意事项

- 脚本支持重复执行，不会产生重复配置
- 自动合并到现有 `settings.json`，不会覆盖其他 hook 或设置
- 首次安装后需重启 iTerm2 使 plist 配置生效
