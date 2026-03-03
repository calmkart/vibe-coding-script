#!/bin/bash
set -euo pipefail

# ============================================================
#  Claude Code × iTerm2 Session Monitor
#
#  Adds per-project badges, branch info, and a status bar
#  overview widget for managing multiple Claude Code sessions.
#
#  Requires iterm-status-setup.sh to be installed first.
#
#  Usage:
#    ./iterm-monitor-setup.sh install              # Install
#    ./iterm-monitor-setup.sh uninstall            # Remove all changes
#    ./iterm-monitor-setup.sh status               # Show current state
# ============================================================

CLAUDE_DIR="$HOME/.claude"
HOOKS_DIR="$CLAUDE_DIR/hooks"
HOOK_SCRIPT="$HOOKS_DIR/iterm-status.sh"
ITERM_PLIST="$HOME/Library/Preferences/com.googlecode.iterm2.plist"
AUTOLAUNCH_DIR="$HOME/Library/Application Support/iTerm2/Scripts/AutoLaunch"
DAEMON_DEST="$AUTOLAUNCH_DIR/claude-session-monitor.py"
SESSION_DIR="/tmp/claude-sessions"
SENTINEL_BEGIN="# --- BEGIN claude-session-monitor ---"
SENTINEL_END="# --- END claude-session-monitor ---"

# Where is this script located? (for finding the daemon source)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
DAEMON_SRC="$SCRIPT_DIR/iterm-monitor-daemon.py"

info()  { printf '\033[1;34m[INFO]\033[0m  %s\n' "$1"; }
ok()    { printf '\033[1;32m[OK]\033[0m    %s\n' "$1"; }
warn()  { printf '\033[1;33m[WARN]\033[0m  %s\n' "$1"; }
err()   { printf '\033[1;31m[ERR]\033[0m   %s\n' "$1"; }

usage() {
    cat <<EOF
Claude Code × iTerm2 Session Monitor

Adds per-project badges, branch/worktree info, and a status bar
overview widget for managing multiple Claude Code sessions.

Prerequisite: iterm-status-setup.sh must be installed first.

Usage:
  $(basename "$0") install        Install daemon + patch hook
  $(basename "$0") uninstall      Remove all changes
  $(basename "$0") status         Show current state
EOF
    exit 1
}

# ===========================================================
#  INSTALL
# ===========================================================
do_install() {
    # ------------------------------------------------------
    # 1. Pre-flight
    # ------------------------------------------------------
    info "Checking environment..."

    if ! command -v python3 &>/dev/null; then
        err "python3 not found — required for iTerm2 Python API"
        exit 1
    fi

    if [ ! -f "$ITERM_PLIST" ]; then
        err "iTerm2 plist not found — install iTerm2 first"
        exit 1
    fi

    if [ ! -f "$HOOK_SCRIPT" ]; then
        err "iterm-status.sh not found — run iterm-status-setup.sh install first"
        exit 1
    fi

    if [ ! -f "$DAEMON_SRC" ]; then
        err "iterm-monitor-daemon.py not found at $DAEMON_SRC"
        exit 1
    fi

    ok "Environment OK"

    # ------------------------------------------------------
    # 2. Install iterm2 Python package
    # ------------------------------------------------------
    info "Checking iterm2 Python package..."

    if python3 -c "import iterm2" 2>/dev/null; then
        ok "iterm2 package already installed"
    else
        info "Installing iterm2 package..."
        pip3 install --user iterm2 2>&1 | tail -1
        if python3 -c "import iterm2" 2>/dev/null; then
            ok "iterm2 package installed"
        else
            err "Failed to install iterm2 package"
            echo "  Try manually: pip3 install --user iterm2"
            exit 1
        fi
    fi

    # ------------------------------------------------------
    # 3. Patch iterm-status.sh (append session JSON block)
    # ------------------------------------------------------
    info "Patching hook script..."

    if grep -q "$SENTINEL_BEGIN" "$HOOK_SCRIPT" 2>/dev/null; then
        ok "Hook already patched (skipped)"
    else
        cat >> "$HOOK_SCRIPT" << 'HOOKEOF'

# --- BEGIN claude-session-monitor ---
# Session metadata for iTerm2 monitor daemon (written by iterm-monitor-setup.sh)
SESSION_DIR="/tmp/claude-sessions"
mkdir -p "$SESSION_DIR" 2>/dev/null
TTY_NAME=$(echo "$TTY" | sed 's|/dev/||; s|/|_|g')
SESSION_FILE="$SESSION_DIR/$TTY_NAME.json"
full_cwd=""
if [ -n "$input" ]; then
    full_cwd=$(echo "$input" | grep -o '"cwd":"[^"]*"' | head -1 | cut -d'"' -f4)
fi
branch=""; worktree=""
if [ -n "$full_cwd" ]; then
    if [ -d "$full_cwd/.git" ] || [ -f "$full_cwd/.git" ]; then
        branch=$(git -C "$full_cwd" rev-parse --abbrev-ref HEAD 2>/dev/null)
        [ -f "$full_cwd/.git" ] && worktree="$branch"
    fi
fi
case "$1" in
    reset) rm -f "$SESSION_FILE" 2>/dev/null ;;
    *) printf '{"tty":"%s","pid":%s,"status":"%s","project":"%s","branch":"%s","worktree":"%s","cwd":"%s","timestamp":%s}\n' \
        "$TTY" "$PPID" "${1:-unknown}" "${dir:-unknown}" "${branch:-}" "${worktree:-}" "${full_cwd:-}" "$(date +%s)" \
        > "$SESSION_FILE" 2>/dev/null ;;
