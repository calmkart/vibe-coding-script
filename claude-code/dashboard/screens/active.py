"""Active Sessions screen - real-time view of running Claude Code sessions."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import VerticalScroll
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Static

from ..data.sessions import ActiveSession, read_active_sessions, active_session_summary
from ..widgets.session_card import ActiveSessionCard
from ..utils.format import format_age
from ..utils.i18n import t


class ActiveSessionsPane(Widget):
    """Pane showing all currently active Claude Code sessions."""

    can_focus = True

    BINDINGS = [
        Binding("up", "cursor_up", "Up", show=False, priority=True),
        Binding("down", "cursor_down", "Down", show=False, priority=True),
        Binding("enter", "view_conversation", "View"),
        Binding("ctrl+g", "jump_to_tab", "Jump to Tab"),
        Binding("r", "resume_session", "Resume"),
    ]

    DEFAULT_CSS = """
    ActiveSessionsPane {
        height: 1fr;
        width: 1fr;
    }
    ActiveSessionsPane #active-header {
        height: auto;
        background: #16213e;
        padding: 0 2;
    }
    ActiveSessionsPane #active-scroll {
        height: 1fr;
    }
    ActiveSessionsPane .empty-state {
        text-align: center;
        color: #888;
        padding: 4;
    }
    """

    class ViewConversation(Message):
        def __init__(self, session: ActiveSession):
            super().__init__()
            self.session = session

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._sessions: list[ActiveSession] = []
        self._selected_index = 0
        self._last_session_data: list[tuple] = []

    def _sessions_equal(self, old: list[ActiveSession], new: list[ActiveSession]) -> bool:
        """Compare old and new session lists to detect changes."""
        if len(old) != len(new):
            return False
        for a, b in zip(old, new):
            if (a.tty, a.pid, a.status, a.project, a.branch, a.worktree, a.cwd) != \
               (b.tty, b.pid, b.status, b.project, b.branch, b.worktree, b.cwd):
                return False
        return True

    def compose(self) -> ComposeResult:
        yield Static("", id="active-header")
        yield VerticalScroll(id="active-scroll")

    def on_mount(self) -> None:
        self._initial_refresh()

    def _update_header(self, sessions: list[ActiveSession]) -> None:
        """Update the header text with session counts."""
        counts = active_session_summary(sessions)
        total = len(sessions)
        badges = []
        if counts["working"]:
            badges.append(f"[#4ade80]\u25c9 {counts['working']} {t('working')}[/]")
        if counts["attention"]:
            badges.append(f"[#fbbf24]\u23f8 {counts['attention']} {t('attention')}[/]")
        if counts["done"]:
            badges.append(f"[#60a5fa]\u2713 {counts['done']} {t('done')}[/]")
        status_str = "  ".join(badges) if badges else f"[dim]{t('active_no_sessions')}[/]"

        header = self.query_one("#active-header", Static)
        header.update(
            f"[bold white]{t('active_sessions')}[/] ({total})    {status_str}\n"
            f"[dim]{t('active_hint')}[/]"
        )

    def _mount_session_cards(self, sessions: list[ActiveSession]) -> None:
        """Mount session cards into empty scroll container."""
        scroll = self.query_one("#active-scroll", VerticalScroll)

        if not sessions:
            scroll.mount(Static(
                f"\n\U0001f916 {t('active_empty')}\n\n"
                f"{t('active_empty_hint')}",
                classes="empty-state",
            ))
            return

        for i, session in enumerate(sessions):
            card = ActiveSessionCard(
                tty=session.tty,
                pid=session.pid,
                status=session.status,
                project=session.project,
                branch=session.branch,
                worktree=session.worktree,
                cwd=session.cwd,
                timestamp=session.timestamp,
                total_input_tokens=session.total_input_tokens,
                total_output_tokens=session.total_output_tokens,
                estimated_cost=session.estimated_cost,
                primary_model=session.primary_model,
                id=f"active-card-{i}",
            )
            scroll.mount(card)

    def _initial_refresh(self) -> None:
        """Initial load on mount - scroll is empty, no async needed."""
        new_sessions = read_active_sessions()
        self._sessions = new_sessions
        self._update_header(new_sessions)
        self._mount_session_cards(new_sessions)

    async def _async_refresh(self, allow_focus: bool = True) -> None:
        """Async refresh: remove old children then mount new ones."""
        new_sessions = read_active_sessions()
        self._update_header(new_sessions)

        if self._sessions_equal(self._sessions, new_sessions):
            return

        focused_id = None
        if allow_focus:
            focused = self.app.focused
            if isinstance(focused, ActiveSessionCard) and focused.id:
                focused_id = focused.id

        self._sessions = new_sessions

        scroll = self.query_one("#active-scroll", VerticalScroll)
        await scroll.remove_children()
        self._mount_session_cards(new_sessions)

        if not allow_focus:
            return

        if focused_id:
            restored = scroll.query(f"#{focused_id}")
            if restored:
                restored.first().focus()
                return

        if self._sessions:
            self._selected_index = 0
            first_card = scroll.query("#active-card-0")
            if first_card:
                first_card.first().focus()

    def update_sessions(self, allow_focus: bool = True) -> None:
        """Called by the app's polling timer."""
        self.run_worker(self._async_refresh(allow_focus=allow_focus), exclusive=True)

    def _get_focusable_cards(self):
        """Return all focusable session cards in order."""
        scroll = self.query_one("#active-scroll", VerticalScroll)
        return list(scroll.query("ActiveSessionCard"))

    def action_cursor_down(self) -> None:
        """Move focus to the next session card."""
        cards = self._get_focusable_cards()
        if not cards:
            return
        focused = self.app.focused
        for i, card in enumerate(cards):
            if card is focused and i + 1 < len(cards):
                cards[i + 1].focus()
                return
        # Nothing focused yet, focus first
        cards[0].focus()

    def action_cursor_up(self) -> None:
        """Move focus to the previous session card."""
        cards = self._get_focusable_cards()
        if not cards:
            return
        focused = self.app.focused
        for i, card in enumerate(cards):
            if card is focused:
                if i > 0:
                    cards[i - 1].focus()
                return
        # Nothing focused yet, focus last
        cards[-1].focus()

    def _get_selected_session(self) -> ActiveSession | None:
        """Get the currently focused session."""
        focused = self.app.focused
        if isinstance(focused, ActiveSessionCard):
            for i, session in enumerate(self._sessions):
                card_id = f"active-card-{i}"
                if focused.id == card_id:
                    return session
        return self._sessions[0] if self._sessions else None

    def action_jump_to_tab(self) -> None:
        session = self._get_selected_session()
        if session:
            from ..utils.iterm import jump_to_iterm_tab
            jump_to_iterm_tab(session.tty)
            self.notify(f"{t('jumping_to')} {session.project} ({session.tty_short})")

    def action_resume_session(self) -> None:
        session = self._get_selected_session()
        if session:
            from ..utils.iterm import jump_to_iterm_tab
            jump_to_iterm_tab(session.tty)
            self.notify(f"{t('switched_to')} {session.project}")

    def action_view_conversation(self) -> None:
        session = self._get_selected_session()
        if session:
            self.post_message(self.ViewConversation(session))
