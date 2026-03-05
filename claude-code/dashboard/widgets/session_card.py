"""Reusable session card widget for active and history views."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static

from ..utils.format import format_age, shorten_path
from ..utils.i18n import t


STATUS_COLORS = {
    "working": "#4ade80",
    "attention": "#fbbf24",
    "done": "#60a5fa",
}

STATUS_ICONS = {
    "working": "\u25c9",
    "attention": "\u23f8",
    "done": "\u2713",
}

_STATUS_LABEL_KEYS = {
    "working": "status_working",
    "attention": "status_attention",
    "done": "status_done",
}


class ActiveSessionCard(Widget):
    """Card widget for an active Claude Code session."""

    can_focus = True
    DEFAULT_CSS = """
    ActiveSessionCard {
        height: auto;
        margin: 0 1 1 1;
        padding: 1 2;
        background: #0f1117;
        border: solid #2a2a4a;
    }
    ActiveSessionCard:focus {
        background: #1a1f2e;
        border: solid #4ade80;
    }
    ActiveSessionCard .card-header {
        height: 1;
    }
    ActiveSessionCard .card-meta {
        color: #888;
        height: 1;
    }
    ActiveSessionCard .card-path {
        color: #777;
        height: 1;
    }
    """

    def __init__(
        self,
        tty: str = "",
        pid: int = 0,
        status: str = "working",
        project: str = "",
        branch: str = "",
        worktree: str = "",
        cwd: str = "",
        timestamp: float = 0,
        total_input_tokens: int = 0,
        total_output_tokens: int = 0,
        estimated_cost: float = 0.0,
        primary_model: str = "",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.tty = tty
        self.pid = pid
        self.session_status = status
        self.project = project
        self.branch = branch
        self.worktree = worktree
        self.cwd = cwd
        self.timestamp = timestamp
        self.total_input_tokens = total_input_tokens
        self.total_output_tokens = total_output_tokens
        self.estimated_cost = estimated_cost
        self.primary_model = primary_model

    def compose(self) -> ComposeResult:
        icon = STATUS_ICONS.get(self.session_status, "?")
        color = STATUS_COLORS.get(self.session_status, "#888")
        label_key = _STATUS_LABEL_KEYS.get(self.session_status)
        label = t(label_key) if label_key else self.session_status
        age = format_age(self.timestamp) if self.timestamp else ""
        tty_short = self.tty.split("/")[-1] if self.tty else ""
        branch_display = self.worktree or self.branch

        wt_tag = f" [{t('worktree_tag')}]" if self.worktree else ""

        yield Static(
            f"[{color}]{icon}[/] [{color}]{label}[/]  "
            f"[bold white]{self.project}[/]",
            classes="card-header",
        )
        yield Static(
            f"\U0001f33f {branch_display}{wt_tag}    "
            f"TTY: {tty_short}    "
            f"{age}",
            classes="card-meta",
        )
        # Usage line (if available)
        if self.total_output_tokens > 0:
            from ..utils.format import format_tokens, format_cost
            from ..utils.pricing import format_model_name
            parts = []
            parts.append(f"{format_tokens(self.total_input_tokens)} {t('in_label')} / {format_tokens(self.total_output_tokens)} {t('out_label')}")
            if self.estimated_cost > 0:
                parts.append(f"[#4ade80]{format_cost(self.estimated_cost)}[/]")
            if self.primary_model:
                parts.append(f"[dim]{format_model_name(self.primary_model)}[/]")
            yield Static("    ".join(parts), classes="card-meta")
        yield Static(
            f"\U0001f4c2 {shorten_path(self.cwd, 70)}",
            classes="card-path",
        )


class HistorySessionCard(Widget):
    """Card widget for a historical session."""

    can_focus = True
    DEFAULT_CSS = """
    HistorySessionCard {
        height: auto;
        margin: 0 0 1 0;
        padding: 1 2;
        background: #0f1117;
        border: solid #2a2a4a;
    }
    HistorySessionCard:focus {
        background: #1a1f2e;
        border: solid #4ade80;
    }
    HistorySessionCard .card-header {
        height: 1;
    }
    HistorySessionCard .card-summary {
        color: #aaa;
        height: 1;
    }
    HistorySessionCard .card-meta {
        color: #888;
        height: 1;
    }
    """

    def __init__(
        self,
        session_id: str = "",
        project_name: str = "",
        first_prompt: str = "",
        summary: str = "",
        message_count: int = 0,
        created: str = "",
        modified: str = "",
        git_branch: str = "",
        file_size: int = 0,
        total_input_tokens: int = 0,
        total_output_tokens: int = 0,
        estimated_cost: float = 0.0,
        primary_model: str = "",
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.session_id = session_id
        self.project_name = project_name
        self.first_prompt = first_prompt
        self.summary = summary
        self.message_count = message_count
        self.created = created
        self.modified = modified
        self.git_branch = git_branch
        self.file_size = file_size
        self.total_input_tokens = total_input_tokens
        self.total_output_tokens = total_output_tokens
        self.estimated_cost = estimated_cost
        self.primary_model = primary_model

    def compose(self) -> ComposeResult:
        from ..utils.format import format_date, format_filesize, format_tokens, format_cost, truncate_text
        from ..utils.pricing import format_model_name

        date_str = format_date(self.modified or self.created)
        prompt = truncate_text(self.first_prompt, 80)
        summary = truncate_text(self.summary, 80)

        yield Static(
            f"[bold white]{date_str}[/]  "
            f"\U0001f33f {self.git_branch or '-'}    "
            f"[dim]{self.session_id[:8]}[/]",
            classes="card-header",
        )
        if summary:
            yield Static(f'"{summary}"', classes="card-summary")
        elif prompt:
            yield Static(f'"{prompt}"', classes="card-summary")

        # Usage line: tokens + cost + model
        if self.total_output_tokens > 0:
            model_short = format_model_name(self.primary_model) if self.primary_model else ""
            cost_str = format_cost(self.estimated_cost) if self.estimated_cost > 0 else ""
            parts = [f"{self.message_count} {t('msgs')}"]
            parts.append(f"{format_tokens(self.total_input_tokens)} {t('in_label')} / {format_tokens(self.total_output_tokens)} {t('out_label')}")
            if cost_str:
                parts.append(f"[#4ade80]{cost_str}[/]")
            if model_short:
                parts.append(f"[dim]{model_short}[/]")
            yield Static("    ".join(parts), classes="card-meta")
        else:
            yield Static(
                f"{self.message_count} {t('msgs')}    {format_filesize(self.file_size)}",
                classes="card-meta",
            )
