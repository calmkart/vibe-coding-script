#!/bin/bash
set -euo pipefail

# ============================================================
#  fix-review skill installer
#
#  Installs the fix-review skill to the current project's
#  .claude/skills/fix-review/ directory, or to a global
#  location (~/.claude/skills/fix-review/).
#
#  Usage:
#    ./setup.sh install [--global]
#    ./setup.sh uninstall [--global]
#    ./setup.sh status
# ============================================================

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_NAME="fix-review"

info()  { printf '\033[1;34m[INFO]\033[0m  %s\n' "$1"; }
ok()    { printf '\033[1;32m[  OK]\033[0m  %s\n' "$1"; }
warn()  { printf '\033[1;33m[WARN]\033[0m  %s\n' "$1"; }
err()   { printf '\033[1;31m[ ERR]\033[0m  %s\n' "$1"; }

get_target_dir() {
    local global="${1:-false}"
    if [ "$global" = "true" ]; then
        echo "$HOME/.claude/skills/$SKILL_NAME"
    else
        # Find git root of current working directory
        local git_root
        git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
        if [ -z "$git_root" ]; then
            err "Not in a git repository. Use --global to install globally."
            exit 1
        fi
        echo "$git_root/.claude/skills/$SKILL_NAME"
    fi
}

do_install() {
    local global="false"
    while [ $# -gt 0 ]; do
        case "$1" in
            --global) global="true"; shift ;;
            *) shift ;;
        esac
    done

    local target_dir
    target_dir="$(get_target_dir "$global")"

    mkdir -p "$target_dir"
    cp "$SCRIPT_DIR/SKILL.md" "$target_dir/SKILL.md"

    if [ "$global" = "true" ]; then
        ok "$SKILL_NAME skill installed to $target_dir"
        info "Available globally via /fix-review in Claude Code"
    else
        ok "$SKILL_NAME skill installed to $target_dir"
        info "Available via /fix-review in this project"
    fi
}

do_uninstall() {
    local global="false"
    while [ $# -gt 0 ]; do
        case "$1" in
            --global) global="true"; shift ;;
            *) shift ;;
        esac
    done

    local target_dir
    target_dir="$(get_target_dir "$global")"

    if [ -f "$target_dir/SKILL.md" ]; then
        rm -f "$target_dir/SKILL.md"
        rmdir "$target_dir" 2>/dev/null || true
        ok "$SKILL_NAME skill removed from $target_dir"
    else
        warn "$SKILL_NAME skill not found at $target_dir (skipped)"
    fi
}

do_status() {
    local global_dir="$HOME/.claude/skills/$SKILL_NAME"

    if [ -f "$global_dir/SKILL.md" ]; then
        printf '  %s: \033[1;32m● installed (global)\033[0m  %s\n' "$SKILL_NAME" "$global_dir"
    else
        # Try current project
        local git_root
        git_root="$(git rev-parse --show-toplevel 2>/dev/null || true)"
        if [ -n "$git_root" ] && [ -f "$git_root/.claude/skills/$SKILL_NAME/SKILL.md" ]; then
            printf '  %s: \033[1;32m● installed (project)\033[0m  %s\n' "$SKILL_NAME" "$git_root/.claude/skills/$SKILL_NAME"
        else
            printf '  %s: \033[1;31m○ not installed\033[0m\n' "$SKILL_NAME"
        fi
    fi
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
    *)
        cat <<EOF
fix-review skill installer

Usage:
  $(basename "$0") install [--global]    Install skill (project or global)
  $(basename "$0") uninstall [--global]  Remove skill
  $(basename "$0") status               Show install status

Options:
  --global    Install to ~/.claude/skills/ (available in all projects)
              Default: install to current project's .claude/skills/
EOF
        exit 1
        ;;
esac
