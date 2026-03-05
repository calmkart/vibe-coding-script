"""Usage & Cost Dashboard screen."""
from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.widget import Widget
from textual.widgets import Static

from ..data.stats import UsageStats, load_stats
from ..utils.format import format_date, format_tokens, format_cost, format_duration
from ..utils.pricing import calculate_cost, calculate_total_cost, format_model_name
from ..widgets.ascii_chart import AsciiBarChart
from ..widgets.heatmap import HourlyHeatmap
from ..widgets.cost_table import CostTable
from ..utils.i18n import t


class UsageDashboardPane(Widget):
    """Usage statistics and cost estimation dashboard."""

    can_focus = True

    BINDINGS = [
        Binding("left", "prev_period", "Prev Period", show=False),
        Binding("right", "next_period", "Next Period", show=False),
    ]

    DEFAULT_CSS = """
    UsageDashboardPane {
        height: 1fr;
        width: 1fr;
    }
    UsageDashboardPane #usage-header {
        height: auto;
        background: #16213e;
        padding: 0 2;
    }
    UsageDashboardPane #usage-scroll {
        height: 1fr;
    }
    UsageDashboardPane .overview-grid {
        layout: horizontal;
        height: auto;
        padding: 1;
    }
    UsageDashboardPane .overview-card {
        width: 1fr;
        height: auto;
        padding: 1 2;
        background: #0f1117;
        border: solid #2a2a4a;
        margin: 0 1;
        content-align: center middle;
    }
    UsageDashboardPane .section-title {
        padding: 1 2 0 2;
        text-style: bold;
        color: #aaa;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._stats: UsageStats | None = None
        self._period = "all"  # "all", "30d", "7d"

    def compose(self) -> ComposeResult:
        yield Static("", id="usage-header")
        with VerticalScroll(id="usage-scroll"):
            # Overview cards
            with Horizontal(classes="overview-grid"):
                yield Static("", id="card-sessions", classes="overview-card")
                yield Static("", id="card-messages", classes="overview-card")
                yield Static("", id="card-cost", classes="overview-card")
                yield Static("", id="card-longest", classes="overview-card")

            # Model cost distribution bar
            yield Static("", id="model-dist")

            # Project cost breakdown
            yield Static(f"\u2500\u2500 [bold]{t('cost_by_project')}[/]", classes="section-title")
            yield Static("", id="project-costs")

            # Daily activity chart
            yield Static(f"\u2500\u2500 [bold]{t('daily_activity')}[/]", classes="section-title")
            yield AsciiBarChart(id="daily-chart")

            # Model cost table
            yield Static(f"\u2500\u2500 [bold]{t('model_usage_cost')}[/]", classes="section-title")
            yield CostTable(id="cost-table-widget")

            # Hourly heatmap
            yield Static(f"\u2500\u2500 [bold]{t('usage_by_hour')}[/]", classes="section-title")
            yield HourlyHeatmap(id="hourly-heatmap")

            # Token trend
            yield Static(f"\u2500\u2500 [bold]{t('daily_token_usage')}[/]", classes="section-title")
            yield AsciiBarChart(id="token-chart")

    def on_mount(self) -> None:
        self._refresh_stats()

    def _refresh_stats(self) -> None:
        self._stats = load_stats()
        self._render_dashboard()

    def _render_dashboard(self) -> None:
        if not self._stats:
            header = self.query_one("#usage-header", Static)
            header.update(
                f"[bold white]{t('usage_dashboard')}[/]\n"
                f"[dim]{t('usage_no_data')}[/]"
            )
            self.query_one("#card-sessions", Static).update(
                f"[bold white]0[/]\n[dim]{t('total_sessions')}[/]"
            )
            self.query_one("#card-messages", Static).update(
                f"[bold white]0[/]\n[dim]{t('total_messages')}[/]"
            )
            self.query_one("#card-cost", Static).update(
                f"[bold white]$0.00[/]\n[dim]{t('est_total_cost')}[/]"
            )
            self.query_one("#card-longest", Static).update(
                f"[bold white]N/A[/]\n[dim]{t('longest_session')}[/]"
            )
            return

        stats = self._stats
        all_time_cost = calculate_total_cost(
            {m: {"inputTokens": u.input_tokens, "outputTokens": u.output_tokens,
                 "cacheReadInputTokens": u.cache_read_tokens,
                 "cacheCreationInputTokens": u.cache_creation_tokens}
             for m, u in stats.model_usage.items()}
        )

        # Compute period-filtered overview stats
        filtered_activity = self._filter_by_period(stats.daily_activity)
        filtered_tokens = self._filter_tokens_by_period(stats.daily_tokens)

        if self._period == "all":
            period_sessions = stats.total_sessions
            period_messages = stats.total_messages
            period_cost = all_time_cost
        else:
            period_sessions = sum(a.session_count for a in filtered_activity)
            period_messages = sum(a.message_count for a in filtered_activity)
            # Estimate cost by token proportion
            all_tokens = sum(t_entry.total_tokens for t_entry in stats.daily_tokens)
            period_tokens = sum(t_entry.total_tokens for t_entry in filtered_tokens)
            if all_tokens > 0:
                period_cost = all_time_cost * (period_tokens / all_tokens)
            else:
                period_cost = 0.0

        total_cost = period_cost  # Used by downstream renderers

        # Header
        header = self.query_one("#usage-header", Static)
        header.update(
            f"[bold white]{t('usage_dashboard')}[/]    "
            f"{t('period_label')}: [bold]{self._period_label()}[/]\n"
            f"[dim]{t('usage_hint')}[/]"
        )

        # Overview cards with icons
        self.query_one("#card-sessions", Static).update(
            f"[#60a5fa]\U0001f4cb[/]  [bold white]{period_sessions}[/]\n[dim]{t('total_sessions')}[/]"
        )
        self.query_one("#card-messages", Static).update(
            f"[#a78bfa]\U0001f4ac[/]  [bold white]{period_messages:,}[/]\n[dim]{t('total_messages')}[/]"
        )
        self.query_one("#card-cost", Static).update(
            f"[#4ade80]\U0001f4b0[/]  [bold #4ade80]{format_cost(period_cost)}[/]\n[dim]{t('est_total_cost')}[/]"
        )
        longest_info = (
            f"{stats.longest_session_messages:,} {t('msgs')}"
            if stats.longest_session_messages else "N/A"
        )
        self.query_one("#card-longest", Static).update(
            f"[#fbbf24]\U0001f3c6[/]  [bold white]{longest_info}[/]\n[dim]{t('longest_session')}[/]"
        )

        # Model cost distribution bar
        self._render_model_dist(stats, total_cost)

        # Project cost breakdown
        self._render_project_costs(total_cost)

        # Daily activity chart
        activity_data = self._filter_by_period(stats.daily_activity)
        chart_data = [
            (a.date[5:], float(a.message_count))  # MM-DD format
            for a in activity_data
        ]
        daily_chart = self.query_one("#daily-chart", AsciiBarChart)
        daily_chart.set_data(chart_data, height=8)

        # Cost table
        cost_table = self.query_one("#cost-table-widget", CostTable)
        cost_table.set_data(stats.model_usage)

        # Hourly heatmap
        heatmap = self.query_one("#hourly-heatmap", HourlyHeatmap)
        heatmap.set_data(stats.hour_counts, title=t('heatmap_title'))

        # Token chart
        token_data = self._filter_tokens_by_period(stats.daily_tokens)
        token_chart_data = [
            (t_entry.date[5:], float(t_entry.total_tokens))
            for t_entry in token_data
        ]
        token_chart = self.query_one("#token-chart", AsciiBarChart)
        token_chart.set_data(token_chart_data, height=6)

    def _render_model_dist(self, stats, total_cost: float) -> None:
        """Render a horizontal cost distribution bar by model."""
        dist = self.query_one("#model-dist", Static)
        if total_cost <= 0:
            dist.update("")
            return

        model_colors = {"opus": "#a78bfa", "sonnet": "#60a5fa", "haiku": "#34d399"}
        bar_width = 40
        lines = [f"  [bold dim]{t('cost_by_model')}[/]"]

        items = []
        for model, usage in stats.model_usage.items():
            cost = calculate_cost(
                model=model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                cache_read_tokens=usage.cache_read_tokens,
                cache_creation_tokens=usage.cache_creation_tokens,
            )
            short = format_model_name(model)
            color = "#888"
            for key, c in model_colors.items():
                if key in short.lower():
                    color = c
                    break
            items.append((short, cost, color))

        items.sort(key=lambda x: x[1], reverse=True)

        for short, cost, color in items:
            pct = cost / total_cost * 100 if total_cost > 0 else 0
            filled = max(1, int(pct / 100 * bar_width)) if pct > 0 else 0
            empty = bar_width - filled
            fill_str = "\u2588" * filled
            empty_str = "\u2591" * empty
            bar = f"[{color}]{fill_str}[/][#333]{empty_str}[/]"
            lines.append(f"  {short:<12} {bar}  {format_cost(cost)}  ({pct:.0f}%)")

        dist.update("\n".join(lines))

    def _render_project_costs(self, total_cost: float) -> None:
        """Render a cost breakdown by project directory."""
        widget = self.query_one("#project-costs", Static)
        from ..data.history import discover_all_projects

        projects = discover_all_projects()
        if not projects:
            widget.update(f"  [dim]{t('chart_no_data')}[/]")
            return

        bar_width = 40
        lines = []
        project_colors = ["#60a5fa", "#a78bfa", "#4ade80", "#fbbf24", "#f87171",
                          "#34d399", "#818cf8", "#fb923c", "#38bdf8", "#c084fc"]

        items = []
        for p in projects:
            cost = sum(s.estimated_cost for s in p.sessions)
            sessions = len(p.sessions)
            items.append((p.name, cost, sessions))

        items.sort(key=lambda x: x[1], reverse=True)

        for idx, (name, cost, sessions) in enumerate(items):
            if cost <= 0 and total_cost > 0:
                continue  # Skip zero-cost projects when there's real data
            color = project_colors[idx % len(project_colors)]
            pct = cost / total_cost * 100 if total_cost > 0 else 0
            filled = max(1, int(pct / 100 * bar_width)) if pct > 0 else 0
            empty = bar_width - filled
            fill_str = "\u2588" * filled
            empty_str = "\u2591" * empty
            bar = f"[{color}]{fill_str}[/][#333]{empty_str}[/]"
            lines.append(
                f"  {name:<16} {bar}  {format_cost(cost)}  "
                f"({pct:.0f}%)  [dim]{sessions} {t('n_sessions')}[/]"
            )

        widget.update("\n".join(lines) if lines else f"  [dim]{t('chart_no_data')}[/]")

    def _period_label(self) -> str:
        labels = {"all": t("period_all"), "30d": t("period_30d"), "7d": t("period_7d")}
        return labels.get(self._period, self._period)

    def _filter_by_period(self, activity):
        if self._period == "all":
            return activity

        from datetime import datetime, timedelta
        now = datetime.now()
        days = 30 if self._period == "30d" else 7
        cutoff = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        return [a for a in activity if a.date >= cutoff]

    def _filter_tokens_by_period(self, tokens):
        if self._period == "all":
            return tokens

        from datetime import datetime, timedelta
        now = datetime.now()
        days = 30 if self._period == "30d" else 7
        cutoff = (now - timedelta(days=days)).strftime("%Y-%m-%d")
        return [t_entry for t_entry in tokens if t_entry.date >= cutoff]

    def action_next_period(self) -> None:
        """Switch to next time period (right arrow)."""
        modes = ["all", "30d", "7d"]
        idx = modes.index(self._period)
        self._period = modes[(idx + 1) % len(modes)]
        self._render_dashboard()
        self.notify(f"{t('period_label')}: {self._period_label()}")

    def action_prev_period(self) -> None:
        """Switch to previous time period (left arrow)."""
        modes = ["all", "30d", "7d"]
        idx = modes.index(self._period)
        self._period = modes[(idx - 1) % len(modes)]
        self._render_dashboard()
        self.notify(f"{t('period_label')}: {self._period_label()}")

    def refresh_data(self) -> None:
        self._refresh_stats()
