#!/bin/bash
# 自动配置 Claude Code hooks
# 用法: bash ~/.claude/setup-hooks.sh

set -e

CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
HOOK_SCRIPT="$HOOKS_DIR/auto-approve.sh"

# 创建目录
mkdir -p "$HOOKS_DIR"

# 创建 auto-approve.sh
cat > "$HOOK_SCRIPT" << 'EOF'
#!/bin/bash
# 自动批准所有 Bash 命令
# 输出 JSON 告诉 Claude Code 自动允许

jq -n '{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "Auto-approved by hook"
  }
}'
EOF

chmod +x "$HOOK_SCRIPT"
echo "✓ 已创建 $HOOK_SCRIPT"

# 要添加的 hook 配置
NEW_HOOK='{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "~/.claude/hooks/auto-approve.sh"
    }
  ]
}'

# 更新 settings.json（保留其他配置）
if [ -f "$SETTINGS_FILE" ]; then
    # 文件存在，合并配置
    TEMP_FILE=$(mktemp)

    jq --argjson newHook "$NEW_HOOK" '
      # 确保 hooks 和 hooks.PreToolUse 存在
      .hooks //= {} |
      .hooks.PreToolUse //= [] |
      # 检查是否已存在相同的 Bash matcher
      if (.hooks.PreToolUse | map(select(.matcher == "Bash" and .hooks[0].command == "~/.claude/hooks/auto-approve.sh")) | length) > 0
      then .
      else .hooks.PreToolUse += [$newHook]
      end
    ' "$SETTINGS_FILE" > "$TEMP_FILE"

    mv "$TEMP_FILE" "$SETTINGS_FILE"
    echo "✓ 已更新 $SETTINGS_FILE（保留原有配置）"
else
    # 文件不存在，创建新文件
    echo '{}' | jq --argjson newHook "$NEW_HOOK" '
      .hooks.PreToolUse = [$newHook]
    ' > "$SETTINGS_FILE"
    echo "✓ 已创建 $SETTINGS_FILE"
fi

echo "✓ 配置完成"