esac
# --- END claude-session-monitor ---
HOOKEOF
        ok "Hook script patched: $HOOK_SCRIPT"
    fi

    # ------------------------------------------------------
    # 4. Install daemon to AutoLaunch
    # ------------------------------------------------------
    info "Installing daemon script..."

    mkdir -p "$AUTOLAUNCH_DIR"
    cp "$DAEMON_SRC" "$DAEMON_DEST"
    chmod +x "$DAEMON_DEST"
    ok "Daemon installed: $DAEMON_DEST"

    # ------------------------------------------------------
    # 5. Enable iTerm2 Python API
    # ------------------------------------------------------
    info "Checking iTerm2 Python API..."

    PB="/usr/libexec/PlistBuddy"
    api_enabled=$("$PB" -c "Print :EnableAPIServer" "$ITERM_PLIST" 2>/dev/null || echo "")

    if [ "$api_enabled" = "true" ]; then
        ok "Python API already enabled"
    else
        "$PB" -c "Set :EnableAPIServer true" "$ITERM_PLIST" 2>/dev/null ||
        "$PB" -c "Add :EnableAPIServer bool true" "$ITERM_PLIST" 2>/dev/null
        ok "Python API enabled in iTerm2 preferences"
    fi

    # ------------------------------------------------------
    # 6. Create session directory
    # ------------------------------------------------------
    mkdir -p "$SESSION_DIR"

    # ------------------------------------------------------
    # 7. Summary
    # ------------------------------------------------------
    echo ""
    echo "============================================"
    echo "  Session Monitor Installed!"
    echo "============================================"
    echo ""
    echo "  Features:"
    echo "    Badge      — 📂 project-name / 🌿 branch (compact watermark)"
    echo "    Dashboard  — click status bar for rich session dashboard"
    echo "    Status Bar — 🤖 3 | ◉2 ⏸1 overview of all sessions"
    echo ""
    echo "  Next steps:"
    echo "    1. Restart iTerm2"
    echo "    2. If prompted, allow the Python API connection"
    echo "    3. Add status bar component:"
    echo "       Preferences > Profiles > Session > Status bar enabled"
    echo "       > Configure Status Bar > drag 'Claude Sessions' to active area"
    echo ""
    echo "  功能说明："
    echo "    Badge      — 📂 项目名 / 🌿 分支名（紧凑水印，不遮挡内容）"
    echo "    Dashboard  — 点击状态栏打开 session 管理面板"
    echo "    状态栏     — 🤖 3 | ◉2 ⏸1 显示所有 session 概览"
    echo ""
    echo "  下一步："
    echo "    1. 重启 iTerm2"
    echo "    2. 如果弹出 Python API 授权提示，请允许"
    echo "    3. 添加状态栏组件："
    echo "       偏好设置 > Profiles > Session > 启用 Status bar"
    echo "       > Configure Status Bar > 将 'Claude Sessions' 拖入激活区域"
    echo ""
}

