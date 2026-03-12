#!/bin/bash
set -euo pipefail

# ============================================================
#  Claude Code × iTerm2  One-Click Setup
#
#  Orchestrator that delegates to feature-specific installers.
#
#  Usage:
#    ./setup.sh install [feature] [--lang zh]
#    ./setup.sh uninstall [feature]
#    ./setup.sh status
#
#  Features: auto-approve, iterm-status, iterm-monitor, dashboard, skills/fix-review
#  Omit feature name to install/uninstall all.
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FEATURES=("auto-approve" "iterm-status" "iterm-monitor" "dashboard" "skills/fix-review")

info()  { printf '\033[1;34m[INFO]\033[0m  %s\n' "$1"; }
ok()    { printf '\033[1;32m[  OK]\033[0m  %s\n' "$1"; }
warn()  { printf '\033[1;33m[WARN]\033[0m  %s\n' "$1"; }
err()   { printf '\033[1;31m[ ERR]\033[0m  %s\n' "$1"; }

usage() {
    cat <<EOF
Claude Code × iTerm2 One-Click Setup

Usage:
  $(basename "$0") install [feature] [--lang zh]   Install (all or specific)
  $(basename "$0") uninstall [feature]              Uninstall (all or specific)
  $(basename "$0") status                           Show current state

Features:
  auto-approve    Auto-approve Bash commands (no manual confirmation)
  iterm-status    iTerm2 tab color & title status indicator
  iterm-monitor   Multi-session dashboard (badges, status bar, popover)
  dashboard       Terminal TUI dashboard for session management
  skills/fix-review  Skill: auto-fix GitLab MR code review comments

Omit feature name to install/uninstall all features.

Examples:
  $(basename "$0") install                     Install all (English)
  $(basename "$0") install --lang zh           Install all (Chinese)
  $(basename "$0") install iterm-status        Install only tab indicator
  $(basename "$0") uninstall iterm-monitor     Uninstall only dashboard
  $(basename "$0") install skills/fix-review   Install only fix-review skill
EOF
    exit 1
}

is_valid_feature() {
    local name="$1"
    for f in "${FEATURES[@]}"; do
        [ "$f" = "$name" ] && return 0
    done
    return 1
}

