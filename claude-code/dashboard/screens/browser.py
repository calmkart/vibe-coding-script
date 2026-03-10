"""Session History Browser - dual-pane view for browsing all sessions."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.events import DescendantFocus
from textual.message import Message
from textual.screen import ModalScreen
from textual.widget import Widget
from textual.widgets import DataTable, Static, ListItem, ListView, Label, Input

from ..data.history import (
    ProjectInfo, SessionEntry,
    discover_all_projects, load_conversation, delete_session,
)
from rich.markup import escape as markup_escape

from ..utils.format import format_date, format_filesize, format_cost, truncate_text
from ..utils.i18n import t


class DeleteConfirmScreen(ModalScreen[bool]):
    """Modal confirmation dialog for deleting a session."""

    DEFAULT_CSS = """
    DeleteConfirmScreen {
        align: center middle;
    }
    DeleteConfirmScreen #confirm-container {
        width: 60;
        height: auto;
        background: #16213e;
        border: solid #ef4444;
        padding: 1 2;
    }
    DeleteConfirmScreen #confirm-buttons {
        layout: horizontal;
        height: 3;
        margin-top: 1;
        align-horizontal: center;
    }
    DeleteConfirmScreen .confirm-btn {
        width: auto;
        min-width: 12;
        margin: 0 1;
        text-align: center;
        padding: 0 2;
        height: 3;
        content-align: center middle;
    }
    DeleteConfirmScreen .confirm-btn:focus {
        text-style: bold reverse;
    }
    DeleteConfirmScreen #btn-cancel {
        background: #2a2a4a;
    }
    DeleteConfirmScreen #btn-confirm {
        background: #7f1d1d;
        color: #fca5a5;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("enter", "confirm_focused", "Confirm"),
    ]

    def __init__(self, session_id: str):
        super().__init__()
        self._session_id = session_id

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-container"):
            yield Static(
                f"[bold #ef4444]{t('delete_session_title')}[/]\n\n"
                f"{t('delete_confirm')} [bold]{self._session_id[:8]}[/]?\n"
                f"{t('delete_warning')}"
            )
            with Horizontal(id="confirm-buttons"):
                cancel = Static(f"[bold]{t('cancel')}[/]  (Esc)", id="btn-cancel", classes="confirm-btn")
                cancel.can_focus = True
                yield cancel
                confirm = Static(f"[bold]{t('delete')}[/]  (Enter)", id="btn-confirm", classes="confirm-btn")
                confirm.can_focus = True
                yield confirm

    def on_mount(self) -> None:
        self.query_one("#btn-cancel").focus()

    def action_cancel(self) -> None:
        self.dismiss(False)

    def action_confirm_focused(self) -> None:
        focused = self.app.focused
        if focused and focused.id == "btn-confirm":
            self.dismiss(True)
        elif focused and focused.id == "btn-cancel":
            self.dismiss(False)
        else:
            # Enter with no focus = cancel
            self.dismiss(False)


