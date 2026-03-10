#!/usr/bin/env python3
"""Claude Code Session Dashboard - Terminal UI.

A comprehensive terminal dashboard for managing Claude Code sessions,
viewing usage statistics, browsing conversation history, and more.

Usage:
    python app.py
    python app.py --lang zh
    # or via launcher:
    claude-dashboard
"""
from __future__ import annotations

import os
import sys

# Ensure the package can be imported when run directly
if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rich.markup import escape as markup_escape
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Input, Static, TabbedContent, TabPane
from textual.containers import Vertical

from dashboard.screens.active import ActiveSessionsPane
from dashboard.screens.browser import SessionBrowserPane
from dashboard.screens.usage import UsageDashboardPane
from dashboard.screens.conversation import ConversationPane
from dashboard.data.cache import DataCache
from dashboard.utils.i18n import t, set_lang


_TAB_ORDER = ["tab-active", "tab-history", "tab-usage", "tab-conversation"]


class SearchScreen(ModalScreen):
    """Modal search screen for full-text conversation search."""

    DEFAULT_CSS = """
    SearchScreen {
        align: center middle;
    }
    SearchScreen #search-container {
        width: 80;
        height: auto;
        max-height: 30;
        background: #16213e;
        border: solid #4ade80;
        padding: 1 2;
    }
    SearchScreen #search-input {
        margin-bottom: 1;
    }
    SearchScreen #search-results {
        height: auto;
        max-height: 20;
        padding: 0 1;
    }
    SearchScreen .search-result-item {
        padding: 0 1;
        margin-bottom: 1;
    }
    """

    BINDINGS = [
        Binding("escape", "dismiss", "Close"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="search-container"):
            yield Static(
                f"[bold]{t('search_title')}[/]  [dim]{t('search_esc_hint')}[/]"
            )
            yield Input(placeholder=t("search_placeholder"), id="search-input")
            yield Static("", id="search-results")

    def on_mount(self) -> None:
        self.query_one("#search-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if not query:
            return
        from .data.search import search_conversations
        results = search_conversations(query, max_results=20)
        results_widget = self.query_one("#search-results", Static)
        if not results:
            results_widget.update(f"[dim]{t('search_no_results')} '{markup_escape(query)}'[/]")
            return
        lines = [f"[bold]{len(results)} {t('search_results_for')} '{markup_escape(query)}':[/]\n"]
        for r in results:
            role_color = "#3b82f6" if r.role == "user" else "#22c55e"
            preview = markup_escape(r.content_preview[:120])
            lines.append(
                f"[{role_color}]{r.role.upper()}[/] in "
                f"[bold]{markup_escape(r.project_name)}[/] [dim]{r.session_id[:8]}[/]\n"
                f"  {preview}\n"
            )
        results_widget.update("\n".join(lines))


class ClaudeDashboard(App):
    """Main dashboard application."""

    CSS_PATH = "styles/dashboard.tcss"
    TITLE = "Claude Code Dashboard"
    SUB_TITLE = "Session Manager"

    # Disable command palette completely
    COMMANDS = set()
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("q", "quit", "Quit", priority=True),
        Binding("1", "switch_tab('tab-active')", "Active", show=True),
        Binding("2", "switch_tab('tab-history')", "History", show=True),
        Binding("3", "switch_tab('tab-usage')", "Usage", show=True),
        Binding("4", "switch_tab('tab-conversation')", "Conversation", show=True),
        Binding("tab", "next_tab", "Next Tab", show=False, priority=True),
        Binding("shift+tab", "prev_tab", "Prev Tab", show=False, priority=True),
        Binding("escape", "go_back", "Back", show=True),
        Binding("question_mark", "show_help", "Help"),
        Binding("ctrl+r", "refresh_all", "Refresh"),
        Binding("ctrl+f", "search", "Search", show=True),
        Binding("slash", "search", "Search", show=False),
    ]

    def __init__(self):
        super().__init__()
        self.title = t("app_title")
        self.sub_title = t("app_subtitle")
        self.cache = DataCache()
        self._polling_active = True
        self._conversation_origin = "tab-history"

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent(id="main-tabs"):
            with TabPane(t("tab_active"), id="tab-active"):
                yield ActiveSessionsPane(id="active-pane")
            with TabPane(t("tab_history"), id="tab-history"):
                yield SessionBrowserPane(id="browser-pane")
            with TabPane(t("tab_usage"), id="tab-usage"):
                yield UsageDashboardPane(id="usage-pane")
            with TabPane(t("tab_conversation"), id="tab-conversation"):
                yield ConversationPane(id="conversation-pane")
        yield Footer()

    def on_mount(self) -> None:
        """Start background polling for active sessions."""
        self.set_interval(2.0, self._poll_active_sessions)

    async def _poll_active_sessions(self) -> None:
        """Refresh active sessions data periodically."""
        if not self._polling_active:
            return
        try:
            tabs = self.query_one("#main-tabs", TabbedContent)
            is_active_tab = tabs.active == "tab-active"
            active_pane = self.query_one("#active-pane", ActiveSessionsPane)
            active_pane.update_sessions(allow_focus=is_active_tab)
        except Exception:
            pass

    def on_tabbed_content_tab_activated(
        self, event: TabbedContent.TabActivated
    ) -> None:
        """When a tab is activated via the tab bar, auto-focus pane content."""
        tab_id = event.tab.id
        if tab_id:
            # ContentTabs tab IDs have a prefix; strip to get pane ID
            # Tab id format: "--content-tab-<pane-id>"
            pane_id = tab_id.replace("--content-tab-", "")
            if pane_id in _TAB_ORDER:
                self.call_after_refresh(self._focus_pane_content, pane_id)

    def action_focus_content(self) -> None:
        """Focus the active pane content."""
        try:
            tabs = self.query_one("#main-tabs", TabbedContent)
            self._focus_pane_content(tabs.active)
        except Exception:
            pass

    def action_switch_tab(self, tab_id: str) -> None:
        """Switch to a specific tab."""
        self.set_focus(None)
        tabs = self.query_one("#main-tabs", TabbedContent)
        tabs.active = tab_id
        self.call_after_refresh(self._focus_pane_content, tab_id)

    def action_next_tab(self) -> None:
        """Cycle to the next tab."""
        tabs = self.query_one("#main-tabs", TabbedContent)
        idx = _TAB_ORDER.index(tabs.active) if tabs.active in _TAB_ORDER else 0
        self.action_switch_tab(_TAB_ORDER[(idx + 1) % len(_TAB_ORDER)])

    def action_prev_tab(self) -> None:
        """Cycle to the previous tab."""
        tabs = self.query_one("#main-tabs", TabbedContent)
        idx = _TAB_ORDER.index(tabs.active) if tabs.active in _TAB_ORDER else 0
        self.action_switch_tab(_TAB_ORDER[(idx - 1) % len(_TAB_ORDER)])

    def action_go_back(self) -> None:
        """Global Escape: go back from Conversation, else no-op."""
        tabs = self.query_one("#main-tabs", TabbedContent)
        if tabs.active == "tab-conversation":
            self.action_switch_tab(self._conversation_origin)

    def _focus_pane_content(self, tab_id: str) -> None:
        """Focus the target pane so pane-level key bindings work."""
        pane_ids = {
            "tab-active": "#active-pane",
            "tab-history": "#browser-pane",
            "tab-usage": "#usage-pane",
            "tab-conversation": "#conversation-pane",
        }
        pane_id = pane_ids.get(tab_id)
        if not pane_id:
            return
        try:
            pane = self.query_one(pane_id)
            pane.focus()
        except Exception:
            pass

    def action_show_help(self) -> None:
        """Show help overlay."""
        help_text = (
            f"[bold]{t('help_title')}[/]\n\n"
            f"[bold white]{t('help_nav_title')}[/]\n"
            f"  {t('help_nav_tab')}\n"
            f"  {t('help_nav_num')}\n"
            f"  {t('help_nav_updown')}\n"
            f"  {t('help_nav_leftright')}\n"
            f"  {t('help_nav_enter')}\n"
            f"  {t('help_nav_escape')}\n\n"
            f"[bold white]{t('help_actions_title')}[/]\n"
            f"  {t('help_action_iterm')}\n"
            f"  {t('help_action_resume')}\n"
            f"  {t('help_action_delete')}\n"
            f"  {t('help_action_export')}\n"
            f"  {t('help_action_thinking')}\n"
            f"  {t('help_action_sort')}\n\n"
            f"[bold white]{t('help_global_title')}[/]\n"
            f"  {t('help_global_search')}\n"
            f"  {t('help_global_refresh')}\n"
            f"  {t('help_global_help')}\n"
            f"  {t('help_global_quit')}\n"
        )
        self.notify(help_text, timeout=10, title="Help")

    def action_refresh_all(self) -> None:
        """Force refresh all data."""
        self.cache.invalidate_all()
        try:
            self.query_one("#active-pane", ActiveSessionsPane).update_sessions()
        except Exception:
            pass
        try:
            self.query_one("#browser-pane", SessionBrowserPane).refresh_data()
        except Exception:
            pass
        try:
            self.query_one("#usage-pane", UsageDashboardPane).refresh_data()
        except Exception:
            pass
        self.notify(t("all_data_refreshed"))

    def action_search(self) -> None:
        """Open search dialog."""
        self.push_screen(SearchScreen())

    # Handle messages from child panes
    def on_active_sessions_pane_view_conversation(
        self,
        message: ActiveSessionsPane.ViewConversation,
    ) -> None:
        """Switch to conversation tab when viewing an active session."""
        self._conversation_origin = "tab-active"
        conv_pane = self.query_one("#conversation-pane", ConversationPane)
        conv_pane.load_active_session(
            cwd=message.session.cwd,
            project=message.session.project,
            branch=message.session.branch,
        )
        self.action_switch_tab("tab-conversation")

    def on_session_browser_pane_view_conversation(
        self,
        message: SessionBrowserPane.ViewConversation,
    ) -> None:
        """Switch to conversation tab when viewing a history session."""
        self._conversation_origin = "tab-history"
        conv_pane = self.query_one("#conversation-pane", ConversationPane)
        conv_pane.load_session(message.session)
        self.action_switch_tab("tab-conversation")

    def on_conversation_pane_go_back(self, message: ConversationPane.GoBack) -> None:
        """Switch back to the tab that navigated to conversation."""
        self.action_switch_tab(self._conversation_origin)


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", default="zh", choices=["en", "zh"])
    args = parser.parse_args()
    set_lang(args.lang)

    app = ClaudeDashboard()
    app.run()


if __name__ == "__main__":
    main()