# ===========================================================
#  INSTALL
# ===========================================================
do_install() {
    local targets=()
    local extra_args=()

    # Parse: first non-flag arg is feature name, rest are passed through
    while [ $# -gt 0 ]; do
        case "$1" in
            --lang)
                [ $# -ge 2 ] || { err "Missing value for --lang"; usage; }
                extra_args+=("--lang" "$2"); shift 2 ;;
            --lang=*)
                extra_args+=("--lang" "${1#--lang=}"); shift ;;
            -*)
                err "Unknown option: $1"; usage ;;
            *)
                if is_valid_feature "$1"; then
                    targets+=("$1")
                else
                    err "Unknown feature: $1"
                    echo "  Available: ${FEATURES[*]}"
                    exit 1
                fi
                shift ;;
        esac
    done

    # Default: all features
    if [ ${#targets[@]} -eq 0 ]; then
        targets=("${FEATURES[@]}")
    fi

    echo ""
    echo "  Claude Code × iTerm2 Setup"
    echo "  ==========================="
    echo ""

    # Pre-flight
    info "Checking dependencies..."
    local missing=0
    local needs_macos=0
    for target in "${targets[@]}"; do
        case "$target" in
            auto-approve|iterm-status|iterm-monitor|dashboard) needs_macos=1 ;;
        esac
    done
    if [ "$needs_macos" -eq 1 ] && [[ "$(uname)" != "Darwin" ]]; then err "macOS is required for $target"; exit 1; fi

    for target in "${targets[@]}"; do
        case "$target" in
            auto-approve)
                command -v jq &>/dev/null || { err "jq not found — brew install jq"; missing=1; } ;;
            iterm-status|iterm-monitor)
                [ -f "$HOME/Library/Preferences/com.googlecode.iterm2.plist" ] || { err "iTerm2 not found"; missing=1; } ;;
            dashboard)
                command -v python3 &>/dev/null || { err "python3 not found"; missing=1; } ;;
            skills/*)
                command -v curl &>/dev/null || { err "curl not found"; missing=1; } ;;
        esac
        if [ "$target" = "iterm-monitor" ]; then
            command -v python3 &>/dev/null || { err "python3 not found"; missing=1; }
        fi
    done
    [ "$missing" -eq 1 ] && { echo ""; err "Please install missing dependencies and re-run."; exit 1; }
    ok "Dependencies OK"
    echo ""

    # Install each target
    for target in "${targets[@]}"; do
        local script="$SCRIPT_DIR/$target/setup.sh"
        if [ ! -f "$script" ]; then
            err "$target/setup.sh not found at $script"
            continue
        fi
        info "Installing $target..."
        bash "$script" install "${extra_args[@]+"${extra_args[@]}"}"
        echo ""
    done

    # Summary
    echo "  ============================================"
    echo "  All done!"
    echo "  ============================================"
    echo ""

    # Restart prompt
    local has_iterm=0
    for target in "${targets[@]}"; do
        [[ "$target" == iterm-* ]] && has_iterm=1
    done

    if [ "$has_iterm" -eq 1 ] && [ -t 0 ]; then
        # Detect language from extra_args
        local lang="en"
        for i in "${!extra_args[@]}"; do
            if [ "${extra_args[$i]}" = "--lang" ]; then
                lang="${extra_args[$((i+1))]:-en}"
            fi
        done

        if [ "$lang" = "zh" ]; then
            printf '  需要重启 iTerm2 使配置生效。现在重启？(y/n) '
        else
            printf '  iTerm2 needs to restart. Restart now? (y/n) '
        fi
        read -r answer
        if [[ "$answer" =~ ^[Yy] ]]; then
            echo ""
            info "Restarting iTerm2..."
            (sleep 1 && open -a iTerm2) &
            osascript -e 'tell application "iTerm2" to quit' 2>/dev/null || true
            exit 0
        fi

        echo ""
        if [ "$lang" = "zh" ]; then
            echo "  ⚠️  请手动重启 iTerm2"
            echo ""
            echo "  首次使用需手动操作（仅一次）："
            echo "    1. 重启后如果弹出 Python API 授权提示 → 点允许"
            echo "    2. 添加状态栏组件："
            echo "       偏好设置 > Profiles > Session > 启用 Status bar"
            echo "       > Configure Status Bar > 将 'Claude Sessions' 拖入激活区域"
        else
            echo "  ⚠️  Please restart iTerm2 manually"
            echo ""
            echo "  First-time manual steps (one-time only):"
            echo "    1. After restart, allow Python API connection if prompted"
            echo "    2. Add status bar component:"
            echo "       Preferences > Profiles > Session > Enable Status bar"
            echo "       > Configure Status Bar > drag 'Claude Sessions' to active area"
        fi
        echo ""
    fi
}

# ===========================================================
#  UNINSTALL
# ===========================================================
do_uninstall() {
    local targets=()

    while [ $# -gt 0 ]; do
        case "$1" in
            -*)  err "Unknown option: $1"; usage ;;
            *)
                if is_valid_feature "$1"; then
                    targets+=("$1")
                else
                    err "Unknown feature: $1"; exit 1
                fi
                shift ;;
        esac
    done

    if [ ${#targets[@]} -eq 0 ]; then
        targets=("${FEATURES[@]}")
    fi

    echo ""
    echo "  Removing features..."
    echo ""

    # Uninstall in reverse order (monitor before status)
    for (( i=${#targets[@]}-1; i>=0; i-- )); do
        local target="${targets[$i]}"
        local script="$SCRIPT_DIR/$target/setup.sh"
        if [ ! -f "$script" ]; then
            warn "$target/setup.sh not found (skipped)"
            continue
        fi
        info "Uninstalling $target..."
        bash "$script" uninstall
        echo ""
    done

    echo "  ============================================"
    echo "  Done! Please restart iTerm2."
    echo "  ============================================"
    echo ""
}

# ===========================================================
#  STATUS
# ===========================================================
do_status() {
    echo ""
    echo "  Claude Code × iTerm2 Status"
    echo "  ============================"
    echo ""

    for target in "${FEATURES[@]}"; do
        local script="$SCRIPT_DIR/$target/setup.sh"
        if [ -f "$script" ]; then
            bash "$script" status
        else
            printf '  %s: \033[1;31mnot found\033[0m\n' "$target"
        fi
    done
}

# ===========================================================
#  MAIN
# ===========================================================
cmd="${1:-}"
shift || true

case "$cmd" in
    install)   do_install "$@" ;;
    uninstall) do_uninstall "$@" ;;
    status)    do_status ;;
    *)         usage ;;
esac
