"""Export conversations to Markdown and JSON formats."""
from __future__ import annotations

import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any


def export_to_markdown(
    session_id: str,
    project_name: str,
    git_branch: str,
    created: str,
    messages: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """Export conversation to Markdown format.

    Args:
        session_id: Session UUID
        project_name: Human-readable project name
        git_branch: Git branch name
        created: ISO date string
        messages: List of parsed conversation messages
        output_path: Path to write the markdown file

    Returns:
        The output file path
    """
    lines = [
        f"# Claude Code Session",
        f"",
        f"- **Session ID:** `{session_id}`",
        f"- **Project:** {project_name}",
        f"- **Branch:** {git_branch}",
        f"- **Created:** {created}",
        f"- **Messages:** {len(messages)}",
        f"- **Exported:** {datetime.now().isoformat()}",
        f"",
        f"---",
        f"",
    ]

    for msg in messages:
        role = msg.get("role", "unknown")
        timestamp = msg.get("timestamp", "")
        content = msg.get("content", "")

        if role == "user":
            lines.append(f"## User")
            if timestamp:
                lines.append(f"*{timestamp}*")
            lines.append(f"")
            if isinstance(content, str):
                lines.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        lines.append(block.get("text", ""))
            lines.append(f"")

        elif role == "assistant":
            lines.append(f"## Assistant")
            if timestamp:
                lines.append(f"*{timestamp}*")
            lines.append(f"")
            if isinstance(content, str):
                lines.append(content)
            elif isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        btype = block.get("type", "")
                        if btype == "text":
                            lines.append(block.get("text", ""))
                        elif btype == "tool_use":
                            tool_name = block.get("name", "unknown")
                            tool_input = block.get("input", {})
                            lines.append(f"**Tool: `{tool_name}`**")
                            input_str = json.dumps(tool_input, indent=2, ensure_ascii=False)
                            if len(input_str) > 1000:
                                input_str = input_str[:1000] + "\n... [truncated]"
                            lines.append(f"```json\n{input_str}\n```")
                        elif btype == "thinking":
                            text = block.get("thinking", block.get("text", ""))
                            if text:
                                lines.append(f"<details><summary>Thinking</summary>\n")
                                lines.append(text[:2000])
                                if len(text) > 2000:
                                    lines.append("\n... [truncated]")
                                lines.append(f"\n</details>")
            lines.append(f"")

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return output_path


def export_to_json(
    session_id: str,
    project_name: str,
    git_branch: str,
    created: str,
    messages: List[Dict[str, Any]],
    output_path: str,
) -> str:
    """Export conversation to structured JSON format."""
    data = {
        "session_id": session_id,
        "project": project_name,
        "git_branch": git_branch,
        "created": created,
        "exported": datetime.now().isoformat(),
        "message_count": len(messages),
        "messages": messages,
    }
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return output_path