class SessionBrowserPane(Widget):
    """Dual-pane session history browser."""

    can_focus = True

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False, priority=True),
        Binding("down", "cursor_down", "Down", show=False, priority=True),
        Binding("left", "focus_projects", "Projects", show=False, priority=True),
        Binding("right", "focus_sessions", "Sessions", show=False, priority=True),
        Binding("enter", "view_conversation", "View"),
        Binding("r", "resume_session", "Resume"),
        Binding("delete", "delete_session", "Delete"),
        Binding("backspace", "delete_session", "Delete", show=False),
        Binding("e", "export_session", "Export"),
        Binding("s", "cycle_sort", "Sort"),
    ]

    DEFAULT_CSS = """
    SessionBrowserPane {
        height: 1fr;
        width: 1fr;
        layout: horizontal;
    }
    SessionBrowserPane #browser-projects {
        width: 30;
        border-right: solid #2a2a4a;
        background: #0f1117;
    }
    SessionBrowserPane #browser-sessions {
        width: 1fr;
        background: #1a1a2e;
    }
    SessionBrowserPane #project-header {
        height: auto;
        padding: 0 2;
        background: #16213e;
    }
    SessionBrowserPane #session-header {
        height: auto;
        padding: 0 2;
        background: #16213e;
    }
    SessionBrowserPane #project-scroll {
        height: 1fr;
    }
    SessionBrowserPane #session-scroll {
        height: 1fr;
    }
    SessionBrowserPane .project-item {
        padding: 0 2;
        height: 2;
    }
    SessionBrowserPane .project-item:focus {
        background: #1a1f2e;
    }
    SessionBrowserPane .project-item.--highlight {
        background: #1a1f2e;
    }
    """

    class ViewConversation(Message):
        def __init__(self, session: SessionEntry):
            super().__init__()
            self.session = session

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._projects: list[ProjectInfo] = []
        self._selected_project_idx = 0
        self._selected_session_idx = 0
        self._sort_mode = "date"  # date, messages, size
        self._focus_in_projects = True  # Track which pane has focus

    def compose(self) -> ComposeResult:
        with Horizontal():
            with Vertical(id="browser-projects"):
                yield Static(f"[bold]{t('projects')}[/]", id="project-header")
                yield VerticalScroll(id="project-scroll")
            with Vertical(id="browser-sessions"):
                yield Static(f"[bold]{t('sessions')}[/]", id="session-header")
                yield VerticalScroll(id="session-scroll")

    def on_mount(self) -> None:
        self._load_projects_initial()

    def _load_projects_initial(self) -> None:
        """Initial load on mount - scroll containers are empty so no async needed."""
        self._projects = discover_all_projects()
        self._mount_project_list()
        if self._projects:
            self._mount_session_cards(0)

    def _mount_project_list(self, focus_first: bool = False) -> None:
        """Mount project items into the project scroll (assumes empty container)."""
        scroll = self.query_one("#project-scroll", VerticalScroll)

        header = self.query_one("#project-header", Static)
        header.update(
            f"[bold]{t('projects')}[/] ({len(self._projects)})\n"
            f"[dim]{t('browser_hint_projects')}[/]"
        )

        for i, project in enumerate(self._projects):
            display_name = project.name if len(project.name) <= 24 else project.name[:23] + "\u2026"
            total_cost = sum(s.estimated_cost for s in project.sessions)
            cost_str = f"[#4ade80]{format_cost(total_cost)}[/]" if total_cost > 0 else ""
            item = Static(
                f"[bold white]{markup_escape(display_name)}[/]\n"
                f"[dim]{project.session_count} {t('n_sessions')}[/]  {cost_str}",
                classes="project-item",
                id=f"project-{i}",
            )
            item.can_focus = True
            scroll.mount(item)

        if focus_first and self._projects:
            items = scroll.query(".project-item")
            if items:
                items.first().focus()

    def _mount_session_cards(self, project_idx: int) -> None:
        """Mount session cards into the session scroll (assumes empty container)."""
        if project_idx < 0 or project_idx >= len(self._projects):
            return

        self._selected_project_idx = project_idx
        project = self._projects[project_idx]

        sessions = list(project.sessions)
        if self._sort_mode == "messages":
            sessions.sort(key=lambda s: s.message_count, reverse=True)
        elif self._sort_mode == "size":
            sessions.sort(key=lambda s: s.file_size, reverse=True)

        header = self.query_one("#session-header", Static)
        sort_display = t(f"sort_{self._sort_mode}")
        header.update(
            f"[bold]{markup_escape(project.name)}[/] ({len(sessions)} {t('n_sessions')})    "
            f"{t('sort_label')}: {sort_display}\n"
            f"[dim]{t('browser_hint_sessions')}[/]"
        )

        scroll = self.query_one("#session-scroll", VerticalScroll)

        if not sessions:
            scroll.mount(Static(f"[dim]{t('no_sessions_in_project')}[/]", classes="empty-state"))
            return

        from ..widgets.session_card import HistorySessionCard
        for i, session in enumerate(sessions):
            card = HistorySessionCard(
                session_id=session.session_id,
                project_name=session.project_name,
                first_prompt=session.first_prompt,
                summary=session.summary,
                message_count=session.message_count,
                created=session.created,
                modified=session.modified,
                git_branch=session.git_branch,
                file_size=session.file_size,
                total_input_tokens=session.total_input_tokens,
                total_output_tokens=session.total_output_tokens,
                estimated_cost=session.estimated_cost,
                primary_model=session.primary_model,
                id=f"session-{i}",
            )
            scroll.mount(card)

    async def _show_project_sessions(self, project_idx: int) -> None:
        """Async version: remove existing cards then mount new ones."""
        scroll = self.query_one("#session-scroll", VerticalScroll)
        await scroll.remove_children()
        self._mount_session_cards(project_idx)

    def on_descendant_focus(self, event: DescendantFocus) -> None:
        """Track which pane has focus and update sessions on project change."""
        widget = event.widget
        if not widget or not hasattr(widget, 'id') or not widget.id:
            return
        if widget.id.startswith("project-"):
            self._focus_in_projects = True
            try:
                idx = int(widget.id.split("-")[1])
                if idx != self._selected_project_idx:
                    self.run_worker(self._show_project_sessions(idx), exclusive=True)
            except (ValueError, IndexError):
                pass
        elif widget.id.startswith("session-"):
            self._focus_in_projects = False

    # --- Arrow key navigation ---

    def action_cursor_down(self) -> None:
        """Move focus to the next item in current pane."""
        if self._focus_in_projects:
            self._navigate_projects(1)
        else:
            self._navigate_sessions(1)

    def action_cursor_up(self) -> None:
        """Move focus to the previous item in current pane, or to tab bar if at first."""
        if self._focus_in_projects:
            self._navigate_projects(-1)
        else:
            self._navigate_sessions(-1)

    def _navigate_projects(self, direction: int) -> None:
        """Navigate project items up/down."""
        scroll = self.query_one("#project-scroll", VerticalScroll)
        items = list(scroll.query(".project-item"))
        if not items:
            return
        focused = self.app.focused
        for i, item in enumerate(items):
            if item is focused:
                new_idx = i + direction
                if 0 <= new_idx < len(items):
                    items[new_idx].focus()
                return
        # Not focused on a project, focus first/last
        items[0 if direction > 0 else -1].focus()

    def _navigate_sessions(self, direction: int) -> None:
        """Navigate session cards up/down."""
        from ..widgets.session_card import HistorySessionCard
        scroll = self.query_one("#session-scroll", VerticalScroll)
        cards = list(scroll.query("HistorySessionCard"))
        if not cards:
            return
        focused = self.app.focused
        for i, card in enumerate(cards):
            if card is focused:
                new_idx = i + direction
                if 0 <= new_idx < len(cards):
                    cards[new_idx].focus()
                return
        cards[0 if direction > 0 else -1].focus()

    def action_focus_projects(self) -> None:
        """Switch focus to the project pane (left arrow)."""
        scroll = self.query_one("#project-scroll", VerticalScroll)
        items = list(scroll.query(".project-item"))
        if items:
            idx = min(self._selected_project_idx, len(items) - 1)
            items[idx].focus()
            self._focus_in_projects = True

    def action_focus_sessions(self) -> None:
        """Switch focus to the session pane (right arrow)."""
        from ..widgets.session_card import HistorySessionCard
        scroll = self.query_one("#session-scroll", VerticalScroll)
        cards = list(scroll.query("HistorySessionCard"))
        if cards:
            cards[0].focus()
            self._focus_in_projects = False

    # --- Actions ---

    def _get_selected_session(self) -> SessionEntry | None:
        """Get the currently focused session entry."""
        from ..widgets.session_card import HistorySessionCard
        focused = self.app.focused
        if isinstance(focused, HistorySessionCard) and focused.id:
            try:
                idx = int(focused.id.split("-")[1])
                project = self._projects[self._selected_project_idx]
                sessions = list(project.sessions)
                if self._sort_mode == "messages":
                    sessions.sort(key=lambda s: s.message_count, reverse=True)
                elif self._sort_mode == "size":
                    sessions.sort(key=lambda s: s.file_size, reverse=True)
                if 0 <= idx < len(sessions):
                    return sessions[idx]
            except (ValueError, IndexError):
                pass
        return None

    def action_view_conversation(self) -> None:
        session = self._get_selected_session()
        if session:
            self.post_message(self.ViewConversation(session))

    def action_resume_session(self) -> None:
        session = self._get_selected_session()
        if session:
            from ..utils.iterm import resume_session_in_iterm
            resume_session_in_iterm(session.project_path, session.session_id)
            self.notify(f"{t('resuming_session')} {session.session_id[:8]} {t('in_new_tab')}")

    def action_delete_session(self) -> None:
        session = self._get_selected_session()
        if not session:
            return

        def _on_confirm(result: bool) -> None:
            if result:
                if delete_session(session):
                    self.notify(f"{t('deleted_session')} {session.session_id[:8]}")
                    self.run_worker(self._async_reload_projects(), exclusive=True)
                else:
                    self.notify(t("failed_to_delete"), severity="error")

        self.app.push_screen(
            DeleteConfirmScreen(session.session_id),
            callback=_on_confirm,
        )

    def action_export_session(self) -> None:
        session = self._get_selected_session()
        if session:
            import os
            from ..data.history import load_conversation
            from ..utils.export import export_to_markdown

            messages = load_conversation(session.jsonl_path)
            output_dir = os.path.expanduser("~/Desktop")
            output_path = os.path.join(
                output_dir,
                f"claude-session-{session.session_id[:8]}.md",
            )
            export_to_markdown(
                session_id=session.session_id,
                project_name=session.project_name,
                git_branch=session.git_branch,
                created=session.created,
                messages=messages,
                output_path=output_path,
            )
            self.notify(f"{t('exported_to')} {output_path}")

    async def action_cycle_sort(self) -> None:
        modes = ["date", "messages", "size"]
        idx = modes.index(self._sort_mode)
        self._sort_mode = modes[(idx + 1) % len(modes)]
        await self._show_project_sessions(self._selected_project_idx)
        self.notify(f"{t('sort_notify')}: {t(f'sort_{self._sort_mode}')}")

    async def _async_reload_projects(self) -> None:
        """Async reload: clear both panes and rebuild."""
        project_scroll = self.query_one("#project-scroll", VerticalScroll)
        session_scroll = self.query_one("#session-scroll", VerticalScroll)
        await project_scroll.remove_children()
        await session_scroll.remove_children()
        self._projects = discover_all_projects()
        self._mount_project_list(focus_first=True)
        if self._projects:
            self._mount_session_cards(0)

    def refresh_data(self) -> None:
        """Reload all project data."""
        self.run_worker(self._async_reload_projects(), exclusive=True)
