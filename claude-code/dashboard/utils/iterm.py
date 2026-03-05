"""iTerm2 AppleScript integration for tab jumping and session operations."""
from __future__ import annotations

import subprocess
from typing import Optional


def jump_to_iterm_tab(tty: str) -> bool:
    """Activate the iTerm2 tab matching the given TTY.

    Returns True if the tab was found and activated.
    """
    script = f'''
    tell application "iTerm2"
        activate
        repeat with w in windows
            repeat with t in tabs of w
                repeat with s in sessions of t
                    if tty of s is "{tty}" then
                        select t
                        select s
                        return true
                    end if
                end repeat
            end repeat
        end repeat
    end tell
    return false
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return "true" in result.stdout.lower()
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def resume_session_in_iterm(project_path: str, session_id: str) -> bool:
    """Open a new iTerm2 tab and resume a Claude Code session.

    Returns True if the command was sent successfully.
    """
    cmd = f'cd "{project_path}" && claude --resume {session_id}'
    script = f'''
    tell application "iTerm2"
        activate
        tell current window
            create tab with default profile
            tell current session
                write text "{cmd}"
            end tell
        end tell
    end tell
    '''
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False


def open_new_session_in_iterm(project_path: str, prompt: Optional[str] = None) -> bool:
    """Open a new iTerm2 tab and start a new Claude Code session."""
    cmd = f'cd "{project_path}" && claude'
    if prompt:
        # Escape quotes in prompt
        safe_prompt = prompt.replace('"', '\\"').replace("'", "'\\''")
        cmd = f'cd "{project_path}" && claude -p "{safe_prompt}"'

    script = f'''
    tell application "iTerm2"
        activate
        tell current window
            create tab with default profile
            tell current session
                write text "{cmd}"
            end tell
        end tell
    end tell
    '''
    try:
        subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return True
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return False
