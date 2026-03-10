"""Conversation preview screen - view full chat history of a session."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static, Input

from ..data.history import SessionEntry, load_conversation
from rich.markup import escape as markup_escape

from ..utils.format import format_date, truncate_text
from ..utils.i18n import t


class ConversationPane(Widget):
    """Pane for viewing conversation content of a session."""

    can_focus = True

    BINDINGS = [
        Binding("e", "export", "Export"),
        Binding("t", "toggle_thinking", "Toggle Thinking"),
        Binding("home", "scroll_top", "Top", show=False),
        Binding("end", "scroll_bottom", "Bottom", show=False),
    ]

    DEFAULT_CSS = """
    ConversationPane {
        height: 1fr;
        width: 1fr;
    }
    ConversationPane #conv-header {
        height: auto;
        padding: 0 2;
        background: #16213e;
    }
    ConversationPane #conv-scroll {
        height: 1fr;
    }
    ConversationPane .msg-user {
        background: #111827;
        border-left: outer #3b82f6;
        margin: 0 1 1 1;
        padding: 1 2;
    }
    ConversationPane .msg-assistant {
        background: #0f1117;
        border-left: outer #22c55e;
        margin: 0 1 1 1;
        padding: 1 2;
    }
    ConversationPane .msg-tool {
        color: #888;
        margin: 0 1 0 3;
        padding: 0 1;
    }
    ConversationPane .msg-thinking {
        color: #888;
        margin: 0 1 0 3;
        padding: 0 1;
        border-left: dashed #777;
    }
    ConversationPane .msg-role {
        text-style: bold;
        margin-bottom: 1;
    }
    ConversationPane .empty-state {
        text-align: center;
        color: #888;
        padding: 4;
    }
    ConversationPane #conv-search {
        dock: bottom;
        height: 3;
        background: #16213e;
        border-top: solid #2a2a4a;
        padding: 0 2;
        display: none;
    }
    ConversationPane #conv-search.visible {
        display: block;
    }
    """

    class GoBack(Message):
        pass

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._session: Optional[SessionEntry] = None
        self._messages: List[Dict[str, Any]] = []
        self._show_thinking = False
        self._search_visible = False
        # Also support active sessions
        self._active_session = None

    def compose(self) -> ComposeResult:
        yield Static(
            f"[dim]{t('conv_select_hint')}[/]",
            id="conv-header",
        )
        yield VerticalScroll(id="conv-scroll")
        yield Static("", id="conv-search")

    def load_session(self, session: SessionEntry) -> None:
        """Load and display a session's conversation."""
        self._session = session
        self._active_session = None
        self._messages = load_conversation(session.jsonl_path)
        self.run_worker(self._render_conversation())

    def load_active_session(self, cwd: str, project: str, branch: str) -> None:
        """Load from an active session (limited info)."""
        self._session = None
        self._active_session = {"cwd": cwd, "project": project, "branch": branch}

        # Try to find matching JSONL
        import os
        import glob as glob_mod
        projects_dir = os.path.expanduser("~/.claude/projects")
        # Look for the most recently modified JSONL in any matching project dir
        matching_files = []
        for dirname in os.listdir(projects_dir):
            if project.lower() in dirname.lower():
                dirpath = os.path.join(projects_dir, dirname)
                for fname in os.listdir(dirpath):
                    if fname.endswith(".jsonl"):
                        fpath = os.path.join(dirpath, fname)
                        matching_files.append((fpath, os.path.getmtime(fpath)))

        if matching_files:
            matching_files.sort(key=lambda x: x[1], reverse=True)
            self._messages = load_conversation(matching_files[0][0])
        else:
            self._messages = []

        self.run_worker(self._render_conversation())

    async def _render_conversation(self) -> None:
        # Update header
        header = self.query_one("#conv-header", Static)
        if self._session:
            s = self._session
            from ..utils.format import format_tokens, format_cost
            from ..utils.pricing import format_model_name
            usage_parts = [f"{len(self._messages)} {t('msgs')}"]
            if s.total_output_tokens > 0:
                usage_parts.append(
                    f"{format_tokens(s.total_input_tokens)} {t('in_label')} / "
                    f"{format_tokens(s.total_output_tokens)} {t('out_label')}"
                )
                if s.estimated_cost > 0:
                    usage_parts.append(f"[#4ade80]{format_cost(s.estimated_cost)}[/]")
                if s.primary_model:
                    usage_parts.append(f"[dim]{format_model_name(s.primary_model)}[/]")
            usage_str = "    ".join(usage_parts)
            header.update(
                f"[bold white]{markup_escape(s.project_name)}[/]  "
                f"\U0001f33f {markup_escape(s.git_branch or '-')}  "
                f"[dim]{s.session_id[:8]}[/]  "
                f"{usage_str}\n"
                f"[dim]{t('conv_hint')}[/]"
            )
        elif self._active_session:
            a = self._active_session
            header.update(
                f"[bold white]{markup_escape(a['project'])}[/]  "
                f"\U0001f33f {markup_escape(a['branch'] or '-')}  "
                f"{len(self._messages)} {t('msgs')}\n"
                f"[dim]{t('conv_hint_short')}[/]"
            )
        else:
            header.update(f"[dim]{t('no_session_loaded')}[/]")

        # Rebuild messages
        scroll = self.query_one("#conv-scroll", VerticalScroll)
        await scroll.remove_children()

        if not self._messages:
            scroll.mount(Static(
                f"\n\U0001f4ac {t('no_conversation')}\n\n"
                f"{t('session_empty_hint')}",
                classes="empty-state",
            ))
            return

        for msg in self._messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            ts_display = format_date(timestamp) if timestamp else ""

            if role == "user":
                text = self._extract_user_text(content)
                if not text:
                    continue
                scroll.mount(Static(
                    f"[bold white on #1e3a5f] {t('user_role')} [/]  [dim]{ts_display}[/]\n{markup_escape(text)}",
                    classes="msg-user",
                ))

            elif role == "assistant":
                blocks = self._render_assistant_content(content)
                if blocks:
                    scroll.mount(Static(
                        f"[bold white on #1a3a2a] {t('assistant_role')} [/]  [dim]{ts_display}[/]\n{blocks}",
                        classes="msg-assistant",
                    ))

    @staticmethod
    def _truncate(text: str, limit: int) -> str:
        """Truncate text and add indicator if it exceeds the limit."""
        if len(text) <= limit:
            return text
        return text[:limit] + "\n... [truncated]"

    def _extract_user_text(self, content) -> str:
        """Extract plain text from user message content."""
        if isinstance(content, str):
            # Skip meta/system messages
            if content.startswith("<") and "local-command" in content[:50]:
                return ""
            return self._truncate(content, 3000)
        if isinstance(content, list):
            parts = []
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")
                    if text.startswith("<") and "local-command" in text[:50]:
                        continue
                    parts.append(self._truncate(text, 3000))
            return "\n".join(parts)
        return self._truncate(str(content), 3000)

    def _render_assistant_content(self, content) -> str:
        """Render assistant message content as rich text."""
        if isinstance(content, str):
            return self._truncate(content, 5000)

        if not isinstance(content, list):
            return self._truncate(str(content), 5000)

        parts = []
        for block in content:
            if not isinstance(block, dict):
                continue

            btype = block.get("type", "")

            if btype == "text":
                text = block.get("text", "")
                if text:
                    parts.append(markup_escape(self._truncate(text, 5000)))

            elif btype == "tool_use":
                name = block.get("name", "unknown")
                tool_input = block.get("input", {})
                # Show compact tool use summary
                if isinstance(tool_input, dict):
                    first_val = ""
                    for k, v in tool_input.items():
                        first_val = markup_escape(str(v)[:80])
                        break
                    parts.append(f"[dim]\u2514 Tool: {name}({first_val})[/]")
                else:
                    parts.append(f"[dim]\u2514 Tool: {name}[/]")

            elif btype == "tool_result":
                # Skip tool results in compact view
                pass

            elif btype == "thinking":
                if self._show_thinking:
                    text = block.get("thinking", block.get("text", ""))
                    if text:
                        parts.append(f"[dim italic]\U0001f4ad {markup_escape(text[:2000])}[/]")
                else:
                    parts.append(f"[dim]\U0001f4ad [{t('thinking_expand_hint')}][/]")

        return "\n".join(parts) if parts else ""

    def action_go_back(self) -> None:
        self.post_message(self.GoBack())

    def action_export(self) -> None:
        if not self._session:
            self.notify(t("no_session_to_export"), severity="warning")
            return

        import os
        from ..utils.export import export_to_markdown

        output_dir = os.path.expanduser("~/Desktop")
        output_path = os.path.join(
            output_dir,
            f"claude-session-{self._session.session_id[:8]}.md",
        )
        export_to_markdown(
            session_id=self._session.session_id,
            project_name=self._session.project_name,
            git_branch=self._session.git_branch,
            created=self._session.created,
            messages=self._messages,
            output_path=output_path,
        )
        self.notify(f"{t('exported_to')} {output_path}")

    def action_toggle_thinking(self) -> None:
        self._show_thinking = not self._show_thinking
        self.run_worker(self._render_conversation())
        state = t("thinking_shown") if self._show_thinking else t("thinking_hidden")
        self.notify(state)

    def action_scroll_top(self) -> None:
        scroll = self.query_one("#conv-scroll", VerticalScroll)
        scroll.scroll_home()

    def action_scroll_bottom(self) -> None:
        scroll = self.query_one("#conv-scroll", VerticalScroll)
        scroll.scroll_end()