# ===========================================================
#  UNINSTALL
# ===========================================================
do_uninstall() {
    # 1. Remove daemon
    info "Removing daemon script..."
    if [ -f "$DAEMON_DEST" ]; then
        rm -f "$DAEMON_DEST"
        ok "Removed $DAEMON_DEST"
    else
        ok "Daemon not found (already removed)"
    fi

    # 2. Unpatch hook script
    info "Removing hook patch..."
    if [ -f "$HOOK_SCRIPT" ] && grep -q "$SENTINEL_BEGIN" "$HOOK_SCRIPT" 2>/dev/null; then
        # Remove everything from sentinel begin to sentinel end (inclusive)
        sed -i '' "/$SENTINEL_BEGIN/,/$SENTINEL_END/d" "$HOOK_SCRIPT"
        # Remove trailing blank line left by the patch
        sed -i '' -e :a -e '/^\n*$/{$d;N;ba' -e '}' "$HOOK_SCRIPT"
        ok "Hook script unpatched: $HOOK_SCRIPT"
    else
        ok "Hook not patched (nothing to remove)"
    fi

    # 3. Cleanup session files
    info "Cleaning up..."
    rm -rf "$SESSION_DIR" 2>/dev/null
    ok "Session files removed"

    echo ""
    echo "============================================"
    echo "  Session Monitor Uninstalled!"
    echo "============================================"
    echo ""
    echo "  The iterm2 Python package was not removed."
    echo "  To remove it: pip3 uninstall iterm2"
    echo ""
    echo "  iTerm2 Python API setting was not changed."
    echo "  The base iterm-status.sh tab colors still work."
    echo ""
    echo "  Restart iTerm2 to complete removal."
    echo ""
}

# ===========================================================
#  STATUS
# ===========================================================
do_status() {
    echo "Claude Code Session Monitor"
    echo ""

    # Daemon
    if [ -f "$DAEMON_DEST" ]; then
        printf '  Daemon:       \033[1;32minstalled\033[0m\n'
    else
        printf '  Daemon:       \033[1;31mnot installed\033[0m\n'
    fi

    # Hook patch
    if [ -f "$HOOK_SCRIPT" ] && grep -q "$SENTINEL_BEGIN" "$HOOK_SCRIPT" 2>/dev/null; then
        printf '  Hook patch:   \033[1;32mapplied\033[0m\n'
    else
        printf '  Hook patch:   \033[1;31mnot applied\033[0m\n'
    fi

    # Python package
    if python3 -c "import iterm2" 2>/dev/null; then
        ver=$(python3 -c "import iterm2; print(iterm2.__version__)" 2>/dev/null || echo "?")
        printf '  iterm2 pkg:   \033[1;32minstalled\033[0m (v%s)\n' "$ver"
    else
        printf '  iterm2 pkg:   \033[1;31mnot installed\033[0m\n'
    fi

    # Python API
    PB="/usr/libexec/PlistBuddy"
    api_enabled=$("$PB" -c "Print :EnableAPIServer" "$ITERM_PLIST" 2>/dev/null || echo "")
    if [ "$api_enabled" = "true" ]; then
        printf '  iTerm2 API:   \033[1;32menabled\033[0m\n'
    else
        printf '  iTerm2 API:   \033[1;31mnot enabled\033[0m\n'
    fi

    # Active sessions
    count=0
    if [ -d "$SESSION_DIR" ]; then
        count=$(find "$SESSION_DIR" -name "*.json" 2>/dev/null | wc -l | tr -d ' ')
    fi
    printf '  Sessions:     %s active\n' "$count"

    echo ""
}

# ===========================================================
#  MAIN
# ===========================================================
cmd="${1:-}"
shift || true

case "$cmd" in
    install)
        do_install
        ;;
    uninstall)
        do_uninstall
        ;;
    status)
        do_status
        ;;
    *)
        usage
        ;;
esac
