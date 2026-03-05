"""Filter bar and search bar widgets."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.message import Message
from textual.widget import Widget
from textual.widgets import Input, Static


class SearchBar(Widget):
    """Search input bar that emits search events."""

    DEFAULT_CSS = """
    SearchBar {
        height: 3;
        background: #16213e;
        border-top: solid #2a2a4a;
        padding: 0 2;
        layout: horizontal;
        dock: bottom;
    }
    SearchBar Input {
        width: 1fr;
    }
    SearchBar .search-label {
        width: auto;
        padding: 1 1 0 0;
        color: #888;
    }
    """

    class Submitted(Message):
        def __init__(self, query: str):
            super().__init__()
            self.query = query

    class Cleared(Message):
        pass

    def compose(self) -> ComposeResult:
        yield Static("Search: ", classes="search-label")
        yield Input(placeholder="Type to search...", id="search-input")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        query = event.value.strip()
        if query:
            self.post_message(self.Submitted(query))
        else:
            self.post_message(self.Cleared())

    def focus_input(self) -> None:
        self.query_one("#search-input", Input).focus()

    def clear(self) -> None:
        self.query_one("#search-input", Input).value = ""
        self.post_message(self.Cleared())
