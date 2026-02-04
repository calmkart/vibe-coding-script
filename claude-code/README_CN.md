# Claude Code Scripts

[English](./README.md) | 中文

Claude Code CLI 工具的配置脚本集合。

## 脚本列表

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
